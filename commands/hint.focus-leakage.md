**The user triggered this hint because focus leaked into your recent output.**

## Response Workflow

1. Review your last changes (code comments, markdown documents, plans)
2. Identify the focus leakage
3. Fix it immediately
4. Do not defend or explain - just fix

## Example

```python
# ✘ WRONG: Comment restates what the function name already says
# Check for ExitPlanMode
if detect_exit_plan_mode(input_data):

# ✓ CORRECT: Function name is self-documenting
if detect_exit_plan_mode(input_data):
```

---

Don't let your focus leak into artifacts. Stick to the 5x rule w.r.t. comments!

**The 5x Rule:** Spend 5x more time finding good names than writing comments.

**Write comments for:**
- WHY (business rules, workarounds, non-obvious decisions)
- Critical invariants that can't be encoded in types

**Don't write comments for:**
- Focus leakage (your thought process, plans, or TODO notes that should stay in your head or task list)
- WHAT the code does (the code already says this)
- HOW it works (should be obvious from good names)
- Restating the obvious (type hints + names make it clear)
- Structuring sections (`# ====`) → Split into modules instead

When you feel the urge to add a comment, ask yourself: "Can I make this code so clear through naming that the comment becomes unnecessary?"
