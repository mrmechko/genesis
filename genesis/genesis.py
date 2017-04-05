from diesel import ontology
from genesis.structures import Skeleton

ont = ontology.load_ontology("/Users/mechko/Projects/python/truck/tester/trips/etc/XMLTrips/lexicon/data")


def properly_constrained(skel):
    return not any([b.essential() and b.wild for b in skel.bones])

ctr = 0
pcon = set()
for n in ont.data:
    node = ont.get(n)
    if properly_constrained(Skeleton(node)):
        pcon.add(n)
        ctr += 1

weight = {}


def weight_under(name):
    node = ont.get(name)
    if node is None:
        print(name)
        return 0
    if node in weight:
        return weight[name]
    children = node.get_children()
    weight[name] = len(children) + sum([weight_under(c.name) for c in children])
    return weight[name]


def is_ancestor(a, c):
    if type(c) is str:
        c = ont.get(c)
    if c is None:
        return False
    if a == c.name:
        return True
    return is_ancestor(a, c.parent)


if __name__ == "__main__":
    print("{}/{}".format(ctr, weight_under("event-of-action")))

    action_history = []
    frontier = set(["root"])
    expand = True
    # while expand:
    #     action = input("?> ")
    #     if ont.get(action) is None:
    #         print("typo")
    #         continue
    #     print(ont.get(action).get_parent_name())
    #     print(action)
    #     print([str(b) for b in Skeleton(ont.get(action)).bones])
    #     print(ont.get(action).get_child_names())

    from collections import defaultdict as ddict

    unamb = {}
    unamb_rev = ddict(set)

    from nltk.corpus import wordnet as wn

    for word in wn.words():
        if "_" in word:
            continue
        types = set([n.name for n in ont.lookup(word, max_depth=3)])
        if 0 < len(types) < 2:
            for t in list(types):
                unamb[word] = t
                unamb_rev[t].add(word)

    keys = set(unamb_rev.keys())
    ctr = 0
    ctr2 = 0
    ctr3 = 0
    ctr4 = 0

    eoa_pcon = set()
    for n in ont.data:
        if n in keys:
            ctr += 1
            if is_ancestor("event-of-action", n):
                ctr2 += 1
                if n in pcon:
                    ctr3 += 1
                    ctr4 += 1
                    eoa_pcon.add(n)
            elif n in pcon:
                ctr3 += 1
            continue

    print("{}/{}".format(ctr, len(ont.data)))
    print("eoa>{}, pcon:{}, eoa>&pcon:{}".format(ctr2, ctr3, ctr4))

    print(sorted(list(eoa_pcon), key=lambda x: -weight_under(x)))
    print(len(unamb.keys()))
    #
    # for x in eoa_pcon:
    #     print(x)
    #     print("\t{}".format(", ".join(unamb_rev[x])))


    def write_dictionary(r, fname):
        with open(fname, 'w') as out:
            for k in r:
                out.write("{}\t{}\n".format(k, r[k]))


    write_dictionary(unamb, "unamb.txt")
