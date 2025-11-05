# Immutability and Traceability Principle

## Core Principle: NEVER DELETE WITHOUT UNDERSTANDING

**CRITICAL RULE**: Never delete, modify, or move any artifact (tags, commits, files, configurations) unless you:

1. **Know exactly why it exists** - Understand its purpose and origin
2. **Know how it got there** - Trace its creation to requirements/specs/decisions  
3. **Know what depends on it** - Understand all downstream impacts
4. **Have explicit authorization** - Clear requirement or user instruction to modify it

## Git Artifacts Are Sacred

### Tags
- **IMMUTABLE**: Git tags represent published releases and MUST NEVER be moved or deleted
- **TRACEABLE**: Every tag should trace to a release decision, spec, or requirement
- **PERMANENT**: Once pushed, tags become part of the permanent project history
- **DEPENDENCIES**: CI systems, deployments, and users depend on tag stability

### Commits
- **IMMUTABLE**: Never rewrite published commit history
- **TRACEABLE**: Every commit should trace to a task, requirement, or fix
- **PERMANENT**: Commits represent the project's historical record

### Branches
- **PROTECTED**: Main/production branches require explicit permission to modify
- **TRACEABLE**: Branch operations should trace to workflow requirements

## Investigation Before Action

Before modifying ANY artifact:

1. **Trace the Origin**: 
   - Check git log for creation context
   - Look for related specs, requirements, or tasks
   - Understand the business/technical reason for existence

2. **Assess Dependencies**:
   - What systems depend on this artifact?
   - What would break if this changes?
   - Are there downstream consumers?

3. **Verify Authority**:
   - Do I have explicit permission to modify this?
   - Is there a clear requirement driving this change?
   - Have I confirmed the impact with stakeholders?

## When In Doubt: DON'T

- **Default to preservation** - If unsure, leave it alone
- **Ask for clarification** - Request explicit guidance
- **Document concerns** - Note what seems wrong but don't "fix" it
- **Escalate decisions** - Let humans make destructive choices

## Violation Consequences

Violating immutability principles:
- **Breaks traceability** - Destroys the audit trail
- **Breaks trust** - Systems and users can't rely on stability  
- **Breaks reproducibility** - Builds and deployments become unreliable
- **Breaks compliance** - May violate regulatory or quality requirements

## Examples of What NOT to Do

❌ `git tag -d v1.0.0` (deleting published release tag)  
❌ `git tag -f v1.0.0 <new-commit>` (moving published tag)  
❌ `git push --force origin main` (rewriting published history)  
❌ Deleting configuration files without understanding their purpose  
❌ Modifying artifacts because they "seem wrong" without investigation

## Examples of Proper Approach

✅ Check `git log --grep="v1.0.0"` to understand tag origin  
✅ Create new version `v1.0.1` instead of modifying `v1.0.0`  
✅ Document concerns and ask for guidance  
✅ Trace artifacts to requirements before any modifications  
✅ Verify dependencies and impacts before changes

## Emergency Procedures

If immutability is accidentally violated:
1. **Stop immediately** - Don't compound the error
2. **Document the violation** - Record what was changed and why
3. **Assess impact** - Determine what systems/users are affected  
4. **Restore if possible** - Attempt to restore original state
5. **Communicate** - Notify affected parties immediately
6. **Learn** - Update processes to prevent recurrence

---

**This principle is non-negotiable. Immutability violations represent fundamental failures in engineering discipline and project integrity.**