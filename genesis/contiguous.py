from diesel import ontology
from nltk.corpus import wordnet as wn
from collections import Counter
from itertools import combinations
from collections import defaultdict as ddict

ont = ontology.load_ontology("/Users/mechko/Projects/python/truck/tester/trips/etc/XMLTrips/lexicon/data")


def is_contiguous(types):
    if len(types) == 0:
        return False
    elif len(types) == 1:
        return True
    else:
        swarm = [types.pop(0)]
        adding = True
        while adding:
            iter_types = types[:]
            types = []
            adding = False
            for t in iter_types:
                if t.get_parent() in swarm:
                    swarm.append(t)
                    adding = True
                elif any([c in swarm for c in t.get_children()]):
                    swarm.append(t)
                    adding = True
                else:
                    types.append(t)
        if len(types) > 0:
            return False
        return True


def minimize(types):
    minimal_types = []
    for t in types:
        if any([c in types for c in t.get_children()]):
            continue
        else:
            minimal_types.append(t)
    return minimal_types


def adj(a, b):
    return a.get_parent() == b or b.get_parent() == a


def adj_lists(a, b):
    for x in a:
        for y in b:
            if adj(x, y):
                return True
    return False


def merge(a, b, cl):
    if adj_lists(cl[a], cl[b]):
        cl[a].update(cl[b])
        del cl[b]
        return cl, True
    return cl, False


def clusters(types):
    cl = {t: {t} for t in types}
    changed = True
    while changed:
        changed = False
        keys = list(cl.keys())
        for k1 in keys:
            for k2 in keys:
                if changed or k1 == k2:
                    continue
                cl, changed = merge(k1, k2, cl)
                if changed:
                    continue
    return list(cl.values())


confusable = Counter()
confusable2 = Counter()
confusion = ddict(set)
confusable3 = Counter()

most_confusable = ddict(Counter)

for w in wn.words():
    types = list(set(ont.lookup(w, max_depth=3)))
    if len(minimize(types)) > 1:
        for x in combinations([t.name for t in minimize(types)], 2):
            confusable2[".".join(sorted(x))] += 1
            confusion[".".join(sorted(x))].add(w)
    if len(types) > 1:
        confusable3[".".join(sorted([t.name for t in types]))] += 1

    if len(types) == 0:
        continue
    cl = clusters(types)
    for c in cl:
        if len(c) < 2:
            continue
        for x in combinations([t.name for t in c], 2):
            confusable[".".join(sorted(x))] += 1

    minimal = [minimize(c) for c in cl]
    cond1 = 1 < len(minimal) < 3
    cond2 = len(minimal) == 1 and len(minimal[0]) > 1
    cond3 = any([len(m) > 1 for m in minimal])
    # if cond1 and cond3:
    #     print(w)
    #     print("\t{}".format(", ".join([str(m) for m in minimal])))

print(confusable.most_common(10))
print(sum(confusable.values()))

print(confusable2.most_common(10))
print(sum(confusable2.values()))

print(confusable3.most_common(10))
