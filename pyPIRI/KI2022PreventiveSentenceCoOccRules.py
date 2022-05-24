# Input: XMI
# Output: XMI with applied preventive and reactive trigger rules

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

data = [[]]

def getXmiEntityForSpacyEnity(spacyEntity, allXmiEntities):
    for xmiEntity in allXmiEntities:
        if (xmiEntity.begin == spacyEntity.start_char) and (xmiEntity.end == spacyEntity.end_char):
            return xmiEntity
            break

PYPIRI_PATH = "D:/Daten/Uni/Promotion/"

#TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-TRAIN/"
#TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-VALIDATE/"
TXT_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-TXT-UTF8-CLEAN-KI2022-TEST/"

#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputApplyPriorKnowledge01/"
#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveTrain/"
#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveValidate/"
XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPreventiveTest/"

#XMI_OUTPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputRelationalClassifier01/"

#XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/Scorpion/outputScorpionNER01/"
#XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPriorTrain/"
#XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPriorValidate/"
XMI_INPUT_PATH = "D:/Daten/Uni/Promotion/PyPIRI/KI2022/outputPriorTest/"

XMI_GOLD_INPUT_PATH = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/IAEA-XMI-GOLD/"

LOG_OUTPUT_PATH = ""

LOG_OUTPUT_FILE = ""

ONTOLOGY_ANNOTATION_INPUT_FILE = "D:/Daten/Uni/Promotion/Korpus/NUCLEAR SAFETY/UIMA/PiriAnnotator01/ontology.rdf"

# load spacy nlp pipeline
nlp = spacy.load("en_core_web_sm")

# create a Graph
piriOnotology = rdflib.Graph()
nodeCount = 1

# parse in an RDF file hosted on the Internet
result = piriOnotology.parse(ONTOLOGY_ANNOTATION_INPUT_FILE)

# print the number of "triples" in the Graph
print("graph has {} statements.".format(len(piriOnotology)))

config = {
    # "phrase_matcher_attr": None,
    # "validate": True,
    # "overwrite_ents": True,
    # "ent_id_sep": "||",
}

# create entity ruler
ruler = nlp.add_pipe("entity_ruler", config=config)

for text in preventiveMeasureRules.measureRules01:
    # print(str(text))
    ruler.add_patterns([{"label": "PREVENTIVEMEASURE", "pattern": str(text)}])
    print ("Rule appended: "+str(text))

for text in reactiveMeasureRules.measureRules01:
    # print(str(text))
    ruler.add_patterns([{"label": "REACTIVEMEASURE", "pattern": str(text)}])
    print ("Rule appended: "+str(text))

# get all documents from text corpus
with os.scandir(TXT_INPUT_PATH) as txtIt:
    for entry in txtIt:
        if entry.name.endswith(".txt") and entry.is_file():
            documentName = entry.name
            documentPatz = entry.path
            print(entry.name, entry.path)

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

                ############################################
                # get all labels and look for co-occurrence annotate relation
                ############################################


                for ent in currentDocObject.ents:



                    # write the found match


                    if (ent.label_ == "PREVENTIVEMEASURE"):
                        print("entity: " + str(ent.label_) + "text: " + str(ent.sent))

                        data.append([documentName, str(ent.sent), 'true'])
                        # add feature structure
                        measureTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypePreventiveMeasureTrigger)

                        # set some attributes
                        measureTag_anno["begin"] = ent.sent.start_char
                        measureTag_anno["end"] = ent.sent.end_char
                        measureTag_anno["owlid"] = "preventiveMeasureCandidate"

                        # add this feature structure into the cas
                        pycas.add_fs(measureTag_anno)
                        # store this document again

                    if (ent.label_ == "REACTIVEMEASURE"):
                        print("entity: " + str(ent.label_) + "text: " + str(ent.sent))

                        data.append([documentName, str(ent.sent), 'true'])
                        # add feature structure
                        measureTag_anno = pycas.create_fs(PIRITypesAndPieces.datatypeReactiveMeasureTrigger)

                        # set some attributes
                        measureTag_anno["begin"] = ent.sent.start_char
                        measureTag_anno["end"] = ent.sent.end_char
                        measureTag_anno["owlid"] = "reactiveMeasureCandidate"

                        # add this feature structure into the cas
                        pycas.add_fs(measureTag_anno)

                allDiscoveredRelations = pycas.get_fs_of_type(PIRITypesAndPieces.datatypeGeneralRelation)

                for sent in currentDocObject.sents:
                    # print(sent.ents)
                    ents = list(sent.ents)

                    # check for co occurrence
                    # if (incident_contained == 1) and (measure_contained == 1):
                    for ent in ents:
                        if (ent.label_ == "PREVENTIVEMEASURE"):
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
                pycas.serialize(XMI_OUTPUT_PATH + entry.name.replace(".pdf", "").replace(".txt", "").replace("_","-") + ".xmi")

                """"
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
                    """
"""
with open('D:/Daten/Uni/Promotion/PyPIRI/KI2022/RelationClassifier.csv', 'x', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)

    header = ['file', 'string', 'relationtruefalse']
    #data = ['Afghanistan', 652090, 'AF', 'AFG']

    # write the header
    writer.writerow(header)

    for elements in data:
        writer.writerow(elements)

    # close the csv statistics file
    f.close()
"""