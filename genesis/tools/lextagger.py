from .spacy import nlp, deep_syntax
from .trips import lexicon, ontology
from .symbols import get_pos, guess_cat

from nltk.corpus import stopwords
from collections import defaultdict

sw_en = set(stopwords.words('english'))

CACHE_WORDNET = defaultdict(lambda: defaultdict(list))
CACHE_LEXICON = defaultdict(lambda: defaultdict(list))
BIG_CACHE = defaultdict(lambda: defaultdict(list))


def normalize_spacy_to_trips(token):
    conversions = [("’", "^"), ("'", "^")]
    for c in conversions:
        token = token.replace(c[0], c[1])
    return token

def lookup_lexicon_type(token, pos):
    if not token in CACHE_LEXICON[pos]:
        res = lexicon.lookup(token, pos)
        types = [ontology.get(x.onttype) for x in res.lexclasses]
        types = set([t for t in types if t])
        CACHE_LEXICON[pos][token] = types
    return CACHE_LEXICON[pos][token][:]

def lookup_wordnet_type(token, pos, wndepth=3):
    if token not in CACHE_WORDNET[pos]:
        CACHE_WORDNET[pos][token] = [
            n for n in ontology.lookup(
                token, max_depth=wndepth,
                wordnet_only=True, pos=pos, with_hierarchy=True
                )
        ]
    return CACHE_WORDNET[pos][token][:]

def lookup_token_from_lexicon(token, surrogate=None, syntax=None):
    ds = syntax
    if not syntax:
        ds = deep_syntax(token)
    tok = normalize_spacy_to_trips(token.text.lower())
    g_cat = guess_cat(tok, ds)
    g_pos = get_pos(tok, ds)
    if surrogate:
        tok = surrogate

    # If nothing in g_pos returns the word, check if the word exists using a specific trips pos
    # otherwise, fallback to g_pos and use wn
    if g_pos:
        words = []
        for p in g_pos:
            words.extend(lookup_lex_type(token, pos))
    else:
        words = lexicon.lookup(tok)
    collected = []
    if g_cat:
        for w in words:
            for c in g_cat:
                if w.has_cat(c) or w.word == tok:
                    for cls in w.lexclasses:
                        collected.append(LexItem(token, c, cls))
    else:
        for w in words:
            for cls in w.lexclasses:
                collected.append(LexItem(token, "base", cls))
    return collected


def lookup_token_from_wordnet(token, wndepth=3, syntax=None):
    ds = syntax
    if not syntax:
        ds = deep_syntax(token)
    tok = normalize_spacy_to_trips(token.text.lower())
    g_pos = get_pos(token, ds)
    g_pos = [p for p in g_pos if p in {"n", "v", "adj", "adv"}]
    if not g_pos:  # not a wordnet pos so ignore
        return []
    collected = []
    for p in g_pos:
        ots = lookup_wordnet_type(tok, p)
        for t in ots:
            for t_ in t[0]:
                collected.append(WNLexItem(token, t_, p, t[1]))
    return collected


def lookup_all(token, types_only=False, wndepth=3):
    syntax = deep_syntax(token)
    lex = lookup_token_from_lexicon(token, syntax=syntax)
    wnl = lookup_token_from_wordnet(token, wndepth=wndepth, syntax=syntax)
    if len(lex) + len(wnl) == 0:
        wnl = lookup_token_from_wordnet(token, wndepth=-1)
    wnl = WNLexItem.collect(wnl)
    if types_only:
        lex = [x.wclass.onttype for x in lex]
        wnl = [x[1].wclass.onttype for x in wnl]
        return set(lex + wnl)
    return lex, wnl


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
    return set()]

def lookup_types_sentence(sentence):
    sentence = nlp(sentence)
    return zip(sentence, [lookup_types(t) for t in sentence])

def transform(sentence, wndepth=3):
    sent = nlp(sentence)
    res = []
    for s in sent:
        if s.text.lower() in sw_en:
            res.append(s.text)
            continue
        l = lookup_all(s, types_only=True, wndepth=3)
        if l:
            rem = set()
            for x in l:
                t = ontology.get(x)
                if t and t.parent in l:
                    rem.add(x)
            for x in rem:
                l.remove(x)
            res.append("ONT_" + "_".join(l))
        elif s.ent_type_:
                # squelch numbers
                res.append("ENT_{}".format(s.ent_type_))
        else:
            res.append(s.text)
    return " ".join(res)


class LexItem:
    def __init__(self, token, cat, wclass, wn_ev=None, target_type=None):
        self.token = token
        self.cat = cat
        self.wclass = wclass
        self.wn_ev = None
        self.target_type = target_type

    def set_ev(self, ev):
        self.wn_ev = ev
        return self

    def set_target_type(self, tt):
        self.target_type = tt
        return self

    def __getattr__(self, item):
        return getattr(self.token, item)

    def __str__(self):
        if self.wn_ev:
            return "{}.{}.{}.{}".format(self.token.text, self.cat, self.wclass, self.wn_ev.name())
        return "{}.{}.{}".format(self.token.text, self.cat, self.wclass)

    def __repr__(self):
        return "lex:"+str(self)


class WNLexItem:
    def __init__(self, token, onttype, pos, hierarchy, wclass=None):
        self.token = token
        self.onttype = onttype
        if hierarchy:
            self.hierarchy = hierarchy
        else:
            self.hierarchy = []
        self.pos = pos
        self.wclass = wclass

    def distance(self, li):
        if self.onttype and ontology.get(li.wclass.onttype):
            return ontology.get(li.wclass.onttype).wup(self.onttype)
        return 1.0

    def infer(self):
        words = []
        for h in reversed(self.hierarchy):
            for w in [l for l in h.lemmas()]:
                res = [x.set_ev(w).set_target_type(self.onttype)
                       for x in lookup_token_from_lexicon(self.token, surrogate=w.name())]
                words.extend([(self.distance(x), x) for x in res])
        return [(s,w) for s, w in words if s > 0.7]

    @staticmethod
    def collect(lexitems):
        all_res = []
        for l in lexitems:
            all_res.extend(l.infer())
        all_res = sorted(all_res, key=lambda x: -x[0])
        seen = set()
        seen_tt = set()
        filtered = []
        for s, t in all_res:
            if t.wclass in seen or t.target_type.name in seen_tt:
                continue
            seen.add(t.wclass)
            if t.wclass.onttype:
                seen_tt.add(t.wclass.onttype)
            filtered.append((s, t))
        return filtered

    def __getattr__(self, item):
        return getattr(self.token, item)

    def __str__(self):
        if self.hierarchy:
            return "{}.{}.{}.{}".format(self.token.text, self.onttype, self.pos, self.hierarchy[0])
        else:
            return "{}.{}.{}".format(self.token.text, self.onttype, self.pos)

    def __repr__(self):
        return "wn:"+str(self)
