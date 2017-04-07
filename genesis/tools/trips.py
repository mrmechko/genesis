from diesel.lexicon import load_lexicon
from diesel.ontology import load_ontology

import os

BASEPATH = os.environ.get("TRIPS_XML_PATH", None)

if BASEPATH is None:
    raise FileNotFoundError(
        "Please point $TRIPS_XML_PATH to your local copy of http://github.com/mrmechko/flaming-tyrion"
    )

lexpath = os.path.join(BASEPATH, "lexicon", "data")
dslpath = os.path.join(BASEPATH, "lexicon", "dsl")

lexicon = load_lexicon(lexpath, dslpath)
ontology = load_ontology(lexpath)


__all__ = ["lexicon", "ontology"]
