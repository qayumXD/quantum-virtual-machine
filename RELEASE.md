# Release Guide

How to publish QVM to PyPI. Artifacts are built with `python -m build` and
validated with `twine check` before anything touches a package index.

## One-time setup

1. Create accounts (username `__token__` auth):
   - https://pypi.org  → account + API token (scope: project after first upload)
   - https://test.pypi.org → separate account + API token
2. Store tokens locally (never in the repo):

   ```bash
   cat > ~/.pypirc <<'EOF'
   [distutils]
   index-servers = pypi testpypi
   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-XXXXXXXXXXXXXXXX
   [pypi]
   username = __token__
   password = pypi-YYYYYYYYYYYYYYYY
   EOF
   chmod 600 ~/.pypirc
   ```

## Release flow

```bash
# 0) clean tree, tagged commit
git status --short            # must be empty
git tag -a vX.Y.Z -m "..." && git push origin main --tags

# 1) build + validate
python -m build
python -m twine check dist/*

# 2) dry-run on TestPyPI
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    "quantum-virtual-machine[all]"     # extras pull real deps from PyPI

# 3) smoke-test the TestPyPI wheel in a fresh venv, then promote
python -m twine upload dist/*

# 4) GitHub release
gh release create vX.Y.Z --title "vX.Y.Z — ..." --notes-file RELEASE_NOTES.md
```

## Notes

- Only upload artifacts built from a tagged, clean commit (`dist/` is gitignored).
- First PyPI upload claims the project name; add collaborators under
  *Account settings → Publishing → Projects* afterwards.
- Yank policy: broken release → `twine yank` rather than delete, so pins keep resolving.
