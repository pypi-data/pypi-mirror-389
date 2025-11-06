# CodeSentinel

CodeSentinel is a cross-platform application that integrates with VS Code or any major IDE to provide a secure, automated, self-healing development environment.

## Core Features

- **Security-First Architecture**: Automated vulnerability scanning and security monitoring
- **Multi-Channel Alerts**: Console, file logging, email, and Slack integration
- **GitHub Integration**: Seamless GitHub and Copilot AI support
- **IDE Integration**: Support for VS Code, PyCharm, IntelliJ, Visual Studio, and more
- **Intelligent Audit**: Development audit with `!!!!` command for automated remediation
- **Process Monitoring**: Low-cost daemon prevents orphaned processes and resource leaks
- **Maintenance Automation**: Scheduled tasks for daily, weekly, and monthly operations

### Process Monitoring

Built-in background daemon that automatically:

- Tracks CodeSentinel-spawned processes
- Detects and terminates orphaned processes
- Cleans up zombie/defunct processes
- Minimal resource usage (<0.1% CPU, ~1-2MB memory)

Active whenever CodeSentinel is running to prevent resource leaks. See `docs/PROCESS_MONITOR.md` for details.

## Installation

```bash
pip install codesentinel
```

## Quick Start

```bash
# Run setup wizard
codesentinel-setup

# Check status
codesentinel status

# Run development audit
codesentinel !!!!
```

## Documentation

- [Installation Guide](INSTALLATION.md)
- [Security Policy](SECURITY.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Process Monitor](docs/PROCESS_MONITOR.md)
- [Changelog](CHANGELOG.md)

## Principles

**SECURITY > EFFICIENCY > MINIMALISM**

CodeSentinel follows a security-first approach with emphasis on efficiency and minimal overhead.
