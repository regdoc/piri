//Highlith PDF-Documents with search strings

package de.regdoc;

import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.Writer;
import java.nio.file.Paths;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.List;
import java.util.regex.Pattern;

import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.query.QuerySolution;
import org.apache.jena.query.ResultSet;
import org.apache.jena.query.ResultSetFactory;
import org.apache.jena.query.ResultSetRewindable;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.Property;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.rdf.model.Resource;
import org.apache.jena.rdf.model.Statement;
import org.apache.jena.util.FileManager;
import org.apache.jena.vocabulary.RDF;
import org.apache.jena.vocabulary.RDFS;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.MatchAllDocsQuery;
import org.apache.lucene.search.PhraseQuery;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.search.highlight.Highlighter;
import org.apache.lucene.search.highlight.QueryScorer;
import org.apache.lucene.search.highlight.SimpleHTMLFormatter;
import org.apache.lucene.search.highlight.TextFragment;
import org.apache.lucene.search.highlight.TokenSources;
import org.apache.lucene.search.uhighlight.UnifiedHighlighter;
import org.apache.lucene.store.FSDirectory;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.graphics.color.PDColor;
import org.apache.pdfbox.pdmodel.graphics.color.PDDeviceRGB;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotation;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationTextMarkup;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.pdfbox.text.TextPosition;


public class OntologyToHighlightPDF extends PDFTextStripper {
	
	public OntologyToHighlightPDF()  throws IOException {
        super();
    }
	
	private static final String ONTOLOGY_OUTPUT_FILE = "REGDOC-OntologyToHighlightPDF-ontology.rdf";
	private static final String PDF_OUTPUT_PATH = "C:\\pdfhighlight\\";
	private static final String PDF_INPUT_PATH = "C:\\IAEA\\";
	private static final String LOG_OUTPUT_FILE = "C:\\log-OntologyToHighlightPDF.txt";
	private static final String INDEX_DIR = "C:\\IAEA-INDEX\\";
	private static final String LUCENE_FIELD = "contents";
	private static final String ONTOLOGY_INPUT_FILE = "C:\\ontology.rdf";
	private static final String NS_REGDOC = "http://www.angesagt-gmbh.de/regdoc#";
	private static final String NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#";
	private static final String NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";
	private static final String WIKI_HEAD = "%%package REGDOC_Ontology\r\n%%Turtle\r\n";
	private static final int REGDOC_BASE_ID = 101000001;
	private static final int RESOURCE_BASE_ID = 1000001;
		
	public static Analyzer analyzer = new EnglishAnalyzer();

	public static void main(String[] args) throws Exception {
		long start = System.currentTimeMillis();
		
		IndexReader idxReader = DirectoryReader.open(FSDirectory.open(Paths.get(INDEX_DIR)));
		IndexSearcher idxSearcher = new IndexSearcher(idxReader);

		// create logfile
		PrintWriter LogWriter;
		LogWriter = new PrintWriter(LOG_OUTPUT_FILE, "UTF-8");

		FileOutputStream out = new FileOutputStream(ONTOLOGY_OUTPUT_FILE);
		PrintStream newOntologyWriter;
		newOntologyWriter =new PrintStream(out, true, "ISO-8859-1"); 

		// create an empty ontology model
		Model model = ModelFactory.createDefaultModel();
		model.setNsPrefix("regdoc", NS_REGDOC);
		model.setNsPrefix("rdfs", NS_RDFS);

		// use the FileManager to find the ontology input file
		InputStream in = FileManager.get().open(ONTOLOGY_INPUT_FILE);
		if (in == null) {
			throw new IllegalArgumentException("File: " + ONTOLOGY_INPUT_FILE + " not found");
		}

		// read the RDF/XML file
		model.read(in, null);

		
		// *************************************************************************************
		// ******** create ontology stub with running id for every document in the corpus
		// *************************************************************************************

		try {
			// get all documents from index by query
			Query queryAll = new MatchAllDocsQuery();
			TopDocs hits1 = idxSearcher.search(queryAll, idxReader.maxDoc());
			LogWriter.println("> CreatKnowWEContent create ontology stub, total number of docs by allquery " + idxReader.maxDoc());

			// create knowwe menu string
			String knowweMenu = "";
			
			int currentID = 0;
			
			//TODO test if document already part of input ontology
			
			for (int i = 0; i < hits1.totalHits; i++) {
				//String instanceID = UUID.randomUUID().toString();
				int instanceID = REGDOC_BASE_ID+i;
				int id = hits1.scoreDocs[i].doc;
				Document docHit = idxSearcher.doc(id);
				String corpusDocPath = docHit.get("path");
				File f = new File(corpusDocPath);
				String currentFileNameTXT = f.getName();
				String currentFileName = currentFileNameTXT.substring(0, currentFileNameTXT.length() - 4);
				LogWriter.println("> CreatKnowWEContent current filename retrieved by lucene query: " + currentFileName);
				
				// create an empty ontology model only for the current file
				Model modelCurrentFile = ModelFactory.createDefaultModel();
				modelCurrentFile.setNsPrefix("regdoc", NS_REGDOC);
				modelCurrentFile.setNsPrefix("rdfs", NS_RDFS);
				
				// write resource for regulatory document to persistent ontology model
				Resource currentRegDoc2 = model.createResource(NS_REGDOC + "rg_" + instanceID);
				currentRegDoc2.addProperty(RDFS.label, "Regulatory Concept based on file: " + currentFileName);
				currentRegDoc2.addProperty(REGDOC.hasFile, currentFileName);
				currentRegDoc2.addProperty(REGDOC.hasTitle, "");
				model.add(currentRegDoc2, RDF.type, REGDOC.RegulatoryConcept);
			
				// write ontology to string
				StringWriter newOntologyStringWriter = new StringWriter();
				modelCurrentFile.write(newOntologyStringWriter, "TURTLE");
				String fileContent = WIKI_HEAD+newOntologyStringWriter;
				fileContent = fileContent.replace("@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .","");
				fileContent = fileContent.replace("@prefix regdoc: <http://www.angesagt-gmbh.de/regdoc#> .","");
				
				
				// create PDF file for current file and write ontology, insert entry into knowwe menu
				String inputPDFFile = PDF_INPUT_PATH + currentFileName;
				String outputPDFFile = PDF_OUTPUT_PATH + "HIGHLIGHT-" + currentFileName;
				
				PDDocument document = null;

				try {
					document = PDDocument.load(new File(inputPDFFile));
					
					if (document.isEncrypted()) {
				        try {
				            document.setAllSecurityToBeRemoved(true);
				        }
				        catch (Exception e) {
				            throw new Exception("Problem with encrytion.", e);
				        }
				    }
					
					PDFTextStripper stripper = new PDFHighlight();
					stripper.setSortByPosition(true);
					stripper.setStartPage(0);
					stripper.setEndPage(document.getNumberOfPages());

					Writer dummy = new OutputStreamWriter(new ByteArrayOutputStream());
					stripper.writeText(document, dummy);

					File file1 = new File(outputPDFFile);
					document.save(file1);
				} finally {
					if (document != null) {
						document.close();
					}
				}

				// close all writers
				modelCurrentFile.close();
				// log runtime
				long end = System.currentTimeMillis();
				NumberFormat formatter = new DecimalFormat("#0.00000");
				LogWriter.print("current Execution time is " + formatter.format((end - start) / 1000d) + " seconds");
			
			}
		
		public static String sanitizeXmlChars(String xml) {
			if (xml == null || ("".equals(xml)))
				return "";
			Pattern xmlInvalidChars = Pattern
					.compile("[^\\u0009\\u000A\\u000D\\u0020-\\uD7FF\\uE000-\\uFFFD\\x{10000}-\\x{10FFFF}]"

							);
			return xmlInvalidChars.matcher(xml).replaceAll("");
		}
		
	    

}
