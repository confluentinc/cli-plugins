### [confluent flink quickstart](confluent-flink-quickstart.py)
- Creates Flink compute pool
    - Displays available databases (Kafka clusters)
    - Prompts user to select one or create a new one
    - If no database is found in the region, it will create one automatically
    - If the plugin creates a new Kafka cluster, it also enables Schema Registry
- Starts a Flink shell session once the Flink compute pool is running
- 
#### Requirements
- Python 3 (3.10.9 used for this plugin)  `brew install python3`
- [Confluent CLI v3](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent flink quickstart [-h] --name NAME [--units NUM-UNITS] [--env ENV] [--region REGION] 


This plugin assumes you have installed the latest Confluent CLI v3

options:
  -h, --help            show this help message and exit
  --name NAME           The name for your Flink compute pool 
                        and the environment / Kafka cluster prefix if either is created
  --max-cfu {5,10}      The number of Confluent Flink Units (default: 5)
  --environment-name ENVIRONMENT_NAME
                        Environment name to use, will create it if the environment does not exist
  --kafka-cluster-name KAFKA_CLUSTER_NAME
                        Kafka cluster name to use when creating a new cluster
  --region REGION       The cloud region to use (default: us-east-1)
  --cloud {aws,gcp,azure}
                        The cloud provider to use (default: aws)
  --datagen-quickstarts [DATAGEN_QUICKSTARTS ...]
                        Datagen Source connector quickstarts to launch in Confluent Cloud.
                        Provide a space-separated list to start more than one.
                        E.g., --datagen-quickstarts shoe_orders shoe_customers shoes.
                        See the available quickstarts here:
                        https://docs.confluent.io/cloud/current/connectors/cc-datagen-source.html
  --create-kafka-keys   Create Kafka API keys for the cluster
  --table-api-client-config-file TABLE_API_CLIENT_CONFIG_FILE
                        Path to Table API client config file to create
  --debug               Prints the results of every command
  --no-flink-shell      Turns off the default behaviour of starting a Flink Shell at the end
```
