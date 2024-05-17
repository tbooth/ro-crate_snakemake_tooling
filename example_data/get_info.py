from bs4 import BeautifulSoup
import json
import re

# Read HTML content from file
with open("report.html", "r") as file:
    html_content = file.read()

# Parse the HTML
soup = BeautifulSoup(html_content, 'html.parser')

# Find the script tag with id="rules"
script_tag = soup.find('script', id='rules')

if script_tag:
    # Extract the content of the script tag
    script_content = script_tag.string.strip()

    # Extract JSON content by removing 'var rules =' prefix and ';' suffix
    json_content = script_content.replace('var rules =', '').rstrip(';')

    try:
        # Parse the JSON content
        rules_data = json.loads(json_content)

        # Create a list to store rule details
        rules_list = []

        # Iterate over each rule and append its details to the list
        for rule_name, rule_data in rules_data.items():
            # Separate software name and version from dependencies
            dependencies = rule_data.get('conda_env', {}).get('dependencies', [])
            dependencies_split = []
            for dep in dependencies:
                if isinstance(dep, str):
                    if '=' in dep:
                        software, version = [ dep.split('=')[i] for i in [0,1]]
                        dependencies_split.append({"software": software.strip(), "version": version.strip()})
                    else:
                        dependencies_split.append({"software": dep.strip(), "version": None})

            rule_details = {
                "Rule": rule_name,
                "Channels": rule_data.get('conda_env', {}).get('channels', []),
                "Dependencies": dependencies_split,
                "Inputs": rule_data.get('input', []),
                "Outputs": rule_data.get('output', []),
                "n_jobs": rule_data.get('n_jobs', None)
            }
            rules_list.append(rule_details)
        # Convert the list of rule details to JSON format
        json_output = json.dumps(rules_list, indent=2)
        print(json_output)

    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
else:
    print("No script tag with id='rules' found in the HTML.")
