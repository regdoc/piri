// convert all PDF-files from INPUT_PATH and sub-folders to OUTPUT_PATH, no sophisticated text processing contained!!!

package de.regdoc;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintWriter;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;

public class PdfToText {

	private static final String INPUT_PATH = "C:\\input\\path\\";
	private static final String OUTPUT_PATH = "C:\\output\\path\\";
	
	public static void main(String args[]) throws IOException {

		File f = new File(INPUT_PATH);
		writeTxt(f);
	}

	static void writeTxt(File seedFile) throws IOException {

		File[] files = seedFile.listFiles();

		if (files != null) {
			for (int i = 0; i < files.length; i++) {
				System.out.print(files[i].getAbsolutePath());
				String fileName = files[i].getName().toLowerCase();
				long fileSize = files[i].length();
				if (files[i].isDirectory()) {
					System.out.print(" (Ordner)\n");
					writeTxt(files[i]);
				} else if (fileName.endsWith(".pdf") && fileSize > 0) {
					System.out.print(" (Datei)\n");

					// read document file to String
					FileReader fr = new FileReader(files[i]);
					BufferedReader br = new BufferedReader(fr);
					String docString = "";
					String line;

					// Loading an existing document
					PDDocument document = PDDocument.load(files[i]);

					// Instantiate PDFTextStripper class
					PDFTextStripper pdfStripper = new PDFTextStripper();

					// Retrieving text from PDF document
					String text = pdfStripper.getText(document);
					// System.out.println(text);

					// Write retrieved text to file

					String outputFile = OUTPUT_PATH
							+ files[i].getName() + ".txt";
					PrintWriter writerDocSim;
					writerDocSim = new PrintWriter(outputFile, "UTF-8");
					writerDocSim.println(text);
					writerDocSim.close();

					// end writing

					// Closing the document
					document.close();

				} else {
					System.out.print("Keine PDF-Datei\n");
				}
			}

		}

	}
}
