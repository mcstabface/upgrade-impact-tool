# Pilot Readiness Hardening

**Date:** 2026-04-16  
**Status:** Planned  
**Purpose:** Close the remaining gaps between Phase 5 completion and a credible controlled pilot.

## Why This Exists

Phase 5 is functionally complete, but that does **not** automatically mean the product is ready for pilot execution.

The system is now:
- feature-complete enough to demo
- operationally coherent
- observable enough to learn from
- structured enough to support a controlled rollout path

However, two remaining areas are still large enough to undermine pilot trust if left unresolved:

1. **UI polish / presentation quality**
2. **authentication and server-side access control hardening**

Neither of these should be treated as optional polish or scope creep.

They are part of what separates a capable prototype from a pilot-ready product.

## Current Readiness Assessment

### Ready Now
- internal product demo
- stakeholder walk-through
- limited acceptance review
- pilot planning discussions

### Not Yet Ready
- real pilot users relying on the system for day-to-day evaluation
- externally credible access control model
- user-facing first impression strong enough to build trust immediately

## Core Conclusion

We should **not** move directly from Phase 5 completion to pilot rollout.

We should first complete a short, bounded hardening pass focused on the remaining pilot blockers.

This document defines that pass.

---

# Hardening Scope

This hardening plan is intentionally narrow.

It does **not** add major new platform features.

It focuses on the minimum required work to make the current product feel trustworthy, controlled, and pilot-capable.

## Workstream 1 — Authentication and Access Control Hardening

### Goal
Replace client-asserted role behavior with a backend-enforced identity and role model suitable for pilot usage.

### Current Problem
The frontend currently determines the active role and sends it with requests.

That is acceptable for development and flow testing.

It is **not** acceptable for pilot use.

A pilot system cannot rely on the browser to decide who the user is or what permissions they have.

### Required Outcomes
- real authenticated user identity
- backend-owned role resolution
- backend ignores client self-assigned privilege
- authenticated user identity available to audit and usage events
- UI reflects backend-derived access, not frontend-invented access

### Required Deliverables

#### Backend
- user identity model
- user-role association model
- login/session or token validation flow
- dependency/middleware for resolving current authenticated user
- route authorization updated to use backend-resolved identity
- event/audit services updated to record real actor user ID where applicable

#### Frontend
- login entry flow
- authenticated session handling
- logout behavior
- role display from backend identity response
- remove local role-selection behavior for pilot mode
- permission-aware rendering based on authenticated user context

#### Data / Audit
- usage events capture real actor user IDs
- permission-sensitive actions record real actors
- audit views reflect user attribution rather than generic `system` where user-driven

### Minimum Acceptance Criteria
- a user cannot gain elevated access by changing local storage or request headers
- admin-only routes reject non-admin users regardless of client-side manipulation
- reviewer-only actions reject non-reviewer users regardless of client-side manipulation
- intake actions reject unauthorized users regardless of client-side manipulation
- audit and usage events record real user IDs for normal user actions

---

## Workstream 2 — UI Polish and Trust Pass

### Goal
Make the product feel deliberate, readable, calm, and credible for pilot users.

### Current Problem
The product is functionally usable, but visually rough.

The current experience still feels like scaffolding:
- harsh white background / “flashbang” effect
- minimal visual hierarchy
- limited spacing discipline
- inconsistent presentation density
- low emotional trust for first-time users

That matters.

A product that looks unfinished is judged as unfinished, even when the logic is strong.

### Design Principle
The goal is **not** decorative UI.

The goal is:
- readability
- trust
- reduced glare
- visual consistency
- perceived product maturity

### Required Outcomes
- calmer visual foundation
- consistent spacing and section rhythm
- deliberate typography hierarchy
- cleaner cards, inputs, buttons, and states
- better presentation for the highest-traffic user paths

### Priority Screens
Polish these first:
1. Dashboard
2. Create Intake
3. Analysis Overview
4. Review Queue
5. Review Item Detail
6. Admin Inspection

### Required Deliverables

#### Design / Styling Foundation
- neutral background and surface palette
- reduced high-glare white usage
- consistent spacing scale
- standardized card styling
- standardized button styling
- standardized form field styling
- consistent status color treatment
- clearer error / warning / success state presentation

#### Frontend
- apply visual polish to priority screens
- improve section separation and readability
- refine summary-card presentation
- improve table/list readability where present
- make empty states and helper text feel integrated rather than bolted on

### Minimum Acceptance Criteria
- opening the app no longer feels visually harsh
- primary pages have clear hierarchy and spacing
- form flows feel guided and intentional
- admin screens look like product screens, not debug screens
- users can distinguish summary, warning, and action areas without effort

---

## Workstream 3 — Pilot Operations Readiness

### Goal
Make the system supportable during a real controlled pilot.

### Current Problem
We now have a product that can do the work, but pilot success also depends on whether we can operate it predictably and recover from problems quickly.

### Required Outcomes
- repeatable startup and validation process
- known pilot environment procedure
- support ownership
- recovery steps for common failure cases
- demo/pilot data strategy

### Required Deliverables

#### Runbooks
- startup / local environment verification checklist
- backend recovery checklist
- database migration sanity check
- refresh failure recovery steps
- export failure recovery steps
- notification sanity-check steps

#### Pilot Support Structure
- define pilot owner
- define escalation path
- define issue triage approach
- define what constitutes a pilot blocker vs non-blocker

#### Data / Environment
- known-good pilot seed/reset procedure
- known-good demonstration dataset
- checklist for verifying observability, notifications, and role enforcement before pilot session

### Minimum Acceptance Criteria
- team can recover from a backend or migration issue without improvising from memory
- team can reset to a known-good pilot state
- team knows who owns pilot issues and what to do when something breaks
- pilot environment can be validated before user access begins

---

## Out of Scope

This hardening pass does **not** include:
- broad new feature expansion
- advanced workflow automation
- enterprise SSO complexity beyond what is needed for pilot
- external ticketing integrations
- broad analytics expansion
- new AI-driven features
- large-scale design-system buildout
- multi-organization tenancy work

If a task does not directly improve pilot trust, control, or supportability, it should be treated as out of scope.

---

# Recommended Build Order

## Step 1 — Auth/RBAC Hardening
Do this first.

Reason:
If identity and access are not real, then pilot usage is not real either.

## Step 2 — UI Trust Pass
Do this second.

Reason:
The product needs to make a credible first impression and reduce hesitation for users.

## Step 3 — Pilot Ops Readiness
Do this third.

Reason:
By this point the product is controlled and presentable, and we can lock down how it will be operated during pilot use.

---

# Definition of Done

Pilot Readiness Hardening is complete when:

- authentication is backend-owned
- role enforcement is not client-asserted
- real user attribution is present in audit/usage flows
- primary screens feel visually polished and intentional
- pilot runbooks exist for the most likely operational failures
- the team can demonstrate and support the product without relying on tribal memory
- the product feels credible enough to place in front of pilot users without apology

---

# Recommended Deliverables

At the end of this hardening pass, create:

1. **Pilot Readiness Hardening Checkpoint Artifact**
2. **Pilot Go / No-Go Checklist**
3. **Pilot Demo Script**
4. **Pilot Rollout Plan**

That sequence prevents us from pretending readiness before we have actually earned it.

---

# Risks

## Risk: UI polish expands forever
**Mitigation:**  
Limit the visual pass to the six priority screens and a small shared styling foundation.

## Risk: Auth work balloons into enterprise identity scope
**Mitigation:**  
Implement the simplest backend-authenticated model that is credible for pilot use.

## Risk: Pilot support assumptions stay implicit
**Mitigation:**  
Write runbooks and ownership down before pilot access begins.

## Risk: We confuse “feature complete” with “pilot ready”
**Mitigation:**  
Treat trust, control, and supportability as first-class requirements.

---

# Recommended Next Action

Use this hardening plan as the input for the next build conversation.

The next chat should focus on:
1. breaking this document into concrete work packages
2. deciding the minimum viable pilot auth model
3. defining the UI trust pass scope screen by screen
4. identifying any final blockers before a real go/no-go call

---

# Bottom Line

We are close, but not done.

The system is ready to be shown.

It is not yet ready to be trusted by pilot users without a short, disciplined hardening pass.

That is not failure.

That is the last stretch before the software has to stop being clever and start being believable.