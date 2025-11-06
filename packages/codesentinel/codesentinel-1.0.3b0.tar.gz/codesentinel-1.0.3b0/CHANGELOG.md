# Changelog

All notable changes to CodeSentinel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1.beta] - 2025-11-03

### Security

- Do not persist sensitive secrets to disk by default (email passwords, GitHub access tokens) when saving configuration
- Add environment variable fallbacks for secrets:
  - `CODESENTINEL_EMAIL_USERNAME`, `CODESENTINEL_EMAIL_PASSWORD`
  - `CODESENTINEL_SLACK_WEBHOOK`
- Enforce Slack webhook allowlist validation (https, hooks.slack.com or *.slack.com, /services/ path) in GUI and runtime to reduce SSRF risk
- Restrict config file permissions on POSIX to 0600 on save
- Add `codesentinel.json` to `.gitignore` and ignore `*.log` by default to avoid accidental commits of secrets/logs

### Changed

- Bump version to 1.0.1
- Enhanced GUI branding with CodeSentinel logo and attribution footer
- Improved thumbnail sizing (150px) for better visual consistency
- Fixed layout issues in navigation sidebar

### Fixed

- Resolved pytest configuration to exclude `quarantine_legacy_archive` from test discovery
- Updated test assertions to dynamically reference package `__version__` constant
- All 18 core tests now pass successfully

## [1.0.0] - 2024-12-XX

### Added

- Initial release of CodeSentinel
- Core security scanning functionality
- Automated maintenance tasks
- Multi-channel alerting system (email, Slack, console, file)
- Configuration management with validation
- Command-line interface with comprehensive commands
- GUI setup wizard with Tkinter
- Terminal setup wizard
- Modular architecture with core, CLI, GUI, and utility modules
- Comprehensive documentation and setup guides
- CI/CD pipeline with GitHub Actions
- Test suite with unit and integration tests
- MIT license

### Features

- Security vulnerability scanning
- Automated maintenance scheduling (daily/weekly/monthly)
- Email alerts via SMTP
- Slack webhook integration
- Console and file logging
- JSON-based configuration management
- Interactive setup wizards (terminal and GUI)
- GitHub Copilot integration instructions
- Development environment setup scripts

### Technical Details

- Python 3.8+ support
- Modern packaging with pyproject.toml
- Type hints and mypy support
- Black code formatting
- pytest testing framework
- Comprehensive error handling and logging
