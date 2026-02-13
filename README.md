# Echoes RustChain Bridge

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


## 中文简介

Elyan Labs POWER 项目 - 为 IBM POWER 和复古系统提供现代支持。

Contributed by eelaine-wzw
