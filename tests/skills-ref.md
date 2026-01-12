# Skills-Ref Integration Tests

## Validate code-test Skill

```scrut
$ uv run "$TESTDIR/fixtures/validate_skill.py" validate "$TESTDIR/../skills/code-test"
Valid skill: * (glob)
```

## Validate code-review Skill

```scrut
$ uv run "$TESTDIR/fixtures/validate_skill.py" validate "$TESTDIR/../skills/code-review"
Valid skill: * (glob)
```

## Validate spec-create Skill

```scrut
$ uv run "$TESTDIR/fixtures/validate_skill.py" validate "$TESTDIR/../skills/spec-create"
Valid skill: * (glob)
```

## Read Properties

```scrut
$ uv run "$TESTDIR/fixtures/validate_skill.py" read-properties "$TESTDIR/../skills/code-test"
{
  "name": "code-test",
  "description": * (glob)
}
```

## Generate Prompt XML

```scrut
$ uv run "$TESTDIR/fixtures/validate_skill.py" to-prompt "$TESTDIR/../skills/code-test" "$TESTDIR/../skills/code-review" | head -1
<available_skills>
```
