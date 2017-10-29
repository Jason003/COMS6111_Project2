#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import requests

from string import Template

# Configuration variables
CLIENT_KEY = "AIzaSyCATX_cG2DgsJjFtCdgcThfR2xaH7MSMl0"
ENGINE_KEY = "010829534362544137563:ndji7c0ivva"
RELATION = "Work_For"
THRESHOLD = 1.0
QUERY = "bill gates microsoft"
TARGET_TUPLE_AMT = 3

# Google API query template
URL = Template("https://www.googleapis.com/customsearch/v1?key=$client_key&cx=$engine_key&q=$query")
URL_HISTORY = []

def getRelationship(i):
    """Return relation string for integer input."""
    relationships = ["Live_In", "Located_In", "OrgBased_In", "Work_For"]
    if i < len(relationships):
        return relationships[i-1]
    return relationships[3]

def requery():
    """Select unused, high-confidence, tuple then query and process."""
    # check if done
    # otherwise, find new query term
    pass

def query():
    """Send request to Google Custom Search endpoint."""
    url = URL.substitute(client_key = CLIENT_KEY, engine_key = ENGINE_KEY, query = QUERY)
    print("--- REMOVE FROM HERE ---")
    print(url)
    print("--- TO HERE --- ")
    response = requests.get(url)
    items = response.json()["items"]
    process(items)

def process(items):
    """Process each result from Google search."""
    for item in items:
        # check if url has already processed
        if item["link"] not in URL_HISTORY:
            # process new url
                # fetch HTML
                # extract plain text
                # annotate text
                # identify tuples
            print("new")
        else:
            print("skip " + item["link"])

    # requery
    pass

def fetchHTML():
    """Fetch url HTML."""
    pass

def extractText():
    """Strip markdown."""
    pass

def annotate():
    """Annotate text with the Stanford CoreNLP."""
    pass

def identify():
    """Identify new tuples."""
    # identify tuples
    # check if they've already been identified
    pass

def progressCheck():
    """Done if k matches."""
    pass


def main():
    """Main entry point for the script."""
    processCLI()
    query()
    #print_result

    print("Finished.")

def print_parameters():
    print("Parameters:")
    print("Client key     = " + CLIENT_KEY)
    print("Engine key     = " + ENGINE_KEY)
    print("Relation       = " + RELATION)
    print("Threshold      = %.1f" % (THRESHOLD))
    print("Query          = " + QUERY)
    print("# of Tuples    = %d" % (TARGET_TUPLE_AMT))

def processCLI():
    """Read values from cli and store in variables."""
    if len(sys.argv) > 1: CLIENT_KEY = sys.argv[1]

    if len(sys.argv) > 2: ENGINE_KEY = sys.argv[2]

    if len(sys.argv) > 3: RELATION = getRelationship(int(sys.argv[3]))

    if len(sys.argv) > 4: THRESHOLD = float(sys.argv[4])

    if len(sys.argv) > 5: QUERY = sys.argv[5].lower()

    if len(sys.argv) > 6: TARGET_TUPLE_AMT = int(sys.argv[6])

    print_parameters()

if __name__ == '__main__':
    sys.exit(main())
