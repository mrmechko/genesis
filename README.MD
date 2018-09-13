# Environment

```
export tripsXMLPATH=[path to your local copy of mrmechko/flaming-tyrion]
export TRIPS_BASE_PATH=[path to your local trips files (doesn't need to be compiled)]
```

# basic running

```
from genesis.tools.trips import ontology as ont
from genesis.tools.spacy import nlp
from genesis.tools.lextagger import lookup_all

ont.get("bread") # should return ontology node for bread
sentence = nlp("I like bread") # returns a spacy annotated sentence involving bread

bread = sentence[2]

lookup_all(bread) # does a full syntactic/semantic lookup for bread, using wordnet, morphology, and the ontology
```
