## Plugins for Confluent CLI

This repo contains plugins for use with
the [Confluent CLI](https://docs.confluent.io/confluent-cli/current/overview.html). For more information on what a plugin is you can consult the [CLI Plugin documentation](https://docs.confluent.io/confluent-cli/current/plugins.html)


## Plugins

### Using the installation command
 
There's a search and install command in the [Confluent CLI](https://docs.confluent.io/confluent-cli/current/install.html)  that you can use for listing and installing the plugins available in this repo.

Here's a list of the current plugins you can install for the confluent CLI:

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

