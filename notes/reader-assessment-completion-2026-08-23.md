# Reader-assessment completion — 23 August 2026

This change activates the already-reviewed reader-assessment layer in the final deployment pipeline and keeps the existing later layers for the genuine bilingual book excerpt, accumulating Sundays archive and grouped homepage menu hierarchy.

The activated reader pass covers:

1. English display dates.
2. Follow loading/honeypot presentation.
3. Homepage opening hierarchy.
4. Fable/cat explanation on the book page.
5. Free complete digital reading from 3 January.
6. Stronger emphasis on the labyrinth already existing at Los Escullos.

The later deployment layers already cover:

7. Genuine bilingual book excerpt and illustration.
8. Accumulating 22-Sundays archive.
9. Grouped secondary navigation to reduce 01–14 flattening.

The final predeploy invariant also preserves the approved English homepage wording `built from stone`.

The Pages Wrangler configuration intentionally excludes `[observability]`: current Wrangler Pages validation does not support that field. Tracing belongs on a Worker/Agent workload rather than this Pages project.
