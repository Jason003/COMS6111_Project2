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
TARGET_TUPLE_AMT = 10

# Path to the client
STANFORD_CORENLP_PATH = "stanford-corenlp-full-2017-06-09"

# Google API query template
URL = Template("https://www.googleapis.com/customsearch/v1?key=$client_key&cx=$engine_key&q=$query")
QUERY_HISTORY = []
URL_HISTORY = []

# Maintain a global list of extracted tuples
EXTRACTED_TUPLES = []

# Relations we care about
VALID_RELATIONS = ['Live_In','Located_In','OrgBased_In','Work_For']

# Relation types we care about
REQUIRED_NERS = {
    'Live_In': ['PERSON','LOCATION'],
    'Located_In': ['LOCATION','LOCATION'],
    'OrgBased_In': ['ORGANIZATION','LOCATION'],
    'Work_For': ['PERSON','ORGANIZATION']
}
REQUIRED_RELATIONS = {
    'Live_In': ['PEOPLE','LOCATION'],
    'Located_In': ['LOCATION','LOCATION'],
    'OrgBased_In': ['ORGANIZATION','LOCATION'],
    'Work_For': ['PEOPLE','ORGANIZATION']
}

def requery():
    """Select unused, high-confidence, tuple then query and process."""
    global QUERY
    new_query = ''
    for r in EXTRACTED_TUPLES:
        q = r['r'].entities[0].value + ' ' + r['r'].entities[1].value
        if q not in QUERY_HISTORY:
            new_query = q
            break

    # out of new terms to query
    if new_query == '':
        return
    print (new_query)
    QUERY = new_query
    query()

def query():
    """Send request to Google Custom Search endpoint."""
    printIterationHeader()
    QUERY_HISTORY.append(QUERY) # Been there, done that
    url = URL.substitute(client_key = CLIENT_KEY, engine_key = ENGINE_KEY, query = QUERY)
    response = requests.get(url)
    items = response.json()["items"]
    process(items)

# Contains each iteration
def process(items):
    """Process each result from Google search."""
    global EXTRACTED_TUPLES
    raw_relations = EXTRACTED_TUPLES
    for item in items:
        # only process URLs once
        if item["link"] not in URL_HISTORY:
            print("Processing: " + item["link"])

            # Scrape site into blob
            blob = fetch_site_blob(item["link"])

            # Extract meaningful text from the blob
            text = extract_text(blob)

            if text is not None:
                # turn the extracted text into phrases
                phrases = find_query_term_occurrences(text) # (pipeline 1)

                # tag relations from the phrases
                relations = tag_relations(phrases) # (pipeline 2)
                raw_relations = raw_relations + relations

                # print outcome of this text
                print ('Relations extracted from this website: ' + str(len(relations)) + ' (Overall:' + str(len(raw_relations)) + ')')

            # Been there, done that
            URL_HISTORY.append(item['link'])
        else:
            print('Program already processed text content from this web site; moving to the next one...')

    # Prune by confidence and duplicates
    print ('Pruning relations below threshold...')
    EXTRACTED_TUPLES = prune_relations(raw_relations)
    print ('Number of tuples after pruning: ' + str(len(EXTRACTED_TUPLES)))
    printAllRelations()

    # Find new tuples and requery if we haven't found 0 or K+
    if len(EXTRACTED_TUPLES) >= TARGET_TUPLE_AMT or len(EXTRACTED_TUPLES) == 0:
        return
    else:
        requery()

# return only high confidence, unique relations
def prune_relations(relations):
    pruned = {}
    unique = set()

    for r in relations:
        # check confidence before wasting any more time on this relation
        confidence = float(r['r'].probabilities[RELATION])
        if  confidence >= THRESHOLD:

            # make sure there are 2 entities before wasting any more time on this relation
            if len(r['r'].entities) == 2:

                # normalize order
                entities = ()
                if r['r'].entities[0].type == REQUIRED_RELATIONS[RELATION][0]:
                    entities = (r['r'].entities[0].value, r['r'].entities[0].type, r['r'].entities[1].value, r['r'].entities[1].type)
                else:
                    entities = (r['r'].entities[1].value, r['r'].entities[1].type, r['r'].entities[0].value, r['r'].entities[0].type)

                if entities not in unique:
                    # new, simply add
                    pruned[entities] = r
                else:
                    # repeat, choose higher confidence
                    if confidence > float(pruned[entities]['r'].probabilities[RELATION]):
                        pruned[entities] = r

                unique.add(entities)

    # return sorted by confidence
    sorted_x = sorted(pruned.items(), key=lambda v:float(v[1]['r'].probabilities[RELATION]), reverse=True)

    # drop keys and just return relations
    sortedRelations = []
    for s in sorted_x:
        sortedRelations.append(s[1])
    return sortedRelations

# Text-extraction
def extract_text(blob):
    """Separate text from markdown."""
    html = BeautifulSoup(blob, "html.parser")

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
        # strip spaces and certain symbols, add the period back to the end of each sentence
        text = []
        for chunk in chunks:
            if chunk:
                text.extend([(re.sub('[ ^`]*$','',re.sub('^[ ^`]*','',s)) + '.') for s in re.sub(r'(\.)([^a-zA-Z0-9\.])',r'\1 \2',chunk).split('. ')])

        return text
    else:
        print('Program could not extract text content from this web site; moving to the next one...')
        return None

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

# Filter sentences after pipeline 1:
#   Only returns sentences if they contain each of the required 'ners'
def eval_sentence(s):
    sentence = ''
    ners_found = [False] * len(REQUIRED_NERS[RELATION])

    # For every word (token) in sentence
    for token in s.tokens:

        # Record valid ners as found
        for i in range(len(REQUIRED_NERS[RELATION])):
            if REQUIRED_NERS[RELATION][i] == token.ner and not ners_found[i]:
                ners_found[i] = True
                # break in case two of same ners needed (like for 'Located_In')
                break

        # Record word
        sentence += ' ' + token.word

    if all(ners_found):
        return sentence
    else:
        return False

# Records the relations
def record_relations(sentence):
    returned_relations = []

    for relation in sentence.relations:

        # are the found relation types valid for the chosen relation?  Also record entities
        ners_found = [False] * len(REQUIRED_RELATIONS[RELATION])
        entities = []
        for entity in relation.entities:
            entities.append(entity.value)
            for i in range(len(REQUIRED_RELATIONS[RELATION])):
                if REQUIRED_RELATIONS[RELATION][i] == entity.type and not ners_found[i]:
                    ners_found[i] = True
                    break

        if not all(ners_found):
            continue

        # Get key of the max-confidence relation types (probabilities returned in a dict)
        max_confidence_relations = [k for k,v in relation.probabilities.items() if v == max(relation.probabilities.values())]

        if RELATION not in max_confidence_relations:
            continue

        # Have we seen this relation yet?
        seen_better_relation = False
        for r_r in returned_relations:
            returned_entities = []
            for entity in r_r['r'].entities:
                returned_entities.append(entity.value)
            if returned_entities.sort() == entities.sort():
                if r_r['r'].probabilities[RELATION] >= relation.probabilities[RELATION]:
                    seen_better_relation = True
                else:
                    returned_relations.remove(r_r)

        if seen_better_relation:
            continue

        # ========================================================
        # If we make it this far, we want to record this relation!

        # Join words into full sentence
        s = ''
        for token in sentence.tokens:
            s += token.word + ' '

        # Record sentence and relation
        returned_relations.append({'s':s,'r':relation})

    # print found valid relations
    printRelations(returned_relations)

    return returned_relations

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
    relations = []
    for sentence in doc.sentences:
        relations.extend(record_relations(sentence))

    return relations

# Scraper: returns document blob
def fetch_site_blob(url):
    """Scrape HTML from URL."""
    doc = requests.get(url, timeout=10)
    return doc.text

def progress_check():
    """Done if k matches."""
    pass

def main():
    """Main entry point for the script."""
    process_CLI()
    query()
    print ('Program reached ' + str(len(EXTRACTED_TUPLES)) + ' number of tuples. Shutting down...')

def print_parameters():
    print("Parameters:")
    print("Client key     = " + CLIENT_KEY)
    print("Engine key     = " + ENGINE_KEY)
    print("Relation       = " + RELATION)
    print("Threshold      = %.2f" % (THRESHOLD))
    print("Query          = " + QUERY)
    print("# of Tuples    = %d" % (TARGET_TUPLE_AMT))

def printIterationHeader():
    iteration = (len(QUERY_HISTORY) + 1)
    template = "=========== Iteration: %d - Query: " + QUERY + " ==========="
    print(template % (iteration))

def printRelations(relations):
    for r in relations:
        print ('=============== EXTRACTED RELATION ===============')
        print ('Sentence: ' + r['s'].strip())
        s = ''
        s += 'RelationType: ' + RELATION
        s += (' | Confidence= %f ' % float(r['r'].probabilities[RELATION]))
        for e_index in range(len(r['r'].entities)):
            s += ' | EntityType' + str(e_index+1) + '= ' + r['r'].entities[e_index].type
            s += ' | EntityValue' + str(e_index+1) + '= ' + r['r'].entities[e_index].value
        print (s)
        print ('============== END OF RELATION DESC ==============')

def printAllRelations():
    print('================== ALL RELATIONS =================')
    for r in EXTRACTED_TUPLES:
        s = ''
        s += 'Relation Type: ' + RELATION
        s += (' | Confidence= %.2f ' % float(r['r'].probabilities[RELATION]))
        for e_index in range(len(r['r'].entities)):
            s += '	 | Entity #' + str(e_index+1) + ': ' + r['r'].entities[e_index].value + '(' + r['r'].entities[e_index].type + ')'
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
    print('Invalid relation!  Defaulting to Work_For...')
    return VALID_RELATIONS[3]

if __name__ == '__main__':
    sys.exit(main())
