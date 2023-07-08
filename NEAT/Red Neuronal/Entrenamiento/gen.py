import random
import os
import statistics
import matplotlib.pyplot as plt
import sys
import numpy as np
import neat

from red import NODOS, CAPAS, BIAS
from flappy_gen import main2, mainGame


POBLACION = 1000
PADRES1 = 10
PADRES2 = int(POBLACION * 0.1)
HIJOS = int(POBLACION * 0.1)

MUTACION = 0.2
DELTA = 0.02

WMIN, WMAX = -1, 1
RANDOM = True
USARPESOS = False
MINFITNESS = 1000


def prob(p):
    return random.uniform(0, 1) < p


class Pajaro:
    def __init__(self):
        self.fitness = 0
        self.distMuerte = 0
        self.victorias = 0
        self.score = 0

        self.pesos = [[]]
        for i in range(1, CAPAS):
            self.pesos.append([])

            for j in range(NODOS[i]):
                self.pesos[i].append(np.zeros(NODOS[i-1], dtype=float))

                if RANDOM:
                    for k in range(NODOS[i-1]):
                        self.pesos[i][-1][k] = random.uniform(WMIN, WMAX)

    def setFitness(self, fitness, dist):
        self.fitness = self.fitness * 0.9 + fitness
        self.distMuerte = dist
        self.score = fitness

        if self.score >= MINFITNESS:
            self.victorias += 1

    def mutar(self):
        self.victorias = 0

        for i in range(1, CAPAS):
            for j in range(NODOS[i]):
                for k in range(NODOS[i-1]):
                    if prob(MUTACION):
                        if random.randint(0, 1):
                            self.pesos[i][j][k] += random.uniform(-1, 1) * DELTA

    def hijo(self, p1, p2):
        for i in range(1, CAPAS):
            for j in range(NODOS[i]):
                for k in range(NODOS[i-1]):
                    self.pesos[i][j][k] = random.choice([p1.pesos[i][j][k], p2.pesos[i][j][k]])

        self.fitness = min([p1.fitness, p2.fitness])
        self.mutar()

    def guardar(self, numero):
        if self.victorias <= 1:
            return

        with open(f"pesos/pesos{numero}-{self.score}-{self.victorias}.txt", 'w') as f:
            f.write(" ".join([str(n) for n in BIAS]) + "\n")
            f.write(" ".join([str(n) for n in NODOS]) + "\n")

            for i in range(1, CAPAS):
                for j in range(NODOS[i]):
                    f.write(" ".join([str(p) for p in self.pesos[i][j]]) + "\n")


class AlgGenetico:
    def __init__(self):
        main2()

        self.numPajaro = 0
        self.pajaros = [Pajaro() for _ in range(POBLACION)]
        if USARPESOS:
            dir_list = os.listdir("./pesos")
            for i in range(min(len(dir_list), POBLACION)):
                self.pajaros[i].cargar("./pesos/" + dir_list[i])

        self.fitnessMaxGen = []
        self.fitnessPromedioGen = []

        self.f = open("calidad.txt", "w")

    def ciclo(self):
        self.calculoFitness()
        self.descendencia()
        self.mutacion()

    def calculoFitness(self):
        pajaros_evaluados = []
        for i, pajaro in enumerate(self.pajaros):
            fitness, distPipe = mainGame(1, [pajaro])
            pajaro.setFitness(fitness[0], distPipe[0])
            pajaro.guardar(self.numPajaro)
            self.numPajaro += 1
            pajaros_evaluados.append(pajaro)

        pajaros_evaluados.sort(key=lambda x: (-x.fitness, x.distMuerte))

        fitness = [pajaro.fitness for pajaro in pajaros_evaluados]
        distPipe = [pajaro.distMuerte for pajaro in pajaros_evaluados]

        self.fitnessMaxGen.append(max(fitness))
        self.fitnessPromedioGen.append(statistics.mean(fitness))
        print(self.fitnessPromedioGen[-1], self.fitnessMaxGen[-1])

        self.f.write(str(self.fitnessPromedioGen[-1]) + " " + str(self.fitnessMaxGen[-1]) + "\n")

    def descendencia(self):
        for i in range(HIJOS):
            p1 = random.randint(0, PADRES1-1)
            p2 = (p1 + random.randint(1, PADRES2-1)) % PADRES2
            self.pajaros[POBLACION-1 - i].hijo(self.pajaros[p1], self.pajaros[p2])

    def mutacion(self):
        for i in range(PADRES1, POBLACION):
            if prob(MUTACION):
                self.pajaros[i].mutar()

    def grafico(self):
        x = [i for i in range(len(self.fitnessMaxGen))]
        plt.plot(x, self.fitnessMaxGen, label="Mejor")
        plt.plot(x, self.fitnessPromedioGen, label="Promedio")

        plt.xlabel('Generacion')
        plt.ylabel('Fitness')

        plt.legend()
        plt.show()


def evaluar_genoma(genoma, config):
    pajaro = Pajaro()
    index = 0
    for i in range(1, CAPAS):
        for j in range(NODOS[i]):
            for k in range(NODOS[i-1]):
                pajaro.pesos[i][j][k] = list(genoma)[index]
                index += 1

    fitness, distPipe = mainGame(1, [pajaro])
    pajaro.setFitness(fitness[0], distPipe[0])
    return pajaro.fitness


def iniciar_neat(config):
    pop = neat.Population(config)
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.run(AlgGenetico().calculoFitness())
    mejor_genoma = stats.best_genome
    return mejor_genoma


config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     './NEAT/neat_config.ini')

mejor_genoma = iniciar_neat(config)
