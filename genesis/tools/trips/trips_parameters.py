from tripsmodule.trips_module import TripsModule
from tripsmodule.kqml_performative import KQMLPerformative


def basic_experiment(datafile, adjustment=None):
    return lambda port: TripsParameters(datafile=datafile, adjustment=adjustment, port=port)


def no_skeleton_score():
    return lambda port: TripsParameters(pred_type="NullScore", port=port)


class TripsParameters(TripsModule):
    """
    This module takes a set of parameters, injects them into the facilitator and then exits.
    TODO: deal with responses to log errors and exit when all three actions are complete
    """
    def __init__(self, pred_type="WuP", lib_type="MAX", datafile=None, adjustment=None, port=None):
        if type(pred_type) is str:
            self.pred_type = pred_type
        else:
            self.pred_type = pred_type.name()
        if type(lib_type) is str:
            self.lib_type = lib_type
        else:
            self.lib_type = lib_type.name()
        self.datafile = datafile
        self.adjustment = adjustment
        if port is None:
            port = 6200
        self.port = port
        TripsModule.__init__(self, {}, port=port)

    def init(self):
        self.name = "EParameters-{}-{}-{}".format(self.pred_type, self.lib_type, self.port)
        print(self.name)
        TripsModule.init(self)
        self.send(KQMLPerformative.from_string(
            "(subscribe :content (tell &key :content(use-skeleton-data . *)))"
        ))
        self.send(KQMLPerformative.from_string(
            "(subscribe :content (tell &key :content(score-method . *)))"
        ))
        self.send(KQMLPerformative.from_string(
            "(subscribe :content (tell &key :content(selection-method . *)))"
        ))
        self.ready()
        self.make_request_and_exit()

    def make_request_and_exit(self):
        self.send(KQMLPerformative.from_string(
            "(request :receiver SKELETONSCORE :content (score-method {}))".format(self.pred_type)
        ))
        self.send(KQMLPerformative.from_string(
            "(request :receiver SKELETONSCORE :content (selection-method {}))".format(self.lib_type)
        ))
        if self.datafile:
            self.send(KQMLPerformative.from_string(
                "(request :receiver SKELETONSCORE :content (use-skeleton-data {}))".format(self.datafile)
            ))
        if self.adjustment:
            self.send(KQMLPerformative.from_string(
                "(request :receiver SKELETONSCORE :content (adjustment-factor {}))".format(self.adjustment)
            ))
        from time import sleep
        sleep(10)
        self.exit(0)

