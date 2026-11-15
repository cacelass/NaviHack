# Roadmap

Work left for the other agents. Pick one item, open a ticket with `harness add`, close it with the gate green.

## Map

- **Bottom-left of the drawing.** The lower-left area does not show at full size/quality (seams and a softer band). Repaint or rescale those tiles so the whole drawing looks the same at every zoom.
- **Seams between tiles.** Keep fixing visible joins (the current set is `v10-costura-izq`).
- **Night and weather.** Bring the light and rain prototypes (`_prototipos/`, local only) into `web/js/ambient.js`.

## Content

- **Photos.** Some places have no photo (e.g. «Papá Noel en la Farola»).
- **Texts.** Review `web/data/stories.json` with a human; English was translated by an agent.
- **Source mismatch.** «Circo de Navidad» says 5 December in its name and 4 December in its schedule.

## Docs

- **README images.** All screenshots in `docs/img/` predate the new HUD; retake them (desktop, phone, walk, agenda, detail) and update `README.md`.
- **Landing.** Refresh the screenshots in `landing/` the same way.

## App

- **Walk.** Link «Seguirme» (live position) with the step-by-step card.
- **Accessibility.** Keyboard and screen reader pass over every panel.
- **Offline.** Installable app with cached tiles for walking without signal.

## Infra

- **Auto-deploy.** Deploy on every push to `main` (Vercel Git integration or a GitHub Action with a `VERCEL_TOKEN` secret; needs the repo owner).
