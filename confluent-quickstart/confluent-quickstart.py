#!/usr/bin/env python3


#  Copyright (c) 2025 Confluent
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import argparse
import datetime
import subprocess
import json
import logging
import os
import time


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Cluster:
    def __init__(self, cid, name, _topics):
        self.cid = cid
        self.name = name
        self.topics = _topics


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def cli(cmd_args, capture_output=True, fmt_json=True):
    """Execute Confluent CLI commands and handle responses"""
    logging.debug(f"CMD args {cmd_args}")
    results = subprocess.run(cmd_args, capture_output=capture_output)
    if results.returncode != 0:
        logging.error(str(results.stderr, 'UTF-8'))
        exit(results.returncode)
    if capture_output:
        if fmt_json:
            final_result = json.loads(results.stdout)
        else:
            final_result = str(results.stdout, 'UTF-8')

        logging.debug("Debug: %s" % final_result)

        return final_result


def validate_region(cloud, region):
    """Validate that the specified region is available for the cloud provider"""
    all_regions = cli(["confluent", "flink", "region", "list", "-o", "json"])
    region_strings = [region['region'].lower() for region in all_regions if region['cloud'].lower() == cloud.lower()]
    if region not in region_strings:
        logging.error(f"Invalid region for cloud provider {cloud}. Valid regions are: {', '.join(region_strings)}")
        exit(1)


# =============================================================================
# ENVIRONMENT FUNCTIONS
# =============================================================================

def get_or_create_environment(environment_name):
    """Get existing environment or create a new one"""
    env_id = None
    all_env_json = cli(["confluent", "environment", "list", "-o", "json"])
    for env_json in all_env_json:
        if environment_name == env_json['name']:
            env_id = env_json['id']
            break
    
    if env_id:
        logging.warning(f'Environment "{environment_name}" already exists (ID: {env_id})')
        choice = input(f"Do you want to use the existing environment '{environment_name}'? (y/n): ").strip().lower()
        if choice not in ['y', 'yes']:
            logging.info("Exiting without making changes.")
            exit(0)
        logging.info(f'Using existing environment {environment_name} ({env_id})')
    else:
        logging.info(f'Creating new environment {environment_name}')
        new_env_json = cli(["confluent", "environment", "create", environment_name,
                            "--governance-package", "essentials", "-o", "json"])
        env_id = new_env_json['id']
        logging.info(f'Created environment {environment_name} ({env_id})')

    cli(["confluent", "environment", "use", env_id], capture_output=False)
    return env_id


# =============================================================================
# KAFKA FUNCTIONS
# =============================================================================

def get_or_create_kafka_cluster(cluster_name, region, cloud):
    """Get existing Kafka cluster or create a new one"""
    # List all clusters and check if our target cluster exists
    try:
        cluster_list = cli(["confluent", "kafka", "cluster", "list", "-o", "json"])
    except Exception as e:
        logging.error(f"Failed to list Kafka clusters: {e}")
        exit(1)
    
    existing_cluster = None
    for cluster in cluster_list:
        if cluster['name'] == cluster_name:
            existing_cluster = cluster
            break
    
    if existing_cluster:
        # Validate region consistency
        if existing_cluster['region'] != region:
            logging.error(f'Existing cluster "{cluster_name}" is in region {existing_cluster["region"]}, but you specified {region}')
            logging.error('Please either use a different cluster name or specify the correct region')
            exit(1)
        
        # Validate cloud consistency if available
        if 'cloud' in existing_cluster and existing_cluster['cloud'].lower() != cloud.lower():
            logging.error(f'Existing cluster "{cluster_name}" is on {existing_cluster["cloud"]}, but you specified {cloud}')
            logging.error('Please either use a different cluster name or specify the correct cloud provider')
            exit(1)
        
        logging.warning(f'Kafka cluster "{cluster_name}" already exists (ID: {existing_cluster["id"]})')
        choice = input(f"Do you want to use the existing Kafka cluster '{cluster_name}'? (y/n): ").strip().lower()
        if choice not in ['y', 'yes']:
            logging.info("Exiting without making changes.")
            exit(0)
        logging.info(f'Using existing Kafka cluster {cluster_name} ({existing_cluster["id"]})')
        return existing_cluster['id']
    else:
        logging.info(f'Creating new Kafka cluster {cluster_name}')
        try:
            cluster_json = cli(["confluent", "kafka", "cluster", "create", cluster_name,
                                "-o", "json", "--cloud", cloud, "--region", region])
            cluster_id = cluster_json['id']
            logging.info(f'Created Kafka cluster {cluster_name} ({cluster_id})')
            return cluster_id
        except Exception as e:
            logging.error(f"Failed to create Kafka cluster: {e}")
            exit(1)


def create_kafka_key(cluster_id):
    """Create API key for Kafka cluster"""
    logging.info(f'Creating API key for Kafka cluster {cluster_id}')
    api_key = cli(["confluent", "api-key", "create", "--resource", cluster_id,
                   "-o", "json"])
    logging.debug(f'Created Kafka API key {api_key}')
    logging.info(f'Created Kafka API key (will be saved to unified config file)')
    return api_key


# =============================================================================
# FLINK FUNCTIONS
# =============================================================================

def get_or_create_flink_compute_pool(compute_pool_name, cloud, region, max_cfu):
    """Get existing Flink compute pool or create a new one"""
    logging.info(f"Checking for existing Flink compute pool {compute_pool_name}")
    flink_compute_pool_json = cli(["confluent", "flink", "compute-pool", "list", "-o", "json"])
    
    existing_pool = None
    for flink_compute_pool in flink_compute_pool_json:
        if flink_compute_pool['name'] == compute_pool_name:
            existing_pool = cli(["confluent", "flink", "compute-pool", "describe", flink_compute_pool['id'],
                              "-o", "json"])
            break
    
    if existing_pool:
        logging.warning(f'Flink compute pool "{compute_pool_name}" already exists (ID: {existing_pool["id"]})')
        choice = input(f"Do you want to use the existing Flink compute pool '{compute_pool_name}'? (y/n): ").strip().lower()
        if choice not in ['y', 'yes']:
            logging.info("Exiting without making changes.")
            exit(0)
        logging.info(f'Using existing Flink compute pool {compute_pool_name} ({existing_pool["id"]})')
        return existing_pool
    else:
        logging.info(f"Creating Flink pool {compute_pool_name}")
        flink_json = cli(["confluent", "flink", "compute-pool", "create", compute_pool_name,
                          "--cloud", cloud, "--region", region,
                          "--max-cfu", max_cfu, "-o", "json"])
        logging.info(f'Created Flink compute pool {compute_pool_name} ({flink_json["id"]})')
        return flink_json


def wait_for_flink_compute_pool(initial_status, compute_pool_id, flink_plugin_start_time):
    """Wait for Flink compute pool to be provisioned"""
    logging.info("Waiting for the Flink compute pool status to be PROVISIONED. Checking every 10 seconds")
    status = initial_status

    while status != 'PROVISIONED':
        logging.debug("Checking status of Flink compute pool")
        provision_wait_time = datetime.datetime.now() - flink_plugin_start_time
        if provision_wait_time.total_seconds() > max_wait_seconds:
            logging.error((f'Time waiting for Flink compute pool provisioning exceeded {max_wait_seconds / 60} '
                           f'minutes, exiting now. Contact Confluent Cloud help for troubleshooting'))
            exit(1)
        time.sleep(10)
        describe_result = cli(["confluent", "flink", "compute-pool",
                               "describe", compute_pool_id, "-o", "json"])
        status = describe_result['status']
    logging.info(f"Flink compute pool {compute_pool_id} is {status}")


def create_flink_key(cloud, region, env_id):
    """Create API key for Flink"""
    logging.info('Creating API key for Flink')
    
    api_key = cli(["confluent", "api-key", "create", "--resource", "flink",
                   "--cloud", cloud, "--region", region,
                   "--environment", env_id, "-o", "json"])
    logging.debug(f'Created Flink API key {api_key}')
    
    # Get additional details about the API key
    api_key_describe = cli(["confluent", "api-key", "describe", api_key['api_key'], "-o", "json"])
    if api_key_describe:
        api_key['principal_id'] = api_key_describe[0].get('owner', '')
    
    logging.info(f'Created Flink API key (will be saved to unified config file)')
    return api_key


# =============================================================================
# SCHEMA REGISTRY FUNCTIONS
# =============================================================================

def create_schema_registry_key():
    """Create API key for Schema Registry"""
    logging.info('Creating API key for Schema Registry')
    
    # Get the Schema Registry cluster details for this environment
    try:
        sr_describe = cli(["confluent", "schema-registry", "cluster", "describe", "-o", "json"])
    except Exception as e:
        logging.error(f"Failed to describe Schema Registry cluster: {e}")
        logging.error("Make sure you have Schema Registry enabled in your environment")
        exit(1)
    
    if not sr_describe or 'cluster' not in sr_describe:
        logging.error('No Schema Registry cluster found in this environment')
        logging.error('Schema Registry must be enabled before creating API keys')
        exit(1)
    
    # Get the Schema Registry cluster ID from the "cluster" field
    sr_cluster_id = sr_describe['cluster']
    
    try:
        api_key = cli(["confluent", "api-key", "create", "--resource", sr_cluster_id,
                       "-o", "json"])
        logging.debug(f'Created Schema Registry API key {api_key}')
    except Exception as e:
        logging.error(f"Failed to create Schema Registry API key: {e}")
        exit(1)
    
    logging.info(f'Created Schema Registry API key (will be saved to unified config file)')
    return api_key


# =============================================================================
# CONFIGURATION FUNCTIONS
# =============================================================================

def generate_kafka_config(cluster_id, kafka_api_key, sr_api_key, env_id, do_generate_java_config, kafka_properties_file):
    """Generate kafka.properties file with Kafka and Schema Registry connection details"""
    content_parts = []
    
    # Environment ID comment
    if env_id:
        content_parts.append(f'# Environment ID: {env_id}')
    
    # Kafka configuration
    if cluster_id:
        cluster_describe_json = cli(["confluent", "kafka", "cluster", "describe", cluster_id, "-o", "json"])
        bootstrap_servers = cluster_describe_json['endpoint'].replace('SASL_SSL://', '')
        
        kafka_config = f"""# Kafka Configuration
bootstrap.servers={bootstrap_servers}
security.protocol=SASL_SSL
sasl.mechanism=PLAIN"""
        
        # Add credentials
        if do_generate_java_config:
            if kafka_api_key:
                kafka_config += f"""
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username='{kafka_api_key["api_key"]}' password='{kafka_api_key["api_secret"]}';"""
            else:
                kafka_config += f"""
# sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username='<your-api-key>' password='<your-api-secret>';"""
        else: # librdkafka-based client config
            if kafka_api_key:
                kafka_config += f"""
sasl.username={kafka_api_key["api_key"]}
sasl.password={kafka_api_key["api_secret"]}"""
            else:
                kafka_config += f"""
# sasl.username=<your-api-key>
# sasl.password=<your-api-secret>"""

        content_parts.append(kafka_config)

    # Schema Registry configuration
    if sr_api_key:
        sr_describe_json = cli(["confluent", "schema-registry", "cluster", "describe", "-o", "json"])
        sr_config = f"""# Schema Registry Configuration
schema.registry.url={sr_describe_json["endpoint_url"]}
basic.auth.credentials.source=USER_INFO
basic.auth.user.info={sr_api_key["api_key"]}:{sr_api_key["api_secret"]}"""
        content_parts.append(sr_config)
    
    # Join all parts with double newlines
    file_contents = '\n\n'.join(content_parts)
    
    # Create directory if it doesn't exist
    config_dir = os.path.dirname(kafka_properties_file)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    with open(kafka_properties_file, 'w') as file:
        file.write(file_contents)
    
    logging.info(f'Created Kafka config file {kafka_properties_file} containing:\n\n{file_contents}')
    return kafka_properties_file


def generate_flink_config(flink_json, flink_api_key, env_id, args, flink_properties_file):
    """Generate flink.properties file with Flink connection details"""
    content_parts = []
    
    # Environment ID comment
    if env_id:
        content_parts.append(f'# Environment ID: {env_id}')
    
    # Flink configuration
    if flink_json and env_id and args:
        org_describe_json = cli(["confluent", "organization", "describe", "-o", "json"])
        
        flink_config = f"""# Flink Configuration
client.cloud={args.cloud}
client.region={args.region}
client.organization-id={org_describe_json["id"]}
client.environment-id={env_id}
client.compute-pool-id={flink_json["id"]}"""
        
        # Add credentials
        if flink_api_key:
            if 'principal_id' in flink_api_key:
                flink_config += f"""
client.principal-id={flink_api_key["principal_id"]}"""
            else:
                flink_config += f"""
# client.principal-id=<your-principal-id>"""
            flink_config += f"""
client.flink-api-key={flink_api_key["api_key"]}
client.flink-api-secret={flink_api_key["api_secret"]}"""
        else:
            flink_config += f"""
# client.principal-id=<your-principal-id>
# client.flink-api-key=<your-flink-api-key>
# client.flink-api-secret=<your-flink-api-secret>"""
        
        content_parts.append(flink_config)
    
    # Join all parts with double newlines
    file_contents = '\n\n'.join(content_parts)
    
    # Create directory if it doesn't exist
    config_dir = os.path.dirname(flink_properties_file)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    with open(flink_properties_file, 'w') as file:
        file.write(file_contents)
    
    logging.info(f'Created Flink config file {flink_properties_file} containing:\n\n{file_contents}')
    return flink_properties_file


# =============================================================================
# ARGUMENT PARSING
# =============================================================================

usage_message = '''confluent quickstart [-h] --environment-name ENVIRONMENT_NAME [--kafka-cluster-name KAFKA_CLUSTER_NAME] [--compute-pool-name COMPUTE_POOL_NAME] [--create-kafka-key] [--create-flink-key] [--create-sr-key] [--max-cfu {5,10}] [--region REGION] [--cloud {aws,gcp,azure}] [--kafka-java-properties-file KAFKA_JAVA_PROPERTIES_FILE] [--kafka-librdkafka-properties-file KAFKA_LIBRDKAFKA_PROPERTIES_FILE] [--flink-properties-file FLINK_PROPERTIES_FILE] [--debug]'''

parser = argparse.ArgumentParser(description='Create and configure Confluent Cloud resources modularly.\n\n'
                                             'ALWAYS CREATES:\n'
                                             '  • Environment (required parameter)\n\n'
                                             'CONDITIONALLY CREATES (based on parameters):\n'
                                             '  • Kafka cluster (if --kafka-cluster-name provided)\n'
                                             '  • Flink compute pool (if --compute-pool-name provided)\n'
                                             '  • API keys (if corresponding --create-*-key flags set, which would also require corresponding config file arguments)\n'
                                             '  • kafka-java.properties file for Java / Kafka Streams clients (if --kafka-java-properties-file provided)\n'
                                             '  • kafka-librdkafka.properties file for librdkafka clients (if --kafka-librdkafka-properties-file provided)\n'
                                             '  • flink.properties file (if --flink-properties-file provided)\n\n'
                                             'RESOURCE HANDLING:\n'
                                             '  • Checks for existing resources and prompts for confirmation\n'
                                             '  • Validates region/cloud consistency for existing resources\n'
                                             '  • Exits gracefully if user declines to use existing resources\n\n'
                                             'OUTPUT:\n'
                                             '  • Separate configuration files for each service with credentials\n\n'
                                             'EXAMPLES:\n'
                                             '  # Environment only:\n'
                                             '  confluent quickstart --environment-name "my_environment"\n\n'
                                             '  # Kafka setup (Java client config only):\n'
                                             '  confluent quickstart --environment-name "my_environment" --kafka-cluster-name "my_cluster" --create-kafka-key --kafka-java-properties-file\n\n'
                                             '  # Full data platform (generates both Java and librdkafka Kafka client configs):\n'
                                             '  confluent quickstart --environment-name "my_environment" --kafka-cluster-name "my_cluster" --compute-pool-name "pool" --create-kafka-key --create-flink-key --create-sr-key --kafka-java-properties-file --kafka-librdkafka-properties-file --flink-properties-file\n\n'
                                             '  # Custom properties file locations:\n'
                                             '  confluent quickstart --environment-name "my_environment" --kafka-java-properties-file "./config/kafka.properties" --flink-properties-file "./config/flink.properties"\n\n'
                                             'Requires confluent CLI v4.0.0 or greater.',
                                 usage=usage_message,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('--environment-name', required=True, 
                    help='Name of the Confluent Cloud environment to create or use')
parser.add_argument('--kafka-cluster-name', 
                    help='Name of the Kafka cluster to create or use (optional - if not specified, no Kafka cluster created)')
parser.add_argument('--compute-pool-name', 
                    help='Name of the Flink compute pool to create or use (optional - if not specified, no compute pool created)')
parser.add_argument('--create-kafka-key', action='store_true', 
                    help='Create Kafka API keys and include in Kafka properties file(s) (requires --kafka-cluster-name and one or both of --kafka-java-properties-file / --kafka-librdkafka-properties-file)')
parser.add_argument('--create-flink-key', action='store_true', 
                    help='Create Flink API keys and include in flink.properties (requires --compute-pool-name and --flink-properties-file)')
parser.add_argument('--create-sr-key', action='store_true', 
                    help='Create Schema Registry API keys and include in Kafka properties file(s) (works independently)')
parser.add_argument('--max-cfu', default='5', choices=['5', '10'], 
                    help='The number of Confluent Flink Units for compute pool (default: %(default)s)')
parser.add_argument('--region', default='us-east-1', 
                    help='The cloud region to use (default: %(default)s)')
parser.add_argument('--cloud', default='aws', choices=['aws', 'gcp', 'azure'],
                    help='The cloud provider to use (default: %(default)s)')
parser.add_argument('--kafka-java-properties-file', nargs='?', const='kafka-java.properties', default=None,
                    help='Path and filename for the Kafka Java client (and Kafka Streams) properties file (default: %(const)s)')
parser.add_argument('--kafka-librdkafka-properties-file', nargs='?', const='kafka-librdkafka.properties', default=None,
                    help='Path and filename for the Kafka librdkafka-based client properties file (default: %(const)s)')
parser.add_argument('--flink-properties-file', nargs='?', const='flink.properties', default=None,
                    help='Path and filename for the Flink properties file (default: %(const)s)')
parser.add_argument("--debug", action='store_true',
                    help="Enable debug logging with detailed command output")

args = parser.parse_args()

# =============================================================================
# MAIN LOGIC
# =============================================================================

# Comprehensive validation logic
if args.create_kafka_key and not args.kafka_cluster_name:
    parser.error("--create-kafka-key requires --kafka-cluster-name to be specified")

if args.create_flink_key and not args.compute_pool_name:
    parser.error("--create-flink-key requires --compute-pool-name to be specified")

if args.create_kafka_key and not args.kafka_java_properties_file and not args.kafka_librdkafka_properties_file:
    parser.error("--create-kafka-key requires --kafka-java-properties-file and/or --kafka-librdkafka-properties-file to be specified")

if args.create_flink_key and not args.flink_properties_file:
    parser.error("--create-flink-key requires --flink-properties-file to be specified")

# Validate that at least one resource is being created
if not args.kafka_cluster_name and not args.compute_pool_name and not args.create_sr_key:
    logging.warning("Only environment will be created. Consider adding --kafka-cluster-name, --compute-pool-name, or --create-sr-key for a more complete setup.")

# Validate max-cfu is only relevant if creating compute pool
if args.max_cfu != '5' and not args.compute_pool_name:
    logging.warning("--max-cfu specified but --compute-pool-name not provided. CFU setting will be ignored.")

debug = args.debug
flink_region = args.region
environment_name = args.environment_name
kafka_cluster_name = args.kafka_cluster_name
compute_pool_name = args.compute_pool_name

logging.basicConfig(format='%(message)s', level=logging.DEBUG if args.debug else logging.INFO)

config_files = [args.kafka_java_properties_file, args.kafka_librdkafka_properties_file, args.flink_properties_file]

# Validate config files are unique. Use os.path.realpath to compare canonical paths (e.g., 'foo' and './foo' will be
# considered duplicates)
canonical_config_file_paths = [os.path.realpath(f) for f in config_files if f is not None]
for canonical_config_file_path in canonical_config_file_paths:
    if canonical_config_file_paths.count(canonical_config_file_path) > 1:
        logging.error(f"Config file {canonical_config_file_path} specified multiple times. Exiting without making changes.")
        exit(1)

# Check if config files already exist and apply "check, warn, and confirm" pattern
existing_files = []
for config_file in config_files:
    if config_file and os.path.exists(config_file):
        existing_files.append(config_file)

if existing_files:
    files_str = ', '.join(existing_files)
    logging.warning(f'Config file(s) {files_str} already exist')
    choice = input(f"Do you want to overwrite the existing config file(s)? (y/n): ").strip().lower()
    if choice not in ['y', 'yes']:
        logging.info("Exiting without making changes.")
        exit(0)
    logging.info(f'Will overwrite existing config file(s): {files_str}')

flink_plugin_start_time = datetime.datetime.now()
max_wait_seconds = 600

validate_region(args.cloud, flink_region)

# Always create environment (required parameter)
env_id = get_or_create_environment(environment_name)

# Initialize variables for optional resources
cluster_id = None
kafka_api_key = None
flink_json = None
flink_api_key = None
sr_api_key = None

# Conditionally create Kafka cluster if name is provided
if kafka_cluster_name:
    cluster_id = get_or_create_kafka_cluster(kafka_cluster_name, args.region, args.cloud)
    logging.debug(f'Setting the active Kafka cluster to {cluster_id}')
    cli(["confluent", "kafka", "cluster", "use", cluster_id], capture_output=False)
    
    # Create Kafka API keys if requested
    if args.create_kafka_key:
        kafka_api_key = create_kafka_key(cluster_id)

# Conditionally create Flink compute pool if name is provided
if compute_pool_name:
    flink_json = get_or_create_flink_compute_pool(compute_pool_name, args.cloud, args.region, args.max_cfu)
    wait_for_flink_compute_pool(flink_json['status'], flink_json['id'], flink_plugin_start_time)
    
    # Create Flink API keys if requested
    if args.create_flink_key:
        flink_api_key = create_flink_key(args.cloud, args.region, env_id)

# Create Schema Registry API keys if requested
if args.create_sr_key:
    sr_api_key = create_schema_registry_key()

# Generate separate config files based on what was created
created_files = []

# Generate Kafka config if Kafka cluster was created and Java and/or librdkafka-based client config file specified
if cluster_id:
    if args.kafka_java_properties_file:
        generate_kafka_config(cluster_id, kafka_api_key, sr_api_key, env_id, True, args.kafka_java_properties_file)
        created_files.append(args.kafka_java_properties_file)
    if args.kafka_librdkafka_properties_file:
        generate_kafka_config(cluster_id, kafka_api_key, sr_api_key, env_id, False, args.kafka_librdkafka_properties_file)
        created_files.append(args.kafka_librdkafka_properties_file)

# Generate Flink config if Flink compute pool was created and config file specified
if flink_json and args.flink_properties_file:
    generate_flink_config(flink_json, flink_api_key, env_id, args, args.flink_properties_file)
    created_files.append(args.flink_properties_file)

if not created_files:
    logging.info("No config files were created (no resources were created)")

logging.info("Quickstart complete. Exiting.")
