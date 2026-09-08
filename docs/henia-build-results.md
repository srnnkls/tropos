# Henia build results

## Outcome

All nine bundled profiles compiled the feature fixture in all three render formats: 27 successful native CLI builds per replay. The first replay completed 87 cases; the expanded replay completed 112, for 199 recorded case executions and 112 distinct cases. Exit codes and output inventories are recorded. Uninspected output semantics are identified below.

The replay uses an evidence-local HOME and does not download dependencies, access the network, or invoke deployment tools.

## Replay and evidence

From the Tropos worktree:

```sh
python3 prototype/henia/build/replay.py
```

The script executes the installed native `henia build` command. It creates timestamped evidence directories. Its reusable source fixture is `prototype/henia/build/fixtures/skills/probe/SKILL.md`; per-case configurations, custom profiles, additional source files, logs, and compiled artifacts are materialized beneath the evidence directory.

Recorded runs:

- `.henia/evidence/build/20260908-172437/`: initial completed replay.
- `.henia/evidence/build/20260908-172641/`: expanded completed replay; final output inspection incomplete.

Each case contains `command.sh`, `stdout.log`, `stderr.log`, `henia.toml`, and its local source directory. The run contains `results.json` and `provenance.json`. The JSON file inventory covers the ordinary `out` directory only; configured alternate destinations and symlink destinations require direct inspection.

Exact case reproduction commands below use:

```sh
E=/Users/srnnkls/projects/tropos/.worktrees/henia-phora/.henia/evidence/build/20260908-172641
```

`command.sh` records the full executable path, source path, config path, output flags, invocation directory, and isolated HOME. Replaying a recorded command overwrites its existing generated output; use the full replay for fresh filesystem preconditions, especially permission, symlink, stale-output, and overwrite probes.

Binary inspected: `/Users/srnnkls/.local/bin/henia`, SHA-256 `9ba79b0664cdc075145deefe1e9d90dc8216e93e1c36cc42b83b74df00720af9`. Go build metadata identifies Go 1.26.5, revision `084015a1a61935eff238f2dc9e51aa1cf75a7412`, and `vcs.modified=true`. The upstream checkout reported the same HEAD; this is evidence for the installed dirty build, not a claim that the binary exactly matches a clean checkout.

## Coverage

| Area | Exercised behavior and observed result |
|---|---|
| Profiles and formats | `claude`, `codex`, `opencode`, `gemini`, `github`, `cursor`, `chatgpt`, `claude-upload`, and `agentskills`, each with `xml`, `directives`, and `markdown`: all 27 exited 0 and emitted a main file plus two resources. |
| Default selection | No harness declaration built nine artifacts; `--harness claude,codex` built two; an unknown selection failed. |
| Templates | `if`, `range`, `with`, named `define`/`template` composition, nested metadata interpolation, and frontmatter/canonical/harness precedence were exercised. The inspected Claude XML output contained both range items, the nested value, the true branch, and harness precedence in body and metadata. Canonical-only and frontmatter-only output contained `Precedence=canonical` and `Precedence=frontmatter`, respectively, with matching metadata and directive attributes. The false-branch case emitted `no`. |
| Nested metadata | Nested map strings were verified in the inspected output. The native array interpolation case emitted `paths: [probe/one, probe/two]`. |
| Directive rendering | Inspected XML output contained nested block tags, an inline tag, quoted attributes, ID and class attributes, and preserved escaped directive syntax, inline directive code, and fenced directive code. All three formats compiled across all nine profiles. |
| Directive errors | Unclosed block/inline syntax and duplicate or malformed attributes failed. Additional nested-inline, escaped-attribute, blockquote, list, and indented-code coverage was attempted as a combined fixture; it failed at an indented directive and does not verify those branches independently. |
| References | All five reference kinds and unknown tools were exercised. The inspected combined fixture left references unchanged after a code fence. Isolated references, references after fences, tilde-fenced references, indented references, and escaped backticks were subsequently run, but their output inspection remains pending. |
| Native overrides | Claude output was inspected: tools became `Read Bash`, target `auto_invoke: false` became `disable-model-invocation: true`, native model won, `argument-hint` appeared, and null removed inherited license and user-invocable output. The Codex sidecar contained interface metadata, `policy.allow_implicit_invocation: true`, and a dependency tool with `type: mcp` and `value: local`. |
| Metadata validation | Strict unsupported metadata, invalid canonical description type, invalid native model type, invalid OpenAI display-name type, unavailable model-tier mapping, and conflicting aliases all failed. |
| Custom profiles and Expr | Project-local profile with aliases, legacy key/value mappings, computed values, immutable-input reads, `require`, `merge`, context variables, and JSON/YAML/text sidecars exited 0 and emitted four files. Nil/empty-map file declarations produced no additional files. Inspected outputs retained booleans and numbers, `seen: mapped`, and `renamed: native-value`; the JSON sidecar contained `merged.a: [1, 2]` and `merged.enabled: false`. The null-override case omitted `renamed` and emitted JSON `native: null`. YAML and text sidecars contained `enabled: false` and `text:probe`, respectively. Parse/runtime expression errors and invalid text-sidecar value type failed. |
| Profile layers | An isolated user profile plus project profile compiled successfully. The layered output retained `from-user: true` alongside project fields and emitted four files. Missing profile failed. |
| Legacy output | Explicit flat skills, agents, and commands built three main artifacts plus one resource. Generated commands were requested but absent; see gaps. |
| Config merge | Isolated user `strict=true` plus project `strict=false` compiled warning-producing metadata. User include array `[second]` plus project `[probe]` built two artifacts, confirming concatenation rather than replacement. The variable override emitted `Precedence=project` and matching metadata. TOML null failed parsing. |
| Filtering and paths | Exact include/exclude produced one artifact; glob-looking include and exclude-all produced no-artifact errors. Config-relative and CLI-relative output cases exited 0; the ordinary inventory intentionally does not cover those alternate locations. Unknown config options, invalid format, and invalid harness names failed. |
| Resources | Main matrix builds copied a text resource and executable-source script. Resource bytes and final modes were not independently compared. Hidden resources produced three files. An empty resource directory produced only the main file; directory retention was not inspected. |
| Collisions | Source/generated sidecar, generated/main, duplicate artifact, shared generated file, and generated file/directory collisions failed. |
| Confinement | Generated traversal, absolute, and backslash paths failed. Canonical direct overwrite, nested output inside a canonical skill, and symlink alias to canonical source failed. Resource file and directory symlinks failed. Output symlink escaping the harness root failed. |
| Symlink boundaries | A harness-root symlink built successfully, so the resolved harness root is the effective boundary rather than an unconditional prohibition on symlinked roots. A source main-file symlink built; a symlinked source skill directory failed discovery. Exact diagnostics for the latter were not inspected. |
| Failure behavior | Invalid transformation across two harnesses failed with no output files. A write-time destination-directory conflict failed after another artifact had been written. A non-writable output root failed. Rebuild with a stale artifact exited 0 and retained two files. |
| Phase boundaries | `[sources]` and harness `path` settings failed; Henia delegates fetching and deployment to Phora. Upload profiles emitted local directories only. |

## Verified gaps and limitations

### Generated commands are not emitted

Reproduce:

```sh
sh "$E/generated-command/command.sh"
sh "$E/legacy-flat/command.sh"
```

Expected: `generate_commands_from_skills=true` emits a command corresponding to the canonical skill, in addition to explicitly authored commands where present.

Actual: the skill-only case exits 0 with only `out/legacy/skills/probe.md`. The mixed case emits the authored skill, agent, command, and resource, but no command generated from the skill. The CLI accepts the setting without an unsupported-feature diagnostic.

The same mixed case requests `artifact_mappings.agents.keys.description="agent-description"`, but the generated agent retains `description: Agent probe.`. Source inspection found that build construction passes general key/value maps without the artifact-specific maps.

### Invalid reference templates do not fail the build

Reproduce:

```sh
sh "$E/invalid-reference-template/command.sh"
```

Expected: an invalid configured reference template such as `{{if}}` fails configuration or transformation with a diagnostic.

Actual: exit 0 and one generated skill. Source inspection confirms reference-template errors are discarded and the original reference is retained rather than surfaced.

### Code preceding references can prevent rewriting

Reproduce:

```sh
sh "$E/all-references/command.sh"
```

Expected: configured command, agent, and file references in ordinary prose are rewritten independently of preceding literal code.

Actual: the inspected generated skill retained all six original backtick references, including the three explicitly configured reference kinds. The preceding directive-code fence and inline literals are present in the fixture. The reference implementation scans raw backtick spans rather than Markdown code nodes.

Further isolation commands were executed, but their rendered results were not inspected:

```sh
sh "$E/references-isolated/command.sh"
sh "$E/references-after-fence/command.sh"
sh "$E/references-in-tilde-fence/command.sh"
sh "$E/references-indented-code/command.sh"
sh "$E/references-escaped-backticks/command.sh"
```

Do not infer exact fence-specific failure modes or literal-code corruption from their successful exits alone.

### Missing template variables are not build errors

Reproduce:

```sh
sh "$E/missing-template/command.sh"
```

Expected for an authoring safety gate: unresolved required interpolation is diagnosed.

Actual: `Missing={{.absent}}.` compiles with exit 0 and emits `Missing=<no value>.`. The source uses Go templates without a missing-key error option. Unresolved interpolation therefore requires a separate authoring check.

### Canonical scalar tools are rejected

Reproduce:

```sh
sh "$E/tool-scalar/command.sh"
sh "$E/tool-native-scalar/command.sh"
```

Expected when applying the documented scalar-preserving tool helper to canonical `tools`: preserve `Bash(git diff *)` as one expression.

Actual: canonical scalar `tools` fails with `canonical tools must be a list of strings`. The alternate `allowed_tools` scalar case exits 0. Canonical lists work and were verified as `Read Bash` in native output. The helper's scalar support does not remove canonical validation restrictions.

### Confined output-directory symlinks still fail writes

Reproduce using fresh preconditions from the full replay, then inspect:

```sh
sh "$E/output-symlink-internal/command.sh"
```

Expected: an existing directory symlink that stays inside the harness root is either supported or explicitly rejected during preflight.

Actual: preflight permits it, then the build fails with `write probe for claude: mkdirat skills/probe: file exists`. An escaping output symlink is separately rejected before writing. Do not rely on internal directory symlinks as reusable output layout.

### Combined markup-context probe is blocked

Reproduce:

```sh
sh "$E/markup-contexts-xml/command.sh"
sh "$E/markup-contexts-directives/command.sh"
sh "$E/markup-contexts-markdown/command.sh"
```

Expected: the intended indented code literal remains literal, while the separate nested-inline, quoted-attribute, blockquote, and list directives render.

Actual: all three fail; the inspected XML diagnostic is `render directives: 15:5: unclosed directive indented-literal`. Because this is a combined fixture, no isolated upstream defect is claimed. Those additional contexts remain unverified.

### Markdown directive labels conflict with Tropos artifact style

Reproduce:

```sh
sh "$E/matrix-claude-markdown/command.sh"
```

Expected for Tropos-authored artifacts: no bold labels introduced solely for formatting.

Actual capability: Henia documents and implements its `markdown` renderer using bold directive labels and attributes; the matrix confirms that this rendering mode compiles. This rendering contract conflicts with Tropos artifact style. XML and normalized directives avoid those labels. Detailed markdown output was not separately inspected.

### Deferred and intentionally unavailable capabilities

| Capability | Exact reproduction | Expected and actual |
|---|---|---|
| Two-colon leaf directives | `sh "$E/leaf-directive/command.sh"` | Documented as deferred. Build exits 0; no semantic leaf transformation was verified. |
| TOML null layer override | `sh "$E/toml-null/command.sh"` | TOML has no null literal; configuration fails. YAML native override null is supported and verified separately. |
| Glob include patterns | `sh "$E/include-glob/command.sh"` | Filters are exact artifact-name lists, not glob matchers. `pro*` selects nothing and build fails with no artifacts. |
| Flat profile output | `sh "$E/profile-flat/command.sh"` | Skill profiles require nested structure; profile plus flat output fails. Explicit legacy flat mode works. |
| Fetching | `sh "$E/sources-setting/command.sh"` | Henia rejects source registry settings; Phora owns fetching. |
| Deployment destinations | `sh "$E/deployment-setting/command.sh"` | Henia rejects harness installation paths; use build output and a separate Phora pipeline. |
| Upload, ZIP, publication | `sh "$E/matrix-claude-upload-directives/command.sh"` | Upload profile stages a local directory. No upload, archive, or publication command was executed or is supplied by this build workflow. |
| Transactional write rollback | `sh "$E/write-partial/command.sh"` | Write-time failure can leave partial artifacts; one completed artifact remained. Preflight failures were separately all-or-none. |
| Stale artifact pruning | `sh "$E/stale-rebuild/command.sh"` | Build does not prune; the pre-existing stale artifact remained alongside the rebuilt skill. |

### Resource overwrites retain a nonexecutable destination mode

The `resource-mode-rebuild` case rebuilds an executable source script over an existing mode-0644 resource. Build exits 0, but native `stat` reports source mode 0755 and output mode 0644. Henia does not restore the executable bit on overwrite. The deployment wrapper uses fresh output directories.

Evidence: `resource-mode-rebuild/source/skills/probe/script` and `resource-mode-rebuild/out/claude/skills/probe/script` under the expanded replay directory. Run the full replay to recreate the overwrite precondition.

### Harness variables accept strings only

Harness variables are string-valued; the deployment failure and working configuration are recorded in [the integration report](henia-phora-prototype.md#harness-variables-are-strings). That deployment probe is outside the compiler replay count. Typed booleans/lists remain supported in canonical `henia.variables`.

## Pending verification

These behaviors remain unverified:

- Resource byte-for-byte equality and fresh executable modes across the matrix.
- Exhaustive alias/value-map order and immutable-input semantics beyond the inspected custom-profile values.
- Codex native policy precedence beyond the inspected sidecar contents.
- Full profile-specific metadata filtering and aliases for every supported metadata field. The 27-case matrix establishes format compilation, not an exhaustive schema-value matrix.
- Individual nested-inline/blockquote/list/escaped-attribute cases blocked by the combined markup fixture.
- Exact rendering of the isolated reference cases.
- Direct filesystem inspection of alternate relative output destinations, empty resource directories, and the harness-root symlink target.
- Crash interruption, concurrent filesystem mutation, symlink race behavior, and special resource files were not exercised.

## Sources consulted

Local upstream resources:

- `/Users/srnnkls/projects/henia/README.md`
- `/Users/srnnkls/projects/henia/docs/vendor-profiles.md`
- `/Users/srnnkls/projects/henia/internal/defaults/henia.toml`
- `/Users/srnnkls/projects/henia/examples/skills/review/SKILL.md`
- `/Users/srnnkls/projects/henia/config.go`
- `/Users/srnnkls/projects/henia/internal/config/config.go`
- `/Users/srnnkls/projects/henia/internal/cli/build.go`
- `/Users/srnnkls/projects/henia/internal/build/build.go`
- `/Users/srnnkls/projects/henia/internal/target/target.go`
- `/Users/srnnkls/projects/henia/internal/transform/transform.go`
- `/Users/srnnkls/projects/henia/internal/reference/reference.go`
- `/Users/srnnkls/projects/henia/internal/vendor/skill.go`
- `/Users/srnnkls/projects/henia/internal/vendor/profiles/claude.toml`
- `/Users/srnnkls/projects/henia/internal/markup/markup_test.go`
