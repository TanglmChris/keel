## Why

`change-close` routes unresolved follow-ups to a durable owner, and the forms it accepts are an
absolute `https://…` reference or a path that outlives the change. In practice that means a
tracker issue. The standing-authorization vocabulary has no name for creating one:

```
authorize: failed - keel/config.yaml declares unrecognized action: issue;
accepted names are commit, push, release, archive, continuation.
The whole declaration authorizes nothing until it is corrected.
```

So the gate asks for a tracker reference and the project has no way to say the agent may create
one (#136). The result is a loop that cannot be closed from inside: stop and ask mid-archive, or
point the durable owner at some pre-existing file that is *related* to the follow-up and does not
own it. The second is what happens, and it degrades exactly the property the gate exists to
protect.

The point is not that it should default to authorized. It is that **the project has no way to
say yes**, having decided to.

## What Changes

- **`issue` joins the vocabulary, and it must name the repository it reaches**:
  `issue:<owner>/<repo>`. A bare `issue` is refused, with the required form in the message.
- **The refusal is the design, not a nicety.** `gh` credentials are account-wide, so a bare
  `issue` would authorize an issue write to every repository the owner's account can touch — a
  wider reach than `commit` or `push`, which the checkout already bounds. Accepting the bare form
  "for convenience" would make the narrow one optional and the wide one the default, which is the
  opposite of the decision. Recorded as the precedent
  `scope-a-grant-to-the-resource-not-the-credential`.
- **`keel --doctor` renders the scoped entry**: `issue` reports `authorized` and names the
  repository it is scoped to, rather than reporting `not authorized` because the declared string
  is not the bare vocabulary name.
- **Fail-closed is preserved.** A malformed scope — a missing `owner/repo`, an extra segment — is
  an unrecognized entry, and one voids the whole declaration exactly as any other does today.
- **Closing an issue stays out of the vocabulary**, and so does commenting, labelling, and
  anything cross-repository. Closing in particular needs no name here: a pull request body
  carrying `Closes #<n>` closes the issue when it lands, which is how #133, #134, and #137 are
  already owned.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-standing-authorization`: an action whose credential reaches further than the action does
  is declared with the resource it may reach, and the unscoped form is refused.

## Impact

- `src/core/config.js` — the vocabulary entry, the scoped-entry parse, and the refusal message.
- `bin/keel.js` — the per-action doctor line.
- `scripts/validate_plugin.py` — one new scenario.
- `keel/config.yaml` — this repository declares `issue:TanglmChris/keel`, so the repository that
  ships the form is the one that demonstrates it, as it already does for `triage`'s bare-list
  form.
- **Keel authorizes and does not enforce.** It never invokes `gh`; the scope is a declaration the
  agent reads and obeys, exactly as `commit` is a declaration Keel never acts on. A reader who
  takes `issue:<owner>/<repo>` for a sandbox has been misled, so the surfaces say so.
