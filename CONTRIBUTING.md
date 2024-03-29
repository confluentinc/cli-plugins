## Contribute a plugin
1. Clone this repository and create a branch. 
2. [Write a plugin](#write-a-plugin)!
3. Your PR for adding a plugin should follow these guidelines.
   - Create a directory with name of the plugin command.  The CLI will infer the name of the plugin from this directory name when listing potential plugins to install. This name should follow the conventions specified in the [Plugin file name](#plugin-file-name) section.
   - Include in the directory a README with the following content. Take a look at [cloud-kickstart](cloud-kickstart/README.md) for an example. 
     - An outline of the plugin functionality
     - Requirements
     - Usage 
4. A YAML file named `manifest.yml` that has the following entries. See [cloud-kickstart/manifest.yml](cloud-kickstart/manifest.yml).  The CLI parses the manifest files to generate a list of plugins to install.
    - `description` - A one sentence description of the functionality.
    - `dependencies` - A list of what users must have installed to run it. Each entry must have the following fields:
      - `name` - The name of the dependency.
      - `version` - A minimum required version to use the plugin.

    Example:
    ```
    description: Use the CLI to print Hello World.
    dependencies:
    - name: Go
      version: "1.19.6"
    - name: jq
      version: "1.6"
    ```
    The first dependency must be the language in which the plugin is written. Currently, we support Go, Python, and Bash scripts. The first dependency's `name` field should be one of `Go`, `Python`, or `Bash`. For example, `Go` is allowed but `Golang` is not.

    Subsequent dependencies may be other programs required by your plugin, such as the [jq command line tool](https://jqlang.github.io/jq/).
5. Add the plugin to the list in the [Available Plugins](README.md#available-plugins) section in the repository README file with a link to its README file.

## Write a Plugin

You can write a plugin in Go, Python, or Bash. For Go, you must set up a module. For Bash scripts, the first line should be
```
#!/bin/bash
```

### Plugin file name

A plugin's command name is determined by its filename. The following
rules apply:

-   A plugin filename must begin with `confluent-`.

-   Subcommands in a plugin's command are separated by dashes (`-`) in
    its filename. For example, a plugin named `confluent-this-command`
    would define the command `confluent this command`.

-   To have a plugin command containing dashes (`-`) or underscores
    (`_`), use an underscore (`_`) in the plugin filenames in place of a
    dash (`-`). For example, you can invoke a plugin whose filename is
    `confluent-that_command` by running either of the following
    commmands:

    ```
    confluent that-command
    ```
    
    ```bash
    confluent that_command
    ```

-   On Windows, all file extensions defined in `$PATHTEXT` are
    supported.

-   On Linux and macOS, any file extension is supported as long as the
    file is executable.

### Naming limitations

The following limitations apply to naming plugins. If these rules are
violated, the `confluent plugin list` command output will have a warning
message that the offending plugin will be ignored.

-   A plugin can't override an existing command. Therefore, a plugin
    whose name exactly matches a native CLI command's name will be
    ignored.

-   Two or more plugins can't have the same name.

    The first one found on your `$PATH` is used. The other plugins
    discovered with the same name are ignored.

