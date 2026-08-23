# Cloudflare request tracing

Configured for the OOLITA Cloudflare Pages project on 2026-08-23.

- Deployment target: Cloudflare Pages with Pages Functions.
- Compatibility date preserved from the live project: `2026-08-10`.
- D1 binding preserved: `OOLITA_SUBSCRIBERS`.
- Normal Workers request tracing enabled with `head_sampling_rate = 0.01` (1%).
- No AI-agent payload instrumentation is enabled.
- No log sampling configuration was changed.

The configuration is validated by the existing Pages Functions build before production deployment.
