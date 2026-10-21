## Decisions

- **D1** — The split. Four pieces move verbatim from `src/skills/keel-review-checklist/SKILL.md` to `conditional-checks.md`:
  - the `Coupling: required` bullet;
  - `## Domain lenses`;
  - `## Skill change review`;
  - `## Planning artifact funnel`.

  In `conditional-checks.md`, each piece sits under a heading that names its condition. `SKILL.md` gains `## Conditional checks`, which lists the four conditions and says to read `conditional-checks.md` beside the file when one applies, and only then. The file is not `guidance.md`. A guidance file is read unless `executor_tier: high` is set and "states no criterion"; these are criteria read by condition.
- **D2** — The handoff paragraph, added under Purpose: "The shift note that `keel shift ready` stores is a different thing: it hands working context to the role's next session and selects no task. HANDOFF overrides which task `keel context` selects. Neither holds task state; OpenSpec does."
- **D3** — Parity covers the whole skill directory. `native-plugin-manifests` compares the relative file set of `src/skills/<skill>/` and `plugins/keel/skills/<skill>/`, then the bytes of each file. A missing file and a differing file each get their own message. This replaces the `SKILL.md` and `guidance.md` comparison.
- **D4** — Moved text stays checked. `SKILL_DOC_REQUIREMENTS` keeps the review-checklist entry for what stays in `SKILL.md`, and adds an entry for `conditional-checks.md` holding the literals that moved: `## Skill change review`, `authoritative sources`, `provenance and license`, `positive and negative trigger cases`, `real-task evidence`, `portable \`SKILL.md\``, and `target-native discovery`. `plan-funnel-guidance` reads `conditional-checks.md` in both copies and checks they are byte-identical. The handoff entry gains `keel shift ready`.
- **D5** — Evidence. A new scenario, `review-checklist-conditional-checks`, checks the following:
  - the base `SKILL.md` names the file and its four conditions, and lacks the moved headings;
  - `conditional-checks.md` holds them;
  - `SKILL.md` is shorter than 80 lines;
  - the handoff skill names `keel shift ready`.

  `native-plugin-manifests` is the parity check. Deleting the plugin's copy of `conditional-checks.md` must make it fail, naming the file.
