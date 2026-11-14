"""Apply the TinyVigo backlog v4 (docs/propuesta-backlog-v4.md) to GEAS.

Idempotent. Dry-run by default; pass --apply to write.

  1. update the tickets that change (title, description, dependencies)
  2. create the missing tickets, in dependency order
  3. mark the tickets that leave v1 as out of scope (reason written in the
     description first, then cancelled: history is kept, nothing is deleted)

Needs an actor with ticket:create, ticket:update and ticket:cancel. The plain
`agent` role has none of them (it only starts/completes/blocks), so the first
write fails with FORBIDDEN and the script stops there.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from agents.agents import geas_backlog as gb  # noqa: E402
from agents.tools.geas_client import GeasError  # noqa: E402
from backlog_v4_tickets import TICKETS_CHANGED, TICKETS_NEW  # noqa: E402

OUT_OF_SCOPE = {
    "X-06": "Crowd or queue data has no open source and is out of scope for v1 (spec, Out of scope).",
    "X-07": "Only fed X-06 (busy-now estimate), which is out of scope for v1.",
    "X-08": "Traffic is not in the F1 layer list; cars on the map are decoration. Revisit if the team wants a traffic layer.",
    "X-10": "DGT road incidents are not in the spec.",
    "X-11": "Concello notices are not in the spec; the cancelled-Christmas-stops cross-check stays inside X-01.",
    "X-12": "The Concello Christmas layer is already identified in the spec; its useful part is absorbed by R-06.",
    "X-13": "AEMET failover and tides are not in the spec; MeteoGalicia licence check moves to LIC-01, sea state to D-10.",
    "X-14": "TomTom traffic tiles are not in the spec.",
}
MARK = "OUT OF SCOPE for v1 (backlog v4, spec docs/tinyvigo-spec.md):"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to GEAS (default: dry-run)")
    ap.add_argument("--root", default=str(ROOT), help="checkout whose .env holds the GEAS config")
    args = ap.parse_args()
    dry = not args.apply
    root = Path(args.root)

    client = gb.load(root)
    repo = gb.repository_id(root)
    items = gb.tickets(root)
    by_fid = {gb.feature_id(t): t for t in items}
    uuid_of = {fid: str(t["id"]) for fid, t in by_fid.items()}
    print(f"GEAS: {len(items)} tickets | mode: {'DRY-RUN' if dry else 'APPLY'}")

    def deps_uuid(deps: list[str]) -> list[str]:
        missing = [d for d in deps if d not in uuid_of]
        if missing:
            raise SystemExit(f"dependency not in GEAS yet: {missing}")
        return [uuid_of[d] for d in deps]

    # 1. changed tickets
    for fid, title, desc, crit, deps in TICKETS_CHANGED:
        t = by_fid.get(fid)
        if not t:
            print(f"  skip update {fid}: not in GEAS")
            continue
        if str(t.get("status", "")).upper() not in {"FREE"}:
            print(f"  skip update {fid}: status {t.get('status')} (not FREE)")
            continue
        # dependencies of changed tickets may point to tickets created in step 2
        wanted_title = f"{fid}: {title}"
        wanted_desc = gb.build_description(desc, crit)
        if t.get("title") == wanted_title and (t.get("description") or "").strip() == wanted_desc:
            print(f"  same   {fid}")
            continue
        print(f"  update {fid}")
        t["_pending"] = (wanted_title, wanted_desc, deps)

    # 2. new tickets, topological order (changed tickets' new deps resolved afterwards)
    pending = [x for x in TICKETS_NEW if x[0] not in by_fid]
    for fid in [x[0] for x in TICKETS_NEW if x[0] in by_fid]:
        print(f"  exists {fid}")
    rounds = 0
    while pending:
        rounds += 1
        still = []
        for fid, title, desc, crit, deps in pending:
            if all(d in uuid_of for d in deps):
                print(f"  create {fid}")
                if not dry:
                    try:
                        created = client.create_ticket(
                            title=f"{fid}: {title}",
                            description=gb.build_description(desc, crit),
                            repository_id=repo,
                            dependencies=deps_uuid(deps),
                            priority=0,
                        )
                    except GeasError as exc:
                        print(f"STOP at create {fid}: {exc}")
                        return 2
                    uuid_of[fid] = str(created.get("id") or created.get("ticket_id") or "")
                else:
                    uuid_of[fid] = f"dry-{fid}"
            else:
                still.append((fid, title, desc, crit, deps))
        if len(still) == len(pending):
            print("unresolved dependencies:", [(x[0], [d for d in x[4] if d not in uuid_of]) for x in still])
            return 3
        pending = still

    # changed tickets: write now that every dependency has a uuid
    for fid, t in [(f, t) for f, t in by_fid.items() if "_pending" in t]:
        title, desc, deps = t.pop("_pending")
        if not dry:
            try:
                client.update_ticket(str(t["id"]), {"title": title, "description": desc, "dependencies": deps_uuid(deps)})
            except GeasError as exc:
                print(f"STOP at update {fid}: {exc}")
                return 2

    # 3. out of scope
    for fid, reason in OUT_OF_SCOPE.items():
        t = by_fid.get(fid)
        if not t:
            continue
        if str(t.get("status", "")).upper() == "CANCELLED":
            print(f"  already out of scope {fid}")
            continue
        print(f"  out of scope {fid}")
        if not dry:
            body = (t.get("description") or "")
            if MARK not in body:
                body = f"{MARK} {reason}\n\n{body}"
            try:
                client.update_ticket(str(t["id"]), {"description": body})
                client.cancel_ticket(str(t["id"]), f"out of scope for v1: {reason}")
            except GeasError as exc:
                print(f"STOP at cancel {fid}: {exc}")
                return 2
    print("done" if not dry else "dry-run finished, nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
