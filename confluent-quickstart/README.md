### [confluent quickstart](confluent-quickstart.py)
- Modularly creates and configures Confluent Cloud resources:
    - Environment (always created)
    - Kafka cluster (optional)
    - Flink compute pool (optional)
    - API keys for Kafka, Flink, and Schema Registry (optional)
    - Generates separate configuration files for Kafka and Flink
- Checks for existing resources and prompts for confirmation
- Validates region/cloud consistency for existing resources
- Exits gracefully if user declines to use existing resources

#### Requirements
- Python 3  
- [Confluent CLI v4.0.0+](https://docs.confluent.io/confluent-cli/current/install.html)

#### Usage
```text
usage: confluent quickstart [-h] --environment-name ENVIRONMENT_NAME [--kafka-cluster-name KAFKA_CLUSTER_NAME] [--compute-pool-name COMPUTE_POOL_NAME] [--create-kafka-key] [--create-flink-key] [--create-sr-key] [--max-cfu {5,10}] [--region REGION] [--cloud {aws,gcp,azure}] [--kafka-properties-file KAFKA_PROPERTIES_FILE] [--flink-properties-file FLINK_PROPERTIES_FILE] [--debug]

This plugin assumes you have installed the latest Confluent CLI v4.0.0 or greater.

options:
  -h, --help            show this help message and exit
  --environment-name ENVIRONMENT_NAME
                        Name of the Confluent Cloud environment to create or use (required)
  --kafka-cluster-name KAFKA_CLUSTER_NAME
                        Name of the Kafka cluster to create or use (optional)
  --compute-pool-name COMPUTE_POOL_NAME
                        Name of the Flink compute pool to create or use (optional)
  --create-kafka-key    Create Kafka API keys and include in kafka.properties (requires --kafka-cluster-name)
  --create-flink-key    Create Flink API keys and include in flink.properties (requires --compute-pool-name)
  --create-sr-key       Create Schema Registry API keys and include in kafka.properties (works independently)
  --max-cfu {5,10}      The number of Confluent Flink Units for compute pool (default: 5)
  --region REGION       The cloud region to use (default: us-east-1)
  --cloud {aws,gcp,azure}
                        The cloud provider to use (default: aws)
  --kafka-properties-file KAFKA_PROPERTIES_FILE
                        Path and filename for the Kafka properties file (default: kafka.properties)
  --flink-properties-file FLINK_PROPERTIES_FILE
                        Path and filename for the Flink properties file (default: flink.properties)
  --debug               Enable debug logging with detailed command output
```

##### Examples
- **Environment only:**
  ```
  confluent quickstart --environment-name "my_environment"
  ```
- **Kafka setup:**
  ```
  confluent quickstart --environment-name "my_environment" --kafka-cluster-name "my_cluster" --create-kafka-key
  ```
- **Full data platform:**
  ```
  confluent quickstart --environment-name "my_environment" --kafka-cluster-name "my_cluster" --compute-pool-name "pool" --create-kafka-key --create-flink-key --create-sr-key
  ```
- **Custom properties file locations:**
  ```
  confluent quickstart --environment-name "my_environment" --kafka-properties-file "./config/kafka.properties" --flink-properties-file "./config/flink.properties"
  ``` 