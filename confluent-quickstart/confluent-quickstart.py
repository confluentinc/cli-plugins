#!/usr/bin/env python3


#  Copyright (c) 2023 Confluent
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


def create_flink_key(environment_name, cloud, region, env_id):
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

def create_schema_registry_key(environment_name):
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

def generate_unified_config(cluster_id=None, kafka_api_key=None, flink_json=None, flink_api_key=None, 
                           sr_api_key=None, env_id=None, args=None, properties_file_path='config.properties'):
    """Generate unified config.properties file with all available connection details"""
    config_filename = properties_file_path
    file_contents_lines = []
    
    # Add Kafka configuration if available
    if cluster_id and kafka_api_key:
        cluster_describe_json = cli(["confluent", "kafka", "cluster", "describe", cluster_id, "-o", "json"])
        bootstrap_servers = cluster_describe_json['endpoint'].replace('SASL_SSL://', '')
        
        file_contents_lines.extend([
            '# Kafka Configuration',
            f'bootstrap.servers={bootstrap_servers}',
            'security.protocol=SASL_SSL',
            'sasl.mechanisms=PLAIN',
            f'sasl.username={kafka_api_key["api_key"]}',
            f'sasl.password={kafka_api_key["api_secret"]}',
            'compression.type=gzip',
            'compression.level=9',
            ''
        ])
    
    # Add Flink configuration if available
    if flink_json and flink_api_key and env_id and args:
        org_describe_json = cli(["confluent", "organization", "describe", "-o", "json"])
        
        file_contents_lines.extend([
            '# Flink Configuration',
            f'client.cloud={args.cloud}',
            f'client.region={args.region}',
            f'client.flink-api-key={flink_api_key["api_key"]}',
            f'client.flink-api-secret={flink_api_key["api_secret"]}',
            f'client.organization-id={org_describe_json["id"]}',
            f'client.environment-id={env_id}',
            f'client.compute-pool-id={flink_json["id"]}',
            f'client.principal-id={flink_api_key["principal_id"]}' if 'principal_id' in flink_api_key else '',
            ''
        ])
    
    # Add Schema Registry configuration if available
    if sr_api_key and env_id:
        # Get Schema Registry endpoint
        sr_describe_json = cli(["confluent", "schema-registry", "cluster", "describe", "-o", "json"])
        
        file_contents_lines.extend([
            '# Schema Registry Configuration',
            f'schema.registry.url={sr_describe_json["endpoint_url"]}',
            'schema.registry.basic.auth.credentials.source=USER_INFO',
            f'schema.registry.basic.auth.user.info={sr_api_key["api_key"]}:{sr_api_key["api_secret"]}',
            ''
        ])
    
    # Add environment information
    if env_id:
        file_contents_lines.extend([
            '# Environment Configuration',
            f'environment.id={env_id}',
            ''
        ])
    
    # Add general connection settings
    if cluster_id or flink_json:
        file_contents_lines.extend([
            '# Connection Settings',
            'request.timeout.ms=20000',
            'retry.backoff.ms=500',
            ''
        ])
    
    # Remove trailing empty line and join
    if file_contents_lines and file_contents_lines[-1] == '':
        file_contents_lines.pop()
    
    file_contents = '\n'.join(file_contents_lines)
    
    # Create directory if it doesn't exist
    config_dir = os.path.dirname(config_filename)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    with open(config_filename, 'w') as file:
        file.write(file_contents)
    
    logging.info(f'Created unified config file {config_filename} containing:\n\n{file_contents}')
    return config_filename


# =============================================================================
# ARGUMENT PARSING
# =============================================================================

usage_message = '''confluent course quickstart [-h] --environment-name ENVIRONMENT_NAME [--kafka-cluster-name KAFKA_CLUSTER_NAME] [--compute-pool-name COMPUTE_POOL_NAME] [--create-kafka-key] [--create-flink-key] [--create-sr-key] [--max-cfu {5,10}] [--region REGION] [--cloud {aws,gcp,azure}] [--properties-file PROPERTIES_FILE] [--debug]'''

parser = argparse.ArgumentParser(description='Create and configure Confluent Cloud resources modularly.\n\n'
                                             'ALWAYS CREATES:\n'
                                             '  • Environment (required parameter)\n'
                                             '  • Unified config.properties file with connection details\n\n'
                                             'CONDITIONALLY CREATES (based on parameters):\n'
                                             '  • Kafka cluster (if --kafka-cluster-name provided)\n'
                                             '  • Flink compute pool (if --compute-pool-name provided)\n'
                                             '  • API keys (if corresponding --create-*-key flags set)\n\n'
                                             'RESOURCE HANDLING:\n'
                                             '  • Checks for existing resources and prompts for confirmation\n'
                                             '  • Validates region/cloud consistency for existing resources\n'
                                             '  • Exits gracefully if user declines to use existing resources\n\n'
                                             'OUTPUT:\n'
                                             '  • Unified configuration file with all service credentials\n\n'
                                             'EXAMPLES:\n'
                                             '  # Environment only:\n'
                                             '  confluent course quickstart --environment-name "confluent_course"\n\n'
                                             '  # Kafka setup:\n'
                                             '  confluent course quickstart --environment-name "confluent_course" --kafka-cluster-name "cluster" --create-kafka-key\n\n'
                                             '  # Full data platform:\n'
                                             '  confluent course quickstart --environment-name "confluent_course" --kafka-cluster-name "cluster" --compute-pool-name "pool" --create-kafka-key --create-flink-key --create-sr-key\n\n'
                                             '  # Custom properties file location:\n'
                                             '  confluent course quickstart --environment-name "confluent_course" --properties-file "./src/main/resources/config.properties"\n\n'
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
                    help='Create Kafka API keys and include in config.properties (requires --kafka-cluster-name)')
parser.add_argument('--create-flink-key', action='store_true', 
                    help='Create Flink API keys and include in config.properties (requires --compute-pool-name)')
parser.add_argument('--create-sr-key', action='store_true', 
                    help='Create Schema Registry API keys and include in config.properties (works independently)')
parser.add_argument('--max-cfu', default='5', choices=['5', '10'], 
                    help='The number of Confluent Flink Units for compute pool (default: %(default)s)')
parser.add_argument('--region', default='us-east-1', 
                    help='The cloud region to use (default: %(default)s)')
parser.add_argument('--cloud', default='aws', choices=['aws', 'gcp', 'azure'],
                    help='The cloud provider to use (default: %(default)s)')
parser.add_argument('--properties-file', default='config.properties', 
                    help='Path and filename for the properties file (default: %(default)s)')
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

# Check if config.properties already exists and apply "check, warn, and confirm" pattern
if os.path.exists(args.properties_file):
    logging.warning(f'Config file {args.properties_file} already exists')
    choice = input(f"Do you want to overwrite the existing {args.properties_file} file? (y/n): ").strip().lower()
    if choice not in ['y', 'yes']:
        logging.info("Exiting without making changes.")
        exit(0)
    logging.info(f'Will overwrite existing {args.properties_file} file')

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
        flink_api_key = create_flink_key(environment_name, args.cloud, args.region, env_id)

# Create Schema Registry API keys if requested
if args.create_sr_key:
    sr_api_key = create_schema_registry_key(environment_name)

# Always generate unified config.properties with available connection details
generate_unified_config(
    cluster_id=cluster_id,
    kafka_api_key=kafka_api_key,
    flink_json=flink_json,
    flink_api_key=flink_api_key,
    sr_api_key=sr_api_key,
    env_id=env_id,
    args=args,
    properties_file_path=args.properties_file
)

logging.info("Quickstart complete. Exiting.")
