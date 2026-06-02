#!/usr/bin/env node
"use strict";

// Thin npm wrapper for the ai-crucible CLI. Pure JSON config — @mcptoolshop/npm-launcher derives
// the release-asset names from convention, downloads the platform binary from the ai-crucible
// GitHub Release, verifies its SHA256 against checksums-<version>.txt, caches it, and runs it
// with full arg passthrough.
//   binary:    ai-crucible-0.2.0-linux-x64
//   checksums: checksums-0.2.0.txt
process.env.MCPTOOLSHOP_LAUNCH_CONFIG = JSON.stringify({
  toolName: "ai-crucible",
  owner: "dogfood-lab",
  repo: "ai-crucible",
  version: "0.2.0",
  tag: "v0.2.0",
});

require("@mcptoolshop/npm-launcher/bin/mcptoolshop-launch.js");
