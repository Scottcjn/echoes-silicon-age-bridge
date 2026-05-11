import hashlib
import json
import os
from pathlib import Path

import pytest

from bridge_echoes import (
    Artifact,
    build_manifest,
    canonical_json_bytes,
    copy_artifact,
    sha256_file,
    sha256_text,
    write_attest_payload,
    write_hashes_file,
    write_submit_script,
)


def make_artifact(name, digest, size, mime):
    return Artifact(path=Path(name), sha256=digest, size_bytes=size, mime=mime)


def test_canonical_json_bytes_sorts_keys_and_removes_extra_spaces():
    payload_a = {"b": [2, 3], "a": {"z": 1}}
    payload_b = {"a": {"z": 1}, "b": [2, 3]}

    assert canonical_json_bytes(payload_a) == canonical_json_bytes(payload_b)
    assert canonical_json_bytes(payload_a) == b'{"a":{"z":1},"b":[2,3]}'


def test_sha256_file_reads_large_files_in_chunks(tmp_path):
    payload = (b"abc123" * 200_000) + b"tail"
    path = tmp_path / "artifact.bin"
    path.write_bytes(payload)

    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()


def test_copy_artifact_creates_destination_parent_and_returns_metadata(tmp_path):
    src = tmp_path / "source" / "paper.pdf"
    src.parent.mkdir()
    src.write_bytes(b"paper bytes")
    dest = tmp_path / "workspace" / "artifacts" / "paper.pdf"

    artifact = copy_artifact(src, dest, "application/pdf")

    assert dest.read_bytes() == b"paper bytes"
    assert artifact.path == dest
    assert artifact.size_bytes == len(b"paper bytes")
    assert artifact.mime == "application/pdf"
    assert artifact.sha256 == hashlib.sha256(b"paper bytes").hexdigest()


def test_copy_artifact_raises_for_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        copy_artifact(tmp_path / "missing.pdf", tmp_path / "out" / "missing.pdf", "application/pdf")


def test_build_manifest_records_artifacts_and_anchor_hash():
    paper = make_artifact("echoes_silicon_age_paper.pdf", "p" * 64, 123, "application/pdf")
    figure = make_artifact("silicon_stratigraphy_figure.png", "f" * 64, 456, "image/png")

    manifest = build_manifest(
        title="Echoes",
        author="Author",
        generated_at="2026-05-11T00:00:00+00:00",
        paper=paper,
        figure=figure,
        jcaa_submission_id="273",
        jcaa_pdf_file_id="8615",
        jcaa_figure_file_id="8614",
    )

    expected_anchor_hash = hashlib.sha256(canonical_json_bytes(manifest["anchor_record"])).hexdigest()
    assert manifest["paper"]["artifacts"][0]["path"] == "artifacts/echoes_silicon_age_paper.pdf"
    assert manifest["paper"]["artifacts"][1]["path"] == "artifacts/silicon_stratigraphy_figure.png"
    assert manifest["jcaa_submission"]["submission_id"] == "273"
    assert manifest["anchor_record_sha256"] == expected_anchor_hash


def test_write_hashes_file_and_attest_payload_use_manifest_digest(tmp_path):
    paper = make_artifact(tmp_path / "echoes_silicon_age_paper.pdf", "a" * 64, 10, "application/pdf")
    figure = make_artifact(tmp_path / "silicon_stratigraphy_figure.png", "b" * 64, 20, "image/png")
    manifest = {
        "anchor_record_sha256": "c" * 64,
        "generated_at": "2026-05-11T00:00:00+00:00",
        "paper": {"title": "Echoes"},
    }

    hashes_path = tmp_path / "manifest" / "hashes.sha256"
    write_hashes_file(hashes_path, paper, figure, "d" * 64)
    assert hashes_path.read_text(encoding="utf-8").splitlines() == [
        f"{'a' * 64}  artifacts/echoes_silicon_age_paper.pdf",
        f"{'b' * 64}  artifacts/silicon_stratigraphy_figure.png",
        f"{'d' * 64}  manifest/paper_manifest.json",
    ]

    payload_path = tmp_path / "rustchain" / "attest_payload.sample.json"
    write_attest_payload(payload_path, manifest, miner_id="miner-test", node_url="http://node.test")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["miner"] == "miner-test"
    assert payload["report"]["commitment"] == "c" * 64
    assert payload["report"]["manifest_sha256"] == sha256_text(json.dumps(manifest, sort_keys=True))
    assert payload["_notes"]["node_url"] == "http://node.test"


def test_write_submit_script_creates_executable_script_with_defaults(tmp_path):
    script_path = tmp_path / "rustchain" / "submit_attestation.sh"

    write_submit_script(script_path, "http://node.test")

    script = script_path.read_text(encoding="utf-8")
    assert 'NODE_URL="${1:-http://node.test}"' in script
    assert 'PAYLOAD="${2:-rustchain/attest_payload.sample.json}"' in script
    assert os.access(script_path, os.X_OK)
