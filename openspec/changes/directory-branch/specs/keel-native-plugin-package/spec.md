## REMOVED Requirements

### Requirement: Each release states its official directory entry

**Reason**: Anthropic's plugin directory now tracks a branch of a repository through the claude.ai developer portal and no longer takes an entry pinned to a commit, so the pinned entry describes nothing the directory reads (#175).

**Migration**: Each release updates the `claude-directory` branch instead, as the requirement "Each release updates the directory branch" states.

## ADDED Requirements

### Requirement: Each release updates the directory branch

Keel MUST be able to build, from the files its npm package publishes, the plugin tree that Anthropic's plugin directory lists. In that tree, `.claude-plugin/plugin.json` is the root manifest with the name `keel-openspec`, and `.claude-plugin/icon.png` is a square PNG. The repository's own root manifest MUST keep the name `keel`. The release job MUST commit that tree to the `claude-directory` branch and push it, and MUST name the resulting commit in the release notes. Building the tree MUST be local, and nothing in Keel MAY submit it to the directory.

#### Scenario: The tree is the package with the directory's name
- **WHEN** `scripts/directory_tree.js` builds into an empty directory
- **THEN** the tree holds exactly the files `npm pack` publishes plus `.claude-plugin/plugin.json` and `.claude-plugin/icon.png`
- **AND THEN** its manifest is the root manifest with `name` set to `keel-openspec`, every skill, agent, and hook path in it resolves inside the tree, and the repository's root manifest still names `keel`

#### Scenario: Each release advances the directory branch
- **WHEN** `scripts/directory_branch.js` runs for a version and commit against an origin
- **THEN** origin's `claude-directory` gains one commit whose tree is the directory tree and whose message names the version and commit, starting the branch when it does not exist
- **AND THEN** running it again with an unchanged tree adds no commit

#### Scenario: The release notes name the branch commit
- **WHEN** the release job creates the release for a landed version
- **THEN** it runs `scripts/directory_branch.js` for that version and the tag's commit, and the notes name `keel-openspec`, the `claude-directory` branch, and the commit it printed
