# Research corpus for case-based reasoning on regulatory documents

Please be patient. The corpus is still in beta condition. We are continously working on the corpus and files. The first stable release will be marked as 1.0 alpha

## Copyright

This is a RESEARCH BODY, NOT real guidance information from the Internatioal Atomic Energy Agency (IAEA). The corpus bases on publications from the IAEA. All rights for IAEA content belong to the IAEA. For direct information and guidance visit www.iaea.org 

For questions on the corpus please write to a.korger[ät]angesagt-gmbh.de

## Files:

### PdfToText.java

Uses Apache PDFBox to convert all PDf-files in a folder to TXT-files.

### CreateLuceneIndexFromFolder.java

Creates a Apache Lucene index from the input folder.
  
### PIRIOntologyToCaseBase.java

Takes an ontology file as input and creates two CSV-files from it. One containing all information-unit-cases and one containing all PIRI-cases derivable from the input ontology.

### REGDOC-Ontology-Version-1-0-beta.rdf (.ttl)

Ontology containing classes for hierarchical incident and measure classification. For more information have a look at the ontology, classes and porperties are self-describing.

### myCBR-model-PIRI-Fire-Version-1-0-beta.prj

Project-file for myCBR containing the case-based model.
