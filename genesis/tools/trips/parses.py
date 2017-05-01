from tripsmodule.trips_module import TripsModule
from tripsmodule.kqml_performative import KQMLPerformative
import random
import tqdm


class GetParse(TripsModule):
    """
    this module is intialized with a single sentence.  The module then requests
    a parse of the sentence, collecting skeletonscore, lf-graph and xml data
    from the facilitator.  When all three have been collected, the module exits
    """

    @staticmethod
    def escape(sentence):
        # first unescape and then re-escape
        return sentence.replace('\\"', '"').replace('"', '\\"')

    def __init__(self, sentence, id=0, argv=None, port=None):
        self.sentence = GetParse.escape(sentence)
        self.parse = None
        self.speechacthyps = None
        self.skeletons = []
        self.lf_graph = None
        self.id = id
        if port is None:
            port = 6200
        if argv is None:
            argv = {}
        TripsModule.__init__(self, argv, port=port)

    def complete(self):
        p = self.parse is not None
        l = self.lf_graph is not None
        s = self.speechacthyps is not None

        return p and l and s

    def init(self):
        self.name = "GetParse-{}".format(self.id)
        TripsModule.init(self)
        self.send(KQMLPerformative.from_string(
            "(subscribe :content (tell &key :content (skelscore . *)))"))
        self.send(KQMLPerformative.from_string(
            "(subscribe :content (tell &key :content (lf-graph . *)))"))
        self.send(KQMLPerformative.from_string(
            "(subscribe :content (tell &key :content (new-speech-act-hyps . *)))"))
        self.ready()
        self.request_sentence_parse(self.sentence)

    def receive_tell(self, msg, content):
        verb = content[0].to_string().lower()
        if verb == "skelscore":
            content = msg.get_parameter(":content")
            score = content.get_keyword_arg(":score")
            to = content.get_keyword_arg(":to")
            match = content.get_keyword_arg(":match")
            self.skeletons.append((score, to, match))
        elif verb == "http":
            cnt = content.get_keyword_arg(":content")
            self.parse = cnt
            if self.complete():
                self.exit(0)
        elif verb == "lf-graph":
            self.lf_graph = content.get_keyword_arg(":content")
            if self.complete():
                self.exit(0)
        elif verb == "new-speech-act-hyps":
            self.speechacthyps = content.to_string()
            if self.complete():
                self.exit(0)

    def request_sentence_parse(self, sentence):
        self.send(KQMLPerformative.from_string(
            """(request :receiver webparser :content
                    (http post "step" :query
                        (:input "{}" :semantic-skeleton-scoring "t")
                    )
                )
            """.format(sentence)
            ))


def main():
    import sys
    gp = GetParse("this is a test sentence", sys.argv[1:])
    # should put gp in its own thread (how?) and then kill it after a minute
    gp.start()
    for h in gp.skeletons:
        print("score: {} {} => {}".format(h[0], h[1], h[2]))
    print(gp.lf_graph)



import signal


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


# using the defined timeout function I can timeout a single function call
# but it needs to mutate the state instead

class tripsparser:
    def __init__(self, trips_base=None, port=None, parameters=None):
        self.parameters = parameters
        if port:
            self.port = port
        else:
            self.port = 6200
        if trips_base:
            self.trips_base = trips_base
        else:
            import os
            tbp = os.environ.get("TRIPS_BASE_PATH")
            if not tbp:
                os.environ.get("TRIPS_BASE")
            if not tbp:
                raise FileNotFoundError("Please point $TRIPS_BASE_PATH to your local copy of TRIPS")
            self.trips_base = tbp
        self.parser = None

    def __enter__(self):
        import subprocess
        from time import sleep
        command = "{}/bin/trips-step -logdir {}/logs -port {} -display none".format(self.trips_base, self.trips_base, self.port)
        self.parser = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sleep(30)
        if self.parameters:
            parameters = self.parameters(self.port)
            sent = False
            while not sent:
                try:
                    parameters.start()
                    sleep(15)
                    sent = True
                except:
                    print("retrying in 5s")
                    sleep(5)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parser.terminate()
        self.parser = None


def parse_sentences(sentences, trips_base=None, parameters=None, port=None, use_timeout=False, max_attempts=5):
    """
    :param sentences: sentences to parse
    :param trips_base: where is trips
    :param parameters: parameters to feed before running
    :param port: port to run trips on
    :param use_timeout: whether or not to use a timeout
    :return: a hash of sentences mapped to their outputs
    """
    from time import sleep
    if not port:
        port = 6300
    runner = run_list_of_sentences
    if use_timeout:
        runner = run_list_of_sentences_with_timeout
    attempts = 0
    total = len(sentences)
    random.shuffle(sentences)
    bar = tqdm.tqdm(total=total, desc="attempt 1")
    result = {}
    while sentences and attempts < max_attempts: 
        with tripsparser(trips_base, port, parameters):
            bar.set_description("attempt "+str(attempts+1)+":"+str(len(sentences)))
            mod = runner(sentences, port)
            last = len(result)
            for m, r in mod.items():
                result[m] = r
            bar.update(len(result) - last)  # want the positive value
            sentences = [s for s in sentences if s not in result]
            if len(sentences):
                failure = sentences.pop(0)
                print("dropping suspected failure:", failure)
                random.shuffle(sentences)  # shuffle the order in case there's just one particular guy failing
            attempts += 1
            port += 1
            sleep(10)
    bar.close()
    return result


def run_list_of_sentences(sentences, port=None, id_offset=0):
    if port is None:
        port = 6200
    from time import sleep
    results = {}
    id = id_offset
    cons_num_incomplete = 0
    warmup = ["This is a warmup sentence", "As is this one"]
    for s in warmup:
        gp = GetParse(s, id=-1, port=port)
        gp.start()

    bar = tqdm.tqdm(sentences, desc="parsing sentences")
    bar.refresh()
    for sentence in bar:
        gp = GetParse(sentence, id=id, port=port)
        gp.start()
        if gp.complete():
            results[sentence] = gp
            cons_num_incomplete = 0
        else:
            cons_num_incomplete += 1
            bar.write("sentence failed")
        if cons_num_incomplete > 1:
            bar.close()
            return results
        id += 1
        sleep(5)  # added a short sleep to avoid error 9 socket errors
    bar.close()
    return results


def run_list_of_sentences_with_timeout(sentences, port=None, id_offset=0):
    if port is None:
        port = 6200
    from time import sleep
    results = {}
    id = id_offset
    cons_num_incomplete = 0
    warmup = ["This is a warmup sentence", "As is this one"]
    for s in warmup:
        gp = GetParse(s, id=-1, port=port)
        gp.start()
    bar = tqdm.tqdm(sentences, desc="parsing sentences") 
    for sentence in bar:
        gp = GetParse(sentence, id=id, port=port)
        try:
            with timeout(seconds=30):
                gp.start()
                if gp.complete():
                    results[sentence] = gp
                    cons_num_incomplete = 0
                    bar.set_description("parsing sentences")
                else:
                    cons_num_incomplete += 1
                    bar.set_description("stall count:" + str(cons_num_incomplete))
        except TimeoutError as e:
            gp.exit(0)  # kill the agent
        id += 1
        if cons_num_incomplete > 1:
            bar.close()
            return results
        sleep(5)  # added a short sleep to avoid error 9 socket errors
    bar.close()
    return results


def run_file_with_timeout(fname, port=None):
    sentences = []
    with open(fname) as f:
        for line in f:
            sentences.append(line.strip())
    run_list_of_sentences_with_timeout(sentences, port=port)

if __name__ == "__main__":
    main()
