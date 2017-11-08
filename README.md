# COMS6111_Project2

* Project Group 21
* Alexander Castleton: awc2134
* Justin (Max) Pugliese: jp3571

## Files in Submission

* ise.py: The python script that runs everything
* transcript.txt: A reference to the printouts for the execution of: python ise.py 4 0.35 "bill gates microsoft" 10
* README.md: this file
* Stanford-corenlp-full-2017/ directory and files
* data.py, data.pyc: defines the data structure that is used
* NLPCore.py, NLPCore.pyc
* input.txt, input.txt.xml: These files just need to exist for the CoreNLP package to work

## Project Dependencies
* BeautifulSoup
* Stanford-corenlp-full-2017 on the same path as `ise.py`
* Python 3+

## Package-Installation Commands on Ubuntu 14.04 Google Cloud VM

* apt-get install python-setuptools <br/>
* apt-get install python3-pip <br/>
* pip3 install bs4 <br/>
Installing Java...
* add-apt-repository ppa:webupd8team/java <br/>
* apt update; sudo apt install oracle-java8-installer <br/>
Once those packages are installed, two more packages need to be extracted:
* This assignment
* Standford CoreNLP package, downloaded at https://stanfordnlp.github.io/CoreNLP/
  * Unfortunately, there is no easier way of doing this. (You should just be using our VM anyway!)

## Connecting to the Virtual Machine

External IP: 35.185.57.0 <br/>
Username: project2 <br/>
password: passw0rd <br/>

ssh project2@35.185.57.0 <br/>
passw0rd

## Running the Code

cd /home/project2/COMS6111_Project2 <br/>
python3 ise.py AIzaSyCATX_cG2DgsJjFtCdgcThfR2xaH7MSMl0 010829534362544137563:ndji7c0ivva \<relation\> \<threshold\> \<query\> \<K\>

## Algorithm Description and Design

* **Query Google**: With the given query
* For each returned web page, if we have not visited it previously:
  * **Extract text**: from web page using BeautifulSoup.  Split sentences by line and periods that are not followed by an alpha-numeric or another period.
  * **Pipeline 1**: Uses Stanford NLPCore.  Runs with annotators: "tokenize,ssplit,pos,lemma,ner".
  * **Filter Sentences**: Filter out sentences based on results of Pipeline 1.  Only keep sentences that contain each of the required relation types necessary for the chosen relation (found in the "ner" attribute on each entity).
  * **Pipeline 2**: Runs with annotators: "tokenize,ssplit,pos,lemma,ner,parse,relation"
  * **Filter Relations**: 3 Criteria on each relation returned by Pipeline 2:
    * Entity relation types (ORGANIZATION, PERSON, LOCATION, etc) must be valid for the chosen relation (Work_For must refer to a PERSON and an ORGANIZATION).
    * The chosen relation must have the highest confidence among the possible relations for those entities.
    * We must not duplicate relation entities for a single sentence.  If we have a duplicate, take only the relation with the higher confidence.
* **Prune Relations**: Keep only highest confidence unique relation entities (across all returned pages so far) that also have confidence above our given threshold.
* **Evaluation**: If we have K+ or 0 found tuples from our relations, return them and we are done.  Otherwise we re-query.
* **Re-Query**: Return to the first step with a new query.  Construct the new query with the highest-confidence tuple from our returned tuples that we have not already queried.  If we cannot, we are done.

##

Custom Search API key:<br/>
`AIzaSyCATX_cG2DgsJjFtCdgcThfR2xaH7MSMl0`

Search Engine ID:<br/>
`010829534362544137563:ndji7c0ivva`

Sample exec cmd:<br/>
