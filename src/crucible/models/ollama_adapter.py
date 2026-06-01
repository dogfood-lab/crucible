"""Ollama model adapter — the Phase-2 bridge from Phase-1 stubs to real local models.

The Phase-1 kernel takes everything model-shaped as an *injected callable*
(``generate``, the ``judges`` list, the ``oracle_runner``) so its policy logic is
unit-testable without a model runtime (kernel docstring; research-grounding §10.2).
This module supplies the first concrete backing for those slots: a local model
served by **Ollama** on the RTX 5090 (§8.6, §11.2). One :class:`OllamaModel`
instance plugs into three places at once:

* the kernel's **``generate``** choke point — :meth:`OllamaModel.generate`;
* a cross-family **panel judge** — :meth:`OllamaModel.judge` (+ :meth:`as_judge`,
  which carries the ``.family`` attribute :class:`~crucible.scoring.judge_panel.JudgePanel`
  reads to enforce EXTERNAL_VERIFIER same-family exclusion, §10.2);
* a **characterization** probe — :meth:`OllamaModel.judge_item`, which returns a
  :class:`~crucible.characterize.types.JudgmentRecord` (the §11.1 admission-test
  input unit).

Determinism / serving (research-grounding §11.2)
------------------------------------------------
Every call pins deterministic sampling: ``temperature=0``, a fixed ``seed``, and a
fixed ``num_ctx``. Per §11.2 the dominant temp-0-drift lever is **batch-invariance,
not RNG** (Thinking Machines 2025, §9.7), so the panel is intended to run
**sequentially** — ``OLLAMA_NUM_PARALLEL=1``, and because three 24–35B models cannot
co-reside in 32 GB, **load → judge → evict** one model at a time (Ollama docs). This
adapter does not *spawn* that serving topology (that is the harness's job); it pins
the per-request determinism knobs and documents the contract so a profiling run is
replayable (PIN_PER_STEP). The recommended ``num_ctx``/seed live on the instance and
are echoed into every request and into :attr:`JudgmentRecord.metadata`.

Injectable client (testability)
-------------------------------
The model client is a **constructor parameter** (``client=None``). When ``None``,
the adapter resolves a real client lazily at call time — the official ``ollama``
async client if installed, else a thin :class:`httpx`-backed POST to
``/api/chat`` — so importing this module never requires either to be present. Tests
pass a fake client exposing ``async def chat(*, model, messages, options, ...)`` and
no network call is made (build-law 3). API endpoints/keys are read from the
environment at call time, never captured at import.

Standards compliance (the six — workflow-standards.md)
------------------------------------------------------
* **PIN_PER_STEP — 3:** every request pins ``model_id`` + ``quant`` + the full
  deterministic option set (``temperature``/``seed``/``num_ctx``), and
  :meth:`judge_item` records all of them in :attr:`JudgmentRecord.metadata` so a
  profile run is byte-for-byte replayable. Proven in ``tests/test_models.py``
  (deterministic-kwargs + metadata assertions).
* **ANDON_AUTHORITY — n/a:** halting authority is the kernel's (budget/andon); an
  adapter is a leaf the kernel drives. A transport error surfaces as an exception
  for the caller's andon, never a silent empty completion.
* **NAMED_COMPENSATORS — n/a:** a completion is a pure read; the adapter performs no
  irreversible action (no publish/write/network mutation) to compensate.
* **DECOMPOSE_BY_SECRETS — 2:** the adapter knows only model-serving config; it
  never sees gold labels (those live with the grader/profiler, §11.6) — ``judge_item``
  leaves ``gold``/``correct`` ``None`` for the scorer to fill.
* **UNCERTAINTY_GATED_HUMANS — n/a:** no human checkpoint at the model-call layer.
* **EXTERNAL_VERIFIER — 3:** the whole point — :meth:`as_judge` tags the judge with
  its ``family`` so the panel can structurally drop a same-family judge (§10.2);
  proven by the ``JudgePanel`` exclusion test.
"""

from __future__ import annotations

import os
import time
from collections.abc import Awaitable, Callable
from typing import Any

from crucible.characterize.types import JudgmentRecord
from crucible.scoring.judge_panel import JudgeFn
from crucible.types import AttemptState, Score

__all__ = ["OllamaModel", "OllamaClient"]

#: Structural type for the Ollama chat client the adapter drives. Both the official
#: ``ollama`` async client and the built-in httpx fallback satisfy this; tests pass a
#: fake of the same shape. ``chat`` returns the raw response mapping (Ollama's
#: ``/api/chat`` shape: ``{"message": {"content": ...}, ...}``).
OllamaClient = Callable[..., Awaitable[dict[str, Any]]]

#: Default fixed context window pinned for determinism (§11.2). Overridable per
#: instance; echoed into every request and into the JudgmentRecord metadata.
_DEFAULT_NUM_CTX = 8192

#: Default fixed RNG seed. With ``temperature=0`` sampling is greedy, but a fixed
#: seed is pinned anyway so any future non-zero-temp arm stays replayable (PIN_PER_STEP).
_DEFAULT_SEED = 0

#: Default Ollama host; read from the env at call time so deployment is not baked in.
_DEFAULT_HOST = "http://localhost:11434"


def _extract_text(response: dict[str, Any]) -> str:
    """Pull the assistant text out of an Ollama ``/api/chat`` response.

    The chat endpoint returns ``{"message": {"role": "assistant", "content": ...}}``.
    Falls back to a top-level ``"response"`` (the ``/api/generate`` shape) so a fake
    client may return either, then to ``""`` — never raising on a missing field, since
    an empty completion is a legitimate (if unhelpful) model answer the caller scores.
    """
    message = response.get("message")
    if isinstance(message, dict) and "content" in message:
        return str(message["content"])
    if "response" in response:
        return str(response["response"])
    return ""


class OllamaModel:
    """A local model served by Ollama, usable as kernel ``generate`` / panel judge /
    characterization probe.

    Args:
        model_id: the Ollama model tag, e.g. ``"mistral-small:24b"``.
        family: the model *family* for EXTERNAL_VERIFIER exclusion, e.g.
            ``"mistral"`` (a judge of the generator's family is dropped by the panel,
            §10.2). Distinct from ``model_id`` so two checkpoints of one base never
            both seat (§11.4 ρ-gate spirit).
        quant: optional quantization tag (e.g. ``"q4_K_M"``) recorded for the §11.2
            quant sweep; carried into every :class:`JudgmentRecord` so reliability can
            be sliced by quant.
        client: an injected client of the :data:`OllamaClient` shape. ``None``
            (default) resolves a real client lazily at call time (official ``ollama``
            async client if importable, else an httpx ``/api/chat`` POST). Injected so
            tests pass a fake and the suite makes no network call.
        num_ctx: fixed context window pinned for determinism (§11.2).
        seed: fixed RNG seed pinned for replayability (§11.2 / PIN_PER_STEP).
        host: Ollama base URL; defaults to ``$OLLAMA_HOST`` then ``localhost:11434``,
            read at call time (never captured at import).
    """

    def __init__(
        self,
        model_id: str,
        family: str,
        quant: str | None = None,
        *,
        client: OllamaClient | None = None,
        num_ctx: int = _DEFAULT_NUM_CTX,
        seed: int = _DEFAULT_SEED,
        host: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.family = family
        self.quant = quant
        self._client = client
        self.num_ctx = num_ctx
        self.seed = seed
        self._host = host

    # -- deterministic request options (§11.2) ------------------------------- #

    def _options(self) -> dict[str, Any]:
        """The pinned deterministic sampling options sent on every request (§11.2).

        ``temperature=0`` (greedy) + a fixed ``seed`` + a fixed ``num_ctx``. Kept in
        one place so the request path and the recorded ``metadata`` cannot drift —
        :meth:`judge_item` stores exactly this dict, making the call replayable.
        """
        return {"temperature": 0, "seed": self.seed, "num_ctx": self.num_ctx}

    def pin_metadata(self) -> dict[str, Any]:
        """The PIN_PER_STEP provenance block stamped on characterization records.

        Captures everything needed to replay a request byte-for-byte: the model tag,
        its quant, and the exact deterministic options. Stored under
        :attr:`JudgmentRecord.metadata` so a profile run reproduces (§11.6).
        """
        return {
            "model_id": self.model_id,
            "family": self.family,
            "quant": self.quant,
            "options": self._options(),
            "serving": "OLLAMA_NUM_PARALLEL=1; load->judge->evict (§11.2)",
        }

    # -- client resolution (lazy, env-read) ---------------------------------- #

    def _resolve_client(self) -> OllamaClient:
        """Return the injected client, or lazily build a real one at call time.

        Order: (1) the injected ``client`` (tests + explicit wiring); (2) the official
        ``ollama`` async client if importable; (3) a thin httpx POST to ``/api/chat``.
        Resolved lazily so importing this module needs neither package, and the host
        is read from the env *now*, not at import (no baked-in deployment).
        """
        if self._client is not None:
            return self._client
        host = self._host or os.environ.get("OLLAMA_HOST", _DEFAULT_HOST)

        try:
            import ollama  # type: ignore[import-untyped]

            async_client = ollama.AsyncClient(host=host)

            async def _via_sdk(**kwargs: Any) -> dict[str, Any]:
                resp = await async_client.chat(**kwargs)
                # The SDK may return a pydantic-ish object; normalize to a mapping the
                # rest of the adapter (and tests) treat uniformly.
                return dict(resp) if not isinstance(resp, dict) else resp

            self._client = _via_sdk
            return self._client
        except ImportError:
            pass

        import httpx

        async def _via_httpx(**kwargs: Any) -> dict[str, Any]:
            payload = {**kwargs, "stream": False}
            async with httpx.AsyncClient(base_url=host, timeout=600.0) as http:
                r = await http.post("/api/chat", json=payload)
                r.raise_for_status()
                return r.json()

        self._client = _via_httpx
        return self._client

    # -- core completion ----------------------------------------------------- #

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        """Call Ollama chat with the pinned deterministic options and return the text.

        Sends ``{model, messages, options}`` (options = :meth:`_options`, §11.2) to the
        resolved client and extracts the assistant content. Determinism is pinned here;
        the *sequential* serving topology (one model loaded at a time,
        ``OLLAMA_NUM_PARALLEL=1``) is the harness's responsibility — this method only
        guarantees a single request carries the replayable knobs.
        """
        client = self._resolve_client()
        response = await client(
            model=self.model_id,
            messages=messages,
            options=self._options(),
        )
        return _extract_text(response)

    # -- kernel generate plug (§10.2) --------------------------------------- #

    async def generate(self, state: AttemptState) -> str:
        """Kernel ``generate`` choke point: complete on ``state.messages`` → text.

        Matches :data:`crucible.roles.GenerateFn` (``(AttemptState) -> Awaitable[str]``)
        so a bound ``model.generate`` drops straight into ``run_attempt(generate=...)``.
        The kernel — not this adapter — records the call as a ``TraceEvent`` and owns
        budget/andon; the adapter only produces the completion (§10.2).
        """
        return await self.complete(state.messages)

    # -- panel judge plug (§10.2, EXTERNAL_VERIFIER) ------------------------- #

    async def judge(self, attempt: AttemptState) -> Score:
        """Score an attempt as a panel judge → :class:`~crucible.types.Score`.

        The model is shown the attempt's solved context + output and asked for a
        verdict; here the parse is intentionally thin (the real rubric/parse lands with
        the Phase-2 calibration set, §11.3). The returned ``Score.metadata`` records the
        judging ``model_id``/``family`` for audit and may carry a ``novelty_validated``
        vote the panel aggregates (§8.7). Use :meth:`as_judge` to obtain the panel-ready
        callable that also carries the ``.family`` attribute the panel reads.
        """
        verdict = await self.complete(self._judge_messages(attempt))
        return Score(
            value=verdict,
            explanation=verdict,
            metadata={"judge_model": self.model_id, "judge_family": self.family},
        )

    def as_judge(self) -> JudgeFn:
        """Return a panel-ready judge callable tagged with this model's ``family``.

        :class:`~crucible.scoring.judge_panel.JudgePanel` reads the model family off a
        ``family`` attribute on the *callable* (``judge_family`` → ``getattr(judge,
        "family", None)``) to drop same-family judges (EXTERNAL_VERIFIER, §10.2). A
        bound method cannot carry that attribute, so this factory wraps :meth:`judge`
        in a plain async function and stamps ``.family`` on it — the supported way to
        seat this model on a :class:`JudgePanel`.
        """

        async def _judge(attempt: AttemptState) -> Score:
            return await self.judge(attempt)

        _judge.family = self.family  # type: ignore[attr-defined]
        return _judge

    def _judge_messages(self, attempt: AttemptState) -> list[dict[str, Any]]:
        """Build the chat messages for a judging call.

        Reuses the attempt's scored context and appends the Solver's output for the
        judge to rule on. NEVER reads ``attempt.chrome`` (Tier-3 is sealed out of every
        model context, §10.1(e)). The terse instruction here is a placeholder for the
        §11.3 rubric prompt; the wiring/exclusion is what Phase-1→2 needs proven now.
        """
        return [
            *attempt.messages,
            {
                "role": "user",
                "content": (
                    "You are an impartial judge. Given the candidate output below, "
                    "respond with your verdict.\n\n"
                    f"OUTPUT:\n{attempt.output or ''}"
                ),
            },
        ]

    # -- characterization probe (§11.1) -------------------------------------- #

    async def judge_item(
        self,
        prompt: str,
        *,
        run_index: int = 0,
        position: int | None = None,
    ) -> JudgmentRecord:
        """Run one calibration item → a :class:`JudgmentRecord` (the §11.1 metric unit).

        Sends ``prompt`` as a single user turn, records the model's prediction and the
        measured latency, and returns a record stamped with ``model_id`` / ``family`` /
        ``quant`` plus the PIN_PER_STEP provenance in ``metadata`` (so the profile run
        is replayable, §11.6). ``gold`` and ``correct`` are left ``None`` — they are
        filled later by the scorer that holds the gold labels (DECOMPOSE_BY_SECRETS:
        labels live with the grader, never the profiled model, §11.6). ``run_index``
        drives test-retest consistency and ``position`` drives position-swap bias
        (§11.1 metrics 4 and 6).

        Args:
            prompt: the calibration item text shown to the model.
            run_index: 0..k-1 index for the test-retest repeat (§11.1 #4).
            position: option-order slot for position-swap bias (e.g. 0/1), or ``None``.

        Returns:
            A :class:`JudgmentRecord` with ``predicted`` set, ``gold``/``correct``
            ``None``, ``latency_s`` measured, and ``metadata`` carrying the pin block.
        """
        messages = [{"role": "user", "content": prompt}]
        start = time.monotonic()
        predicted = await self.complete(messages)
        latency_s = time.monotonic() - start
        return JudgmentRecord(
            item_id=_item_id(prompt),
            model_id=self.model_id,
            predicted=predicted,
            gold=None,
            quant=self.quant,
            latency_s=latency_s,
            run_index=run_index,
            position=position,
            family=self.family,
            metadata=self.pin_metadata(),
        )


def _item_id(prompt: str) -> str:
    """A stable short id for a calibration item, derived from its prompt text.

    The profiler keys records by item; deriving the id from the prompt content keeps
    a probe self-identifying without a separate registry at this layer. (The real
    calibration set, §11.3, will supply authored item ids; this is the adapter-local
    fallback so :meth:`judge_item` is usable standalone in tests.)
    """
    import hashlib

    return "item-" + hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
