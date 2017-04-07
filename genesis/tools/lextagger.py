from .spacy import deep_syntax
from .trips import lexicon
from .symbols import get_pos, guess_cat


def normalize_spacy_to_trips(token):
    conversions = [("’", "^"), ("'", "^")]
    for c in conversions:
        token = token.replace(c[0], c[1])
    return token


class LexicalInfo:
    def __init__(self, token):
        self.token = token
        self.guess_cats = []
        self.guess_pos = []
        self.lex_cats = []
        self.lex_pos = []
        self.lex_words = []

        self._guess_lexical_tags()

        self.filt_cat = self._filter_cats()
        self.filt_pos = self._filter_pos()
        self.hypotheses = self._filter_lex_words()

    def verbose(self):
        return """
        text: {}
        spacy_lem: {}
        inferred_cats: {}
        possible_cats: {}
        inferred_pos: {}
        possible_pos: {}
        filtered_cats: {}
        filtered_poss: {}
        possible_lexs: {}
        hypotheses: {}
        """.format(
            self.token.text,
            self.token.lemma_,
            self.guess_cats,
            self.lex_cats,
            self.guess_pos,
            self.lex_pos,
            self.filt_cat,
            self.filt_pos,
            self.lex_words,
            self.hypotheses
        )

    def generate_wordnet_hypotheses(self):
        pass

    def _filter_cats(self):
        cats = list(set(self.guess_cats).intersection(set(self.lex_cats)))
        if cats:
            return cats
        else:
            return self.lex_cats[:]

    def _filter_pos(self):
        pos = list(set(self.guess_pos).intersection(set(self.lex_pos)))
        if pos:
            return pos
        else:
            return self.lex_pos[:]

    def _filter_lex_words(self):
        words = [w for w in self.lex_words if w.pos in self.filt_pos]
        words_cat = [w for w in words if any([w.has_cat(c) for c in self.filt_cat])]
        if words_cat:
            return words_cat
        if words:
            return words
        return self.lex_words[:]

    def _guess_lexical_tags(self):
        """Get lexical tags for a token"""
        syn = deep_syntax(self.token)
        tok = normalize_spacy_to_trips(self.token.text)
        cats = guess_cat(tok, syn)
        poss = get_pos(tok, syn)

        self.guess_cats = cats
        self.guess_pos = poss

        lex_morph = lexicon.morph(tok, detailed=True)
        self.lex_cats = [l.cat for l in lex_morph]
        self.lex_words = lexicon.lookup(tok)
        self.lex_pos = list(set([l.pos for l in self.lex_words]))
