# gazetteer entity matching with phrase matcher, cooccurrence relation matcher, compares to gold standard and creates consistent xmi files

import string

import rdflib
import os

from spacy.tokens import Span
from uima.PyCAS import PyCAS
from pathlib import Path

import incidentRules
import measureRules

import spacy
from spacy.matcher import PhraseMatcher, Matcher

def getXmiEntityForSpacyEnity(spacyEntity, allXmiEntities):
    for xmiEntity in allXmiEntities:
        if (xmiEntity.begin == spacyEntity.start_char) and (xmiEntity.end == spacyEntity.end_char):
            return xmiEntity
            break

PYPIRI_PATH = "D:/Daten/Uni/Promotion/"

TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN/"

XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/output/"

#XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/Scorpion/outputScorpionNER01/"

XMI_GOLD_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-XMI-GOLD/"

LOG_OUTPUT_PATH = ""

LOG_OUTPUT_FILE = ""

ONTOLOGY_ANNOTATION_INPUT_FILE = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/UIMA/PiriAnnotator01/ontology.rdf"

NS_PIRI = "http://www.angesagt-gmbh.de/piri#"

NS_REGDOC = "http://www.angesagt-gmbh.de/regdoc#"

NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#"

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

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

# iterate over found labels
for row in queryForIncidents:
    ruler.add_patterns([{"label": "INCIDENT", "pattern": str(row.prefLabel)}])

for row in queryForMeasures:
    ruler.add_patterns([{"label": "MEASURE", "pattern": str(row.prefLabel)}])

# joinedQueries = queryForMeasures + queryForIncidents

# create matcher for text patterns indicating entities
# incidentMatcher = PhraseMatcher(nlp.vocab)
# measureMatcher = PhraseMatcher(nlp.vocab)

# matchRule = [{'LOWER': str(row.prefLabel)}]
# patterns = [nlp.make_doc(text) for text in incidentRules.incidentRules01]
# incidentMatcher.add("INCIDENT", patterns)

for text in incidentRules.incidentRules01:
    # print(str(text))
    ruler.add_patterns([{"label": "INCIDENT", "pattern": str(text)}])

for text in measureRules.measureRules01:
    # print(str(text))
    ruler.add_patterns([{"label": "MEASURE", "pattern": str(text)}])

# patterns = [nlp.make_doc(text) for text in measureRules.measureRules01]
# measureMatcher.add("MEASURE", patterns)

# define CAS datatypes
datatype = "de.uniwue.aries.ie.IEEntityGold"
datatypeRelation = "de.uniwue.aries.ie.IERelationGold"

# get all documents from text corpus
with os.scandir(TXT_INPUT_PATH) as txtIt:
    for entry in txtIt:
        if entry.name.endswith(".txt") and entry.is_file():
            print(entry.name, entry.path)

            # read document content
            with open(entry.path, encoding="utf8") as currentDocText:
                lines = currentDocText.read()
                lines.encode('utf-8').decode('unicode-escape')
                # print(lines)
                currentDocObject = nlp(lines)

                # create CAS for current document
                pycas = PyCAS.empty("D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/ARIESTypesystem.xml")
                pycas.set_document_text(lines)

                ############################################
                # get all labels and look for co-occurrence annotate relation
                ############################################
                for ent in currentDocObject.ents:

                    # print("entity: " + str(ent.label_) + "text: " + str(ent.text))

                    if (ent.label_ == "INCIDENT"):
                        # add feature structure
                        incidentTag_anno = pycas.create_fs(datatype)

                        # set some attributes
                        incidentTag_anno["begin"] = ent.start_char
                        incidentTag_anno["end"] = ent.end_char
                        incidentTag_anno["owlid"] = "incidentRoot"

                        # add this feature structure into the cas
                        pycas.add_fs(incidentTag_anno)

                    if (ent.label_ == "MEASURE"):
                        # add feature structure
                        measureTag_anno = pycas.create_fs(datatype)

                        # set some attributes
                        measureTag_anno["begin"] = ent.start_char
                        measureTag_anno["end"] = ent.end_char
                        measureTag_anno["owlid"] = "measureRoot"

                        # add this feature structure into the cas
                        pycas.add_fs(measureTag_anno)

                ############################################
                # get all sentences and check co-occurrence of measure and incident
                ############################################
                incident_contained = 0
                measure_contained = 0
                relation_contained = 0

                # get GOLD document for current document
                # create CAS for current GOLD document
                goldxmi = entry.name.replace(".pdf", "").replace(".txt", "") + ".xmi"
                # print(goldxmi)
                goldpath = XMI_GOLD_INPUT_PATH + goldxmi
                goldfile = Path(goldpath)

                if (goldfile.exists()):
                    goldCas = PyCAS.from_xmi(
                        path=goldpath,
                        path_to_typesystem="D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/ARIESTypesystem.xml")
                    # pycas.set_document_text(lines)

                    docTextFromXMI = goldCas.get_sofa()
                    currentDocObjectXMI = nlp(str(docTextFromXMI))
                    # print(docTextFromXMI.data)

                    # loop through incident annotations and print their text

                    allGoldEntities = goldCas.get_fs_of_type(datatype)
                    allDiscoveredEntities = pycas.get_fs_of_type(datatype)
                    # all_measures = goldCas.get_fs_of_type(datatype)
                    # for goldEntity in allGoldEntities:
                    # print("goldEntity: "+str(goldEntity.begin)+" - "+str(goldEntity.end)+" - "+goldEntity["owlid"])
                    # print(annotation.get_covered_text())
                    # loop through measure annotations and print their text
                    # for measure_annotation in goldCas.get_fs_of_type(datatype):
                    # print("measure: "+str(measure_annotation.begin)+" - "+str(measure_annotation.end)+" - "+str(measure_annotation.owlid))
                    # print(annotation.get_covered_text())


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

                        # check gold match for sentence
                        for goldEntity in allGoldEntities:
                            if (goldEntity.begin > sent.start_char) and (goldEntity.begin < sent.end_char):
                                if (goldEntity["owlid"] == "incidentRoot"):
                                    goldIncidentFound = 1
                                    currentFoundIncident = goldEntity
                                if (goldEntity["owlid"] == "measureRoot"):
                                    goldMeasureFound = 1
                                    currentFoundMeasure = goldEntity
                        if (goldIncidentFound == 1):
                            incidentGoldPositives += 1
                        if (goldMeasureFound == 1):
                            measureGoldPositives += 1
                        if (goldIncidentFound == 1) and (goldMeasureFound == 1):
                            goldRelationFound = 1
                            relationGoldPositives += 1

                        for ent in ents:
                            if (ent.label_ == "INCIDENT"):
                                incident_contained = 1
                            if (ent.label_ == "MEASURE"):
                                measure_contained = 1
                        if (incident_contained == 1) and (measure_contained == 1):
                            relation_contained = 1

                        # check for positives
                        if (incident_contained == 1) and (goldIncidentFound == 1):
                            incidentTruePositives += 1

                        if (incident_contained == 1) and (goldIncidentFound == 0):
                            incidentFalsePositives += 1

                        if (measure_contained == 1) and (goldMeasureFound == 1):
                            measureTruePositives += 1

                        if (measure_contained == 1) and (goldMeasureFound == 0):
                            measureFalsePositives += 1

                        if (relation_contained == 1) and (goldRelationFound == 1):
                            relationTruePositives += 1

                        if (relation_contained == 1) and (goldRelationFound == 0):
                            relationFalsePositives += 1

                        # check for negatives
                        if (incident_contained == 0) and (goldIncidentFound == 0):
                            incidentTrueNegatives += 1

                        if (incident_contained == 0) and (goldIncidentFound == 1):
                            incidentFalseNegatives += 1

                        if (measure_contained == 0) and (goldMeasureFound == 0):
                            measureTrueNegatives += 1

                        if (measure_contained == 0) and (goldMeasureFound == 1):
                            measureFalseNegatives += 1

                        if (relation_contained == 0) and (goldRelationFound == 0):
                            relationTrueNegatives += 1

                        if (relation_contained == 0) and (goldRelationFound == 1):
                            relationFalseNegatives += 1

                        # check for co occurrence
                        # if (incident_contained == 1) and (measure_contained == 1):
                        for ent in ents:
                            if (ent.label_ == "INCIDENT"):
                                for ent2 in ents:
                                    if (ent2.label_ == "MEASURE"):
                                        relationTag_anno = pycas.create_fs(datatypeRelation)
                                        relationTag_anno["begin"] = sent.start_char
                                        relationTag_anno["end"] = sent.end_char
                                        #relationTag_anno["EntityFrom"] = currentFoundIncident.id
                                        relationTag_anno.set_feature_value("EntityFrom", getXmiEntityForSpacyEnity(ent, allDiscoveredEntities))
                                        #relationTag_anno["EntityTo"] = currentFoundMeasure.id
                                        relationTag_anno.set_feature_value("EntityTo", getXmiEntityForSpacyEnity(ent2, allDiscoveredEntities))
                                        relationTag_anno["Label"] = "hasMeasure"
                                        relationTag_anno["DisplayLabel"] = "hasMeasure"
                                        pycas.add_fs(relationTag_anno)


                                        # print("relation found")

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

                    incidentPrecision = 10 * incidentTruePositives / (incidentTruePositives + incidentFalsePositives)
                    incidentRecall = incidentTruePositives / (incidentTruePositives + incidentFalseNegatives)
                    incidentF1 = 2 * (incidentPrecision * incidentRecall) / (incidentPrecision + incidentRecall)

                    measurePrecision = 10 * measureTruePositives / (measureTruePositives + measureFalsePositives)
                    measureRecall = measureTruePositives / (measureTruePositives + measureFalseNegatives)
                    measureF1 = 2 * (measurePrecision * measureRecall) / (measurePrecision + measureRecall)

                    relationPrecision = 10 * relationTruePositives / (relationTruePositives + relationFalsePositives)
                    relationRecall = relationTruePositives / (relationTruePositives + relationFalseNegatives)
                    relationF1 = 2 * (relationPrecision * relationRecall) / (relationPrecision + relationRecall)

                    print("totalCheckedChunks: " + str(totalCheckedChunks))
                    print("incidentPrecision: " + str(incidentPrecision))
                    print("incidentRecall: " + str(incidentRecall))
                    print("incidentF1: " + str(incidentF1))
                    print("measurePrecision: " + str(measurePrecision))
                    print("measureRecall: " + str(measureRecall))
                    print("measureF1: " + str(measureF1))
                    print("relationPrecision: " + str(relationPrecision))
                    print("relationRecall: " + str(relationRecall))
                    print("relationF1: " + str(relationF1))
                else:
                    print("No Gold Standard Available")
                    #goldCas = PyCAS.empty(
                        #path_to_typesystem="D:/Daten/Uni/Promotion/PyPIRI/TypeSystems/ARIESTypesystem.xml")
                    # pycas.set_document_text(lines)

                    #docTextFromXMI = ""
                    #currentDocObjectXMI = nlp(str(docTextFromXMI))
                    # print(docTextFromXMI.data)

                    # loop through incident annotations and print their text

                    #allGoldEntities = goldCas.get_fs_of_type(datatype)
                    #allDiscoveredEntities = pycas.get_fs_of_type(datatype)


