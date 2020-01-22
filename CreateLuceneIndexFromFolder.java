//create a lucene index with term vectors and offsets from data in english language

package de.regdoc;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Date;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.FieldType;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.IndexOptions;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.IndexWriterConfig.OpenMode;
import org.apache.lucene.index.Term;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

public class CreateLuceneIndexFromFolder {

	private static final String LOG_OUTPUT_FILE = "log-CreateLuceneIndex.txt";
	
	public static void main(String[] args) throws IOException {
		PrintWriter LogWriter;
		LogWriter = new PrintWriter(LOG_OUTPUT_FILE, "UTF-8");
		
		String indexPath = "C:\\index\\";
		String docsPath = "C:\\data\\";
		boolean create = false;

		final Path docDir = Paths.get(docsPath);
		System.out.println("Document directory '" + docDir.toAbsolutePath() + "' ");

		Date start = new Date();

		System.out.println("Indexing to directory '" + indexPath + "'...");

		Directory dir = FSDirectory.open(Paths.get(indexPath));
	
		Analyzer analyzer = new EnglishAnalyzer();
		IndexWriterConfig iwc = new IndexWriterConfig(analyzer);

		if (create) {
			// Create a new index in the directory, removing any previously indexed documents:
			iwc.setOpenMode(OpenMode.CREATE);
		} else {
			// Add new documents to an existing index:
			iwc.setOpenMode(OpenMode.CREATE_OR_APPEND);
		}

		IndexWriter writer = new IndexWriter(dir, iwc);
		indexDocs(writer, docDir, LogWriter);
		
		 writer.close();
		 LogWriter.close();
		 Date end = new Date();
		 System.out.println(end.getTime() - start.getTime() + " total milliseconds");
	}
	
	static void indexDoc(IndexWriter writer, Path file, long lastModified, PrintWriter LogWriter) throws IOException {
		try (InputStream stream = Files.newInputStream(file)) {
			
			if (file.toString().toLowerCase().endsWith(".pdf"))
            {
				// skip PDF-files
            }
			else {
			Document doc = new Document();

			FieldType MY_FIELD_TYPE = new FieldType(TextField.TYPE_STORED);
			MY_FIELD_TYPE.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS_AND_OFFSETS);
			MY_FIELD_TYPE.setTokenized(true);
			MY_FIELD_TYPE.setStored(true);
			MY_FIELD_TYPE.setStoreTermVectors(true);
			MY_FIELD_TYPE.setStoreTermVectorPositions(true);
			MY_FIELD_TYPE.setStoreTermVectorOffsets(true);
			MY_FIELD_TYPE.freeze();
				
			Field pathField = new Field("path", file.toString(), MY_FIELD_TYPE);
			doc.add(pathField);

			String documentText = "";
			
			FileReader fr = new FileReader(file.toString());
			BufferedReader br = new BufferedReader(fr);
			
			BufferedReader in = new BufferedReader(
					   new InputStreamReader(
			                      new FileInputStream(file.toString()), "UTF8"));
			
            String sCurrentLine;

            while ((sCurrentLine = in.readLine()) != null) {

                   documentText += (sCurrentLine);
                   LogWriter.println(sCurrentLine);

            }
			
			doc.add(new Field("contents", documentText , MY_FIELD_TYPE));

			if (writer.getConfig().getOpenMode() == OpenMode.CREATE) {
				System.out.println("adding " + file);
				writer.addDocument(doc);
			} else {
				System.out.println("updating " + file);
				writer.updateDocument(new Term("path", file.toString()), doc);
			}
			}
		}
	}

	
	static void indexDocs(final IndexWriter writer, Path path, PrintWriter LogWriter) throws IOException {
		if (Files.isDirectory(path)) {
			Files.walkFileTree(path, new SimpleFileVisitor<Path>() {
				@Override
				public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
					try {
						indexDoc(writer, file, attrs.lastModifiedTime().toMillis(), LogWriter);
					} catch (IOException ignore) {
						// don't index files that can't be read.
					}
					return FileVisitResult.CONTINUE;
				}
			});
		} else {
			indexDoc(writer, path, Files.getLastModifiedTime(path).toMillis(), LogWriter);
		}
	}

}
