"""
Genetic Algorithm Engine for Multi-Objective UAV Fleet Path Planning.
Implements:
  - Multi-objective fitness evaluation with physics/energy/hazard modeling
  - Dynamic constraint repair & penalty functions
  - Tournament selection with elitism
  - Custom spatial geometric crossover & segment swapping
  - Multi-segment Gaussian, swap, and bit-flip mutation
"""

import numpy as np
import config
from chromosome import UAVChromosome


class GeneticAlgorithmEngine:
    """
    Core GA Optimization Engine designed for multi-objective UAV fleet mission planning.
    """
    def __init__(self,
                 environment,
                 pop_size=config.DEFAULT_POP_SIZE,
                 generations=config.DEFAULT_GENERATIONS,
                 crossover_rate=config.DEFAULT_CROSSOVER_RATE,
                 mutation_rate=config.DEFAULT_MUTATION_RATE,
                 tournament_size=config.DEFAULT_TOURNAMENT_SIZE,
                 elitism_count=config.DEFAULT_ELITISM_COUNT,
                 seed=config.RANDOM_SEED):
        
        self.env = environment
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism_count = elitism_count
        
        if seed is not None:
            np.random.seed(seed)
            
        self.population = []
        self.best_individual = None
        self.history = {
            'best_fitness': [],
            'avg_fitness': [],
            'best_coverage': [],
            'best_energy': [],
            'best_time': [],
            'best_hazard': [],
            'snapshots': {}  # Store best individual at certain generations (e.g. 1, mid, final)
        }

    # ==========================================
    # Multi-Objective Evaluation & Physics Model
    # ==========================================
    def evaluate_fitness(self, individual):
        """
        Calculates the multi-objective fitness score of a candidate UAV fleet plan.
        High-performance vectorized and precomputed numerical routine.
        """
        fleet_priority_cells = set()
        total_fleet_energy = 0.0
        drone_flight_times = []
        total_hazard_exposure = 0.0
        total_nfz_violations = 0
        total_battery_excess = 0.0
        drone_energies = []
        
        for d in range(individual.num_drones):
            traj = individual.get_full_trajectory(d)  # (K+2, 2) coords
            drone_energy = 0.0
            drone_time = 0.0
            drone_hazard = 0.0
            
            num_legs = len(traj) - 1
            for leg in range(num_legs):
                p1 = traj[leg]
                p2 = traj[leg + 1]
                v = individual.speeds[d, leg]
                
                # Sensor active only during intermediate legs (idle on base return leg)
                sensor_active = (individual.sensors[d, leg] == 1) if leg < individual.num_waypoints else False
                
                # Fast sample line for hazard & obstacle check
                samples, dist = self.env.fast_sample_line(p1, p2, step_size=2.0)
                leg_time = dist / max(v, 0.1)
                drone_time += leg_time
                
                # Evaluate hazards and NFZ collisions along trajectory
                leg_hazard_sum = 0.0
                for (sx, sy) in samples:
                    ix = int(round(sx))
                    iy = int(round(sy))
                    if 0 <= ix < self.env.size and 0 <= iy < self.env.size:
                        if self.env.obstacle_mask[ix, iy]:
                            total_nfz_violations += 1
                        leg_hazard_sum += self.env.hazard_grid[ix, iy]
                    else:
                        total_nfz_violations += 1  # Out of bounds counts as violation
                        
                avg_leg_hazard = leg_hazard_sum / max(len(samples), 1)
                drone_hazard += avg_leg_hazard * leg_time
                
                # Priority sensing coverage (samples midpoint and destination of leg)
                if sensor_active:
                    fleet_priority_cells.update(self.env.get_priority_cells_in_footprint((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0))
                    fleet_priority_cells.update(self.env.get_priority_cells_in_footprint(p2[0], p2[1]))
                
                # Aerodynamic & Sensor Energy Model
                hazard_factor = 1.0 + (config.HAZARD_ENERGY_PENALTY - 1.0) * avg_leg_hazard
                leg_propulsion_energy = dist * (config.PROPULSION_BASE_COST + config.PROPULSION_SPEED_FACTOR * (v ** 2)) * hazard_factor
                leg_sensor_energy = (config.SENSOR_POWER_COST * leg_time) if sensor_active else 0.0
                drone_energy += (leg_propulsion_energy + leg_sensor_energy)
                
            drone_flight_times.append(drone_time)
            drone_energies.append(drone_energy)
            total_fleet_energy += drone_energy
            total_hazard_exposure += drone_hazard
            
            if drone_energy > config.MAX_BATTERY_ENERGY:
                total_battery_excess += (drone_energy - config.MAX_BATTERY_ENERGY)
                
        mission_completion_time = max(drone_flight_times)
        
        # Calculate coverage score from unique scanned priority cells
        coverage_score = sum(self.env.priority_grid[cx, cy] for (cx, cy) in fleet_priority_cells)
        total_possible_priority = np.sum(self.env.priority_grid)
        detection_rate = (coverage_score / total_possible_priority) if total_possible_priority > 0 else 0.0
        
        # Multi-Objective Fitness Evaluation
        objective_value = (
            config.W_COVERAGE * coverage_score
            - config.W_ENERGY * total_fleet_energy
            - config.W_TIME * mission_completion_time
            - config.W_HAZARD * total_hazard_exposure
        )
        
        # Hard Penalties
        penalties = (
            config.PENALTY_NFZ * total_nfz_violations
            + config.PENALTY_BATTERY * total_battery_excess
        )
        
        fitness = objective_value - penalties
        
        individual.fitness = float(fitness)
        individual.metrics = {
            'coverage_score': float(coverage_score),
            'unique_cells_covered': len(fleet_priority_cells),
            'detection_rate': float(detection_rate),
            'total_fleet_energy': float(total_fleet_energy),
            'mission_time': float(mission_completion_time),
            'total_hazard_exposure': float(total_hazard_exposure),
            'nfz_violations': int(total_nfz_violations),
            'battery_excess': float(total_battery_excess),
            'drone_energies': drone_energies,
            'drone_flight_times': drone_flight_times
        }
        return individual.fitness

    # ==========================================
    # Population Initialization
    # ==========================================
    def initialize_population(self):
        """Initializes population with random valid chromosomes."""
        self.population = []
        for _ in range(self.pop_size):
            ind = UAVChromosome.create_random(self.env, config.NUM_DRONES, config.NUM_WAYPOINTS_PER_DRONE)
            self.evaluate_fitness(ind)
            self.population.append(ind)
        self._update_best()

    def _update_best(self):
        """Identifies and stores the current elite individual."""
        current_best = max(self.population, key=lambda ind: ind.fitness)
        if self.best_individual is None or current_best.fitness > self.best_individual.fitness:
            self.best_individual = current_best.copy()

    # ==========================================
    # Selection Mechanism
    # ==========================================
    def tournament_selection(self):
        """Tournament selection operator with configurable pressure."""
        candidates = np.random.choice(self.population, size=self.tournament_size, replace=False)
        winner = max(candidates, key=lambda ind: ind.fitness)
        return winner

    # ==========================================
    # Genetic Operators: Crossover
    # ==========================================
    def crossover(self, parent1, parent2):
        """
        Hybrid multi-segment crossover operator:
          - Spatial Waypoints: Geometric interpolation or Segment swapping
          - Speed & Sensors: Uniform swap
        """
        if np.random.rand() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
            
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # 1. Waypoint Crossover
        for d in range(config.NUM_DRONES):
            mode = np.random.rand()
            if mode < 0.5:
                # Geometric Blending Crossover
                alpha = np.random.uniform(0.2, 0.8)
                child1.waypoints[d] = alpha * parent1.waypoints[d] + (1 - alpha) * parent2.waypoints[d]
                child2.waypoints[d] = (1 - alpha) * parent1.waypoints[d] + alpha * parent2.waypoints[d]
            else:
                # Segment Swapping Crossover
                cut = np.random.randint(1, config.NUM_WAYPOINTS_PER_DRONE)
                child1.waypoints[d, cut:] = parent2.waypoints[d, cut:]
                child2.waypoints[d, cut:] = parent1.waypoints[d, cut:]
                
        # 2. Speeds Crossover (Uniform)
        speed_mask = np.random.rand(*child1.speeds.shape) < 0.5
        child1.speeds[speed_mask] = parent2.speeds[speed_mask]
        child2.speeds[speed_mask] = parent1.speeds[speed_mask]
        
        # 3. Sensor Activation Crossover (Uniform)
        sensor_mask = np.random.rand(*child1.sensors.shape) < 0.5
        child1.sensors[sensor_mask] = parent2.sensors[sensor_mask]
        child2.sensors[sensor_mask] = parent1.sensors[sensor_mask]
        
        # Repair both offspring
        child1.repair(self.env)
        child2.repair(self.env)
        
        return child1, child2

    # ==========================================
    # Genetic Operators: Mutation
    # ==========================================
    def mutate(self, individual):
        """
        Custom spatial and categorical mutation operators:
          - Spatial Coordinates: Gaussian jitter perturbation and route waypoint swaps
          - Speeds: Discrete level alteration
          - Sensors: Bit-flip mutation
        """
        for d in range(config.NUM_DRONES):
            for w in range(config.NUM_WAYPOINTS_PER_DRONE):
                if np.random.rand() < self.mutation_rate:
                    sigma = 3.5
                    dx = np.random.normal(0, sigma)
                    dy = np.random.normal(0, sigma)
                    individual.waypoints[d, w, 0] += dx
                    individual.waypoints[d, w, 1] += dy
                    
            if np.random.rand() < (self.mutation_rate * 0.7):
                idx1, idx2 = np.random.choice(config.NUM_WAYPOINTS_PER_DRONE, size=2, replace=False)
                individual.waypoints[d, [idx1, idx2]] = individual.waypoints[d, [idx2, idx1]]
                
            for leg in range(individual.speeds.shape[1]):
                if np.random.rand() < self.mutation_rate:
                    individual.speeds[d, leg] = np.random.choice(config.SPEED_LEVELS)
                    
            for leg in range(config.NUM_WAYPOINTS_PER_DRONE):
                if np.random.rand() < self.mutation_rate:
                    individual.sensors[d, leg] = 1 - individual.sensors[d, leg]
                    
        individual.repair(self.env)

    # ==========================================
    # Main Evolution Loop
    # ==========================================
    def evolve(self, verbose=True):
        """
        Executes the genetic algorithm evolution across generations.
        """
        if not self.population:
            self.initialize_population()
            
        for gen in range(1, self.generations + 1):
            self.population.sort(key=lambda ind: ind.fitness, reverse=True)
            self._update_best()
            
            fits = [ind.fitness for ind in self.population]
            best_fit = float(fits[0])
            avg_fit = float(np.mean(fits))
            
            self.history['best_fitness'].append(best_fit)
            self.history['avg_fitness'].append(avg_fit)
            self.history['best_coverage'].append(self.population[0].metrics['coverage_score'])
            self.history['best_energy'].append(self.population[0].metrics['total_fleet_energy'])
            self.history['best_time'].append(self.population[0].metrics['mission_time'])
            self.history['best_hazard'].append(self.population[0].metrics['total_hazard_exposure'])
            
            if gen == 1 or gen == self.generations // 2 or gen == self.generations:
                self.history['snapshots'][gen] = self.population[0].copy()
                
            if verbose and (gen == 1 or gen % 10 == 0 or gen == self.generations):
                best_m = self.population[0].metrics
                print(f"[Gen {gen:02d}/{self.generations}] Best Fit: {best_fit:7.2f} | Avg Fit: {avg_fit:7.2f} | "
                      f"Coverage: {best_m['coverage_score']:6.1f} ({best_m['detection_rate']*100:4.1f}%) | "
                      f"Energy: {best_m['total_fleet_energy']:5.1f} | NFZ Violations: {best_m['nfz_violations']}")
                
            next_generation = []
            
            # Elitism
            for i in range(self.elitism_count):
                next_generation.append(self.population[i].copy())
                
            # Selection, Crossover & Mutation
            while len(next_generation) < self.pop_size:
                p1 = self.tournament_selection()
                p2 = self.tournament_selection()
                c1, c2 = self.crossover(p1, p2)
                self.mutate(c1)
                self.mutate(c2)
                self.evaluate_fitness(c1)
                self.evaluate_fitness(c2)
                next_generation.append(c1)
                if len(next_generation) < self.pop_size:
                    next_generation.append(c2)
                    
            self.population = next_generation
            
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)
        self._update_best()
        return self.best_individual, self.history
