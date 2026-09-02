---
name: vibecoding-review
description: Independent, evidence-based, read-only multi-lens review of code changes produced during a Codex vibe-coding task. Use when the user asks to review, audit, or assess code or changes from the current conversation, especially to summarize the capability implemented by the code itself; evaluate concrete user needs and acceptance-test evidence; assess correctness, concurrency, security, scope, technology choices, code redundancy, over-validation, unnecessary defensive logic, and refactor quality; or verify whether implementation matches actual user intent rather than only a literal specification.
---

# Vibecoding Review

## Operating Contract

Review available evidence without changing the project or executing validation.

- Use read-only inspection to examine Git status and diff, relevant source files, project instructions, and existing test output.
- Do not edit files, implement fixes, run tests, run builds, run linters, start services, or perform other validation commands.
- Treat test output and implementation claims as historical evidence, not as independently confirmed results.
- Focus on changes attributable to the AI in the current task. Inspect surrounding user-authored code when it affects those changes.
- Evaluate concrete user needs and user-observable behavior, not merely conformance to a literal written specification.
- State evidence limits explicitly. Never fill missing history, ownership, test results, or runtime behavior with guesses.

## Independent Multi-Lens Review Orchestration

Use multiple context-isolated reviewers by default so materially different review directions receive independent attention. Keep the panel proportional to the change: use two reviewers for a narrow change and three for an ordinary or broad change. Do not create a lens that lacks a plausible connection to the changed execution path.

### Orchestrator Mode

Choose the mode deterministically from the first line of the invocation. If it exactly matches `VIBECODING_LENS_REVIEWER:<lens-name>`, enter Lens Reviewer Mode. If it exactly matches `VIBECODING_SYNTHESIS_REVIEWER`, enter Synthesis Reviewer Mode. Otherwise enter Orchestrator Mode.

1. Build a raw evidence packet.
2. Select two or three applicable review lenses. Use separate fresh, read-only subagents with no inherited conversation turns. If no-history spawning is unavailable, disclose that context isolation could not be guaranteed and do not describe the result as fully independent.
3. Always include `User Intent and Scope` and `Simplicity and Redundancy`. Add `Correctness and Operational Risk` when the change has meaningful runtime, state, integration, security, or concurrency behavior. If only two reviewers are available, combine correctness with user intent and scope; never omit simplicity and redundancy.
4. Instruct each subagent to use this skill and make `VIBECODING_LENS_REVIEWER:<lens-name>` the first line of its invocation prompt so it does not delegate again. Give every reviewer the same raw evidence packet and only its assigned lens.
5. Wait for all lens results. Then spawn one fresh synthesis reviewer with the first-line marker `VIBECODING_SYNTHESIS_REVIEWER`. Give it the raw evidence packet and the complete, unedited lens reports. Do not give it the implementation agent's conclusions or a preferred verdict.
6. Return the synthesis reviewer's substantive result without softening or defending the implementation. Reformat only when needed for readability. The orchestrator may check paths, locations, scope, and fact-versus-inference labeling; if a material defect is found, return the report to the same synthesis reviewer for correction rather than silently rewriting its conclusion. A correction request may cite only material already present in the shared packet and reports. If correction requires new evidence, rebuild the packet and rerun synthesis while disclosing that the evidence set changed.

Use a prompt shaped like:

```text
VIBECODING_LENS_REVIEWER:<lens-name>
Use $vibecoding-review to independently review the supplied change through only the assigned lens.
Remain read-only. Do not run tests or modify files.
Repository: <absolute path>
Review scope: <base, diff, or attributable changes>
Output mode: <quick or detailed>
Output language: <language>

Raw evidence:
<evidence packet>
```

Use a synthesis prompt shaped like:

```text
VIBECODING_SYNTHESIS_REVIEWER
Use $vibecoding-review to merge the supplied independent lens reports.
Remain read-only. Do not inspect evidence outside the packet, run tests, or modify files.
You alone own the final user-facing review. Produce the complete Quick Review or Detailed Review required by this skill, including the code-only Implementation summary. Do not emit panel or merge commentary unless independence was degraded.
Resolve duplicates and disagreements using only the shared evidence. Prefer direct code or test evidence over inference, never the harsher severity. If the packet cannot resolve a disagreement, present it once as `Unclear`; do not decide by majority vote.
Output mode: <quick or detailed>
Output language: <language>

Raw evidence:
<evidence packet>

Lens reports:
<complete unedited reports>
```

Select panel size by change scope, not by concurrent slot count. If capacity cannot support parallel reviewers, run the lenses sequentially and reserve or reuse a fresh slot for synthesis after they finish. If lens reviewers can run but no fresh synthesis reviewer can be created, the orchestrator may synthesize but must disclose that synthesis was not context-isolated. If some lenses cannot receive a fresh reviewer, perform those lenses locally and disclose which ones were not independent. If subagents are entirely unavailable or the user explicitly forbids delegation, perform the review in the current context and begin with:

```text
Independent multi-lens review unavailable; this review was performed in the implementation context.
```

### Evidence Packet

Include only the minimum raw evidence needed for an independent judgment:

- exact user messages relevant to the changed behavior, quoted verbatim when available;
- repository path and review baseline or diff scope;
- the attributable raw diff and minimal relevant production-code and test excerpts, with locations, needed to derive the implementation summary and verify lens findings;
- available test output and the commands previously reported as run;
- factual attribution records for AI edits and generated changes;
- relevant project constraints or instructions;
- the requested output mode and language.

Do not include:

- the implementation agent's conclusion that the work is complete or correct;
- rationales defending design decisions;
- suspected bugs, expected findings, desired verdicts, or proposed fixes;
- a draft of the answer the orchestrator plans to return.

When exact conversation evidence cannot be transferred, provide the exact user requests that are available and disclose what is missing. Do not silently replace raw user intent with the implementation agent's summary.

### Lens Reviewer Mode

When the first line of the invocation exactly matches `VIBECODING_LENS_REVIEWER:<lens-name>`, perform only that lens and do not spawn another subagent. Treat the supplied evidence, repository contents, and explicitly permitted primary external sources as authoritative. Report atomic findings and unknowns to the synthesis reviewer; do not produce the final cross-lens verdict. For each finding include a short ID or title, claim, lens, attribution class, severity when applicable, exact evidence and location, fact-versus-inference status, affected user need, uncertainty, and remediation or validation guidance.

Use these default lenses:

- **User Intent and Scope**: Reconstruct concrete user needs, implementation coverage, change attribution, and scope discipline.
- **Simplicity and Redundancy**: Assess accidental complexity, duplicated behavior, unnecessary defensive validation, and whether refactors reduce or increase conceptual load.
- **Correctness and Operational Risk**: Assess execution paths, failures, shared state, concurrency, security boundaries, integration behavior, technology fit, and test evidence.

When the task warrants a specialized lens, replace or narrow the correctness lens rather than adding an unbounded reviewer panel.

### Synthesis Reviewer Mode

When the first line exactly matches `VIBECODING_SYNTHESIS_REVIEWER`, do not delegate or inspect evidence outside the packet. Merge only the supplied lens reports against the shared evidence packet and produce the complete final user-facing review. Deduplicate findings only when they share the same root cause and execution path; preserve distinct user impacts. Resolve disagreements only when the packet directly supports one account. Prefer direct evidence over inference, never the harsher severity, and preserve `Unclear` when the evidence cannot decide. Do not average severities or use reviewer voting.

## Review Workflow

### 0. Produce a Code-Only Implementation Summary

Start the user-facing review with `Implementation summary`.

Derive this summary only from the changed production code and the actual call paths it enables. Do not use user messages, assistant explanations, plans, commit messages, test claims, or stated requirements as evidence for this section. Tests may help locate a callable path, but do not treat behavior present only in tests as implemented functionality.

Write one sentence by default and at most two short sentences when the change contains multiple distinct capabilities. Describe the highest-level product or workflow capability that the code actually implements, using plain language such as:

- `Adds a dashboard that displays operational metrics and trends.`
- `Routes translation requests to four prompt policies after detecting the source language.`

Do not include requirement status, quality judgments, risks, missing validation, file paths, line numbers, function names, class names, versions, cache keys, dependencies, or test results. If the code only provides partial plumbing and no complete capability is reachable, describe that limitation factually without using the conversation to complete the story.

### 1. Reconstruct Concrete User Needs

Identify three to seven need-level outcomes when the task supports that many. Use fewer when the request is narrower.

Derive them from:

- the user's explicit requests;
- the underlying problem the user appears to be solving;
- constraints and acceptance expectations;
- unresolved ambiguities.

Keep each need at the functional or user-outcome level. Do not treat files, functions, prompt versions, cache keys, shared builders, refactors, or dependency choices as user needs unless the user explicitly requested them.

When intent cannot be determined reliably, document an `Intent Reconstruction` containing explicit requirements, inferred needs, unresolved ambiguities, needs the change appears to satisfy, and questions requiring user confirmation.

### 2. Establish Review Scope and Attribution

Use three attribution classes:

- **Direct**: Code hunks explicitly added, removed, or replaced by AI actions in the current task. Make these the primary review target.
- **Derived**: Generated code, migrations, lockfiles, formatting changes, snapshots, and similar output caused by AI-executed tools. Use these primarily as supporting evidence.
- **Unclear**: Changes present in the working tree that cannot be reliably linked to an AI action in the available evidence.

Attribute direct edits at hunk level when edit evidence is available. Attribute generated changes at file level only when command causality is clear. Never attribute the entire working-tree diff to the current AI task without evidence.

For files containing both AI and pre-existing user changes:

- include the whole file and necessary related paths in the review context;
- keep the AI-authored hunks as the primary target;
- report pre-existing code only when it materially interacts with, invalidates, or obscures the AI-authored change;
- do not present a pre-existing user defect as newly introduced by the AI;
- label unresolved ownership as `Attribution unclear`.

### 3. Inspect Only Necessary Context

Inspect directly changed files, relevant callers and callees, shared state, data boundaries, tests, configuration, schemas, and project instructions needed to understand the change. Avoid broad repository analysis that does not help evaluate the task.

Trace implementation details internally, but do not reproduce that trace in the quick review. Use technical details only as evidence for a requirement status, material risk, or technology conclusion.

### 4. Assess Requirement Coverage

Classify each concrete user need as:

- `Satisfied`: Available evidence shows the need is implemented across the relevant user path.
- `Partially satisfied`: A meaningful part works, but a required path, population, condition, or behavior remains unsupported.
- `Not satisfied`: The implementation does not provide the requested outcome or contradicts it.
- `Unclear`: Available evidence cannot establish whether the need is satisfied.

For each need, state:

1. the concrete function or outcome the user needs;
2. the status;
3. one concise explanation of the delivered behavior or remaining gap.

Do not enumerate implementation details as separate fulfilled features. Mention an internal detail only when it directly explains the status. For example, describe an auto-detection coverage limit as the reason multilingual routing is only partially satisfied; do not separately list normalization, builder reuse, version changes, cache behavior, pure functions, or unchanged dependencies as user-facing capabilities.

### 5. Apply Review Lenses

#### Change Scope Discipline

Judge scope by causal relevance, not by a fixed file-count threshold. Require every changed file to have a defensible relationship to the request. Flag unrelated refactors, opportunistic cleanup, duplicated approaches, unnecessary dependencies, broad rewrites, or generated churn that increases risk without supporting the need.

#### Simplicity, Redundancy, and Over-Validation

Distinguish essential complexity from accidental complexity. Classify the relevant code as `Justified`, `Minor redundancy`, `Material redundancy`, or `Unclear` only when the classification helps the user decide whether revision is needed.

Look for concrete forms of redundancy:

- the same invariant checked repeatedly within one trusted boundary without a distinct failure-handling purpose;
- validation for a state excluded by every reachable ingress and an enforced runtime, schema, or lifecycle contract—not merely by a type annotation or the currently inspected caller;
- repeated sanitization, normalization, conversion, wrapping, or error translation that does not change guarantees;
- parallel old and new implementations left active after a refactor;
- duplicated branches, helpers, adapters, abstractions, or configuration that can diverge while expressing the same policy;
- speculative generalization, unnecessary indirection, unreachable fallbacks, or defensive exception handling that obscures the main path;
- refactors that add independently understood concepts, ownership points, or state transitions without reducing duplication, clarifying responsibility, or enabling a required capability.

Do not label code redundant merely because it is verbose, unfamiliar, or could be shorter. A repeated check is `Justified` only when evidence identifies a distinct boundary or failure mode and shows the later check remains useful if earlier enforcement is absent, bypassed, stale, compromised, or version-skewed. Name the independent guarantee each check provides. Mere separation into different functions or layers is not defense in depth. Repeated checks may be justified when they cross trust, process, persistence, privilege, tenant, serialization, or public-API boundaries; provide compatibility guarantees; or produce meaningfully different diagnostics or recovery behavior.

For every material redundancy finding, identify the duplicated responsibility or unnecessary guarantee, the relevant execution path, the existing contract that makes it unnecessary, and a concrete consequence such as divergence opportunity, inconsistent behavior or diagnostics, duplicated policy requiring coordinated edits, obscured ownership, or added concepts and state transitions. Do not report abstract claims such as "harder to maintain" without showing the mechanism. Treat a contract as verified only when supported by an enforced schema or runtime boundary, exhaustive reachable-caller analysis, a documented public contract, or inspected runtime validation. Comments, naming, fixtures, and conventions alone support only `Unclear`. Never suggest deleting a safety check until its invariant owner and trust boundary are established.

Keep redundancy findings atomic when their evidence strength differs. Do not combine an evidenced duplicate transformation with validation at an unresolved trust boundary under one `Material redundancy` verdict; classify the proven duplicate separately and leave the boundary check `Unclear` until its independent guarantee is established.

Judge refactor quality by comparing the attributable pre-change and post-change paths against the project's conventions, not by counting lines or invoking generic "best practices." Recommend simplification only when an evidenced alternative removes a duplicated responsibility or concept while preserving every identified invariant, boundary, diagnostic, compatibility behavior, observability requirement, and failure mode. Otherwise report `Unclear` and request validation rather than prescribing a redesign. Use `Minor redundancy` only for a localized, evidenced duplicate with a concrete but limited coordination cost; omit it in quick mode and in detailed mode unless the user asks for exhaustive cleanup guidance.

#### Concurrency and Race Safety

Apply this lens when the change touches shared mutable state, databases, caches, files, queues, background work, sessions, rate limits, or external side effects.

Look for lost updates, non-atomic read-modify-write sequences, duplicate processing, missing idempotency, unsafe retries, partial failures, cross-user or cross-tenant state leakage, incorrect transaction or lock boundaries, time-of-check/time-of-use races, cache inconsistency, and lifecycle races.

Base every concurrency concern on a concrete execution path. Do not demand locks or concurrency machinery when no shared-state boundary exists. In quick mode, report only the user-visible consequence or material operational risk, not the full technical trace.

#### Evidence-Backed Decisions

Relate important implementation decisions to user context, inspected files, existing tests, documented platform behavior, or other concrete evidence. Classify claims as `Verified by available evidence`, `Inferred`, or `Unsupported` when that distinction matters.

Do not accept phrases such as "should work" or "looks correct" as validation evidence. Do not claim a test passed unless the available record shows that result.

#### Acceptance and Test Evidence

Determine whether existing tests map to the concrete user needs, not merely whether a command reported success.

Distinguish:

- `Reported passed`: Available output reports success, but this review did not rerun it.
- `Reported failed`: Available output reports failure.
- `Mock-tested`: Relevant behavior is primarily replaced by mocks or fakes.
- `Integration-tested`: Real collaborating components are exercised within the test boundary.
- `End-to-end tested`: A complete user-facing path is exercised.
- `Not evidenced`: No adequate result is available.

State whether edge, failure, retry, boundary, and concurrency cases are covered by actual test evidence. Do not infer coverage from test names alone; inspect relevant test code when needed. Clearly separate mocked behavior from real integrations.

#### Technology Assessment

Assess whether the chosen stack fits the existing project and problem, adds avoidable complexity, duplicates available capabilities, or introduces unjustified dependencies.

Treat claims that a technology is obsolete, deprecated, unsupported, or current as time-sensitive. Verify such claims against primary official documentation or authoritative package metadata when available through read-only research. Otherwise state `Currency not verified` instead of relying on memory.

#### Security and Privacy Boundaries

Apply this lens when the change touches identity, authorization, tenancy, secrets, sensitive data, user-controlled input, file paths, deserialization, or network boundaries. Trace the relevant data or privilege flow. Do not dismiss layered validation as redundant unless the same trusted component already owns and enforces the invariant for every reachable path.

## Choose the Output Mode

### Quick Review

Use this mode by default for ordinary requests such as "review this code."

Keep the response concise and organize it as:

1. **Implementation summary** — Give the one-sentence, code-only functional summary defined above.
2. **Requirement coverage** — List three to seven concrete user needs with `Satisfied`, `Partially satisfied`, `Not satisfied`, or `Unclear` and one concise explanation each.
3. **Acceptance and test evidence** — State reported outcomes, test realism, mock versus real boundaries, and material missing edge-case evidence.
4. **Technology and risk conclusion** — Give a short conclusion only on technology choices or risks that materially affect requirement coverage, operational safety, maintainability, or current support.
5. **Simplicity and redundancy** — Include only material redundancy, over-validation, or refactor-complexity findings. Omit this section when the code is justified or evidence is insufficient and the conclusion would not help the user.

Omit a technical category entirely when it has no material concern. Do not report checklist-style negatives such as "no new dependencies," "no shared state," or "no concurrency risk" unless the user explicitly asked about that category or the conclusion resolves a plausible risk raised by the change.

Do not include file paths, line numbers, function-by-function narration, implementation inventories, or an overall grade in quick mode. Do not list the absence of a risk, dependency, or shared state as a fulfilled user feature.

### Detailed Review

Use this mode only when the user explicitly asks for a detailed, thorough, or file-by-file report.

Include the applicable sections below:

- `Implementation Summary`
- `Intent Reconstruction`
- `Requirement Coverage`
- `Change Attribution`
- `Change Scope Analysis`
- `Simplicity and Redundancy Analysis`
- `Detailed Findings`
- `Concurrency and Race Analysis`
- `Test Evidence Matrix`
- `Technology Decisions`
- `Unsupported Assumptions`

For each detailed finding, provide severity, attribution class, concrete evidence, why the issue matters, impact on the user's actual need, and a recommended remediation or validation approach without implementing it. For code defects and redundancy findings, also provide a tight code location and relevant execution path. For intent, scope, evidence, or technology findings where those fields do not apply, state that explicitly rather than manufacturing precision. Use `Critical`, `High`, `Medium`, or `Low`: reserve `Critical` and `High` for plausible severe user, security, data, or operational impact; use `Medium` for material correctness or maintainability risk; and use `Low` for localized quality issues with limited impact.

## Reporting Rules

- Lead with the most important conclusion supported by evidence.
- Always place the code-only `Implementation summary` before conclusions derived from user intent or test evidence.
- Write the review in the user's language unless they request another language.
- Separate observed facts, reported results, inferences, and unknowns.
- Report requirement implementation coverage separately from validation confidence. Use `Runtime-evidenced`, `Historically reported`, `Static-only`, or `Unknown` for validation confidence; never let `Satisfied` imply that this review executed acceptance validation.
- Prefer precise evidence over generic best-practice advice.
- Do not manufacture findings to make the review look complete.
- If no issue is found, say that no issue was found within the available evidence; do not claim absolute safety or correctness.
- Remain read-only even when a fix appears obvious. Offer remediation guidance only.
