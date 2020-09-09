# Research corpus for case-based reasoning on regulatory documents, Version 1.0 alpha

Please be patient. The corpus is still in beta condition. We are continously working on the corpus and files. The first stable release will be marked as 1.0 beta

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

### IUCaseBase.csv

This file is created by the JAVA-file PIRIOntologyToCaseBase. Containing all information-unit-cases. This file can be imported in myCBR.

### PIRICaseBase.csv

This file is created by the JAVA-file PIRIOntologyToCaseBase.java. Containing all PIRI-cases. This file can be imported in myCBR.

### PIRI-HighlightPDFToOntology-ontology.ttl

Ontology containing classes created from annotated PDF-files.

### REGDOC-Ontology-Version-1-0-beta.rdf (.ttl) "deprecated"

Ontology containing classes for hierarchical incident and measure classification. For more information have a look at the ontology, classes and porperties are self-describing.

### myCBR-model-PIRI-Fire-Version-1-0-beta.prj

Project-file for myCBR containing the case-based model.

### KnowWE-workspace-Version-1-0-beta.zip

Contains a ready-to-use KnowWE workspace with the implemented ontology identical to the provided RDF- and TTL-files. To set up the semantic wiki, download KnowWE from www.d3web.de and follow the instructions available there.
