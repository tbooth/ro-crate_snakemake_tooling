# Report to RO-crate

This is a brief summary of efforts during the iBOL Europe Hackathon, which took place in April 2024 aimed at forming a structure for provenance RO-crate from a Snakemake pipeline.
We aimed to define the information necessary to reproduce a Workflow Run for a given existing workflow.
Our efforts were based on extracting the necessary information from the Snakemake `report.html`, including software dependencies, input and output files, runtimes and dates.
These have been extracted with the view of aligning with the recommendations and guidelines for provenance RO-crate explained [here](https://www.researchobject.org/workflow-run-crate/profiles/provenance_run_crate)

## Example data

An example report can be found here: `example_data/report.html`, which is a run of the genome skimming pipeline published here on : [Workflowhub](https://workflowhub.eu/workflows/791)
A desired output format for the provenance RO-crate would include the following information which is available within the `report.html`:

- Rules:
  - Dependencies (with channel and versions)
  - Input
  - Output
  - Command run
  - Location of rule (permanent url)
  - Number of run instances
  - Runtime of each instance
  - Finishing time of each instance

An example of the format of json we are aiming to build would be something like the following:

```
{   
    "@id": "go_fetch",
    "@type": "SoftwareApplication",
    "url": "https://workflowhub.eu/workflows/791/git/1/download/workflow/rules/go_fetch.smk"
    "softwareRequirements": [
        {"@id": "go_fetch_getorganelle"},
        {"@id": "go_fetch_trf"},
        {"@id": "go_fetch_biopython"}
    ],
},
{   
    "@id": "go_fetch_getorganelle",
    "@type": "SoftwareApplication",
    "url": "https://anaconda.org/bioconda/getorganelle",
    "name": "getorganelle",
    "version": "1.7.7.0"
},
{
    "@id": "go_fetch_trf"
    "@type": "SoftwareApplication",
    "url": "https://anaconda.org/bioconda/trf",
    "name": "trf"
},
{
    "@id": "go_fetch_biopython",
    "@type": "SoftwareApplication",
    "url": "https://anaconda.org/conda-forge/biopython",
    "name": "biopython"
}
```

## Extracting metadata

To extract the information above from the html file, we have relied on the BeautifulSoup library.
An initial script to extract the channels, dependencies, inputs, outputs and number of jobs is available in `example_data/get_info.py` and dependencies can be installed via the conda yaml: `example_data/conda_env.yaml`.

In this instance we obtained the following outputs:

```
Channels: ['conda-forge', 'bioconda', 'defaults']
Dependencies: ['getorganelle =1.7.7.0', 'trf', 'biopython']
Inputs: []
Outputs: ['results/go_fetch/{taxids}/gene.fasta', 'results/go_fetch/{taxids}/seed.fasta']
n_jobs: 4
```

The output dependencies would be used to fill the softwareRequirements and versions, however it is not yet clear how to uniquely determine the url for each tool.
As this is not output by the Snakemake report by default, we have relied on the user inputting the information manually, and while the channels used are listed in the report, it is not clear which channel was used for which tool, unless the user has strict channel priority enabled.

## Limitations

So far not every tool lists a version, as this was not given in the conda yaml in the workflow itself.
Furthermore there are channels listed in the Snakemake `report.html` which are not present in the conda yaml, likely a function of how channels were set up by the user that run the pipeline.
This is particularly an issue for reproducibility if each user has different channels, different channel priorities.

There are also a number of fields that we would like to include in the provenance RO-crate which are not immediately retrievable from the run.
These include: Name and affiliation of the individual who did the run, location (url) of the workflow run and of each sub-workflow or rule.	

## Future work and wishes
### Extracting metadata from workflow runs
Wherever possible, the metadata should be extracted automatically either by the workflow executor or the reporting or log files.
It would be preferable not to have to extract the versions and tools from each rule folder, but rather rely on a single log/report file, which should contain the necessary information.
Part of the issues observed in the report we analysed come from how Snakemake is handling the conda environments, where if versions are not listed in the environment yamls, they are not transferred to the report, and personal channels and priorities can overwrite any written for the pipeline.
It would perhaps be preferable for future implementations to create Singularity or Docker images to handle this and any future user could download the entire image, rather than install the environments from scratch.
### Provenance run crates
It is not entirely obvious how to convert a Snakemake workflow run into the format described in the provenance run crate documentation and we encountered a number of edge-cases that we were not able to independently resolve"
- Can a "rule" only be documented as a tool wrapper if it exists in its own sub-workflow file?
- How should multiple rules within one Snakefile be documented?
- If two rules use the same software but different versions, how should this be handled within the metadata json?
- If a tool is run on multiple (even thousands) of different files or variables, do these all need to be documented, or do wildcards suffice?


