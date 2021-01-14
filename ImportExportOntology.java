//import ontology file and export feature queries to a text file

package de.regdoc;

import java.io.InputStream;
import java.io.PrintWriter;
import java.util.regex.Pattern;

import org.apache.jena.query.Query;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.query.QuerySolution;
import org.apache.jena.query.ResultSet;
import org.apache.jena.query.ResultSetFactory;
import org.apache.jena.query.ResultSetRewindable;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.util.FileManager;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.PhraseQuery;

public class ImportExportOntology {

	private static final String INPUT_FILE = "C:\\ontology.rdf";
	private static final String OUTPUT_FILE = "C:\\ontoquery-2.txt";
	private static final String ONTOLOGY_OUTPUT_FILE = "C:\\REGDOC-booted-ontology.rdf";
	private static final String LOG_OUTPUT_FILE = "C:\\log-ImportExportOntology.txt";
	private static final String INDEX_DIR = "C:\\Canada-INDEX\\";
	//private static final String OPEN_NLP_GERMAN_TOKENIZER = "C:\\de-token.bin";
	private static final String LUCENE_FIELD = "contents";
	private static final String NS_PIRI = "http://www.angesagt-gmbh.de/piri#";
	private static final String NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#";
	private static final String NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";
	
	
	public static void main(String[] args) throws Exception {
		PrintWriter writerDocSim;
		writerDocSim = new PrintWriter(OUTPUT_FILE, "UTF-8");

		// create an empty model
		Model ontologyModel = ModelFactory.createDefaultModel();

		// use the FileManager to find the input file
		InputStream inputOntologyFile = FileManager.get().open(INPUT_FILE);
		if (inputOntologyFile == null) {
			throw new IllegalArgumentException("File: " + INPUT_FILE + " not found");
		}

		// read the RDF/XML file
		ontologyModel.read(inputOntologyFile, null);

		String ontologySparqlString = "PREFIX piri: <"+NS_PIRI+"> PREFIX rdfs: <"+NS_RDFS+"> SELECT ?x ?yLabel ?z WHERE {\r\n"
				+ "	    ?x ?y ?z . \r\n" + "	    ?x a piri:Incident. \r\n" + "	    ?x rdfs:label ?xLabel.\r\n"
				+ "	    ?z rdfs:label ?zLabel.\r\n" + "	    FILTER(LANGMATCHES(LANG(?xLabel), \"en\"))\r\n"
				+ "	    FILTER(LANGMATCHES(LANG(?zLabel), \"en\"))\r\n" + "	    FILTER (?y = piri:partOf).\r\n"
				+ "	    FILTER (?z != ?x).\r\n" + "	    BIND (SUBSTR(STR(?y), 41) AS ?yLabel)  \r\n" + "}";
		Query ontologySparqlQuery = QueryFactory.create(ontologySparqlString);

		try (QueryExecution ontologySparqlExecution = QueryExecutionFactory.create(ontologySparqlQuery, ontologyModel)) {
			ResultSet ontologySparqlResults = ontologySparqlExecution.execSelect();
			System.out.println("rowNumber:" + ontologySparqlResults.getRowNumber());
			while (ontologySparqlResults.hasNext()) {
				QuerySolution soln = ontologySparqlResults.nextSolution();
				RDFNode x = soln.get("x"); // Get a result variable by name.
				System.out.println("varName: " + x.toString());
				String className = x.toString();
				className = className.replace(NS_PIRI, "");
				System.out.println("className: " + className);
				
				String queryString11 = "PREFIX piri: <"+NS_PIRI+"> PREFIX rdfs: <"+NS_RDFS+"> SELECT ?x\r\n"
						+ "WHERE { <" + x.toString() + "> piri:hasTrace  ?x. }";

				Query query11 = QueryFactory.create(queryString11);

				try (QueryExecution qexec1 = QueryExecutionFactory.create(query11, ontologyModel)) {
					ResultSet results1 = qexec1.execSelect();
					ResultSetRewindable results2 = ResultSetFactory.copyResults(results1);
					int i = 0;
					for (; results2.hasNext(); ++i)
						results2.next();
					System.out.println("results: " + i);
					// if no trace then write class name
					if (i == 0) {
						writerDocSim.println(className + "--->" + className);
					} else {
						writerDocSim.print(className + "--->");
					}
					results2.reset();
					int count = 1;
					// write traces as query
					while (results2.hasNext()) {
						QuerySolution soln1 = results2.nextSolution();
						RDFNode x1 = soln1.get("x"); // Get a result variable by name.
						System.out.println("varNameLabel: " + x1.toString());
						if (count == i) {
							writerDocSim.println(x1.toString());
						} else {
							writerDocSim.print(x1.toString() + " AND ");
						}
						count++;
					}
				}

			}
		}

		writerDocSim.close();
		ontologyModel.close();

	}

	public static String[][] getTaxoSearchFeatures(Model model, String startResource, String nsStartResource,
		
		String derivePropertyStartResource, String connectingProperty, PrintWriter logFile) throws Exception {
		String[][] exportFeatures = null;
		
		/*
		// create an empty model
		Model model = ModelFactory.createDefaultModel();

		// use the FileManager to find the input file
		InputStream in = FileManager.get().open(modelFile);
		if (in == null) {
			throw new IllegalArgumentException("File: " + modelFile + " not found");
		}

		// read the RDF/XML file
		model.read(in, null);
		*/
		
		String queryString2 = "PREFIX piri: <"+NS_PIRI+"> PREFIX rdfs: <"+NS_RDFS+"> PREFIX rdf: <"+NS_RDF+">" 
				+ "SELECT ?x ?xLabel WHERE {"
				+ "	    ?x ?y ?z . \r\n" + "	    ?x " + derivePropertyStartResource + " " + startResource + ". \r\n"
				+ "	    ?x rdfs:label ?xLabel.\r\n" + "	    ?z rdfs:label ?zLabel.\r\n"
				+ "	    FILTER(LANGMATCHES(LANG(?xLabel), \"en\"))\r\n"
				+ "	    FILTER(LANGMATCHES(LANG(?zLabel), \"en\"))\r\n" + "	    FILTER (?y = " + connectingProperty
				+ "). " + "	    FILTER (?z != ?x).\r\n" + "	    BIND (SUBSTR(STR(?y), 41) AS ?yLabel)  \r\n" + "}";
		Query query1 = QueryFactory.create(queryString2);

		try (QueryExecution qexec = QueryExecutionFactory.create(query1, model)) {

			ResultSet resultsa = qexec.execSelect();
			System.out.println(resultsa.getRowNumber());

			ResultSetRewindable results = ResultSetFactory.copyResults(resultsa);
			int m = 0;
			for (; results.hasNext(); ++m)
				results.next();
			int resultcount = m;
			results.reset();
			System.out.println("totalresults:" + resultcount);

			// initialize with number of sparql results
			exportFeatures = new String[resultcount][2];

			int j = 0;
			while (results.hasNext()) {
				QuerySolution soln = results.nextSolution();
				RDFNode x = soln.get("x"); // Get a result variable by name.
				RDFNode xLabel = soln.get("xLabel"); // Get a result variable by name.
				System.out.println("varName: " + x.toString());
				String className = x.toString();
				className = className.replace(nsStartResource, "");
				System.out.println("className: " + className);
				String labelName = xLabel.toString();
				labelName = labelName.replace("@en", "");
				labelName = labelName.replace("/", "");
				System.out.println("labelName: " + labelName);
				
				String queryString12 = " PREFIX rdf: <"+NS_RDF+"> PREFIX piri: <"+NS_PIRI+"> PREFIX rdfs: <"+NS_RDFS+">" 
						+ " SELECT ?x "
						+ " WHERE { <" + x.toString() + "> piri:hasTrace  ?x. FILTER(LANGMATCHES(LANG(?x), \"en\"))}";

				Query query11 = QueryFactory.create(queryString12);

				QueryExecution qexec1 = QueryExecutionFactory.create(query11, model);

				ResultSet results1 = qexec1.execSelect();
				ResultSetRewindable results2 = ResultSetFactory.copyResults(results1);

				int i = 0;
				for (; results2.hasNext(); ++i)
					results2.next();
				int tracecount = i;
				System.out.println("results: " + i);

				// if no trace then write label name
				if (i == 0) {
					exportFeatures[j][0] = className;
					exportFeatures[j][1] = labelName;
				} else {
					exportFeatures[j][0] = className;
				}
				logFile.println(
						"> " + j + "-ImportExportOntology-Feature#1exportFeatures[j][1]:" + exportFeatures[j][0]);
				results2.reset();
				int count = 1;

				// write traces as query
				String concatFeatures = "";
				while (results2.hasNext()) {
					QuerySolution soln1 = results2.nextSolution();
					RDFNode x1 = soln1.get("x"); // Get a result variable by name.

					logFile.println("> " + j + "-ImportExportOntology-varNameLabel: " + x1.toString());

					if (count == tracecount) {
						concatFeatures = concatFeatures+x1.toString().replace("@en", "");
					} else {
						concatFeatures = concatFeatures+x1.toString().replace("@en", "") + " AND ";
					}
					exportFeatures[j][1] = concatFeatures;
					logFile.println("> -ImportExportOntology-exportFeatures[j][1]:" + exportFeatures[j][1]);
					count++;
				}

				j++;
			}
		}
		//model.close();
		for (int n = 0; n < exportFeatures.length; n++) {
			System.out.println(
					n + "XXXfeatureArraytest0:" + exportFeatures[n][0] + "featureArraytest1:" + exportFeatures[n][1]);
		}
		return exportFeatures;

	}

	public static Object[][] getPhraseQueries(Model model, String startResource, String nsStartResource,
			
			String derivePropertyStartResource, String connectingProperty, PrintWriter logFile) throws Exception {
			Object[][] exportFeatures = null;
			PhraseQuery pq = null;
			
			String queryString2 = "PREFIX rdf: <"+NS_RDF+"> PREFIX piri: <"+NS_PIRI+"> PREFIX rdfs: <"+NS_RDFS+">" 
					+ " SELECT ?x  ?xLabel "
					+ " WHERE { ?x " + connectingProperty+"* "+startResource+". ?x rdfs:label ?xLabel. FILTER(LANGMATCHES(LANG(?xLabel), \"en\"))}";
			
			org.apache.jena.query.Query query1 = QueryFactory.create(queryString2);

			try (QueryExecution qexec = QueryExecutionFactory.create(query1, model)) {

				ResultSet resultsa = qexec.execSelect();
				ResultSetRewindable results = ResultSetFactory.copyResults(resultsa);
				int m = 0;
				for (; results.hasNext(); ++m)
					results.next();
				int resultcount = m;
				results.reset();
				logFile.println("> getPhraseQuerysFeatures totalresults:" + resultcount);

				// initialize with number of sparql results
				exportFeatures = new Object[resultcount][2];

				int j = 0;
				while (results.hasNext()) {
					QuerySolution soln = results.nextSolution();
					RDFNode x = soln.get("x"); // Get a result variable by name.
					RDFNode xLabel = soln.get("xLabel"); // Get a result variable by name.
					String className = x.toString();
					className = className.replace(nsStartResource, "");
					String labelName = xLabel.toString();
					labelName = labelName.replace("@en", "");
					labelName = labelName.replace("/", "");
					
					String queryString12 = " PREFIX rdf: <"+NS_RDF+"> PREFIX piri: <"+NS_PIRI+"> PREFIX rdfs: <"+NS_RDFS+">" 
							+ " SELECT ?x "
							+ " WHERE { <" + x.toString() + "> piri:hasTrace  ?x. FILTER(LANGMATCHES(LANG(?x), \"en\"))}";

					org.apache.jena.query.Query query11 = QueryFactory.create(queryString12);

					QueryExecution qexec1 = QueryExecutionFactory.create(query11, model);

					ResultSet results1 = qexec1.execSelect();
					ResultSetRewindable results2 = ResultSetFactory.copyResults(results1);

					int i = 0;
					for (; results2.hasNext(); ++i)
						results2.next();

					// if no trace then write label name
					if (i == 0) {
						exportFeatures[j][0] = (Object) className;
						exportFeatures[j][1] = (Object) labelName;
					} else {
						exportFeatures[j][0] = (Object) className;
					}
					results2.reset();
					
					// write traces as phrase query
					PhraseQuery.Builder builder = new PhraseQuery.Builder();
					builder.setSlop(3);
										
					while (results2.hasNext()) {
						QuerySolution soln1 = results2.nextSolution();
						RDFNode x1 = soln1.get("x"); // Get a result variable by name.
						builder.add(new Term("contents", x1.toString().replace("@en", "").toLowerCase()));
						logFile.println("> -ImportExportOntology, PhraseQuery term added:" + x1.toString().replace("@en", "").toLowerCase());
					}
					pq = builder.build();
					exportFeatures[j][1] = (Object) pq;
					j++;
					
				}
			}
			return exportFeatures;

		}
	
	// get all resources from model that are associated with a file
	public static String[] getResourceByFile(Model model, String fileName) throws Exception {
		String[] exportResources = null;

		String fileSparqlString = " PREFIX rdf: <"+NS_RDF+"> PREFIX piri: <"+NS_PIRI+"> PREFIX rdfs: <"+NS_RDFS+">" 
				+ " SELECT ?x "
				+ " WHERE { ?x piri:hasFile  \"" + fileName + "\" . }";

		Query fileSparqlQuery = QueryFactory.create(fileSparqlString);
		QueryExecution fileSparqlExecution = QueryExecutionFactory.create(fileSparqlQuery, model);

		ResultSet fileSparqlResults = fileSparqlExecution.execSelect();
		ResultSetRewindable fileSparqlResultsRewindable = ResultSetFactory.copyResults(fileSparqlResults);
		
		int count_i = 0;
		for (; fileSparqlResultsRewindable.hasNext(); ++count_i)
			fileSparqlResultsRewindable.next();
		exportResources = new String[count_i];
		fileSparqlResultsRewindable.reset();
		
		int count_j = 0;
		while (fileSparqlResultsRewindable.hasNext()) {
			QuerySolution fileSparqlSolution = fileSparqlResultsRewindable.nextSolution();
			RDFNode resultVariableX = fileSparqlSolution.get("x"); // Get a result variable by name
			exportResources[count_j] = resultVariableX.toString();
			count_j++;
		}
		return exportResources;
	}
	
	// proof whether a file is already instantiated in a model
	public static boolean proofModelForFile(Model model, String fileName, PrintWriter logFile) throws Exception {
		Boolean fileProof = false;
		String fileSparqlString = " PREFIX rdf: <" + NS_RDF + "> PREFIX piri: <" + NS_PIRI + "> PREFIX rdfs: <"
				+ NS_RDFS + ">" + " SELECT ?x " + " WHERE { ?x piri:hasFile  \"" + fileName + "\" . }";

		org.apache.jena.query.Query fileSparqlQuery = QueryFactory.create(fileSparqlString);
		QueryExecution fileSparqlExecution = QueryExecutionFactory.create(fileSparqlQuery, model);
		ResultSet fileSparqlResults = fileSparqlExecution.execSelect();
		ResultSetRewindable fileSparqlResultsRewindable = ResultSetFactory.copyResults(fileSparqlResults);

		int count_i = 0;
		for (; fileSparqlResultsRewindable.hasNext(); ++count_i) {
			fileSparqlResultsRewindable.next();
		}
		
		if (count_i == 0) {
			fileProof = false;
		} else {
			fileProof = true;
		}

		//System.out.println("Dateiname:"+fileName+" Status:"+fileProof);
		
		return fileProof;
	}
	
	public static String sanitizeXmlChars(String xml) {
		if (xml == null || ("".equals(xml)))
			return "";
		// ref : http://www.w3.org/TR/REC-xml/#charsets
		// jdk 7
		Pattern xmlInvalidChars = Pattern
				.compile("[^\\u0009\\u000A\\u000D\\u0020-\\uD7FF\\uE000-\\uFFFD\\x{10000}-\\x{10FFFF}]"

						);
		return xmlInvalidChars.matcher(xml).replaceAll("");
	}

}
