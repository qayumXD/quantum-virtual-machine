# Release Guide

Releases are **automated**: pushing a tag `v*` runs tests + the audit corpus,
builds distributions, twine-checks them, publishes to PyPI, and attaches the
artifacts to a GitHub release.

## One-time setup

1. PyPI API token scoped to this project
   (pypi.org → Account settings → API tokens → *Add token* → scope:
   `quantum-virtual-machine`).
2. Store it as an Actions secret:

   ```bash
   gh secret set PYPI_TOKEN --body "pypi-..."
   ```

## Cutting a release

```bash
# 0) clean tree on main, all green locally
git status --short && pytest -q

# 1) bump version in pyproject.toml (+ api/app.py /health payload)
sed -i 's/^version = ".*"/version = "X.Y.Z"/' pyproject.toml
sed -i 's/"version": ".*",/"version": "X.Y.Z",/' api/app.py
git commit -am "chore: bump version to X.Y.Z"

# 2) tag and push — CI does the rest
git tag -a vX.Y.Z -m "..."
git push origin main --tags
```

The [Release workflow](.github/workflows/release.yml) then:

1. runs the unit suite + 20-algorithm audit on Python 3.12,
2. builds sdist + wheel, `twine check`,
3. uploads to PyPI using the `PYPI_TOKEN` secret,
4. attaches both artifacts to the auto-generated GitHub release.

Watch it: `gh run watch` (or the Actions tab). Manual trigger (build-only,
no publish): `gh workflow run Release`.

## Manual fallback

If automation must be bypassed, artifacts can be built and uploaded by hand:

```bash
python -m build && python -m twine check dist/*
twine upload dist/*        # uses ~/.pypirc
```

Only upload artifacts built from a tagged, clean commit (`dist/` is gitignored).

## Notes

- First upload of a new major/minor claims that version line; yank broken
  builds with `twine yank` rather than deleting so pins keep resolving.
- Consider upgrading to PyPA **Trusted Publishing** (OIDC, no token at all):
  pypi.org → project → Publishing → add trusted publisher
  (`qayumXD/quantum-virtual-machine`, workflow `release.yml`), then swap the
  upload step to `pypa/gh-action-pypi-publish@release/v1`.
