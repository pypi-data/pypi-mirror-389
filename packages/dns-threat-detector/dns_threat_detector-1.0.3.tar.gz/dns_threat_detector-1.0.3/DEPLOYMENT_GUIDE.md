# DNS Threat Detector - PyPI Deployment Guide

**Version:** 1.0.0
**Date:** October 30, 2025
**Status:** Ready for Deployment

## Prerequisites

- Python ≥ 3.8
- twine installed (`pip install twine`)
- PyPI account (https://pypi.org)
- TestPyPI account (https://test.pypi.org) - for testing

## Package Location

```
C:\Users\KIIT\Desktop\UMUDGA\DNS_Improvements\dns_threat_detector_package\
```

## Distribution Files

Located in `dist/` directory:
- `dns_threat_detector-1.0.0-py3-none-any.whl` (1.8 MB)
- `dns_threat_detector-1.0.0.tar.gz` (1.8 MB)

**Validation Status:** PASSED (twine check)

## Step-by-Step Deployment

### Phase 1: TestPyPI Deployment (Testing)

#### 1.1 Create TestPyPI Account
1. Go to https://test.pypi.org/account/register/
2. Complete registration
3. Verify email

#### 1.2 Generate API Token
1. Go to https://test.pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: `dns-threat-detector-upload`
4. Scope: "Entire account" (for first upload)
5. Copy token (starts with `pypi-`)
6. Store securely (will not be shown again)

#### 1.3 Configure .pypirc (Optional)
Create/edit `~/.pypirc`:
```ini
[distutils]
index-servers =
    testpypi
    pypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE
```

#### 1.4 Upload to TestPyPI
```powershell
cd c:\Users\KIIT\Desktop\UMUDGA\DNS_Improvements\dns_threat_detector_package

# Upload using twine
twine upload --repository testpypi dist/*

# When prompted:
# Username: __token__
# Password: (paste your TestPyPI API token)
```

Expected output:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading dns_threat_detector-1.0.0-py3-none-any.whl
Uploading dns_threat_detector-1.0.0.tar.gz
View at: https://test.pypi.org/project/dns-threat-detector/1.0.0/
```

#### 1.5 Test Installation from TestPyPI
```powershell
# Create fresh virtual environment
python -m venv test_env
test_env\Scripts\activate

# Install from TestPyPI (note: dependencies come from PyPI)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ dns-threat-detector

# Verify installation
python -c "from dns_threat_detector import DNS_ThreatDetector; print('Import success')"
dns-detect --help
dns-detect test
```

#### 1.6 Functional Testing
```python
from dns_threat_detector import DNS_ThreatDetector

detector = DNS_ThreatDetector()
detector.load_models()

# Test typosquatting detection
result = detector.predict('gooogle.com')
assert result['prediction'] == 'MALICIOUS'
assert result['method'] == 'typosquatting_rule'

# Test legitimate domain
result = detector.predict('google.com')
assert result['prediction'] == 'BENIGN'

print("All functional tests passed!")
```

### Phase 2: Production PyPI Deployment

#### 2.1 Create PyPI Account
1. Go to https://pypi.org/account/register/
2. Complete registration
3. Verify email
4. Enable 2FA (recommended)

#### 2.2 Generate API Token
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: `dns-threat-detector-upload`
4. Scope: "Entire account" (for first upload)
5. Copy token (starts with `pypi-`)
6. Store securely

#### 2.3 Upload to PyPI

**IMPORTANT:** You can only upload each version once. Make sure everything is perfect.

```powershell
cd c:\Users\KIIT\Desktop\UMUDGA\DNS_Improvements\dns_threat_detector_package

# Upload to production PyPI
twine upload dist/*

# When prompted:
# Username: __token__
# Password: (paste your PyPI API token)
```

Expected output:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading dns_threat_detector-1.0.0-py3-none-any.whl
Uploading dns_threat_detector-1.0.0.tar.gz
View at: https://pypi.org/project/dns-threat-detector/1.0.0/
```

#### 2.4 Verify Production Installation
```powershell
# Create fresh virtual environment
python -m venv prod_test_env
prod_test_env\Scripts\activate

# Install from PyPI
pip install dns-threat-detector

# Verify installation
python -c "from dns_threat_detector import DNS_ThreatDetector; print('Production install successful')"
dns-detect --help
dns-detect test
```

#### 2.5 Post-Deployment Verification
```python
from dns_threat_detector import DNS_ThreatDetector, __version__

print(f"Version: {__version__}")

detector = DNS_ThreatDetector(use_safelist=True)
detector.load_models()

# Run comprehensive tests
test_cases = [
    ('google.com', 'BENIGN'),
    ('gooogle.com', 'MALICIOUS'),
    ('facebook.com', 'BENIGN'),
    ('faceb00k.com', 'MALICIOUS'),
]

for domain, expected in test_cases:
    result = detector.predict(domain)
    assert result['prediction'] == expected, f"Failed for {domain}"
    print(f"✓ {domain}: {result['prediction']}")

print("\nAll production tests passed!")
```

## Post-Deployment Tasks

### 1. Update Project Documentation
- Update README with PyPI badge
- Add installation instructions
- Link to PyPI package page

### 2. GitHub Repository (if public)
1. Create GitHub repository
2. Push code:
   ```bash
   git init
   git add .
   git commit -m "Initial release v1.0.0"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```
3. Create release tag:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

### 3. Package Page Customization
- Add project URLs in PyPI dashboard
- Upload logo (optional)
- Add long description formatting
- Set project classifiers

### 4. Monitoring
- Check download statistics on PyPI
- Monitor issue reports
- Track user feedback

## Updating the Package

### Version Bump Process
1. Update version in:
   - `setup.py`
   - `pyproject.toml`
   - `dns_threat_detector/__init__.py`

2. Update CHANGELOG.md with changes

3. Rebuild distribution:
   ```powershell
   # Clean old builds
   Remove-Item -Recurse -Force dist, build, *.egg-info

   # Build new distribution
   python -m build
   ```

4. Validate:
   ```powershell
   twine check dist/*
   ```

5. Test on TestPyPI first, then upload to PyPI

### Semantic Versioning
- MAJOR.MINOR.PATCH (1.0.0)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Troubleshooting

### Common Issues

#### "File already exists"
- Each version can only be uploaded once
- Increment version number and rebuild

#### "Invalid distribution"
- Run `twine check dist/*`
- Fix reported issues
- Rebuild

#### "Package name already taken"
- Package name is globally unique
- Choose different name
- Update setup.py and pyproject.toml

#### Import errors after install
- Check dependencies installed correctly
- Verify Python version ≥ 3.8
- Check model files included in wheel

#### CLI command not found
- Check entry_points in setup.py
- Reinstall package
- Verify PATH includes Python Scripts/

### Getting Help
- PyPI Help: https://pypi.org/help/
- Python Packaging: https://packaging.python.org/
- GitHub Issues: (your repository)/issues

## Security Best Practices

1. **API Tokens**
   - Never commit tokens to version control
   - Use separate tokens for TestPyPI and PyPI
   - Rotate tokens periodically

2. **Distribution Integrity**
   - Always run `twine check` before upload
   - Verify package contents with `tar -tzf dist/*.tar.gz`
   - Test in clean environment

3. **Version Control**
   - Tag releases in git
   - Keep CHANGELOG.md updated
   - Sign releases with GPG (optional)

## Rollback Procedure

PyPI does not allow deleting releases, but you can:

1. **Yank the release:**
   - Go to package page on PyPI
   - Click "Manage" → "Releases"
   - Select version → "Options" → "Yank"
   - This marks it as broken (won't be installed by default)

2. **Upload fixed version:**
   - Increment version (e.g., 1.0.0 → 1.0.1)
   - Fix issues
   - Upload new version

## Success Checklist

- [ ] TestPyPI account created
- [ ] TestPyPI upload successful
- [ ] TestPyPI installation tested
- [ ] PyPI account created
- [ ] PyPI 2FA enabled
- [ ] PyPI upload successful
- [ ] Production installation verified
- [ ] CLI commands working
- [ ] Python API functional
- [ ] Documentation updated
- [ ] Repository tagged
- [ ] Announcement prepared

## Contact Information

**Package Maintainer:** UMUDGA Project
**Email:** contact@umudga.edu
**PyPI Package:** https://pypi.org/project/dns-threat-detector/
**GitHub:** (to be added)

## License

MIT License - See LICENSE file

## Acknowledgments

- PyPI for hosting
- Python Packaging Authority for tools
- Community for feedback and contributions

---

**Deployment Guide Version:** 1.0
**Last Updated:** October 30, 2025
**Status:** Ready for Production Deployment
