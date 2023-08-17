### [confluent schema-purge](schema-purge/confluent-schema_purge.py)
  - Performs a hard delete for all schemas
  - User prompted to confirm
#### Requirements
  - Python 3 (3.10.9 used for this plugin)  `brew install python3`
  - [Confluent CLI v3](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent schema-registry schema purge [-h] [--subject-prefix SUBJECT_PREFIX] [--context CONTEXT] [--env ENV]

Deletes schemas This plugin assumes confluent CLI v3.25.0 or greater

options:
  -h, --help                      Show this help message and exit
  --subject-prefix SUBJECT_PREFIX List schemas for subjects matching the prefix
  --context CONTEXT               The CLI context name
  --env ENV                       The environment ID
```
