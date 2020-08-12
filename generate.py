from urllib.request import urlopen
from urllib.parse import  urljoin, urlsplit, urlunsplit, urldefrag, quote
from os.path import split, join
import re

from bs4 import BeautifulSoup
import spacy

from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib.namespace import SKOS, DCTERMS, Namespace, OWL, ALLOWED_NAME_CHARS, FOAF, RDFS

from datetime import date

nlp = spacy.load("en_core_web_sm")
stopwords = nlp.Defaults.stop_words
lemmatizer = nlp.vocab.morphology.lemmatizer

ALLOWED_NAME_CHARS += ["(", ")"]

ALMA_NS = "http://purl.org/lu/uni/alma/"
SCHEME_NAME = 'swift'
LANGUAGE_VERSION = '5.2'
ONTOLOGY_VERSION = '1.0.0'
DATE_CREATED = '2020-04-27'
DATE_MODIFIED = date.today().strftime("%Y-%m-%d")
AUTHOR_NAME = "Christian GREVISSE"
AUTHOR_EMAIL = "christian.grevisse@uni.lu"

SERIALIZATION_FORMATS = { 'xml': 'xml', 'turtle': 'ttl' }

def lstrip_stopwords(chunk):
    for i, token in enumerate(chunk):
        if token.text not in stopwords or (i+1 < len(chunk) and chunk[i+1].pos_ == "PUNCT"): # avoid removing combined words starting with a stop word (e.g. two-phased)
            return chunk[i:]
    return chunk

def lemmatize(chunk):
    tokens = []

    for token in chunk:
        if token.pos_ == 'NOUN':
            tokens.append(token.lemma_)
        else:
            tokens.append(token.text)
        tokens.append(token.whitespace_)

    return "".join(tokens)

def strip_fragment(url):
    return urldefrag(url)[0]

def page_included(newURL, links):
    return strip_fragment(newURL) in list(map(lambda x: strip_fragment(x), links))

def replaceAll(s, chars, replacement):
    for c in chars:
        s = s.replace(c, replacement)
    return s

def cleanse(s):
    digits = [str(i) for i in range(10)]
    hyphens = ['_', '-']
    misc = ['’']

    s = replaceAll(s, misc + digits, '')
    s = replaceAll(s, hyphens, ' ')

    # title case and remove spaces
    s = s.title().replace(' ', '')

    # check for other symbols
    invalidSymbols = list(set([i for i in s if not i.isalpha()]))
    for symbol in invalidSymbols:
        s = s.replace(symbol, '')

    return s

def main():

    # Parse Swift book to retrieve concepts and related resources
    start = "https://docs.swift.org/swift-book/"
    nextURL = start
    urls = [nextURL]

    concepts = {}

    while nextURL:
        url = nextURL
        page = urlopen(url)
        soup = BeautifulSoup(page, 'html.parser')

        #title = soup.find('title').string

        article = soup.select_one('article.page')
        headings = article.find_all(re.compile('^h[1-6]$'))

        for heading in headings:
            heading_text = str(heading.contents[0]).lower()
            permalink = url + heading.contents[1].get('href')

            doc = nlp(heading_text)

            noun_phrases = [chunk for chunk in doc.noun_chunks]

            if len(noun_phrases) > 0:
                new_concepts = [lemmatize(lstrip_stopwords(chunk)).strip() for chunk in noun_phrases]
            else:
                # if no noun-phrases, take as verbatim (e.g. break, continue)
                new_concepts = [heading_text]

            for c in new_concepts:
                if c not in concepts:
                    concepts[c] = []
                if permalink not in concepts[c]:
                    # optionally: don't add if permalink (apart from fragment) is already contained (to avoid reindexing the same page multiple times, as a concept like "Function" might appear many times on its dedicated page in different headers)
                    if not page_included(permalink, concepts[c]):
                        concepts[c].append(permalink)

        # continue to next page (if any)
        nextLink = soup.select_one("p.next a")

        if nextLink:
            parts = urlsplit(nextURL)
            base_path, _ = split(parts.path)
            base_url = urlunsplit((parts.scheme, parts.netloc, join(base_path, ""), parts.query, parts.fragment))
            nextURL = urljoin(base_url, nextLink.get('href'))
            urls.append(nextURL)
        else:
            nextURL = None

    # RDF Graph creation
    g = Graph()

    # Namespace bindings
    NS = Namespace(ALMA_NS + SCHEME_NAME + "#")
    DBPEDIA = Namespace('http://dbpedia.org/page/')
    g.namespace_manager.bind('owl', OWL)
    g.namespace_manager.bind('skos', SKOS)
    g.namespace_manager.bind('dct', DCTERMS)
    g.namespace_manager.bind('foaf', FOAF)
    g.namespace_manager.bind('dbr', DBPEDIA)
    g.namespace_manager.bind(SCHEME_NAME, NS)

    # Ontology Metadata
    ontology = URIRef(ALMA_NS + SCHEME_NAME)
    g.add((ontology, RDF.type, OWL.term("Ontology")))
    g.add((ontology, DCTERMS.term("title"), Literal("{} Ontology".format(SCHEME_NAME.title()))))
    g.add((ontology, DCTERMS.term("description"), Literal("This is an SKOS-based lightweight ontology about the Swift programming language.")))
    g.add((ontology, DCTERMS.term("subject"), URIRef(quote("http://dbpedia.org/page/Swift_(programming_language)"))))
    g.add((ontology, DCTERMS.term("license"), URIRef("https://creativecommons.org/licenses/by-sa/4.0/")))
    g.add((ontology, DCTERMS.term("created"), Literal(DATE_CREATED)))
    g.add((ontology, DCTERMS.term("modified"), Literal(DATE_MODIFIED)))
    g.add((ontology, RDFS.term("seeAlso"), URIRef("https://coast.uni.lu/alma/")))
    g.add((ontology, OWL.term("versionIRI"), URIRef("http://purl.org/lu/uni/alma/{}/{}".format(SCHEME_NAME, LANGUAGE_VERSION))))
    g.add((ontology, OWL.term("versionInfo"), Literal("{}/{}".format(LANGUAGE_VERSION, ONTOLOGY_VERSION))))
    g.add((ontology, OWL.term("imports"), URIRef("http://www.w3.org/2004/02/skos/core")))
    creator = BNode()
    g.add((ontology, DCTERMS.term("creator"), creator))
    g.add((creator, RDF.type, FOAF.term("Person")))
    g.add((creator, FOAF.term("name"), Literal(AUTHOR_NAME)))
    g.add((creator, FOAF.term("mbox"), URIRef(AUTHOR_EMAIL)))

    # Concept Scheme
    schemeURI = NS.term("Scheme")
    g.add((schemeURI, RDF.type, SKOS.term("ConceptScheme")))
    g.add((schemeURI, DCTERMS.term("title"), Literal(SCHEME_NAME.title())))

    # Concepts
    for (concept, urls) in concepts.items():
        conceptURI = NS.term(cleanse(concept))
        prefLabel = concept.title()
        g.add((conceptURI, RDF.type, SKOS.term("Concept")))
        g.add((conceptURI, RDF.type, OWL.term("NamedIndividual")))
        g.add((conceptURI, SKOS.term("inScheme"), schemeURI))
        g.add((conceptURI, SKOS.term("prefLabel"), Literal(prefLabel, lang='en')))

        # Resources from Swift book
        for url in urls:
            g.add((conceptURI, SKOS.term("definition"), URIRef(url)))

    # Serialization
    for (format, file_extension) in SERIALIZATION_FORMATS.items():
        file_name = "{}_{}_{}.{}".format(SCHEME_NAME, LANGUAGE_VERSION, ONTOLOGY_VERSION, file_extension)
        g.serialize(format=format, destination=file_name)
        print("Saved under {}".format(file_name))

    print("# triples:", len(g))

if __name__ == "__main__":
    main()
