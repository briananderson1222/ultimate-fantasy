# Brand Identity & Art Direction

This brief defines the brand, tone, logo directions, and illustration style for Ultimate Fantasy. It includes a lightweight moodboard you can evolve into a formal Brand Kit.

## Name & Tagline

- Product name: Ultimate Fantasy
- Tagline (candidate): Build the league you want.

Rationale: professional and sport‑agnostic; aligns with the platform’s deep customization.

## Tone of Voice

- Competitive, confident, and welcoming
- Short, active phrasing; avoid jargon and fluff
- Pro‑grade without being elitist; helpful, approachable guidance

Examples:
- Success: “League created.” / “Lineup saved.”
- Help: “Set starters. We’ll validate positions.”
- Error: “Validation failed. Fix the highlighted fields.”

## Logo Directions

- Primary: Wordmark “Ultimate Fantasy” in a modern, geometric sans (e.g., Inter/Alternate or similar). Tight tracking, medium–semibold.
- Secondary mark: Monogram “UF” in a shield/crest or rounded square. Angled baseline evokes forward motion/speed.
- Iconography style: outline icons matching lucide‑react’s stroke weight; limited fills; strong contrast on dark/graphite backgrounds.

Construction notes:
- Use a 24px grid for small marks; 2px corner radii to match UI tokens.
- Prefer simple geometry for scalable clarity (no fine details).

## Mascot/Illustration Style

- Style: minimal geometric sport motifs (ball seams, field hash marks, goal posts) with subtle gradients and noise textures.
- Avoid literal mascots in v1; prefer abstract shapes and badges that adapt to multiple sports.
- Motion: subtle parallax or hover shifts (reduced‑motion compliant).

## Color & Surface Moodboard

Primary palette (Light):
- Turf Green: #17803A (primary)
- Honey Gold: #FFC94D (accent)
- Graphite: #111827 / #0B1220 (dark mode surfaces)
- Surfaces: #FFFFFF (cards), #F7F8FA (background)
- Text: #0F172A (body), #475569 (muted)

Shadows & depth:
- Shadows are soft and sparse; use `--shadow-sm` and `--shadow-md` tokens.
- Elevation is subtle; reserve strong shadows for overlays.

Textures:
- Optional noise overlay for hero/headers and scoreboard tiles.
- Angle or diagonal motif to suggest motion in section dividers.

See `specs/001-ultimate-fantasy-platform/docs/ui-theme.md` for the full token set and Tailwind integration.

## Applications

- Landing hero: bold wordmark, badge/icon, concise value props, create/join CTAs.
- League public page: scoreboard tiles with badges (Leader, Streak), member avatars.
- Dashboard: modular widgets with brand‑colored accents and accessible focus rings.

## Asset Structure

Place brand assets here (add your own sources):
- `frontend/public/brand/logo-wordmark.svg`
- `frontend/public/brand/logo-mark.svg`
- `frontend/public/brand/palette.png` (or exported from Theme Studio)
- `frontend/public/brand/textures/noise.png`

Optional: export a `BrandKit.zip` containing the above and `README` usage.

## Next Steps

- Finalize wordmark/mark vectors; ensure legibility on light and dark.
- Produce favicon set and social preview image.
- Build brand preset in Theme Studio (`/settings/theme`) named “Ultimate Fantasy”.

