import spacy
from spacy.symbols import VERB, dobj, nsubj, pobj

from genesis.unambiguous import is_unambiguous, get_bar, get_simplewiki

nlp = spacy.load('en')

ignored_verbs = {"be", "have", "do"}


def dependency_labels_to_root(token):
    """Walk up the syntactic tree, collecting the arc labels."""
    dep_labels = []
    while token.head is not token:
        dep_labels.append(token.dep_)
        token = token.head
    return dep_labels


def tree_is_unambiguous(root):
    children = [c for c in root.children]
    if len(children) == 0 and not is_unambiguous(root.norm_):
        return False
    elif len(children) > 0 and not is_unambiguous(root.norm_, require_meaning=False):
        return False
    return all([tree_is_unambiguous(c) for c in children])


def get_unamb_verb_deps(sentence):
    sentence = nlp(sentence)
    verbs = []
    for t in sentence:
        children = [c for c in t.children]
        if t.pos == VERB and t.lemma_ not in ignored_verbs and len(children) > 1:
            if tree_is_unambiguous(t):
                verbs.append(t)
    return verbs


def stringified(x, root=True):
    children = [child for child in x.children]
    dep = x.dep_
    if root:
        dep = "root"
    if len(children) == 0:
        return ":{} {}".format(dep, x.norm_+"/"+x.pos_)
    else:
        return "(:{} {} {})".format(
            dep,
            x.norm_+"/"+x.pos_,
            " ".join([stringified(child, root=False) for child in children])
        )


def collect_corpus(corp, func, name="collecting", verbose=False, stringify=lambda x: str(x)):
    res = []
    bar = get_bar(title=name, redirect_stdout=verbose)
    for sentence in bar(corp):
        collected = func(sentence)
        if len(collected) > 0:
            res.append(collected)
            if verbose:
                for c in collected:
                    print(stringify(c))
    return res


def test():
    swiki = get_simplewiki(word_tokenized=False)
    collect_corpus(swiki, get_unamb_verb_deps, verbose=True, stringify=stringified)
