# OOLITA copy freeze

Status: active after the 26 August 2026 content audit.

Existing reader-facing authored copy is frozen. It changes only for:

1. a factual correction;
2. a genuine ambiguity demonstrated by reader behaviour or direct feedback;
3. an approved launch-state change tied to a confirmed date, availability or link;
4. an explicitly approved new work, edition, Sunday or project update.

It does not change because an SEO tool wants more words, a page is short, a generic content score asks for depth, or another page uses similar terminology.

Automated scripts may change technical metadata, structured data, accessibility attributes, analytics attributes, layout, spacing, image handling, URLs, dates and approved status labels. They must not manufacture new reader-facing explanatory paragraphs.

Protected voice anchors include:

- `Primero fue un laberinto.` / `First there was a labyrinth.`
- `El lugar no es un fondo.` / `The place is not a backdrop.`
- `Piedra. Papel. Código.` / `Stone. Paper. Code.`
- the approved Hallazgo practice description;
- the approved environmental language around one physical labyrinth and remote access.

The final production guard in `scripts/apply_post_audit_growth_system_v1.py` fails deployment if retired synthetic filler returns or protected anchors disappear.
