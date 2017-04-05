from diesel.weights import default_weights
from itertools import combinations

core_roles = set(default_weights().keys())


class Bone:
    # A wrapper for SemanticArgument
    def __init__(self, arg, filled=None, generator=None):
        self.arg = arg
        can_fill = arg.fltype.strip("()").split()
        if len(can_fill) == 1:
            self.can_fill = set(["*"])
        elif len(can_fill) > 2:
            self.can_fill = set(can_fill[2:])
        else:
            raise ValueError("{} does not look like something I know".format(self.arg.fltype))
        self.filled = filled
        self.generator = generator

    def is_abstract(self):
        return self.filled is None

    def essential(self):
        return self.arg.optionality == "essential"

    def wild(self):
        return "*" in self.can_fill

    def __str__(self):
        if self.filled is None:
            return "{}-role:{} [{}]".format(self.arg.optionality, self.arg.role, ", ".join(self.can_fill))
        return "{}-role:{} [{}]".format(self.arg.optionality, self.arg.role, self.filled)

    def apply(self, tpe):
        if "*" in self.can_fill:
            return Bone(self.arg, filled=tpe, generator=self)
        semval = tpe.sem.strip("()").split()
        if len(semval) > 2:
            semval = semval[2:]
        if len(set(semval).intersection(self.can_fill)) > 0:
            return Bone(self.arg, filled=tpe, generator=self)


class Skeleton:
    def __init__(self, core):
        self.core = core
        self.bones = [Bone(s) for s in core.arguments if s.role in core_roles]

    def has_required(self, roles=None):
        if roles is None:
            return any([b.essential() for b in self.bones])
        return any([b.essential() for b in self.bones if b.arg.role in roles or b.arg.role == roles])

    def enumerate(self):
        essential = [b for b in self.bones if b.essential()]
        nonessential = [b for b in self.bones if not b.essential()]
        structs = []
        if len(essential) > 0:
            structs = [" ".join(sorted([str(b) for b in essential]))]

        for i in range(len(nonessential)):
            for comb in combinations(nonessential, i+1):
                base = essential[:]
                base.extend([*comb])
                structs.append(" ".join(sorted([str(b) for b in base])))
        return structs
