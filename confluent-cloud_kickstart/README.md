### [confluent cloud-kickstart](confluent-cloud_kickstart.py)
  - Creates a Kafka cluster in the preferred cloud provider and region
  - Generates API key and secret for Kafka cluster access 
  - Sets the new API key as the active one for the cluster
  - Generates API key and secret for Schema Registry access
  - Writes API key and secret for cluster and SR to files, writes client config to file or stdout
  - TODO
    - Support creating environment and service account
#### Requirements
  - Python 3 (3.10.9 used for this plugin)  `brew install python3`
  - [Confluent CLI v4.0.0](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent cloud-kickstart [-h] --name NAME [--env ENV] [--cloud {aws,azure,gcp}] [--region REGION] [--output-format {properties,stdout}]
[--client {clojure,cpp,csharp,go,groovy,java,kotlin,ktor,nodejs,python,restapi,ruby,rust,scala,springboot}] [--debug {y,n}] [--dir DIR]

Creates a Kafka cluster with API keys, Schema Registry with API keys and a client config properties file. This plugin assumes confluent CLI v3.0.0 or greater

options:
  -h, --help            show this help message and exit
  --name NAME           The name for your Confluent Kafka Cluster
  --env ENV             The environment name
  --cloud {aws,azure,gcp}
                        Cloud Provider, Defaults to aws
  --region REGION       Cloud region e.g us-west-2 (aws), westus (azure), us-west1 (gcp) Defaults to us-west-2
  --output {properties,stdout}
                        Whether to write client properties to a properties file or stdout
  --client {clojure,cpp,csharp,go,groovy,java,kotlin,ktor,nodejs,python,restapi,ruby,rust,scala,springboot}
                        Properties file used by client (default java). Only applies if `--output` argument is 
                        `properties`.
  --debug               Prints the results of every command, defaults to n
  --dir DIR             Directory to save credentials and client configs, defaults to download directory. Only applies
                        if `--output` argument is `properties`.
```
