# Repository Configuration Instructions

This document outlines the manual GitHub repository configuration needed to enforce CI/CD workflows.

## Branch Protection Rules

To ensure all PRs run the CI workflow before merging, configure the following branch protection rules:

### For the `main` branch:

1. Go to **Settings** → **Branches** in your GitHub repository
2. Click **Add rule** or edit existing rule for `main`
3. Configure the following settings:

   - ✅ **Require a pull request before merging**
     - ✅ Require approvals: 1
     - ✅ Dismiss stale PR approvals when new commits are pushed
     - ✅ Require review from code owners (if CODEOWNERS file exists)

   - ✅ **Require status checks to pass before merging**
     - ✅ Require branches to be up to date before merging
     - **Required status checks:**
       - `backend-tests`
       - `code-quality`

   - ✅ **Require conversation resolution before merging**
   - ✅ **Require signed commits** (recommended)
   - ✅ **Require linear history** (recommended)
   - ✅ **Do not allow bypassing the above settings**
   - ✅ **Restrict pushes that create files**

## Repository Rules (Alternative/Additional Configuration)

GitHub's newer Repository Rules provide more granular control:

1. Go to **Settings** → **Rules** → **Rulesets**
2. Click **New ruleset**
3. Configure:
   - **Name**: `Main branch protection`
   - **Enforcement status**: Active
   - **Target branches**: `main`
   - **Rules**:
     - ✅ Require a pull request before merging
     - ✅ Require status checks to pass
     - ✅ Block force pushes
     - ✅ Require conversation resolution before merging

## Required Status Checks

The CI workflow creates the following status checks that should be required:

- `backend-tests` - Backend tests on Python 3.13.2
- `code-quality` - Linting, formatting, and type checking

## Additional Recommendations

### Enable Dependabot Security Updates
1. Go to **Settings** → **Security & analysis**
2. Enable **Dependency graph**
3. Enable **Dependabot alerts**
4. Enable **Dependabot security updates**

### Auto-merge Setup
Consider enabling auto-merge for Dependabot PRs that pass all checks:
1. Go to **Settings** → **General**
2. Enable **Allow auto-merge**

### CODEOWNERS File
Create a `.github/CODEOWNERS` file to automatically request reviews:
```
# Global owners
* @maxshowarth

# Backend specific
backend/ @maxshowarth

# CI/CD workflows
.github/ @maxshowarth
```

## Testing the Configuration

After setting up the rules:

1. Create a test branch and PR
2. Verify that the CI workflow runs automatically
3. Confirm that merging is blocked until all status checks pass
4. Test that the workflow fails appropriately for breaking changes

## Troubleshooting

- If status checks don't appear, ensure the workflow has run at least once
- Check that branch names match exactly (case-sensitive)
- Verify webhook delivery in **Settings** → **Webhooks** if workflows don't trigger
- Review **Actions** tab for workflow execution logs