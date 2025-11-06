import random
from typing import Self


class Locus:
    def __init__(self, alleles: tuple):
        self.alleles = alleles  

    def __str__(self):
        canon_alleles = sorted(self.alleles)
        return_str = f""
        for i in canon_alleles:
            return_str += f"{i}"
        return return_str

    def __eq__(self, other: Self):
        return set(self.alleles) == set(other.alleles)

    def __hash__(self):
        return hash(frozenset(self.alleles))

    def __getitem__(self, key):
        return sorted(self.alleles)[key]

    def __len__(self):
        return len(self.alleles)

    def pass_allele(self):
        rand = random.randint(0, len(self.alleles) - 1)
        return self.alleles[rand]
