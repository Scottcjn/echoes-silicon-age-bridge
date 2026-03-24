# Contributing to Echoes of the Silicon Age Bridge

Welcome! This project bridges historical computing artifacts with modern RustChain attestation. We preserve digital archaeology through blockchain-verified fixity manifests. Your contributions help immortalize computing history.

## Table of Contents

- [About This Project](#about-this-project)
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Paper Artifact Standards](#paper-artifact-standards)
- [Fixity Manifest Format](#fixity-manifest-format)
- [Bridge Payload Structure](#bridge-payload-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## About This Project

Echoes of the Silicon Age Bridge connects:

- **Paper Artifacts**: Historical documents, schematics, manuals
- **Fixity Manifests**: Cryptographic proof of document integrity
- **RustChain Bridge**: Blockchain attestation for permanent verification

### Project Structure

```
echoes-silicon-age-bridge/
├── artifacts/          # Historical document archives
├── manifests/          # Fixity manifests (SHA-256, etc.)
├── bridge/             # RustChain integration code
├── validator/          # Manifest verification tools
├── docs/               # Documentation
└── tests/              # Test suites
```

## Code of Conduct

We are stewards of computing history. All contributors must:

- Treat historical artifacts with academic rigor
- Verify sources before adding artifacts
- Respect intellectual property of historical documents
- Collaborate with transparency and integrity
- Welcome researchers, historians, and developers alike

## Getting Started

### Prerequisites

**Required:**
- Python 3.8+ (for tools and validation)
- Rust 1.70+ (for bridge components)
- Git LFS (for large artifact storage)
- Node.js 18+ (for web components)

**Recommended:**
- Experience with archival standards (OAIS, PREMIS)
- Familiarity with blockchain concepts
- Knowledge of cryptographic hashing

### Installation

```bash
# Clone the repository
git clone https://github.com/Scottcjn/echoes-silicon-age-bridge.git
cd echoes-silicon-age-bridge

# Install Git LFS
git lfs install
git lfs pull

# Set up Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Rust components
cd bridge/
cargo build --release
cd ..

# Install Node dependencies (for web UI)
cd web/
npm install
cd ..
```

## Development Setup

### Git LFS Configuration

This project uses Git LFS for large artifacts:

```bash
# Configure Git LFS for artifact types
git lfs track "artifacts/*.pdf"
git lfs track "artifacts/*.tiff"
git lfs track "artifacts/*.wav"
git lfs track "scans/*.tiff"
git lfs track "*.iso"

# Verify tracking
git lfs ls-files
```

### Environment Configuration

Create `.env` file:

```bash
# Copy template
cp .env.template .env

# Edit with your settings
EDITOR=vim
```

Required variables:

```bash
# RustChain Configuration
RUSTCHAIN_RPC_URL=https://rpc.rustchain.network
RUSTCHAIN_BRIDGE_CONTRACT=0x...

# IPFS Gateway (for artifact storage)
IPFS_GATEWAY=https://ipfs.io/ipfs/
IPFS_PINNING_SERVICE=api.pinata.cloud

# Validation Settings
MIN_HASH_VERIFICATION=2  # Required confirmations
DEFAULT_HASH_ALGORITHM=sha256

# Development
DEBUG=false
LOG_LEVEL=INFO
```

## How to Contribute

### Adding Historical Artifacts

1. **Research and Verify**:
   - Confirm document authenticity
   - Research provenance and history
   - Check copyright status

2. **Prepare Artifact**:
   ```bash
   # Create artifact directory
   mkdir -p artifacts/YYYY-MM-DD-descriptive-name/
   
   # Add scanned document (TIFF preferred for archival)
   cp /path/to/scan.tiff artifacts/YYYY-MM-DD-descriptive-name/
   
   # Create metadata file
   cat > artifacts/YYYY-MM-DD-descriptive-name/metadata.json << 'EOF'
   {
     "title": "Original Document Title",
     "date": "1985-03-15",
     "source": "Archive Name or Collection",
     "provenance": "How this was obtained",
     "description": "Brief description of contents",
     "significance": "Why this matters to computing history",
     "tags": ["hardware", "cpu", "motorola", "68000"],
     "related": ["other-artifact-id"],
     "rights": "Public domain / CC BY-SA / etc",
     "scanner": "Scanner model and settings",
     "resolution_dpi": 600,
     "color_space": "Grayscale"
   }
   EOF
   ```

3. **Generate Fixity Manifest**:
   ```bash
   # Run manifest generator
   python tools/generate_manifest.py \
     --artifact artifacts/YYYY-MM-DD-descriptive-name/ \
     --output manifests/YYYY-MM-DD-descriptive-name.json
   ```

4. **Submit for Review**:
   ```bash
   git add artifacts/ manifests/
   git commit -m "artifact: Add Motorola 68000 Programmer's Reference (1985)
   
   - Original scanned manual from Stanford archives
   - 600 DPI grayscale TIFF
   - Verified against known-good copy
   - Public domain (pre-1989 US publication)"
   
   git push origin artifact/motorola-68000-manual
   gh pr create --title "artifact: Motorola 68000 Manual (1985)"
   ```

### Creating Fixity Manifests

Manifests prove artifact integrity:

```json
{
  "manifest_version": "1.0",
  "created": "2026-03-25T10:30:00Z",
  "artifact_id": "motorola-68000-manual-1985",
  "artifact_path": "artifacts/1985-03-15-motorola-68000-manual/",
  "hashes": {
    "sha256": {
      "algorithm": "SHA-256",
      "files": {
        "scan_001.tiff": "a1b2c3d4e5f6...",
        "scan_002.tiff": "b2c3d4e5f6a7...",
        "metadata.json": "c3d4e5f6a7b8..."
      },
      "combined": "d4e5f6a7b8c9..."
    },
    "blake3": {
      "algorithm": "BLAKE3",
      "files": {
        "scan_001.tiff": "e5f6a7b8c9d0...",
        "scan_002.tiff": "f6a7b8c9d0e1...",
        "metadata.json": "a7b8c9d0e1f2..."
      },
      "combined": "b8c9d0e1f2a3..."
    }
  },
  "file_count": 3,
  "total_bytes": 157286400,
  "metadata_hash": "c9d0e1f2a3b4..."
}
```

Generate with:

```bash
# Single artifact
python tools/generate_manifest.py --artifact <path> --output <manifest.json>

# Batch process
python tools/batch_manifest.py --artifacts-dir artifacts/ --output-dir manifests/

# Verify existing manifest
python tools/verify_manifest.py --manifest <manifest.json>
```

### Submitting Bridge Payloads

Bridge payloads connect manifests to RustChain:

```rust
// bridge/src/payload.rs
use rustchain_bridge::{Attestation, Payload};

pub struct EchoesPayload {
    pub manifest_hash: [u8; 32],
    pub artifact_id: String,
    pub timestamp: u64,
    pub metadata_uri: String,
}

impl Payload for EchoesPayload {
    fn to_attestation(&self) -> Attestation {
        Attestation::new(
            self.manifest_hash,
            self.timestamp,
            self.metadata_uri.as_bytes(),
        )
    }
}
```

Submit via CLI:

```bash
# Build bridge tool
cargo build --release --bin echoes-bridge

# Submit attestation
./target/release/echoes-bridge submit \
  --manifest manifests/artifact.json \
  --private-key $PRIVATE_KEY \
  --rpc $RUSTCHAIN_RPC_URL
```

## Paper Artifact Standards

### Scanning Requirements

For archival-quality digitization:

| Document Type | Resolution | Color Depth | Format |
|--------------|------------|-------------|--------|
| Text/Schematics | 600 DPI | Grayscale 8-bit | TIFF |
| Photos/Color | 400 DPI | Color 24-bit | TIFF |
| Microfiche | 800 DPI | Grayscale 8-bit | TIFF |
| Audio | 96kHz | 24-bit | WAV |

### Metadata Schema

```json
{
  "$schema": "