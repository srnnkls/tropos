---
form: leaf
doc: Lists the skill's slot providers and context commands as preloads.
attributes:
  slots:
    type: list
    of: slot
    doc: Slots whose providers the context lists.
body:
  kind: none
---
## Context

{{if .slots -}}
::include{component="providers" slots="{{range $i, $s := .slots}}{{if $i}} {{end}}{{$s}}{{end}}"}

{{end}}{{range .context_commands}}{{.label}}:
!`{{.command}}`

{{end}}