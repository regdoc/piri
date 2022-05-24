from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import numpy
import rdflib
import spacy

PYPIRI_PATH = "D:/Daten/Uni/Promotion/"

TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-LWDA2021-REDUCED/"

XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/Scorpion/PiriIEwebAthenTypeSystem/"

#XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/Scorpion/outputScorpionNER01/"

XMI_GOLD_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-XMI-GOLD/"

LOG_OUTPUT_PATH = ""

LOG_OUTPUT_FILE = ""

ONTOLOGY_ANNOTATION_INPUT_FILE = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/UIMA/PiriAnnotator01/ontology.rdf"

ONTOLOGY_INPUT_FILE = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/UIMA/PiriAnnotator01/ontology.rdf"

NS_PIRI = "http://www.angesagt-gmbh.de/piri#"

NS_REGDOC = "http://www.angesagt-gmbh.de/regdoc#"

NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#"

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

# load spacy nlp pipeline
nlp = spacy.load("en_core_web_sm")

# create a Graph
piriOnotology = rdflib.Graph()

# parse in an RDF file hosted on the Internet
result = piriOnotology.parse(ONTOLOGY_INPUT_FILE)

# print the number of "triples" in the Graph
print("graph has {} statements.".format(len(piriOnotology)))

# query for incident labels
queryForIncidents = piriOnotology.query(
    "PREFIX piri: <" + NS_PIRI + "> PREFIX rdfs: <" + NS_RDFS + "> PREFIX rdf: <" + NS_RDF + ">" +
    "SELECT ?x ?prefLabel WHERE {" +
    "	    ?x piri:broader* piri:incidentRootNuclearSafety ." +
    "	    ?x piri:prefLabel ?prefLabel ." +
    "	    FILTER(LANGMATCHES(LANG(?prefLabel), 'en')) ." +
    "}")

# query for measure labels
queryForMeasures = piriOnotology.query(
    "PREFIX piri: <" + NS_PIRI + "> PREFIX rdfs: <" + NS_RDFS + "> PREFIX rdf: <" + NS_RDF + ">" +
    "SELECT ?x ?prefLabel WHERE {" +
    "	    ?x piri:broader* piri:measureRootNuclearSafety ." +
    "	    ?x piri:prefLabel ?prefLabel ." +
    "	    FILTER(LANGMATCHES(LANG(?prefLabel), 'en')) ." +
    "}")

config = {
    # "phrase_matcher_attr": None,
    # "validate": True,
    # "overwrite_ents": True,
    # "ent_id_sep": "||",
}

# create entity ruler
ruler = nlp.add_pipe("entity_ruler", config=config)

joinedQueries = []
incidentQuery = []
measureQuery = []
preventiveMeasureQuery = []
reactiveMeasureQuery = []

# iterate over found labels
for row in queryForIncidents:
    joinedQueries.append(str(row.prefLabel))
    incidentQuery.append(str(row.prefLabel))
    #print(row.prefLabel + " added to joinedQueries")

for row in queryForMeasures:
    joinedQueries.append(str(row.prefLabel))
    measureQuery.append(str(row.prefLabel))
    #print(row.prefLabel + " added to joinedQueries")

# get alle semantic concepts of basic piri ontology, incidents and measures
def getPiriOntologyConcepts():
    return joinedQueries

# get incidents from piri ontology
def getPiriOntologyIncidents():
    return incidentQuery

# get measures from piri ontology
def getPiriOntologyMeasures():
    return measureQuery

# get preventive measures from piri ontology
def getPiriOntologyPreventiveMeasures():
    return joinedQueries

# get reactive measures from piri ontology
def getPiriOntologyReactiveMeasures():
    return joinedQueries

# get available infos for concept label
def getPiriOntologyConceptInfo(conceptLabel):
    joinedOutput = []
    print(conceptLabel)
    # query for measure labels
    queryForConcept = piriOnotology.query(
        "PREFIX piri: <" + NS_PIRI + "> PREFIX rdfs: <" + NS_RDFS + "> PREFIX rdf: <" + NS_RDF + ">" +
        "SELECT ?x ?altLabel ?definition WHERE {" +
        "	    ?x piri:prefLabel '" + str(conceptLabel) + "'@en ." +
        "	    OPTIONAL { ?x piri:altLabel ?altLabel . }" +
        "	    OPTIONAL { ?x piri:definition ?definition . }" +
        "	    FILTER(LANGMATCHES(LANG(?altLabel), 'en')) ." +
        "	    FILTER(LANGMATCHES(LANG(?definition), 'en')) ." +
        "}")

    allAltLabels = ""
    definition = ""

    for rowC in queryForConcept:
        joinedOutput.append(str(rowC.definition))
        #print(str(row2.definition))
        #print(str(row2.x))
        allAltLabels = rowC.altLabel
        definition = rowC.definition

    output_string = "preferred Label: " + str(conceptLabel) + "\n alternative Label: " + str(allAltLabels) + "\n definition: " + str(definition)

    return output_string

# get available infos for concept label
def getPiriOntologyConceptSchemes():
    joinedOutput = []

    # query for concept schemes
    queryForConcept = piriOnotology.query(
        "PREFIX piri: <" + NS_PIRI + "> PREFIX rdfs: <" + NS_RDFS + "> PREFIX rdf: <" + NS_RDF + ">" +
        "SELECT ?x WHERE {" +
        "	    ?x rdf:type piri:ConceptScheme ." +
        "}")

    for rowCS in queryForConcept:
        joinedOutput.append(str(rowCS.x))

    return joinedOutput

def getDocumentHomogeneityMatrix(allInformationUnits):
    matrixDimension = len(allInformationUnits)
    homogeneityMatrix = numpy.empty((matrixDimension, matrixDimension))

    i = 0
    j = 0

    for currentInformationUnit1 in allInformationUnits:
        for currentInformationUnit2 in allInformationUnits:
            homogeneityMatrix[i][j] = SequenceMatcher(None, currentInformationUnit1, currentInformationUnit2).ratio()
            i += 1
        j += 1

    return homogeneityMatrix

def getConceptEntitySimilarityMatrix(numberOfOntologyConcpets, numberOfInformationUnits, languageModel):
    #matrixDimensionX = len(allSemanticConcepts)
    #print(str(matrixDimensionX))
    #matrixDimensionY = len(allInformationUnits)
    #print(str(matrixDimensionY))
    similarityMatrix = numpy.empty([numberOfOntologyConcpets, numberOfInformationUnits])

    #i = 0
    #j = 0

    for currentOntologyConcept in range(numberOfOntologyConcpets):
        for currentInformationUnit in range(numberOfInformationUnits):
            similarityMatrix[currentOntologyConcept][currentInformationUnit] = cosine_similarity([languageModel[currentOntologyConcept]],[languageModel[numberOfOntologyConcpets+currentInformationUnit]])
            print("oC:"+str(currentOntologyConcept)+" iU:"+str(currentInformationUnit)+" sim:"+str(similarityMatrix[currentOntologyConcept][currentInformationUnit]))
            #i += 1
        #i = 0
        #j += 1

    return similarityMatrix
