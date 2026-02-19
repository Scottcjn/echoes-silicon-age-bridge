# Extended Provenance Validation Report (2026-02-19)

All streams were fetched live and evaluated with deterministic transforms plus controlled fault injection.

## Streams
- `nyc_archaeology_reports` (300 records): https://data.cityofnewyork.us/resource/fuzb-9jre.json
- `cleveland_museum_ancient_collections` (196 records): https://openaccess-api.clevelandart.org/api/artworks/
- `aic_ancient_collections` (191 records): https://api.artic.edu/api/v1/artworks/search

## Integrity Metrics

| Stream | Fixity | Ctx Naive | Ctx Prov | Dist Prov | Lineage Prov | Disclosure Prov | Repro Root |
|---|---:|---:|---:|---:|---:|---:|---|
| nyc_archaeology_reports | 1.000 | 0.000 | 0.999 | 1.000 | 1.000 | 1.000 | True |
| cleveland_museum_ancient_collections | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | True |
| aic_ancient_collections | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | True |

## Fault-Injection Detection

| Stream | Tamper Recall | Tamper FP | Lineage Break Recall | Lineage Break FP | Parent Mismatch Recall | Parent Mismatch FP |
|---|---:|---:|---:|---:|---:|---:|
| nyc_archaeology_reports | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| cleveland_museum_ancient_collections | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| aic_ancient_collections | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 |

## Timing

- `nyc_archaeology_reports` fetch=1.1725s validate=0.0188s
- `cleveland_museum_ancient_collections` fetch=4.5133s validate=0.0115s
- `aic_ancient_collections` fetch=0.1511s validate=0.0092s

## Additional Audit-Failure Proof-of-Concept

### nyc_archaeology_reports

| Scenario | Injected | Failed | Pass Rate | Fail Rate | Recall | FP |
|---|---:|---:|---:|---:|---:|---:|
| baseline_provenance | 0 | 0 | 1.000 | 0.000 | n/a | 0.000 |
| orphan_parent_link | 30 | 30 | 0.900 | 0.100 | 1.000 | 0.000 |
| missing_generated_by | 30 | 30 | 0.900 | 0.100 | 1.000 | 0.000 |
| mandatory_context_erasure | 30 | 30 | 0.900 | 0.100 | 1.000 | 0.000 |
| generated_label_stripped | 30 | 30 | 0.900 | 0.100 | 1.000 | 0.000 |

### cleveland_museum_ancient_collections

| Scenario | Injected | Failed | Pass Rate | Fail Rate | Recall | FP |
|---|---:|---:|---:|---:|---:|---:|
| baseline_provenance | 0 | 0 | 1.000 | 0.000 | n/a | 0.000 |
| orphan_parent_link | 19 | 19 | 0.903 | 0.097 | 1.000 | 0.000 |
| missing_generated_by | 19 | 19 | 0.903 | 0.097 | 1.000 | 0.000 |
| mandatory_context_erasure | 19 | 19 | 0.903 | 0.097 | 1.000 | 0.000 |
| generated_label_stripped | 19 | 19 | 0.903 | 0.097 | 1.000 | 0.000 |

### aic_ancient_collections

| Scenario | Injected | Failed | Pass Rate | Fail Rate | Recall | FP |
|---|---:|---:|---:|---:|---:|---:|
| baseline_provenance | 0 | 0 | 1.000 | 0.000 | n/a | 0.000 |
| orphan_parent_link | 19 | 19 | 0.901 | 0.099 | 1.000 | 0.000 |
| missing_generated_by | 19 | 19 | 0.901 | 0.099 | 1.000 | 0.000 |
| mandatory_context_erasure | 19 | 19 | 0.901 | 0.099 | 1.000 | 0.000 |
| generated_label_stripped | 19 | 19 | 0.901 | 0.099 | 1.000 | 0.000 |

