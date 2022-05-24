# transforms folder of webATHEN annotated xmi documents into one ontology document (rdf ttl)

import string

import rdflib
import os

from sentence_transformers import SentenceTransformer
from spacy.tokens import Span
from uima.PyCAS import PyCAS
from pathlib import Path

import PiriOntologyTools
import incidentRules
import measureRules
import PiriMethods

import spacy
from spacy.matcher import PhraseMatcher, Matcher

from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import FOAF, RDF, Namespace

PYPIRI_PATH = "D:/Daten/Uni/Promotion/"

#XMI_GOLD_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-XMI-GOLD/"
XMI_GOLD_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/Scorpion/PiriIEwebAthenTypeSystem/"

LOG_OUTPUT_PATH = ""

LOG_OUTPUT_FILE = ""

#ONTOLOGY_ANNOTATION_INPUT_FILE = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/UIMA/PiriAnnotator01/ontology.rdf"

NS_PIRI = "http://www.piri-safety.com/piri#"

NS_PIRINU = "http://www.piri-safety.com/pirinu#"

NS_PIRIDO= "http://www.piri-safety.com/pirido#"

NS_REGDOC = "http://www.piri-safety.com/regdoc#"

NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#"

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

#ANNOTATION_SCHEME = "GoldAnnotationIAEA"
ANNOTATION_SCHEME = "Experiment001IAEA"

#ONTOLOGY_NAME = "OntologyGoldAnnotationIAEA"
ONTOLOGY_NAME = "OntologyExperiment001IAEA"

IU_ID_SPACE = "1111"

# load spacy nlp pipeline
nlp = spacy.load("en_core_web_sm")

# create a Graph
piriOntology = rdflib.Graph()

# parse in an RDF file hosted on the Internet
#result = piriOntology.parse(ONTOLOGY_ANNOTATION_INPUT_FILE)

#piriOntology.bind("piri", NS_PIRI)

piri = Namespace(NS_PIRI)

# print the number of "triples" in the Graph
#print("graph has {} statements.".format(len(piriOntology)))

outputOntology = Graph()
outputOntology.bind("piri", piri)

documentCounter = 0

# get all documents from corpus
with os.scandir(XMI_GOLD_INPUT_PATH) as xmiIt:
    for entry in xmiIt:
        if entry.name.endswith(".xmi") and entry.is_file():
            print(entry.name, entry.path)
            documentCounter += 1

            # read document content
            with open(entry.path, encoding="utf8") as currentDocText:
                #lines = currentDocText.read()
                #lines.encode('utf-8').decode('unicode-escape')
                # print(lines)
                #currentDocObject = nlp(lines)

                # get GOLD document for current document
                # create CAS for current GOLD document
                goldxmi = entry.name
                #.replace(".pdf", "").replace(".txt", "") + ".xmi"
                goldDocumentName = entry.name.replace(".pdf", "").replace(".txt", "").replace(".xmi", "").replace("_", "-")
                print(goldxmi)
                goldpath = XMI_GOLD_INPUT_PATH + goldxmi
                print(goldpath)
                goldfile = Path(goldpath)

                if (goldfile.exists()):
                    goldCas = PyCAS.from_xmi(
                        path=goldpath,
                        path_to_typesystem="D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/ARIESTypesystem.xml")

                    docTextFromXMI = goldCas.get_sofa()
                    currentDocObjectXMI = nlp(str(docTextFromXMI))

                    # loop through incident annotations and print their text
                    datatype = "de.uniwue.aries.ie.IEEntityGold"
                    datatypeRelation = "de.uniwue.aries.ie.IERelationGold"

                    annoCounter = 0
                    allGoldEntities = goldCas.get_fs_of_type(datatype)
                    allGoldRelations = goldCas.get_fs_of_type(datatypeRelation)

                    # calculating language model once to have it everywhere accessible
                    # problem: integrate all entities with id???
                    # list of all entities from ontology, then list of alle information units
                    model = SentenceTransformer('bert-base-nli-mean-tokens')
                    #semanticConceptList = [str(semanticConcept)]
                    allSemanticConcepts = PiriOntologyTools.getPiriOntologyConcepts()

                    allGoldEntitiesText = []
                    for goldEntity in allGoldEntities:
                        allGoldEntitiesText.append(str(goldEntity.get_covered_text()))

                    allSentences = allSemanticConcepts + allGoldEntitiesText
                    print(str(len(allSentences)))
                    sentence_embeddings = model.encode(allSentences)
                    sentence_embeddings.shape
                    currentSimilarityMatrix = PiriOntologyTools.getConceptEntitySimilarityMatrix(len(allSemanticConcepts), len(allGoldEntitiesText), sentence_embeddings)
                    # sentence_embeddings.reshape(-1, 1)

                    goldEntityCount = 0

                    for goldEntity in allGoldEntities:
                        print(str(goldEntityCount) + " goldEntity: "+str(goldEntity.begin)+" - "+str(goldEntity.end)+" - "+goldEntity["owlid"]+" id:"+str(goldEntity.id))
                        print(goldEntity.get_covered_text())

                        currentInformationUnit = URIRef(NS_PIRI+"informationUnit-"+IU_ID_SPACE+"-"+str(documentCounter)+"-"+str(goldEntity.id))

                        # search for most similar class
                        similarLabelID = PiriMethods.getMostSimilarPiriClassIDFromSimilarityMatrix(goldEntityCount, currentSimilarityMatrix)
                        print("similarLabel: " + str(similarLabelID[0]))
                        print("similarLabelallSentences: " + str(allSentences[similarLabelID[0]]))
                        similarLabel = allSentences[similarLabelID[0]]

                        outputOntology.add((currentInformationUnit, RDF.type, piri.InformationUnit))
                        outputOntology.add((currentInformationUnit, piri.hasID, Literal(str(goldEntity.id))))
                        outputOntology.add((currentInformationUnit, piri.mostProbableLabel, Literal(str(similarLabel))))
                        outputOntology.add((currentInformationUnit, piri.probableAltLabel, Literal(str(similarLabel))))
                        outputOntology.add((currentInformationUnit, piri.inScheme, piri.nuclearSafetyRegulatoryDocuments))
                        outputOntology.add((currentInformationUnit, piri.inScheme, piri.annotationScheme+ANNOTATION_SCHEME))
                        outputOntology.add((currentInformationUnit, piri.broader, piri.regulatoryDocumentNuclearSafety+goldDocumentName))
                        outputOntology.add((currentInformationUnit, piri.hasPhrase, Literal(goldEntity.get_covered_text())))
                        outputOntology.add((currentInformationUnit, piri.hasAnnotation, rdflib.term.URIRef(NS_PIRI+goldEntity["owlid"]+"NuclearSafety")))
                        outputOntology.add((currentInformationUnit, piri.hasOffsetFrom, Literal(str(goldEntity.begin))))
                        outputOntology.add((currentInformationUnit, piri.hasOffsetTo, Literal(str(goldEntity.end))))

                        annoCounter += 1
                        goldEntityCount += 1

                    for goldRelation in allGoldRelations:
                        print("goldRelation: "+str(goldRelation["EntityFrom"].id)+" - "+str(goldRelation["EntityTo"].id))

                        queryForEntityIDFrom = outputOntology.query(
                            "PREFIX piri: <" + NS_PIRI + "> PREFIX rdfs: <" + NS_RDFS + "> PREFIX rdf: <" + NS_RDF + ">" +
                            "SELECT ?x WHERE {" +
                            "	    ?x piri:broader piri:regulatoryDocumentNuclearSafety"+str(goldDocumentName)+" ." +
                            "	    ?x piri:hasID '"+str(goldRelation["EntityFrom"].id)+"' ." +
                            "}")

                        print("query")
                        print(str(piri.regulatoryDocumentNuclearSafety)+str(goldDocumentName))

                        for row in queryForEntityIDFrom:
                            print("resource: "+str(row.x))
                            entityFrom = row.x

                        queryForEntityIDTo = outputOntology.query(
                            "PREFIX piri: <" + NS_PIRI + "> PREFIX rdfs: <" + NS_RDFS + "> PREFIX rdf: <" + NS_RDF + ">" +
                            "SELECT ?x WHERE {" +
                            "	    ?x piri:broader piri:regulatoryDocumentNuclearSafety" + str(goldDocumentName) + " ." +
                            "	    ?x piri:hasID '" + str(goldRelation["EntityTo"].id) + "' ." +
                            "}")

                        annotatedRelation = ""

                        if str(goldRelation["Label"]) == "hasMeasure":
                            annotatedRelation = piri.hasMeasure
                        elif str(goldRelation["Label"]) == "broader":
                            annotatedRelation = piri.broader
                        else:
                            annotatedRelation = piri.related

                        for row in queryForEntityIDTo:
                            print("resource: " + str(row.x))
                            entityTo = row.x

                        outputOntology.add((entityFrom, annotatedRelation, entityTo))

outputOntology.serialize(destination=XMI_GOLD_INPUT_PATH + ONTOLOGY_NAME+".rdf")

print(str(documentCounter)+" documents processed")