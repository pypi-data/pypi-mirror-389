from galapagos.generation import Generation
from galapagos.utils import Utils
from galapagos.genotype import Genotype
from galapagos.individual import Individual
from plotnine import *
from collections import defaultdict
import plotly.express as px
import numpy as np
import polars as pl
import math

class Simulation:
    def __init__(self,
                 max_generations: int,
                 first_generation: Generation,
                 genepool: list
                 ):
        self.max_generations = max_generations
        self.genepool = genepool
        self.data = []

        self.first_generation = first_generation
        self.generation_history = [self.first_generation]

    # TODO: Still under development
    def _get_individual_allele_frequency(self, 
                                         freq_dict,
                                         individual: Individual, 
                                         individual_count: str):
        for locus in individual.genotype:
            for allele in locus:
                freq_dict[allele] += individual_count

    def _process_generation_data(self, generation, index: int):
        freq_dict = defaultdict(int)
        for individual, individual_count in generation:
            self._get_individual_allele_frequency(freq_dict, individual, individual_count)

        locus = generation[0][0].genotype.loci[0]
        for allele, allele_count in freq_dict.items():
            self.data.append({
                "generation": index,
                "allele": str(allele),
                "frequency": allele_count / (len(locus) * len(generation))
            })

    def _selection_model(self) -> list:
        # TODO: Rever referência, me parece errado
        data_theory = []
        first_gen = self.first_generation
        freq_prev = {}
        freq_theory = {}

        for locus, _ in self.genepool:
            freq_prev[str(locus)] = first_gen.get_locus_frequency(locus)

        for g in range(self.max_generations):
            fitness_avg = 0

            # Calculates fitness_avg
            for locus, fitness in self.genepool:
                fitness_avg += freq_prev[str(locus)] * fitness

            # Calculate expected frequency
            for locus, fitness in self.genepool:
                freq_theory[str(locus)] = freq_prev[str(locus)] * fitness / fitness_avg
                data_theory.append({
                    "generation": g + 1,
                    "genotype": str(locus),
                    "expected_frequency": freq_theory[str(locus)]
                })
            freq_prev = freq_theory
        return data_theory

    def get_allele_frequency(self, allele: str):
        df = pl.DataFrame(self.data)
        return df.filter(pl.col("allele") == allele).sum()

    def simulate(self):
        gene_lines = [
            f"Gene: {str(gene)}, Fitness: {fitness}"
            for gene, fitness in self.genepool
        ]

        print(f"Simulation info: \n"
              f"maximum number of generations: {self.max_generations}, \n"
              f"population size: {len(self.first_generation)}, \n"
              f"available genes: {gene_lines}"
             )
        for i in range(self.max_generations):
            new_generation = self.generation_history[i].next()
            self.generation_history.append(new_generation)
            self._process_generation_data(new_generation, index=i + 1)

    def show(self):

        df_simu = pl.DataFrame(self.data)
        # fig = px.line(df_simu,
        #               x="generation",
        #               y="frequency",
        #               color="allele",
        #               title="Simulação de Frequência de Genótipo")

        # fig.show()
        # df_theory = pl.DataFrame(self._selection_model())
        (
            ggplot(df_simu, aes(x="generation", color="allele"))
            + geom_line(aes(y="frequency"), size=1)
            + scale_y_continuous(limits=(0, 1))
            # + geom_line(data=df_theory,
            #            mapping=aes(y="expected_frequency", linetype="'Teórico'"),
            #            size=1
            #            )
            + labs(x="Geração", y="Frequência", color="Alelo")

            # + scale_linetype_manual(
            #     name="Fonte dos Dados",
            #     values={"Simulado": "solid", "Teórico": "dashed"}
            # )
        ).show()
