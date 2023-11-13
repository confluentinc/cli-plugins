### [confluent flink quickstart](confluent-flink-quickstart.py)
- Creates Flink compute pool
    - Displays existing databases (Kafka clusters) if available
    - Prompts user to select one or create one
    - If no database is found in the region, it will create one
    - If the plugin creates a new Kafka cluster, it also enables Schema Registry
- Creates a Flink shell session once the pool is running
- 
#### Requirements
- Python 3 (3.10.9 used for this plugin)  `brew install python3`
- [Confluent CLI v3.0.0](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent flink quickstart [-h] --name NAME [--units NUM-UNITS] [--env ENV] [--region REGION] 

Creates a Flink compute pool.
Look for existing Kafka clusters and prompt the user to select one as the database for the Flink compute pool.
Creating one is an option as well.                                           
If there are no existing Kafka clusters, the plugin will automatically create one.
Then it starts a Flink SQL CLI session

This plugin assumes confluent CLI v3.0.0 or greater

options:
  -h, --help            show this help message and exit
  --name NAME           The name for your Flink compute pool
  --units {5,10}        The number of Confluent Flink Units
  --env ENV             The environment name
  --region {us-east-1,us-east-2,eu-central-1,eu-west-1}
                        Cloud region defaults to us-east-1
  --cloud {aws}         Cloud defaults to aws
  --debug {y,n}         Prints the results of every command, defaults to n
```
