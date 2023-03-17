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


def cli(cmd_args, print_output, fmt_json=True):
    results = subprocess.run(cmd_args, capture_output=True)
    if results.returncode != 0:
        print(str(results.stderr, 'UTF-8'))
        exit(results.returncode)
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


usage_message = '''confluent cloud-kickstart [-h] --name NAME [--env ENV] [--cloud {aws,azure,gcp}] [--region REGION] [--geo {apac,eu,us}]
[--client {clojure,cpp,csharp,go,groovy,java,kotlin,ktor,nodejs,python,restapi,ruby,rust,scala,springboot}] [--debug {y,n}] [--dir DIR]
'''

parser = argparse.ArgumentParser(description='Creates a Kafka cluster with API keys, '
                                             'Schema Registry with API keys and a client '
                                             'config properties file.'
                                             '\nThis plugin assumes confluent CLI v3.0.0 or greater',
                                 usage=usage_message)

parser.add_argument('--name', required=True, help='The name for your Confluent Kafka Cluster')
parser.add_argument('--env', help='The environment name')
parser.add_argument('--cloud', default='aws', choices=['aws', 'azure', 'gcp'],
                    help='Cloud Provider, Defaults to aws')
parser.add_argument('--region', default='us-west-2', help='Cloud region e.g us-west-2 (aws), '
                                                          'westus (azure), us-west1 (gcp)  Defaults to us-west-2')
parser.add_argument('--geo', choices=['apac', 'eu', 'us'], default='us',
                    help='Cloud geographical region Defaults to us')
parser.add_argument('--client', choices=['clojure', 'cpp', 'csharp', 'go', 'groovy', 'java', 'kotlin',
                                         'ktor', 'nodejs', 'python', 'restapi',
                                         'ruby', 'rust', 'scala', 'springboot'],
                    default='java', help='Properties file used by client (default java)')
parser.add_argument("--debug", choices=['y', 'n'], default='n',
                    help="Prints the results of every command, defaults to n")
parser.add_argument("--dir", help='Directory to save credentials and client configs, defaults to download directory')

args = parser.parse_args()
save_dir = args.dir
if save_dir is None:
    save_dir = str(os.path.join(Path.home(), "Downloads"))

debug = False if args.debug == 'n' else True

print("Creating the Kafka cluster")
cluster_json = cli(["confluent", "kafka", "cluster", "create", args.name,
                    "-o", "json", "--cloud", args.cloud, "--region", args.region], debug)

print("Generating api keys for the cluster")
creds_json = cli(["confluent", "api-key", "create", "--resource", cluster_json['id'], "-o", "json"], debug)

print("Enabling Schema Registry")
sr_json = cli(["confluent", "schema-registry", "cluster", "enable", "--cloud",
               cluster_json['provider'], "--geo", args.geo, "-o", "json"], debug)

print("Generating API keys for Schema Registry")
sr_creds_json = cli(["confluent", "api-key", "create", "--resource", sr_json['id'], "-o", "json"], debug)

print("Enabling the API key for Cluster")
cli(["confluent", "api-key", "use", creds_json['api_key'], "--resource", cluster_json['id']], debug, fmt_json=False)

print("Generating client config")
client_config = cli(["confluent", "kafka", "client-config", "create", args.client,
                     "--cluster", cluster_json['id'],
                     "--api-key", creds_json['api_key'],
                     "--api-secret", creds_json['api_secret'],
                     "--schema-registry-api-key", sr_creds_json['api_key'],
                     "--schema-registry-api-secret", sr_creds_json['api_secret']],
                    debug, fmt_json=False)

cluster_keys_file = save_dir + '/' + "cluster-api-keys-" + cluster_json['id'] + ".json"
write_to_file(cluster_keys_file, creds_json)

ts = date_string = f'{datetime.now():%Y-%m-%d_%H-%M-%S%z}'
sr_keys_file = save_dir + '/' + "sr-api-keys-" + ts + '_' + sr_json['id'] + ".json"
write_to_file(sr_keys_file, sr_creds_json)

client_configs_file = save_dir + '/' + args.client + '_configs_' + cluster_json['id'] + ".properties"
write_to_file(client_configs_file, client_config, json_fmt=False)
