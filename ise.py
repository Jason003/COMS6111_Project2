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
OUTPUT_AMOUNT = 3

# Google API query template
URL = Template("https://www.googleapis.com/customsearch/v1?key=$client_key&cx=$engine_key&q=$query")



def getRelationship(i):
    """Return relation string for integer input."""
    relationships = ["Live_In", "Located_In", "OrgBased_In", "Work_For"]
    if i < len(relationships):
        return relationships[i-1]
    return relationships[3]

def requery():
    """Select unused, high-confidence, tuple then query and process."""
    pass

def query():
    """Send request to Google Custom Search endpoint."""
    url = URL.substitute(client_key = CLIENT_KEY, engine_key = ENGINE_KEY, query = QUERY)
    print("--- REMOVE FROM HERE ---")
    print(url)
    print("--- TO HERE --- ")
    response = requests.get(url)
    items = response.json()["items"]
    print (items)

def process():
    """Process each result from Google search."""
    # check if already processed
    # process new url
        # fetch HTML
        # extract plain text
        # annotate text
        # identify tuples

    # check if done
    # else, requery
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
    print("# of Tuples    = %d" % (OUTPUT_AMOUNT))

def processCLI():
    """Read values from cli and store in variables."""
    if len(sys.argv) > 1: CLIENT_KEY = sys.argv[1]

    if len(sys.argv) > 2: ENGINE_KEY = sys.argv[2]

    if len(sys.argv) > 3: RELATION = getRelationship(int(sys.argv[3]))

    if len(sys.argv) > 4: THRESHOLD = float(sys.argv[4])

    if len(sys.argv) > 5: QUERY = sys.argv[5].lower()

    if len(sys.argv) > 6: OUTPUT_AMOUNT = int(sys.argv[6])

    print_parameters()

if __name__ == '__main__':
    sys.exit(main())
