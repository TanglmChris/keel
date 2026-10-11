## ADDED Requirements

### Requirement: A group member can be listen-only

`keel chat group add <group> <role> --listen` MUST add `<role>` as a listen-only member of `<group>`. A listen-only member MUST receive the group's records, have them unread, and be woken by them exactly as any member, and MUST be able to acknowledge a record and close a todo assigned to it with `keel chat done`. It MUST be refused, naming that it is listen-only, when it posts or opens a todo in that group, adds or removes a member, or archives the group. `keel chat group list` MUST mark it. A member added without `--listen` MUST keep today's behavior.

#### Scenario: A listen-only member hears and is refused a post
- **WHEN** `review` is added to `soc` with `--listen` and `rtl` posts `@review is clause 4 waived?`
- **THEN** `review` has the record unread and is woken by it, and `keel chat post soc …` by `review` exits non-zero naming listen-only

#### Scenario: A listen-only member may acknowledge and close its todo
- **WHEN** `rtl` posts to `review` with `--ack` and assigns it a todo
- **THEN** `keel chat ack` and `keel chat done` by `review` succeed

#### Scenario: A listen-only member cannot change the group
- **WHEN** `review`, listen-only in `soc`, runs `keel chat group add soc spec` or `keel chat group archive soc`
- **THEN** each exits non-zero naming listen-only, and `keel chat group list` shows `review (listen)`
