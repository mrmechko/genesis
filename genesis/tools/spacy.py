import spacy
import copy

nlp = spacy.load('en')

tag_map = nlp.vocab.morphology.tag_map


def deep_syntax(token):
    tags = copy.deepcopy(tag_map.get(token.tag_, None))
    if tags is None:
        return {}
    if "Other" in tags:
        other = tags["Other"]
        del tags["Other"]
        for k in other:
            tags[k] = other[k]
    # convert all tags to strings
    conv = {}
    for t, v in tags.items():
        if type(t) is int:
            t = nlp.vocab[t].norm_
        if type(v) is int:
            v = nlp.vocab[v].norm_
        conv[t.lower()] = v.lower()
    return conv
