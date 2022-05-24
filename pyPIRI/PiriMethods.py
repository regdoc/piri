
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# check every element of ontology for similarity, save current most similar concept
import PiriOntologyTools


def getMostSimilarPiriClass(semanticConcept, allSemanticConcepts):
    bestSimilarity = 0
    mostSimilarElement = semanticConcept

    model = SentenceTransformer('bert-base-nli-mean-tokens')
    semanticConceptList = [str(semanticConcept)]
    allSentences = semanticConceptList + allSemanticConcepts

    sentence_embeddings = model.encode(allSentences)
    sentence_embeddings.shape
    #sentence_embeddings.reshape(-1, 1)
    i = 1

    for currentSemanticConcept in allSemanticConcepts:

        #currentSimilarity = SequenceMatcher(None, semanticConcept, currentSemanticConcept).ratio()
        currentSimilarity = cosine_similarity([sentence_embeddings[0]],[sentence_embeddings[i]])
        if (currentSimilarity > bestSimilarity):
            bestSimilarity = currentSimilarity
            mostSimilarElement = currentSemanticConcept
        i += 1

    print(mostSimilarElement + " " + str(bestSimilarity))
    return [mostSimilarElement, bestSimilarity]

# check every element of ontology for similarity, save current most similar concept
def getSemanticResults(semanticSearchText):
    model = SentenceTransformer('bert-base-nli-mean-tokens')

    semanticSearchChunks = semanticSearchText.split()
    semanticResults = ""

    allIncidents = PiriOntologyTools.getPiriOntologyIncidents()
    allMeasures = PiriOntologyTools.getPiriOntologyMeasures()

    for semanticWord in semanticSearchChunks:
        for incident in allIncidents:
            s = SequenceMatcher(None, semanticWord, incident)
            s.ratio()
            semanticResults += "Incident: " + str(incident)+" Similarity: " + str(s.ratio()) + "\n\n"

    return semanticResults

def getMostSimilarPiriClassIDFromSimilarityMatrix(informationUnitID, similarityMatrix):
    bestSimilarity = 0
    mostSimilarElementID = 0

    for currentSemanticConceptID in range(similarityMatrix.shape[0]):
        #currentSimilarity = SequenceMatcher(None, semanticConcept, currentSemanticConcept).ratio()
        currentSimilarity = similarityMatrix[currentSemanticConceptID][informationUnitID]
        if (currentSimilarity > bestSimilarity):
            bestSimilarity = currentSimilarity
            mostSimilarElementID = currentSemanticConceptID

    print(str(mostSimilarElementID) + " best similarity: " + str(bestSimilarity))
    return [mostSimilarElementID, bestSimilarity]

#def getMostSimilarPiriClass(semanticConcept, allSemanticConcpets):
#    return