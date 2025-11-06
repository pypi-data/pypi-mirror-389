"""
Defines an individual to simulate.
"""
from galapagos.genotype import Genotype
from galapagos.locus import Locus
from galapagos.utils import Utils
from typing import Self


class Individual:
    def __init__(self, sex: str, genotype: Genotype,
                 fitness: float = 1.0):
        self.__fitness = fitness
        self.__sex = sex
        self.genotype = genotype

    def __str__(self):
        return (f"Sexo: {self.sex} Genótipo: {self.genotype}"
                f"Fitness: {self.__fitness}")

    def __eq__(self, other):
        return (self.fitness == other.fitness) and (self.sex == other.sex) and (self.genotype == other.genotype)

    def __hash__(self):
        return hash((self.fitness, self.sex, self.genotype))

    @property
    def fitness(self):
        return self.__fitness

    @fitness.setter
    def fitness(self, fitness):
        self.__fitness = fitness

    @property
    def sex(self):
        return self.__sex

    def mate(self, other: Self) -> Self:
        new_genotype = Genotype(size=len(self.genotype))
        for i in range(len(self.genotype)):
            locus = Locus( (self.genotype[i].pass_allele(),
                            other.genotype[i].pass_allele())
                          )
            new_genotype[i] = locus

        new_sex = Utils.random_sex()
        newborn = Individual(new_sex, new_genotype)

        return newborn

    def update_fitness(self, genepool):
        if genepool:
            self.fitness = 0.0
            for gene in genepool:
                if gene[0] in self.genotype:
                    self.fitness += gene[1]/len(self.genotype)
