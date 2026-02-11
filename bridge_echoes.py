#!/usr/bin/env python3
"""
Bridge utility for staging the Echoes paper, generating fixity artifacts,
and optionally submitting a RustChain attestation payload.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_TITLE = (
    "Echoes from the Silicon Age: A Provenance-First Framework for Preserving "
    "Pre-LLM Digital Artifacts"
)
DEFAULT_AUTHOR = "Scott J. Boudreaux"
DEFAULT_SRC_PDF = "/home/scott/jcaa_submission/echoes_silicon_age_jcaa.pdf"
DEFAULT_SRC_IMAGE = "/home/scott/jcaa_submission/silicon_stratigraphy_correct.png"
DEFAULT_NODE_URL = "http://50.28.86.131:8099"
DEFAULT_MINER_ID = "paper_anchor_echoes_v1"


@dataclass
class Artifact:
    path: Path
    sha256: str
    size_bytes: int
    mime: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_artifact(src: Path, dest: Path, mime: str) -> Artifact:
    if not src.exists():
        raise FileNotFoundError(f"Source artifact does not exist: {src}")
    ensure_dir(dest.parent)
    shutil.copy2(src, dest)
    return Artifact(
        path=dest,
        sha256=sha256_file(dest),
        size_bytes=dest.stat().st_size,
        mime=mime,
    )


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(
    *,
    title: str,
    author: str,
    generated_at: str,
    paper: Artifact,
    figure: Artifact,
    jcaa_submission_id: str,
    jcaa_pdf_file_id: str,
    jcaa_figure_file_id: str,
) -> dict[str, Any]:
    anchor_record = {
        "title": title,
        "author": author,
        "generated_at": generated_at,
        "artifacts": [
            {
                "name": paper.path.name,
                "sha256": paper.sha256,
                "size_bytes": paper.size_bytes,
                "mime": paper.mime,
            },
            {
                "name": figure.path.name,
                "sha256": figure.sha256,
                "size_bytes": figure.size_bytes,
                "mime": figure.mime,
            },
        ],
    }
    anchor_record_sha256 = hashlib.sha256(canonical_json_bytes(anchor_record)).hexdigest()

    return {
        "schema_version": 1,
        "project": "echoes-rustchain-bridge",
        "generated_at": generated_at,
        "paper": {
            "title": title,
            "author": author,
            "artifacts": [
                {
                    "role": "manuscript_pdf",
                    "path": f"artifacts/{paper.path.name}",
                    "sha256": paper.sha256,
                    "size_bytes": paper.size_bytes,
                    "mime": paper.mime,
                },
                {
                    "role": "primary_figure",
                    "path": f"artifacts/{figure.path.name}",
                    "sha256": figure.sha256,
                    "size_bytes": figure.size_bytes,
                    "mime": figure.mime,
                },
            ],
        },
        "jcaa_submission": {
            "submission_id": jcaa_submission_id,
            "corrected_pdf_file_id": jcaa_pdf_file_id,
            "corrected_figure_file_id": jcaa_figure_file_id,
        },
        "anchor_record": anchor_record,
        "anchor_record_sha256": anchor_record_sha256,
        "publication_links": {
            "github_repo": "",
            "github_commit": "",
            "notes": "Fill publication links after pushing repo.",
        },
    }


def write_hashes_file(path: Path, paper: Artifact, figure: Artifact, manifest_sha256: str) -> None:
    ensure_dir(path.parent)
    lines = [
        f"{paper.sha256}  artifacts/{paper.path.name}",
        f"{figure.sha256}  artifacts/{figure.path.name}",
        f"{manifest_sha256}  manifest/paper_manifest.json",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_attest_payload(path: Path, manifest: dict[str, Any], miner_id: str, node_url: str) -> None:
    payload = {
        "miner": miner_id,
        "report": {
            "commitment": manifest["anchor_record_sha256"],
            "nonce": f"paper-{manifest['generated_at']}",
            "document_type": "academic_manuscript",
            "paper_title": manifest["paper"]["title"],
            "manifest_path": "manifest/paper_manifest.json",
            "manifest_sha256": sha256_text(json.dumps(manifest, sort_keys=True)),
        },
        "device": {
            "device_family": "paper",
            "device_arch": "archive-bridge",
            "device_model": "echoes-holding",
            "serial_number": "echoes-bridge-manual",
        },
        "signals": {},
        "_notes": {
            "node_url": node_url,
            "safe_default": "This payload is generated but not auto-submitted.",
        },
    }
    write_json(path, payload)


def write_submit_script(path: Path, node_url: str) -> None:
    ensure_dir(path.parent)
    content = f"""#!/usr/bin/env bash
set -euo pipefail

NODE_URL="${{1:-{node_url}}}"
PAYLOAD="${{2:-rustchain/attest_payload.sample.json}}"
OUT="${{3:-rustchain/attest_response.json}}"

curl -sS -X POST "$NODE_URL/attest/submit" \\
  -H "Content-Type: application/json" \\
  --data @"$PAYLOAD" > "$OUT"

echo "Wrote response to $OUT"
"""
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def write_grok_inputs(path: Path, manifest: dict[str, Any], node_url: str) -> None:
    lines = [
        "# Grok Article Inputs",
        "",
        "## Working Thesis",
        "Preserve pre-LLM digital artifacts with explicit provenance and verifiable fixity.",
        "",
        "## Paper",
        f"- Title: {manifest['paper']['title']}",
        f"- Author: {manifest['paper']['author']}",
        "- PDF: artifacts/echoes_silicon_age_paper.pdf",
        "- Figure: artifacts/silicon_stratigraphy_figure.png",
        "",
        "## Verifiability",
        f"- Anchor record SHA-256: `{manifest['anchor_record_sha256']}`",
        "- Manifest: manifest/paper_manifest.json",
        "- Hash list: manifest/hashes.sha256",
        "",
        "## RustChain",
        f"- Node URL: {node_url}",
        "- Payload template: rustchain/attest_payload.sample.json",
        "",
        "## Public Links (fill after push)",
        "- GitHub repo URL:",
        "- GitHub commit URL:",
        "",
        "## Suggested Grok Post Angle",
        "A methodology paper plus reproducible artifact set proving fixity-first preservation in a post-LLM world.",
    ]
    ensure_dir(path.parent)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def cmd_prepare(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    artifacts_dir = workspace / "artifacts"
    manifest_dir = workspace / "manifest"
    rustchain_dir = workspace / "rustchain"

    src_pdf = Path(args.src_pdf).resolve()
    src_image = Path(args.src_image).resolve()

    paper = copy_artifact(
        src_pdf,
        artifacts_dir / "echoes_silicon_age_paper.pdf",
        "application/pdf",
    )
    figure = copy_artifact(
        src_image,
        artifacts_dir / "silicon_stratigraphy_figure.png",
        "image/png",
    )

    generated_at = now_utc_iso()
    manifest = build_manifest(
        title=args.title,
        author=args.author,
        generated_at=generated_at,
        paper=paper,
        figure=figure,
        jcaa_submission_id=args.jcaa_submission_id,
        jcaa_pdf_file_id=args.jcaa_pdf_file_id,
        jcaa_figure_file_id=args.jcaa_figure_file_id,
    )

    manifest_path = manifest_dir / "paper_manifest.json"
    write_json(manifest_path, manifest)
    manifest_sha256 = sha256_file(manifest_path)
    write_hashes_file(manifest_dir / "hashes.sha256", paper, figure, manifest_sha256)
    write_attest_payload(
        rustchain_dir / "attest_payload.sample.json",
        manifest,
        miner_id=args.miner_id,
        node_url=args.node_url,
    )
    write_submit_script(rustchain_dir / "submit_attestation.sh", args.node_url)
    write_grok_inputs(workspace / "grok_article_inputs.md", manifest, args.node_url)

    print("Prepared bridge artifacts:")
    print(f"- Workspace: {workspace}")
    print(f"- Manifest: {manifest_path}")
    print(f"- Anchor record SHA-256: {manifest['anchor_record_sha256']}")
    return 0


def http_post_json(url: str, payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        if not data:
            return {}
        return json.loads(data.decode("utf-8"))


def cmd_submit_rustchain(args: argparse.Namespace) -> int:
    payload_path = Path(args.payload).resolve()
    if not payload_path.exists():
        print(f"Payload file not found: {payload_path}", file=sys.stderr)
        return 2

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    target_url = args.node_url.rstrip("/") + "/attest/submit"

    if not args.execute:
        print("Dry run only. Use --execute to submit.")
        print(f"Would POST to: {target_url}")
        print(f"Commitment: {payload.get('report', {}).get('commitment', '')}")
        return 0

    try:
        response = http_post_json(target_url, payload, timeout=args.timeout)
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(f"HTTP error {e.code}: {detail}", file=sys.stderr)
        return 1
    except URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 1

    out_path = Path(args.output).resolve()
    write_json(out_path, response)
    print(f"Submitted to {target_url}")
    print(f"Saved response: {out_path}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Echoes paper holding bridge utility.")
    sub = p.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare", help="Stage artifacts and build manifests.")
    p_prepare.add_argument("--workspace", default=".", help="Output workspace path.")
    p_prepare.add_argument("--src-pdf", default=DEFAULT_SRC_PDF, help="Source PDF path.")
    p_prepare.add_argument("--src-image", default=DEFAULT_SRC_IMAGE, help="Source image path.")
    p_prepare.add_argument("--title", default=DEFAULT_TITLE, help="Paper title.")
    p_prepare.add_argument("--author", default=DEFAULT_AUTHOR, help="Primary author.")
    p_prepare.add_argument("--jcaa-submission-id", default="273", help="JCAA submission ID.")
    p_prepare.add_argument("--jcaa-pdf-file-id", default="8615", help="JCAA corrected PDF file ID.")
    p_prepare.add_argument(
        "--jcaa-figure-file-id", default="8614", help="JCAA corrected figure file ID."
    )
    p_prepare.add_argument("--miner-id", default=DEFAULT_MINER_ID, help="RustChain miner ID label.")
    p_prepare.add_argument("--node-url", default=DEFAULT_NODE_URL, help="RustChain node URL.")
    p_prepare.set_defaults(func=cmd_prepare)

    p_submit = sub.add_parser("submit-rustchain", help="Submit prepared payload to RustChain.")
    p_submit.add_argument(
        "--payload",
        default="rustchain/attest_payload.sample.json",
        help="Path to JSON payload.",
    )
    p_submit.add_argument(
        "--output", default="rustchain/attest_response.json", help="Output response JSON path."
    )
    p_submit.add_argument("--node-url", default=DEFAULT_NODE_URL, help="RustChain node URL.")
    p_submit.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds.")
    p_submit.add_argument(
        "--execute",
        action="store_true",
        help="Actually submit payload. Without this flag, command is dry-run.",
    )
    p_submit.set_defaults(func=cmd_submit_rustchain)
    return p


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
