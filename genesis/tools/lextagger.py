from .spacy import nlp, deep_syntax
from .trips import lexicon, ontology
from .symbols import get_pos, guess_cat


def normalize_spacy_to_trips(token):
    conversions = [("’", "^"), ("'", "^")]
    for c in conversions:
        token = token.replace(c[0], c[1])
    return token


def lookup_token_from_lexicon(token, surrogate=None):
    ds = deep_syntax(token)
    tok = normalize_spacy_to_trips(token.text)
    g_cat = guess_cat(tok, ds)
    g_pos = get_pos(tok, ds)
    if surrogate:
        tok = surrogate

    # If nothing in g_pos returns the word, check if the word exists using a specific trips pos
    # otherwise, fallback to g_pos and use wn
    if g_pos:
        words = []
        for p in g_pos:
            words.extend(lexicon.lookup(tok, p))
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


def lookup_token_from_wordnet(token):
    ds = deep_syntax(token)
    tok = normalize_spacy_to_trips(token.text)
    g_pos = get_pos(token, ds)
    g_pos = [p for p in g_pos if p in {"n", "v", "adj", "adv"}]
    if not g_pos:  # not a wordnet pos so ignore
        return []
    collected = []
    for p in g_pos:
        ots = [n for n in ontology.lookup(tok, wordnet_only=True, pos=p, with_hierarchy=True)]
        for t in ots:
            for t_ in t[0]:
                collected.append(WNLexItem(token, t_, p, t[1]))
    return collected


def lookup_all(token):
    lex = lookup_token_from_lexicon(token)
    wnl = lookup_token_from_wordnet(token)
    wnl = WNLexItem.collect(wnl)
    return lex, wnl


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


# class LexicalInfo:
#     def __init__(self, token):
#         self.token = token
#         self.guess_cats = []
#         self.guess_pos = []
#         self.lex_cats = []
#         self.lex_pos = []
#         self.lex_words = []
#
#         self._guess_lexical_tags()
#
#         self.filt_cat = self._filter_cats()
#         self.filt_pos = self._filter_pos()
#         self.hypotheses = self._filter_lex_words()
#         self.wnhyps = []
#         self.generate_wordnet_hypotheses()
#
#     def describe(self):
#         types = set()
#         for t in self.hypotheses:
#             for c in t.lexclasses:
#                 types.add(c)
#         description = self.token.text
#
#     def verbose(self):
#         types = set()
#         for t in self.hypotheses:
#             for c in t.lexclasses:
#                 types.add(c)
#         templs = [[x.name for x in t.templates] for t in types]
#         types = [t.onttype for t in types]
#
#         return """
#         text: {}
#         spacy_lem: {}
#         inferred_cats: {}
#         possible_cats: {}
#         inferred_pos: {}
#         possible_pos: {}
#         filtered_cats: {}
#         filtered_poss: {}
#         possible_lexs: {}
#         hypotheses: {}
#         templates: {}
#         onttypes: {}
#         wnhyps: {}
#         """.format(
#             self.token.text,
#             self.token.lemma_,
#             self.guess_cats,
#             self.lex_cats,
#             self.guess_pos,
#             self.lex_pos,
#             self.filt_cat,
#             self.filt_pos,
#             self.lex_words,
#             self.hypotheses,
#             templs,
#             types,
#             [".".join(x) for x in self.wnhyps]
#         )
#
#     def generate_wordnet_hypotheses(self):
#         self.wnhyps = []
#         for p in self.filt_pos:
#             types = [t.name for t in ontology.lookup(self.token.lemma_, wordnet_only=True, max_depth=3, pos=p)]
#             for t in types:
#                 self.wnhyps.append((t, p))
#
#     def _filter_cats(self):
#         cats = list(set(self.guess_cats).intersection(set(self.lex_cats)))
#         if cats:
#             return cats
#         else:
#             return self.lex_cats[:]
#
#     def _filter_pos(self):
#         pos = list(set(self.guess_pos).intersection(set(self.lex_pos)))
#         if pos:
#             return pos
#         else:
#             return self.lex_pos[:]
#
#     def _filter_lex_words(self):
#         words = [w for w in self.lex_words if w.pos in self.filt_pos]
#         words_cat = [w for w in words if any([w.has_cat(c) for c in self.filt_cat])]
#         if words_cat:
#             return words_cat
#         if words:
#             return words
#         return self.lex_words[:]
#
#     def _guess_lexical_tags(self):
#         """Get lexical tags for a token"""
#         syn = deep_syntax(self.token)
#         tok = normalize_spacy_to_trips(self.token.text)
#         cats = guess_cat(tok, syn)
#         poss = get_pos(tok, syn)
#
#         self.guess_cats = cats
#         self.guess_pos = poss
#
#         lex_morph = lexicon.morph(tok, detailed=True)
#         self.lex_cats = [l.cat for l in lex_morph]
#         self.lex_words = lexicon.lookup(tok)
#         self.lex_pos = list(set([l.pos for l in self.lex_words]))
#
#
# def test(sentence):
#     doc = nlp(sentence)
#     for d in doc:
#         print(LexicalInfo(d).verbose())
