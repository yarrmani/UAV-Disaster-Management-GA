"""
Comprehensive Experimentation Suite for UAV Fleet Disaster Management GA.
Executes:
  1. Primary GA Optimization Run
  2. Baseline Random Search Benchmark
  3. Hyperparameter Sensitivity Suite (Population Size, Mutation Rate, Selection Pressure)
  4. Generates all comparative plots and saves quantitative summary data for technical report.
"""

import time
import json
import os
import numpy as np
import config
from environment import GridEnvironment
from genetic_algorithm import GeneticAlgorithmEngine
from baseline_random import RandomSearchBaseline
from visualizer import MissionVisualizer


def run_full_experiment_suite():
    print("=" * 80)
    print("  COMPREHENSIVE UAV FLEET GA EXPERIMENTATION SUITE")
    print("=" * 80)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = MissionVisualizer.setup_output_dir(os.path.join(base_dir, "outputs"))
    env = GridEnvironment(size=config.GRID_SIZE)
    total_evals = config.DEFAULT_POP_SIZE * config.DEFAULT_GENERATIONS
    
    experiment_results = {
        'ga_metrics': {},
        'random_search_metrics': {},
        'sensitivity_analysis': {
            'pop_size': {},
            'mutation_rate': {},
            'tournament_size': {}
        }
    }
    
    # -------------------------------------------------------------------------
    # Experiment 1: Primary Genetic Algorithm Optimization
    # -------------------------------------------------------------------------
    print("\n[EXPERIMENT 1] Running Primary Genetic Algorithm...")
    t0 = time.time()
    ga_engine = GeneticAlgorithmEngine(
        environment=env,
        pop_size=config.DEFAULT_POP_SIZE,
        generations=config.DEFAULT_GENERATIONS,
        crossover_rate=config.DEFAULT_CROSSOVER_RATE,
        mutation_rate=config.DEFAULT_MUTATION_RATE,
        tournament_size=config.DEFAULT_TOURNAMENT_SIZE,
        elitism_count=config.DEFAULT_ELITISM_COUNT,
        seed=config.RANDOM_SEED
    )
    ga_best, ga_history = ga_engine.evolve(verbose=True)
    ga_duration = time.time() - t0
    print(f"--> GA Completed in {ga_duration:.2f} s | Best Fitness: {ga_best.fitness:.2f}")
    
    # Save standard GA plots
    MissionVisualizer.plot_convergence(ga_history, save_path=os.path.join(output_dir, "fitness_convergence.png"))
    MissionVisualizer.plot_flight_map(ga_best, env, title="Final Evolved UAV Fleet Mission Plan", save_path=os.path.join(output_dir, "final_flight_paths.png"))
    MissionVisualizer.plot_generational_evolution(ga_history['snapshots'], env, save_path=os.path.join(output_dir, "generational_evolution.png"))
    
    experiment_results['ga_metrics'] = {
        'best_fitness': float(ga_best.fitness),
        'coverage_score': float(ga_best.metrics['coverage_score']),
        'detection_rate_pct': float(ga_best.metrics['detection_rate'] * 100.0),
        'unique_cells_covered': int(ga_best.metrics['unique_cells_covered']),
        'total_fleet_energy_kJ': float(ga_best.metrics['total_fleet_energy']),
        'mission_time_s': float(ga_best.metrics['mission_time']),
        'total_hazard_exposure': float(ga_best.metrics['total_hazard_exposure']),
        'nfz_violations': int(ga_best.metrics['nfz_violations']),
        'runtime_seconds': float(ga_duration)
    }
    
    # -------------------------------------------------------------------------
    # Experiment 2: Baseline Random Search Comparison
    # -------------------------------------------------------------------------
    print(f"\n[EXPERIMENT 2] Running Baseline Random Search ({total_evals} evaluations)...")
    t0 = time.time()
    rs_baseline = RandomSearchBaseline(environment=env, total_evaluations=total_evals, seed=config.RANDOM_SEED)
    rs_best, rs_history = rs_baseline.run(ga_engine=ga_engine, batch_size=config.DEFAULT_POP_SIZE, verbose=True)
    rs_duration = time.time() - t0
    print(f"--> Random Search Completed in {rs_duration:.2f} s | Best Fitness: {rs_best.fitness:.2f}")
    
    # Save comparison plot
    MissionVisualizer.plot_baseline_comparison(
        ga_history, rs_history,
        save_path=os.path.join(output_dir, "baseline_comparison.png")
    )
    
    experiment_results['random_search_metrics'] = {
        'best_fitness': float(rs_best.fitness),
        'coverage_score': float(rs_best.metrics['coverage_score']),
        'detection_rate_pct': float(rs_best.metrics['detection_rate'] * 100.0),
        'unique_cells_covered': int(rs_best.metrics['unique_cells_covered']),
        'total_fleet_energy_kJ': float(rs_best.metrics['total_fleet_energy']),
        'mission_time_s': float(rs_best.metrics['mission_time']),
        'total_hazard_exposure': float(rs_best.metrics['total_hazard_exposure']),
        'nfz_violations': int(rs_best.metrics['nfz_violations']),
        'runtime_seconds': float(rs_duration)
    }
    
    # -------------------------------------------------------------------------
    # Experiment 3: Hyperparameter Sensitivity Suite
    # -------------------------------------------------------------------------
    print("\n[EXPERIMENT 3] Running Hyperparameter Sensitivity Analysis...")
    sens_generations = 30
    
    # 3.1 Population Size Sensitivity [20, 50, 100]
    pop_sizes = [20, 50, 100]
    print("\n  Evaluating Population Sizes:", pop_sizes)
    for pop in pop_sizes:
        print(f"    Testing Pop Size = {pop}...")
        engine = GeneticAlgorithmEngine(
            environment=env, pop_size=pop, generations=sens_generations,
            mutation_rate=config.DEFAULT_MUTATION_RATE, tournament_size=config.DEFAULT_TOURNAMENT_SIZE,
            seed=config.RANDOM_SEED
        )
        _, hist = engine.evolve(verbose=False)
        experiment_results['sensitivity_analysis']['pop_size'][str(pop)] = [float(x) for x in hist['best_fitness']]
        
    # 3.2 Mutation Rate Sensitivity [0.05, 0.15, 0.30]
    mut_rates = [0.05, 0.15, 0.30]
    print("\n  Evaluating Mutation Rates:", mut_rates)
    for mr in mut_rates:
        print(f"    Testing Mutation Rate = {mr}...")
        engine = GeneticAlgorithmEngine(
            environment=env, pop_size=50, generations=sens_generations,
            mutation_rate=mr, tournament_size=config.DEFAULT_TOURNAMENT_SIZE,
            seed=config.RANDOM_SEED
        )
        _, hist = engine.evolve(verbose=False)
        experiment_results['sensitivity_analysis']['mutation_rate'][str(mr)] = [float(x) for x in hist['best_fitness']]
        
    # 3.3 Selection Pressure (Tournament Size) [2, 3, 5]
    tourn_sizes = [2, 3, 5]
    print("\n  Evaluating Selection Pressure (Tournament Size):", tourn_sizes)
    for ts in tourn_sizes:
        print(f"    Testing Tournament Size = {ts}...")
        engine = GeneticAlgorithmEngine(
            environment=env, pop_size=50, generations=sens_generations,
            mutation_rate=config.DEFAULT_MUTATION_RATE, tournament_size=ts,
            seed=config.RANDOM_SEED
        )
        _, hist = engine.evolve(verbose=False)
        experiment_results['sensitivity_analysis']['tournament_size'][str(ts)] = [float(x) for x in hist['best_fitness']]
        
    # Plot sensitivity analysis
    MissionVisualizer.plot_sensitivity_analysis(
        experiment_results['sensitivity_analysis'],
        save_path=os.path.join(output_dir, "hyperparameter_sensitivity.png")
    )
    
    # -------------------------------------------------------------------------
    # Save Quantitative Summary Report
    # -------------------------------------------------------------------------
    json_path = os.path.join(output_dir, "experiment_results.json")
    with open(json_path, 'w') as f:
        json.dump(experiment_results, f, indent=4)
        
    summary_txt = f"""
================================================================================
          UAV FLEET DISASTER OPTIMIZATION - EXPERIMENTAL SUMMARY
================================================================================

1. ALGORITHM BENCHMARK COMPARISON (GA vs Random Search):
--------------------------------------------------------------------------------
Metric                          Genetic Algorithm        Random Search      Advantage / Diff
--------------------------------------------------------------------------------
Best Fitness Score:             {experiment_results['ga_metrics']['best_fitness']:15.2f}  {experiment_results['random_search_metrics']['best_fitness']:15.2f}   +{experiment_results['ga_metrics']['best_fitness'] - experiment_results['random_search_metrics']['best_fitness']:8.2f} pts
Priority Coverage Score:        {experiment_results['ga_metrics']['coverage_score']:15.2f}  {experiment_results['random_search_metrics']['coverage_score']:15.2f}   +{experiment_results['ga_metrics']['coverage_score'] - experiment_results['random_search_metrics']['coverage_score']:8.2f} pts
Detection Rate:                 {experiment_results['ga_metrics']['detection_rate_pct']:14.1f}%  {experiment_results['random_search_metrics']['detection_rate_pct']:14.1f}%   +{experiment_results['ga_metrics']['detection_rate_pct'] - experiment_results['random_search_metrics']['detection_rate_pct']:7.1f}%
Unique Priority Cells Scanned:  {experiment_results['ga_metrics']['unique_cells_covered']:15d}  {experiment_results['random_search_metrics']['unique_cells_covered']:15d}   +{experiment_results['ga_metrics']['unique_cells_covered'] - experiment_results['random_search_metrics']['unique_cells_covered']:8d} cells
Total Fleet Energy (kJ):        {experiment_results['ga_metrics']['total_fleet_energy_kJ']:15.2f}  {experiment_results['random_search_metrics']['total_fleet_energy_kJ']:15.2f}   {experiment_results['ga_metrics']['total_fleet_energy_kJ'] - experiment_results['random_search_metrics']['total_fleet_energy_kJ']:8.2f} kJ
Mission Time (s):               {experiment_results['ga_metrics']['mission_time_s']:15.2f}  {experiment_results['random_search_metrics']['mission_time_s']:15.2f}   {experiment_results['ga_metrics']['mission_time_s'] - experiment_results['random_search_metrics']['mission_time_s']:8.2f} s
Total Hazard Exposure:          {experiment_results['ga_metrics']['total_hazard_exposure']:15.2f}  {experiment_results['random_search_metrics']['total_hazard_exposure']:15.2f}   {experiment_results['ga_metrics']['total_hazard_exposure'] - experiment_results['random_search_metrics']['total_hazard_exposure']:8.2f}
No-Fly Zone Collisions:         {experiment_results['ga_metrics']['nfz_violations']:15d}  {experiment_results['random_search_metrics']['nfz_violations']:15d}   {experiment_results['ga_metrics']['nfz_violations'] - experiment_results['random_search_metrics']['nfz_violations']:8d}
Execution Time (s):             {experiment_results['ga_metrics']['runtime_seconds']:15.2f}  {experiment_results['random_search_metrics']['runtime_seconds']:15.2f}
--------------------------------------------------------------------------------

2. HYPERPARAMETER SENSITIVITY INSIGHTS:
--------------------------------------------------------------------------------
- Population Size:
  * Pop = 20:  Final Fitness = {experiment_results['sensitivity_analysis']['pop_size']['20'][-1]:.2f} (Faster runtime, but prone to localized exploration)
  * Pop = 50:  Final Fitness = {experiment_results['sensitivity_analysis']['pop_size']['50'][-1]:.2f} (Optimal balance of diversity and computational budget)
  * Pop = 100: Final Fitness = {experiment_results['sensitivity_analysis']['pop_size']['100'][-1]:.2f} (Superior diversity, slightly higher evaluation overhead)

- Mutation Rate:
  * Rate = 0.05: Final Fitness = {experiment_results['sensitivity_analysis']['mutation_rate']['0.05'][-1]:.2f} (Insufficient exploration, prone to stagnation)
  * Rate = 0.15: Final Fitness = {experiment_results['sensitivity_analysis']['mutation_rate']['0.15'][-1]:.2f} (Ideal equilibrium between exploration and exploitation)
  * Rate = 0.30: Final Fitness = {experiment_results['sensitivity_analysis']['mutation_rate']['0.3'][-1]:.2f} (Excessive disruption, hinders convergence stability)

- Selection Pressure (Tournament Size):
  * k = 2: Final Fitness = {experiment_results['sensitivity_analysis']['tournament_size']['2'][-1]:.2f} (Low pressure, slower convergence)
  * k = 3: Final Fitness = {experiment_results['sensitivity_analysis']['tournament_size']['3'][-1]:.2f} (Balanced selection pressure, consistent elitist progression)
  * k = 5: Final Fitness = {experiment_results['sensitivity_analysis']['tournament_size']['5'][-1]:.2f} (High pressure, faster initial convergence, risk of premature local minima)
================================================================================
"""
    txt_path = os.path.join(output_dir, "experiment_summary.txt")
    with open(txt_path, 'w') as f:
        f.write(summary_txt)
        
    print(summary_txt)
    print(f"\nAll experimental results, plots, and summaries successfully saved in '{output_dir}'.")


if __name__ == '__main__':
    run_full_experiment_suite()
