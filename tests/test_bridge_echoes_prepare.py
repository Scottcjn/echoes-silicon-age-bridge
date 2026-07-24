"""End-to-end checks that `prepare` emits a verifiable attestation payload.

The point of the bridge is fixity: whoever holds the workspace must be able to
recompute every digest it publishes. The payload names
`manifest/paper_manifest.json` in `manifest_path`, so `manifest_sha256` has to
be the digest of that file on disk - the same value `manifest/hashes.sha256`
lists for it.
"""

import hashlib
import json
from pathlib import Path

from bridge_echoes import parser

REPO_ROOT = Path(__file__).resolve().parents[1]


def _prepare_workspace(tmp_path: Path) -> Path:
    src_pdf = tmp_path / "src" / "paper.pdf"
    src_png = tmp_path / "src" / "figure.png"
    src_pdf.parent.mkdir(parents=True)
    src_pdf.write_bytes(b"%PDF-1.4 fake manuscript bytes")
    src_png.write_bytes(b"\x89PNG\r\n\x1a\n fake figure bytes")

    workspace = tmp_path / "workspace"
    args = parser().parse_args(
        [
            "prepare",
            "--workspace",
            str(workspace),
            "--src-pdf",
            str(src_pdf),
            "--src-image",
            str(src_png),
        ]
    )
    assert args.func(args) == 0
    return workspace


def _hashes_entry(hashes_path: Path, name: str) -> str:
    for line in hashes_path.read_text(encoding="utf-8").splitlines():
        digest, _, path = line.partition("  ")
        if path == name:
            return digest
    raise AssertionError(f"{name} missing from {hashes_path}")


def test_payload_manifest_digest_matches_the_file_it_names(tmp_path):
    workspace = _prepare_workspace(tmp_path)

    payload = json.loads((workspace / "rustchain" / "attest_payload.sample.json").read_text("utf-8"))
    named = payload["report"]["manifest_path"]
    on_disk = hashlib.sha256((workspace / named).read_bytes()).hexdigest()

    assert payload["report"]["manifest_sha256"] == on_disk
    assert _hashes_entry(workspace / "manifest" / "hashes.sha256", named) == on_disk


def test_payload_commitment_matches_the_manifest_anchor_record(tmp_path):
    workspace = _prepare_workspace(tmp_path)

    manifest = json.loads((workspace / "manifest" / "paper_manifest.json").read_text("utf-8"))
    payload = json.loads((workspace / "rustchain" / "attest_payload.sample.json").read_text("utf-8"))

    assert payload["report"]["commitment"] == manifest["anchor_record_sha256"]


def test_committed_sample_payload_is_verifiable():
    """The workspace committed to this repo must verify the same way."""
    payload = json.loads((REPO_ROOT / "rustchain" / "attest_payload.sample.json").read_text("utf-8"))
    manifest_path = REPO_ROOT / payload["report"]["manifest_path"]

    on_disk = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert payload["report"]["manifest_sha256"] == on_disk
    assert _hashes_entry(REPO_ROOT / "manifest" / "hashes.sha256", payload["report"]["manifest_path"]) == on_disk
