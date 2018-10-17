from .symbols import get_pos
from .spacy import deep_syntax, nlp
from .lextagger import normalize_spacy_to_trips, lookup_lexicon_type, lookup_wordnet_type

from .lextagger import BIG_CACHE


def extract_types(res):
    """WN are returned as [([types], [wn]) ...]"""
    lex, wn = res
    wn = [r[0] for r in wn]
    res = set(lex)
    for w in wn:
        res.update(w)
    return res

def lookup_types(token, pos=None, wndepth=3):
    if not pos:
        pos = get_pos(token, deep_syntax(token))
    token = normalize_spacy_to_trips(token.text.lower())
    if pos:
        pos = pos[0]
        if token not in BIG_CACHE[pos]:
            res = (lookup_lexicon_type(token, pos), lookup_wordnet_type(token, pos))
            BIG_CACHE[pos][token] = extract_types(res)
        return BIG_CACHE[pos][token]
    return set()

def lookup_types_sentence(sentence, wndepth=3):
    sentence = nlp(sentence)
    return zip(sentence, [lookup_types(t, wndepth=wndepth) for t in sentence])
