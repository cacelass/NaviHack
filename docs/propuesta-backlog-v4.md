# TinyVigo backlog v4: proposal

Status: **ready to apply, not applied yet.** Jose asked for it to be applied directly in GEAS. The agent actor has the `agent` role (start, complete, block) and GEAS answers FORBIDDEN `ticket:update` / create / cancel, so the changes cannot be written until an actor with those permissions runs `scripts/apply_backlog_v4.py --apply` (dry-run is the default). Nothing has been changed in GEAS.

Source of truth: `docs/tinyvigo-spec.md` (the isometric pixel-art spec, which replaces spec v3). Context: `INFORME.md` of the competition study (sections 1, 4, lessons 10-11 and licences 7).

Legend: ticket ids of existing tickets are kept on purpose (GEAS dependencies and history survive); only title, description, criteria and dependencies change. The ticket blocks are in the same tuple format as `scripts/seed_tinyvigo.py`: `(id, title, description, criteria[], depends_on[])`.

## 1. Classification of the 38 existing product tickets

The other 13 tickets in GEAS (GEAS-001, SCOPE-001, QA-001, BOOT-001..004, ONBOARD-001/002, FIX-001, DESIGN-001, CORE-001, WIN-001) are harness/infra tickets and are not classified here; see section 5 for the three that are affected.

Total: **15 stay, 15 change, 8 leave v1, 28 new.**

### 1.1 Stay as they are (15)

| Ticket | Why it still holds |
| --- | --- |
| R-03 | Dated photos and GPS per point feed F3 (real photo next to the sprite), the asset sprites and the tile notes. Only the old word "scenes" in the description is stale. |
| R-04 | F2 needs schedule per point; also gives the Concello's real switch-on time for the night layer. |
| R-05 | The spec says the loader is re-run and the app shows when the data was last refreshed. |
| D-00 | In progress, claimed by someone else. Feed measurements still needed for the nightly job. |
| D-01 | The spec's "nightly job" that publishes plain files. |
| D-03 | F4 source: the cultural agenda. |
| D-04 | F4: events matched to venues by name; unmatched go to the list only. |
| D-05 | "Parking" is one of the F1 toggle layers. |
| D-11 | Needed by the "Easy walk" route (avoid steep streets). |
| D-18 | The spec requires showing the date of the last data refresh. |
| STORY-01 | F2 story cards, with a source link or not shown. Same rule as before. |
| I18N-01 | Galician, Spanish, English; no hard-coded strings (non-functional). |
| X-01 | Vitrasa GTFS, labelled "scheduled". **Enters v1** (F6). Content unchanged. |
| X-03 | The spec says to verify Renfe live coverage before showing anything live. Same check. |
| X-09 | "Cameras" is one of the F1 toggle layers; proxy or links, terms checked. |

### 1.2 Change (15)

| Ticket | What changes |
| --- | --- |
| R-01 | Starts from the Concello's ArcGIS layer (43 points, 2025-26) plus an editable overrides file for 2026 changes, instead of building the list from nothing. Press-only points get "not yet confirmed by the Concello". Depends on R-06. |
| R-02 | Output is no longer "unblocks scene generation" but reference photos and verified coordinates for tile notes and assets. |
| R-06 | No longer optional: it becomes the loader of the base layer. Absorbs X-12. |
| D-10 | Open-Meteo is now also the input of the map weather overlay, so it needs the hourly forecast for several days and more variables (cloud cover, visibility, wind, gusts, weather code). Adds the Marine coverage check. |
| D-12 | Adds the rain warning and "favour covered or indoor stops". Parking hint is not in the spec (see Doubts). |
| D-17 | Credits list grows: Renfe, Open-Meteo, the image model provider. Depends on LIC-01. |
| MAP-01 | From "satellite + night + sprites" to the isometric tile viewer: pan/zoom, mini-map, search, 7 toggle layers, PNOA satellite toggle. Night moves to NIGHT-01. |
| SCENES-01 | From "6 night scenes" to "6 animated-ready Christmas assets with their own ground patch". The close-up illustration is a later bonus. |
| PREVIEW-01 | Fly-to at full zoom; real photo and pixel sprite side by side; "not yet confirmed" label. The nearest car park block leaves the panel (not in F3). |
| PLANNER-01 | Adds start options (including "I arrive at Vigo-Urzáiz"), the rain warning, and the route drawn on the map with numbered stops. Depends on MAP-01. |
| POSTCARD-01 | Draws from a crop of the map or the point asset plus the style reference. Depends on IMGAPI-01 (payment decision) instead of SCENES-01 alone. |
| X-02 | Spec feed is Renfe Alta Velocidad, Larga y Media Distancia (CC BY 4.0). Cercanías static GTFS is not in the spec (see Doubts). |
| X-04 | Dependency only: needs PLANNER-01 (it adds transit legs to it). Adds the "scheduled" label for train and bus legs. |
| X-05 | Goes from an optional layer to **input of the render pipeline** (the Concello 3D buildings are the geometry). Adds data year per area (feeds outdated zones) and licence for derived images. |
| EVENTS-01 | Dependency only: add MAP-01 (it has a map layer). Added events become fixed-time stops. |

### 1.3 Leave v1 (8)

| Ticket | Reason | Where its useful part goes |
| --- | --- | --- |
| X-06 busy-now | Spec: "Crowd or queue data (no open source exists)" is out of v1. | Nothing. |
| X-07 MITMA OD | Only fed X-06. | Nothing. |
| X-08 traffic layer | "Traffic" is not in the F1 layer list. Moving cars on the map are decoration, not real traffic. | See Doubts. |
| X-10 DGT incidents | Not in the spec. | Nothing. |
| X-11 Concello notices | Not in the spec. The "cancelled Christmas stops" cross-check stays inside X-01. | X-01. |
| X-12 enumerate map services | The Concello layer is already identified in the spec. | R-06. |
| X-13 weather backups and tides | AEMET and tides are not in the spec. MeteoGalicia is only a "candidate, licence to check". | Licence check in LIC-01; Marine in D-10. |
| X-14 TomTom tiles | Not in the spec. | Nothing. |

Proposal: move them to `blocked`/"post-v1" with a note, never delete (history stays). Jose and the team decide.

## 2. Changed tickets (full new text)

_The ticket text lives in `scripts/backlog_v4_tickets.py` (`TICKETS_CHANGED`)._

## 3. New tickets

Order follows the spec plan: style, render, 3x3 block (go/no-go), day map, light/night/weather, Christmas assets, viewer, routes/transit, postcard.

_The ticket text lives in `scripts/backlog_v4_tickets.py` (`TICKETS_NEW`)._

## 4. Dependency graph, short version

```
R-06 -> R-01 -> R-02 -> SCENES-01 -> ASSETS-02 / ANIM-01 / PREVIEW-01 / POSTCARD-01
R-06 -> ZONE-01 -> RENDER-01 (+X-05) -> DRAW-01 (+STYLE-01, IMGAPI-01) -> SEAM-01
DRAW-01 + CHECK-01 + REVIEW-01 + SEAM-01 + LIC-01 -> BLOCK-01 (go/no-go) -> DAY-01
DRAW-01 -> FINISH-01 -> PYR-01 -> MAP-01 -> LIGHT-01 -> NIGHT-01
MAP-01 + D-10 -> WEATHER-01 -> WEATHER-02
MAP-01 -> PLANNER-01 -> X-04 ; MAP-01 + X-01 + X-02 -> TRANSIT-02
```

First things that can start with no dependency: STYLE-01, IMGAPI-01, LIC-01, R-06, X-05, X-01, X-02, D-11, I18N-01.

## 5. Tickets outside the 38 that are affected

- **DESIGN-001** (pending): `vault/01_PROYECTO/arquitectura.md` still describes the harness template. Its content should come from the spec's Architecture section (offline map build, static front end with tile viewer, small server, nightly job). Its criterion "rename `app/`" needs a decision on the stack (see Doubts).
- **CORE-001** (pending): "first end-to-end piece" can be read as the 3x3 block of tiles: render, draw, seams, pyramid, viewer. Suggest rewording once DESIGN-001 is written.
- **ONBOARD-001** (in progress) wrote objetivo.md for spec v3; SCOPE-002 above replaces it.

## 6. Updates after reading the latest spec and the 3x3 test

- Spec: added URL-hash state and share button (SHARE-01), `pixel art off` switch and clock control (MAP-01, LIGHT-01), `what is near` in the point panel (PREVIEW-01), event link (EVENTS-01), per-tile record and immutable versions (DRAW-01), flat-colour, palette-drift and seam-jump measures (CHECK-01), `how to draw, not what is there` prompts (STYLE-01).
- 3x3 test findings from Jose: zone cut to the Christmas core (4x4 or 5x5 tiles, ZONE-01, DAY-01); style crop and neighbour strip instead of whole tiles (DRAW-01); straight seams only, no AI corners (SEAM-01); colour matching and water in code (FINISH-01, WATER-01); at most 2 parallel calls with back-off (IMGAPI-01); LoRA only if more than 30 percent of tiles still fail (BLOCK-01); the old block is not valid, the chosen style is p-7/p-8 (STYLE-01).
- The viewer chain no longer waits for the drawn map: PYR-01 has no dependencies and works with placeholder tiles.

## 7. Doubts (not decided here)

1. **Zone.** The spec leaves the exact limits open. The zone decides tile count and cost. ZONE-01 cannot close without a decision from Jose.
2. **Which image model, who pays, and what is "no-go" for the 3x3 block.** The spec requires an API model but does not pick one. Provider terms for commercial use are not checked. The competition study found one third of seams visible in the tile-by-tile test of tiny.london, so BLOCK-01 needs its numeric threshold agreed before drawing, not after.
3. **Stack and AGENTS.md.** The repo is a Python harness (`app/`, `agents/` stdlib only). The spec needs a heavy offline pipeline (render, image calls), a static web front end and a small server. The repo does not say where each lives, nor whether `app/` becomes the pipeline. DESIGN-001 must decide it before RENDER-01.
4. **Tested prompts name contents.** The spec now says prompts say how to draw, not what is there, but p-7 and p-8 (the chosen style) mention granite facades, miradores and terracotta roofs. STYLE-01 tests a content-free variant; if it loses the look, the content words stay and the decision is recorded.
4b. **Tile scale.** Spec: about 0.3 m per pixel (1024 px is about 300 m). The 3x3 test used 2 px/m (1024 px is 512 m). ZONE-01 must pick one; it changes the number of tiles of the core zone.
5. **R-01 effort.** The old R-01 asks for at least 3 sources per point from scratch. With the 43-point layer as base, is one source (the layer) enough for unchanged points and 3 only for changed ones?
6. **Traffic and parking.** Spec lists "traffic" under datos.vigo.org but the F1 layers do not include it (cars on the map are decoration). X-08 is proposed out of v1. Parking is a layer (D-05 stays) but the planner parking hint (D-12) and the parking block in the point panel are not in the spec.
7. **Cercanías.** X-02 asked for Cercanías static GTFS too. The spec only names AV/LD/MD and says Cercanías live feeds are not confirmed for Vigo. Removed from X-02, to confirm.
8. **Planner determinism.** The old criterion said weather only changes summary text. The spec says the planner can favour covered or indoor stops when rain is expected, which can change the order. Same input must still give the same routes; is weather part of the input? D-12 and PLANNER-01 assume yes.
9. **Share-view URL (hash).** Not in the spec; the study recommends it (lesson 4). Not added; propose adding to MAP-01 if the team agrees.
10. **Frame rate.** "Steady frame rate on a mid-range phone" has no number and no reference phone. Proposed >=30 fps; reference device to choose.
11. **Hosting.** Object storage, CDN and server host are not chosen; part of DESIGN-001.
12. **Season end date** (spec open question) decides how long R-05 weekly checks run.
