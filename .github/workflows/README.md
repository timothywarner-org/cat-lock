# KittyLock GitHub Actions Workflows

This directory contains automated CI/CD workflows for KittyLock.

## Workflows

### 1. CI Workflow (`ci.yml`)

**Purpose:** Automated testing and building on every code change

**Triggers:**
- Push to `master` branch
- Pull requests targeting `master`
- Manual workflow dispatch

**Jobs:**
- **test**: Runs pytest suite with coverage on Python 3.11 and 3.12
  - Generates coverage reports
  - Uploads coverage XML as artifact
  - Displays coverage summary in workflow output

- **build**: Creates Windows executable with PyInstaller
  - Only runs if tests pass
  - Uploads `CatLock.exe` as workflow artifact
  - Shows executable size in workflow summary

**Artifacts:**
- `coverage-report`: Test coverage XML (30 days retention)
- `CatLock-{sha}`: Built executable (30 days retention)

**Local Simulation:**
```bash
# Run the same tests locally
pytest --cov=src --cov-report=term-missing

# Build the same executable locally
pyinstaller --clean CatLock.spec
```

---

### 2. Release Workflow (`release.yml`)

**Purpose:** Create GitHub releases with versioned executables

**Triggers:**
- Tags matching `v*.*.*` pattern (e.g., `v1.0.0`, `v2.3.1`)
- Manual workflow dispatch with tag input

**Jobs:**
- **build**: Creates production-ready Windows executable
  - Generates SHA256 checksum for security
  - Renames executable with version number
  - Uploads as workflow artifact (90 days retention)

- **release**: Creates GitHub release
  - Auto-generates changelog from commits since previous tag
  - Uploads versioned executable and checksum
  - Marks alpha/beta/rc versions as pre-release
  - Includes installation instructions and security notes

**Release Assets:**
- `CatLock-{version}.exe`: Windows executable
- `CatLock-{version}.exe.sha256`: SHA256 checksum file

**Creating a Release:**
```bash
# 1. Update version in code (if applicable)
# 2. Commit all changes
git add .
git commit -m "chore: Bump version to 1.2.3"

# 3. Create and push tag
git tag -a v1.2.3 -m "Release v1.2.3: Add awesome new feature"
git push origin v1.2.3

# 4. GitHub Actions will automatically:
#    - Build the executable
#    - Generate changelog
#    - Create release on GitHub
#    - Upload assets
```

**Versioning Convention:**
- Use semantic versioning: `v{major}.{minor}.{patch}`
- Examples:
  - `v1.0.0` - Major release (stable)
  - `v1.2.3` - Minor/patch release (stable)
  - `v2.0.0-beta.1` - Pre-release (marked as pre-release)
  - `v1.5.0-rc.2` - Release candidate (marked as pre-release)

---

## Caching Strategy

Both workflows use pip dependency caching to speed up builds:
- Cache key based on `requirements.txt` and `requirements-dev.txt` hashes
- Automatically invalidates when dependencies change
- Reduces workflow time by ~30-60 seconds

## Secrets and Permissions

**Required Secrets:**
- `GITHUB_TOKEN` - Automatically provided by GitHub (no action needed)

**Required Permissions:**
- CI workflow: Default (read-only)
- Release workflow: `contents: write` (configured in workflow)

## Troubleshooting

### Test Failures
If tests fail in CI but pass locally:
1. Check Python version consistency (use 3.11 or 3.12)
2. Ensure all dependencies are in `requirements.txt` / `requirements-dev.txt`
3. Review test logs in Actions tab

### Build Failures
If PyInstaller build fails:
1. Verify `CatLock.spec` is up to date
2. Check for missing hidden imports or data files
3. Test build locally: `pyinstaller --clean CatLock.spec`

### Release Not Created
If tag push doesn't trigger release:
1. Verify tag matches pattern `v*.*.*`
2. Check workflow permissions in repo settings
3. Review workflow run logs in Actions tab

### Manual Workflow Trigger
To manually run workflows:
1. Go to Actions tab on GitHub
2. Select the workflow
3. Click "Run workflow"
4. Select branch/tag and confirm

## Best Practices

1. **Always let tests pass before merging PRs**
   - CI workflow must succeed
   - Review coverage reports

2. **Tag from master branch only**
   - Ensure all changes are merged
   - Pull latest before tagging

3. **Write clear commit messages**
   - They become part of the auto-generated changelog
   - Format: `type(scope): Description`
   - Examples:
     - `feat: Add cat breed detection`
     - `fix: Resolve webcam reconnection issue`
     - `docs: Update installation instructions`

4. **Test releases locally first**
   - Build and test executable locally
   - Verify functionality before tagging

5. **Include breaking changes in tag message**
   - Helps users understand what changed
   - Consider using `BREAKING CHANGE:` in commit message

## Monitoring

View workflow status:
- **Badge URL:** `https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg`
- **Actions tab:** See all workflow runs, logs, and artifacts
- **Email notifications:** Configure in GitHub notification settings

## Future Enhancements

Potential additions to consider:
- [ ] Code linting job (flake8, black, mypy)
- [ ] Security scanning (Bandit, Safety)
- [ ] Automated installer creation (Inno Setup, NSIS)
- [ ] Multi-OS testing (if expanding beyond Windows)
- [ ] Automated deployment to Microsoft Store
- [ ] Performance benchmarking in CI
