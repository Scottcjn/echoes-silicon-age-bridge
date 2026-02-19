# Peer Review Write-Up for Grok and External Reviewers
**Project:** Silicon Stratigraphy (JCAA resubmission package)  
**Author:** Scott J. Boudreaux  
**Date:** 2026-02-19  
**Review intent:** Technical and methodological peer review before journal submission.

---

## 1) What This Submission Is
This manuscript is a **methods paper** for archaeology-focused digital evidence integrity under AI-mediated workflows.

Core claim:
- A provenance-first workflow can preserve source/derivative boundaries and provide auditable lineage, fixity, and disclosure controls on real archaeology-relevant data streams.

This is **not** presented as:
- a universal benchmark,
- a legal admissibility standard,
- or a completed human-subject interpretive trial.

---

## 2) Review Package (Exact Files)
### Manuscript
- TeX: `/home/scott/silicon_stratigraphy_jcaa_full_rewrite.tex`
- PDF: `/home/scott/silicon_stratigraphy_jcaa_full_rewrite.pdf`

### Validation scripts/results
- Extended validation script: `/home/scott/jcaa_experiments_2026-02-19/scripts/run_provenance_extended_validation.py`
- Real-LLM validation script: `/home/scott/jcaa_experiments_2026-02-19/scripts/run_llm_provenance_validation.py`
- Rerun protocol: `/home/scott/jcaa_experiments_2026-02-19/RERUN_PROTOCOL.md`
- Extended results (JSON): `/home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_results.json`
- Extended results (human report): `/home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_report.md`
- Real-LLM results (JSON): `/home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_results.json`
- Real-LLM results (human report): `/home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_report.md`

### Source snapshots used in the run
- NYC archaeology reports: `/home/scott/jcaa_experiments_2026-02-19/data/nyc_archaeology_reports_source_extended.json`
- Cleveland Museum API sample: `/home/scott/jcaa_experiments_2026-02-19/data/cleveland_museum_ancient_collections_source_extended.json`
- Art Institute of Chicago API sample: `/home/scott/jcaa_experiments_2026-02-19/data/aic_ancient_collections_source_extended.json`

---

## 3) Data Sources and Scope of Executed Validation
This run used live retrieval from three public endpoints:
1. NYC Archaeology Reports Database  
   `https://data.cityofnewyork.us/resource/fuzb-9jre.json`
2. Cleveland Museum Open Access API  
   `https://openaccess-api.clevelandart.org/api/artworks/`
3. Art Institute of Chicago API  
   `https://api.artic.edu/api/v1/artworks/search`

Executed corpus size (single run):
- NYC: 300 records
- Cleveland Museum: 196 records
- AIC: 191 records
- **Total:** 687 records

---

## 4) Method Implemented in Validation
For each source stream, two derivative modes are compared:

### A) Naive mode
- Generates summary output without lineage/disclosure fields.
- Intended to model high-risk “derived output detached from source evidence.”

### B) Provenance-first mode
- Includes explicit:
  - `generated_label`
  - `generated_by`
  - `generated_at`
  - `parent_sha256`
- Preserves stream-specific mandatory context fields exactly.
- Computes and compares root hashes for deterministic rerun reproducibility.

---

## 5) Key Integrity Metrics (Observed)
From `extended_provenance_validation_report.md`:

For all three streams in provenance mode:
- Fixity stability: **1.000**
- Source distinguishability: **1.000**
- Lineage completeness: **1.000**
- Disclosure label rate: **1.000**
- Reproducible root hash: **True**

Context retention (provenance mode):
- NYC: **0.999**
- Cleveland: **1.000**
- AIC: **1.000**

Naive mode context retention:
- **0.000** in all streams in this implementation.

---

## 6) Audit Failure Proof-of-Concept (Executed)
Additional injected failure scenarios (10% records per stream):
1. orphan parent link
2. missing `generated_by`
3. mandatory context erasure
4. stripped `generated_label`

Observed outcomes:
- Baseline provenance (no injection): fail rate **0.000**
- Injected scenarios: fail rates approx **0.097–0.100** (expected due to sample rounding)
- Detection recall: **1.000**
- False positive rate: **0.000**

Interpretation:
- The audit layer produces deterministic fail states when provenance constraints are violated.

## 7) Real-LLM One-Hop and Two-Hop Validation (Executed)
To test behavior with live model outputs, a separate run used:
- local Ollama endpoint: `http://127.0.0.1:11434/api/generate`
- model: `qwen2.5-coder:1.5b` (CPU-forced in request options)
- sample: 12 records per stream (36 total), 72 LLM calls

Measured outcomes:
- One-hop naive lineage completeness: **0.000**
- One-hop provenance lineage completeness: **1.000**
- One-hop provenance audit pass rate: **1.000**
- Two-hop naive lineage completeness: **0.000**
- Two-hop provenance lineage completeness: **1.000**
- Two-hop provenance chain-audit pass rate: **1.000**

Additional two-hop failure injections (20% records per stream):
- orphan parent link
- ancestor mismatch
- mandatory context erasure
- stripped generated label

Observed outcomes:
- Baseline two-hop provenance fail rate: **0.000**
- Injected scenarios fail rate: **0.167** (2/12)
- Detection recall: **1.000**
- False positive rate: **0.000**

Interpretation:
- Provenance controls remained effective under real LLM text generation and across multi-hop lineage.

---

## 8) What This Evidence Supports
Defensible support:
- The implemented workflow functions across multiple live archaeology-relevant data streams.
- Provenance-first controls are materially stronger than a naive derivative workflow for auditable evidence lineage.
- The current audit policy reliably detects injected integrity failures in tested scenarios.

---

## 9) What This Evidence Does Not Yet Prove
Still unproven in this package:
- Robustness under advanced adversarial behavior beyond current injection classes.
- Human interpretive impact via blinded expert study.
- Cross-institution legal compliance and evidentiary admissibility standards.
- Long-duration operational reliability under real production drift.

---

## 10) Known Technical Caveats
- The package now includes both deterministic and real-LLM runs, but the real-LLM sample is limited (36 records).
- Real-LLM evidence is based on one local open model (`qwen2.5-coder:1.5b`), not cross-model comparison.
- Some values are near-perfect by design due to strict deterministic controls.
- Endpoint behavior can vary over time; rerun protocol is provided to verify reproducibility at review time.

---

## 11) Reviewer Questions Requested (for Grok + peers)
Please challenge the package on:
1. **Claim scope discipline:** Are claims appropriately constrained to what is measured?
2. **Metric adequacy:** Are the integrity metrics sufficient for archaeology-facing methodological claims?
3. **Failure-case realism:** Which additional failure classes should be added before submission?
4. **Reproducibility quality:** Is the rerun protocol specific enough for an independent lab?
5. **Publication framing:** Does the manuscript read as archaeology-first rather than tool-first?
6. **Statistical/experimental rigor:** What minimum additions are needed for a stronger acceptance probability?

---

## 12) Suggested Critical Stress Tests (if reviewers ask for more)
1. Add cross-model replication (at least one additional model family).
2. Add timestamp/order attacks (out-of-order anchors).
3. Add cross-run drift tests over multiple days and endpoint changes.
4. Add human expert blind review on interpretive fidelity outputs.

---

## 13) Copy-Paste Prompt for Grok
Use this prompt exactly if useful:

> You are reviewing a pre-submission archaeology methods manuscript and its executed validation artifacts. Critically evaluate whether the claims are justified by evidence, identify weaknesses, and propose concrete revisions before journal submission.  
>  
> Primary manuscript: `/home/scott/silicon_stratigraphy_jcaa_full_rewrite.pdf`  
> Validation report: `/home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_report.md`  
> Validation JSON: `/home/scott/jcaa_experiments_2026-02-19/results/extended_provenance_validation_results.json`  
> Real-LLM report: `/home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_report.md`  
> Real-LLM JSON: `/home/scott/jcaa_experiments_2026-02-19/results/llm_provenance_validation_results.json`  
> Rerun protocol: `/home/scott/jcaa_experiments_2026-02-19/RERUN_PROTOCOL.md`  
>  
> Focus on: claim scope, reproducibility rigor, archaeology relevance, potential methodological overreach, missing experiments, and reviewer-facing risk areas.  
>  
> Output format:  
> 1) Major concerns (severity-ranked),  
> 2) Minor concerns,  
> 3) Required revisions before submission,  
> 4) Optional improvements,  
> 5) Overall readiness score (0-100) with justification.

---

## 14) Requested Reviewer Output Format
For consistency across peer feedback, ask reviewers to respond with:
1. Severity-ranked findings
2. Concrete text edits required
3. Additional experiment requests (minimum set)
4. Go/No-Go recommendation for submission readiness
