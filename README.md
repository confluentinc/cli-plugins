## Plugins for Confluent CLI

This repo contains plugins for use with
the [Confluent CLI](https://docs.confluent.io/confluent-cli/current/overview.html). For more information on plugins, consult the [CLI Plugin documentation](https://docs.confluent.io/confluent-cli/current/plugins.html)


## Plugins


Here's a list of the current plugins you can install for the confluent CLI:

1. [confluent cloud-kickstart](cloud-kickstart/README.md)

2. [confluent-login-headless_sso](confluent-login-headless_sso/README.md)

2. [confluent purge-keys](purge-keys/README.md)




## Instructions for adding a plugin to this repo

1. Clone this repo and create a branch. Write a plugin!
2. Your PR for adding a plugin should follow these guidelines.  Take a look at [cloud-kickstart](cloud-kickstart/README.md) for an example.
   - Create a directory with name of the plugin command
   - Include in the directory a README file containing
     - An outline of the plugin functionality
     - Requirements
     - Useage 
3. A yml file name `manifest.yml` that has the following entries. See [cloud-kickstart/manifest.yml](cloud-kickstart/manifest.yml).  The CLI parses the manifest files to generate a list of plugins to install.
    -  `name` - The name of the plugin
    - `description` - A one sentence description of the plugin functionality
    - `requirements` - The requirments users must have installed to run it.

4. Add the plugin to the list in the (#Plugins) section with a link to its README file.