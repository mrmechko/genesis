class MorphFeatTemplate:
    feature = "NONE"

    def __init__(self, name, required=None, token_attribute=None):
        self.name = name
        if required is None:
            required = {}
        self.required = required
        self.token_attribute = token_attribute
        if token_attribute is None:
            self.token_attribute = lambda x: True

    def match(self, token, morph):
        for k in self.required:
            if k in morph:
                if type(k) is str and self.required[k] == morph[k]:
                    continue
                if type(self.required[k]) is set and morph[k] in self.required[k]:
                    continue
                else:
                    return False
            else:
                return False

        return self.token_attribute(token)


class Cat(MorphFeatTemplate):
    feature = "CAT"

cat = [
    Cat("pastpart", {"verbvorm": "part", "tense": "past", "pos": "verb"}),
    Cat("past", {"tense": "past", "pos": "verb"}),
    Cat("ly", {"pos": "adj"}, lambda x: x.endswith("ly")),
    Cat("3s", {"pos": "verb", "person": 3, "number": "sing", "tense": "pres"}),
    Cat("est", {"pos": "adj"}, lambda x: x.endswith("est")),
    Cat("er", {}, lambda x: x.endswith("er")),
    Cat("12s123pbase", {"pos": "verb", "tense": "pres"}),
    Cat("sing", {"number": "sing", "pos": "noun"}),
    Cat("plur", {"number": "plur", "pos": "noun"}),
    Cat("ing", {"pos": "verb"}, lambda x: x.endswith("ing")),
    Cat("nom", {"pos": {"noun", "verb"}}),
    Cat("nil", {"pos": "adj"}),
]


def guess_cat(token, morph):
    return [c.name for c in cat if c.match(token, morph)]


class Pos(MorphFeatTemplate):
    feature = "POS"

pos = [
    Pos('n', {"pos": "noun"}),
    Pos('v', {"pos": "verb"}),
    Pos('adj', {"pos": "adj"}),
    Pos('adv', {"pos": "adv"}),
    Pos('prep', {"pos": "adp"}),
    Pos("pro", {"pos": "pron"}),
    Pos('name', {"nountype": "prop"}),
]


def get_pos(token, morph):
    """Only gets basic pos'.  The rest should be inferred from the lexicon"""
    return [c.name for c in pos if c.match(token, morph)]

__all__ = ['guess_cat', 'get_pos']
# synargs: {
#   'lcomp',
#   'lsubj',
#   'liobj',
#   'lobj',
#   'argument',
#   'subcat'
# }

# syncat: {
#   'vp-',
#   'np',
#   't',
#   'advbl',
#   'number',
#   'pp',
#   'cp',
#   'adjp',
#   's',
#   'utt',
#   'pred'
# }
