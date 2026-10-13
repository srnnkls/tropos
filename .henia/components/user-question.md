---
form: container
doc: Asks the user a question with the listed options.
attributes:
  header:
    type: string
    required: true
  question:
    type: string
    required: true
  multi:
    type: boolean
    doc: Allows several options.
body:
  kind: text
---
```
Header: {{.header}}
Question: {{.question}}
multiSelect: {{if .multi}}true{{else}}false{{end}}
Options:
{{.body}}```
