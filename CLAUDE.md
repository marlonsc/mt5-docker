<!-- AIHUB-INVIOLABLE-LAW-PRELUDE v1 -->
# AI Hub Inviolable Law - Strict Prelude

These rules are loaded before any agent action and are not negotiable. Absolute truth: never claim done, green, or resolved without command, exit code, and decisive output. Root cause only: no bypass, fallback, shim, suppression, stub, hardcode, or old+new coexistence. Beads first: claim/update the bead before substantive work and keep evidence current. Research first: inspect code, docs, and canonical sources before acting; never invent APIs, flags, facts, or behavior. FLEXT first for ai-hub Python: use the project facades backed by flext-core and flext-cli; do not reimplement primitives locally. If a gate blocks, stop and escalate with the exact command/edit; never route around it. Land verified work with native gates, commit, fast-forward push, and bead evidence. If any rule cannot be followed cleanly, stop and ask the operator.
<!-- /AIHUB-INVIOLABLE-LAW-PRELUDE -->

# CLAUDE.md

Canonical governance lives in this repo's `AGENTS.md` (the ai-hub-managed universal-core block,
mirrored from `~/.agents/UNIVERSAL_CORE.md`) and in `~/.ai-hub`. **Do not duplicate rules here** —
keep only project-specific notes below.

- **Task tracking:** `bd` (beads). Run `bd prime`.
- **Validation:** prefer `make` targets (`make lint` / `make typecheck` / `make test`).
- **Tools:** `ast-grep` (`sg`) for structural search; never `rm` / `sed -i` (use the Edit tool or `trash-put`).

<!-- project-specific notes below -->
