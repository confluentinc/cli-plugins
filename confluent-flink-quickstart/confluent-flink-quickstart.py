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
import pathlib
import tempfile
import time


class Cluster:
    def __init__(self, cid, name, _topics):
        self.cid = cid
        self.name = name
        self.topics = _topics


def cli(cmd_args, capture_output=True, fmt_json=True):
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


def create_cluster_with_schema_registry(name, region, cloud):
    logging.debug("Creating the database (Kafka cluster)")
    cluster_json = cli(["confluent", "kafka", "cluster", "create", name,
                        "-o", "json", "--cloud", cloud, "--region", region])
    created_cluster_id = cluster_json['id']
    logging.debug(f"Kafka cluster created {cluster_json}")

    return created_cluster_id


def associate_topics_with_clusters(_candidate_clusters):
    cluster_with_topics = {}
    for cluster in _candidate_clusters:
        _cluster_id = cluster['id']
        topics_json = cli(["confluent", "kafka", "topic", "list", "--cluster", _cluster_id, '-o', 'json'])
        topics = []
        for topic in topics_json:
            topics.append(topic['name'])
        cluster_with_topics[_cluster_id] = (Cluster(_cluster_id, cluster['name'], topics))
        logging.debug(f'Found topics {topics} for cluster {_cluster_id}')
    return cluster_with_topics


def prompt_user_to_pick_cluster_id(cluster_with_topics, name, region, cloud):
    while True:
        choice = input("Enter a Kafka cluster ID to use or 'create' to use a new one for Flink > ")
        if choice:
            if choice.lower() == 'create':
                _cluster_id = create_cluster_with_schema_registry(name, region, cloud)
                break
            if choice in cluster_with_topics:
                _cluster_id = choice
                break

        logging.info(f'{choice} is not valid')
    return _cluster_id


def get_cluster_id_for_flink_pool(_candidate_clusters, name, region, cloud):
    if not _candidate_clusters:
        _cluster_id = create_cluster_with_schema_registry(name, region, cloud)
    else:
        logging.debug(f'Using databases {_candidate_clusters}')
        cluster_with_topics = associate_topics_with_clusters(_candidate_clusters)

        logging.info("Found the following databases with tables")
        logging.info(table_format.format("CLUSTER ID", "CLUSTER NAME", "TOPICS"))
        for cluster in cluster_with_topics.values():
            logging.info(table_format.format(cluster.cid, cluster.name, str(cluster.topics)))

        _cluster_id = prompt_user_to_pick_cluster_id(cluster_with_topics, name, region, cloud)

    return _cluster_id


def process_cluster_list(existing_clusters, curr_flink_region):
    if not existing_clusters:
        logging.info(f'No existing database found, will create one in {curr_flink_region}')
    else:
        clusters = []
        for existing_cluster in existing_clusters:
            if existing_cluster['region'] == curr_flink_region:
                kafka_cluster = existing_cluster['name']
                clusters.append(existing_cluster)
                logging.debug(f'Found a Kafka cluster, {kafka_cluster} with region {curr_flink_region}')

        if not clusters:
            logging.debug(f'No existing database found in region {curr_flink_region}, will create one')
        return clusters


def wait_for_flink_compute_pool(initial_status, compute_pool_id, flink_plugin_start_time):
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


def create_datagen_connectors():
    logging.info(f'Creating API key for Datagen Source connector quickstart(s) {datagen_quickstarts}')
    api_key = cli(["confluent", "api-key", "create", "--resource", cluster_id,
                   "-o", "json"])
    connect_cluster_ids = []
    for datagen_quickstart in datagen_quickstarts:
        with tempfile.NamedTemporaryFile(mode='w+t') as temp_file_object:
            connector_config = f'''{{
                    "name" : "{'datagen-' + datagen_quickstart}",
                    "connector.class": "DatagenSource",
                    "kafka.auth.mode": "KAFKA_API_KEY",
                    "kafka.api.key": "{api_key['api_key']}",
                    "kafka.api.secret" : "{api_key['api_secret']}",
                    "kafka.topic" : "{datagen_quickstart}",
                    "output.data.format" : "AVRO",
                    "quickstart" : "{datagen_quickstart}",
                    "tasks.max" : "1"
                }}'''
            temp_file_object.write(connector_config)
            temp_file_object.flush()
            connector_json = cli(["confluent", "connect", "cluster", "create", "--config-file", temp_file_object.name,
                                  "-o", "json"])
            logging.debug(f'Created connector {connector_json}')
            connect_cluster_ids.append(connector_json['id'])

    wait_for_datagen_connectors(connect_cluster_ids)


def wait_for_datagen_connectors(connect_cluster_ids):
    logging.info("Waiting for the Datagen connector status(es) to be RUNNING. Checking every 10 seconds")
    while True:
        found_unprovisioned_connector = False
        for connect_cluster_id in connect_cluster_ids:
            describe_result = cli(["confluent", "connect", "cluster", "describe", connect_cluster_id,
                                   "-o", "json"])
            status = describe_result['connector']['status']
            if status != 'RUNNING':
                found_unprovisioned_connector = True

                if status == 'FAILED':
                    logging.debug("Datagen connector failed to provision. Attempting to resume the connector "
                                  "as this can happen due to delays in Schema Registry API key propagation.")
                    cli(["confluent", "connect", "cluster", "resume", connect_cluster_id], capture_output=False)

        if not found_unprovisioned_connector:
            logging.info('Connector(s) provisioned')
            break

        provision_wait_time = datetime.datetime.now() - flink_plugin_start_time
        if provision_wait_time.total_seconds() > max_wait_seconds:
            logging.error((f'Time waiting for connector provisioning exceeded {max_wait_seconds / 60} '
                           f'minutes, exiting now. Contact Confluent Cloud help for troubleshooting'))
            exit(1)

        time.sleep(10)


def resolve_environment(environment_name):
    env_id = None
    all_env_json = cli(["confluent", "environment", "list", "-o", "json"])
    for env_json in all_env_json:
        if environment_name == env_json['name']:
            # environment names are unique so it's safe to short circuit
            env_id = env_json['id']
            break
    if not env_id:
        logging.info(f'Creating new environment {environment_name}')
        new_env_json = cli(["confluent", "environment", "create", environment_name,
                            "--governance-package", "essentials", "-o", "json"])
        env_id = new_env_json['id']

    logging.info(f'Setting the active environment to {environment_name} ({env_id})')
    cli(["confluent", "environment", "use", env_id], capture_output=False)
    return env_id


def validate_region(cloud, region):
    all_regions = cli(["confluent", "flink", "region", "list", "-o", "json"])
    region_strings = [region['region'].lower() for region in all_regions if region['cloud'].lower() == cloud.lower()]
    if region not in region_strings:
        logging.error(f"Invalid region for cloud provider {cloud}. Valid regions are: {', '.join(region_strings)}")
        exit(1)


def generate_table_api_client_config(client_config_file, cloud, region, env_id, compute_pool_id):
    flink_api_key_json = cli(["confluent", "api-key", "create", "--resource", "flink",
                      "--cloud", cloud, "--region", region,
                      "--environment", env_id, "-o", "json"])
    org_describe_json = cli(["confluent", "organization", "describe", "-o", "json"])
    flink_api_key_describe_json = cli(["confluent", "api-key", "describe", flink_api_key_json['api_key'], "-o", "json"])
    config_path = pathlib.Path(client_config_file)
    config_path.parent.mkdir(exist_ok=True, parents=True)
    file_contents = (
        f'client.cloud={cloud}\n'
        f'client.region={region}\n'
        f"client.flink-api-key={flink_api_key_json['api_key']}\n"
        f"client.flink-api-secret={flink_api_key_json['api_secret']}\n"
        f"client.organization-id={org_describe_json['id']}\n"
        f'client.environment-id={env_id}\n'
        f"client.compute-pool-id={compute_pool_id}\n"
        f"client.princixpal-id={flink_api_key_describe_json[0]['owner']}"
    )
    with open(client_config_file, 'w') as file:
        file.write(file_contents)
    logging.info(f'Created Table API client config file {client_config_file} containing:\n\n{file_contents}')

usage_message = '''confluent flink quickstart [-h] --name NAME [--max-cfu NUM-UNITS] 
[--environment-name Environment NAME] [--region REGION] [--cloud CLOUD]'''

parser = argparse.ArgumentParser(description='Create a Flink compute pool.\n'
                                             'Looks for existing Kafka clusters '
                                             'and prompts the user to select one as a database for the Flink pool. \n'
                                             'If there are no existing clusters, the plugin will create one.\n'
                                             'Creates zero or more datagen source connectors to seed the database.\n'
                                             'Then it either generates a Table API client config file or starts a Flink SQL shell.\n'
                                             'This plugin assumes confluent CLI v4.0.0 or greater.',
                                 usage=usage_message)
parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

parser.add_argument('--name', required=True, help='The name for your Flink compute pool '
                                                  'and the environment / Kafka cluster prefix if either is created')
parser.add_argument('--max-cfu', default='5', choices=['5', '10'], help='The number of Confluent Flink Units')
parser.add_argument('--environment-name', help='Environment name to use, will create it if the environment does not exist')
parser.add_argument('--kafka-cluster-name', help='Kafka cluster name to use when creating a new cluster.')
parser.add_argument('--region', default='us-east-1', help='The cloud region to use')
parser.add_argument('--cloud', default='aws', choices=['aws', 'gcp', 'azure'],
                    help='The cloud provider to use')
parser.add_argument('--datagen-quickstarts',
                    nargs='*',
                    help='Datagen Source connector quickstarts to launch in Confluent Cloud. Provide a space-separated'
                         'list to start more than one.  E.g., --datagen-quickstarts shoe_orders shoe_customers shoes. '
                         'See the available quickstarts here: '
                         'https://docs.confluent.io/cloud/current/connectors/cc-datagen-source.html')
parser.add_argument('--table-api-client-config-file', help='Path to Table API client config file to create')
parser.add_argument("--debug", action='store_true',
                    help="Prints the results of every command")

args = parser.parse_args()
debug = args.debug
flink_region = args.region
environment_name = args.environment_name if args.environment_name else args.name + '_environment'
datagen_quickstarts = args.datagen_quickstarts

logging.basicConfig(format='%(message)s', level=logging.DEBUG if args.debug else logging.INFO)

if args.table_api_client_config_file is not None and os.path.exists(args.table_api_client_config_file):
    logging.error(f'Table API config file {args.table_api_client_config_file} already exists')
    exit(1)

table_format = "{:<45} {:<45} {:<45}"
flink_plugin_start_time = datetime.datetime.now()
max_wait_seconds = 600

validate_region(args.cloud, flink_region)
env_id = resolve_environment(environment_name)

logging.info("Searching for existing databases (Kafka clusters)")
cluster_list = cli(["confluent", "kafka", "cluster", "list", "-o", "json"])

candidate_clusters = process_cluster_list(cluster_list, flink_region)
cluster_name = args.kafka_cluster_name if args.kafka_cluster_name else args.name + '_kafka-cluster'
cluster_id = get_cluster_id_for_flink_pool(candidate_clusters, cluster_name, args.region, args.cloud)

logging.debug(f'Setting the active Kafka cluster to {cluster_id}')
cli(["confluent", "kafka", "cluster", "use", cluster_id], capture_output=False)

pool_name = args.name
logging.info("Creating the Flink pool")
flink_json = cli(["confluent", "flink", "compute-pool", "create", pool_name,
                  "--cloud", args.cloud, "--region", args.region,
                  "--max-cfu", args.max_cfu, "-o", "json"])
logging.debug(f'Created Flink pool {flink_json}')

# Launch connector(s) before waiting for the Flink compute pool so that we spin up all resources as early as possible
if datagen_quickstarts is not None:
    create_datagen_connectors()

wait_for_flink_compute_pool(flink_json['status'], flink_json['id'], flink_plugin_start_time)

if args.table_api_client_config_file is not None:
    generate_table_api_client_config(args.table_api_client_config_file,
                                     args.cloud, flink_region, env_id, flink_json['id'])
else:
    logging.info("Starting interactive Flink shell now")
    cli(["confluent", "flink", "shell", "--compute-pool", flink_json['id'],
         "--database", cluster_id], capture_output=False)
