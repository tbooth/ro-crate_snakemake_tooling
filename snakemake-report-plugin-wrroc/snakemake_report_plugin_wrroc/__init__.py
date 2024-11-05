"""RO-Crate exporter plugin for Snakemake.

   Activate this reporter while running a test run of your workflow to generate
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

@dataclass
class ReportSettings(ReportSettingsBase):
    """Additional settings for the RO-Crate reporter.
       They will occur in the Snakemake CLI as --report-wrroc-<param-name>
       Make sure that any further defined fields are Optional (or bool) and specify a default
       value of None (or False) or else Snakemake will demand these settings even when the
       reporter is not in use. Use the "required" flag below for required options.
    """
    exclude: Optional[str] = field(
        default=None,
        metadata={
            "help": "Comma-separed list of extra files to exclude",
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
        if self.settings.exclude:
            self.excludelist.extend(self.settings.exclude.split(','))

        # Decide if we are in dry-run mode. Oh, apparently the reporter always runs off
        # --dry-run mode. Right.

        # Load the existing Workflow RO-Crate...
        try:
            self.crate = ROCrate(source='./', exclude=self.excludelist)
        except ValueError:
            # ...or make a fresh one
            self.crate = ROCrate(exclude=self.excludelist)
            self.crate.add_directory(".")

    def check_essential_files(self):
        """Check for the presence of essential files.

           We want to scan/report everything even if there is an error.

           See https://docs.google.com/document/d/1KozjchVFqrctBGooRR-OWpifyI0TRuoSWIUUGIDWNyI/edit?tab=t.0
        """
        errors = []

        # A license
        if not os.path.exists("LICENSE.md") or not os.path.exists("LICENSE.txt"):
            errors.append("No LICENSE.md or LICENSE.txt found.")

        # TODO - do we need CODE_OF_CONDUCT.md and CONTRIBUTING.md too? I'm making these
        # warnings just now.

        # Evidence of Git repo. This is probably not the best way to check but we'd like to know
        # the remote URL
        if not os.path.exists(".git/config"):
            if os.path.exists("../.git/config"):
                # We are within a GIT repo but not at the top level, so:
                if not os.path.exists("workflowhub.yml"):
                    errors.append("Since your workflow is in a subdirectory of your GIT repo,"
                                  " you must include a 'workflowhub.yml' file.")
            else:
                errors.append("No .git/config file found. Is the code under source control?")

        # We need a README.md
        if not os.path.exists("README.md"):
            errors.append("Add a README.md file to introduce your worflow.")

        # The main workflow should be called "workflow/Snakefile"
        # And we should be able to introspect what was run
        if self.dag.workflow.snakefile != "workflow/Snakefile":
            # FIXME - this is returning nonsense in Snakemake 8. Does the regular html
            # reporter get a meaningful value? Nope.
            errors.append("Your main Snakefile needs to be called 'workflow/Snakefile'."
                          f" Please rename {self.dag.workflow.snakefile}.")

        # And we want a config.yaml file.
        if not os.path.exists("config/config.yaml"):
            if os.path.exists("config/config.json"):
                # For anything that needs to be hand-edited and not read by JS, YAML >> JSON.
                errors.append("Please convert your config/config.json file to YAML format using"
                              " <insert suggested converter tool here>.")
            else:
                errors.append("Please supply a default/sample configuration file for the workflow"
                              " under 'config/config.yaml'.")

        # WFH wants a "CITATION.cff"
        if not os.path.exists("CITATION.cff"):
            errors.append("You must include a 'CITATION.cff' file. If you are not requesting a"
                          " specific citation for use of the workflow, please <link instrux here"
                          " for making a minimal CFF, or maybe create a template>")

        return errors

    def check_desirable_files(self):
        """Things that *should* be in the submission but are not essential.
        """
        errors = []

        # WorkflowHub says the tests should be under "tests" but Snakemake says they should
        # be under ".tests". Can we be opinionated about it?
        if not os.path.isdir("tests"):
            if os.path.isdir(".tests"):
                errors.append("You have a '.tests' directory. Please rename it as 'tests' or else"
                              " make a symlink called 'tests'.")
            else:
                errors.append("Please add a 'tests' directory with 'unit' and 'integration'"
                              " subdirectories.")
        elif not(os.path.isdir("tests/integration") and os.path.isdir("tests/unit")):
            errors.append("Please create 'unit' and 'integration' subdirectories under 'tests'.")


        if not(os.path.exists("CODE_OF_CONDUCT.md") and os.path.exists("CONTRIBUTING.md")):
            errors.append("Please add CODE_OF_CONDUCT.md and CONTRIBUTING.md files."
                          " You may be happy copying the versions from <suggest something here>")

        return errors

    def conformance_check(self):
        """Ensure that some expected files are found. The rocrate module does
           not scan the files until the crate is exported, so we have to look for the
           files here.
        """
        essential_problems = self.check_essential_files()
        if essential_problems:
            for prob in essential_problems:
                logger.error(f"Conformance error: {prob}")
            raise RuntimeError(str(f"Exiting due to len(essential_problems) conformance issues."))

        desirable_problems = self.check_desirable_files()
        if desirable_problems:
            for prob in desirable_problems:
                logger.warning(f"Conformance warning: {prob}")
            logger.warning(f"Continuing despite len(desirable_problems) warnings.")

        # images/rulegraph.svg should be something we can generate here. If we can't do things
        # like this, what is the point of the plugin?
        if not os.path.exists("image/rulegraph.svg"):
            pass
            # TODO - call the code that plots the rulegraph and convert to SVG

    def render(self):
        try:
            self.try_render()
        except Exception as e:
            # Catch all exceptions and turn them into error messages.
            logger.error(e)

    def try_render(self):
        """Generate the crate, using the ROCrate library.
        """
        logger.info(f"Excludelist: {self.excludelist}")

        crate = self.crate

        # Remove any publication date from the root dataset of the original RO-Crate
        if 'datePublished' in crate.root_dataset:
            crate.root_dataset.__delitem__('datePublished')

        self.conformance_check()

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
