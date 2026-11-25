---
form: leaf
doc: Lists the providers of the given slots with the one command that resolves them.
attributes:
  slots:
    type: list
    of: slot
    required: true
    doc: Slots whose providers to resolve.
body:
  kind: none
---
Slot providers:

Resolve with one `henia slots --inline` call: `--skill` for each loaded skill, `--key` for the task's domain and each language; read the whole output.

:slot[{{range $i, $s := .slots}}{{if $i}} {{end}}{{$s}}{{end}}]

