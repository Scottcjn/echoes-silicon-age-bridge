# Contributing to Echoes RustChain Bridge

Thank you for helping improve the Echoes paper bridge. This repository keeps
publication artifacts, fixity manifests, and RustChain attestation payloads for
the "Echoes from the Silicon Age" paper. Contributions should preserve that
reproducible record and keep generated files easy to audit.

## Project Scope

The main bridge workflow is in `bridge_echoes.py`. It stages the paper PDF and
figure, writes a canonical manifest, records SHA-256 hashes, and creates a
RustChain payload template. The `jcaa_2026-02-19/` package contains a separate
JCAA submission bundle with its own rerun protocol, validation scripts, result
files, and RustChain receipt.

Good contributions include:

- documentation improvements that make the artifact workflow clearer
- fixes to bridge script behavior or command-line help
- updates to paper artifacts accompanied by refreshed manifests and hashes
- focused validation script changes with updated result files when appropriate
- small tests or checks that make the bridge workflow easier to maintain

Avoid broad rewrites unless they are needed for the artifact workflow you are
changing.

## Local Setup

Use a recent Python 3 interpreter. The top-level bridge script uses the Python
standard library only. The JCAA rerun protocol also requires the dependencies
listed in `jcaa_2026-02-19/RERUN_PROTOCOL.md`, including `requests` and a local
Ollama model for the LLM validation step.

Clone the repository and create a working branch:

```bash
git clone https://github.com/Scottcjn/echoes-silicon-age-bridge.git
cd echoes-silicon-age-bridge
git switch -c <your-branch-name>
```

## Development Workflow

Before changing generated artifacts, run the existing command once in a scratch
workspace so you understand the files it writes. Pass local copies of the paper
PDF and figure when you do not have the default source paths:

```bash
python3 bridge_echoes.py prepare \
  --workspace /tmp/echoes-bridge-preview \
  --src-pdf /path/to/echoes_silicon_age_paper.pdf \
  --src-image /path/to/silicon_stratigraphy_figure.png
```

When changing the bridge script, keep generated JSON deterministic where
possible. The manifest and payload writers intentionally use sorted keys and
stable formatting so reviews can focus on meaningful changes.

If you update the paper PDF, figure, manifest schema, or attestation payload:

1. Regenerate the affected files with `bridge_echoes.py prepare`.
2. Review `manifest/paper_manifest.json` for the expected metadata.
3. Confirm `manifest/hashes.sha256` matches the regenerated artifacts.
4. Include the generated files in the same pull request as the source change.

Keep RustChain submission behavior opt-in. The `submit-rustchain` command should
remain a dry run unless the caller passes `--execute`.

## Validation

Run the checks that match your change before opening a pull request.

For top-level bridge changes:

```bash
python3 -m py_compile bridge_echoes.py
python3 bridge_echoes.py submit-rustchain --payload rustchain/attest_payload.sample.json
```

For JCAA validation changes, follow `jcaa_2026-02-19/RERUN_PROTOCOL.md` and
commit updated result files only when they are intentionally regenerated.

For documentation-only changes, at minimum review the Markdown rendering and
check that all referenced paths still exist.

## Pull Request Guidelines

Use focused pull requests. In the description, include:

- a short summary of the artifact, script, or documentation change
- the validation commands you ran
- whether any generated files were refreshed
- any manual review notes for paper, manifest, or RustChain payload changes

Do not mix unrelated paper edits, bridge script changes, and JCAA result updates
in one pull request unless they are part of the same reproducibility update.

## Artifact Review Notes

This repository is useful because reviewers can trace each artifact back to its
hash, manifest entry, and attestation payload. When reviewing or preparing a
change, pay special attention to:

- artifact paths under `artifacts/`
- manifest entries under `manifest/`
- RustChain payloads and receipts under `rustchain/`
- JCAA validation outputs under `jcaa_2026-02-19/results/`

If a generated artifact changes unexpectedly, stop and identify the source of
the difference before including it in a pull request.
