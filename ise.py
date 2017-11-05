#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import requests
import re

from bs4 import BeautifulSoup
from string import Template
from NLPCore import NLPCoreClient

# Configuration variables
CLIENT_KEY = "AIzaSyCATX_cG2DgsJjFtCdgcThfR2xaH7MSMl0"
ENGINE_KEY = "010829534362544137563:ndji7c0ivva"
RELATION = "Work_For"
THRESHOLD = 0.35
QUERY = "bill gates microsoft"
TARGET_TUPLE_AMT = 3
K = 10

# Path to the client
STANFORD_CORENLP_PATH = "stanford-corenlp-full-2017-06-09"

# Google API query template
URL = Template("https://www.googleapis.com/customsearch/v1?key=$client_key&cx=$engine_key&q=$query")
URL_HISTORY = []

# List of extracted tuples
EXTRACTED_TUPLES = []

# List of relations we care about
VALID_RELATIONS = ['Live_In','Located_In','OrgBased_In','Work_For']
VALID_ENTITIES = {
    'Live_In': [],
    'Located_In': [],
    'OrgBased_In': [],
    'Work_For': ['PEOPLE','ORGANIZATION']
}

def requery():
    """Select unused, high-confidence, tuple then query and process."""
    # TODO
    # check if done
    # otherwise, find new query term
    pass

def query():
    """Send request to Google Custom Search endpoint."""
    printIterationHeader()
    url = URL.substitute(client_key = CLIENT_KEY, engine_key = ENGINE_KEY, query = QUERY)
    response = requests.get(url)
    # print(response.json()) # TESTING
    items = response.json()["items"]
    process(items)

# TODO remove testing printouts
def process(items):
    """Process each result from Google search."""
    for item in items:
        # only process URLs once
        if item["link"] not in URL_HISTORY:
            print("Processing: " + item["link"])

            # Scrape site into blob
            print('fetching blob...') # TESTING
            blob = fetch_site_blob(item["link"])

            # Extract meaningful text from the blob
            print('extracting text...') # TESTING
            text = extract_text(blob)

            if text is not None:
                # turn the extracted text into phrases
                print('finding query term occurrences...') # TESTING
                phrases = find_query_term_occurrences(text) # (pipeline 1)

                # tag relations from the phrases
                print('tagging relations...') # TESTING
                tag_relations(phrases) # more TODO

            # Been there, done that
            URL_HISTORY.append(item['link'])
        else:
            print("--- REMOVE FROM HERE ---")
            print("skip " + item["link"])
            print ("--- TO HERE ---")

    # 3.d) filter_by_confidence TODO

    # 4. find new tuples TODO

    if len(EXTRACTED_TUPLES) >= K:
        # 5. check if we have k tuples TODO
        pass
    else:
        # 6. otherwise requery
        requery()
    pass

# TODO: Alex
# Text-extraction
def extract_text(blob):
    """Separate text from markdown."""
    html = BeautifulSoup(blob, "html.parser")

    # TODO there are probably opportunites to improve the code below
    body = html.find('body')

    if body is not None:
        # remove any script or style elements
        for chunk in body(["script", "style"]):
            chunk.extract()

        # get raw text of web page body
        rawText = body.get_text()

        # reduce whitespace
        lines = (line.strip() for line in rawText.splitlines())

        # break multi-headlines into a single line
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

        # split sentences on periods that are not followed by an alphanumeric or another period
        # add the period back to the end of each sentence
        text = []
        for chunk in chunks:
            if chunk:
                text.extend([(s + '.') for s in re.sub(r'(\.)([^a-zA-Z0-9\.])',r'\1 \2',chunk).split('. ')])

        return text
    else:
        print('Cannot retrieve web page!  Skipping...')
        return None

# helper method to print sentences from string
def printSentence(s):
    str = ''
    for tkn in s.tokens:
        str += tkn.word + ' '
    print(str[:-1])

def find_query_term_occurrences(text):
    """Annotate text with the Stanford CoreNLP."""
    client = NLPCoreClient(STANFORD_CORENLP_PATH)
    properties = {
        "annotators": "",
        "parse.model": "edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz",
        "ner.useSUTime": "0"
    }

    # annotate first pipeline
    properties["annotators"] = "tokenize,ssplit,pos,lemma,ner"
    doc = client.annotate(text=text, properties=properties)

    # find sentences with matching tokens from query
    eligiblePhrases = []
    for sentence in doc.sentences:
        s = eval_sentence(sentence)
        if s is not False:
            eligiblePhrases.append(s)

    return eligiblePhrases

# Looks for sentences which contain all of the query terms
def eval_sentence(s):
    sentence = ''
    queryTokens = QUERY.split(' ')
    for token in s.tokens:
        sentence += ' ' + token.word
        if token.word.lower() in queryTokens:
            queryTokens.remove(token.word.lower())
    if (len(queryTokens) == 0):
        # print('True: ' + sentence) # TESTING
        return sentence
    else:
        # print('False: ' + sentence) # TESTING
        return False

# Records the relations
# TODO: record in global params, change printouts to the format of example
def record_relation(sentence, relation, testing = False):

    # Join words into full sentence
    s = ''
    for token in sentence.tokens:
        s += token.word + ' '

    # Define relation
    index = 0
    rObj = {}
    for entity in relation.entities:
        index += 1
        if entity.type == 'O': # don't want these types
            return
        else:
            key = 'value' + str(index)
            rObj[key] = entity.value
            key = 'type' + str(index)
            rObj[key] = entity.type

    for r in VALID_RELATIONS:
        if r in relation.probabilities and r == RELATION:
            rObj['confidence'] = relation.probabilities[r]

    # Print relation record
    print ('=============== EXTRACTED RELATION ===============')
    print ('Sentence: ' + s)
    printRelationObj(rObj)
    print ('============== END OF RELATION DESC ==============')


# Pipeline 2
def tag_relations(phrases):
    client = NLPCoreClient(STANFORD_CORENLP_PATH)
    properties = {
        "annotators": "",
        "parse.model": "edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz",
        "ner.useSUTime": "0"
    }

    # annotate second pipeline
    properties["annotators"] = "tokenize,ssplit,pos,lemma,ner,parse,relation"
    doc = client.annotate(text=phrases, properties=properties)

    # Iterate through all relations, evaluate and print and record

    for sentence in doc.sentences:
        for relation in sentence.relations:
            record_relation(sentence, relation, testing=True)

# Scraper: returns document blob
def fetch_site_blob(url):
    """Scrape HTML from URL."""
    doc = requests.get(url, timeout=10)
    return doc.text

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

    print("Finished.")

def print_parameters():
    print("Parameters:")
    print("Client key     = " + CLIENT_KEY)
    print("Engine key     = " + ENGINE_KEY)
    print("Relation       = " + RELATION)
    print("Threshold      = %.3f" % (THRESHOLD))
    print("Query          = " + QUERY)
    print("# of Tuples    = %d" % (TARGET_TUPLE_AMT))

def printIterationHeader():
    iteration = (len(URL_HISTORY) + 1)
    template = "=========== Iteration: %d - Query: " + QUERY + " ==========="
    print(template % (iteration))

def printRelationObj(r):
    s = ''
    s += 'RelationType: ' + RELATION
    s += (' | Confidence= %f ' % float(r['confidence']))
    s += ' | EntityType1= ' + r['type1']
    s += ' | EntityValue1= ' + r['value1']
    s += ' | EntityType2= ' + r['type2']
    s += ' | EntityValue2= ' + r['value2']
    print(s)

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
    if i < len(VALID_RELATIONS):
        return VALID_RELATIONS[i-1]
    return VALID_RELATIONS[3]

if __name__ == '__main__':
    sys.exit(main())
