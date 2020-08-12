# Swift Vocabulary

This repository contains reference serializations and a generation script for the *Swift Vocabulary*, an SKOS-based vocabulary on the Swift programming language. This is a work to appear at the *"Resources Track"* of [ISWC 2020](https://iswc2020.semanticweb.org/).

## Requirements & Usage

To run the `generate.py` script, you first need to install a couple of Python packages:

```bash
pip install beautifulsoup4 spacy spacy-lookups-data rdflib
python3 -m spacy download en_core_web_sm
```

Now you can run the script:

```bash
python3 generate.py
```

It was tested on an Ubuntu 20.04 running Python 3.8, as well as on macOS Catalina (10.15.6) running Python 3.6. The execution takes less than a minute.

## Features

The generation script provides the following features:

- Extraction of concepts & resources from the ["Swift book"](https://docs.swift.org/swift-book/)
- Cleansing of concept names (removing non-alphabetical characters, applying camel case
- Creation of the RDF graph (metadata, concept scheme, concepts & labels, resources)
- Serialization to Turtle & XML format

## Manual Tasks

Some manual curation is needed for the generated files. This can be done, e.g., using [Protégé](https://protege.stanford.edu/).

- Selection of final concepts
- Selection of best resources per concept
- Creation of associative links (`skos:related`) and hierarchical links (`skos:broader`)
- Determination of the scheme's top concepts (`skos:hasTopConcept`)
- Alignment with DBpedia (cf. `dbpedia.txt` for common programming-related DBpedia concepts)

Reference serializations in Turtle and XML format after manual curation can be found in this repository.

## Further References

- [Documentation](http://purl.org/lu/uni/alma/swift)
- [SPARQL endpoint](https://alma.uni.lu/sparql)
- [Swift Semantic](https://github.com/cgrevisse/swift-semantic): A Swift utility to retrieve the main concept from the Swift Vocabulary for a selection in a Swift source file. Based on [SwiftSyntax](https://github.com/apple/swift-syntax).
- [ALMA 4 Code](https://github.com/cgrevisse/alma4code): An extension for [Visual Studio Code](https://code.visualstudio.com/) allowing to retrieve learning material related to a selected piece of code from the ALMA repository. Currently supporting the Swift programming language by using [Swift Semantic](https://github.com/cgrevisse/swift-semantic).
- Swift Vocabulary as a dataset on the [Linked Open Data Cloud](https://lod-cloud.net/dataset/Swift)

## Citation

As a canonical citation, please use:

```
Grévisse, C. and Rothkugel, S. (2020). Swift Vocabulary. http://purl.org/lu/uni/alma/swift
```

The citation to the paper will be provided after its publication.
