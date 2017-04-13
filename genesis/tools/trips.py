from diesel.lexicon import load_lexicon
from diesel.ontology import load_ontology

import os

TRIPSPATH = os.environ.get("TRIPS_BASE_PATH", None)

if TRIPSPATH is None:
    raise FileNotFoundError(
        "Please point $TRIPS_BASE_PATH to your local copy of TRIPS"
    )

lexpath = os.path.join(TRIPSPATH, "etc", "XMLTrips", "lexicon", "data")
templpath = os.path.join(TRIPSPATH, "src", "LexiconManager", "Data", "templates")


lexicon = load_lexicon(lexpath, templpath)
ontology = load_ontology(lexpath)


__all__ = ["lexicon", "ontology"]
