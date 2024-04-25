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

        # Extract the "go_fetch" rule entry
        go_fetch_rule = rules_data.get("go_fetch")

        if go_fetch_rule:
            print(go_fetch_rule)
        else:
            print("No 'go_fetch' rule found.")
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
else:
    print("No script tag with id='rules' found in the HTML.")

if go_fetch_rule:
    # List channels 
    channels = go_fetch_rule.get('conda_env', {}).get('channels', [])
    print("Channels:", channels)
    
    # List dependencies
    dependencies = go_fetch_rule.get('conda_env', {}).get('dependencies', [])
    print("Dependencies:", dependencies)

    # List inputs
    inputs = go_fetch_rule.get('input', [])
    print("Inputs:", inputs)

    # List outputs
    outputs = go_fetch_rule.get('output', [])
    print("Outputs:", outputs)

    # Print n_jobs
    n_jobs = go_fetch_rule.get('n_jobs', None)
    print("n_jobs:", n_jobs)
else:
    print("No 'go_fetch' rule found.")
