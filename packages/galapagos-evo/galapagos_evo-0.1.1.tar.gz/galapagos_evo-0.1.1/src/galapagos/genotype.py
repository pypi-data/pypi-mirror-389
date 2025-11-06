"""
Defines a given genotype
"""


class Genotype:
    def __init__(self, size: int):
        self.__size = size
        self.__loci = [None] * size  # Gera uma genótipo vazio com
                                     # `size` loci

    def __str__(self):
        return_string = ""
        for i in range(len(self)):
            return_string += f"{self[i]} "
        return return_string

    def __len__(self):
        return self.__size

    def __getitem__(self, key):
        return self.__loci[key]

    def __setitem__(self, key, value):
        self.__loci[key] = value

    def __contains__(self, locus):
        for item in self:
            if item == locus:
                return True
        return False

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for i in range(len(self)):
            if self[i] != other[i]:
                return False

        return True

    def __hash__(self):
        return hash(tuple(self.__loci))

    @property
    def loci(self):
        return self.__loci
