"""RO-Crate exporter plugin for Snakemake.

   Activate this reporter while running a test run of your workflwo to generate
   ???.zip

   Maybe at some point there will be an upload to WorkflowHub via the API included?
"""

from dataclasses import dataclass, field
from typing import Optional

import snakemake
from snakemake.logging import logger
import os

from snakemake_interface_common.exceptions import WorkflowError  # noqa: F401
from snakemake_interface_report_plugins.reporter import ReporterBase
from snakemake_interface_report_plugins.settings import ReportSettingsBase

from rocrate.rocrate import ROCrate
from rocrate.model import ContextEntity, Person

# Optional:
# Define additional settings for your reporter.
# They will occur in the Snakemake CLI as --report-<reporter-name>-<param-name>
# Omit this class if you don't need any.
# Make sure that all defined fields are Optional (or bool) and specify a default value
# of None (or False) or anything else that makes sense in your case.
@dataclass
class ReportSettings(ReportSettingsBase):
    exclude: Optional[str] = field(
        default=None,
        metadata={
            "help": "Comma-separed list of files to exclude",
            # Optionally request that setting is also available for specification
            # via an environment variable. The variable will be named automatically as
            # SNAKEMAKE_REPORT_<reporter-name>_<param-name>, all upper case.
            # This mechanism should ONLY be used for passwords and usernames.
            # For other items, we rather recommend to let people use a profile
            # for setting defaults
            # (https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles).
            "env_var": False,
            # Optionally specify a function that parses the value given by the user.
            # This is useful to create complex types from the user input.
            #"parse_func": ...,
            # If a parse_func is specified, you also have to specify an unparse_func
            # that converts the parsed value back to a string.
            #"unparse_func": ...,
            # Optionally specify that setting is required when the reporter is in use.
            "required": False,
        },
    )


# Required:
# Implementation of your reporter
class Reporter(ReporterBase):
    def __post_init__(self, excludelist = (".snakemake", ".git", ".github", ".test", ".gitignore")):
        # initialize additional attributes
        # Do not overwrite the __init__ method as this is kept in control of the base
        # class in order to simplify the update process.
        # See https://github.com/snakemake/snakemake-interface-report-plugins/snakemake_interface_report_plugins/reporter.py # noqa: E501
        # for attributes of the base class.
        # In particular, the settings of above ReportSettings class are accessible via
        # self.settings.
        self.outdir = "ro-crate_out"
        self.excludelist = list(excludelist)
        self.excludelist.append(self.outdir)

        # Add any exclude items specified by the user
        self.excludelist.extend(self.settings.exclude.split(',') if self.settings.exclude else [])

        # Decide if we are in dry-run mode. Oh, apparently the reporter always runs off
        # --dry-run mode. Right.

        # Load the existing Workflow RO-Crate...
        try:
            self.crate = ROCrate(source='./', exclude=self.excludelist)
        except ValueError:
            # ...or make a fresh one
            self.crate = ROCrate(exclude=self.excludelist)
            self.crate.add_directory(".")

    def render(self):
        """Generate the crate, using the ROCrate library.
        """
        logger.info(f"Excludelist: {self.excludelist}")

        crate = self.crate

        # Remove any publication date from the root dataset of the original RO-Crate
        if 'datePublished' in crate.root_dataset:
            crate.root_dataset.__delitem__('datePublished')

        # Ensure that some expected files are found. The rocrate module does
        # not scan the files until the crate is exported, so we have to look for the
        # files here.
        import pdb ; pdb.set_trace()

        # Provenance Crate - add snakemake version
        for entity in crate.contextual_entities:
            if entity.type == 'ComputerLanguage' and 'snakemake' in entity.id.lower():
                entity['version'] = snakemake.__version__.split("+")[0]

        # Provenance Crate - record execution of workflow as a CreateAction object
        instruments = {}
        for entity in crate.data_entities:
            if 'ComputationalWorkflow' in entity.type:
                instruments["@id"] = entity.id
        workflow_run_properties = {
            #"@id":"FIXME-add-workflow-run-properties-id",
            "@type":"CreateAction",
            "name":"Snakemake workflow run (FIXME)",
            "endTime":"FIXME date",
            #"instrument":instruments,
            #"subjectOf":{"@id":"FIXME creative work (workflow?)"},
            "object":["FIXME inputs"],
            "result":["FIXME outputs"]
        }
        if '@id' in instruments:
            workflow_run_properties['instruments'] = instruments
        logger.info(workflow_run_properties)
        workflow_run = crate.add(
            ContextEntity(crate, properties=workflow_run_properties)
        )

        # Provenance Run Crate (individual step information)

        # print basic information (start/end) of each job
        for rulename, rule  in self.rules.items():
            logger.info(f"rule: {rulename}")
            #print(rule)
            #print("rule: " + rec.rule)
            #print("starttime: " + str(rec.starttime))
            #print("endtime: " + str(rec.endtime))
            #print("ROCrate date published: " + str(crate.datePublished.date()))

        # Add Person running workflow (agent)
        person_properties = {
            #"@id": "FIXME-ORCID?",
            "givenName": "FIXME",
            "familyName": "FIXME",
            "affiliation": "FIXME"
        }
        agent = crate.add(Person(crate,
                                 "FIXME-ORCID?",
                                 properties=person_properties))
        workflow_run.append_to( "agent", [agent] )

        # Reference CreateAction in the root Dataset
        crate.root_dataset.append_to(
            "mentions" , [{"@id": workflow_run.id}]
        )

        # Set the conformsTo statement for the root Dataset.
        # Note that this will replace any pre-existing conformsTo information
        crate.root_dataset["conformsTo"] = [
                    {"@id": "https://w3id.org/ro/wfrun/process/0.1"},
                    {"@id": "https://w3id.org/ro/wfrun/workflow/0.5"},
                    {"@id": "https://w3id.org/workflowhub/workflow-ro-crate/1.0"}
                ]


        crate.write(self.outdir)
        crate.write_zip(self.outdir + ".zip")
