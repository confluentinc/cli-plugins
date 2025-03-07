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
from pathlib import Path
from datetime import datetime
import os
import time


def cli(cmd_args, print_output, retries=0, retry_wait_seconds=1, capture_output=True, fmt_json=True):
    results = subprocess.run(cmd_args, capture_output=capture_output)

    while results.returncode != 0 and retries > 0:
        results = subprocess.run(cmd_args, capture_output=capture_output)
        time.sleep(retry_wait_seconds)
        retries -= 1

    if results.returncode != 0:
        print(str(results.stderr, 'UTF-8'))
        exit(results.returncode)

    if capture_output:
        if fmt_json:
            final_result = json.loads(results.stdout)
        else:
            final_result = str(results.stdout, 'UTF-8')

        if print_output:
            print("Debug: %s" % final_result)

        return final_result


def write_to_file(file_name, text, json_fmt=True):
    print("Writing %s to %s" % (file_name, save_dir))
    with open(file_name, 'w', encoding='utf-8') as out_file:
        if json_fmt:
            json.dump(text, out_file, indent=2, sort_keys=True)
        else:
            out_file.writelines(text)


def resolve_environment(environment_name, debug):
    env_id = None
    all_env_json = cli(["confluent", "environment", "list", "-o", "json"], debug)
    for env_json in all_env_json:
        if environment_name == env_json['name']:
            # environment names are unique so it's safe to short circuit
            env_id = env_json['id']
            break
    if not env_id:
        print(f'Creating new environment {environment_name}')
        new_env_json = cli(["confluent", "environment", "create", environment_name,
                            "--governance-package", "essentials", "-o", "json"], debug)
        env_id = new_env_json['id']

    print(f'Setting the active environment to {environment_name} ({env_id})')
    cli(["confluent", "environment", "use", env_id], debug, capture_output=False)


usage_message = '''confluent cloud-kickstart [-h] --name NAME [--env ENV] [--cloud {aws,azure,gcp}] [--region REGION]
[--client {clojure,cpp,csharp,go,groovy,java,kotlin,ktor,nodejs,python,restapi,ruby,rust,scala,springboot}] 
[--output-format {properties, stdout} [--debug {y,n}] [--dir DIR]
'''

parser = argparse.ArgumentParser(description='Creates a Kafka cluster with API keys, '
                                             'Schema Registry API keys, and optionally a client '
                                             'config properties file.'
                                             '\nThis plugin assumes confluent CLI v4.0.0 or greater',
                                 usage=usage_message)

parser.add_argument('--name', required=True, help='The name for your Confluent Kafka Cluster')
parser.add_argument('--environment-name', help='Environment name to use, will create it if the environment does not exist',
                    required=True)
parser.add_argument('--cloud', default='aws', choices=['aws', 'azure', 'gcp'],
                    help='Cloud Provider, Defaults to aws')
parser.add_argument('--region', default='us-west-2', help='Cloud region e.g us-west-2 (aws), '
                                                          'westus (azure), us-west1 (gcp)  Defaults to us-west-2')
parser.add_argument('--client', choices=['clojure', 'cpp', 'csharp', 'go', 'groovy', 'java', 'kotlin',
                                         'ktor', 'nodejs', 'python', 'restapi',
                                         'ruby', 'rust', 'scala', 'springboot'],
                    default='java', help='Properties file used by client (default java)')
parser.add_argument("--output-format", choices=['properties', 'stdout'], default='properties',
                    help="Whether to output a client configuration properties file or human-readable credentials to the terminal, defaults to 'properties'")
parser.add_argument("--debug", choices=['y', 'n'], default='n',
                    help="Prints the results of every command, defaults to n")
parser.add_argument("--dir", help='Directory to save credentials and client configs, defaults to download directory')

args = parser.parse_args()
save_dir = args.dir
if save_dir is None:
    save_dir = str(os.path.join(Path.home(), "Downloads"))

debug = False if args.debug == 'n' else True

resolve_environment(args.environment_name, debug)

print("Creating the Kafka cluster")
cluster_json = cli(["confluent", "kafka", "cluster", "create", args.name,
                    "-o", "json", "--cloud", args.cloud, "--region", args.region], debug)

print("Generating API keys for the Kafka cluster")
creds_json = cli(["confluent", "api-key", "create", "--resource", cluster_json['id'], "-o", "json"], debug)

print("Generating API keys for Schema Registry")
sr_describe_json = cli(["confluent", "schema-registry", "cluster", "describe", "-o", "json"], debug,
                       retries=15, retry_wait_seconds=5)
sr_creds_json = cli(["confluent", "api-key", "create", "--resource", sr_describe_json['cluster'], "-o", "json"], debug)

print("Enabling the API key for the Kafka cluster")
cli(["confluent", "api-key", "use", creds_json['api_key'], "--resource", cluster_json['id']], debug, fmt_json=False)

print("Setting created cluster for use in subsequent commands")
cli(["confluent", "kafka", "cluster", "use", cluster_json['id']], debug, fmt_json=False)

if args.output_format == 'properties':
    print("Generating client configuration")
    client_config = cli(["confluent", "kafka", "client-config", "create", args.client,
                         "--api-key", creds_json['api_key'],
                         "--api-secret", creds_json['api_secret'],
                         "--schema-registry-api-key", sr_creds_json['api_key'],
                         "--schema-registry-api-secret", sr_creds_json['api_secret']],
                        debug, fmt_json=False)

    cluster_keys_file = save_dir + '/' + "cluster-api-keys-" + cluster_json['id'] + ".json"
    write_to_file(cluster_keys_file, creds_json)

    ts = date_string = f'{datetime.now():%Y-%m-%d_%H-%M-%S%z}'
    sr_describe_json = cli(["confluent", "schema-registry", "cluster", "describe", "-o", "json"], debug)
    sr_keys_file = save_dir + '/' + "sr-api-keys-" + ts + '_' + sr_describe_json['cluster'] + ".json"
    write_to_file(sr_keys_file, sr_creds_json)

    client_configs_file = save_dir + '/' + args.client + '_configs_' + cluster_json['id'] + ".properties"
    write_to_file(client_configs_file, client_config, json_fmt=False)
else:
    cluster_describe_json = cli(["confluent", "kafka", "cluster", "describe", cluster_json['id'], "-o", "json"], debug)
    print("\nKafka bootstrap servers endpoint: %s" % cluster_describe_json['endpoint'].replace('SASL_SSL://',''))
    print("Kafka API key:                    %s" % creds_json['api_key'])
    print("Kafka API secret:                 %s\n" % creds_json['api_secret'])
    print("\nSchema Registry Endpoint:   %s" % sr_describe_json['endpoint_url'])
    print("Schema Registry API key:    %s" % sr_creds_json['api_key'])
    print("Schema Registry API secret: %s" % sr_creds_json['api_secret'])