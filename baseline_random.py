"""
Baseline Random Search module for UAV Fleet Mission Planning.
Generates purely random candidate solutions to establish a rigorous empirical baseline
against which the Genetic Algorithm's optimization capability is benchmarked.
"""

import numpy as np
import config
from chromosome import UAVChromosome


class RandomSearchBaseline:
    """
    Random Search optimizer that samples candidate fleet configurations uniformly at random
    and tracks the best discovered solution over an equivalent number of evaluations.
    """
    def __init__(self, environment, total_evaluations=3000, seed=config.RANDOM_SEED):
        self.env = environment
        self.total_evaluations = total_evaluations
        if seed is not None:
            np.random.seed(seed)
            
        self.best_individual = None
        self.history = {
            'eval_steps': [],
            'best_fitness': [],
            'avg_fitness': []
        }

    def run(self, ga_engine, batch_size=config.DEFAULT_POP_SIZE, verbose=True):
        """
        Executes random search in generational-equivalent batches.
        Uses ga_engine.evaluate_fitness to guarantee identical evaluation criteria.
        """
        total_batches = self.total_evaluations // batch_size
        all_fitnesses = []
        
        for batch in range(1, total_batches + 1):
            batch_fitnesses = []
            for _ in range(batch_size):
                ind = UAVChromosome.create_random(self.env, config.NUM_DRONES, config.NUM_WAYPOINTS_PER_DRONE)
                fit = ga_engine.evaluate_fitness(ind)
                batch_fitnesses.append(fit)
                all_fitnesses.append(fit)
                
                if self.best_individual is None or fit > self.best_individual.fitness:
                    self.best_individual = ind.copy()
                    
            best_so_far = self.best_individual.fitness
            avg_batch = float(np.mean(batch_fitnesses))
            
            self.history['eval_steps'].append(batch * batch_size)
            self.history['best_fitness'].append(best_so_far)
            self.history['avg_fitness'].append(avg_batch)
            
            if verbose and (batch == 1 or batch % 10 == 0 or batch == total_batches):
                print(f"[Random Search Batch {batch:02d}/{total_batches}] "
                      f"Best Fit: {best_so_far:7.2f} | Batch Avg: {avg_batch:7.2f}")
                
        return self.best_individual, self.history
