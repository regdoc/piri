//PDF-Highlighting

package de.regdoc;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.List;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.graphics.color.PDColor;
import org.apache.pdfbox.pdmodel.graphics.color.PDDeviceRGB;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotation;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationTextMarkup;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.pdfbox.text.TextPosition;

public class PDFHighlight extends PDFTextStripper {

	private static final String fileName = "C:\\PDF.pdf";
	
    public PDFHighlight()  throws IOException {
        super();
    }

    public static void main(String[] args)  throws IOException {
        PDDocument document = null;
        
        try {
            document = PDDocument.load( new File(fileName) );
            PDFTextStripper stripper = new PDFHighlight();
            stripper.setSortByPosition( true );

            stripper.setStartPage( 0 );
            stripper.setEndPage( document.getNumberOfPages() );

            Writer dummy = new OutputStreamWriter(new ByteArrayOutputStream());
            stripper.writeText(document, dummy);

            File file1 = new File("C:\\PDF-new.pdf");
            document.save(file1);
        }
        finally {
            if( document != null ) {
                document.close();
            }
        }
    }

    @Override
    protected void writeString(String string, List<TextPosition> textPositions) throws IOException {
        boolean isFound = false;
        float posXInit  = 0, 
              posXEnd   = 0, 
              posYInit  = 0,
              posYEnd   = 0,
              width     = 0, 
              height    = 0, 
              fontHeight = 0;
        String[] criteria = {"fire", "alarm"};

        for (int i = 0; i < criteria.length; i++) {
            if (string.contains(criteria[i])) {
                isFound = true;
           
        if (isFound) {
            posXInit = textPositions.get(0).getXDirAdj();
            posXEnd  = textPositions.get(textPositions.size() - 1).getXDirAdj() + textPositions.get(textPositions.size() - 1).getWidth();
            posYInit = textPositions.get(0).getPageHeight() - textPositions.get(0).getYDirAdj();
            posYEnd  = textPositions.get(0).getPageHeight() - textPositions.get(textPositions.size() - 1).getYDirAdj();
            width    = textPositions.get(0).getWidthDirAdj();
            height   = textPositions.get(0).getHeightDir();

            System.out.println(string + "X-Init = " + posXInit + "; Y-Init = " + posYInit + "; X-End = " + posXEnd + "; Y-End = " + posYEnd + "; Font-Height = " + fontHeight);

            float quadPoints[] = {posXInit, posYEnd + height + 2, posXEnd, posYEnd + height + 2, posXInit, posYInit - 2, posXEnd, posYEnd - 2};

            List<PDAnnotation> annotations = document.getPage(this.getCurrentPageNo() - 1).getAnnotations();
            PDAnnotationTextMarkup highlight = new PDAnnotationTextMarkup(PDAnnotationTextMarkup.SUB_TYPE_HIGHLIGHT);

            PDRectangle position = new PDRectangle();
            position.setLowerLeftX(posXInit);
            position.setLowerLeftY(posYEnd);
            position.setUpperRightX(posXEnd);
            position.setUpperRightY(posYEnd + height);

            highlight.setRectangle(position);

            highlight.setQuadPoints(quadPoints);

            PDColor red = new PDColor(new float[]{1.0f, 0.0f, 0.0f}, PDDeviceRGB.INSTANCE);
            PDColor green = new PDColor(new float[]{0.0f, 1.0f, 0.0f}, PDDeviceRGB.INSTANCE);
            PDColor actualColor = red;
            
            if(i==0) {actualColor = red;}
            if(i==1) {actualColor = green;}
          
            highlight.setColor(actualColor);
            annotations.add(highlight);
        }
            } 
        }
    }

}
