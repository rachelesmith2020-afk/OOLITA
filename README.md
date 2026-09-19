# OOLITA

**OOLITA** is an independent environmental, cultural and artistic project based in Almería, Spain.

This repository supports the development, maintenance and deployment of the public website at **https://oolita.es**.

## Project scope

OOLITA combines place-based environmental research, bilingual publishing, digital documentation and artistic work connected to the landscape of Almería.

The repository is used to manage the website as a live digital project rather than as a static portfolio. Work includes content maintenance, deployment, validation, accessibility, search, analytics and supporting web infrastructure.

## Maintainer role

The project is maintained by **Rachele Smith**. Day-to-day work includes:

- researching and checking environmental and project information
- preparing and reviewing English- and Spanish-language content
- maintaining website content and code
- using Git for version control and change tracking
- managing Cloudflare-based deployment
- reviewing changes against written requirements before publication
- producing project documentation and maintaining structured digital records

The repository reflects practical project maintenance rather than a claim of professional software-engineering specialization.

## Technical workflow

The project uses a Git-based workflow with:

- **GitHub** for version control and change history
- **GitHub Actions** for automated validation and deployment workflows
- **Cloudflare Pages** for production hosting
- **Cloudflare Workers / Functions and D1** for supporting site functionality
- reviewed overrides and scripted transformations for controlled site updates
- automated checks designed to prevent incomplete or unsafe deployments

The deployment process is documented in [DEPLOYMENT.md](DEPLOYMENT.md).

## Repository structure

Key areas include:

- `.github/workflows/` — automated workflow and deployment configuration
- `assets/` — site assets
- `functions/` — supporting application functions
- `overrides/` — reviewed website changes
- `scripts/` — maintenance, validation and transformation scripts
- `search/` — search-related functionality
- `social/` — supporting social/web content tooling
- `wrangler.toml` — Cloudflare Pages configuration

## Content governance

Reader-facing authored copy is intentionally controlled. The current content policy is documented in [COPY_FREEZE.md](COPY_FREEZE.md), which distinguishes approved editorial changes from technical, accessibility and deployment changes.

## Skills demonstrated

This project provides evidence of practical work in:

- research, evidence checking and documentation
- Git and version-controlled workflows
- website and content management
- bilingual English/Spanish publishing
- quality assurance and detailed procedural checking
- Cloudflare-based deployment
- independent digital project management

## Website

**https://oolita.es**
