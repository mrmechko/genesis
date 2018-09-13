from diesel.lexicon import load_lexicon
from diesel.ontology import load_ontology

import os
import math
import sys

TRIPSPATH = os.environ.get("TRIPS_BASE_PATH", None)
TRIPSXMLPATH = os.environ.get("tripsXMLPath", None)

if TRIPSPATH is None:
    raise FileNotFoundError(
        "Please point $TRIPS_BASE_PATH to your local copy of TRIPS"
    )

lexpath=TRIPSXMLPATH

if TRIPSXMLPATH is None:
    print("$tripsXMLPath is not set.  Defaulting to $TRIPS_BASE_PATH.  This will not work if TRIPS is not compiled", file=sys.stderr)
    lexpath=os.path.join(TRIPSPATH, "etc", "XMLTrips", "lexicon", "data")

templpath = os.path.join(TRIPSPATH, "src", "LexiconManager", "Data", "templates")


lexicon = load_lexicon(lexpath, templpath)
ontology = load_ontology(lexpath)


# convenient ont and lex lookups
def lexlookup(w, pos=None):
    """extract just the onttypes from a lexical lookup.  Add to genesis"""
    lc = lexicon.lookup(w, pos)
    res = set()
    for w in lc:
        for cls in w.lexclasses:
            g = ontology.get(cls.onttype)
            if g:
                res.add(g)
    return res

def ontlookup(w, pos=None, max_depth=3):
    """Get all proposed trips types from lexical, wordnet, and ont lookup."""
    ontset = set(ontology.lookup(w, wordnet_only=True, pos=pos, max_depth=max_depth))
    ontset.update(lexlookup(w, pos=pos))
    return list(ontset)


def sensenum(sense):
    return int(sense.name().split(".")[-1])

def weighted_lookup(w, pos=None, max_depth=3):
    wnweights = ontology.lookup(w, wordnet_only=True, pos=pos, max_depth=max_depth, with_hierarchy=True)
    decay = {}
    for x in wnweights:
        if type(x) is tuple:
            tps, ks = x
            for t in tps:
                decay[t] = min(decay.get(t, 99), 1 + math.log(sensenum(ks[0])))
        else:
            decay[x] = 1
    for x in lexlookup(w, pos=pos):
        decay[x] = 1
    return decay


__all__ = ["lexicon", "ontology", "lexlookup", "ontlookup", "weighted_lookup"]
