# CodeSentinel AI Agent Instructions

CodeSentinel is a security-first automated maintenance and monitoring system with the core principle: **SECURITY > EFFICIENCY > MINIMALISM**.

## Fundamental Policy Hierarchy

**Priority Order (Descending Importance):**

1. **🎯 CORE CONCEPTS** (Absolute Priority)
   - **SECURITY** > **EFFICIENCY** > **MINIMALISM**
   - These three principles guide ALL decisions
   - Security always overrides efficiency and minimalism
   - Efficiency cannot compromise security
   - Minimalism serves efficiency, not vice versa

2. **⚠️ PERMANENT DIRECTIVES**
   - Non-negotiable security rules
   - Credential management requirements
   - Audit logging mandates

3. **📋 PERSISTENT POLICIES**
   - Non-destructive operations
   - Feature preservation
   - Style preservation
   - Security-first decision making

**Dev Audit Execution:**
- Always executed thoroughly and comprehensively
- Heavy focus on the three core concepts
- Complies with all directives and policies EXCEPT where they would explicitly violate a core concept
- This hierarchy is fundamental to CodeSentinel's operating policy

## Architecture Overview

The codebase follows a dual-architecture pattern:

- **`codesentinel/`** - Core Python package with CLI interface (`codesentinel`, `codesentinel-setup`)
- **`tools/codesentinel/`** - Comprehensive maintenance automation scripts
- **`tools/config/`** - JSON configuration files for alerts, scheduling, and policies
- **`tests/`** - Test suite using pytest with unittest fallback

## Key Commands

### Development Audit
```bash
# Run interactive audit
codesentinel !!!!

# Get agent-friendly context for remediation
codesentinel !!!! --agent
```

### Maintenance Operations
```bash
# Daily maintenance workflow
python tools/codesentinel/scheduler.py --schedule daily

# Weekly maintenance (security, dependencies, performance)
python tools/codesentinel/scheduler.py --schedule weekly
```

## Core Principles

### SECURITY ⚠️ **PERMANENT DIRECTIVES**

**FORBIDDEN ACTIONS - NEVER DO THESE:**
- ❌ **NEVER store plain text passwords or tokens in files**
- ❌ **NEVER store passwords or tokens in executable files**
- ❌ **NEVER include credentials in code, comments, or documentation**
- ❌ **NEVER commit credentials to the repository**

**REQUIRED PRACTICES:**
- ✅ Use environment variables for sensitive data (CODESENTINEL_* prefix)
- ✅ Reference credentials by hash/key from secure storage
- ✅ All credentials in `.gitignore` if file-based
- ✅ Audit logging for all operations with timestamps
- ✅ Configuration validation with secure defaults
- ✅ Automated dependency vulnerability detection

### EFFICIENCY
- Avoid redundant code and duplicate implementations
- Consolidate multiple versions of similar functionality
- Clean up orphaned test files and unused scripts
- Optimize import structures and module organization

### MINIMALISM
- Remove unnecessary dependencies
- Archive deprecated code to quarantine_legacy_archive/
- Maintain single source of truth for each feature
- Keep codebase focused and maintainable

## Persistent Policies

**Priority: Level 3** (Below Core Concepts and Permanent Directives)

When working with this codebase:

1. **NON-DESTRUCTIVE**: Never delete code without archiving first (unless security violation)
2. **FEATURE PRESERVATION**: All existing functionality must be maintained (unless security violation)
3. **STYLE PRESERVATION**: Respect existing code style and patterns (unless security violation)
4. **SECURITY FIRST**: Security concerns always take priority over all other considerations

**Note:** These policies may be overridden by Core Concepts or Permanent Directives when necessary.

## Agent-Driven Remediation

When `codesentinel !!!! --agent` is run, you will receive comprehensive audit context with:

- Detected issues (security, efficiency, minimalism)
- Remediation hints with priority levels
- Safe-to-automate vs. requires-review flags
- Step-by-step suggested actions

Your role is to:

1. **ANALYZE**: Review each issue with full context
2. **PRIORITIZE**: Focus on critical/high priority items first  
3. **DECIDE**: Determine safe vs. requires-review actions
4. **PLAN**: Build step-by-step remediation plan
5. **EXECUTE**: Only perform safe, non-destructive operations
6. **REPORT**: Document all actions and decisions

## Safe Actions (can automate)

- Moving test files to proper directories
- Adding entries to .gitignore
- Removing __pycache__ directories
- Archiving confirmed-redundant files to quarantine_legacy_archive/

## Requires Review (agent decision needed)

- Deleting or archiving potentially-used code
- Consolidating multiple implementations
- Removing packaging configurations
- Modifying imports or entry points

## Forbidden Actions

- Deleting files without archiving
- Forcing code style changes
- Removing features without verification
- Modifying core functionality without explicit approval

## Integration Points

### GitHub Integration
- Repository-aware configuration detection
- Copilot instructions generation (this file)
- PR review automation capabilities

### Multi-Platform Support  
- Python 3.13/3.14 requirement with backward compatibility
- Cross-platform paths using `pathlib.Path` consistently
- PowerShell/Python dual execution support for Windows/Unix

## When Modifying This Codebase

1. **Understand the dual architecture** - Core package vs. tools scripts serve different purposes
2. **Maintain execution order** - Change detection dependency is critical
3. **Preserve configuration structure** - JSON configs have specific schemas
4. **Test both execution paths** - pytest and unittest must both work
5. **Follow security-first principle** - Never compromise security for convenience
6. **Update timeout values carefully** - Task timeouts affect workflow reliability
