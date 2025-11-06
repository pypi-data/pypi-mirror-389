# Dispatch Configuration Summary - Pipeline

## ✅ Changes Implemented

Added two repository dispatch steps to Pipeline's `auto_release_on_merge.yml`:

### 1. Dispatch to market-data-ibkr
**Purpose:** Notify IBKR when Pipeline releases a new version  
**Event Type:** `core_release`  
**Payload:** 
```json
{
  "version": "0.8.X",
  "origin": "market-data-pipeline"
}
```

### 2. Notify Infra Repository
**Purpose:** Notify infrastructure when Pipeline releases (for image rebuilds)  
**Event Type:** `downstream_release`  
**Payload:**
```json
{
  "origin": "market-data-pipeline",
  "version": "0.8.X"
}
```

---

## 🔐 Token Configuration

### ⚠️ IMPORTANT: Token Name Discrepancy

**Store uses:** `REPO_DISPATCH_TOKEN`  
**Pipeline currently has:** `REPO_TOKEN`  
**Pipeline implementation uses:** `REPO_TOKEN` (for both dispatches)

### Options:

#### Option 1: Add REPO_DISPATCH_TOKEN (Recommended for consistency)
```bash
# If Store and other repos use REPO_DISPATCH_TOKEN, add it to Pipeline
gh secret set REPO_DISPATCH_TOKEN --body "<same-PAT-value-as-REPO_TOKEN>"
```

Then update the workflow to use `REPO_DISPATCH_TOKEN`:
```yaml
token: ${{ secrets.REPO_DISPATCH_TOKEN }}
```

#### Option 2: Keep using REPO_TOKEN
If `REPO_TOKEN` has the same permissions, it should work fine. Just ensure consistency.

### Token Permissions Required:
- ✅ `repo` (full repository access)
- ✅ `workflow` (trigger workflows in other repos)

---

## 📋 Current Workflow Structure

```yaml
- Checkout
- Setup Python
- Bump version
- Guard duplicate tags
- Commit and tag
- Install build tools
- Build & Check
- Publish to PyPI
- Create GitHub Release
- ⬇️ Dispatch to market-data-ibkr  ← NEW
- ⬇️ Notify Infra Repository      ← NEW
- Show environment summary
```

---

## 🔄 Expected Flow

```
[Pipeline Release]
    ↓
[PyPI Published]
    ↓
[GitHub Release Created]
    ↓
[Dispatch to IBKR] → [IBKR receives core_release event]
    ↓
[Dispatch to Infra] → [Infra receives downstream_release event]
    ↓
[Infra rebuilds images]
```

---

## ✅ Verification Checklist

- [x] Dispatch to market-data-ibkr added
- [x] Dispatch to market-data-infra added
- [x] Origin set correctly: "market-data-pipeline"
- [x] Version variable correct: `steps.bump.outputs.new_version`
- [ ] Token secret verified (REPO_TOKEN vs REPO_DISPATCH_TOKEN)
- [ ] Infra repository has listener for downstream_release
- [ ] IBKR repository has listener for core_release
- [ ] Test end-to-end dispatch

---

## 🧪 Testing

### Test the Dispatch Manually

1. **Trigger a release:**
   ```bash
   gh workflow run on_core_release.yml --ref base -f version=1.2.11
   ```

2. **Wait for auto-release to complete**

3. **Check IBKR received dispatch:**
   ```bash
   # In market-data-ibkr repo
   gh run list --limit 5
   ```

4. **Check Infra received dispatch:**
   ```bash
   # In market-data-infra repo
   gh run list --limit 5
   ```

---

## 📝 Still TODO

### For Core Repository
Add dispatch to market-data-ibkr in Core's release workflow.  
See: `CORE_DISPATCH_CONFIGURATION.md`

### For Infra Repository
Ensure workflow exists to handle `downstream_release` events:

```yaml
on:
  repository_dispatch:
    types: [downstream_release]

jobs:
  rebuild:
    runs-on: ubuntu-latest
    steps:
      - name: Log release info
        run: |
          echo "Release from: ${{ github.event.client_payload.origin }}"
          echo "Version: ${{ github.event.client_payload.version }}"
      
      - name: Pull latest images
        run: make rebuild-all
```

### For IBKR Repository
Ensure workflow exists to handle `core_release` events:

```yaml
on:
  repository_dispatch:
    types: [core_release]

jobs:
  update-core:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Update Core dependency
        run: |
          # Similar to Pipeline's on_core_release.yml
```

---

## 🎯 Summary

✅ **Pipeline is configured** to dispatch to both IBKR and Infra on release  
⚠️ **Token verification needed** - check if REPO_DISPATCH_TOKEN should be added  
⏳ **Pending** - Core dispatch configuration (see CORE_DISPATCH_CONFIGURATION.md)  
⏳ **Pending** - Verify target repos have listeners configured  

---

## 📊 Complete Architecture

```
[Core Release] → [Pipeline, Store, Orchestrator]
                      ↓
                [Each releases independently]
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
    [to IBKR]    [to Infra]   [to other services]
```

**Pipeline specifically:**
```
Core v1.2.X released
    ↓
Pipeline receives dispatch
    ↓
Pipeline bumps to v0.8.X
    ↓
Pipeline publishes to PyPI
    ↓
Pipeline dispatches to:
    ├─→ IBKR (core_release)
    └─→ Infra (downstream_release)
```


