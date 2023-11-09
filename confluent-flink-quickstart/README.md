### [confluent flink quickstart](confluent-flink-quickstart.py)
- Creates Flink compute pool
    - Selects first existing database (cluster) if available    
    - If no database is found in the region, it will create one
    - Also enables Schema Registry for the new cluster 
- Creates a Flink shell session once the pool is running
- TODO
    - Display all available databases (Kafka cluster) and allow users to interactively pick vs. first one
#### Requirements
- Python 3 (3.10.9 used for this plugin)  `brew install python3`
- [Confluent CLI v3.0.0](https://docs.confluent.io/confluent-cli/current/install.html)
#### Usage
```text
usage: confluent flink quickstart [-h] --name NAME [--units NUM-UNITS] [--env ENV] [--region REGION] 

Creates Flink compute pool Associates a Kafka cluster for it creating one if none found then starts a Flink SQL cli session This plugin assumes confluent CLI v3.0.0 or greater

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
