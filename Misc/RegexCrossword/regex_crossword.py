import itertools
import re
from deap import base, creator, tools, algorithms
import random
import numpy
import string

GRID_SIZE = 13

X_REGEXES = {
    -6: ".*G.*V.*H.*",
    -5: "[CR]*",
    -4: ".*XEXM*",
    -3: ".*DD.*CCM.*",
    -2: ".*XHCR.*X.*",
    -1: ".*(.)(.)(.)(.)\\4\\3\\2\\1.*",
    0: ".*(IN|SE|HI)",
    1: "[^C]*MMM[^C]*",
    2: ".*(.)C\\1X\\1.*",
    3: "[CEIMU]*OH[AEMOR]*",
    4: "(RX|[^R])*",
    5: "[^M]*M[^M]*",
    6: "(S|MM|HHH)*"
}

Y_REGEXES = {
    -6: ".*SE.*UE.*",
    -5: ".*LR.*RL.*",
    -4: ".*OXR.*",
    -3: "([^EMC]|EM)*",
    -2: "(HHX|[^HX])*",
    -1: ".*PRR.*DDC.*",
    0: ".*",
    1: "[AM]*CM(RC)*R?",
    2: "([^MC]|MM|CC)*",
    3: "(E|CR|MN)*",
    4: "P+(..)\\1.*",
    5: "[CHMNOR]*I[CHMNOR]*",
    6: "(ND|ET|IN)[^X]*"
}

Z_REGEXES = {
    -6: ".*H.*H.*",
    -5: "(DI|NS|TH|OM)*",
    -4: "F.*[AO].*[AO].*",
    -3: "(O|RHH|MM)*",
    -2: ".*",
    -1: "C*MC(CCC|MM)*",
    0: "[^C]*[^R]*III.*",
    1: "(...?)\\1*",
    2: "([^X]|XCC)*",
    3: "(RR|HHH)*.?",
    4: "N.*X.X.X.*E",
    5: "R*D*M*",
    6: ".(C|HH)*"
}


class Hex(object):
    def __init__(self, x, z):
        self.x = x
        self.y = -x - z
        self.z = z
        self.contents = None

    def __repr__(self):
        return "{:<2},{:<2},{:<2}: {}".format(self.x, self.y, self.z, self.contents)


class HexGrid(object):
    def __init__(self, letters=None):
        self.size = GRID_SIZE
        self.max_dist = self.size // 2
        self.hexes = [Hex(x, z) for x, z in itertools.product(range(-self.max_dist, self.max_dist + 1), repeat=2)
                      if self.cube_distance_hexs(Hex(0, 0), Hex(x, z)) <= self.max_dist]
        self.set_all_contents(letters)

    @staticmethod
    def cube_distance_hexs(a, b):
        return max(abs(a.x - b.x), abs(a.y - b.y), abs(a.z - b.z))

    def get_x_row(self, index):
        # sort by z
        return "".join(h.contents for h in sorted(self.hexes, key=lambda h: -h.z) if h.x == index)

    def get_y_row(self, index):
        # sort by x
        return "".join(h.contents for h in sorted(self.hexes, key=lambda h: -h.x) if h.y == index)

    def get_z_row(self, index):
        # sort by y
        return "".join(h.contents for h in sorted(self.hexes, key=lambda h: -h.y) if h.z == index)

    def _set_contents_hex(self, target_hex, new_contents):
        self.set_contents(target_hex.x, target_hex.z, new_contents)

    def get_contents(self, x, z):
        this_hex = next((h for h in self.hexes if h.x == x and h.z == z), None)
        if this_hex is None:
            raise ValueError
        else:
            return this_hex.contents

    def set_contents(self, x, z, new_contents):
        this_hex = next((h for h in self.hexes if h.x == x and h.z == z), None)
        if this_hex is None:
            raise ValueError
        else:
            this_hex.contents = new_contents

    def set_all_contents(self, letters):
        letter_iter = iter(letters)
        for z in range(-self.max_dist, self.max_dist + 1):
            for x in range(max(-self.max_dist, -z - self.max_dist), min(self.max_dist, -z + self.max_dist) + 1):
                self.set_contents(x, z, next(letter_iter))

    def validate_x_row(self, index):
        return re.match(X_REGEXES[index], "".join(self.get_x_row(index)))

    def validate_y_row(self, index):
        return re.match(Y_REGEXES[index], "".join(self.get_y_row(index)))

    def validate_z_row(self, index):
        return re.match(Z_REGEXES[index], "".join(self.get_z_row(index)))

    def get_string(self):
        output = ""
        for z in range(-self.max_dist, self.max_dist + 1):
            for x in range(max(-self.max_dist, -z - self.max_dist), min(self.max_dist, -z + self.max_dist) + 1):
                output += self.get_contents(x, z)

        return output

    def score(self):
        count_x = sum(
            [1 for index in range(-self.max_dist, self.max_dist + 1) if self.validate_x_row(index) is not None])
        count_y = sum(
            [1 for index in range(-self.max_dist, self.max_dist + 1) if self.validate_y_row(index) is not None])
        count_z = sum(
            [1 for index in range(-self.max_dist, self.max_dist + 1) if self.validate_z_row(index) is not None])
        return sum([count_x, count_y, count_z])

    def mutate(self, indpb):
        for this_hex in self.hexes:
            if random.random() < indpb:
                self._set_contents_hex(this_hex, generate_random_letter())


def mutate_grid(individual, indpb):
    individual.mutate(indpb)

    return individual,


def total_grid_score(individual):
    return individual.score(),


def generate_random_letter():
    return random.choice(string.ascii_uppercase)


def get_best_board(stats):
    fit_values = [ind.fitness.values[0] for ind in stats]
    index = fit_values.index(max(fit_values))
    return ''.join(stats[index])


def mate_grids(ind1, ind2):
    new_string1, new_string2 = tools.cxTwoPoint(list(ind1.get_string()), list(ind2.get_string()))

    ind1.set_all_contents(new_string1)
    ind2.set_all_contents(new_string2)

    return ind1, ind2


def get_num_unique_boards(stats):
    return len(set(''.join(ind) for ind in stats))


def simulate(population=200,
             generations=20,
             letter_mutate_prob=0.25,
             tournament_size=20,
             mating_prob=0.5,
             individual_mutate_prob=0.2,
             hof_size=1):
    toolbox = base.Toolbox()

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Grid", HexGrid, fitness=creator.FitnessMax)

    toolbox.register("letter", generate_random_letter)
    toolbox.register("individual", tools.initRepeat, creator.Grid, toolbox.letter,
                     n=(3 * GRID_SIZE * (GRID_SIZE + 1)) + 1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", total_grid_score)
    toolbox.register("mate", mate_grids)
    toolbox.register("mutate", mutate_grid, indpb=letter_mutate_prob)
    toolbox.register("select", tools.selTournament, tournsize=tournament_size)

    pop = toolbox.population(n=population)
    hof = tools.HallOfFame(hof_size)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)

    best_stats = tools.Statistics(lambda ind: ind)
    best_stats.register("best", get_best_board)
    best_stats.register("uniq", get_num_unique_boards)

    all_stats = tools.MultiStatistics(scores=stats, boards=best_stats)

    pop, logbook = algorithms.eaSimple(pop,
                                       toolbox,
                                       mating_prob,
                                       individual_mutate_prob,
                                       generations,
                                       stats=stats,
                                       halloffame=hof,
                                       verbose=True)

    return pop, logbook, hof


if __name__ == "__main__":
    p, l, h = simulate(population=5000, generations=100)
    print("done")
