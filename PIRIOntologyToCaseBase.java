//Export input PIRI-ontology to information uni case base and PIRI case base

package de.regdoc;

import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.nio.file.Paths;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.query.QuerySolution;
import org.apache.jena.query.ResultSet;
import org.apache.jena.query.ResultSetFactory;
import org.apache.jena.query.ResultSetRewindable;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.util.FileManager;
import org.apache.log4j.BasicConfigurator;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.store.FSDirectory;

public class PIRIOntologyToCaseBase {

	private static final String CASE_BASE_OUTPUT_FILE = "C:\\output\\path\\IUCaseBase.csv";
	private static final String PIRI_CASE_BASE_OUTPUT_FILE = "C:\\output\\path\\PIRICaseBase.csv";
	private static final String LOG_OUTPUT_FILE = "C:\\output\\path\\log-PIRIOntologyToCaseBase.txt";
	private static final String INDEX_DIR = "C:\\index\\path\\";
	private static final String INPUT_FILE = "C:\\input\\path\\ontology.rdf";
	private static final String NS_REGDOC = "http://www.angesagt-gmbh.de/regdoc#";
	private static final String NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#";
	private static final String NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";

	public static Analyzer analyzer = new EnglishAnalyzer();

	public static void main(String[] args) throws Exception {
		BasicConfigurator.configure();

		IndexReader idxReader = DirectoryReader.open(FSDirectory.open(Paths.get(INDEX_DIR)));
		new IndexSearcher(idxReader);

		String preventiveMeasures = "";
		String reactiveMeasures = "";
		String currentIncidentInstance = "";
		String currentIncidentType = "";
		String currentRegDocFile = "";
		String currentRegDocTitle = "";
		int cut_NS_REGDOC = NS_REGDOC.length();

		// create logfile
		PrintWriter LogWriter;
		LogWriter = new PrintWriter(LOG_OUTPUT_FILE, "UTF-8");

		// create csv case files
		FileOutputStream outIUCaseBaseWriter = new FileOutputStream(CASE_BASE_OUTPUT_FILE);
		PrintStream iUCaseBaseWriter;
		iUCaseBaseWriter = new PrintStream(outIUCaseBaseWriter, true, "ISO-8859-1");

		FileOutputStream outPIRICaseBaseWriter = new FileOutputStream(PIRI_CASE_BASE_OUTPUT_FILE);
		PrintStream pIRICaseBaseWriter;
		pIRICaseBaseWriter = new PrintStream(outPIRICaseBaseWriter, true, "ISO-8859-1");

		// create heads
		iUCaseBaseWriter.println("CaseID;Document;Entities;Annotations;Context");
		pIRICaseBaseWriter.println("CaseID;Document;Title;PreventiveMeasures;Incident;ReactiveMeasures");
		int caseCount = 1;
		int PIRIcaseCount = 1;

		// create an empty model
		Model model = ModelFactory.createDefaultModel();
		model.setNsPrefix("regdoc", NS_REGDOC);
		model.setNsPrefix("rdfs", NS_RDFS);

		// use the FileManager to find the ontology input file
		InputStream in = FileManager.get().open(INPUT_FILE);
		if (in == null) {
			throw new IllegalArgumentException("File: " + INPUT_FILE + " not found");
		}

		// read the RDF/XML file
		model.read(in, null);

		// *************************************************************************************
		// ******** get all annotated instances from input ontology
		// *************************************************************************************
		String queryStringIU = "PREFIX rdf: <"+NS_RDF+"> PREFIX regdoc: <"+NS_REGDOC+"> PREFIX rdfs: <"+NS_RDFS+">"
				+ " SELECT ?x ?annotation ?y ?yLabel ?context ?file \r\n"
				+ "WHERE { ?x regdoc:hasContent ?annotation . ?x rdf:type ?y. ?y rdfs:label ?v. ?x regdoc:partOf ?context. ?context regdoc:hasFile ?file. FILTER(LANGMATCHES(LANG(?v), \"en\")). BIND (SUBSTR(STR(?v), 1) AS ?yLabel)}";

		org.apache.jena.query.Query queryIU = QueryFactory.create(queryStringIU);
		QueryExecution queryExecutionIU = QueryExecutionFactory.create(queryIU, model);
		ResultSet resultsIU = queryExecutionIU.execSelect();
		ResultSetRewindable resultsIURewind = ResultSetFactory.copyResults(resultsIU);

		while (resultsIURewind.hasNext()) {
			QuerySolution solIU = resultsIURewind.nextSolution();
			String sanAnnotation = solIU.get("annotation").toString().replaceAll("\n|\r", "");
			// sanAnnotation = sanAnnotation.replaceAll("\r", "");
			iUCaseBaseWriter.println(
					"Case" + caseCount + ";" + solIU.get("file") + ";" + solIU.get("yLabel") + ";" + sanAnnotation);
			caseCount++;
		}

		// *************************************************************************************
		// ******** construct all PIRI-snippets from input ontology
		// *************************************************************************************

		// get all regulatory documents
		String queryStringRegDocs1 = "PREFIX rdf: <"+NS_RDF+"> PREFIX regdoc: <"+NS_REGDOC+"> PREFIX rdfs: <"+NS_RDFS+">"
				+ " SELECT ?x ?file ?title "
				+ "WHERE { ?x rdf:type regdoc:RegulatoryConcept . ?x regdoc:hasFile ?file. ?x regdoc:hasTitle ?title. }";

		org.apache.jena.query.Query queryRegDocs1 = QueryFactory.create(queryStringRegDocs1);
		QueryExecution queryExecutionRegDocs1 = QueryExecutionFactory.create(queryRegDocs1, model);
		ResultSet resultsRegDocs1 = queryExecutionRegDocs1.execSelect();
		ResultSetRewindable resultsRegDocsRewind1 = ResultSetFactory.copyResults(resultsRegDocs1);

		while (resultsRegDocsRewind1.hasNext()) {
			QuerySolution solRegDocs = resultsRegDocsRewind1.nextSolution();
			String currentRegDocInstance = solRegDocs.get("x").toString();
			currentRegDocFile = solRegDocs.get("file").toString();
			currentRegDocTitle = solRegDocs.get("title").toString();

			System.out.println(currentRegDocInstance);

			// get all incidents associated with current regulatory document
			String queryStringIncident1 = "PREFIX rdf: <"+NS_RDF+"> PREFIX regdoc: <"+NS_REGDOC+"> PREFIX rdfs: <"+NS_RDFS+">"
					+ " SELECT DISTINCT ?x ?file ?title ?itype "
					+ "WHERE { ?x rdf:type* regdoc:Incident. ?x regdoc:partOf <" + currentRegDocInstance + ">. }";

			org.apache.jena.query.Query queryIncident1 = QueryFactory.create(queryStringIncident1);
			QueryExecution queryExecutionIncident1 = QueryExecutionFactory.create(queryIncident1, model);
			ResultSet resultsIncident1 = queryExecutionIncident1.execSelect();

			// copy results to reset the pointer for count
			ResultSetRewindable resultsIncidentRewind1 = ResultSetFactory.copyResults(resultsIncident1);

			while (resultsIncidentRewind1.hasNext()) {
				QuerySolution solIncidents = resultsIncidentRewind1.nextSolution();
				// System.out.println(solIncidents.get("itype").toString());
				currentIncidentInstance = solIncidents.get("x").toString();
				System.out.println("IncidentInstance:" + currentIncidentInstance);

				// get incident type for current incident instance
				String queryStringIncident2 = "PREFIX rdf: <"+NS_RDF+"> PREFIX regdoc: <"+NS_REGDOC+"> PREFIX rdfs: <"+NS_RDFS+">"
						+ " SELECT DISTINCT ?itype " + "WHERE { <" + currentIncidentInstance + "> rdf:type ?itype. }";

				org.apache.jena.query.Query queryIncident2 = QueryFactory.create(queryStringIncident2);
				QueryExecution queryExecutionIncident2 = QueryExecutionFactory.create(queryIncident2, model);
				ResultSet resultsIncident2 = queryExecutionIncident2.execSelect();

				// copy results to reset the pointer for count
				ResultSetRewindable resultsIncidentRewind2 = ResultSetFactory.copyResults(resultsIncident2);
		
				while (resultsIncidentRewind2.hasNext()) {
					QuerySolution solIncidents2 = resultsIncidentRewind2.nextSolution();
					// System.out.println(solIncidents.get("itype").toString());
					currentIncidentType = solIncidents2.get("itype").toString();
					System.out.println("Type:" + currentIncidentType);
				}

				// document = solIncidents.get("file").toString();
				// documentTitle = solIncidents.get("title").toString();

				// get all preventive measures to Incident
				String queryStringPreventiveMeasures1 = "PREFIX rdf: <"+NS_RDF+"> PREFIX regdoc: <"+NS_REGDOC+"> PREFIX rdfs: <"+NS_RDFS+">"
						+ "SELECT ?preventiveMeasures ?preMeasureClass "
						+ "WHERE { ?preventiveMeasures regdoc:preventiveMeasureFor <" + currentIncidentInstance
						+ ">. ?preventiveMeasures rdf:type ?preMeasureClass. }";

				org.apache.jena.query.Query queryPreventiveMeasures1 = QueryFactory
						.create(queryStringPreventiveMeasures1);
				QueryExecution queryExecutionPreventiveMeasures1 = QueryExecutionFactory
						.create(queryPreventiveMeasures1, model);
				ResultSet resultsPreventiveMeasures1 = queryExecutionPreventiveMeasures1.execSelect();
				ResultSetRewindable resultsPreventiveMeasuresRewind1 = ResultSetFactory
						.copyResults(resultsPreventiveMeasures1);

				int m = 0;
				for (; resultsPreventiveMeasuresRewind1.hasNext(); ++m)
					resultsPreventiveMeasuresRewind1.next();
				int preventiveCount = m;
				resultsPreventiveMeasuresRewind1.reset();
				
				int count=1;
				while (resultsPreventiveMeasuresRewind1.hasNext()) {
					QuerySolution solPreventiveMeasures = resultsPreventiveMeasuresRewind1.nextSolution();
					String preMeasureClass = solPreventiveMeasures.get("preMeasureClass").toString();
					if (count == preventiveCount) {
						preventiveMeasures = preventiveMeasures + preMeasureClass.substring(cut_NS_REGDOC);
					} else {
						preventiveMeasures = preventiveMeasures + preMeasureClass.substring(cut_NS_REGDOC) + ", ";
					}
					count++;
				}

				// get all reactive measures to Incident
				String queryStringReactiveMeasures1 = "PREFIX rdf: <"+NS_RDF+"> PREFIX regdoc: <"+NS_REGDOC+"> PREFIX rdfs: <"+NS_RDFS+">"
						+ "SELECT ?reactiveMeasures ?reMeasureClass "
						+ "WHERE { ?reactiveMeasures regdoc:reactiveMeasureFor <" + currentIncidentInstance
						+ ">. ?reactiveMeasures rdf:type ?reMeasureClass. }";

				org.apache.jena.query.Query queryReactiveMeasures1 = QueryFactory.create(queryStringReactiveMeasures1);
				QueryExecution queryExecutionReactiveMeasures1 = QueryExecutionFactory.create(queryReactiveMeasures1,
						model);
				ResultSet resultsReactiveMeasures1 = queryExecutionReactiveMeasures1.execSelect();
				ResultSetRewindable resultsReactiveMeasuresRewind1 = ResultSetFactory
						.copyResults(resultsReactiveMeasures1);
				
				m = 0;
				for (; resultsReactiveMeasuresRewind1.hasNext(); ++m)
					resultsReactiveMeasuresRewind1.next();
				int reactiveCount = m;
				resultsReactiveMeasuresRewind1.reset();
				
				count=1;
				while (resultsReactiveMeasuresRewind1.hasNext()) {
					QuerySolution solReactiveMeasures = resultsReactiveMeasuresRewind1.nextSolution();
					String reMeasureClass = solReactiveMeasures.get("reMeasureClass").toString();
					if (count == reactiveCount) {
						reactiveMeasures = reactiveMeasures + reMeasureClass.substring(cut_NS_REGDOC);
					} else {
						reactiveMeasures = reactiveMeasures + reMeasureClass.substring(cut_NS_REGDOC) + ", ";
					}
					count++;	
				}

				System.out.println(preventiveMeasures);
				// write whole PIRI case
				pIRICaseBaseWriter.println("Case" + PIRIcaseCount + ";" + currentRegDocFile + ";" + currentRegDocTitle
						+ ";" + preventiveMeasures + ";" + currentIncidentType.substring(cut_NS_REGDOC) + ";"
						+ reactiveMeasures);
				PIRIcaseCount++;
				preventiveMeasures = "";
				reactiveMeasures = "";
			}

		}
		// close all writers
		LogWriter.close();
		iUCaseBaseWriter.close();
		pIRICaseBaseWriter.close();

	}

}
