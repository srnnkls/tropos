# Code Review Checklist

---

## Correctness

- [ ] Logic matches stated requirements
- [ ] Edge cases handled (null, empty, boundary conditions)
- [ ] Error handling present and appropriate
- [ ] Type safety maintained
- [ ] No off-by-one errors

## Style

- [ ] Consistent naming conventions
- [ ] Code is readable without excessive comments
- [ ] No commented-out code
- [ ] Follows project conventions

## Performance

- [ ] No unnecessary computations
- [ ] Appropriate data structures used
- [ ] No N+1 query patterns
- [ ] Resource cleanup handled (files, connections)

## Security

- [ ] No hardcoded secrets or credentials
- [ ] Input validation at boundaries
- [ ] No injection vulnerabilities (SQL, command, etc.)
- [ ] Safe handling of user-provided paths

## Over-engineering

- [ ] No speculative abstraction — interface, factory, or layer with one implementation; inline until a second exists
- [ ] No hand-rolled code the stdlib or platform already ships
- [ ] No new dependency for what a few lines or an installed dep covers
- [ ] No dead flexibility — unused config, flags, or parameters
- [ ] Same behavior couldn't be materially shorter

## Architecture

- [ ] Single responsibility principle
- [ ] Appropriate coupling between components
- [ ] Clear interfaces and contracts
- [ ] No circular dependencies

## Testing (if applicable)

- [ ] Tests cover the change
- [ ] Edge cases tested
- [ ] Tests are readable and maintainable

---

## Severity Quick Reference

| Severity | Examples |
|----------|----------|
| **Critical** | Security vulnerability, data loss, crash |
| **High** | Logic error, missing validation, unclear behavior |
| **Medium** | Style issue, minor inefficiency, missing docs |
