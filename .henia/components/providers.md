---
form: leaf
doc: Lists the providers of the given slots.
attributes:
  slots:
    type: list
    of: slot
    required: true
    doc: Slots whose providers to list.
body:
  kind: none
---
Slot providers:

:slot[{{range $i, $s := .slots}}{{if $i}} {{end}}{{$s}}{{end}}]

