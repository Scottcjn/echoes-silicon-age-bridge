# Contributing to Echoes Silicon Age Bridge

Thank you for your interest in contributing to the Echoes RustChain Bridge project! This repository holds code for the "Echoes from the Silicon Age" paper and provides tools for staging corrected paper artifacts, generating SHA-256 fixity, and building RustChain-ready attestation payloads.

## 🚀 Quick Start

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/YOUR_USERNAME/echoes-silicon-age-bridge.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes**
5. **Test your changes**
6. **Commit and push**: `git commit -m "feat: add your feature" && git push origin feature/your-feature-name`
7. **Open a Pull Request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/Scottcjn/echoes-silicon-age-bridge.git
cd echoes-silicon-age-bridge

# The project uses standard Python libraries
# No additional pip install required for basic usage
```

## 📝 Project Structure

```
echoes-silicon-age-bridge/
├── bridge_echoes.py              # Main bridge script
├── build_sdh_echoes_faithful.py  # Build faithful SDH version
├── build_sdh_manuscript.py       # Build manuscript
├── BCOS.md                       # BCOS certification
├── README.md                     # Project documentation
├── artifacts/                    # Generated artifacts (PDFs, images)
├── manifest/                     # SHA-256 hashes and manifests
├── rustchain/                    # RustChain attestation payloads
└── jcaa_2026-02-19/             # JCAA submission package
```

## 🔧 Making Changes

### Code Style

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Add docstrings for new functions
- Keep functions focused and small

### Commit Messages

We follow conventional commits:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code
test: Add tests
```

## 🧪 Testing

Before submitting changes:

1. **Test the bridge script**:
   ```bash
   python3 bridge_echoes.py prepare
   ```

2. **Verify generated artifacts**:
   - Check `artifacts/` directory for expected outputs
   - Verify `manifest/hashes.sha256` is generated
   - Confirm `rustchain/attest_payload.sample.json` is valid JSON

3. **Test RustChain submission (dry-run)**:
   ```bash
   python3 bridge_echoes.py submit-rustchain
   ```

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Changes are tested locally
- [ ] Commit messages are clear and descriptive
- [ ] Documentation is updated if needed
- [ ] No unrelated changes included

### PR Title Format

Use conventional commit prefixes:

- `feat:` — New features
- `fix:` — Bug fixes
- `docs:` — Documentation changes
- `refactor:` — Code refactoring
- `test:` — Testing improvements

Examples:
- `feat: Add support for additional output formats`
- `fix: Correct manifest hash generation`
- `docs: Update README with new options`

### PR Description Template

```markdown
## Summary
Brief description of changes

## Motivation
Why this change is needed

## Changes
- List of specific changes

## Testing
How you tested these changes
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Environment** (OS, Python version)
5. **Screenshots** (if applicable)

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check existing issues to avoid duplicates
2. Describe the feature and use case
3. Explain why it's valuable for paper artifact management

## 🎯 Areas We Need Help With

- **Documentation**: Improving code comments and examples
- **Testing**: Additional test cases for edge cases
- **Validation**: Cross-platform testing (Windows, macOS, Linux)
- **Features**: Additional output formats or integrations

## 🏆 RTC Bounties

Contributions can earn RTC tokens through the [RustChain Bounties](https://github.com/Scottcjn/rustchain-bounties) program:

- Bug fixes: 2-5 RTC
- Features: 5-15 RTC
- Documentation: 2-8 RTC
- Community files: 1-3 RTC

## ❓ Questions?

- Open an issue for questions
- Check existing documentation
- Contact maintainers directly

---

**Task Reference**: [#1605](https://github.com/Scottcjn/rustchain-bounties/issues/1605) - Add a CONTRIBUTING.md to any repo missing one

**Bounty**: 1 RTC

Thank you for contributing! Every contribution helps improve the Echoes RustChain Bridge.
