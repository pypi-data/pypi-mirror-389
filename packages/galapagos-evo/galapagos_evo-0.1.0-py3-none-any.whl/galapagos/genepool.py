from galapagos.generation import Generation
from galapagos.utils import Utils
from galapagos.genotype import Genotype
from galapagos.individual import Individual

class Genepool:
    def __init__(self, 
                 genotypes: list, 
                 fitnesses: list,
                 loci: list
                 ):
        self.genotypes = genotypes
        self.fitnesses = fitnesses
        self.loci = loci

    def __getitem__(self, key):
        return (self.genotype[key], self.fitnesses[key], self.loci[key])

    def __setitem__(self, key, value):
        self.genotype[key] = value[0]
        self.fitnesses[key] = value[1]
        self.loci[key] = value[2]


