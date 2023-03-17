## Plugins for Confluent CLI

This repo contains plugins for use with
the [Confluent CLI](https://docs.confluent.io/confluent-cli/current/overview.html)

### What is a plugin?

Plugins are standalone executable files that begin with `confluent-`, and they can be written in any programming language
that allows you to write terminal commands. Because of this, plugins open the door for both simple and very complex
scripting of CLI workflows.

### Installing a plugin

Installing a plugin is very simple, as it entails just moving its executable to anywhere on your PATH.
There is no plugin installation or preloading required. Plugin executables receive the inherited environment from
confluent.

### Naming a plugin

Plugins determine the command path that they will implement based on their filenames. Subcommands in a plugin's command
path are separated by dashes (-) in its filename. For example, the plugin that is run when the user invokes the command
`confluent this command` would have the filename `confluent-this-command` (excluding a possible file extension).

#### Flags and argument handling

If the user invokes a plugin and passes in additional arguments and/or flags, it is the plugin’s responsibility to
validate and parse them, as the CLI will just pass them in as is. For example, when running `confluent this command arg1
--flag=val arg2`, the CLI will first attempt to find the plugin with the longest possible name, in this case
confluent-this-command-arg1. If this plugin is not found, the CLI will treat the last dash-separated value as an
argument and try to find the next longest possible name until either a plugin is found or there are no more
dash-separated values besides `confluent-`, meaning that no plugins matching the command name have been found. Since
confluent-this-command exists, the CLI runs this plugin and passes all arguments and flags after the plugin’s name (`arg1
--flag=val arg2`) as arguments to the plugin process.

## Plugins

### Using the installation command
 
There's a search and install plugin [confluent plugin-search](search/confluent-plugin_search.py) that you can use for listing and installing
the plugins available in this repo. Just place the file in your path then you can use the `confluent plugin-search` command. Note that you'll need to create 
a [GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) for the command to work.

Here's a list of the current plugins you can install for the confluent CLI

### [confluent cloud-kickstart](cloud-kickstart/confluent-cloud_kickstart.py)
  - Creates a cluster with the preferred cloud provider and region
  - Generates API key and secret for cluster access 
  - Enables Schema Registry
  - Sets the new API key as the active one for the cluster
  - Generates API key and secret for Schema Registry access
  - Writes API key and secret for cluster and SR to files, writes client config to file
  - TODO
    - Support creating environment and service account
#### Requirements
  - Python 3 (3.10.9 used for this plugin)  `brew install python3`
  - [Confluent CLI v3.0.0](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent cloud-kickstart [-h] --name NAME [--env ENV] [--cloud {aws,azure,gcp}] [--region REGION] [--geo {apac,eu,us}]
[--client {clojure,cpp,csharp,go,groovy,java,kotlin,ktor,nodejs,python,restapi,ruby,rust,scala,springboot}] [--debug {y,n}] [--dir DIR]

Creates a Kafka cluster with API keys, Schema Registry with API keys and a client config properties file. This plugin assumes confluent CLI v3.0.0 or greater

options:
  -h, --help            show this help message and exit
  --name NAME           The name for your Confluent Kafka Cluster
  --env ENV             The environment name
  --cloud {aws,azure,gcp}
                        Cloud Provider, Defaults to aws
  --region REGION       Cloud region e.g us-west-2 (aws), westus (azure), us-west1 (gcp) Defaults to us-west-2
  --geo {apac,eu,us}    Cloud geographical region Defaults to us
  --client {clojure,cpp,csharp,go,groovy,java,kotlin,ktor,nodejs,python,restapi,ruby,rust,scala,springboot}
                        Properties file used by client (default java)
  --debug {y,n}         Prints the results of every command, defaults to n
  --dir DIR             Directory to save credentials and client configs, defaults to download directory
```

### [confluent keys-purge](purge-keys/confluent-keys_purge.py)
 - Purges all API keys 
   - User prompted to confirm
#### Requirements
  - Python 3 (3.10.9 used for this plugin)  `brew install python3`
  - [Confluent CLI v3.0.0](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent keys-purge [-h] [--resource RESOURCE] [--env ENV] [--sa SA]

Deletes API keys for the current user, specified environment, or service account This plugin assumes confluent CLI v3.0.0 or greater

options:
  -h, --help           show this help message and exit
  --resource RESOURCE  The resource id to filter results by
  --env ENV            The environment id to purge keys from
  --sa SA              The service account id to purge keys from
```

### [confluent schema-purge](purge-schemas/confluent-schema_purge.py)
 - Deletes all schemas (all versions) - only a soft delete for now
 - NOTE: This command will fail if you have schemas references - - you still need to delete those manually first
#### Requirements
- Python 3 (3.10.9 used for this plugin)  `brew install python3`
- [Confluent CLI v3.0.0](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent schema-purge [-h] [--subject-prefix SUBJECT_PREFIX] [--api-key API_KEY] [--api-secret API_SECRET] [--context CONTEXT] [--env ENV] [--secrets-file SECRETS_FILE]

Deletes schemasThis plugin assumes confluent CLI v3.0.0 or greater

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