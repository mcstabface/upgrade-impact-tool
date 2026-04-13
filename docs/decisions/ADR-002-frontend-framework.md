# ADR-002 — Frontend Framework Choice

## Status
Accepted

## Context
Phase 0 required a frontend that could stand up route shells quickly, consume typed API responses, and support a clean user workflow without introducing heavy framework overhead.

## Decision
Use React with Vite and TypeScript for the frontend.

## Consequences
Benefits:
- fast development server
- straightforward route shell construction
- strong TypeScript support
- low ceremony for connecting to backend APIs

Tradeoffs:
- shared types are mirrored, not generated
- UI state management remains manual for now
- route/data conventions must be kept disciplined as the app grows

## Deferred / Follow-up
- no advanced component library in Phase 0
- no design system in Phase 0
- no SSR or deployment optimization work in Phase 0