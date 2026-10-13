---
form: container
doc: Marks the hybrid head, with its runtime context, slot providers and title.
attributes:
  context:
    type: boolean
    doc: Opens the head with the skill's runtime context.
  title:
    type: string
    doc: Titles the head.
  slots:
    type: list
    of: slot
    doc: Slots whose providers the head lists.
body:
  kind: markdown
---
{{if .context -}}
::include{component="context" slots="{{range $i, $s := .slots}}{{if $i}} {{end}}{{$s}}{{end}}"}

{{else if .slots -}}
::include{component="providers" slots="{{range $i, $s := .slots}}{{if $i}} {{end}}{{$s}}{{end}}"}

{{end}}{{if .title -}}
::include{component="title" title="{{.title}}"}

{{end}}::body
