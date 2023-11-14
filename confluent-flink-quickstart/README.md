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
                        and the prefix of a Kafka cluster name if one is created
  --max-cfu {5,10}      The number of Confluent Flink Units
  --environment         The environment id
  --region {us-east-1,us-east-2,eu-central-1,eu-west-1}
                        Cloud region defaults to us-east-1
  --cloud {aws}         Cloud defaults to aws
  --debug               Prints the results of every command, defaults to false
```
