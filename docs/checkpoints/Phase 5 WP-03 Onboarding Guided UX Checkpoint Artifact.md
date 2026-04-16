# Upgrade Impact Tool — Phase 5 WP-03 Onboarding and Guided UX Checkpoint Artifact

**Date:** 2026-04-15  
**Status:** Checkpoint Complete  
**Phase:** Phase 5  
**Work Package:** WP-03 Onboarding and Guided UX

## Objective

WP-03 introduced the first bounded onboarding and guided UX layer for the Upgrade Impact Tool.

The goal of this checkpoint was not a full walkthrough system or training overlay. The goal was to make the current MVP intake and results experience more legible by adding practical guidance, explaining why fields matter, and improving the explanatory quality of blocked / unknown / review-needed states.

## Completed Scope

### 1. Guided Intake Helper Text

Delivered:
- helper text for major intake sections
- examples for environment naming
- examples for application/module entry
- KB source guidance
- clearer wording around how the intake should be prepared before submission

Result:
- intake is now more understandable for first-pass users and less dependent on tribal knowledge

### 2. “Why We Ask” Explanations

Delivered:
- environment rationale
- application/version rationale
- contact rationale
- KB provenance rationale

Result:
- the form now explains why requested data matters to downstream analysis, review, and trustworthiness

### 3. Sample Intake Prep Guidance

Delivered:
- sample intake prep checklist
- inline sample intake template
- copyable example intake content

Result:
- users now have a concrete reference for the level of detail expected before running analysis

### 4. Improved Blocked / Warning Guidance on Intake

Delivered:
- blocked validation language rewritten as recovery guidance
- warnings rewritten to explain downstream consequences rather than merely listing issues

Result:
- intake failures now read like actionable guidance instead of opaque validation fallout

### 5. Improved Status Explanation Surfaces

Delivered:
- richer `StatusHelp` text
- expanded `StatusBanner` messaging for:
  - `UNKNOWN`
  - `REQUIRES_REVIEW`
  - `BLOCKED`
- explicit “What to do next” bullets on banner states

Result:
- result surfaces now provide more useful explanations of ambiguous or unresolved states

### 6. Expanded Empty-State Guidance Structure

Delivered:
- empty-state component now supports optional guidance title and follow-up guidance items

Result:
- the UI now has a reusable structure for instructional empty states without redesigning current views

## Verified Behaviors

### Intake Guidance
Verified:
- “Before you start” guidance is visible
- sample prep checklist is visible
- sample intake template is visible
- copy sample template action is available
- each major intake section includes helper text
- each major intake section includes “Why we ask” explanatory copy

### Intake Recovery Language
Verified:
- blocked validation section explains what is missing and what to do next
- warning section explains likely downstream consequences of incomplete context

### Result-State Guidance
Verified:
- blocked / unknown / requires-review surfaces now provide:
  - clearer explanation
  - practical next-step bullets
  - more user-forward language

## Architectural Notes

WP-03 preserved current MVP architecture and constraints:

- no new workflow engine
- no guided-tour framework
- no modal walkthrough system
- no external help service
- no redesign of the intake flow
- no asynchronous onboarding state
- no new persistence model for onboarding progress

Guidance was added directly to existing frontend surfaces using the current component structure.

## Invariants Preserved

- synchronous MVP execution path remains unchanged
- current intake workflow remains unchanged
- guidance is additive and explanatory, not a new process layer
- backend validation remains source of truth
- frontend guidance does not replace backend enforcement or validation
- current architecture, ownership, and route structure remain intact

## Deferred / Not Yet Implemented

Not completed in this checkpoint:

- multi-step walkthrough or wizard mode
- downloadable intake template file artifacts
- guided onboarding state persistence
- inline contextual help expansion/collapse controls
- role-specific onboarding copy
- richer unknown/blocked guidance on every page
- first-run dashboard guidance
- deeper review-queue education patterns
- user-forward onboarding analytics or completion tracking

## Outcome

WP-03 established the first real guided UX layer for the Upgrade Impact Tool.

The system now does a better job of:
- telling users what to prepare
- explaining why inputs matter
- reducing ambiguity during intake
- making unresolved result states more understandable

This improves usability and trust without violating the current MVP scope or introducing a redesign.

## Recommended Next Step

Proceed to the next bounded WP-03 slice only after preserving this checkpoint.

The next reasonable slice is:
- extend user-forward explanation patterns to additional results surfaces, especially blocked / unknown explanation consistency across more pages, before considering any larger onboarding framework work.

## Bottom Line

WP-03 now has a real foundation.

The app still expects users to bring facts, but it is at least no longer greeting them with the UX equivalent of a blank stare and an accusation.