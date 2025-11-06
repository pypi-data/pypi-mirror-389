import random


class Utils:
    def random_sex() -> str:
        return "M" if random.randint(0, 1) == 0 else "F"

    def get_total_cumulative_fit(available_individuals: list):
        cumulative_fit = 0
        for individual in available_individuals:
            cumulative_fit += individual[0].fitness * individual[1]
        return cumulative_fit

    def select_individual(available_individuals: list) -> 'Individual':
        # In probability theory, this is known
        # as sampling from a discrete distribution.
        cumulative_fit = 0
        total_cumulative_fit = (Utils
                                .get_total_cumulative_fit(available_individuals)
                                )
        rand = random.uniform(0, total_cumulative_fit)
        for individual in available_individuals:
            cumulative_fit += individual[0].fitness * individual[1]
            if cumulative_fit > rand:
                return individual[0]

        if cumulative_fit <= rand:
            raise Exception("Valor aleatório não mapeia para "
                            "nenhum indivíduo")
