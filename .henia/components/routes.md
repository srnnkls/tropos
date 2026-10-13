---
form: container
doc: Routes the skill's arguments.
attributes:
  ordered:
    type: boolean
    doc: Rows apply in order; the first match wins.
  protocol:
    type: boolean
    doc: Links the dispatch protocol.
body:
  kind: markdown
---
## Routes

{{if .ordered}}Apply the first row that matches `$ARGUMENTS`:

{{end}}::body
{{if .protocol}}{{$p := "../dispatch/protocol.md"}}{{if eq .name "dispatch"}}{{$p = "protocol.md"}}{{end}}
> **Protocol:** [{{$p}}]({{$p}})
{{end}}
