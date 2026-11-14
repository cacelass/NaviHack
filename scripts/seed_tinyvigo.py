"""Siembra los tickets de TinyVigo (spec v3) en GEAS. Idempotente por id."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/cancelas/NaviHack")
sys.path.insert(0, str(ROOT))

from agents.agents import geas_backlog as gb

# (id, title, description, criteria[], depends_on[])
TICKETS = [
    # ---- Part A: research / data (R) ----
    ("R-01", "Master research of all Christmas attractions",
     "Build the candidate list from last year's points, the 2026-27 official programme, Turismo de Vigo, press, social profiles, Google Maps/Street View, OSM, listings and blogs. For each point compare several websites recording source, date, location and schedule; resolve conflicts per F2 protocol; produce points.json and the research log.",
     ["Candidate list built from all listed sources",
      "Each point has >=3 sources recorded (or on-site check)",
      "Conflicts resolved with the documented priority order",
      "points.json and research log committed",
      "Every shown point has status above 'unverified'"], []),
    ("R-02", "Landmarks first: verify 6 landmark points",
     "Verify location and schedule of Porta do Sol tree, Alameda, Garcia Barbon street, Vialia attractions (ferris wheel at new location), Cies Market stalls (new location), new Disney items, with on-site checks. Unlocks the first scenes.",
     ["6 landmark points verified on site with dated photos",
      "Coordinates placed by hand on satellite with accuracy noted",
      "Schedule confirmed from official 2026-27 programme",
      "Scene generation unblocked for these 6"], ["R-01"]),
    ("R-03", "On-site visit: dated photos and GPS of every point",
     "Take dated photos and GPS positions of every point reachable on foot. Feeds F3 scenes and story cards.",
     ["Dated photo per point",
      "GPS position recorded where reachable",
      "Photos stored and referenced in points.json",
      "Copyright status noted (own photos preferred)"], ["R-01"]),
    ("R-04", "Collect official 2026-27 programme into points.json",
     "Opening days, hours, show times, prices and closures for every point loaded into points.json.",
     ["Programme fields populated for every point",
      "Show times with clock times where available",
      "Closed dates recorded",
      "last_verified updated"], ["R-01"]),
    ("R-05", "Weekly re-verification during the season",
     "Re-verify dataset before launch and weekly during season, after any Concello announcement. Update last_verified and log.",
     ["Re-verification cadence documented",
      "last_verified within 7 days for shown points",
      "Log of changes kept",
      "Schedule changes reflected in points.json"], ["R-01"]),
    ("R-06", "Locate Concello Christmas layer (optional baseline)",
     "Try portal search API (nadal, luces, atracciones, photocall, mercado) one request at a time; then network requests of official map; then request channel. Only a starting checklist.",
     ["Search attempted and outcome documented",
      "If found: URL recorded and layer compared to points.json",
      "If not found: documented as not blocking v1",
      "No dependency created on this layer"], []),

    # ---- Part A: data infra (D) ----
    ("D-00", "Measure real refresh rate and terms of Concello feeds",
     "Measure real refresh rate, CORS, payload size, availability and terms for car parks and agenda feeds. Sets snapshot intervals.",
     ["Refresh rate measured for parkings-ocupacion.json",
      "Refresh rate measured for agenda-hoy.json",
      "CORS headers recorded",
      "Terms/licence noted",
      "Intervals in A7 updated with measured values"], []),
    ("D-01", "Snapshot publisher",
     "Scheduled job: fetch feed, validate payload, write timestamped static snapshot with fetched_at and source timestamp, append history row, keep last-good on failure, expose age to app.",
     ["Job runs on schedule (cron/systemd timer)",
      "Bad payloads rejected, previous good kept",
      "Snapshot includes fetched_at and source timestamp",
      "History file appended",
      "App shows age and 'no data' after threshold"], ["D-00"]),
    ("D-03", "Agenda loader",
     "Nightly fetch of agenda-hoy.json; identify which dataset serves future days; build own history if none does.",
     ["agenda-hoy.json fetched nightly",
      "Future-days dataset identified (or history built)",
      "Clock times sourced from points.json, not agenda",
      "Events without time show 'time to be confirmed'"], ["D-00"]),
    ("D-04", "Venue join for agenda events",
     "Join instalacion to CKAN venue datasets, with name and address fallbacks; unmatched-event report.",
     ["Join by instalacion id implemented",
      "Fallback by venue name",
      "Fallback by direccion text",
      "Unmatched events logged",
      "Events without location shown in list only"], ["D-03"]),
    ("D-05", "Car park layer",
     "Snapshot, stale detection, map layer and detail in point panel.",
     ["12 car parks shown with free spaces and percent",
      "Last update time shown",
      "Stale car park shown as 'no data'",
      "Detail in point panel (nearest car park)"], ["D-01"]),
    ("D-10", "Weather (Open-Meteo)",
     "Open-Meteo snapshot, status strip, hourly rain for the planner.",
     ["Now + next 6 hours shown",
      "Rain probability for route window",
      "Last-good fallback with age",
      "Strip hides itself if feed fails"], ["D-01"]),
    ("D-11", "Elevation: MDT05 slope layer",
     "CNIG MDT05 slope layer for 'Easy walk' route.",
     ["Slope data loaded for Vigo centre",
      "Consumed by planner's Easy walk option",
      "Missing data handled gracefully"], []),
    ("D-12", "Planner signals and weights",
     "Weights for After dark and Easy walk, rain and parking hints in the summary.",
     ["After dark uses light hours and avoids unlit stretches",
      "Easy walk uses slope and benches/cafes",
      "Rain hint in summary",
      "Parking hint when occupancy >90%",
      "Missing signals reported, not fatal"], ["R-04", "D-05", "D-10", "D-11"]),
    ("D-17", "About screen with attributions",
     "Credits for OSM, IGN, Concello (ODC-BY) and other sources.",
     ["All data sources credited",
      "Licences shown",
      "Reachable from main UI"], []),
    ("D-18", "Freshness UI",
     "Per-layer last-updated time and per-point last-verified date and status.",
     ["Each data layer shows last update",
      "Each point shows last_verified and status",
      "Stale state visually distinct"], ["D-05", "R-01"]),

    # ---- Part A: product features ----
    ("MAP-01", "Base map: satellite + night, points, lights schedule",
     "PNOA orthophoto base with pan/zoom. Two base modes (Satellite, Night: darkened+tinted with lights on at real hours). Points as pixel-art sprites. Layers toggle: points, events, car parks (points+events on by default).",
     ["Satellite base pans smoothly on mid-range phone",
      "Night mode darkens and tints, lights on at Concello schedule",
      "Points rendered as sprites at researched coords",
      "Layer toggles work",
      "First view loads under 3s on 4G (to be measured)",
      "No plain-HTTP or direct city-feed request from browser"], ["R-01"]),
    ("SCENES-01", "Generate scenes for 6 landmarks",
     "Prove the look: generate pixel-art scenes for the 6 landmarks using real photo + satellite crop + style reference. Review against photo before shipping.",
     ["6 landmark scenes generated",
      "Each reviewed against real photo",
      "Invented/identity-changing elements rejected and redone",
      "Style matches reference look (warm night, chunky pixels, no thin outlines)",
      "Scenes stored as images with prompt and source photo"], ["R-02"]),
    ("PREVIEW-01", "Point preview panel",
     "Tap a point: scene, real photo one tap away, schedule today+next days and on-now, story card, walk directions + add-to-route, nearest car park with occupancy and update time, confirmation status and last_verified date.",
     ["Panel opens on tap",
      "Scene and real photo both available",
      "Schedule and on-now state shown",
      "Story card shown",
      "Walk directions and add-to-route button",
      "Nearest car park occupancy + update time",
      "Confirmation status and last_verified shown"], ["R-02", "D-05"]),
    ("STORY-01", "Story cards for Christmas points",
     "3-5 sentence story per point about the tradition. Set of cards tells the history of Christmas in Vigo. Every historical claim has a source link; unsourced cards not shown.",
     ["Card per shown point",
      "3-5 sentences each",
      "Every historical claim sourced",
      "Cards read in order tell Vigo Christmas history",
      "Unsourced cards hidden"], ["R-01", "R-03"]),
    ("EVENTS-01", "Events UI (list + map layer)",
     "Daily events list and map layer, date picker for next days, filters (date, time of day, category, free, near me), permanent items and cycles grouped, add-to-route.",
     ["Events list and map layer",
      "Date picker for future days",
      "Filters work",
      "Permanent/cycle items grouped",
      "Add-to-route button",
      "Events without clock time show 'time to be confirmed'"], ["D-04"]),
    ("PLANNER-01", "Route planner (walking, 3 options)",
     "Input start + time window + chosen stops. Output 3 options (fastest, after dark, easy walk) with total time, distance, ordered stops and plain explanation. Events as time windows. Pedestrian graph from OSM. Exact search up to ~12 stops. Missing stop reported, not silently skipped.",
     ["3 options returned for same input",
      "Deterministic order (weather/parking hints only change summary text)",
      "Event pinned at 20:00 -> no option arrives after 20:00",
      "Unreachable stop reported with drop suggestion",
      "Answers in under 2s for 12 stops",
      "Walking times from OSM pedestrian graph"], ["D-12"]),
    ("POSTCARD-01", "Postcard pipeline and UI",
     "Upload/take photo, pick place, optional message+name -> pixel-art postcard. Vision model describes photo as structured data (no identification). Image model draws person in scene. Frame/title/name/message added in code. PNG download + share. Credit line + date. Daily per-device limit and monthly spending cap. Photo and result not kept unless user opts in. Notice about third-party model.",
     ["Photo upload/capture works on mobile",
      "Place picker from Christmas points",
      "Vision description is structured, no identification",
      "Person drawn in scene in pixel style",
      "Frame/title/name/message added in code, not by model",
      "PNG download and share",
      "Daily per-device limit enforced",
      "Monthly spending cap enforced",
      "No server-side retention unless opted in",
      "Notice about third-party model shown"], ["SCENES-01"]),
    ("I18N-01", "Galician/Spanish/English strings",
     "All UI strings externalised; no hard-coded text.",
     ["Strings in gl/es/en",
      "No hard-coded user-facing strings",
      "Language switch works"], []),

    # ---- Part B: extras ----
    ("X-01", "Vitrasa GTFS ingest",
     "Stops, lines, timetables; 'scheduled' labelling; cross-check with Christmas mobility plan (cancelled stops).",
     ["GTFS ingested (stops, lines, timetables)",
      "Labelled 'scheduled', not live",
      "Cancelled Christmas stops cross-checked",
      "No dependency on unofficial real-time wrappers"], []),
    ("X-02", "Renfe static GTFS ingest",
     "Ingest long-distance and Cercanias GTFS; check Vigo stops present.",
     ["Long-distance GTFS ingested",
      "Cercanias GTFS ingested",
      "Vigo-Urzáiz and Vigo-Guixar present",
      "Stops listed"], []),
    ("X-03", "Renfe live feasibility check",
     "Test whether real-time feeds cover Vigo; go/no-go decision.",
     ["Trip-update and vehicle-position endpoints tested for Vigo",
      "Coverage documented",
      "Go/no-go recorded",
      "Protobuf decoding handled or noted as blocker"], ["X-02"]),
    ("X-04", "Transit legs in planner + next departures",
     "Walking+bus transit legs in planner; next departures at nearest stop/station in point panel.",
     ["Transit leg option in planner",
      "Next departures shown in point panel",
      "Bus stop and train station layers on map"], ["X-01", "X-02"]),
    ("X-05", "Buildings: 3D footprint + height layer",
     "Read FeatureServer in pages, reproject EPSG:25829->WGS84, check GeoJSON for MultiPatch, altura completeness and licence; export offline footprint+height file; fallback Catastro footprints joined by refcat.",
     ["Pagination implemented (<=2000 records/request)",
      "Reprojection to WGS84 correct",
      "GeoJSON MultiPatch feasibility documented",
      "altura completeness measured",
      "Licence recorded",
      "Offline file exported",
      "Fallback documented"], []),
    ("X-06", "Busy-now estimate prototype",
     "Coarse per-zone busy estimate (quiet/normal/busy) from car park occupancy, traffic, agenda, weekday/holiday, weather, Celta matches. Labelled 'estimate', hides if >=2 inputs missing.",
     ["3 levels per zone",
      "Inputs combined",
      "Word 'estimate' always visible",
      "No person counts shown",
      "Hides itself if >=2 inputs missing",
      "Celta home match dates considered"], ["D-01", "D-05", "D-03"]),
    ("X-07", "MITMA OD analysis for Vigo",
     "Typical December flows into the centre from MITMA mobile data to seed busy estimate.",
     ["MITMA CSVs acquired for Vigo",
      "December flows into centre extracted",
      "District granularity documented",
      "Fed into X-06"], []),
    ("X-08", "Traffic layer",
     "Inspect treal.geojson; render segments or fall back to city-wide indicator.",
     ["treal.geojson inspected and usability documented",
      "Segments rendered if usable, else city-wide indicator",
      "Source freshness shown"], ["D-01"]),
    ("X-09", "Cameras via server or links only",
     "Fetch camera images through server if terms allow, else outbound links.",
     ["Terms checked",
      "Either proxied images or links implemented",
      "61 cameras with location shown"], ["D-00"]),
    ("X-10", "DGT DATEX II incidents",
     "Road incidents on access roads (AP-9, A-55, A-52) from DGT NAP v3.7.",
     ["v3.7 feed parsed",
      "Incidents shown for access roads",
      "Refresh every 5 min",
      "City streets excluded"], ["D-01"]),
    ("X-11", "Concello notices in alerts list",
     "t-avisos and t-avisos-transporte notices about closures during events/parades.",
     ["Both datasets ingested",
      "Notices shown in alerts list",
      " closures during events highlighted"], ["D-01"]),
    ("X-12", "Enumerate Concello map services",
     "Use portal search API one request at a time to list useful services; add to catalogue.",
     ["Search run politely (one request at a time, back-off)",
      "Useful services recorded with URLs",
      "Catalogue updated"], []),
    ("X-13", "Weather backups and tides",
     "AEMET OpenData and MeteoGalicia MeteoSIX with failover; tides for coastal walks.",
     ["AEMET failover works",
      "MeteoSIX failover works",
      "Active source shown in UI",
      "Tides shown for coastal walks"], ["D-10"]),
    ("X-14", "TomTom traffic tiles (optional)",
     "Flow and incident tiles behind caching; attribution; stay within free tier.",
     ["Tiles render with attribution",
      "Caching proxy keeps within 50k/day",
      "429 handled gracefully"], ["D-01"]),
]

def main():
    root = ROOT
    # load existing ids
    existing = {t.get("id") for t in gb.tickets(root)}  # by ticket uuid; filter by feature id below
    existing_fids = {gb.feature_id(t) for t in gb.tickets(root)}
    print("existentes:", sorted(existing_fids))

    # topological add
    pending = list(TICKETS)
    added = []
    failed = []
    # track added feature ids
    added_ids = set(existing_fids)
    # repeat until no progress
    changed = True
    rounds = 0
    while pending and changed:
        changed = False
        rounds += 1
        still = []
        for fid, title, desc, crit, deps in pending:
            if fid in added_ids:
                continue
            if all(d in added_ids for d in deps):
                try:
                    created = gb.create_feature(
                        root, feature_id=fid, title=title, description=desc,
                        criteria=crit, depends_on=deps, priority=0,
                    )
                    added.append(fid)
                    added_ids.add(fid)
                    changed = True
                    print(f"OK {fid} -> {str(created.get('id',''))[:8]}")
                except Exception as exc:
                    failed.append((fid, str(exc)))
                    still.append((fid, title, desc, crit, deps))
            else:
                still.append((fid, title, desc, crit, deps))
        pending = still

    if pending:
        print("\nPendientes por dependencia no resuelta:")
        for fid, title, desc, crit, deps in pending:
            print(f"  {fid}: deps={deps} (faltan: {[d for d in deps if d not in added_ids]})")
    if failed:
        print("\nFallidos:")
        for fid, err in failed:
            print(f"  {fid}: {err}")

    # refresh mirror once
    try:
        from agents.agents import harness_agent as ha
    except Exception:
        pass
    print(f"\nAñadidos: {len(added)} | Pendientes: {len(pending)} | Fallidos: {len(failed)}")

if __name__ == "__main__":
    main()
