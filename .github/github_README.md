# GitHub Workflows

This directory contains GitHub Actions workflows for the AI Email Categorizer Backend.

## Available Workflows

### CrashLens Analysis (`crashlens-scan.yml`)

A comprehensive security and performance analysis workflow that:

- **Security Scanning**: 
  - Dependency vulnerability checks using Safety
  - Static security analysis with Bandit
  - Additional security patterns with Semgrep

- **Performance Analysis**:
  - API response time monitoring
  - Log-based performance tracking
  - Bottleneck identification

- **Integration Testing**:
  - CrashLens core functionality tests
  - Integration test execution
  - API usage pattern analysis

- **Automated Reporting**:
  - Generates comprehensive analysis reports
  - Uploads artifacts for detailed review
  - Comments on pull requests with results
  - Provides workflow summaries

#### Triggers

- **Push**: Runs on pushes to `main` and `raj` branches
- **Pull Request**: Runs on PRs targeting `main`
- **Scheduled**: Daily at 6 AM UTC
- **Manual**: Can be triggered manually with scan type options:
  - `full` - Complete analysis (default)
  - `logs-only` - Log analysis only
  - `security` - Security-focused scan

#### Artifacts

The workflow generates and uploads:
- Security scan reports (JSON format)
- Performance analysis results
- Log analysis summaries
- Comprehensive markdown report

#### Configuration

The workflow uses:
- `crashlens_config.yaml` - CrashLens configuration
- `requirements.txt` - Main dependencies
- `crashlens_requirements.txt` - CrashLens-specific dependencies

## Usage

The workflows run automatically based on their triggers. For manual execution:

1. Go to the **Actions** tab in GitHub
2. Select the **CrashLens Analysis** workflow
3. Click **Run workflow**
4. Choose scan type and branch
5. Review results in the workflow summary and artifacts
