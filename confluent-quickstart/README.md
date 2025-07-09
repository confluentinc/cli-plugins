### [confluent quickstart](confluent-quickstart.py)
- Modularly creates and configures Confluent Cloud resources:
    - Environment (always created)
    - Kafka cluster (optional)
    - Flink compute pool (optional)
    - API keys for Kafka, Flink, and Schema Registry (optional)
    - Generates separate configuration files for Kafka and Flink
      - Separate Java and librdkafka Kafka client configs since basic auth credentials are specified differently
- Checks for existing resources and prompts for confirmation
- Validates region/cloud consistency for existing resources
- Exits gracefully if user declines to use existing resources

#### Requirements
- Python 3  
- [Confluent CLI v4.0.0+](https://docs.confluent.io/confluent-cli/current/install.html)

#### Usage
```text
usage: confluent quickstart [-h] --environment-name ENVIRONMENT_NAME [--kafka-cluster-name KAFKA_CLUSTER_NAME] [--compute-pool-name COMPUTE_POOL_NAME] [--create-kafka-key] [--create-flink-key] [--create-sr-key] [--max-cfu {5,10}] [--region REGION] [--cloud {aws,gcp,azure}] [--kafka-java-properties-file KAFKA_JAVA_PROPERTIES_FILE] [--kafka-librdkafka-properties-file KAFKA_LIBRDKAFKA_PROPERTIES_FILE] [--flink-properties-file FLINK_PROPERTIES_FILE] [--debug]

This plugin assumes you have installed the latest Confluent CLI v4.0.0 or greater.

options:
  -h, --help            show this help message and exit
  --environment-name ENVIRONMENT_NAME
                        Name of the Confluent Cloud environment to create or use
  --kafka-cluster-name KAFKA_CLUSTER_NAME
                        Name of the Kafka cluster to create or use (optional - if not specified, no Kafka cluster created)
  --compute-pool-name COMPUTE_POOL_NAME
                        Name of the Flink compute pool to create or use (optional - if not specified, no compute pool created)
  --create-kafka-key    Create Kafka API keys and include in Kafka properties file(s) (requires --kafka-cluster-name and one or both of --kafka-java-properties-file / --kafka-librdkafka-properties-file)
  --create-flink-key    Create Flink API keys and include in flink.properties (requires --compute-pool-name and --flink-properties-file)
  --create-sr-key       Create Schema Registry API keys and include in Kafka properties file(s) (requires one or both of --kafka-java-properties-file / --kafka-librdkafka-properties-file)
  --max-cfu {5,10}      The number of Confluent Flink Units for compute pool (default: 5)
  --region REGION       The cloud region to use (default: us-east-1)
  --cloud {aws,gcp,azure}
                        The cloud provider to use (default: aws)
  --kafka-java-properties-file KAFKA_JAVA_PROPERTIES_FILE
                        Path and filename for the Kafka Java client (and Kafka Streams) properties file (default: kafka-java.properties)
  --kafka-librdkafka-properties-file KAFKA_LIBRDKAFKA_PROPERTIES_FILE
                        Path and filename for the Kafka librdkafka-based client properties file (default: kafka-librdkafka.properties)
  --flink-properties-file FLINK_PROPERTIES_FILE
                        Path and filename for the Flink properties file (default: flink.properties)
  --debug               Enable debug logging with detailed command output
```

##### Examples
- **Environment only:**
  ```
  confluent quickstart --environment-name "my_environment"
  ```
- **Kafka setup (Java client config only):**
  ```
  confluent quickstart --environment-name "my_environment" --kafka-cluster-name "my_cluster" --create-kafka-key --kafka-java-properties-file
  ```
- **Full data platform (generates both Java and librdkafka Kafka client configs):**
  ```
  confluent quickstart --environment-name "my_environment" --kafka-cluster-name "my_cluster" --compute-pool-name "pool" --create-kafka-key --create-flink-key --create-sr-key --kafka-java-properties-file --kafka-librdkafka-properties-file --flink-properties-file
  ```
- **Custom properties file locations:**
  ```
  confluent quickstart --environment-name "my_environment" --kafka-java-properties-file "./config/kafka.properties" --flink-properties-file "./config/flink.properties"
  ``` 