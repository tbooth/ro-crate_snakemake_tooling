# ro-crate_snakemake_tooling
Collection of python tools for processing snakemake metadata for RO-Crate creation


## Snakemake reporter plugin

Documentation how the wrroc reporter plugin is built.

### Setup poetry

Poetry is used for setting up a new plugin from a template.  
In my experience, the Python version used here has to match the Python version used with Snakemake environment, otherwise the plugin does not work.  
But this should be a solvable problem.

```
conda create --name poetry python=3.12
conda activate poetry
pip install poetry
```

### Create new plugin from the template

Note: The poetry project was added to this repository.  
You only have to install the poetry plugin and can use the project in this repository.

```
# Install poetry plugin via
poetry self add poetry-snakemake-plugin

# Create a new poetry project via
poetry new snakemake-report-plugin-wrroc

cd snakemake-report-plugin-wrroc

# Scaffold the project as a snakemake report plugin
poetry scaffold-snakemake-report-plugin

# Next, edit the scaffolded code according to your needs, and publish
# the resulting plugin into a github repository. The scaffold command also 
# creates github actions workflows that will immediately start to check and test
# the plugin.
```

### Implement plugin

Implement the report `render` method here:

```
snakemake-report-plugin-wrroc/snakemake_report_plugin_wrroc/__init__.py
```

For plugin development one can take a look what information the base class [ReporterBase](https://github.com/snakemake/snakemake-interface-report-plugins/blob/main/snakemake_interface_report_plugins/reporter.py) provides.

### Build and install plugin

Build wheel and tar.gz:

```
poetry build
```

Install the plugin.

```
pip install --force-reinstall dist/snakemake_report_plugin_wrroc-0.1.0-py3-none-any.whl
```

Snakemake should find the plugin! Note that there are many copy&paste errors for the reporter plugin, even in the poetry template repository. Most of the time the term `executor plugin` is used instead of `reporter plugin`.

```
snakemake -h
[...]
wrroc executor settings:
  --report-wrroc-myparam VALUE
                        Some help text (default: <dataclasses._MISSING_TYPE object at 0x7f0091b3f140>)
```

### Create a report

Test the reporter plugin in the skim2mt directory, where the `.snakemake/metadata` resides:

```
snakemake --reporter wrroc
```