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


def flink_shell(cmd_args):
    if debug:
        print(f'Starting Flink shell {cmd_args}')
    subprocess.run(cmd_args, capture_output=False)


def process_cluster_list(existing_clusters, curr_flink_region):
    if not existing_clusters:
        print(f'No existing database found, will create one in {curr_flink_region}')
    else:
        for cluster in existing_clusters:
            if cluster['region'] == flink_region:
                kafka_cluster = cluster['name']
                if debug:
                    print(f'Found a database, {kafka_cluster} with region {curr_flink_region} using that for Flink')
                return cluster
        if debug:
            print(f'No exising database found in region {curr_flink_region}, will create one')


usage_message = '''confluent flink quickstart [-h] --name NAME [--units NUM-UNITS] [--env ENV] [--region REGION] '''

parser = argparse.ArgumentParser(description='Creates Flink compute pool '
                                             'Associates a Kafka cluster for it '
                                             'creating one if none found '
                                             'then starts a Flink SQL cli session'
                                             '\nThis plugin assumes confluent CLI v3.0.0 or greater',
                                 usage=usage_message)

parser.add_argument('--name', required=True, help='The name for your Flink compute pool')
parser.add_argument('--units', default='10', choices=['5', '10'], help='The number of Confluent Flink Units')
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

print("Searching for existing database (Kafka cluster)")
cluster_list = cli(["confluent", "kafka", "cluster", "list",
                    "-o", "json"])

cluster_to_use = process_cluster_list(cluster_list, flink_region)
if cluster_to_use:
    print(f'Using database {cluster_to_use}')
    database = cluster_to_use['id']
else:
    if debug:
        print("Creating the database (Kafka cluster)")
    cluster_json = cli(["confluent", "kafka", "cluster", "create", args.name + '_kafka-cluster',
                        "-o", "json", "--cloud", args.cloud, "--region", args.region])
    database = cluster_json['id']
    if debug:
        print(f"Kafka cluster created {cluster_json}")
    geo = flink_region[0:2]
    if debug:
        print(f"Enabling Schema Registry in geo {geo}")
    sr_json = cli(["confluent", "schema-registry", "cluster", "enable", "--cloud",
                   cluster_json['provider'], "--geo", geo, "-o", "json"])
    if debug:
        print(f"Schema Registry enabled {sr_json}")

pool_name = args.name + '_flink_pool'
flink_output = cli(["confluent", "flink", "compute-pool", "create", pool_name,
                    "--cloud", args.cloud, "--region", args.region,
                    "--max-cfu", args.units, "-o", "json"])
if debug:
    print(f'Created Flink pool {flink_output}')

print("Waiting for the Flink pool status to be PROVISIONED. Checking every 10 seconds")
status = flink_output['status']

while status != 'PROVISIONED':
    if debug:
        print("Checking status of flink compute pool")
    time.sleep(10)
    describe_result = cli(["confluent", "flink", "compute-pool",
                           "describe", flink_output['id'], "-o", "json"])
    status = describe_result['status']

print("Starting interactive Flink shell now")
cli(["confluent", "flink", "shell", "--compute-pool", flink_output['id'],
     "--database", database], capture_output=False)
