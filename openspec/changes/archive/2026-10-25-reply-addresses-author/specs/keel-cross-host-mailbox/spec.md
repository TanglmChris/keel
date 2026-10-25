## ADDED Requirements

### Requirement: A reply addresses the role it answers

When `keel chat post <group> <text> --reply-to <id>` answers a record of another role that is a member of the group, the reply MUST mention that role, as if its text wrote `@role`, so that the notice, the hooks, `keel chat notice --check`, and the waker treat it as addressed to that role. A reply to the replier's own record, or to a record whose author is not a member of the group, MUST NOT add a mention.

#### Scenario: A reply without @ reaches the author it answers
- **WHEN** `rtl` posts r1 to `soc`, and `verify` posts `keel chat post soc "closed both" --reply-to r1` without writing `@rtl`
- **THEN** the reply's mentions include `rtl`, `rtl`'s `keel chat notice` lists it among the records addressed to it, and `keel chat notice --check` in `rtl`'s worktree exits 0

#### Scenario: A reply to one's own record, or no reply at all, addresses no one
- **WHEN** `rtl` has read `soc`, and `verify` then replies to its own record without `@`, and posts a plain message without `--reply-to` or `@`
- **THEN** neither record mentions anyone, and `keel chat notice --check` in `rtl`'s worktree exits 1
