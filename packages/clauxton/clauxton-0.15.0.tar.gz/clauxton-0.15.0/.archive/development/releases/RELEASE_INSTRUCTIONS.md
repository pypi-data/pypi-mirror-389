# v0.10.1 Release Instructions

**Date**: October 22, 2025
**Status**: 🔄 Ready for PyPI Upload

---

## ✅ Completed Steps

1. ✅ **Code Changes**: Path/str compatibility bug fixed
2. ✅ **Tests**: 11 new tests added and passing
3. ✅ **Documentation**: English technical-design.md + TEST_WRITING_GUIDE.md created
4. ✅ **Version Update**: 0.10.0 → 0.10.1
5. ✅ **CHANGELOG**: Updated with v0.10.1 details
6. ✅ **Quality Checks**: mypy, ruff, twine all passing
7. ✅ **Package Build**: `dist/clauxton-0.10.1-py3-none-any.whl` and `.tar.gz` created
8. ✅ **Local Install**: Verified `clauxton --version` shows 0.10.1
9. ✅ **GitHub**: Code pushed to main branch
10. ✅ **Git Tag**: v0.10.1 created and pushed
11. ✅ **GitHub Release**: Created at https://github.com/nakishiyaman/clauxton/releases/tag/v0.10.1

---

## 🚀 Remaining Steps: PyPI Upload

### Prerequisites

You need PyPI API tokens for upload. If you don't have them, create them at:
- **TestPyPI**: https://test.pypi.org/manage/account/token/
- **PyPI**: https://pypi.org/manage/account/token/

### Step 1: Upload to TestPyPI (Verification)

```bash
# Activate virtual environment
source .venv/bin/activate

# Upload to TestPyPI
twine upload --repository-url https://test.pypi.org/legacy/ \
  dist/clauxton-0.10.1* \
  --username __token__ \
  --password <YOUR-TESTPYPI-TOKEN>
```

**Verify on TestPyPI**:
1. Visit: https://test.pypi.org/project/clauxton/0.10.1/
2. Check project description displays correctly
3. Verify README renders properly
4. Confirm version number is 0.10.1

**Test Installation from TestPyPI**:
```bash
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  clauxton==0.10.1

clauxton --version  # Should show: clauxton, version 0.10.1
```

### Step 2: Upload to PyPI (Production)

**⚠️ IMPORTANT**: Only proceed if TestPyPI verification passed!

```bash
# Upload to PyPI
twine upload dist/clauxton-0.10.1* \
  --username __token__ \
  --password <YOUR-PYPI-TOKEN>
```

**Verify on PyPI**:
1. Visit: https://pypi.org/project/clauxton/0.10.1/
2. Check project page displays correctly
3. Verify download links work

**Test Installation from PyPI**:
```bash
pip install clauxton==0.10.1
clauxton --version  # Should show: clauxton, version 0.10.1

# Test basic functionality
clauxton --help
```

### Step 3: Post-Release Verification

**Check GitHub Release**:
- Visit: https://github.com/nakishiyaman/clauxton/releases/tag/v0.10.1
- Verify release notes are accurate
- Confirm wheel and source distribution are attached

**Update GitHub Release** (if needed):
```bash
gh release edit v0.10.1 \
  --notes "$(cat <<'EOF'
## 🐛 Bug Fix Release

### Fixed
- **CRITICAL**: Path vs str type incompatibility in KnowledgeBase and TaskManager
- Now accepts both Path and str for root_dir parameter
- Fixes TypeError when passing string paths to constructors
- Example: KnowledgeBase('.clauxton') now works

### Documentation
- Add TEST_WRITING_GUIDE.md for contributors
- Replace Japanese technical-design.md with English version (v2.0)

### Tests
- Add 11 new tests for Path/str compatibility
- Edge cases: paths with spaces, relative paths

### Quality
- mypy: 23 files passing
- ruff: All checks passed
- 100% test pass rate

Full Changelog: https://github.com/nakishiyaman/clauxton/compare/v0.10.0...v0.10.1
EOF
)"
```

---

## 📋 Verification Checklist

Before marking release as complete, verify:

- [ ] TestPyPI upload successful
- [ ] TestPyPI page renders correctly
- [ ] Test install from TestPyPI works
- [ ] PyPI upload successful
- [ ] PyPI page renders correctly
- [ ] Install from PyPI works: `pip install clauxton==0.10.1`
- [ ] `clauxton --version` shows 0.10.1
- [ ] GitHub Release page is correct
- [ ] Release assets (wheel, tar.gz) are attached

---

## 🎉 Success Criteria

**v0.10.1 is successfully released when**:
1. ✅ Package available on PyPI: https://pypi.org/project/clauxton/0.10.1/
2. ✅ Installation works: `pip install clauxton==0.10.1`
3. ✅ GitHub Release visible: https://github.com/nakishiyaman/clauxton/releases/tag/v0.10.1
4. ✅ README on PyPI shows updated content (no Phase/beta references)

---

## 🔧 Troubleshooting

### Issue: twine upload fails with authentication error

**Solution**: Use API token instead of username/password
```bash
twine upload dist/* --username __token__ --password pypi-AgE...
```

### Issue: Package description not rendering on PyPI

**Solution**: Check README.md syntax with:
```bash
twine check dist/clauxton-0.10.1*
```

### Issue: Old version still showing on PyPI

**Solution**: PyPI caches can take a few minutes to update. Wait 5-10 minutes and refresh.

---

## 📞 Support

If you encounter issues:
1. Check GitHub Issues: https://github.com/nakishiyaman/clauxton/issues
2. Review PyPI documentation: https://packaging.python.org/
3. Verify twine configuration: `twine --version`

---

**Prepared by**: Claude Code
**Date**: October 22, 2025
**Status**: Ready for PyPI upload
