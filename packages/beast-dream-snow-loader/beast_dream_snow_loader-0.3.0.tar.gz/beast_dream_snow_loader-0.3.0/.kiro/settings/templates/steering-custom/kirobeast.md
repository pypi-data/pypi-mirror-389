# KiroBeast Configuration

**KiroBeast** = Kiro (BeastSpec workflow) + Beast (Beastmaster framework)

## Overview

KiroBeast integrates the BeastSpec/Kiro spec-driven development workflow with the Beastmaster framework patterns and principles.

## Quorum Principle Integration

**Quorum Principle** (for Beast Collaboration Network):
- **In physics**: Need quorum to verify results - multiple independent verifications
- **In teams**: Teams of three provide better reliability than pairs
- **In Beast Collaboration Network**: Need at least 3 "beasts" for quorum:
  - Could be: 1 human + 2 LLMs
  - Could be: 3 LLMs
  - Without quorum, you're just taking a chance (single point of failure, hallucination risk)

**Why it matters**: Multiple perspectives catch errors, hallucinations, and blind spots.

**Background Observer Pattern** (Third Beast for Quorum):
- **Background LLM** watching everything spawned from IDE instance
- **Maintains real-time/near-real-time DAG** of all activities and changes
- **Context window management** via continuous questions:
  - "What changed?"
  - "What's the current state?"
  - "What needs attention?"

## Integration Points

### Kiro Commands + Beast Principles
- `/kiro:spec-init` - Create specs following Beast patterns
- `/kiro:spec-requirements` - Requirements using Beast domain patterns
- `/kiro:spec-design` - Design aligned with Beast architecture
- `/kiro:validate-gap` - Validation using Beast quorum principles

### Beast Patterns in Specs
- **Naming**: `nkllon/beast-*` repositories
- **Credentials**: 1Password "Beastmaster" vault
- **Quality**: PyPI publishing, SonarCloud, GitHub Actions
- **Architecture**: Domain-driven patterns, type safety, TDD

### Quorum in Development
1. **Spec Creation**: Multiple perspectives (LLMs/humans) review requirements
2. **Design Review**: Quorum validates design decisions
3. **Implementation**: Background observer tracks changes
4. **Validation**: Multiple validators check alignment

## Configuration

### .kiro/steering/ Structure
- `product.md` - Product vision (Beast-focused)
- `tech.md` - Technology stack (Beast patterns)
- `structure.md` - Project organization (Beast conventions)

### .kiro/specs/ Structure
- Feature specs follow Beast domain patterns
- Validation uses quorum principles
- Background observer maintains DAG of changes

## Usage

When creating new features:

1. **Initialize**: `/kiro:spec-init <feature>` - Creates Beast-compliant spec
2. **Requirements**: `/kiro:spec-requirements <feature>` - Uses Beast domain patterns
3. **Design**: `/kiro:spec-design <feature>` - Aligns with Beast architecture
4. **Validate**: `/kiro:validate-gap <feature>` - Quorum validation

## Background Observer

The background observer (beast-watcher) maintains:
- Real-time DAG of all activities
- Context window management
- Change tracking
- Quorum validation triggers

