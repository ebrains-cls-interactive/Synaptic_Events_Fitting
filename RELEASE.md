# Release Process

This project publishes releases from GitHub Releases to PyPI.

## Versioning

Use PEP 440 versions in `pyproject.toml`.

- Alpha releases use `0.1.0a1`, `0.1.0a2`, and so on.
- Each GitHub release tag should match the package version prefixed with `v`, for example `v0.1.0a1`.

## Pre-release Checklist

Run these checks from a clean checkout before creating a release:

```powershell
git status --short
python -m pip install --upgrade pip
python -m pip install build twine
python -m pip install -e ".[test]"
python -m pytest clsiwidgets/tests -v
python -m build
python -m twine check dist/*
```

Before uploading manually, make sure `dist/` was created by the current version and does not contain artifacts from older package names.

## Automated GitHub Release

The automated release workflow is triggered when a GitHub Release is published.

1. Update `version` in `pyproject.toml`.
2. Commit the release changes.
3. Create and push a matching tag, for example:

```powershell
git tag v0.1.0a1
git push origin v0.1.0a1
```

4. Draft a GitHub Release for that tag.
5. Publish the GitHub Release.

After publishing, `.github/workflows/release.yml` will:

1. Install build and test tooling.
2. Import the public API.
3. Run the test suite.
4. Build the wheel and source distribution.
5. Run `twine check`.
6. Install the built wheel in a temporary environment.
7. Upload `dist/*` to PyPI using `PYPI_USER` and `PYPI_PASS` repository secrets.

## Manual PyPI Release

Manual release should be used only when the GitHub release workflow is unavailable.

```powershell
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
python -m pip install --upgrade pip
python -m pip install build twine
python -m pip install -e ".[test]"
python -m pytest clsiwidgets/tests -v
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

Verify on PyPI that the published version, package name and project metadata are correct.
