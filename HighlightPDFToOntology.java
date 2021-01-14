//Extract comments from PDF files in a folder and transfer to an ontology
//At the same time create a text file for each annotation for machine learning purposes

package de.regdoc;

import java.awt.geom.Rectangle2D;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.Writer;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Date;
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
import org.apache.lucene.document.Field;
import org.apache.lucene.document.FieldType;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexOptions;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.IndexWriterConfig.OpenMode;
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
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.pdfbox.cos.COSArray;
import org.apache.pdfbox.cos.COSFloat;
import org.apache.pdfbox.cos.COSName;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.graphics.color.PDColor;
import org.apache.pdfbox.pdmodel.graphics.color.PDDeviceRGB;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotation;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationTextMarkup;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.pdfbox.text.PDFTextStripperByArea;
import org.apache.pdfbox.text.TextPosition;

public class HighlightPDFToOntology extends PDFTextStripper {

	public HighlightPDFToOntology() throws IOException {
		super();
	}

	private static final String ONTOLOGY_OUTPUT_FILE = "C:\\PIRI-HighlightPDFToOntology-ontology.ttl";
	private static final String PDF_INPUT_PATH = "C:\\manualpdfhighlight\\";
	private static final String LOG_OUTPUT_FILE = "C:\\log-HighlightPDFToOntology.txt";
	private static final String ONTOLOGY_INPUT_FILE = "C:\\ontology.rdf";
	private static final String NS_PIRI = "http://www.angesagt-gmbh.de/piri#";
	private static final String NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#";
	private static final String NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";

	public static Analyzer analyzer = new EnglishAnalyzer();

	public static void main(String[] args) throws Exception {

		long start = System.currentTimeMillis();

		// create logfile
		PrintWriter LogWriter;
		LogWriter = new PrintWriter(LOG_OUTPUT_FILE, "UTF-8");

		FileOutputStream out = new FileOutputStream(ONTOLOGY_OUTPUT_FILE);
		PrintStream newOntologyWriter;
		newOntologyWriter = new PrintStream(out, true, "ISO-8859-1");

		// create an empty ontology model for output
		Model modelOut = ModelFactory.createDefaultModel();
		modelOut.setNsPrefix("piri", NS_PIRI);
		modelOut.setNsPrefix("rdfs", NS_RDFS);

		// create an empty ontology model for input
		Model modelIn = ModelFactory.createDefaultModel();
		modelIn.setNsPrefix("piri", NS_PIRI);
		modelIn.setNsPrefix("rdfs", NS_RDFS);

		// use the FileManager to find the ontology input file
		InputStream inOntoStream = FileManager.get().open(ONTOLOGY_INPUT_FILE);
		if (inOntoStream == null) {
			throw new IllegalArgumentException("File: " + ONTOLOGY_INPUT_FILE + " not found");
		}

		// read the RDF/XML file
		modelIn.read(inOntoStream, null);

		// start extraction process
		Path pdfDocDir = Paths.get(PDF_INPUT_PATH);
		indexDocs(modelIn, modelOut, pdfDocDir, LogWriter);

		// log runtime
		long end = System.currentTimeMillis();
		NumberFormat formatter = new DecimalFormat("#0.00000");
		LogWriter.print("Execution time is " + formatter.format((end - start) / 1000d) + " seconds");
		System.out.println(end - start + " total milliseconds");

		// choose between TURTLE and RDF/XML output
		modelOut.write(newOntologyWriter, "TURTLE");
		newOntologyWriter.close();
		LogWriter.close();
		modelOut.close();
		modelIn.close();
	}

	static void indexDoc(Model modelIn, Model modelOut, Path file, long lastModified, PrintWriter LogWriter)
			throws IOException {
		String fileWatch = "";
		int exceptionAtPageNumber = 0;
		try (InputStream stream = Files.newInputStream(file)) {

			String currentFileName = file.getFileName().toString();
			fileWatch = currentFileName;
			String currentInstanceID;
			Resource informationUnit = modelOut.createResource(NS_PIRI + "InformationUnit");

			LogWriter.println("currentFileName: " + currentFileName);

			String[] hasFileResources = ImportExportOntology.getResourceByFile(modelIn, currentFileName + ".txt");
			currentInstanceID = "";
			if (hasFileResources.length == 0) {
				hasFileResources = new String[1];
			} else {
				currentInstanceID = hasFileResources[0].replace("http://www.angesagt-gmbh.de/piri#rg_", "");
				LogWriter.println("ID: " + currentInstanceID);
			}

			// create resource for current regulatory document
			Resource currentRegulatoryDocument = modelOut.createResource(NS_PIRI + "rg_" + currentInstanceID);

			// proof weather file already part of ontology
			if (!ImportExportOntology.proofModelForFile(modelIn, currentFileName + ".txt", LogWriter)) {
				Resource currentRegDoc2 = modelOut.createResource(NS_PIRI + "rg_" + currentInstanceID);
				currentRegDoc2.addProperty(RDFS.label, "Regulatory Concept based on file: " + currentFileName);
				currentRegDoc2.addProperty(PIRI.hasFile, currentFileName);
				currentRegDoc2.addProperty(PIRI.hasTitle, "");
				modelOut.add(currentRegDoc2, RDF.type, PIRI.Document);
				LogWriter.println("> file not part of ontology, stub created: " + currentFileName);
			} else {
				LogWriter.println("> file already part of ontology, stub NOT created: " + currentFileName);
			}

			if (file.toString().toLowerCase().endsWith(".pdf")) {
				PDDocument pddDocument = PDDocument.load(new File(PDF_INPUT_PATH + file.getFileName()));
				List<PDPage> allPages = new ArrayList<>();
				pddDocument.getDocumentCatalog().getPages().forEach(allPages::add);

				for (int p = 0; p < allPages.size(); p++) {
					int pageNum = p + 1;
					exceptionAtPageNumber = pageNum;
					LogWriter.println("\nProcess Page " + pageNum + "...");
					PDPage page = (PDPage) allPages.get(p);
					List<PDAnnotation> annotations = page.getAnnotations();
					LogWriter.println("Total annotations = " + annotations.size());

					for (int i = 0; i < annotations.size(); i++) {
						// check subType
						LogWriter.println("Annotation Subtype = " + annotations.get(i).getSubtype());
						if (annotations.get(i).getSubtype().equals("Highlight")) {
							
							// extract comment
							String commentValue = annotations.get(i).getContents();
							LogWriter.println("Comment Value = " + annotations.get(i).getContents());
							LogWriter.println("Commentend Phrase:" + annotations.get(i).getContents());
							Boolean splitApart = false;
							Boolean multiAnnotations = false;
							String featureValue = "";	
							String partialID = "";
							String partialCounter = "";
							
							//split comma separated multi comments like "incident, fireIncident"
							String[] commaSeparatedFeatures = null;
							if (commentValue!=null) {
								commaSeparatedFeatures = commentValue.split(",");
							};
							
							
							// iterate over features
							for (int j = 0; j < commaSeparatedFeatures.length; j++) {
							commaSeparatedFeatures[j]=commaSeparatedFeatures[j].replaceAll("\\s+","");
								
							//split partial comments
							String[] commentParts = null;
							if (commentValue!=null) {
								commentParts = commaSeparatedFeatures[j].split("-");
							};
							//System.out.println(commentParts.length);
							if(commentParts.length==1) {
								splitApart = false;
								featureValue = commaSeparatedFeatures[j]+"RootNuclearSafety";	
								
							}
							else {
								splitApart = true;
								featureValue = commentParts[0]+"RootNuclearSafety";	
								partialID = commentParts[1];
								partialCounter = commentParts[3];
							}
							
							if (commentValue.contains("-part-")) {
								//write all parts to Datastructure
								//at the end sort Datastructure and write to Ontology
								writeInformationUnitToOntology(modelOut, currentInstanceID, splitApart, featureValue, partialID, partialCounter, page, pageNum, informationUnit, currentRegulatoryDocument, annotations, p, i, LogWriter);
							}
							else {
								writeInformationUnitToOntology(modelOut, currentInstanceID, splitApart, featureValue, partialID, partialCounter, page, pageNum, informationUnit, currentRegulatoryDocument, annotations, p, i, LogWriter);
							}
						}
						}
					}
				}
				pddDocument.close();
			} else {
				// skip other than PDF
			}
		} catch (Exception e) {
			// TODO Auto-generated catch block
			System.out.println("Exception at fileName: "+fileWatch+" page:"+exceptionAtPageNumber);
			e.printStackTrace();
			LogWriter.println(e.toString());
		}
	}

	static void indexDocs(final Model inModel, Model outModel, Path path, PrintWriter LogWriter) throws IOException {
		if (Files.isDirectory(path)) {
			Files.walkFileTree(path, new SimpleFileVisitor<Path>() {
				@Override
				public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
					try {
						indexDoc(inModel, outModel, file, attrs.lastModifiedTime().toMillis(), LogWriter);
					} catch (IOException ignore) {
						// don't index files that can't be read.
						ignore.printStackTrace();
						LogWriter.println(ignore.toString());
					}
					return FileVisitResult.CONTINUE;
				}
			});
		} else {
			indexDoc(inModel, outModel, path, Files.getLastModifiedTime(path).toMillis(), LogWriter);
		}
	}
	
	static void writeInformationUnitToOntology(Model modelOut, String currentInstanceID, Boolean splitApart, String featureValue, String partialID, String partialCounter, PDPage page, int pageNum, Resource informationUnit, Resource currentRegulatoryDocument, List<PDAnnotation> annotations, int p, int i, PrintWriter LogWriter) throws IOException {
		LogWriter.println("Getting text from comment = " + featureValue);
		LogWriter.println("Page Object = " + page);
		// extract highlighted text
		PDFTextStripperByArea stripperByArea = new PDFTextStripperByArea();

		COSArray quadsArray = (COSArray) annotations.get(i).getCOSObject()
				.getDictionaryObject(COSName.getPDFName("QuadPoints"));
		
		LogWriter.println("Getting quadsArray = " + annotations.get(i).getCOSObject()
				.getDictionaryObject(COSName.getPDFName("QuadPoints")));
		
		String str = null;

		// create ontology resource for annotated information unit
		Resource currentInformationUnit = modelOut.createResource(
				NS_PIRI + "informationUnit" + "_" + currentInstanceID + "_" + (p + 1) * (i + 1));
		
		// if information unit is split apart, insert relevant infos
		if(splitApart) {
			currentInformationUnit.addProperty(PIRI.hasPartialID, partialID);
			currentInformationUnit.addProperty(PIRI.hasPartialCounter, partialCounter);
		}
		
		Resource currentAnnotation = modelOut.createResource(NS_PIRI + featureValue);
		System.out.println("featureValue: "+featureValue);
		currentInformationUnit.addProperty(PIRI.hasPDFAnnotation, currentAnnotation);

		// get all highlighted quad points
		for (int j = 1, k = 0; j <= (quadsArray.size() / 8); j++) {

			COSFloat ULX = (COSFloat) quadsArray.get(0 + k);
			COSFloat ULY = (COSFloat) quadsArray.get(1 + k);
			COSFloat URX = (COSFloat) quadsArray.get(2 + k);
			COSFloat URY = (COSFloat) quadsArray.get(3 + k);
			COSFloat LLX = (COSFloat) quadsArray.get(4 + k);
			COSFloat LLY = (COSFloat) quadsArray.get(5 + k);
			COSFloat LRX = (COSFloat) quadsArray.get(6 + k);
			COSFloat LRY = (COSFloat) quadsArray.get(7 + k);

			k += 8;

			float ulx = ULX.floatValue() - 1; // upper left x.
			float uly = ULY.floatValue(); // upper left y.
			float width = URX.floatValue() - LLX.floatValue(); 
			// calculated by upperRightX - lowerLeftX
			
			float height = URY.floatValue() - LLY.floatValue(); 
			// calculated by upperRightY - lowerLeftY.

			// get media box
			PDRectangle pageSize = page.getMediaBox();
			PDRectangle pageArtBox = page.getArtBox();
			LogWriter.println("media Box = " + page.getMediaBox());
			LogWriter.println("Art Box = " + page.getArtBox() + "" + pageArtBox.getLowerLeftX() + "" + pageArtBox.getLowerLeftY());
			LogWriter.println("Bleed Box = " + page.getBleedBox());
			LogWriter.println("Trim Box = " + page.getTrimBox());
			LogWriter.println("Crop Box = " + page.getCropBox());
			LogWriter.println("BB Box = " + page.getBBox());
			
			// get page height
			uly = pageSize.getHeight() - uly - pageArtBox.getLowerLeftY();
			LogWriter.println("page Size height = " + pageSize.getHeight());
			LogWriter.println("page Size width = " + pageSize.getWidth());
			
			ulx = ulx - pageArtBox.getLowerLeftX();
			
			
			// create java rectangle
			Rectangle2D.Float rectangle_2 = new Rectangle2D.Float(ulx, uly, width, height);
			LogWriter.println("java rectangle = " + rectangle_2);
			
			// write offset to ontology resource
			currentInformationUnit.addProperty(PIRI.hasOffset, "" + rectangle_2);
			currentInformationUnit.addProperty(PIRI.hasPageNumber, "" + pageNum);
			
			//System.out.println("Getting text from region = " + rectangle_2 + "\n");
			stripperByArea.addRegion("highlightedRegion", rectangle_2);
			stripperByArea.extractRegions(page);
			String highlightedText = stripperByArea.getTextForRegion("highlightedRegion");

			if (j > 1) {
				str = str.concat(highlightedText);
			} else {
				str = highlightedText;
			}
		}
		// Write annotation string to console
		//System.out.println(str);

		// Write information unit to output ontology
		currentInformationUnit.addProperty(RDF.type, informationUnit);
		currentInformationUnit.addProperty(PIRI.broader, currentRegulatoryDocument);

		String sanitizedContent = ImportExportOntology.sanitizeXmlChars(str.toString());
		sanitizedContent = sanitizedContent.replace("\r", " ");
		sanitizedContent = sanitizedContent.replace("\t", " ");
		sanitizedContent = sanitizedContent.replace("\n", " ");
		currentInformationUnit.addProperty(PIRI.hasPhrase, sanitizedContent);
		LogWriter.println("Phrase: " + sanitizedContent);
	}
	

}
