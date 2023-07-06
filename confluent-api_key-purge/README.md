### [confluent keys-purge](purge-keys/confluent-keys_purge.py)
 - Purges all API keys 
   - User prompted to confirm
#### Requirements
  - Python 3 (3.10.9 used for this plugin)  `brew install python3`
  - [Confluent CLI v3.0.0](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent api-key purge [-h] [--resource RESOURCE] [--env ENV] [--sa SA]

Deletes API keys for the current user, specified environment, or service account This plugin assumes confluent CLI v3.0.0 or greater

options:
  -h, --help           show this help message and exit
  --resource RESOURCE  The resource id to filter results by
  --env ENV            The environment id to purge keys from
  --sa SA              The service account id to purge keys from
```
