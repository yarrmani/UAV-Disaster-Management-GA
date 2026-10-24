"""
Main execution script for UAV Fleet Disaster Management GA Optimization.
Executes the GA simulation, logs convergence progress, and saves core visualization plots.
"""

import time
import os
import config
from environment import GridEnvironment
from genetic_algorithm import GeneticAlgorithmEngine
from visualizer import MissionVisualizer


def run_single_simulation():
    """Executes a standard single run of the UAV GA optimization pipeline."""
    print("=" * 75)
    print("  UAV FLEET DISASTER SURVEILLANCE STRATEGY ENGINE")
    print("  Multi-Objective Genetic Algorithm Path Optimization")
    print("=" * 75)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = MissionVisualizer.setup_output_dir(os.path.join(base_dir, "outputs"))
    
    # 1. Initialize Disaster Operational Environment
    print("\n[1/4] Initializing 2D Discretized Hazard Environment (50x50)...")
    env = GridEnvironment(size=config.GRID_SIZE)
    total_target_priority = env.priority_grid.sum()
    print(f"      Grid Dimensions: {config.GRID_SIZE}x{config.GRID_SIZE} cells")
    print(f"      Total Priority Targets In Grid: {total_target_priority:.1f} points")
    print(f"      Fleet Size: {config.NUM_DRONES} UAVs | Waypoints per UAV: {config.NUM_WAYPOINTS_PER_DRONE}")
    
    # 2. Build and Initialize GA Engine
    print("\n[2/4] Initializing Population and Genetic Algorithm Engine...")
    ga = GeneticAlgorithmEngine(
        environment=env,
        pop_size=config.DEFAULT_POP_SIZE,
        generations=config.DEFAULT_GENERATIONS,
        crossover_rate=config.DEFAULT_CROSSOVER_RATE,
        mutation_rate=config.DEFAULT_MUTATION_RATE,
        tournament_size=config.DEFAULT_TOURNAMENT_SIZE,
        elitism_count=config.DEFAULT_ELITISM_COUNT,
        seed=config.RANDOM_SEED
    )
    
    # 3. Evolve Solutions
    print(f"\n[3/4] Executing GA Evolution over {config.DEFAULT_GENERATIONS} generations...")
    start_time = time.time()
    best_solution, history = ga.evolve(verbose=True)
    elapsed_time = time.time() - start_time
    print(f"\n      Optimization Completed in {elapsed_time:.2f} seconds.")
    
    # 4. Display Final Best Plan Metrics
    m = best_solution.metrics
    print("\n" + "=" * 75)
    print("  OPTIMIZED UAV FLEET MISSION PLAN SUMMARY")
    print("=" * 75)
    print(f"  Final Multi-Objective Fitness:  {best_solution.fitness:8.2f}")
    print(f"  High-Priority Coverage Score:   {m['coverage_score']:8.2f} / {total_target_priority:.1f} ({m['detection_rate']*100:.1f}%)")
    print(f"  Unique Priority Cells Scanned:  {m['unique_cells_covered']} cells")
    print(f"  Total Fleet Energy Expenditure: {m['total_fleet_energy']:8.2f} kJ (Max allowance: {config.MAX_BATTERY_ENERGY * config.NUM_DRONES:.1f} kJ)")
    print(f"  Mission Makespan (Flight Time): {m['mission_time']:8.2f} seconds")
    print(f"  Cumulative Hazard Exposure:     {m['total_hazard_exposure']:8.2f}")
    print(f"  No-Fly Zone Collisions:         {m['nfz_violations']} (0 indicates fully compliant)")
    print(f"  Battery Constraint Violations:  {m['battery_excess']:.2f}")
    print("-" * 75)
    for d in range(best_solution.num_drones):
        print(f"    Drone {d+1}: Energy = {m['drone_energies'][d]:.2f} kJ | Flight Time = {m['drone_flight_times'][d]:.2f} s | "
              f"Speeds = {[float(v) for v in best_solution.speeds[d]]} | Sensors = {[int(s) for s in best_solution.sensors[d]]}")
    print("=" * 75)
    
    # 5. Generate and Save Visualizations
    print("\n[4/4] Generating Publication-Quality Plots...")
    conv_path = os.path.join(output_dir, "fitness_convergence.png")
    MissionVisualizer.plot_convergence(history, save_path=conv_path)
    
    map_path = os.path.join(output_dir, "final_flight_paths.png")
    MissionVisualizer.plot_flight_map(best_solution, env, title="Final Evolved UAV Fleet Trajectories & Coverage", save_path=map_path)
    
    evo_path = os.path.join(output_dir, "generational_evolution.png")
    MissionVisualizer.plot_generational_evolution(history['snapshots'], env, save_path=evo_path)
    
    print(f"\nAll visualization assets successfully generated in '{output_dir}'.")


if __name__ == '__main__':
    run_single_simulation()
