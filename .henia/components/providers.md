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

Resolve with one `henia slots --inline` over these slots, each requested as `<slot>.<domain>` and `<slot>.<language>`; read the whole output.

:slot[{{range $i, $s := .slots}}{{if $i}} {{end}}{{$s}}{{end}}]

