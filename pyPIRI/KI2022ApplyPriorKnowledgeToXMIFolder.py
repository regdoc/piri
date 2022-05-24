# Input: TXT corpus
# Output: XMI with matched ontology labels, incident and measure triggers, relation triggers, co-occurence relations

import string
from os.path import exists

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




def getXmiEntityForSpacyEnity(spacyEntity, allXmiEntities):
    for xmiEntity in allXmiEntities:
        #print("xmi: " + str(xmiEntity.get_covered_text()) + str(xmiEntity.begin)+ " "+str(xmiEntity.end))
        #print("spacyEnity: " + str(spacyEntity)+ " "+ str(spacyEntity.start_char)+" "+ str(spacyEntity.end_char))
        if (xmiEntity.begin == spacyEntity.start_char) and (xmiEntity.end == spacyEntity.end_char):
            return xmiEntity
            break

PYPIRI_PATH = "D:/Daten/Uni/Promotion/"

#TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-TRAIN/"
TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-VALIDATE/"
#TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-TEST/"

#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputApplyPriorKnowledge01/"
#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPriorTrain/"
XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPriorValidate/"
#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPriorTest/"

XMI_INPUT_PATH = ""
#XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputRelationalClassifier01/"

XMI_GOLD_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-XMI-GOLD/"

LOG_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/"

LOG_OUTPUT_FILE = "KI2022ApplyPriorKnowledgt.txt"

ONTOLOGY_ANNOTATION_INPUT_FILE = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/UIMA/PiriAnnotator01/ontology.rdf"

# create file writer
f = open(LOG_OUTPUT_PATH+LOG_OUTPUT_FILE, "w+")
f.write(LOG_OUTPUT_FILE+"\r\n")

# load spacy nlp pipeline
nlp = spacy.load("en_core_web_sm")

# create a Graph
piriOnotology = rdflib.Graph()
nodeCount = 1

# parse in an RDF file hosted on the Internet
result = piriOnotology.parse(ONTOLOGY_ANNOTATION_INPUT_FILE)

# print the number of "triples" in the Graph
print("graph has {} statements.".format(len(piriOnotology)))

# query for incident labels
queryForIncidents = piriOnotology.query(
    "PREFIX piri: <" + PIRITypesAndPieces.NS_PIRI + "> PREFIX rdfs: <" + PIRITypesAndPieces.NS_RDFS + "> PREFIX rdf: <" + PIRITypesAndPieces.NS_RDF + ">" +
    "SELECT ?x ?prefLabel ?altLabel WHERE {" +
    "	    ?x piri:broader* piri:incidentRootNuclearSafety ." +
    "	    ?x piri:prefLabel ?prefLabel ." +
    "	    OPTIONAL {?x piri:altLabel ?altLabel }" +
    "	    FILTER(LANGMATCHES(LANG(?prefLabel), 'en')) ." +
    "}")

# query for measure labels
queryForMeasures = piriOnotology.query(
    "PREFIX piri: <" + PIRITypesAndPieces.NS_PIRI + "> PREFIX rdfs: <" + PIRITypesAndPieces.NS_RDFS + "> PREFIX rdf: <" + PIRITypesAndPieces.NS_RDF + ">" +
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

# iterate over found labels
for row in queryForIncidents:
    ruler.add_patterns([{"label": "INCIDENT", "pattern": str(row.prefLabel)}])
    f.write("incident label added: "+str(row.prefLabel)+"\r\n")
    # check if alt label exists
    f.write("incident alt label added: " + str(row.altLabel) + "\r\n")

for row in queryForMeasures:
    ruler.add_patterns([{"label": "MEASURE", "pattern": str(row.prefLabel)}])
    f.write("measure label added: " + str(row.prefLabel) + "\r\n")

for text in incidentRules.incidentRules01:
    # print(str(text))
    ruler.add_patterns([{"label": "INCIDENTTRIGGER", "pattern": str(text)}])
    f.write("incident pattern added: " + str(text) + "\r\n")

for text in measureRules.measureRules01:
    # print(str(text))
    ruler.add_patterns([{"label": "MEASURETRIGGER", "pattern": str(text)}])
    f.write("measure pattern added: " + str(text) + "\r\n")

# patterns = [nlp.make_doc(text) for text in measureRules.measureRules01]
# measureMatcher.add("MEASURE", patterns)

# get all documents from text corpus
with os.scandir(TXT_INPUT_PATH) as txtIt:
    for entry in txtIt:
        if entry.name.endswith(".txt") and entry.is_file():
            print(entry.name, entry.path)

            # read document content
            with open(entry.path, encoding="utf8") as currentDocText:
                lines = repr(currentDocText.read())
                lines.encode('utf-8').decode('unicode-escape')
                # print(lines)
                currentDocObject = nlp(lines)

                inputXMI = entry.name.replace("_", "-").replace(".pdf", "").replace(".txt", "") + ".xmi"
                #print(inputXMI)
                inputXMIpath = XMI_INPUT_PATH + inputXMI
                #print(inputXMIpath)
                inputXMIfile = Path(inputXMIpath)
                print(inputXMIfile)

                if (inputXMIfile.exists()):
                    # create CAS for current document
                    pycas = PyCAS.from_xmi(
                        path=inputXMIpath,
                        path_to_typesystem="D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/PIRITypesystem.xml")
                    print("Input XMI updated")
                else:
                    pycas = PyCAS.empty("D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/PIRITypesystem.xml")
                    pycas.set_document_text(lines)
                    print("New XMI created")

                ############################################
                # get all labels and look for co-occurrence annotate relation
                ############################################
                for ent in currentDocObject.ents:

                    # print("entity: " + str(ent.label_) + "text: " + str(ent.text))

                    if (ent.label_ == "INCIDENT"):
                        # add feature structure
                        incidentTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypeIncident)

                        # set some attributes
                        incidentTag_anno["begin"] = ent.start_char
                        incidentTag_anno["end"] = ent.end_char
                        incidentTag_anno["owlid"] = "incidentRoot"

                        # add this feature structure into the cas
                        pycas.add_fs(incidentTag_anno)

                    if (ent.label_ == "MEASURE"):
                        # add feature structure
                        measureTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypeMeasure)

                        # set some attributes
                        measureTag_anno["begin"] = ent.start_char
                        measureTag_anno["end"] = ent.end_char
                        measureTag_anno["owlid"] = "measureRoot"

                        # add this feature structure into the cas
                        pycas.add_fs(measureTag_anno)

                    if (ent.label_ == "INCIDENTTRIGGER"):
                        # add feature structure
                        incidentTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypeIncidentTrigger)

                        # set some attributes
                        incidentTag_anno["begin"] = ent.start_char
                        incidentTag_anno["end"] = ent.end_char
                        incidentTag_anno["owlid"] = "incidentRoot"

                        # add this feature structure into the cas
                        pycas.add_fs(incidentTag_anno)

                    if (ent.label_ == "MEASURETRIGGER"):
                        # add feature structure
                        measureTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypeMeasureTrigger)

                        # set some attributes
                        measureTag_anno["begin"] = ent.start_char
                        measureTag_anno["end"] = ent.end_char
                        measureTag_anno["owlid"] = "measureRoot"

                        # add this feature structure into the cas
                        pycas.add_fs(measureTag_anno)

                # check for relations

                # re-get entities by type
                #allGoldEntities = pycas.get_fs_of_type(datatype)
                allDiscoveredIncidents = pycas.get_fs_of_type(PIRITypesAndPieces.datatypeIncident) + pycas.get_fs_of_type(PIRITypesAndPieces.datatypeIncidentTrigger)
                allDiscoveredMeasures = pycas.get_fs_of_type(PIRITypesAndPieces.datatypeMeasure) + pycas.get_fs_of_type(PIRITypesAndPieces.datatypeMeasureTrigger)
                #print("size"+str(allDiscoveredMeasures.__sizeof__()))
                #print("size" + str(allDiscoveredIncidents.__sizeof__()))

                # initialize performance variables
                incidentTruePositives = 0
                incidentFalsePositives = 0
                incidentTrueNegatives = 0
                incidentFalseNegatives = 0

                incidentGoldPositives = 0

                measureTruePositives = 0
                measureFalsePositives = 0
                measureTrueNegatives = 0
                measureFalseNegatives = 0

                measureGoldPositives = 0

                relationTruePositives = 0
                relationFalsePositives = 0
                relationTrueNegatives = 0
                relationFalseNegatives = 0

                relationGoldPositives = 0

                totalCheckedChunks = 0

                goldIncidentFound = 0
                goldMeasureFound = 0
                goldRelationFound = 0

                goldMeasureFound = 0
                goldIncidentFound = 0

                for sent in currentDocObject.sents:
                    # print(sent.ents)
                    ents = list(sent.ents)

                    # check for co occurrence
                    # if (incident_contained == 1) and (measure_contained == 1):
                    for ent in ents:
                        if (ent.label_ == "INCIDENT" or ent.label_ == "INCIDENTTRIGGER"):
                            for ent2 in ents:
                                if (ent2.label_ == "MEASURE" or ent2.label_ == "MEASURETRIGGER"):
                                    relationTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypeGeneralRelation)
                                    relationTag_anno["begin"] = sent.start_char
                                    relationTag_anno["end"] = sent.end_char
                                    # relationTag_anno["EntityFrom"] = currentFoundIncident.id
                                    relationTag_anno.set_feature_value("EntityFrom",getXmiEntityForSpacyEnity(ent2,allDiscoveredMeasures))
                                    # relationTag_anno["EntityTo"] = currentFoundMeasure.id
                                    relationTag_anno.set_feature_value("EntityTo",getXmiEntityForSpacyEnity(ent,allDiscoveredIncidents))
                                    relationTag_anno["Label"] = "hasMeasure"
                                    relationTag_anno["DisplayLabel"] = "hasMeasure"
                                    pycas.add_fs(relationTag_anno)
                                    # add nodes and relation in graph
                                    # PiriGraph.add_node(nodeCount,pos=(nodeCount,i))

                                    #print(str(getXmiEntityForSpacyEnity(ent,allDiscoveredMeasures)) + "relation found" + str(getXmiEntityForSpacyEnity(ent2,allDiscoveredIncidents)))

                            # reset temporary counters
                            incident_contained = 0
                            measure_contained = 0
                            relation_contained = 0

                            goldIncidentFound = 0
                            goldMeasureFound = 0
                            goldRelationFound = 0

                            # upgrade checked chunk counter
                            totalCheckedChunks += 1

                # store this document again
                pycas.serialize(XMI_OUTPUT_PATH + entry.name.replace(".pdf", "").replace(".txt", "").replace("_", "-") + ".xmi")
f.close()