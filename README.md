# Echoes RustChain Bridge

[![BCOS Certified](https://img.shields.io/badge/BCOS-Certified-brightgreen?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAxTDMgNXY2YzAgNS41NSAzLjg0IDEwLjc0IDkgMTIgNS4xNi0xLjI2IDktNi40NSA5LTEyVjVsLTktNHptLTIgMTZsLTQtNCA1LjQxLTUuNDEgMS40MSAxLjQxTDEwIDE0bDYtNiAxLjQxIDEuNDFMMTAgMTd6Ii8+PC9zdmc+)](BCOS.md)
Holding code for the `Echoes from the Silicon Age` paper:

- stages corrected paper artifacts for publication
- generates SHA-256 fixity and a canonical manifest
- builds a RustChain-ready attestation payload (optional submit)
- prepares inputs you can reuse in a Grok article

## Quick Start

```bash
cd /home/scott/echoes-rustchain-bridge
python3 bridge_echoes.py prepare
```

This creates:

- `artifacts/echoes_silicon_age_paper.pdf`
- `artifacts/silicon_stratigraphy_figure.png`
- `manifest/paper_manifest.json`
- `manifest/hashes.sha256`
- `rustchain/attest_payload.sample.json`
- `rustchain/submit_attestation.sh`
- `grok_article_inputs.md`

## Optional: Submit Anchor Payload to RustChain

Safe default is dry-run. To actually submit:

```bash
python3 bridge_echoes.py submit-rustchain --execute
```

Response is saved to `rustchain/attest_response.json`.

## Optional: Push to GitHub (Manual)

```bash
git init
git add .
git commit -m "Add Echoes paper bridge artifacts and RustChain payload template"
git branch -M main
git remote add origin https://github.com/<your-user>/<repo>.git
git push -u origin main
```

## JCAA 2026 Package

A full archaeology-focused submission package with reproducible validation and
RustChain anchoring is included at:

- `jcaa_2026-02-19/`

This includes:
- updated manuscript (`.tex` + `.pdf`)
- deterministic and real-LLM validation outputs
- rerun protocol
- Grok reviewer packet
- RustChain attestation payload/response and hash receipt
