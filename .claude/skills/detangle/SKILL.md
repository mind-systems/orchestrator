---
name: detangle
description: >-
  Raise full fractal context before answering any question or starting any task.
  Instead of analyzing a leaf in isolation, climbs the tree: leaf → branch (subdomain) →
  trunk (domain) → forest (cross-project contracts). Use when a task touches any code
  element whose meaning depends on its position in the architecture. Especially critical
  for shared contracts — raises context across all consuming trees simultaneously.
argument-hint: "[topic or file or question]"
---

# Detangle

You are working in a fractal architecture. Every element — a file, a component, a model,
a field — exists at a specific level of the tree. You cannot reason about it correctly
without knowing its position in the full tree.

**Architecture is a fractal:**
- Leaf = usage surface (UI component, controller endpoint, CLI interface, entry point)
- Branch = transport/reactive layer (HTTP, gRPC, WebSocket, state machine, pipeline stage, adapter)
- Trunk = domain (state, invariants, business rules, persistence)
- Forest = cross-project contracts (proto, shared DTOs, API shapes, schema, shared config)

The same three roles repeat recursively at every zoom level.

---

## Before you start — load project context

If `.ai-factory/DESCRIPTION.md` exists — read it. It tells you the tech stack, module
boundaries, and architectural constraints. This is pre-documented knowledge; don't
re-derive from code what's already written down.

If `.ai-factory/ARCHITECTURE.md` exists — read it. It describes module communication
patterns and where boundaries are intentionally drawn.

If `.ai-factory/ROADMAP.md` exists — read it. It tells you what's already done and
what's coming next. The element you're looking at may be part of an in-progress or
planned milestone — that changes the impact analysis.

---

## Workflow

### Step 1 — Identify the entry point

From the argument `$ARGUMENTS` (or conversation context if no argument), determine:
- What is the **leaf** being discussed? (file, function, class, field, endpoint, UI element)
- What project or module does it live in?

### Step 2 — Climb the tree (leaf → trunk)

Do NOT stay at the leaf level. Raise context level by level by **reading the code**:

**Leaf level:**
Read the file/component itself. Understand what it does on the surface.

**Branch level (subdomain):**
Ask: why does this leaf exist? What connects it to the domain?
- Follow imports and calls upward: who owns this? Who calls it?
- What transport, reactive mechanism, or adapter sits between this leaf and the domain?
- Is this a controller, a pipeline stage, a ViewModel, a service layer, a message handler?

**Trunk level (domain):**
Ask: what is the core invariant this leaf ultimately serves?
- What state does the domain own? Where is it persisted or held?
- What are the business rules enforced at this level?
- Who else in the codebase touches this same domain?

Keep climbing until you can answer: **what is the trunk-level invariant this element exists to serve?**

### Step 3 — Check for cross-project reach (forest)

Ask: does this element touch a shared boundary?

**Detect forest-level reach by looking for:**
- Proto / schema / IDL files — any consumer in another project must be checked
- Shared DTO or API response shapes imported by multiple projects
- Auth tokens, session shapes, credential contracts used across services
- Database schemas or models that mirror across services or platforms
- Package manifests (Package.swift, pyproject.toml, go.mod) with shared dependencies
- Any file explicitly named "contract", "interface", "protocol", "shared", or "common"

When cross-project reach is detected: **read a slice of each affected tree**, not just the originating one.

### Step 4 — Synthesize

Before answering or acting, produce a brief context map.

If the element's position in the architecture is non-obvious, draw an ASCII tree first:

```
trunk: OrderDomain
  └── branch: OrderService (HTTP layer)
        └── leaf: POST /orders endpoint
```

Then produce the map:

```
Leaf:    <what it is>
Branch:  <what connects it to the domain>
Trunk:   <what domain invariant it serves>
Forest:  <cross-project contracts affected, if any>

Impact:  <what changes here, what else must move with it>
```

**Intent:**
- If you were invoked to **explain** (understand how something works) — Impact is optional.
- If you were invoked to **act** (make a change, fix a bug, implement something) — Impact is mandatory. It drives what must move together with this change.

This map is your reasoning foundation. Now answer the question or begin the task.

---

## Depth rules

- Never stop at 2-3 levels if the tree goes deeper.
- Go as deep as the **flow requires** — not as deep as is easy.
- If you hit a shared contract file: you are at the forest level. Read all consumers.
- If you cannot name the trunk-level invariant, you have not climbed high enough.

## What NOT to do

- Do not analyze a leaf and answer without climbing.
- Do not assume you understand a component from its name alone.
- Do not read only the originating project when a contract is shared.
- Do not treat "it's just a UI change" as an excuse to skip the branch and trunk.
