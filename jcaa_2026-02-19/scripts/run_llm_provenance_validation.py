#!/usr/bin/env python3
"""
Real-LLM provenance validation with one-hop and two-hop lineage checks.

This script uses local Ollama to produce:
1) one-hop LLM summaries from source records
2) two-hop LLM interpretations from hop-1 summaries

It compares a naive mode (no lineage metadata) against a provenance-first
mode and executes additional two-hop audit-failure proof-of-concept cases.
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

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:1.5b"

# Keep runtime practical while still demonstrating real-LLM behavior.
SAMPLE_PER_STREAM = 12


@dataclass
class StreamConfig:
    name: str
    source_file: str
    mandatory_fields: list[str]
    summary_fields: list[str]


STREAMS = [
    StreamConfig(
        name="nyc_archaeology_reports",
        source_file="nyc_archaeology_reports_source_extended.json",
        mandatory_fields=["biblioid", "borough", "author", "date", "title"],
        summary_fields=["title", "date", "borough", "author", "report_abstract"],
    ),
    StreamConfig(
        name="cleveland_museum_ancient_collections",
        source_file="cleveland_museum_ancient_collections_source_extended.json",
        mandatory_fields=["objectID", "department", "title", "culture", "objectDate", "accessionNumber"],
        summary_fields=["title", "culture", "objectDate", "department", "accessionNumber"],
    ),
    StreamConfig(
        name="aic_ancient_collections",
        source_file="aic_ancient_collections_source_extended.json",
        mandatory_fields=["id", "title", "date_display", "place_of_origin", "main_reference_number"],
        summary_fields=["title", "date_display", "place_of_origin", "main_reference_number"],
    ),
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_stream_records(cfg: StreamConfig) -> list[dict[str, Any]]:
    path = DATA_DIR / cfg.source_file
    if not path.exists():
        raise FileNotFoundError(f"Missing source snapshot: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Unexpected data shape in {path}; expected list")
    return [x for x in raw if isinstance(x, dict)]


def sample_records(records: list[dict[str, Any]], n: int, seed: int) -> list[dict[str, Any]]:
    if len(records) <= n:
        return records
    rng = random.Random(seed)
    idxs = list(range(len(records)))
    rng.shuffle(idxs)
    keep = sorted(idxs[:n])
    return [records[i] for i in keep]


def llm_generate(prompt: str, *, retries: int = 3) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_gpu": 0,
            "temperature": 0.2,
            "top_p": 0.9,
            "num_ctx": 2048,
        },
    }
    last_err: str | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
            resp.raise_for_status()
            body = resp.json()
            text = str(body.get("response", "")).strip()
            if text:
                return " ".join(text.split())
            last_err = "empty response"
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
        time.sleep(1.0 * attempt)
    raise RuntimeError(f"LLM request failed after {retries} attempts: {last_err}")


def format_record_for_prompt(rec: dict[str, Any], fields: list[str]) -> str:
    lines = []
    for f in fields:
        val = str(rec.get(f, "")).strip()
        if not val:
            continue
        lines.append(f"- {f}: {val[:420]}")
    return "\n".join(lines) if lines else "- record: (no populated fields)"


def build_summary_prompt(stream_name: str, rec: dict[str, Any], fields: list[str]) -> str:
    body = format_record_for_prompt(rec, fields)
    return (
        "You are assisting archaeological record processing.\n"
        f"Dataset stream: {stream_name}\n"
        "Write exactly one concise sentence summarizing the record.\n"
        "Do not invent facts and keep uncertainty qualifiers if present.\n"
        "Record fields:\n"
        f"{body}\n"
    )


def build_interpret_prompt(stream_name: str, hop1_summary: str) -> str:
    return (
        "You are assisting archaeological interpretation.\n"
        f"Dataset stream: {stream_name}\n"
        "Given this prior summary, write exactly one sentence describing "
        "what can be interpreted at a high level.\n"
        "Do not introduce specific facts not present in the input.\n"
        f"Prior summary: {hop1_summary}\n"
    )


def lineage_complete(rec: dict[str, Any]) -> bool:
    for k in ("generated_label", "generated_by", "generated_at", "parent_sha256"):
        if not rec.get(k):
            return False
    return True


def context_retention(source: dict[str, Any], derived: dict[str, Any], mandatory_fields: list[str]) -> float:
    if not mandatory_fields:
        return 0.0
    kept = 0
    for f in mandatory_fields:
        if str(source.get(f, "")) and str(source.get(f, "")) == str(derived.get(f, "")):
            kept += 1
    return kept / len(mandatory_fields)


def audit_one_hop(
    source_hashes: set[str],
    source_by_hash: dict[str, dict[str, Any]],
    derived: dict[str, Any],
    mandatory_fields: list[str],
) -> bool:
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


def audit_two_hop(
    source_hashes: set[str],
    source_by_hash: dict[str, dict[str, Any]],
    hop1_hashes: set[str],
    hop1_by_hash: dict[str, dict[str, Any]],
    derived: dict[str, Any],
    mandatory_fields: list[str],
) -> bool:
    if not lineage_complete(derived):
        return False
    parent = str(derived.get("parent_sha256", ""))
    ancestor = str(derived.get("ancestor_source_sha256", ""))
    if parent not in hop1_hashes:
        return False
    if ancestor not in source_hashes:
        return False
    hop1 = hop1_by_hash.get(parent)
    if not hop1:
        return False
    if str(hop1.get("parent_sha256", "")) != ancestor:
        return False
    src = source_by_hash.get(ancestor)
    if not src:
        return False
    for f in mandatory_fields:
        if str(derived.get(f, "")) != str(src.get(f, "")):
            return False
    return True


def inject_indices(n: int, frac: float, seed: int) -> list[int]:
    rng = random.Random(seed)
    k = max(1, int(n * frac))
    idxs = list(range(n))
    rng.shuffle(idxs)
    return sorted(idxs[:k])


def scenario_result(
    name: str,
    mutated: list[dict[str, Any]],
    injected_idxs: list[int],
    check_fn: Any,
) -> dict[str, Any]:
    n = len(mutated)
    failed = [i for i, rec in enumerate(mutated) if not check_fn(rec)]
    inj = set(injected_idxs)
    fail = set(failed)
    if inj:
        recall = len(inj & fail) / len(inj)
        fp = len([i for i in fail if i not in inj]) / max(1, (n - len(inj)))
    else:
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


def run_stream(cfg: StreamConfig, records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    generated_at = now_iso()

    source_hashes = [sha256_value(r) for r in records]
    source_hash_set = set(source_hashes)
    source_by_hash = {h: rec for h, rec in zip(source_hashes, records)}

    naive_hop1: list[dict[str, Any]] = []
    prov_hop1: list[dict[str, Any]] = []
    naive_hop2: list[dict[str, Any]] = []
    prov_hop2: list[dict[str, Any]] = []

    llm_calls = 0
    t0 = time.perf_counter()

    for src, src_hash in zip(records, source_hashes):
        prompt1 = build_summary_prompt(cfg.name, src, cfg.summary_fields)
        summary = llm_generate(prompt1)
        llm_calls += 1

        hop1_naive = {"summary": summary}
        naive_hop1.append(hop1_naive)

        hop1_prov = {
            "generated_label": "DERIVED_RECORD",
            "generated_by": f"ollama:{MODEL_NAME}",
            "generated_at": generated_at,
            "parent_sha256": src_hash,
            "summary": summary,
        }
        for f in cfg.mandatory_fields:
            hop1_prov[f] = src.get(f, "")
        prov_hop1.append(hop1_prov)

        prompt2 = build_interpret_prompt(cfg.name, summary)
        interpretation = llm_generate(prompt2)
        llm_calls += 1

        hop2_naive = {"interpretation": interpretation}
        naive_hop2.append(hop2_naive)

        hop1_hash = sha256_value(hop1_prov)
        hop2_prov = {
            "generated_label": "DERIVED_RECORD",
            "generated_by": f"ollama:{MODEL_NAME}",
            "generated_at": generated_at,
            "parent_sha256": hop1_hash,
            "ancestor_source_sha256": src_hash,
            "interpretation": interpretation,
        }
        for f in cfg.mandatory_fields:
            hop2_prov[f] = src.get(f, "")
        prov_hop2.append(hop2_prov)

    elapsed = time.perf_counter() - t0

    hop1_hashes = [sha256_value(x) for x in prov_hop1]
    hop1_hash_set = set(hop1_hashes)
    hop1_by_hash = {h: rec for h, rec in zip(hop1_hashes, prov_hop1)}

    one_hop_naive_lineage = sum(1 for x in naive_hop1 if lineage_complete(x)) / n
    one_hop_prov_lineage = sum(1 for x in prov_hop1 if lineage_complete(x)) / n
    one_hop_prov_context = sum(context_retention(s, d, cfg.mandatory_fields) for s, d in zip(records, prov_hop1)) / n
    one_hop_naive_context = sum(context_retention(s, d, cfg.mandatory_fields) for s, d in zip(records, naive_hop1)) / n
    one_hop_prov_audit = sum(
        1 for d in prov_hop1
        if audit_one_hop(source_hash_set, source_by_hash, d, cfg.mandatory_fields)
    ) / n

    two_hop_naive_lineage = sum(1 for x in naive_hop2 if lineage_complete(x)) / n
    two_hop_prov_lineage = sum(
        1 for x in prov_hop2
        if lineage_complete(x) and bool(x.get("ancestor_source_sha256"))
    ) / n
    two_hop_prov_audit = sum(
        1 for d in prov_hop2
        if audit_two_hop(
            source_hash_set,
            source_by_hash,
            hop1_hash_set,
            hop1_by_hash,
            d,
            cfg.mandatory_fields,
        )
    ) / n

    # Two-hop audit failure proof-of-concept.
    def check_two_hop(rec: dict[str, Any]) -> bool:
        return audit_two_hop(
            source_hash_set,
            source_by_hash,
            hop1_hash_set,
            hop1_by_hash,
            rec,
            cfg.mandatory_fields,
        )

    scenarios: list[dict[str, Any]] = []
    scenarios.append(scenario_result("two_hop_baseline_provenance", [dict(x) for x in prov_hop2], [], check_two_hop))

    idx = inject_indices(n, 0.20, seed=401)
    mut = [dict(x) for x in prov_hop2]
    for i in idx:
        mut[i]["parent_sha256"] = "deadbeef" * 8
    scenarios.append(scenario_result("two_hop_orphan_parent_link", mut, idx, check_two_hop))

    idx = inject_indices(n, 0.20, seed=402)
    mut = [dict(x) for x in prov_hop2]
    for i in idx:
        j = (i + 1) % n
        mut[i]["ancestor_source_sha256"] = source_hashes[j]
    scenarios.append(scenario_result("two_hop_ancestor_mismatch", mut, idx, check_two_hop))

    idx = inject_indices(n, 0.20, seed=403)
    mut = [dict(x) for x in prov_hop2]
    field = cfg.mandatory_fields[0]
    for i in idx:
        mut[i][field] = ""
    scenarios.append(scenario_result("two_hop_context_erasure", mut, idx, check_two_hop))

    idx = inject_indices(n, 0.20, seed=404)
    mut = [dict(x) for x in prov_hop2]
    for i in idx:
        mut[i]["generated_label"] = ""
    scenarios.append(scenario_result("two_hop_generated_label_stripped", mut, idx, check_two_hop))

    return {
        "stream_name": cfg.name,
        "record_count": n,
        "mandatory_fields": cfg.mandatory_fields,
        "llm_model": MODEL_NAME,
        "llm_calls": llm_calls,
        "timing": {
            "llm_seconds": round(elapsed, 4),
            "seconds_per_record_pair": round(elapsed / n, 4),
        },
        "metrics": {
            "one_hop_naive_lineage_completeness_rate": one_hop_naive_lineage,
            "one_hop_provenance_lineage_completeness_rate": one_hop_prov_lineage,
            "one_hop_naive_context_retention_avg": one_hop_naive_context,
            "one_hop_provenance_context_retention_avg": one_hop_prov_context,
            "one_hop_provenance_audit_pass_rate": one_hop_prov_audit,
            "two_hop_naive_lineage_completeness_rate": two_hop_naive_lineage,
            "two_hop_provenance_lineage_completeness_rate": two_hop_prov_lineage,
            "two_hop_provenance_chain_audit_pass_rate": two_hop_prov_audit,
        },
        "two_hop_audit_failure_scenarios": scenarios,
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True), encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Real-LLM Provenance Validation Report (2026-02-19)")
    lines.append("")
    lines.append(f"- Model: `{summary['model']}`")
    lines.append(f"- Ollama endpoint: `{summary['ollama_url']}`")
    lines.append(f"- Sample size per stream: `{summary['sample_per_stream']}`")
    lines.append(f"- Total sampled records: `{summary['total_records']}`")
    lines.append(f"- Total LLM calls: `{summary['total_llm_calls']}`")
    lines.append("")
    lines.append("## One-Hop + Two-Hop Metrics")
    lines.append("")
    lines.append("| Stream | Records | One-Hop Naive Lineage | One-Hop Prov Lineage | One-Hop Prov Audit | Two-Hop Naive Lineage | Two-Hop Prov Lineage | Two-Hop Prov Chain Audit |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for s in summary["streams"]:
        m = s["metrics"]
        lines.append(
            f"| {s['stream_name']} | {s['record_count']} | "
            f"{m['one_hop_naive_lineage_completeness_rate']:.3f} | "
            f"{m['one_hop_provenance_lineage_completeness_rate']:.3f} | "
            f"{m['one_hop_provenance_audit_pass_rate']:.3f} | "
            f"{m['two_hop_naive_lineage_completeness_rate']:.3f} | "
            f"{m['two_hop_provenance_lineage_completeness_rate']:.3f} | "
            f"{m['two_hop_provenance_chain_audit_pass_rate']:.3f} |"
        )
    lines.append("")
    lines.append("## Two-Hop Audit Failure Proof-of-Concept")
    lines.append("")
    for s in summary["streams"]:
        lines.append(f"### {s['stream_name']}")
        lines.append("")
        lines.append("| Scenario | Injected | Failed | Pass Rate | Fail Rate | Recall | FP |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for case in s.get("two_hop_audit_failure_scenarios", []):
            rec = case["detection_recall"]
            rec_s = "n/a" if rec is None else f"{rec:.3f}"
            lines.append(
                f"| {case['scenario']} | {case['injected_count']} | {case['failed_count']} | "
                f"{case['audit_pass_rate']:.3f} | {case['audit_fail_rate']:.3f} | {rec_s} | "
                f"{case['false_positive_rate']:.3f} |"
            )
        lines.append("")
    lines.append("## Timing")
    lines.append("")
    for s in summary["streams"]:
        t = s["timing"]
        lines.append(f"- `{s['stream_name']}` LLM seconds={t['llm_seconds']} ({t['seconds_per_record_pair']} s/record)")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    started_at = now_iso()
    t0 = time.perf_counter()

    stream_results: list[dict[str, Any]] = []
    for i, cfg in enumerate(STREAMS, start=1):
        full = load_stream_records(cfg)
        sampled = sample_records(full, SAMPLE_PER_STREAM, seed=700 + i)
        stream_results.append(run_stream(cfg, sampled))

    summary = {
        "generated_at": now_iso(),
        "started_at": started_at,
        "total_runtime_seconds": round(time.perf_counter() - t0, 4),
        "ollama_url": OLLAMA_URL,
        "model": MODEL_NAME,
        "sample_per_stream": SAMPLE_PER_STREAM,
        "stream_count": len(stream_results),
        "total_records": sum(s["record_count"] for s in stream_results),
        "total_llm_calls": sum(s["llm_calls"] for s in stream_results),
        "streams": stream_results,
    }

    out_json = RESULTS_DIR / "llm_provenance_validation_results.json"
    out_md = RESULTS_DIR / "llm_provenance_validation_report.md"
    write_json(out_json, summary)
    write_report(out_md, summary)

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
