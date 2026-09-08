---
name: probe
description: "Build feature probe for {{.priority}}."
license: MIT
metadata:
  precedence: "{{.priority}}"
  nested: "{{with .henia.variables.group}}{{.label}}{{end}}"
priority: frontmatter
henia:
  variables:
    priority: canonical
    checks: [alpha, beta]
    group:
      label: nested-value
---
{{define "item"}}Item={{.}}.{{end}}
{{if .checks}}Condition=yes.{{else}}Condition=no.{{end}}
{{range .checks}}{{template "item" .}}
{{end}}
{{with .group}}With={{.label}}.{{end}}
Precedence={{.priority}}.

::::instruction{priority="{{.priority}}" #outer .urgent title="two words"}
Outer :badge[inline]{tone="high"}.

:::step{order=1}
Nested text.
:::
::::

Escaped \:badge[plain] and \:::instruction.

`:badge[literal]{tone=low}`

```text
:::instruction{priority=literal}
Code stays literal.
:::
```

References `$probe`, `/launch`, `@helper`, `#reference/data.txt`, `!read`, `!unknown`.

[Local resource](reference/data.txt)
