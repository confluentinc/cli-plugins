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
import subprocess
import json
import time


class Cluster:
    def __init__(self, cid, name, _topics):
        self.cid = cid
        self.name = name
        self.topics = _topics


def cli(cmd_args, capture_output=True, fmt_json=True):
    if debug:
        print(f"CMD args {cmd_args}")
    results = subprocess.run(cmd_args, capture_output=capture_output)
    if results.returncode != 0:
        print(str(results.stderr, 'UTF-8'))
        exit(results.returncode)
    if capture_output:
        if fmt_json:
            final_result = json.loads(results.stdout)
        else:
            final_result = str(results.stdout, 'UTF-8')

        if debug:
            print("Debug: %s" % final_result)

        return final_result


def create_cluster_with_schema_registry():
    if debug:
        print("Creating the database (Kafka cluster)")
    cluster_json = cli(["confluent", "kafka", "cluster", "create", args.name + '_kafka-cluster',
                        "-o", "json", "--cloud", args.cloud, "--region", args.region])
    created_cluster_id = cluster_json['id']
    if debug:
        print(f"Kafka cluster created {cluster_json}")
    geo = flink_region[0:2]
    if debug:
        print(f"Enabling Schema Registry in geo {geo}")
    sr_json = cli(["confluent", "schema-registry", "cluster", "enable", "--cloud",
                   cluster_json['provider'], "--geo", geo, "-o", "json"])
    if debug:
        print(f"Schema Registry enabled {sr_json}")
    return created_cluster_id


def get_cluster_id_for_flink_pool(_candidate_clusters):
    if _candidate_clusters:
        cluster_with_topics = {}
        if debug:
            print(f'Using databases {_candidate_clusters}')
        for cluster in _candidate_clusters:
            _cluster_id = cluster['id']
            topics_json = cli(["confluent", "kafka", "topic", "list", "--cluster", _cluster_id, '-o', 'json'])
            topics = []
            for topic in topics_json:
                topics.append(topic['name'])
            cluster_with_topics[_cluster_id] = (Cluster(_cluster_id, cluster['name'], topics))
            if debug:
                print(f'Found topics {topics} for cluster {_cluster_id}')

        print("Found the following databases with tables")
        print(table_format.format("CLUSTER ID", "CLUSTER NAME", "TOPICS"))
        for cluster in cluster_with_topics.values():
            print(table_format.format(cluster.cid, cluster.name, str(cluster.topics)))

        while True:
            choice = input("Enter a Kafka cluster ID to use or 'create' to use a new one for Flink > ")
            if choice:
                if choice.lower() == 'create':
                    _cluster_id = create_cluster_with_schema_registry()
                    break
                if choice in cluster_with_topics:
                    _cluster_id = choice
                    break

            print(f'{choice} is not valid')

    else:
        _cluster_id = create_cluster_with_schema_registry()

    return _cluster_id


def process_cluster_list(existing_clusters, curr_flink_region):
    if not existing_clusters:
        print(f'No existing database found, will create one in {curr_flink_region}')
    else:
        clusters = []
        for existing_cluster in existing_clusters:
            if existing_cluster['region'] == curr_flink_region:
                kafka_cluster = existing_cluster['name']
                clusters.append(existing_cluster)
                if debug:
                    print(f'Found a Kafka cluster, {kafka_cluster} with region {curr_flink_region}')

        if not clusters and debug:
            print(f'No exising database found in region {curr_flink_region}, will create one')
        return clusters


usage_message = '''confluent flink quickstart [-h] --name NAME [--units NUM-UNITS] [--env ENV] [--region REGION] '''

parser = argparse.ArgumentParser(description='Create a Flink compute pool.\n'
                                             'Looks for exising Kafka clusters '
                                             'and prompt the user to select one as a database for the Flink pool. \n'
                                             'Creating one is an option as well.\n'
                                             'If there are no existing clusters, the plugin will create one.\n'
                                             'Then it starts a Flink SQL cli session'
                                             '\nThis plugin assumes confluent CLI v3.0.0 or greater',
                                 usage=usage_message)

parser.add_argument('--name', required=True, help='The name for your Flink compute pool')
parser.add_argument('--units', default='5', choices=['5', '10'], help='The number of Confluent Flink Units')
parser.add_argument('--env', help='The environment name')
parser.add_argument('--region', default='us-east-1', choices=['us-east-1', 'us-east-2', 'eu-central-1', 'eu-west-1'],
                    help='Cloud region defaults to us-east-1')
parser.add_argument('--cloud', default='aws', choices=['aws'],
                    help='Cloud defaults to aws')
parser.add_argument("--debug", choices=['y', 'n'], default='n',
                    help="Prints the results of every command, defaults to n")

args = parser.parse_args()
debug = False if args.debug == 'n' else True
flink_region = args.region

table_format = "{:<30} {:<30} {:<30}"

print("Searching for existing databases (Kafka clusters)")
cluster_list = cli(["confluent", "kafka", "cluster", "list",
                    "-o", "json"])

candidate_clusters = process_cluster_list(cluster_list, flink_region)
cluster_id = get_cluster_id_for_flink_pool(candidate_clusters)

pool_name = args.name + '_flink_pool'
print("Creating the Flink pool")
flink_json = cli(["confluent", "flink", "compute-pool", "create", pool_name,
                  "--cloud", args.cloud, "--region", args.region,
                  "--max-cfu", args.units, "-o", "json"])
if debug:
    print(f'Created Flink pool {flink_json}')

print("Waiting for the Flink compute pool status to be PROVISIONED. Checking every 10 seconds")
status = flink_json['status']

while status != 'PROVISIONED':
    if debug:
        print("Checking status of Flink compute pool")
    time.sleep(10)
    describe_result = cli(["confluent", "flink", "compute-pool",
                           "describe", flink_json['id'], "-o", "json"])
    status = describe_result['status']

print("Starting interactive Flink shell now")
cli(["confluent", "flink", "shell", "--compute-pool", flink_json['id'],
     "--database", cluster_id], capture_output=False)
