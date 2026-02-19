# Independent Rerun Protocol (JCAA Provenance Validation)

## Purpose
Reproduce the extended provenance validation and audit-failure proof-of-concept exactly as reported in the manuscript.

## Preconditions
- Linux/macOS shell with `python3`
- Python package: `requests`
- Network access to:
  - `data.cityofnewyork.us`
  - `openaccess-api.clevelandart.org`
  - `api.artic.edu`
- Local Ollama service on `http://127.0.0.1:11434`
- Ollama model available: `qwen2.5-coder:1.5b`

## 1) Run Validation
```bash
python3 /home/scott/jcaa_experiments_2026-02-19/scripts/run_provenance_extended_validation.py
```

Expected terminal output includes:
- `Wrote /home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_results.json`
- `Wrote /home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_report.md`

## 2) Verify Output Files
```bash
ls -l /home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_results.json
ls -l /home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_report.md
```

## 3) Verify Core Metrics Programmatically
```bash
python3 - <<'PY'
import json
p='/home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_results.json'
obj=json.load(open(p))
assert obj['total_records'] >= 500, obj['total_records']
for s in obj['streams']:
    m=s['metrics']
    assert m['fixity_stability_rate'] == 1.0
    assert m['provenance_source_distinguishability_rate'] == 1.0
    assert m['provenance_lineage_completeness_rate'] == 1.0
    assert m['provenance_disclosure_label_rate'] == 1.0
    assert m['provenance_reproducible_root_hash'] is True
print('core metrics OK')
PY
```

## 4) Verify Audit-Failure Proof-of-Concept Cases
```bash
python3 - <<'PY'
import json
p='/home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_results.json'
obj=json.load(open(p))
for s in obj['streams']:
    cases={c['scenario']:c for c in s['audit_failure_scenarios']}
    assert cases['baseline_provenance']['audit_fail_rate'] == 0.0
    for name in ['orphan_parent_link','missing_generated_by','mandatory_context_erasure','generated_label_stripped']:
        c=cases[name]
        assert c['detection_recall'] == 1.0, (s['stream_name'],name,c['detection_recall'])
        assert c['false_positive_rate'] == 0.0, (s['stream_name'],name,c['false_positive_rate'])
        assert 0.09 <= c['audit_fail_rate'] <= 0.11, (s['stream_name'],name,c['audit_fail_rate'])
print('audit failure cases OK')
PY
```

## 5) Human-Readable Review
Open and inspect:
- `/home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_report.md`

The report should contain:
- Integrity metrics table
- Fault-injection detection table
- Additional audit-failure proof-of-concept scenario tables

## 6) Run Real-LLM One-Hop + Two-Hop Validation
```bash
python3 /home/scott/jcaa_experiments_2026-02-19/scripts/run_llm_provenance_validation.py
```

Expected terminal output includes:
- `Wrote /home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_results.json`
- `Wrote /home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_report.md`

## 7) Verify Real-LLM Metrics Programmatically
```bash
python3 - <<'PY'
import json
p='/home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_results.json'
obj=json.load(open(p))
assert obj['model'] == 'qwen2.5-coder:1.5b'
assert obj['total_records'] == 36, obj['total_records']
assert obj['total_llm_calls'] == 72, obj['total_llm_calls']
for s in obj['streams']:
    m=s['metrics']
    assert m['one_hop_naive_lineage_completeness_rate'] == 0.0
    assert m['one_hop_provenance_lineage_completeness_rate'] == 1.0
    assert m['one_hop_provenance_audit_pass_rate'] == 1.0
    assert m['two_hop_naive_lineage_completeness_rate'] == 0.0
    assert m['two_hop_provenance_lineage_completeness_rate'] == 1.0
    assert m['two_hop_provenance_chain_audit_pass_rate'] == 1.0
print('real-LLM metrics OK')
PY
```

## 8) Verify Real-LLM Two-Hop Audit-Failure Cases
```bash
python3 - <<'PY'
import json
p='/home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_results.json'
obj=json.load(open(p))
for s in obj['streams']:
    cases={c['scenario']:c for c in s['two_hop_audit_failure_scenarios']}
    assert cases['two_hop_baseline_provenance']['audit_fail_rate'] == 0.0
    for name in [
        'two_hop_orphan_parent_link',
        'two_hop_ancestor_mismatch',
        'two_hop_context_erasure',
        'two_hop_generated_label_stripped',
    ]:
        c=cases[name]
        assert c['detection_recall'] == 1.0, (s['stream_name'],name,c['detection_recall'])
        assert c['false_positive_rate'] == 0.0, (s['stream_name'],name,c['false_positive_rate'])
        assert abs(c['audit_fail_rate'] - (2/12)) < 1e-9, (s['stream_name'],name,c['audit_fail_rate'])
print('real-LLM two-hop audit failures OK')
PY
```

## 9) Human-Readable Real-LLM Review
Open and inspect:
- `/home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_report.md`
