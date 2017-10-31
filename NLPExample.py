from NLPCore import NLPCoreClient

text = ["Bill Gates works at Microsoft."," Sergei works at Google."]

#path to corenlp
client = NLPCoreClient('stanford-corenlp-full-2017-06-09')
properties = {
	"annotators": "tokenize,ssplit,pos,lemma,ner",
	"parse.model": "edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz",
	"ner.useSUTime": "0"
	}
doc = client.annotate(text=text, properties=properties)
for sentence in doc.sentences:
    print ("NEW SENT")
    for token in sentence.tokens:
        print (token.word +' ')
    for dependency in sentence.dependencies:
        print ("dependency = " + dependency.value)
    for entity in sentence.entities:
        print ("entity = " + entity.value)
    print ("------")

# print(doc.tree_as_string())
