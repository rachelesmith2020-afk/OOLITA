# OOLITA deployment

This repository is a deployment bridge for the existing Cloudflare Pages project `oolita`.

## Safety model

- Deployment is manual only (`workflow_dispatch`).
- The Cloudflare API token must exist only as the GitHub Actions secret `CLOUDFLARE_API_TOKEN`.
- The token must have only Cloudflare Pages write/edit permission.
- The workflow reconstructs the current site from the clean Pages origin `https://oolita.pages.dev/`, overlays reviewed files from `overrides/`, checks the site bundle, then deploys the complete folder.
- The workflow refuses to deploy if the reconstructed bundle has fewer than 80 files or contains `.bak`, `.py`, editor-backup, or `.DS_Store` files.

## Project

- Cloudflare Pages project: `oolita`
- Cloudflare account ID: `c608b5c0e07dc00bd74aa24c9cc78c4a`

Do not commit Cloudflare tokens, passwords, API keys, or other credentials to this repository.
