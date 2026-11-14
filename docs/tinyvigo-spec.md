# TinyVigo: spec

Status: draft.

## Summary

TinyVigo is an isometric pixel-art map of Vigo, in the family of tiny.london, isometric.nyc, tinygyn and tinyrj. You pan and zoom over the whole centre of the city, drawn like a SimCity 2000 board. On top of it sit Vigo's Christmas: every lit installation, market, ride and show, with its real schedule and a short story. From any starting point the app proposes walking routes through the points you pick, adds the day's events to the route, and shows buses and trains. At the end you can turn a photo of yourself into a pixel-art postcard of Vigo.

It is built for people walking around the centre with a phone, in the evening, so it has to work on mobile first.

## How these maps work

What the user sees is a set of images, not a 3D model and not an AI running live. The whole city is drawn once, offline, as pixel art, cut into small square tiles at several zoom levels, and served as plain image files. The browser downloads only the tiles that fit on screen, like any web map. Everything that moves or changes (cars, buses, lights, markers, routes) is code drawn on top of the picture.

AI is used only to create the images, before launch. The only live AI feature is the postcard (F7).

## Approach

### What we take from existing maps

- From tiny.london: a tile pyramid of small WebP tiles in a deep-zoom viewer, a first view that loads fast because its tiles are precomputed and downloaded in parallel, search over places and stations, and a plain statement of what is not live.
- From Tiny Lisbon, the closest one: a "what's on" layer fed by the city's cultural agenda with a shareable link per event, a "near this point" panel, and day light, weather and transit as layers.
- From Tiny Stockholm: switches for each layer, a clock with fast-forward, and an honest label saying that vehicles follow the timetable and are not live. A "pixel art off" switch shows the photo of the same place.
- From Tiny Prague: a route planner with stops, walking elevation profile and transit, with no sign-up.
- From Tiny Rome and Kraków en pixeles: story cards with a citation and a source.
- From Isopolis: the view, selection and tour step kept in the URL hash so any state can be shared, and a postcard made on a canvas with the text set in code.

What none of them combine is Christmas, timed routes, the day's events and a postcard with your own photo on one isometric map of one city.

### Drawing the city

1. **Render.** An orthographic camera tilted 45 degrees and turned 15 degrees (the angle all the tiny maps share) renders Vigo from open data into a grid of 1024 px tiles. Ground is the PNOA orthophoto, geometry is the Concello's 3D buildings, streets and shops come from OpenStreetMap. At about 0.3 m per pixel a tile covers roughly 300 m. The render also writes a height map and a building-id map for every tile, used later for shadows, occlusion and clicks.
2. **Draw.** An image model with image input redraws each render tile as pixel art. Each call gets the render, a fixed style reference and, when they exist, the already drawn neighbours. The prompt fixes the style, asks for unlit neutral rendering with no cast shadows, and forbids moving, adding or removing buildings, streets and trees. The prompt says how to draw (style, scale, rules), not what is there. Describing contents (for example "granite facades and red tile roofs") makes the model paint them where they do not exist. What is there comes from the render and from the tile notes.
3. **Seams.** Tiles drawn separately disagree at the edges. For every seam, a strip made of the right half of one tile and the left half of the next is built, the outer parts are tinted transparent red, and the model redraws only the untinted middle so that it joins both sides. The result is blended back with a soft fade at its edges. The same is done for every corner where four tiles meet. A block of 9 by 9 tiles needs 81 tile drawings, 144 seam drawings and 64 corner drawings.
4. **Check.** Automatic checks compare each drawing with its render and with OpenStreetMap, and reject copies of the photo, buildings invented on open water, and silhouettes that moved. The measures include the share of flat-colour pixels compared with the render (to catch drawings that just copy the aerial photo), per-tile colour statistics (to catch palette drift between tiles), and a jump metric on every seam. A person reviews contact sheets (a crop of the drawing next to its render) and flags tiles to redo. The model cannot reliably judge its own seams and invented details, so this step is not automated away.
5. **Targeted fixes.** The batch draws the whole city the same way, but not every place deserves the same treatment. Three tools go back over the map one place at a time:
   - Tile notes. A tile can carry reference photos and a written description of a landmark (its shape, which way it opens, its roof). Every drawing of that tile receives them. This is for buildings such as the cathedral, the Sireno or the main squares.
   - Outdated zones. The base data is not all from the same year, so new buildings, works and demolished blocks do not match the city today. The outdated area is outlined, redrawn from a more recent image of that spot, and blended into the rest with a soft edge.
   - Colour guide for uniform areas. Parks, fields and wooded slopes drawn tile by tile can differ in tone from one tile to the next, because tiles a few squares apart never see each other. The whole area is drawn once as a single picture, and then each tile is redrawn using its piece of that picture as a colour guide.
6. **Finishing.** A fixed stack of colour and contrast filters is applied in code to every tile as soon as it is drawn, and re-applied to the whole map when the stack changes, so the finished look is the same everywhere and can be tuned in one place.
7. **Water.** The ría is not drawn by the model. One sea texture is repeated across the map and coloured in code, with coastlines from OpenStreetMap. Boats and surf are kept from the drawing.
8. **Night and weather.** Not drawn by the model. Night is made in code from the day tiles, and weather is a set of code layers (see "Time of day and weather"). Only the day map is painted. The base map never contains seasonal installations: the Christmas elements are separate assets (see F2).

Fidelity is a limit and it is stated plainly. Positions, heights, streets and footprints are real. Facade details, window patterns and roof materials are drawn by the model, so they are plausible and not exact.

### What is not used

Google's Photorealistic 3D Tiles, which most of the tiny maps start from, are not available for projects billed in the European Economic Area, so they cannot be the input. The map starts from open data instead. Because that input has plain walls, it can be enriched: PNOA LiDAR for heights of trees and roofs, Catastro building parts (number of floors per volume), and the Catastro facade photo of each building, read by a vision model as plain text attributes (colour, material, galleries, shops at ground level). These enrichments are optional and each one is added only if it measurably reduces invented details.

### Fall-back if the API approach has problems

The default is the API approach described above. Drawing tile by tile with a general model can leave small style differences between tiles, and only if that cannot be solved with the style reference, the seam redraws and review, the fall-back is the method used by tiny.london and isometric.nyc: use the general model to draw a few hundred examples, check them automatically, train a small style model (a LoRA) on them on a rented GPU, and draw the whole city as one image with overlapping windows so that seams cannot form. This costs a few hours of rented GPU (the references report a few dollars per hour) and a lot more engineering, and the style model licences have to be checked first, since some are research-only. It is a plan B and is not part of the default plan.

## Look and feel

The map is isometric (2:1) in a modern high-bit pixel-art style, in the spirit of Eastward or Octopath Traveler: rich tones, fine detail on roofs, windows, balconies and cobbles, hard pixel edges, no thin anti-aliased outline around every object, and a clear difference between roofs, walls and ground.

The painted tiles are drawn unlit. Light is not part of the painting, because sun, shadows and time of day are added in code. The day tiles use flat neutral daylight with no cast shadows, no warm tint and no glow, only a little ambient occlusion in the narrowest streets, and each visible face of a building (roof, left wall, right wall) has its own gentle fixed tone so volumes stay readable. Colours are neutral and slightly desaturated so a grade can be applied on top. Streets, squares and the ría must read at a glance when zoomed out, and buildings must be recognisable as Vigo at street level: granite facades, white glass galleries (miradores), terracotta and dark grey roofs.

At street zoom at night, the map should feel like this reference scene. An isometric view from about 45 degrees above, of a cobbled Galician square. A large Christmas tree covered in warm white lights with a golden star stands in the middle. Around it are four- and five-storey granite buildings with dark red tile roofs and dormer windows. White galleries glow yellow from inside, and wrought-iron balconies and ground-floor arcades add detail. Garlands of small warm bulbs hang between the buildings and the lamp posts. Wooden market stalls with red-lit goods sit near the tree, with benches and ornate black street lamps casting round halos. Wet cobblestones reflect the lights. About twenty tiny people in coats and hats, some with umbrellas, are scattered over the square.

Rules that hold at every zoom:

- Warm night: deep navy and brown shadows, golden light from windows, lamps and garlands.
- Hard-edged chunky pixels, a limited palette, a little dithering on wet ground and roofs.
- Small life: people, cars, boats, stalls.
- One style for everything: the map, sprites, icons, postcard and interface. No icons drawn in code next to painted art.
- Text is never drawn by the image model. Labels, titles and postcard captions are set in code with a pixel font.

What to avoid: pale flat ochre walls, terracotta roofs on everything, thin black outlines everywhere, and a look of a plain illustration.

The map is painted once, in daylight. Time of day and weather are applied on top of it in code, so the same tiles serve every hour and every kind of weather.

## Time of day and weather

### Time of day

The sun position for Vigo is computed from the clock, with sunrise and sunset. The map goes through day, golden hour, dusk, night and dawn as a continuous grading, not a switch between two images. A manual control lets the user pick any hour, which also shows what a route will look like later tonight.

Sunlight is computed in code over the unlit tiles. Using the height map, the sun position for the current hour casts shadows from every building and tree onto the ground and onto neighbouring walls, and the same shadows apply to moving sprites. Shadows therefore follow the sun through the day.

Night is made in code over the same tiles:

- A dark blue multiply tint, stronger as the sun goes down, with warm highlights on facades near lamps. Sun shadows fade out as the sun sets.
- Lit windows. The building footprints, heights and the camera are known, so the wall surfaces of every building can be computed and small warm lights placed on them, floor by floor. How many are lit depends on the hour (most in the evening, few after midnight), and the pattern is fixed per building so it does not flicker. Shops at ground level glow from their OpenStreetMap position.
- Halos on street lamps, placed along streets at a fixed spacing, and headlights on the moving cars.
- Christmas lights, sprites and garlands, which switch on at the Concello's real switch-on time and follow each installation's schedule.
- Stars, and the moon phase.

Limit: the windows drawn by the model will not line up exactly with the lit windows added in code. Lit windows are kept small and soft so that this does not show at map zoom, and they are tuned until it looks right.

### Weather

Weather comes from Open-Meteo (no key, current conditions plus an hourly forecast for the next days). Everything is an overlay in code, and none of it is painted into the tiles.

| Data | Effect on the map |
| --- | --- |
| Precipitation and weather code | Rain particles whose density grows from drizzle to heavy rain and whose slant follows the wind. Wet look: darker tint, light reflections and puddles on streets and squares only, using the ground mask from the height and building-id maps. Snow particles if it snows. Lightning flashes for thunderstorm codes. |
| Cloud cover (low, mid, high) | Cloud shadows drifting over the map at the wind speed and direction, plus a soft haze at high cover. |
| Visibility and fog codes | Fog that thickens with distance and over the ría. |
| Wind speed, direction and gusts | Swaying trees and flags, ripples in the sea texture, rain slant, cloud drift. |
| Sea state (Open-Meteo Marine, coverage of the ría to confirm) | Wave amplitude in the water texture. |
| Temperature | Shown in the interface, with no visual effect. |

Other rules:

- The forecast drives the hour control: choosing 21:00 tomorrow shows the expected weather and the state of the lights at that hour.
- A manual override lets anyone force rain, fog or any hour, for demos and for people who want to see the city under a given weather.
- The route planner warns when rain is expected during the route and can favour covered or indoor stops.
- MeteoGalicia, the regional agency, is a candidate for local observations and radar. Licence and API to check before using it.
- Effects switch off on low-end devices and respect the reduced-motion setting.

Acceptance: at load, the weather layer matches Open-Meteo's current conditions for Vigo; with rain forced at 21:00 the map keeps a steady frame rate on a mid-range phone.

## Features

### F1. Map

The pixel map, with pan, zoom, a mini-map and a search box for places, streets, stations and Christmas points. A toggle shows the real satellite view of the same area (the PNOA orthophoto) for orientation.

- Layers that can be toggled: Christmas points, events, buses, trains, parking, cameras, routes. Christmas points and events are on by default.
- Animated layers: lights at their real hours, cars moving by street, buses on their timetable, boats in the ría, animated Christmas installations (the ferris wheel turning, the tree's show), and the weather effects below.
- Shadows follow the real sun, using the height map. At street zoom a focus effect can follow the pointer to help read the slopes of the city.
- Clicking a building highlights it, using the building-id map.
- Everything shareable lives in the URL: view, zoom, layers, selected point or event, route and chosen hour. A link to any state can be sent by message. There is a share button with copy link and the phone's share sheet.
- A "pixel art off" switch shows the real photo of the same place for comparison.
- A clock control runs the hour forward faster (real time, ×10, ×60) to preview the lights and a route.

Acceptance: on a mid-range phone the map pans at a steady frame rate with the default layers on, and the first view shows something recognisable in under 3 seconds on 4G (to be measured). The tiles of the first view are precomputed and downloaded in parallel, the coarsest zoom levels are preloaded, and the map data the first view needs is baked into the page.

### F2. Christmas points and their story

Source: the Concello's ArcGIS layer, 43 points in these types: attractions, exhibits, light installations, photo galleries, Christmas markets, Santa and the Three Kings, photocalls. The layer is the 2025-26 edition. The 2026 changes (new ferris wheel location at Vialia, Cíes Market, ice rink, giant gifts) come from local press and sit in an editable overrides file until the Concello publishes them.

- Each point has name, type, short and long description, real photo, coordinates, schedule, and a pixel-art asset made from its photo, placed on the map at its real position and at a size that stays readable.
- Installations are separate assets on top of the map, never painted into the base tiles. They are temporary, the base data does not contain them (the 2026 ferris wheel stands in what the base data shows as a car park), they can be animated, they can be clicked, and they come and go with the season without redrawing any tile. An asset includes its own patch of ground so that it covers whatever the base shows underneath.
- Animation is done in code. The ferris wheel is drawn as a structure plus a single cabin, and the code places the cabins on an isometric ellipse and rotates them while the spokes blink. Light installations blink or pulse and the tree runs its show at the scheduled hours.
- Each point has a short story card of three to five sentences about where the tradition comes from or why it is there. Read in order, the cards tell the history of Christmas in Vigo.
- Every historical claim carries a source link. A card without a source is not shown. Cards are written from sources by us and reviewed, never published as raw model output.
- A point whose 2026 data comes only from the press is marked "not yet confirmed by the Concello".

### F3. Preview a point

Tap a point and the map flies to it at full zoom and a panel opens with:

1. The real photo and the pixel sprite side by side.
2. Schedule for today and the next days, and whether it is on now.
3. The story card.
4. What is near it: events today and other points within walking distance, each with its own link.
5. How to get there from the user's position, and a button to add it to the route.

For landmarks, an extra close-up illustration in the night reference style can be added later, drawn once from the real photo and reviewed against it. It is a bonus and not required for the first launch.

### F4. Daily events

A list and a map layer of what is happening today, with a date picker for the next days.

- Sources: the Concello's cultural agenda ("Today's Agenda", published as JSON, CSV and XLS on datos.gob.es) and the time slots inside the Christmas layer, such as the tree's music-and-light shows and parades.
- Filters: date, time of day, category, free entry, near me.
- Each event has a place, start and end time, a link that opens the map on it, and a button "Add to route". Added events become fixed-time stops.
- Events without coordinates are matched to a venue by name. If that fails they appear in the list but not on the map.

### F5. Route planner

Input: a starting point (the user's location, an address, or "I arrive at Vigo-Urzáiz station"), a time window ("tonight from 19:00 to 22:30"), the chosen stops (points and events), and how they move (walking, or walking plus bus).

Output: three route options, each with total time, walking distance, ordered stops and a plain explanation of what it optimises.

1. Fastest: shortest total time visiting all chosen stops.
2. After dark: light installations are visited when they are on, and daytime-only points first.
3. Easy walk: avoids the steepest streets and long stretches without a place to sit.

It is a small ordering problem (up to about 12 stops), so an exact search is enough. Events are time windows the route must respect. Walking times come from a pedestrian graph built from OpenStreetMap, and bus and train legs from the GTFS schedules (F6). If a chosen stop cannot be reached in time, the planner names it and proposes dropping it, instead of silently skipping it. The chosen route is drawn on the map as a line with numbered stops.

Acceptance: the same input always gives the same three routes; with an event pinned at 20:00 no option arrives after 20:00; it answers in under 2 seconds for 12 stops.

### F6. Trains and buses

- Buses: Vitrasa GTFS from the Concello. This is the timetable, not GPS positions, and the interface says "scheduled", not "live", on every moving vehicle and in the legend.
- Trains: Renfe GTFS for Alta Velocidad, Larga y Media Distancia (public zip, CC BY 4.0). It includes Vigo-Urzáiz and Vigo-Guixar.
- Live trains: Renfe publishes real-time feeds (vehicle positions, trip updates, alerts) on data.renfe.com. The Cercanías feeds respond, but it is not confirmed that they cover Vigo, and the URLs of the long and medium-distance feeds are not confirmed either. Verify both before showing anything live. Until then trains are scheduled only.
- On the map: bus lines in their colours, vehicles moving along them by timetable, stations and stops as icons with next departures, and transit legs inside the routes.

### F7. Postcard

The user uploads or takes a photo, picks a place from the Christmas points, and optionally writes a short message and a name. They get a pixel-art postcard of that place with themselves in it.

1. A vision model describes the photo as structured data: number of people, rough clothing and colours, pose, mood. No identification of anyone.
2. An image model receives the person photo, a crop of the map or the close-up of the chosen point, and the style reference, and draws the person in the scene in the same pixel style.
3. The frame, the title, the name and the message are added in code, never by the model.
4. The user saves the PNG, copies a link or uses the phone's share sheet. The postcard has a small credit line and the date.

Rules: the uploaded photo and the result are not kept on the server once the request ends, unless the user chooses to save. A short notice says the photo goes to a third-party model. Each device has a daily limit and the service has a monthly spending cap, because every postcard costs money.

## Data sources

| Data | Source | Status |
| --- | --- | --- |
| Satellite imagery and ground texture | PNOA orthophoto, IGN, CC BY 4.0 | Available |
| Heights of trees and roofs | PNOA LiDAR, IGN, CC BY 4.0 | Candidate enrichment |
| Streets, shops, coastline, water | OpenStreetMap, ODbL | Available |
| Building footprint, height, year, use | Concello de Vigo, "Edificios 3D" | Available |
| Floors per volume, facade photos | Catastro | Candidate enrichment; to verify coverage |
| Christmas points (43) | Concello ArcGIS Online, edition 2025-26 | Available |
| Christmas 2026 changes | Local press, OpenStreetMap, overrides file | Reload when the Concello publishes the 2026-27 layer |
| Cultural agenda | Concello via datos.gob.es, JSON/CSV/XLS | Exists; URL and fields to confirm |
| Vitrasa buses | GTFS from the Concello | Available, timetable only |
| Bus stops, traffic, parking, cameras | datos.vigo.org | Available |
| Renfe timetables | ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip | Available (includes both Vigo stations) |
| Renfe live | data.renfe.com, GTFS-RT | Cercanías feeds respond; Vigo coverage to confirm |
| Weather | Open-Meteo | Available |

The Concello's official 2026-27 Christmas programme was approved recently, so points and dates will change. The loader has to be re-run, and the app shows the date the data was last refreshed.

## Architecture

- **Map build (offline, run by us):** the render, the drawing, the seams, the checks and the tile pyramid, as separate scripts that can be re-run on any tile. A small internal tool shows which tiles are drawn and which need review, and lets us pick the next ones to draw. Long jobs can be resumed after a crash. Every tile keeps a record of its inputs, prompt, model, parameters, output and review status, and contact sheets put each drawing next to its render.
- **Front end:** a static site with a tile viewer (OpenSeadragon or similar, with pixelated scaling), the code layers, search and the panels. Tiles are 512 px WebP at several zoom levels, served from object storage behind a CDN. Published tiles are never overwritten: each version lives in its own folder with immutable caching.
- **Server:** a small service for the parts that cannot be static: route planning, event aggregation and postcards. It holds the model credentials, so none of them reach the browser.
- **Nightly job:** refreshes the Christmas layer, the agenda and the GTFS files and publishes them as plain files.

Decision needed before the postcard goes live: how the server authenticates and pays for the image model. A long-lived server credential has to be set up (an API key with prepaid balance, or a Vertex AI service account). Nothing else in the spec depends on this, but the map build also needs an image model with enough quota for a few hundred calls.

## Non-functional

- Mobile first, readable outdoors at night, one-handed. No heavy modes (flight, driving, games) and no long loading screens.
- Languages: Galician, Spanish, English. Strings are not hard-coded.
- UI text is real text with enough contrast against the dark map. Pixel art never carries information that is not also in text.
- Credits for OpenStreetMap, IGN, the Concello, Renfe and the image model provider on an About screen.
- No account, no tracking beyond privacy-friendly page counts.

## Out of scope for v1

- The whole metropolitan area. v1 covers the centre.
- Real GPS positions of Vitrasa buses (not published).
- Crowd or queue data (no open source exists).
- Ticket sales, bookings, user accounts.
- Games, missions, collectibles or multiplayer. They can come later.
- Anything outside Vigo and its Christmas season.

## Plan

The work is tracked as tickets in the team backlog, in this order. No time estimates.

1. **Style.** Fix the look: the high-bit style drawn unlit, with a reference prompt and a style reference image, and the code lighting (sun shadows from the height map, dusk and night grade, lit windows) applied over it. Light, night and weather are done in code, and the work here is to tune that code until it looks good on painted tiles.
2. **Render pipeline.** Grid over the chosen zone, tile render with height map and building-id map, and the optional enrichments added one at a time.
3. **A block of 3 by 3 tiles.** The method is fixed: an image model through its API, tile by tile, with seams and corners. Draw the block and check style consistency across tiles, visible seams and how many invented details survive the checks. The style-model fall-back (below) is considered only if a problem shows up that review and fixes cannot solve.
4. **Day map of the zone.** About 50 to 65 tiles and about 250 drawings with seams for an area of around 6 km², then review and fixes, including tile notes for the landmarks, redrawing the outdated zones and colour guides for uniform areas. Water in code, and the finishing filters applied to every tile.
5. **Light, night and weather in code.** Sun shadows, grading, lit windows, then the weather layers.
6. **Christmas assets.** The animated installation assets from the photos of the 43 points, placed in code, and the story cards (researched and written in parallel).
7. **Viewer and layers.** Tile pyramid, viewer, search, lights, vehicles, markers, building highlight.
8. **Routes, events and transit.**
9. **Postcard,** after the payment decision.

## Open questions

- Zone. The first launch should cover the area where the Christmas points are. Its exact limits decide the number of tiles and the cost.
- Who it is for first: tourists or people from Vigo. It changes the story cards and the default language.
- Name and domain. `tinyvigo` is a working name.
- Season end date. The Concello's closing date for the lights decides how long the project stays useful.
- Whether to submit it to isometriccities.com once it is online.
