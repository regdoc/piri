# Input: XMI with Sentences classified as preventive
# Output: XMI with similar Sentences above threshold

import string

import rdflib
import os

from spacy.tokens import Span
from uima.PyCAS import PyCAS
from pathlib import Path

import PIRITypesAndPieces
import incidentRules
import measureRules

import spacy
from spacy.matcher import PhraseMatcher, Matcher

import csv

import preventiveMeasureRules
import reactiveMeasureRules

from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

data = [[]]

def getXmiEntityForSpacyEnity(spacyEntity, allXmiEntities):
    for xmiEntity in allXmiEntities:
        if (xmiEntity.begin == spacyEntity.start_char) and (xmiEntity.end == spacyEntity.end_char):
            return xmiEntity
            break

PYPIRI_PATH = "D:/Daten/Uni/Promotion/"

TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-TRAIN/"
#TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-VALIDATE/"
#TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-TEST/"

XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveTrain/"
#XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveValidate/"
#XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveTest/"

XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveSimTrain/"
#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveSimValidate/"
#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveSimTest/"

XMI_GOLD_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-XMI-GOLD/"

LOG_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/"

LOG_OUTPUT_FILE = "KI2022PreventiveSimilarity.txt"

ONTOLOGY_ANNOTATION_INPUT_FILE = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/UIMA/PiriAnnotator01/ontology.rdf"

# load spacy nlp pipeline
nlp = spacy.load("en_core_web_sm")

# create file writer
f = open(LOG_OUTPUT_PATH+LOG_OUTPUT_FILE, "w+")
f.write(LOG_OUTPUT_FILE+"\r\n")

# create a Graph
piriOnotology = rdflib.Graph()
nodeCount = 1

# parse in an RDF file hosted on the Internet
result = piriOnotology.parse(ONTOLOGY_ANNOTATION_INPUT_FILE)

# print the number of "triples" in the Graph
print("graph has {} statements.".format(len(piriOnotology)))

#getConceptEntitySimilarityMatrix(numberOfOntologyConcpets, numberOfInformationUnits, languageModel):
positivePriorPreventiveSentences = []

# first read from xmi input priory labeled preventive sentences into list

with os.scandir(XMI_INPUT_PATH) as xmiIt:
    for entry in xmiIt:
        if entry.name.endswith(".xmi") and entry.is_file():
            documentName = entry.name
            f.write("*** XMI input document name: " + str(documentName) + "\r\n")
            f.write("----------------------------------------------------------\r\n")
            documentPatz = entry.path
            print(entry.name, entry.path)

            # read document content
            with open(entry.path, encoding="utf8") as currentDocText:
                lines = currentDocText.read()
                lines.encode('utf-8').decode('unicode-escape')
                # print(lines)
                currentDocObject = nlp(lines)

                inputXMI = documentName
                print(inputXMI)
                inputXMIpath = XMI_INPUT_PATH + inputXMI
                print(inputXMIpath)
                inputXMIfile = Path(inputXMIpath)
                print(inputXMIfile)

                if (inputXMIfile.exists()):
                    # create CAS for current document
                    pycas = PyCAS.from_xmi(
                        path=inputXMIpath,
                        path_to_typesystem="D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/PIRITypesystem.xml")
                    print("inputXMI created")
                else:
                    pycas = PyCAS.empty("D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/PIRITypesystem.xml")
                    pycas.set_document_text(lines)

                # get all sentences from xmi
                allPreventiveSentencesFromXMI = pycas.get_fs_of_type(PIRITypesAndPieces.datatypePreventiveMeasureTrigger)
                positivePriorPreventiveSentences = positivePriorPreventiveSentences + allPreventiveSentencesFromXMI

positivePriorPreventiveSentencesStrings = []

f.write("number of prior sentences: "+str(len(positivePriorPreventiveSentences)) + "\r\n")

for ent in positivePriorPreventiveSentences:
    positivePriorPreventiveSentencesStrings.append(ent.get_covered_text())
    f.write("add prior sentence: "+str(ent.get_covered_text()) + "\r\n")
    f.write("----------------------------------------------------------\r\n")
    #print("entsize: "+str(ent.size()))

model = SentenceTransformer('bert-base-nli-mean-tokens')
priorSentenceEmbeddings = model.encode(positivePriorPreventiveSentencesStrings)

# get all documents from text corpus
with os.scandir(TXT_INPUT_PATH) as txtIt:
    for entry in txtIt:
        if entry.name.endswith(".txt") and entry.is_file():
            documentName = entry.name
            documentPatz = entry.path
            print(entry.name, entry.path)
            f.write("*** TXT input document name: " + str(documentName) + "\r\n")
            f.write("----------------------------------------------------------\r\n")
            # read document content
            with open(entry.path, encoding="utf8") as currentDocText:
                lines = currentDocText.read()
                lines.encode('utf-8').decode('unicode-escape')
                # print(lines)
                currentDocObject = nlp(lines)

                inputXMI = entry.name.replace("_", "-").replace(".pdf", "").replace(".txt", "") + ".xmi"
                print(inputXMI)
                inputXMIpath = XMI_INPUT_PATH + inputXMI
                print(inputXMIpath)
                inputXMIfile = Path(inputXMIpath)
                print(inputXMIfile)

                if (inputXMIfile.exists()):
                    # create CAS for current document
                    pycas = PyCAS.from_xmi(
                        path=inputXMIpath,
                        path_to_typesystem="D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/PIRITypesystem.xml")
                    print("inputXMI created")
                else:
                    pycas = PyCAS.empty("D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/PIRITypesystem.xml")
                    pycas.set_document_text(lines)

                currentSentenceStrings = []
                for sent in currentDocObject.sents:
                    currentSentenceStrings.append(sent)
                    #f.write("add current sentence: " + str(ent.get_covered_text()) + "\r\n")
                    #f.write("----------------------------------------------------------\r\n")

                currentEmbeddings = model.encode(currentSentenceStrings)

                for sentence, embedding in zip(currentDocObject.sents, currentEmbeddings):
                    #print("Sentence:", sentence)
                    #print("Embedding:", embedding)
                    for priorSentence, priorEmbedding in zip(positivePriorPreventiveSentencesStrings, priorSentenceEmbeddings):
                        #print("Sentence:", sentence)
                        #print("Embedding:", embedding)
                        sentenceSimilarity = cosine_similarity([embedding], [priorEmbedding])
                        f.write("Similarity: " + str(sentenceSimilarity) + "\r\n")
                        f.write("----------------------------------------------------------\r\n")
                        f.write("Prior Sentence: " + str(priorSentence) + "\r\n")
                        f.write("----------------------------------------------------------\r\n")
                        f.write("Current Sentence: " + str(sentence.get_covered_text()) + "\r\n")
                        f.write("----------------------------------------------------------\r\n")

                        print("Similarity: " + str(sentenceSimilarity))
                        if (sentenceSimilarity > 0.6):
                            # add new sentence to outputxmi
                            # print("entity: " + str(ent.label_) + "text: " + str(sent))

                            data.append([documentName, str(sentence), 'true'])
                            # add feature structure
                            measureTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypePreventiveExperimentTrigger)

                            # set some attributes
                            measureTag_anno["begin"] = sentence.start_char
                            measureTag_anno["end"] = sentence.end_char
                            measureTag_anno["owlid"] = "preventiveMeasureCandidate"

                            # add this feature structure into the cas
                            pycas.add_fs(measureTag_anno)

                """
                i = 0
                j = 0
                # compare current doc sentences with priory classified sentences
                for sent in currentDocObject.sents:
                    for priorsent in positivePriorPreventiveSentences:
                        sentenceSimilarity = cosine_similarity([priorSentenceEmbeddings[j]], [currentEmbeddings[i]])
                        f.write("Similarity: " + str(sentenceSimilarity) + "\r\n")
                        f.write("----------------------------------------------------------\r\n")
                        f.write("Similarity: " + str([priorSentenceEmbeddings[j]]) + "\r\n")
                        f.write("----------------------------------------------------------\r\n")
                        f.write("Similarity: " + str([currentEmbeddings[i]]) + "\r\n")
                        f.write("----------------------------------------------------------\r\n")


                        print("Similarity: " + str(sentenceSimilarity))
                        if (sentenceSimilarity > 0.9):
                            #add new sentence to outputxmi
                            #print("entity: " + str(ent.label_) + "text: " + str(sent))

                            data.append([documentName, str(sent), 'true'])
                            # add feature structure
                            measureTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypePreventiveMeasureTrigger)

                            # set some attributes
                            measureTag_anno["begin"] = sent.start_char
                            measureTag_anno["end"] = sent.end_char
                            measureTag_anno["owlid"] = "preventiveMeasureCandidate"

                            # add this feature structure into the cas
                            pycas.add_fs(measureTag_anno)
                            break
                        j += 1
                    if(i == priorSentenceEmbeddings.size-1):
                        break
                    i += 1
                """
                # store this document again
                pycas.serialize(XMI_OUTPUT_PATH + entry.name.replace(".pdf", "").replace(".txt", "").replace("_","-") + ".xmi")

f.close()
