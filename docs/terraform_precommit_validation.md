# Terraform Pre-commit Validation

This document describes the Terraform validation hooks configured in the pre-commit setup.

## Pre-commit Hooks for Terraform

The following Terraform validation hooks are now configured in `.pre-commit-config.yaml`:

### 1. Terraform Format (`terraform_fmt`)

- **Purpose**: Automatically formats Terraform files to canonical format
- **Files**: `*.tf` and `*.tfvars` files
- **When**: Runs on every commit
- **Action**: Automatically fixes formatting issues

### 2. Terraform Validate (`terraform_validate`)

- **Purpose**: Validates Terraform configuration syntax and consistency
- **Files**: `*.tf` and `*.tfvars` files
- **When**: Runs on every commit
- **Action**: Checks for syntax errors, missing variables, invalid references

## How It Works

### Automatic Validation on Commit

When you commit changes to any Terraform files, the hooks will automatically:

1. **Format** all Terraform files using `terraform fmt`
1. **Validate** the Terraform configuration using `terraform validate`
1. **Block the commit** if any validation errors are found

### Manual Validation

You can also run the hooks manually:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run only Terraform formatting
pre-commit run terraform_fmt --all-files

# Run only Terraform validation
pre-commit run terraform_validate --all-files

# Run on specific files
pre-commit run --files infrastructure/terraform/main.tf
```

## Configuration Files

### `.pre-commit-config.yaml`

Contains the hook configuration:

```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.1
  hooks:
    - id: terraform_fmt
      files: (\.tf|\.tfvars)$
    - id: terraform_validate
      files: (\.tf|\.tfvars)$
      args:
        - --args=-no-color
```

### `.tflint.hcl`

TFLint configuration for additional linting rules:

- Google Cloud Platform specific rules
- Terraform best practices
- Variable and output documentation requirements
- Naming convention enforcement

## Benefits

### 1. Code Quality

- Ensures consistent formatting across all Terraform files
- Prevents syntax errors from being committed
- Enforces Terraform best practices

### 2. Team Collaboration

- All team members use the same formatting standards
- Reduces diff noise from formatting changes
- Catches errors early in the development process

### 3. CI/CD Integration

- Pre-commit hooks run before code reaches CI/CD
- Faster feedback loop for developers
- Reduces failed pipeline runs due to formatting/syntax issues

## Example Usage

### Successful Validation

```bash
$ git commit -m "Update dashboard configuration"
Terraform format.........................................................Passed
Terraform validate.......................................................Passed
[main abc1234] Update dashboard configuration
 1 file changed, 2 insertions(+)
```

### Failed Validation

```bash
$ git commit -m "Add new resource"
Terraform format.........................................................Failed
- hook id: terraform_fmt
- files were modified by this hook

Terraform validate.......................................................Failed
- hook id: terraform_validate
- exit code: 1

Error: Invalid resource type
...
```

## Troubleshooting

### Common Issues

1. **Hook Installation**

   ```bash
   pre-commit install
   ```

1. **Update Hook Versions**

   ```bash
   pre-commit autoupdate
   ```

1. **Skip Hooks (Emergency)**

   ```bash
   git commit --no-verify -m "Emergency fix"
   ```

1. **Clear Cache**

   ```bash
   pre-commit clean
   ```

### Terraform-Specific Issues

1. **Module Not Initialized**

   - Run `terraform init` in the relevant directory
   - Hooks require initialized Terraform state

1. **Missing Providers**

   - Ensure all required providers are configured
   - Check `terraform init` has been run

1. **Variable Validation**

   - Ensure all required variables have default values or are provided
   - Check `terraform.tfvars` file exists and is properly configured

## File Structure

The hooks validate files in these locations:

```
infrastructure/
├── terraform/
│   ├── main.tf          # ✓ Validated
│   ├── variables.tf     # ✓ Validated
│   ├── outputs.tf       # ✓ Validated
│   └── terraform.tfvars # ✓ Validated
└── .tflint.hcl         # Configuration for TFLint
```

## Integration with VS Code

The pre-commit hooks work seamlessly with the VS Code Terraform extension:

1. **Format on Save**: VS Code formats files automatically
1. **Pre-commit Validation**: Hooks ensure consistency across all commits
1. **Problem Detection**: Both tools highlight validation issues

This provides multiple layers of validation for robust Terraform development.
