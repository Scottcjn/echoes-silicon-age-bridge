#!/usr/bin/env python3
"""
Extended proof-of-function validation for provenance workflow.

Live data streams:
1) NYC Archaeology Reports Database
2) Cleveland Museum of Art Open Access API
3) Art Institute of Chicago API

Validation includes:
- Baseline vs provenance integrity metrics
- Tamper detection (hash drift)
- Lineage break detection
- Parent-link mismatch detection
- Reproducible root-hash checks
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


ROOT = Path("/home/scott/jcaa_experiments_2026-02-19")
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def http_get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    r = requests.get(
        url,
        params=params,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (compatible; jcaa-provenance-validation/1.0)"},
    )
    r.raise_for_status()
    return r.json()


@dataclass
class StreamData:
    name: str
    source_url: str
    mandatory_fields: list[str]
    records: list[dict[str, Any]]
    fetch_seconds: float


def load_nyc(limit: int = 300) -> StreamData:
    t0 = time.perf_counter()
    url = "https://data.cityofnewyork.us/resource/fuzb-9jre.json"
    rows = http_get_json(url, params={"$limit": limit})
    records: list[dict[str, Any]] = []
    for row in rows:
        records.append(
            {
                "biblioid": str(row.get("biblioid", "")),
                "borough": str(row.get("borough", "")),
                "author": str(row.get("author", "")),
                "date": str(row.get("date", "")),
                "title": str(row.get("title", "")),
                "report_abstract": str(row.get("report_abstract", "")),
            }
        )
    return StreamData(
        name="nyc_archaeology_reports",
        source_url=url,
        mandatory_fields=["biblioid", "borough", "author", "date", "title"],
        records=records,
        fetch_seconds=time.perf_counter() - t0,
    )


def _cma_query(query: str, limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    skip = 0
    while len(out) < limit:
        take = min(100, limit - len(out))
        js = http_get_json(
            "https://openaccess-api.clevelandart.org/api/artworks/",
            params={"q": query, "limit": take, "skip": skip},
        )
        rows = js.get("data") or []
        if not rows:
            break
        out.extend(rows)
        skip += len(rows)
    return out


def load_cma(limit: int = 200) -> StreamData:
    t0 = time.perf_counter()
    raw = _cma_query("roman", limit // 2) + _cma_query("egyptian", limit - (limit // 2))
    seen = set()
    records: list[dict[str, Any]] = []
    for obj in raw:
        oid = obj.get("id")
        if oid in seen:
            continue
        seen.add(oid)
        culture = obj.get("culture", "")
        if isinstance(culture, list):
            culture = "; ".join(str(x) for x in culture)
        records.append(
            {
                "objectID": str(obj.get("id", "")),
                "department": str(obj.get("department", "")),
                "title": str(obj.get("title", "")),
                "culture": str(culture),
                "objectDate": str(obj.get("creation_date", "")),
                "accessionNumber": str(obj.get("accession_number", "")),
                "objectURL": str(obj.get("url", "")),
            }
        )
        if len(records) >= limit:
            break
    return StreamData(
        name="cleveland_museum_ancient_collections",
        source_url="https://openaccess-api.clevelandart.org/api/artworks/",
        mandatory_fields=["objectID", "department", "title", "culture", "objectDate", "accessionNumber"],
        records=records,
        fetch_seconds=time.perf_counter() - t0,
    )


def _aic_query(query: str, limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    page = 1
    while len(out) < limit:
        take = min(100, limit - len(out))
        js = http_get_json(
            "https://api.artic.edu/api/v1/artworks/search",
            params={
                "q": query,
                "limit": take,
                "page": page,
                "fields": "id,title,date_display,place_of_origin,main_reference_number,api_link",
            },
        )
        rows = js.get("data") or []
        if not rows:
            break
        out.extend(rows)
        page += 1
    return out


def load_aic(limit: int = 200) -> StreamData:
    t0 = time.perf_counter()
    raw = _aic_query("roman", limit // 2) + _aic_query("egyptian", limit - (limit // 2))
    seen = set()
    records: list[dict[str, Any]] = []
    for obj in raw:
        oid = obj.get("id")
        if oid in seen:
            continue
        seen.add(oid)
        records.append(
            {
                "id": str(obj.get("id", "")),
                "title": str(obj.get("title", "")),
                "date_display": str(obj.get("date_display", "")),
                "place_of_origin": str(obj.get("place_of_origin", "")),
                "main_reference_number": str(obj.get("main_reference_number", "")),
                "api_link": str(obj.get("api_link", "")),
            }
        )
        if len(records) >= limit:
            break
    return StreamData(
        name="aic_ancient_collections",
        source_url="https://api.artic.edu/api/v1/artworks/search",
        mandatory_fields=["id", "title", "date_display", "place_of_origin", "main_reference_number"],
        records=records,
        fetch_seconds=time.perf_counter() - t0,
    )


def transform_naive(rec: dict[str, Any], stream_name: str) -> dict[str, Any]:
    # A minimal derivative output without provenance fields.
    if stream_name == "nyc_archaeology_reports":
        return {"summary": f"{rec['title']} ({rec['date']})"}
    if stream_name == "cleveland_museum_ancient_collections":
        return {"summary": f"{rec['title']} | {rec['culture']} | {rec['objectDate']}"}
    if stream_name == "aic_ancient_collections":
        return {"summary": f"{rec['title']} | {rec['date_display']} | {rec['place_of_origin']}"}
    return {"summary": json.dumps(rec, ensure_ascii=True)[:180]}


def transform_provenance(rec: dict[str, Any], mandatory_fields: list[str], parent_hash: str, generated_at: str) -> dict[str, Any]:
    out = {
        "generated_label": "DERIVED_RECORD",
        "generated_by": "deterministic_transform_v2",
        "generated_at": generated_at,
        "parent_sha256": parent_hash,
        "summary": "",
    }
    for f in mandatory_fields:
        out[f] = rec.get(f, "")
    return out


def set_summary(derivative: dict[str, Any], source: dict[str, Any], stream_name: str) -> None:
    derivative["summary"] = transform_naive(source, stream_name)["summary"]


def lineage_complete(derived: dict[str, Any]) -> bool:
    for k in ("generated_label", "generated_by", "generated_at", "parent_sha256"):
        if not derived.get(k):
            return False
    return True


def audit_record(
    source_hashes: set[str],
    source_by_hash: dict[str, dict[str, Any]],
    derived: dict[str, Any],
    mandatory_fields: list[str],
) -> bool:
    # Core audit policy for this proof-of-concept:
    # 1) Required lineage metadata is present.
    # 2) parent_sha256 points to known source.
    # 3) Mandatory context fields are preserved exactly from source.
    if not lineage_complete(derived):
        return False
    parent = str(derived.get("parent_sha256", ""))
    if parent not in source_hashes:
        return False
    src = source_by_hash.get(parent)
    if not src:
        return False
    for f in mandatory_fields:
        if str(derived.get(f, "")) != str(src.get(f, "")):
            return False
    return True


def context_retention(source: dict[str, Any], derived: dict[str, Any], mandatory_fields: list[str]) -> float:
    if not mandatory_fields:
        return 0.0
    kept = 0
    for f in mandatory_fields:
        if str(source.get(f, "")) != "" and str(source.get(f, "")) == str(derived.get(f, "")):
            kept += 1
    return kept / len(mandatory_fields)


def inject_indices(n: int, frac: float, seed: int) -> list[int]:
    rng = random.Random(seed)
    k = max(1, int(n * frac))
    idxs = list(range(n))
    rng.shuffle(idxs)
    return sorted(idxs[:k])


def run_failure_scenarios(
    source: list[dict[str, Any]],
    source_hashes: list[str],
    prov_records: list[dict[str, Any]],
    mandatory_fields: list[str],
) -> list[dict[str, Any]]:
    n = len(source)
    source_hash_set = set(source_hashes)
    source_by_hash = {h: rec for h, rec in zip(source_hashes, source)}

    def scenario_result(
        name: str,
        mutated: list[dict[str, Any]],
        injected_idxs: list[int],
    ) -> dict[str, Any]:
        failed = [
            i for i, d in enumerate(mutated)
            if not audit_record(source_hash_set, source_by_hash, d, mandatory_fields)
        ]
        inj = set(injected_idxs)
        fail = set(failed)
        if inj:
            recall = len(inj & fail) / len(inj)
            fp = len([i for i in fail if i not in inj]) / max(1, (n - len(inj)))
        else:
            # Baseline case: all failures are false positives.
            recall = None
            fp = len(fail) / max(1, n)
        return {
            "scenario": name,
            "injected_count": len(injected_idxs),
            "failed_count": len(failed),
            "audit_pass_rate": (n - len(failed)) / n,
            "audit_fail_rate": len(failed) / n,
            "detection_recall": recall,
            "false_positive_rate": fp,
        }

    scenarios: list[dict[str, Any]] = []

    # Baseline provenance should pass.
    scenarios.append(scenario_result("baseline_provenance", [dict(x) for x in prov_records], []))

    # 1) Orphan parent links.
    idx = inject_indices(n, 0.10, seed=61)
    mut = [dict(x) for x in prov_records]
    for i in idx:
        mut[i]["parent_sha256"] = "deadbeef" * 8
    scenarios.append(scenario_result("orphan_parent_link", mut, idx))

    # 2) Missing lineage metadata.
    idx = inject_indices(n, 0.10, seed=71)
    mut = [dict(x) for x in prov_records]
    for i in idx:
        mut[i]["generated_by"] = ""
    scenarios.append(scenario_result("missing_generated_by", mut, idx))

    # 3) Context erasure in mandatory fields.
    idx = inject_indices(n, 0.10, seed=81)
    mut = [dict(x) for x in prov_records]
    field = mandatory_fields[0]
    for i in idx:
        mut[i][field] = ""
    scenarios.append(scenario_result("mandatory_context_erasure", mut, idx))

    # 4) Label stripping (masquerading derivative as source).
    idx = inject_indices(n, 0.10, seed=91)
    mut = [dict(x) for x in prov_records]
    for i in idx:
        mut[i]["generated_label"] = ""
    scenarios.append(scenario_result("generated_label_stripped", mut, idx))

    return scenarios


def eval_stream(stream: StreamData) -> dict[str, Any]:
    t0 = time.perf_counter()
    source = stream.records
    n = len(source)
    source_hashes = [sha256_value(x) for x in source]
    generated_at = now_iso()

    naive = [transform_naive(x, stream.name) for x in source]
    prov = []
    for rec, h in zip(source, source_hashes):
        d = transform_provenance(rec, stream.mandatory_fields, h, generated_at)
        set_summary(d, rec, stream.name)
        prov.append(d)

    # Baseline/provenance metrics.
    fixity_re = [sha256_value(x) for x in json.loads(canonical_json(source))]
    fixity_stability = sum(1 for a, b in zip(source_hashes, fixity_re) if a == b) / n
    naive_ctx = sum(context_retention(s, d, stream.mandatory_fields) for s, d in zip(source, naive)) / n
    prov_ctx = sum(context_retention(s, d, stream.mandatory_fields) for s, d in zip(source, prov)) / n
    naive_dist = sum(1 for d in naive if d.get("parent_sha256")) / n
    prov_dist = sum(1 for d in prov if d.get("parent_sha256")) / n
    naive_line = sum(1 for d in naive if lineage_complete(d)) / n
    prov_line = sum(1 for d in prov if lineage_complete(d)) / n
    naive_disc = sum(1 for d in naive if d.get("generated_label")) / n
    prov_disc = sum(1 for d in prov if d.get("generated_label")) / n

    # Root-hash reproducibility.
    root1 = sha256_value(sorted(sha256_value(x) for x in prov))
    prov2 = []
    for rec, h in zip(source, source_hashes):
        d = transform_provenance(rec, stream.mandatory_fields, h, generated_at)
        set_summary(d, rec, stream.name)
        prov2.append(d)
    root2 = sha256_value(sorted(sha256_value(x) for x in prov2))
    reproducible_root = root1 == root2

    # Fault injections.
    tamper_idxs = inject_indices(n, 0.10, seed=31)
    tampered_source = [dict(x) for x in source]
    tamper_field = stream.mandatory_fields[0]
    for i in tamper_idxs:
        tampered_source[i][tamper_field] = str(tampered_source[i].get(tamper_field, "")) + "::tampered"
    tampered_hashes = [sha256_value(x) for x in tampered_source]
    drift_detected = [i for i, (a, b) in enumerate(zip(source_hashes, tampered_hashes)) if a != b]
    tamper_recall = len(set(drift_detected) & set(tamper_idxs)) / len(tamper_idxs)
    tamper_fp = len([i for i in drift_detected if i not in tamper_idxs]) / (n - len(tamper_idxs))

    lineage_break_idxs = inject_indices(n, 0.10, seed=41)
    broken = [dict(x) for x in prov]
    for i in lineage_break_idxs:
        broken[i]["parent_sha256"] = ""
    broken_detected = [i for i, d in enumerate(broken) if not lineage_complete(d)]
    lineage_recall = len(set(broken_detected) & set(lineage_break_idxs)) / len(lineage_break_idxs)
    lineage_fp = len([i for i in broken_detected if i not in lineage_break_idxs]) / (n - len(lineage_break_idxs))

    mismatch_idxs = inject_indices(n, 0.10, seed=51)
    mismatched = [dict(x) for x in prov]
    for i in mismatch_idxs:
        j = (i + 1) % n
        mismatched[i]["parent_sha256"] = source_hashes[j]
    mismatch_detected = [i for i, (d, h) in enumerate(zip(mismatched, source_hashes)) if d.get("parent_sha256") != h]
    mismatch_recall = len(set(mismatch_detected) & set(mismatch_idxs)) / len(mismatch_idxs)
    mismatch_fp = len([i for i in mismatch_detected if i not in mismatch_idxs]) / (n - len(mismatch_idxs))

    # Additional explicit audit-failure proof-of-concept scenarios.
    failure_scenarios = run_failure_scenarios(
        source=source,
        source_hashes=source_hashes,
        prov_records=prov,
        mandatory_fields=stream.mandatory_fields,
    )

    validate_seconds = time.perf_counter() - t0

    return {
        "stream_name": stream.name,
        "source_url": stream.source_url,
        "record_count": n,
        "mandatory_fields": stream.mandatory_fields,
        "timing": {
            "fetch_seconds": round(stream.fetch_seconds, 4),
            "validate_seconds": round(validate_seconds, 4),
        },
        "metrics": {
            "fixity_stability_rate": fixity_stability,
            "naive_context_retention_avg": naive_ctx,
            "provenance_context_retention_avg": prov_ctx,
            "naive_source_distinguishability_rate": naive_dist,
            "provenance_source_distinguishability_rate": prov_dist,
            "naive_lineage_completeness_rate": naive_line,
            "provenance_lineage_completeness_rate": prov_line,
            "naive_disclosure_label_rate": naive_disc,
            "provenance_disclosure_label_rate": prov_disc,
            "provenance_reproducible_root_hash": reproducible_root,
            "tamper_detection_recall": tamper_recall,
            "tamper_detection_false_positive_rate": tamper_fp,
            "lineage_break_detection_recall": lineage_recall,
            "lineage_break_detection_false_positive_rate": lineage_fp,
            "parent_mismatch_detection_recall": mismatch_recall,
            "parent_mismatch_detection_false_positive_rate": mismatch_fp,
        },
        "audit_failure_scenarios": failure_scenarios,
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True), encoding="utf-8")


def write_report(path: Path, streams: list[dict[str, Any]]) -> None:
    lines = []
    lines.append("# Extended Provenance Validation Report (2026-02-19)")
    lines.append("")
    lines.append("All streams were fetched live and evaluated with deterministic transforms plus controlled fault injection.")
    lines.append("")
    lines.append("## Streams")
    for s in streams:
        lines.append(f"- `{s['stream_name']}` ({s['record_count']} records): {s['source_url']}")
    lines.append("")
    lines.append("## Integrity Metrics")
    lines.append("")
    lines.append("| Stream | Fixity | Ctx Naive | Ctx Prov | Dist Prov | Lineage Prov | Disclosure Prov | Repro Root |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for s in streams:
        m = s["metrics"]
        lines.append(
            f"| {s['stream_name']} | {m['fixity_stability_rate']:.3f} | "
            f"{m['naive_context_retention_avg']:.3f} | {m['provenance_context_retention_avg']:.3f} | "
            f"{m['provenance_source_distinguishability_rate']:.3f} | {m['provenance_lineage_completeness_rate']:.3f} | "
            f"{m['provenance_disclosure_label_rate']:.3f} | {m['provenance_reproducible_root_hash']} |"
        )
    lines.append("")
    lines.append("## Fault-Injection Detection")
    lines.append("")
    lines.append("| Stream | Tamper Recall | Tamper FP | Lineage Break Recall | Lineage Break FP | Parent Mismatch Recall | Parent Mismatch FP |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for s in streams:
        m = s["metrics"]
        lines.append(
            f"| {s['stream_name']} | {m['tamper_detection_recall']:.3f} | {m['tamper_detection_false_positive_rate']:.3f} | "
            f"{m['lineage_break_detection_recall']:.3f} | {m['lineage_break_detection_false_positive_rate']:.3f} | "
            f"{m['parent_mismatch_detection_recall']:.3f} | {m['parent_mismatch_detection_false_positive_rate']:.3f} |"
        )
    lines.append("")
    lines.append("## Timing")
    lines.append("")
    for s in streams:
        t = s["timing"]
        lines.append(
            f"- `{s['stream_name']}` fetch={t['fetch_seconds']}s validate={t['validate_seconds']}s"
        )
    lines.append("")
    lines.append("## Additional Audit-Failure Proof-of-Concept")
    lines.append("")
    for s in streams:
        lines.append(f"### {s['stream_name']}")
        lines.append("")
        lines.append("| Scenario | Injected | Failed | Pass Rate | Fail Rate | Recall | FP |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for case in s.get("audit_failure_scenarios", []):
            rec = case["detection_recall"]
            rec_s = "n/a" if rec is None else f"{rec:.3f}"
            lines.append(
                f"| {case['scenario']} | {case['injected_count']} | {case['failed_count']} | "
                f"{case['audit_pass_rate']:.3f} | {case['audit_fail_rate']:.3f} | {rec_s} | {case['false_positive_rate']:.3f} |"
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    started = now_iso()
    t0 = time.perf_counter()

    streams_data = [
        load_nyc(limit=300),
        load_cma(limit=200),
        load_aic(limit=200),
    ]

    # Write source snapshots.
    for s in streams_data:
        write_json(DATA_DIR / f"{s.name}_source_extended.json", s.records)

    stream_results = [eval_stream(s) for s in streams_data]

    summary = {
        "generated_at": now_iso(),
        "started_at": started,
        "total_runtime_seconds": round(time.perf_counter() - t0, 4),
        "stream_count": len(stream_results),
        "total_records": sum(s["record_count"] for s in stream_results),
        "streams": stream_results,
    }

    out_json = RESULTS_DIR / "extended_provenance_validation_results.json"
    out_md = RESULTS_DIR / "extended_provenance_validation_report.md"
    write_json(out_json, summary)
    write_report(out_md, stream_results)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
