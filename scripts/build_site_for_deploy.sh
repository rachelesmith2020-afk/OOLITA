#!/usr/bin/env bash
set -euo pipefail

# This branch is superseded by main, which now ships and validates the exact
# Hallazgo PNG from the repository. Keep the branch build aligned with main so
# no alternate image-source strategy can be merged accidentally.
exec bash scripts/build_site_for_deploy_original.sh
