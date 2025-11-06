# Core Repository Dispatch Configuration

## 🎯 Objective
Configure Core repository to dispatch release events to market-data-ibkr when Core is released.

---

## 📝 Changes Required in Core Repository

### File to Modify
`.github/workflows/auto_release_on_merge.yml` (or equivalent release workflow)

### Change to Add

Add the following step **after** the "Create GitHub Release" step:

```yaml
      - name: Dispatch to market_data_ibkr
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.REPO_TOKEN }}
          repository: mjdevaccount/market_data_ibkr
          event-type: core_release
          client-payload: |
            {
              "version": "${{ steps.bump.outputs.new_version }}",
              "origin": "market-data-core"
            }
```

### ⚠️ Important: Verify Key Names

Before adding, verify in Core's workflow:

1. **Version Output Variable**: Check what the version step ID and output name are
   - Look for: `id: bump` (or similar)
   - Verify output: `${{ steps.bump.outputs.new_version }}` (or could be `version`, `tag`, etc.)

2. **Step Placement**: Add after GitHub Release creation but before summary/cleanup steps

3. **Token**: Verify `REPO_TOKEN` secret exists in Core repository
   - Run: `gh secret list` in Core repo
   - If not present, add it with same PAT used in other repos

---

## 📋 Example: Full Context

Here's what the section should look like (with context):

```yaml
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          python -m twine upload dist/* --skip-existing

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v${{ steps.bump.outputs.new_version }}
          name: Release v${{ steps.bump.outputs.new_version }}
          body: |
            ## Release v${{ steps.bump.outputs.new_version }}
            ...
          files: |
            dist/*.whl
            dist/*.tar.gz

      # ⬇️ ADD THIS STEP ⬇️
      - name: Dispatch to market_data_ibkr
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.REPO_TOKEN }}
          repository: mjdevaccount/market_data_ibkr
          event-type: core_release
          client-payload: |
            {
              "version": "${{ steps.bump.outputs.new_version }}",
              "origin": "market-data-core"
            }

      - name: Show environment summary
        if: always()
        run: |
          echo "Release complete"
```

---

## 🔐 Token Requirements

The `REPO_TOKEN` must have these permissions:
- ✅ `repo` (full repository access)
- ✅ `workflow` (trigger workflows in other repos)

This is typically a Personal Access Token (PAT) with appropriate scopes.

---

## ✅ Verification Steps

After adding to Core:

1. **Commit and push** the workflow change
2. **Test manually** (if Core supports manual release trigger)
3. **Check dispatch**: In market-data-ibkr, verify workflow was triggered
4. **Monitor logs**: Check Core workflow logs for dispatch step

### Test Command (if manual trigger available):
```bash
# In Core repo
gh workflow run <release-workflow-name> --ref <branch>

# Then check in IBKR repo
gh run list --limit 5
```

---

## 📊 Current Status

| Repository | Dispatch Added | Tested | Status |
|------------|---------------|---------|---------|
| **market-data-core** | ⏳ Pending | ⏳ Pending | Awaiting implementation |
| **market-data-pipeline** | ✅ Done | ⏳ Pending | Ready for testing |

---

## 🔄 Expected Flow After Implementation

```
[Core Release v1.2.X]
    ↓
[auto_release_on_merge.yml runs]
    ↓
[PyPI Publish]
    ↓
[GitHub Release Created]
    ↓
[Dispatch to market-data-ibkr] ← NEW STEP
    ↓
[IBKR receives core_release event]
    ↓
[IBKR workflow triggered]
```

---

## 🚨 Troubleshooting

### Dispatch not triggering?
1. Check `REPO_TOKEN` exists: `gh secret list`
2. Verify token permissions (needs `workflow` scope)
3. Check workflow logs for dispatch step errors
4. Ensure target repo has `on: repository_dispatch` trigger

### Wrong version being sent?
1. Verify step ID: `id: bump` (or whatever it's called in Core)
2. Check output name: `outputs.new_version` vs `outputs.version`
3. Look at workflow logs to see actual values

---

## 📝 Notes

- The `event-type` must be `core_release` to match IBKR's workflow trigger
- The `origin` field helps IBKR identify the source of the release
- Client payload is JSON format (use `|` for multiline in YAML)
- Using `REPO_TOKEN` instead of `GITHUB_TOKEN` is required for cross-repo triggers


