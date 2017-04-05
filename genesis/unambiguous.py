from nltk.corpus import semcor
from nltk.corpus import stopwords
from diesel import ontology
import progressbar
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import pos_tag

ont = ontology.load_ontology("/Users/mechko/Projects/python/truck/tester/trips/etc/XMLTrips/lexicon/data")

english_stopwords = set(stopwords.words('english'))


def get_bar(title="progress", redirect_stdout=False):
    return progressbar.ProgressBar(
        widgets=[title, ' [', progressbar.Timer(), ']', progressbar.Bar(), '(', progressbar.ETA(), ')'],
        redirect_stdout=redirect_stdout
    )


def read_index(idx):
    res = {}
    with open(idx) as index:
        for line in index:
            line = line.strip.split()
            res[line[0]] = res[line[1]]
    return res


def get_simplewiki(fname="simplewiki.txt", word_tokenized=True):
    corp = []
    fl = open(fname)
    swiki = fl.readlines()
    bar = get_bar(title='read simplewiki')
    for line in bar(swiki):
        sentences = sent_tokenize(line.strip())
        if len(sentences) > 1:
            if word_tokenized:
                corp.extend([word_tokenize(s) for s in sentences])
            else:
                corp.extend(sentences)
    return corp


def product(l):
    x = 1
    for y in l:
        if y != 0:
            x *= y
    return x


def is_unambiguous(word, thresh=1, require_meaning=True):
    word = word.lower()
    if word in english_stopwords:
        return True
    amb = len(set([x.name for x in ont.lookup(word)]))
    if require_meaning and amb == 0:
        return False
    return amb < thresh+1


def trim_stops(seq):
    while len(seq) > 0 and seq[0] in english_stopwords:
        seq.pop(0)
    while len(seq) > 0 and seq[-1] in english_stopwords:
        seq.pop()
    return seq


def unamb_subsequences(sentence, thresh=1, amb_thresh=1):
    subseqs = []
    current_seq = []
    for s in sentence:
        if is_unambiguous(s, thresh=amb_thresh):
            current_seq.append(s)
        elif len(trim_stops(current_seq)) > thresh:
            subseqs.append(trim_stops(current_seq))
            current_seq = []
        else:
            current_seq = []
    return subseqs


def get_ambiguity():
    best = []
    corp = get_simplewiki()
    bar = get_bar(title='get ambiguity', redirect_stdout=True)
    for sentence in bar(corp):
        subs = unamb_subsequences(sentence, thresh=4, amb_thresh=2)
        if len(subs) > 1:
            best.append((sentence, subs))
            print(" || ".join([" ".join(sub) for sub in subs]))
        bar.update()
    return best


if __name__ == "__main__":
    best = get_ambiguity()
    print(len(best))
