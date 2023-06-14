### [confluent schema-purge](schema-purge/confluent-schema_purge.py)
 - Performs a hard delete for all schemas
   - User prompted to confirm
#### Requirements
  - Python 3 (3.10.9 used for this plugin)  `brew install python3`
  - [Confluent CLI v3](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent schema-purge [-h] [--subject-prefix SUBJECT_PREFIX] [--api-key API_KEY] [--api-secret API_SECRET] [--context CONTEXT] [--env ENV] [--secrets-file SECRETS_FILE]

Deletes schemas This plugin assumes confluent CLI v3.0.0 or greater

options:
  -h, --help            show this help message and exit
  --subject-prefix SUBJECT_PREFIX
                        List schemas for subjects matching the prefix
  --api-key API_KEY     The API key
  --api-secret API_SECRET
                        The API secret
  --context CONTEXT     The CLI context name
  --env ENV             The environment id
  --secrets-file SECRETS_FILE
                        Path to a JSON file with the API key and secret, the --api-key and --api-secret flags take priority
```
