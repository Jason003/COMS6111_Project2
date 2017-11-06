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

# Path to the client
STANFORD_CORENLP_PATH = "stanford-corenlp-full-2017-06-09"

# Google API query template
URL = Template("https://www.googleapis.com/customsearch/v1?key=$client_key&cx=$engine_key&q=$query")
QUERY_HISTORY = []
URL_HISTORY = []

# List of extracted tuples
EXTRACTED_TUPLES = []

# List of relations we care about
VALID_RELATIONS = ['Live_In','Located_In','OrgBased_In','Work_For']
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
        temp = r['value1'] + ' ' + r['value2']
        if temp not in QUERY_HISTORY:
            new_query = temp
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

# TODO remove testing printouts
def process(items):
    """Process each result from Google search."""
    global EXTRACTED_TUPLES
    raw_relations = EXTRACTED_TUPLES
    for item in items:
        # only process URLs once
        if item["link"] not in URL_HISTORY:
        # if item['link'] == 'https://en.wikipedia.org/wiki/Bill_Gates': # TESTING
            print("Processing: " + item["link"])

            # Scrape site into blob
            # print('fetching blob...') # TESTING
            blob = fetch_site_blob(item["link"])

            # Extract meaningful text from the blob
            # print('extracting text...') # TESTING
            text = extract_text(blob)

            if text is not None:
                # turn the extracted text into phrases
                # print('finding query term occurrences...') # TESTING
                phrases = find_query_term_occurrences(text) # (pipeline 1)

                # tag relations from the phrases
                # print('tagging relations...') # TESTING
                relations = tag_relations(phrases) # more TODO
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

    # 4. find new tuples TODO
    if len(EXTRACTED_TUPLES) >= TARGET_TUPLE_AMT:
        return
    else:
        requery()
    pass

# return only high confidence, unique relations
def prune_relations(relations):
    uniques, pruned = set(), []
    for r in relations:
        if float(r['confidence']) >= THRESHOLD:
            v1 = r["value1"]
            v2 = r["value2"]
            if v1 not in uniques and v2 not in uniques:
                pruned.append(r)
            uniques.add(v1)
            uniques.add(v2)

    # return sorted by confidence
    return sorted(pruned, key=lambda k: k['confidence'], reverse=True)

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

    # for sentence in doc.sentences:
    #     if len(sentence.entities) == 0:
    #         print('NO entities!!!!')
    #     for entity in sentence.entities:
    #         print ('type:' + entity.type)

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
        # print('\t' + s.id + ': ' + sentence) # TESTING
        return sentence
    else:
        return False

# Records the relations
# TODO: don't record the same relation multiple times, take the higher confidence (this is pretty tricky)
def record_relations(sentence):
    returned_relations = []

    for relation in sentence.relations:
        # is this found relation valid for the chosen relation?
        ners_found = [False] * len(REQUIRED_RELATIONS[RELATION])
        for entity in relation.entities:
            for i in range(len(REQUIRED_RELATIONS[RELATION])):
                if REQUIRED_RELATIONS[RELATION][i] == entity.type and not ners_found[i]:
                    ners_found[i] = True
                    break

        # This is the correct relation type!
        if all(ners_found):
            # Join words into full sentence
            s = ''
            for token in sentence.tokens:
                s += token.word + ' '

            # Record sentence and relation
            returned_relations.append({'s':s,'r':relation})

    # TODO De-duplicate relations

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

        # for relation in sentence.relations:
        #     r = record_relation(sentence, relation)
        #     if r is not False:
        #         relations.append(r)

    return relations

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
            s += ' | EntityType' + str(e_index) + '= ' + r['r'].entities[e_index].type
            s += ' | EntityValue' + str(e_index) + '= ' + r['r'].entities[e_index].value
        print (s)
        print ('============== END OF RELATION DESC ==============')

def printAllRelations():
    print('================== ALL RELATIONS =================')
    for r in EXTRACTED_TUPLES:
        s = ''
        s += 'Relation Type: ' + RELATION
        s += (' | Confidence= %.2f ' % float(r['confidence']))
        s += '	 | Entity #1: ' + r['value1'] + '(' + r['type1'] + ')'
        s += '            	 | Entity #2: ' + r['value2'] + '(' + r['type2'] + ')'
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
