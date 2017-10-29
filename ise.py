#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import requests

from bs4 import BeautifulSoup
from string import Template
from NLPCore import NLPCoreClient

# Configuration variables
CLIENT_KEY = "AIzaSyCATX_cG2DgsJjFtCdgcThfR2xaH7MSMl0"
ENGINE_KEY = "010829534362544137563:ndji7c0ivva"
RELATION = "Work_For"
THRESHOLD = 0.25
QUERY = "bill gates microsoft"
TARGET_TUPLE_AMT = 3

STANFORD_CORENLP_PATH = "stanford-corenlp-full-2017-06-09"

# Google API query template
URL = Template("https://www.googleapis.com/customsearch/v1?key=$client_key&cx=$engine_key&q=$query")
URL_HISTORY = []

# List of extracted tuples
EXTRACTED_TUPLES = []

def requery():
    """Select unused, high-confidence, tuple then query and process."""
    # check if done
    # otherwise, find new query term
    pass

def query():
    """Send request to Google Custom Search endpoint."""
    print("=========== Iteration: ### - Query: " + QUERY + "===========")
    url = URL.substitute(client_key = CLIENT_KEY, engine_key = ENGINE_KEY, query = QUERY)
    response = requests.get(url)
    items = response.json()["items"]
    process(items)

def process(items):
    """Process each result from Google search."""
    for item in items:
        # check if url has already processed
        if item["link"] not in URL_HISTORY:
            # process new url
            print("Processing: " + item["link"])
            blob = fetch_site_blob(item["link"])
            text = extract_text(blob)
            relations = find_relations(text)
            # identify_quality_tuples()
        else:
            print("--- REMOVE FROM HERE ---")
            print("skip " + item["link"])
            print ("--- TO HERE ---")

    # requery
    pass

def fetch_site_blob(url):
    """Scrap HTML from URL."""
    doc = requests.get(url, timeout=10)
    return doc.text

def extract_text(blob):
    """Separate text from markdown."""
    html = BeautifulSoup(blob, "html.parser")

    # TODO there are probably opportunites to improve the code below
    body = html.find('body')

    # remove any script or style elements
    for chunk in body(["script", "style"]):
        chunk.extract()

    # raw text
    rawText = body.get_text()

    # reduce whitespace
    lines = (line.strip() for line in rawText.splitlines())

    # break multi-headlines into a single line
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

def find_relations(text):
    """Annotate text with the Stanford CoreNLP."""
    client = NLPCoreClient(STANFORD_CORENLP_PATH)
    properties = {
        "annotators": "",
        "parse.model": "edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz",
        "ner.useSUTime": "0"
    }


    print ("find relations doesn't work yet!")
    # annotate first pipeline
    # properties["annotators"] = "tokenize,ssplit,pos,lemma,ner,relation"
    # doc = client.annotate(text=text, properties=properties)
    #
    # # extract sentences for second pipeline
    # sentences = []
    # for sentence in doc.sentences:
    #     print (len(sentence.relations))
    #     for relation in sentence.relations:
    #         print (relation.entities)
    #     s = ""
    #     for token in sentence.tokens:
    #         s += " " + token.word
    #     sentences.append(s)
    #
    # print(sentences)

    # annotate second pipeline
    # properties["annotators"] = "tokenize,ssplit,pos,lemma,ner,parse,relation"
    # doc = client.annotate(text=sentences, properties=properties)
    #
    # print(doc.sentences[0].relations[0])

    # extract relations into dict
                # # build tuples out of the docs
                # relations = []
                # for sentence in doc.sentences:
                #     r = {}
                #     r["EntityType1"] = sentence.entities[0].type
                #     r["EntityValue1"] = sentence.entities[0].value
                #     r["EntityType2"] = sentence.entities[1].type
                #     r["EntityValue2"] = sentence.entities[1].value
                #     print (len(sentence.relations))
                #     print(sentence.relations[0])
                #     relations.append(r)
                #
                # print (relations)

def identify_quality_tuples(tuples):
    """Identify new tuples with confidence at least equal to the requested threshold."""
    for t in tuples:
        print (t)
    # check if they've already been identified
    pass

def progress_check():
    """Done if k matches."""
    pass


def main():
    """Main entry point for the script."""
    process_CLI()
    query()
    #print_result

    print("Finished.")

def print_parameters():
    print("Parameters:")
    print("Client key     = " + CLIENT_KEY)
    print("Engine key     = " + ENGINE_KEY)
    print("Relation       = " + RELATION)
    print("Threshold      = %.3f" % (THRESHOLD))
    print("Query          = " + QUERY)
    print("# of Tuples    = %d" % (TARGET_TUPLE_AMT))

def process_CLI():
    """Read values from cli and store in variables."""
    global CLIENT_KEY
    if len(sys.argv) > 1: CLIENT_KEY = sys.argv[1]

    global ENGINE_KEY
    if len(sys.argv) > 2: ENGINE_KEY = sys.argv[2]

    global RELATION
    if len(sys.argv) > 3: RELATION = get_relationship(int(sys.argv[3]))

    global THRESHOLD
    if len(sys.argv) > 4: THRESHOLD = float(sys.argv[4])

    global QUERY
    if len(sys.argv) > 5: QUERY = sys.argv[5].lower()

    global TARGET_TUPLE_AMT
    if len(sys.argv) > 6: TARGET_TUPLE_AMT = int(sys.argv[6])

    print_parameters()

def get_relationship(i):
    """Return relation string for integer input."""
    relationships = ["Live_In", "Located_In", "OrgBased_In", "Work_For"]
    if i < len(relationships):
        return relationships[i-1]
    return relationships[3]

if __name__ == '__main__':
    sys.exit(main())
