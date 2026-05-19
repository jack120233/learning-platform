# brainstorm: diagnose UI frontend startup failure

## Goal

Find why the frontend in `UI` does not start and identify the minimal fix or correct startup command so the Vite dev server can run reliably.

## What I already know

* The user reported the frontend under `UI` cannot start.
* The repository root is not the frontend package root.
* `UI/package.json` defines `npm run dev` as `vite` and `npm run dev:reset` as cache reset plus `vite --force`.
* Running `npm run dev` from the repository root fails because `/Users/jacob/Developer/a3.learn_platform/learning-platform/package.json` does not exist.

## Assumptions (temporary)

* The likely immediate issue is launching from the wrong directory, but `UI` itself still needs to be tested for dependency, Vite, or port issues.

## Open Questions

* None yet; continue deriving from local inspection and startup output.

## Requirements (evolving)

* Reproduce the startup failure.
* Determine whether the failure is wrong working directory, missing dependencies, incompatible Node/npm/Vite versions, port conflict, or project code error.
* Avoid changing frontend code unless the root cause requires it.

## Acceptance Criteria (evolving)

* [ ] The exact startup failure is identified.
* [ ] The correct startup command or code/config fix is provided.
* [ ] If files are changed under `UI`, update `UI/operations-log.md`.

## Definition of Done (team quality bar)

* Frontend startup path verified.
* Build/typecheck considered if code/config changes are made.
* No unrelated frontend behavior changed.

## Out of Scope (explicit)

* Redesigning the frontend.
* Changing backend behavior unless startup diagnosis proves it is required.

## Technical Notes

* `UI/package.json` scripts: `dev`, `dev:force`, `dev:reset`, `build`, `preview`.
* Root-level `npm run dev` is invalid in this repo because the root is not a npm package.
