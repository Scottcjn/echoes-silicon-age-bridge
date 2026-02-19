# Real-LLM Provenance Validation Report (2026-02-19)

- Model: `qwen2.5-coder:1.5b`
- Ollama endpoint: `http://127.0.0.1:11434/api/generate`
- Sample size per stream: `12`
- Total sampled records: `36`
- Total LLM calls: `72`

## One-Hop + Two-Hop Metrics

| Stream | Records | One-Hop Naive Lineage | One-Hop Prov Lineage | One-Hop Prov Audit | Two-Hop Naive Lineage | Two-Hop Prov Lineage | Two-Hop Prov Chain Audit |
|---|---:|---:|---:|---:|---:|---:|---:|
| nyc_archaeology_reports | 12 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| cleveland_museum_ancient_collections | 12 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| aic_ancient_collections | 12 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 |

## Two-Hop Audit Failure Proof-of-Concept

### nyc_archaeology_reports

| Scenario | Injected | Failed | Pass Rate | Fail Rate | Recall | FP |
|---|---:|---:|---:|---:|---:|---:|
| two_hop_baseline_provenance | 0 | 0 | 1.000 | 0.000 | n/a | 0.000 |
| two_hop_orphan_parent_link | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_ancestor_mismatch | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_context_erasure | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_generated_label_stripped | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |

### cleveland_museum_ancient_collections

| Scenario | Injected | Failed | Pass Rate | Fail Rate | Recall | FP |
|---|---:|---:|---:|---:|---:|---:|
| two_hop_baseline_provenance | 0 | 0 | 1.000 | 0.000 | n/a | 0.000 |
| two_hop_orphan_parent_link | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_ancestor_mismatch | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_context_erasure | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_generated_label_stripped | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |

### aic_ancient_collections

| Scenario | Injected | Failed | Pass Rate | Fail Rate | Recall | FP |
|---|---:|---:|---:|---:|---:|---:|
| two_hop_baseline_provenance | 0 | 0 | 1.000 | 0.000 | n/a | 0.000 |
| two_hop_orphan_parent_link | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_ancestor_mismatch | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_context_erasure | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |
| two_hop_generated_label_stripped | 2 | 2 | 0.833 | 0.167 | 1.000 | 0.000 |

## Timing

- `nyc_archaeology_reports` LLM seconds=49.4524 (4.121 s/record)
- `cleveland_museum_ancient_collections` LLM seconds=38.414 (3.2012 s/record)
- `aic_ancient_collections` LLM seconds=32.0713 (2.6726 s/record)
