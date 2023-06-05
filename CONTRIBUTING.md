1. Clone this repository and create a branch. 
2. Write a plugin!
3. Your PR for adding a plugin should follow these guidelines.
   - Create a directory with name of the plugin command.  The CLI will infer the name of the plugin from this directory name when listing potential plugins to install.
   - Include in the directory a README with the following content. Take a look at [cloud-kickstart](cloud-kickstart/README.md) for an example. 
     - An outline of the plugin functionality
     - Requirements
     - Usage 
4. A YAML file named `manifest.yml` that has the following entries. See [cloud-kickstart/manifest.yml](cloud-kickstart/manifest.yml).  The CLI parses the manifest files to generate a list of plugins to install.
    - `description` - A one sentence description of the functionality
    - `dependencies` - What users must have installed to run it.
5. Add the plugin to the list in the [Available Plugins](#avaiable-plugins) section above with a link to its README file.
