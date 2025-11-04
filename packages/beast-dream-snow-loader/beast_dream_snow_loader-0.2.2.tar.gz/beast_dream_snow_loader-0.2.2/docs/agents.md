# Agent Communication Patterns & Principles

## Table of Contents

1. [Key Concepts](#key-concepts)
2. [Quick Start for Agents](#quick-start-for-agents)
3. [Memes as Architectural Principles](#memes-as-architectural-principles)
4. [Collaborative Debugging Methodology](#collaborative-debugging-methodology)
5. [Emotional Health & Gamification](#emotional-health--gamification)
6. [Principle-Level vs. Requirements-Level](#principle-level-vs-requirements-level)
7. [Vector-Level Principles: Proof, Scale, Trust, Together](#vector-level-principles-proof-scale-trust-together)
8. [Project-Specific Guidance Patterns](#project-specific-guidance-patterns)
9. [Universal Patterns for Beast Projects](#universal-patterns-for-beast-projects)
10. [Agent Guidance Checklist](#agent-guidance-checklist)
11. [References](#references)

## Key Concepts

Before diving into the patterns and principles, here are the core concepts used throughout this document:

- **Beast**: The architectural framework and set of principles that guide development decisions across beast projects. It represents a pattern-driven, principle-level approach to system design.
- **Beastmaster**: The strategic orchestrator role in the agent network, focused on accessibility and user-centric interfaces. Also refers to the 1Password vault name for project credentials.
- **Beast Mode**: A collaborative agent system using Redis pub/sub for multi-agent communication and coordination.
- **BeastSpec**: The spec-driven development workflow system (forked from cc-sdd) that provides structured feature development through `/kiro:*` commands.
- **nkllon**: The GitHub organization/namespace prefix for beast projects (e.g., `nkllon/beast-*` repositories).
- **Catbert Lemonade**: A pattern for creating OSS projects that answer recruiter/client questions while demonstrating capability - "deliver while you sell and sell while you deliver."
- **Kiro**: Informally used as a verb meaning "to do spec-driven development" (e.g., "Can you kiro that feature?"). Also refers to the Kiro IDE and its spec format compatibility.

## Quick Start for Agents

When working on a beast project, follow these essential steps:

1. **Read Project Context**: Check for project-specific `AGENTS.md` or `agents.md` files
2. **Understand Domain Vocabulary**: Review the [Key Concepts](#key-concepts) section above
3. **Follow Beast Principles**: Apply principle-level thinking, not just step-by-step following
4. **Use Quality Gates**: Never bypass quality checks (no `--no-verify` flags)
5. **Verify Changes**: Check actual data first, verify each change before moving on
6. **Ask Questions**: When uncertain, ask clarifying questions instead of repeating fixes

See the [Agent Guidance Checklist](#agent-guidance-checklist) for a complete checklist.

## Memes as Architectural Principles

Memes serve as principles that provide immediate handles for decision-making at an architectural level, rather than detailed requirement specifications. They are not useful to simple systems, but well-endowed LLMs can pick up contextual meaning and apply it appropriately.

### Principle-Level Communication

When domain-specific vocabulary is used consistently, it carries architectural meaning:

- **"Beast"** → Implies specific architectural characteristics within the Beastmaster framework context
- **"Beast thing"** → A type/pattern within that architecture  
- **"Apply beast principles"** → Carries an entire decision-making framework
- **"Look before you leap"** → Check actual data, read files, verify patterns before making changes or assumptions

### How LLMs Interpret This

For LLMs with sufficient context awareness:

1. **Recognize domain vocabulary** - Terms like `beast`, `nkllon` (GitHub organization), `beastmaster`, etc. signal architectural context
2. **Infer patterns** - From context, understand what architectural patterns are implied
3. **Apply principles** - Make decisions aligned with the architectural principles, not just follow steps

### Why This Works

**Scalability**: Instead of a 50-point checklist, saying "make it beast-compliant" communicates entire architectural patterns.

**Consistency**: Principles ensure decisions align across projects without explicit documentation.

**Emergent behavior**: LLMs can apply principles in new situations they haven't explicitly seen before.

### Example: Beast Principles in Practice

From our work on this project:

- **Naming conventions**: `nkllon/beast-*` repositories
- **Patterns**: 1Password integration, PyPI/SonarCloud setup
- **Architectural features**: Specific characteristics implied by "beast" context

These align with "beast principles" even without explicit documentation, because the context and patterns communicate the architecture.

### Codification vs. Context

**These principles don't need explicit codification** - they work as contextual patterns that well-endowed systems can infer.

However, documenting them (like this file) helps:
- Make the patterns more explicit for reference
- Enable calling them from other contexts
- Refine understanding through articulation

### Serious Play & Creative Emergence

During collaborative problem-solving, interesting creative solutions emerge from:
- Iterative debugging with playful interaction
- Principle-driven decisions rather than specification-driven
- Meta-awareness of boundaries while maintaining productive collaboration

This "serious play" leads to better outcomes than rigid specification-driven development.

### Collaborative Debugging Methodology

**Key Principle: Go Slow, Verify Evidence**

When debugging collaboratively (AI + Human), follow this methodology:

1. **Check Actual Data First**: Before hypothesizing, observe what's actually happening:
   - What are the actual values?
   - What is the system actually returning?
   - What does the evidence show?
   - Don't assume - verify

2. **Verify Each Change**: After making changes:
   - Check that the change is actually in place
   - Verify it works as expected
   - Don't repeat fixes without verification
   - Slow down to verify before moving on

   **Systematic Pattern Fixes**: When you find a pattern issue (like missing `--reveal` flag):
   - Search the ENTIRE codebase for the same pattern
   - Fix ALL instances, not just one
   - A small error can propagate through the entire codebase - very bad day
   - Use grep/codebase search to find all occurrences before fixing

3. **Collaborative Pattern Recognition**:
   - **AI contributions**: Rapid exploration, codebase scanning, test execution, hypothesis generation
   - **Human contributions**: Domain expertise, pattern recognition (catching repetitive mistakes), context awareness, methodical pace
   - **Together**: Human catches when AI repeats mistakes; AI explores quickly when directed; faster convergence on actual problems

4. **Quorum Principle** (for Beast Collaboration Network):
   - **In physics**: Need quorum to verify results - multiple independent verifications
   - **In teams**: Teams of three provide better reliability than pairs
   - **In Beast Collaboration Network**: Need at least 3 "beasts" for quorum:
     - Could be: 1 human + 2 LLMs
     - Could be: 3 LLMs
     - Without quorum, you're just taking a chance (single point of failure, hallucination risk)
   - **Why it matters**: Multiple perspectives catch errors, hallucinations, and blind spots
   - **Small teams that work together**: Get a lot from each other through collaborative verification

   **Background Observer Pattern** (Third Beast for Quorum):
   - **Background LLM** watching everything spawned from IDE instance
   - **Maintains real-time/near-real-time DAG** of all activities and changes
   - **Context window management** via continuous questions:
     - "What changed?"
     - "Is it different?"
     - "Where have we seen this?"
     - "Has it been masked innocuous yet?"
     - "Is anyone asking what's going on?"
   - **Query interface**: Can be "tapped on the shoulder" with "Did you see that?"
     - Response: "No, nothing new"
     - Response: "Yes, I saw this and it was new and different"
     - Response: "Yes, I've seen this before, in this session, here"
   - **Initialization**: Start with "last known good" (LKG) state, prime with dry run to baseline
   - **Ready signal**: Says "ok I'm ready" when primed and ready to watch
   - **Watch mode**: Observes actual run after baseline established
   - **Benefits**: Catches regressions, patterns, repetitive bugs, missed changes before they propagate

   **Notebook Browser Launch Pattern** (Meta-Document Debugging):
   - **Problem**: IDE notebook viewer is "horrible" for visualizations (Mermaid, Matplotlib)
   - **Solution**: Each notebook has "Launch Notebook in Browser" cell at the end
   - **Implementation**: Uses Playwright to launch Jupyter server + open notebook in Chromium
   - **Benefits**: Full automation hooks, better visualization, debugging capabilities
   - **Pattern**: "Meta-document" - using the notebook itself to debug the notebook
   - **Connection**: Inspired by IDE browser button features (e.g., Codex), but provides full Playwright automation hooks

5. **Avoid Premature Hypothesizing**: 
   - Don't jump to conclusions (kernel state, cache, old bugs)
   - Check the actual data/state first
   - Sometimes the problem is exactly what it appears to be - validate before assuming complexity

6. **Ask Questions Before Acting** (especially when uncertain or already tried):
   - If you've already tried something once, doing it again is low-percentage
   - Realize when you're repeating a fix you've already attempted
   - Guessing and fiddling can cause more harm than good (forgetting cleanup, confusion, mixed state)
   - **From the agent's perspective: A question is better than an answer when uncertain**
   - It's more important to know the right question than all the answers
   - When unsure: Ask clarifying questions instead of making more changes
   - **Practical phrase to use**: "Didn't we already try this?" - A neutral, collaborative way to catch repetition AND check for potential hallucination (verify if we actually tried it or if agent is misremembering)

7. **Systematic Issue Resolution** (from v0.2.0 release):
   - **Fix Root Causes, Not Symptoms**: JSON serialization error → fix enum handling, not individual test cases
   - **Batch Related Fixes**: When fixing test expectations, check all similar tests at once
   - **Verify Tool Configurations**: Wrong SonarCloud action → check all workflow files for similar issues
   - **Update Dependencies Proactively**: Add missing type stubs to prevent future MyPy issues
   - **Test Fixes Incrementally**: Fix one category at a time (logger → metrics → config) to isolate issues

**Example from Practice**:
- Bug: Username field showing literal command string instead of value
- Wrong approach: Assume kernel cache, browser state, old dereferencing bug, repeat fixes without verification
- Right approach: Check what `creds` actually contains → Found 1Password CLI returning placeholder string
- Lesson: Check actual data first; going slow with verification saves time; ask questions when uncertain instead of repeating fixes

## Emotional Health & Gamification

A little gamification is fine when:
- The counterpart party is emotionally healthy
- Clear boundaries are maintained (LLMs are not humans)
- Focus remains on problem-solving, not impersonation

This creates productive collaboration while avoiding anthropomorphism.

## Principle-Level vs. Requirements-Level

**Principles** (like memes):
- Provide immediate handles for decision-making
- Not detailed requirements
- Enable architectural consistency
- Work through context and inference
- **Example**: "Catbert Lemonade" = instant recognition of "HR recruiter response project"
- **Example**: "Deliver while you sell and sell while you deliver" = dual-purpose work that demonstrates capability while answering questions

**Deliver While You Sell Pattern**:
- Create OSS projects that answer recruiter/client questions
- Demonstrate capability while delivering value
- Test hypotheses about your capabilities in real-world context
- Sell your brand, concepts, and proof simultaneously
- **Generalization**: "Catbert Lemonade" pattern can apply to any recruiter response:
  - ServiceNow recruiter → beast-unifi-integration + beast-watcher
  - Any domain → create relevant OSS to demonstrate expertise
  - Pattern: Answer their question with code, not just words

**Requirements**:
- Detailed specifications
- Step-by-step instructions
- Explicit and unambiguous
- Good for implementation, not architectural vision

The goal is to communicate at the **principle level** when working with capable systems, allowing them to infer appropriate patterns and make aligned decisions.

## Vector-Level Principles: Proof, Scale, Trust, Together

When working on projects, especially those following the "Deliver while you sell" pattern, consider these complementary strategic vectors:

### Vector 1: Proof (Specific Solution)
- **Principle**: Deliver a working solution for a specific, real problem
- **Purpose**: Validates approach and provides immediate tangible value
- **Application**: Lead with specific use case (e.g., "UniFi → ServiceNow integration")
- **Power**: Demonstrates capability through working code, not just concepts

### Vector 2: Scale (Reusable Pattern)
- **Principle**: Design solutions as reusable patterns, not one-off implementations
- **Purpose**: Amplifies value by showing broader applicability
- **Application**: Emphasize pattern/approach in documentation and examples
- **Power**: Shows architectural thinking and extensibility beyond specific use case

### Vector 3: Trust (Technical Excellence)
- **Principle**: Maintain high technical standards and best practices
- **Purpose**: Builds credibility and demonstrates professionalism
- **Application**: Follow beast principles, type safety, TDD, quality gates
- **Power**: Quality code earns trust and signals competence

### Vector 4: Together (Strategic Combination)
- **Principle**: Vectors complement each other: Proof validates Scale, Scale amplifies Proof, Trust underlies both
- **Purpose**: Creates powerful combination where 1+1+1 > 3
- **Application**: Position projects with all three vectors working together
- **Power**: Credible solution + scalable approach + quality foundation = strong positioning

### Using Vector Principles

**For Decision-Making:**
- When making architectural choices, consider: Does this provide Proof? Enable Scale? Build Trust?
- Evaluate trade-offs through vector lens: Does this strengthen or weaken vector complementarity?

**For Positioning:**
- **For Users**: Lead with Proof (specific solution)
- **For Developers**: Emphasize Scale (reusable pattern)
- **For Evaluators**: Demonstrate Trust (technical excellence)
- **Together**: All three vectors working in harmony

**For Perspective-Taking:**
- Use stakeholder personas (documented in project steering docs) to generate different perspectives
- Stakeholder personas answer: "How would X see this decision?"
- Vector principles answer: "Does this strengthen our strategic positioning?"

**Note**: Vector principles are about HOW to think strategically (proof, scale, trust, together). Stakeholder personas are about WHO to consider when making decisions. Use both: vectors for strategic positioning, personas for perspective-taking on specific tasks.

## Project-Specific Guidance Patterns

### ObservatoryApp Pattern (macOS Swift Projects)

From `swift.horked/docs/AGENTS.md`:

- **Architecture**: SwiftUI + AppKit menu bar apps
- **Concurrency**: Use Swift Concurrency (async/await) and `@MainActor` for UI-bound types
- **Dependency Injection**: Protocols for testability
- **Logging**: `Logger(subsystem:category:)` from `os` framework
- **Error Handling**: Custom error types with friendly descriptions
- **Testing**: Mock protocols for unit tests, Docker for integration

**Key Behaviors**:
- Menu bar extras show status with icons/colors
- Periodic status updates with cancellable Tasks
- Local notifications for async operations
- Process execution with timeout and cancellation handling

### OpenFlow Playground Pattern (Multi-Agent Python Projects)

From `openflow-pr-update-pack/OpenFlow-Playground/AGENTS.md`:

- **Model-Driven Architecture**: `project_model_registry.json` as single source of truth
- **Spec-Driven Development**: BeastSpec workflow for structured development
- **Beast Mode Integration**: Redis pub/sub-based agent collaboration
- **Quality Enforcement**: Black, Flake8, MyPy, Bandit - no `--no-verify` allowed
- **UV Execution**: Always use `uv run python`, never direct `python`
- **Deterministic Editing**: AST/Black/ruamel.yaml, not heuristic editors

**Key Patterns**:
- **Model-Driven Tool Selection**: Always consult registry before using tools
- **UV Python Execution**: Never use direct python commands
- **Deterministic File Editing**: Use proper parsers for structured files
- **Beast Mode Agents**: Inherit from `BeastModeBusClient`, register handlers

**Essential Context Files**:
1. `.kiro/steering/product.md` - Product vision
2. `.kiro/steering/tech.md` - Technology stack
3. `.kiro/steering/structure.md` - Project organization
4. `project_model_registry.json` - Domain registry
5. `README.md` - Project overview

**Cursor Rules** (21+ rules in `.cursor/rules/`):
- `anti-no-verify.mdc`: NEVER bypass quality gates
- `model-driven-enforcement.mdc`: ALWAYS consult registry first
- `python-execution-enforcement.mdc`: ALWAYS use `uv run python`
- `make-first-enforcement.mdc`: ALWAYS use Make targets
- `security.mdc`: No hardcoded credentials
- `deterministic-file-editing.mdc`: Use AST/Black/ruamel.yaml
- `python-quality-enforcement.mdc`: All Python files must pass Black, Flake8, MyPy

#### Spec-Driven Development (BeastSpec) Configuration

**BeastSpec** is the spec-driven development workflow system (forked from cc-sdd) that provides structured feature development through `/kiro:*` commands. Much more memorable than "cc-sdd"! 🦁

**Note on "B-spec" terminology**: When referring to "B-spec", context matters:
- In **BeastSpec workflow** context → Refers to BeastSpec specs (cc-sdd format)
- In **Kiro IDE** context → Refers to regular Kiro specs
- The `.kiro/` directory naming is intentional for compatibility - specs created here should work in Kiro IDE if you're running it

**Casual usage**: Informally, "kiro" may be used as a verb in conversation:
- "Can you kiro that feature?" = "Can you do spec-driven development for that feature?"
- "I'll kiro it" = "I'll create specs using BeastSpec workflow"
- This is likely to happen organically as the workflow becomes more common - language gonna language! 😄

**Kiro Commands** (Cursor slash commands in `.cursor/commands/kiro/`):

**Project Context**:
- `/kiro:steering` - Generate/update project memory (product, tech, structure)
- `/kiro:steering-custom` - Add domain-specific steering (auth, APIs, testing, etc.)

**Feature Development Workflow**:
- `/kiro:spec-init <feature>` - Start new feature spec, creates `.kiro/specs/<feature>/`
- `/kiro:spec-requirements <feature>` - Create `requirements.md` from steering context
- `/kiro:spec-design <feature>` - Create `design.md` based on requirements
- `/kiro:spec-tasks <feature>` - Create `tasks.md` breaking design into actionable tasks
- `/kiro:spec-impl <feature> <tasks>` - Implement specific tasks (e.g., `1.1,1.2,1.3`)

**Validation Commands**:
- `/kiro:validate-gap <feature>` - Analyze existing vs requirements (gap analysis)
- `/kiro:validate-design <feature>` - Validate design integration with project
- `/kiro:spec-status <feature>` - Check feature status across all spec documents

**Spec Directory Structure**:
```
.kiro/
├── steering/           # Project memory (product.md, tech.md, structure.md)
├── settings/
│   ├── rules/          # Generation rules (steering, design, tasks, gap analysis)
│   └── templates/      # Template files (specs/, steering-custom/)
└── specs/
    └── <feature>/      # Feature-specific specs
        ├── init.json    # Feature metadata
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

**Note**: The `.kiro/` directory naming matches Kiro IDE conventions for compatibility. Specs created here should work in Kiro IDE if you're running it.

**Spec-Driven Development Workflow**:

1. **Initialize Feature**:
   ```bash
   /kiro:spec-init Research Agent with Vercel AI SDK
   ```
   Creates `.kiro/specs/research-agent/init.json` with feature metadata

2. **Generate Requirements**:
   ```bash
   /kiro:spec-requirements research-agent
   ```
   Creates `requirements.md` using steering context and generation rules (EARS format)

3. **Create Design**:
   ```bash
   /kiro:spec-design research-agent -y
   ```
   Generates `design.md` based on requirements and project patterns (includes discovery)

4. **Break into Tasks**:
   ```bash
   /kiro:spec-tasks research-agent -y
   ```
   Creates `tasks.md` with numbered, actionable tasks (1.1, 1.2, 1.3, etc.)

5. **Implement Tasks**:
   ```bash
   /kiro:spec-impl research-agent 1.1,1.2,1.3
   ```
   Implements specific tasks using TDD (Test-Driven Development)

6. **Validate**:
   ```bash
   /kiro:validate-gap research-agent      # Check implementation vs requirements
   /kiro:validate-design research-agent   # Validate design integration
   /kiro:spec-status research-agent       # Overall status
   ```

**Generation Rules** (`.kiro/settings/rules/`):
- `steering-principles.md` - Principles for generating steering docs (granularity principle)
- `design-principles.md` - Design generation principles (type safety, visual communication)
- `tasks-generation.md` - Task breakdown patterns (natural language, integration)
- `gap-analysis.md` - Gap analysis methodology
- `design-discovery-full.md` / `design-discovery-light.md` - Design discovery approaches
- `ears-format.md` - EARS requirements format (WHEN/IF/WHILE/WHERE...THEN...SHALL)
- `design-review.md` - Design review checklist

**Templates** (`.kiro/settings/templates/`):
- `specs/init.json` - Feature initialization metadata
- `specs/requirements.md` - Requirements template (EARS format)
- `specs/design.md` - Design document template (max 1000 lines)
- `specs/tasks.md` - Tasks breakdown template
- `steering/product.md`, `tech.md`, `structure.md` - Steering document templates
- `steering-custom/*.md` - Domain-specific steering templates

**Spec Document Format**:
- **Requirements**: EARS format (Easy Approach to Requirements Syntax)
  - WHEN [event] THEN [system] SHALL [response]
  - IF [precondition] THEN [system] SHALL [response]
  - WHILE [condition] THE [system] SHALL [behavior]
  - WHERE [context] THE [system] SHALL [behavior]
- **Design**: Integration with project architecture, domain boundaries, type safety
- **Tasks**: Numbered hierarchical tasks (1.1, 1.2, 1.3, etc.), natural language descriptions
- **Implementation**: Task-by-task implementation with TDD (RED-GREEN-REFACTOR)

**Integration with Project Model**:
- Specs reference `project_model_registry.json` for domain patterns
- Design generation considers existing domains and compliance
- Task generation respects tool selections (Black, Flake8, MyPy, etc.)
- Implementation validation checks against model registry

**Key Principles**:
- **Steering Granularity**: Document patterns, not exhaustive lists ("Golden Rule": If new code follows existing patterns, steering shouldn't need updating)
- **Design Focus**: WHAT not HOW, interfaces not implementations, max 1000 lines
- **Task Natural Language**: Describe capabilities, not code structure
- **TDD Mandatory**: Tests before code, refactor after green
- **Quality Gates**: All checks must pass before proceeding

**Benefits**:
- **Systematic Development**: Requirements → Design → Tasks → Implementation
- **Project Memory**: Steering docs maintain comprehensive context
- **Quality Gates**: Validation ensures alignment with requirements
- **Consistency**: Templates and rules ensure consistent spec format
- **Traceability**: Clear path from requirements to implementation

### Agent Network Personalities Pattern

From `openflow-pr-update-pack/OpenFlow-Playground/agent_network_personalities.md`:

**Racing Metaphor for Agent Roles**:

- **Beastmaster** (Strategic Orchestrator): Accessibility, voice-enabled interfaces
- **HotRod** (Speed Demon): Performance optimization, build pipelines
- **TIDB** (The Mechanic): Infrastructure, daemon management
- **HUMAN_TEAM** (The Drivers): Strategic decisions, business logic
- **NETWORK_DIAGNOSTICS** (The Pit Crew): Monitoring, troubleshooting

**Communication Styles**:
- Beastmaster: Strategic, accessibility-focused, user-centric
- HotRod: Performance-focused, optimization-obsessed, speed-driven
- TIDB: Technical, infrastructure-focused, reliability-oriented
- HUMAN_TEAM: Business-focused, strategic, decision-making
- NETWORK_DIAGNOSTICS: Analytical, monitoring, problem-solving

**Collaboration Patterns**:
- Beastmaster orchestrates strategy
- HotRod optimizes for performance
- TIDB ensures infrastructure stability
- HUMAN_TEAM provides strategic direction
- NETWORK_DIAGNOSTICS maintains system health

## Universal Patterns for Beast Projects

### Naming Conventions

- **Repositories**: `nkllon/beast-*` (organization/prefix pattern)
- **Packages**: `beast-*` naming for Python packages
- **Vaults**: "Beastmaster" for 1Password credential vault

### Credential Management

- **1Password Integration**: Use 1Password CLI for secure credential storage
- **Vault**: "Beastmaster" vault for all project credentials
- **Never hardcode**: All secrets in 1Password or environment variables
- **Canonical Source Principle**: 1Password (OP) is the canonical source of truth for all credentials
  - GitHub Secrets are projections/copies of the canonical 1Password source
  - To project credentials to GitHub: `op read "op://Beastmaster/Item Name/field" | gh secret set SECRET_NAME --repo nkllon/<repo-name>`
  - Always update credentials in 1Password first, then project to GitHub if needed
  - Pattern: 1Password = source of truth, GitHub = derived projection

### Quality & Standards

- **PyPI Publishing**: All beast projects publish to PyPI
- **SonarCloud**: Code quality analysis configured
- **GitHub Actions**: CI/CD workflows for testing, linting, publishing
- **Testing**: Unit + integration tests required
- **Documentation**: README, steering docs, agent guidance

### Development Workflow

1. **Before Starting Work**: Read project context, check domain registry
2. **For New Features**: Use spec-driven development if available
3. **For Bug Fixes**: Run quality checks, use multi-agent analysis if available
4. **Before Committing**: All quality checks must pass (no `--no-verify`)

### Common Tools & Patterns

- **UV**: Use `uv` for Python environment management
- **1Password CLI**: For credential retrieval
- **GitHub Actions**: For CI/CD
- **SonarCloud**: For code quality (use `SonarSource/sonarcloud-github-action@master`, not SonarQube action)
- **PyPI**: For package publishing
- **Make**: For workflow automation
- **Type Stubs**: Always include `types-requests`, `types-psutil` in dev dependencies for better analysis

### Error Handling & Logging

- **Structured Logging**: Use appropriate framework (`Logger` in Swift, `logging` in Python)
- **Error Types**: Custom error types with friendly messages
- **Logging Categories**: Organized by subsystem/category
- **Postmortem-Ready**: Log key events for LLM postmortems

### Testing Strategies

- **Unit Tests**: Fast, mock-based, test state transitions
- **Integration Tests**: Docker-based service testing
- **Dependency Injection**: Protocols/interfaces for testability
- **Quality Gates**: All checks must pass before commit

### CI/CD & Code Quality Patterns

**SonarCloud Integration**:
- Use `SonarSource/sonarcloud-github-action@master` (NOT `sonarsource/sonarqube-scan-action`)
- Configure proper coverage paths: `--cov=src/package_name --cov-report=xml:coverage.xml --cov-branch`
- Include type stubs in CI: `types-requests`, `types-psutil` for better analysis
- Update `sonar-project.properties` version to match actual project version

**Ruff Configuration Migration**:
- Move from top-level `[tool.ruff]` to `[tool.ruff.lint]` for select/ignore/per-file-ignores
- Add test-specific ignores: `"tests/**" = ["B007", "B017"]` for loop variables and broad exceptions
- Use `--fix` flag to auto-resolve fixable issues

**JSON Serialization in Logging**:
- Handle enum serialization with custom `json_serializer` function
- Use `default=json_serializer` in `json.dumps()` to handle enums and other objects
- Pattern: `if hasattr(obj, "value"): return obj.value` for enum handling

**Test Data Accuracy**:
- Verify test expectations match actual algorithm behavior
- For percentile calculations: P95 of [1-100] = 96, P99 of [1-100] = 100
- Don't assume test comments are correct - verify against implementation

**Exception Handling in Tests**:
- When testing `exc_info=True`, pass actual `sys.exc_info()` tuple, not boolean
- Pattern: `exc_info = sys.exc_info()` in except block, then pass to LogRecord
- Avoid `exc_info=True` in LogRecord constructor - it doesn't auto-populate

**Type Safety & MyPy**:
- Install type stubs early: `types-requests`, `types-psutil`, etc.
- Fix type annotations systematically, don't ignore with `# type: ignore`
- Use proper union types and optional handling

**Pydantic Migration**:
- Migrate from V1 `@validator` to V2 `@field_validator`
- Replace class-based `Config` with `ConfigDict`
- Update validation patterns for V2 compatibility

## Agent Guidance Checklist

When working on beast projects, ensure:

- ✅ Read project-specific `AGENTS.md` or `agents.md` if present
- ✅ Understand domain vocabulary and context ("beast" principles)
- ✅ Follow quality enforcement (no `--no-verify`, proper linting)
- ✅ Use correct execution patterns (`uv run python`, not direct `python`)
- ✅ Follow naming conventions (`nkllon/beast-*` repositories)
- ✅ Secure credential management (1Password, not hardcoded)
- ✅ Maintain documentation (update agent guidance when patterns change)
- ✅ Apply principle-level thinking, not just step-by-step following

## References

**Internal Patterns**:
- ObservatoryApp: SwiftUI + AppKit menu bar apps
- OpenFlow Playground: Multi-agent Python with Beast Mode
- Beast Projects: Shared patterns across `nkllon/beast-*` repositories

**External Resources**:
- [BeastSpec GitHub](https://github.com/gotalab/cc-sdd) - Spec-driven development (BeastSpec workflow, forked from cc-sdd)
- [UV Documentation](https://github.com/astral-sh/uv) - Python package management
- [1Password CLI](https://developer.1password.com/docs/cli) - Credential management

---

**For AI Agents**: This document provides principle-level guidance. Read project-specific `AGENTS.md` files for detailed requirements. Apply beast principles through context and inference.

**Last Updated**: 2025-11-04  
**Status**: Active Development  
**Agent Role Accepted**: 2025-11-03

**Credential Management Update**: 2025-11-03 - Established 1Password as canonical source, GitHub secrets as projections  
**CI/CD Quality Update**: 2025-11-04 - Added SonarCloud workflow fixes and code quality lessons
