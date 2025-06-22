# Secret Detection and Management Guide

This document explains how to handle secrets detected by the pre-commit hooks and gitleaks scanning in the NYC Landmarks Vector DB project.

## OThe secret detection system is now properly configured and working. All previously detected issues have been resolved:

1. ✅ **Real API tokens in documentation files** - Redacted with safe examples
1. ✅ **Example tokens that look too real** - Replaced with obvious placeholders
1. ✅ **Development credentials in .env files** - Excluded from scanning (gitignored)
1. ✅ **Private key examples in documentation** - Fixed to avoid triggering detection

The pre-commit hooks now pass cleanly while still detecting real secrets if accidentally added.

### CI/CD Integration

The secret detection is fully integrated into the GitHub Actions CI/CD pipeline:

- **Automatic Installation**: The CI workflow automatically installs `gitleaks` and all dependencies
- **Pull Request Checks**: Secret scanning runs on every pull request
- **Branch Protection**: Prevents merging if secrets are detected

See `.github/workflows/pre-commit.yml` for the complete CI configuration.

The project uses gitleaks to automatically scan for API keys, tokens, credentials, and other secrets in all files, including documentation. This helps prevent accidental exposure of sensitive information.

## How Secret Detection Works

### Pre-commit Hook Integration

The pre-commit hooks automatically run gitleaks when you try to commit changes:

```bash
# This will automatically run when you commit
git commit -m "Your commit message"

# Or run manually on all files
pre-commit run gitleaks-scan --all-files

# Or run gitleaks directly
gitleaks detect --source=. --config=.gitleaks.toml --no-git
```

### Configuration

Secret detection is configured in:

- `.gitleaks.toml` - Main gitleaks configuration
- `.pre-commit-config.yaml` - Pre-commit hook configuration

## When Secrets Are Detected

If secrets are found, you'll see output like:

```
❌ Secrets detected! Please review and remove any exposed API keys, tokens, or credentials.

Finding:     TF_TOKEN_NYC_LANDMARKS=REAL_TOKEN_DETECTED_HERE
Secret:      REAL_TOKEN_DETECTED_HERE
RuleID:      terraform-cloud-token
File:        memory-bank/terraform_cloud_integration.md
Line:        17
```

## How to Handle Detected Secrets

### 1. Real Secrets (Immediate Action Required)

If a real API key or secret is detected:

1. **DO NOT COMMIT THE FILE**
1. **Remove or redact the secret immediately**
1. **Rotate the compromised secret if it was ever committed**
1. **Use environment variables or secure secret management instead**

Example - Replace this:

```bash
# ❌ BAD - Real secret in code
OPENAI_API_KEY=sk-1234567890abcdef...
```

With this:

```bash
# ✅ GOOD - Reference to environment variable
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Documentation Examples (Handle with Care)

For documentation that includes example tokens:

#### Option A: Use Obviously Fake Examples

```bash
# ✅ GOOD - Clearly fake example
TF_TOKEN_NYC_LANDMARKS=example_token_replace_with_real_value
```

#### Option B: Redact Parts of Real Examples

```bash
# ✅ GOOD - Redacted real example
TF_TOKEN_NYC_LANDMARKS=Q4so3pb31QpLuA.atlasv1.xFOxhBihsE...REDACTED_FOR_SECURITY
```

#### Option C: Add to Allowlist (Use with Extreme Caution)

If you must include a real-looking token for documentation purposes:

1. **Verify it's not a real, active secret**
1. **Add it to the allowlist in `.gitleaks.toml`**:

```toml
[allowlist]
regexes = [
    '''EXAMPLE_REDACTED_TOKEN_PATTERN''',
]
```

**⚠️ WARNING**: Only do this if you're absolutely certain the token is not real and active.

### 3. Template Files

For template files with placeholder secrets:

- Use obvious placeholders like `YOUR_API_KEY_HERE`
- These are automatically allowlisted in our configuration

## Common Secret Types Detected

Our configuration detects:

- **Terraform Cloud tokens**: `*.atlasv1.*` format
- **OpenAI API keys**: `sk-*` format
- **Pinecone API keys**: `pcsk_*` format
- **Private keys**: PEM format files (BEGIN/END PRIVATE KEY blocks)
- **Generic API keys**: High-entropy strings assigned to variables
- **Environment variables**: `API_KEY=`, `SECRET=`, `TOKEN=`, etc.

## Best Practices

### 1. Use Environment Variables

```bash
# In .env file (which should be .gitignore'd)
OPENAI_API_KEY=your_real_api_key_here

# In code
api_key = os.getenv('OPENAI_API_KEY')
```

### 2. Use Secret Management Services

- Google Cloud Secret Manager
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

### 3. Documentation Best Practices

- Use clearly fake examples: `sk-example123...`
- Redact real examples: `sk-abc123...REDACTED...`
- Reference environment variables: `$OPENAI_API_KEY`
- Use configuration file examples with placeholders

### 4. Template Files

- Use `.sample` or `.template` extensions
- Include instructions for users to copy and fill in real values
- Use obvious placeholders like `YOUR_KEY_HERE`

## Bypassing Secret Detection (Emergency Only)

If you absolutely must bypass secret detection temporarily:

```bash
# Skip pre-commit hooks entirely (NOT RECOMMENDED)
git commit --no-verify -m "Emergency commit"

# Skip only gitleaks
SKIP=gitleaks-scan git commit -m "Your message"
```

**⚠️ Only use this in emergencies and ensure secrets are removed before pushing!**

## Testing Secret Detection

To test if the secret detection is working:

```bash
# Run on all files
pre-commit run gitleaks-scan --all-files

# Run gitleaks directly
gitleaks detect --source=. --config=.gitleaks.toml --no-git

# Test specific file
gitleaks detect --source=path/to/file --config=.gitleaks.toml --no-git
```

## Current Status

The secret detection system is now properly configured and working. All previously detected issues have been resolved:

1. ✅ **Real API tokens in documentation files** - Redacted with safe examples
1. ✅ **Example tokens that look too real** - Replaced with obvious placeholders
1. ✅ **Development credentials in .env files** - Excluded from scanning (gitignored)

The pre-commit hook now passes cleanly while still detecting real secrets if accidentally added.

## Getting Help

If you need help with secret detection:

1. **Check this guide first**
1. **Review the gitleaks output for specific guidance**
1. **Ask the team about proper secret management practices**
1. **Consider if the secret is really needed in the file**

Remember: **When in doubt, don't commit secrets!**
