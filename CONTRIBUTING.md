1. Clone this repo and create a branch. 
2. Write a plugin!
3. Your PR for adding a plugin should follow these guidelines.
   - Create a directory with name of the plugin command.
   - Include in the directory a README with the following content.  Take a look at [cloud-kickstart](cloud-kickstart/README.md) for an example. 
     - An outline of the plugin functionality
     - Requirements
     - Useage 
4. A yml file name `manifest.yml` that has the following entries. See [cloud-kickstart/manifest.yml](cloud-kickstart/manifest.yml).  The CLI parses the manifest files to generate a list of plugins to install.
    -  `name` - The name of the plugin
    - `description` - A one sentence description of the functionality
    - `requirements` - What users must have installed to run it.
5. Add the plugin to the list in the [Available Plugins](#avaiable-plugins) section above with a link to its README file.
