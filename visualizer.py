"""
Visualization module for UAV Fleet Disaster Management Simulation.
Generates publication-quality plots:
  - Fitness convergence (Best vs. Average)
  - Multi-objective metric progression (Coverage, Energy, Time, Hazard)
  - 2D Operational Mission Maps with hazard/obstacle overlays and UAV trajectories
  - Generational Evolution Comparisons (Early vs Mid vs Final)
  - Baseline Comparison (Genetic Algorithm vs Random Search)
  - Hyperparameter Sensitivity Analysis (Pop Size, Mutation Rate, Selection Pressure)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import config


class MissionVisualizer:
    """Provides modular plotting routines for GA optimization results and UAV spatial paths."""
    
    DRONE_COLORS = ['#1f77b4', '#e377c2', '#ff7f0e', '#2ca02c', '#9467bd']
    
    @staticmethod
    def setup_output_dir(dir_path="outputs"):
        """Ensures destination output directory exists."""
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    @classmethod
    def plot_convergence(cls, history, save_path=None):
        """
        Plots multi-objective fitness convergence curves:
          1. Best Fitness vs Average Fitness
          2. Priority Area Coverage Progression
          3. Total Energy Consumption and Mission Flight Time
        """
        generations = range(1, len(history['best_fitness']) + 1)
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle("Genetic Algorithm Multi-Objective Optimization Progression", fontsize=15, fontweight='bold', y=1.02)
        
        # 1. Fitness Convergence
        axes[0].plot(generations, history['best_fitness'], label='Best Fitness', color='#2ca02c', linewidth=2.5)
        axes[0].plot(generations, history['avg_fitness'], label='Population Average', color='#1f77b4', linestyle='--', linewidth=1.8)
        axes[0].set_title("Fitness Convergence over Generations", fontsize=12, fontweight='bold')
        axes[0].set_xlabel("Generation", fontsize=11)
        axes[0].set_ylabel("Fitness Score", fontsize=11)
        axes[0].grid(True, linestyle=':', alpha=0.6)
        axes[0].legend(loc='lower right', framealpha=0.9)
        
        # 2. Priority Coverage
        axes[1].plot(generations, history['best_coverage'], label='Disaster Priority Coverage', color='#ff7f0e', linewidth=2.2)
        axes[1].set_title("High-Priority Target Coverage", fontsize=12, fontweight='bold')
        axes[1].set_xlabel("Generation", fontsize=11)
        axes[1].set_ylabel("Coverage Score", fontsize=11)
        axes[1].grid(True, linestyle=':', alpha=0.6)
        axes[1].legend(loc='lower right', framealpha=0.9)
        
        # 3. Energy & Mission Time
        ax3_energy = axes[2]
        line1 = ax3_energy.plot(generations, history['best_energy'], label='Fleet Energy (kJ)', color='#d62728', linewidth=2.0)
        ax3_energy.set_xlabel("Generation", fontsize=11)
        ax3_energy.set_ylabel("Total Fleet Energy", color='#d62728', fontsize=11)
        ax3_energy.tick_params(axis='y', labelcolor='#d62728')
        
        ax3_time = ax3_energy.twinx()
        line2 = ax3_time.plot(generations, history['best_time'], label='Mission Time (s)', color='#9467bd', linestyle='-.', linewidth=2.0)
        ax3_time.set_ylabel("Mission Makespan (s)", color='#9467bd', fontsize=11)
        ax3_time.tick_params(axis='y', labelcolor='#9467bd')
        
        axes[2].set_title("Energy Expenditure & Mission Time", fontsize=12, fontweight='bold')
        axes[2].grid(True, linestyle=':', alpha=0.6)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        axes[2].legend(lines, labels, loc='upper right', framealpha=0.9)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Visualizer] Saved convergence plot to: {save_path}")
        plt.close(fig)

    @classmethod
    def plot_flight_map(cls, individual, environment, title="Optimized UAV Fleet Deployment", save_path=None):
        """
        Renders a detailed 2D operational disaster map displaying:
          - Target priority heatmap
          - Environmental hazard contours (radiation, smoke, winds)
          - No-Fly Zones (NFZ) / Obstacles
          - Individual UAV trajectories with waypoint nodes & sensor activation mode
        """
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # 1. Base grid: Priority Heatmap
        im = ax.imshow(environment.priority_grid.T, origin='lower', cmap='YlGnBu', alpha=0.65, extent=[0, environment.size, 0, environment.size])
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Target Priority Value', fontsize=11)
        
        # 2. Draw Hazard Zones
        for (hx, hy, h_rad, intensity) in config.HAZARD_ZONES:
            circle = patches.Circle((hx, hy), h_rad, linewidth=1.5, edgecolor='#d95f02', facecolor='#fd8d3c', alpha=0.35, linestyle='--')
            ax.add_patch(circle)
            ax.text(hx, hy, f"Hazard\n({intensity:.1f})", color='#7f2704', fontsize=8, ha='center', va='center', fontweight='bold')
            
        # 3. Draw No-Fly Zones (Obstacles)
        for (min_x, max_x, min_y, max_y) in config.NO_FLY_ZONES:
            width = max_x - min_x
            height = max_y - min_y
            rect = patches.Rectangle((min_x, min_y), width, height, linewidth=2.0, edgecolor='#252525', facecolor='#525252', hatch='//', alpha=0.85)
            ax.add_patch(rect)
            ax.text(min_x + width / 2.0, min_y + height / 2.0, "NFZ", color='white', fontsize=9, ha='center', va='center', fontweight='bold')

        # 4. Mark Base Station
        bx, by = config.BASE_STATION
        ax.scatter([bx], [by], s=250, c='gold', marker='*', edgecolors='black', linewidth=1.5, zorder=10, label='Base Station')
        ax.text(bx + 1.2, by + 1.2, "BASE", fontsize=10, fontweight='bold', color='black', zorder=11)

        # 5. Plot Drone Trajectories & Waypoints
        for d in range(individual.num_drones):
            color = cls.DRONE_COLORS[d % len(cls.DRONE_COLORS)]
            traj = individual.get_full_trajectory(d)
            
            # Plot intermediate legs
            num_legs = len(traj) - 1
            for leg in range(num_legs):
                p1 = traj[leg]
                p2 = traj[leg + 1]
                sensor_on = individual.sensors[d, leg] if leg < individual.num_waypoints else 0
                
                linestyle = '-' if sensor_on else ':'
                linewidth = 2.4 if sensor_on else 1.5
                alpha = 0.95 if sensor_on else 0.65
                
                # Draw path segment
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linestyle=linestyle, linewidth=linewidth, alpha=alpha, zorder=6)
                
                # Draw directional arrow along the segment
                mx = (p1[0] + p2[0]) / 2.0
                my = (p1[1] + p2[1]) / 2.0
                dx = (p2[0] - p1[0]) * 0.001
                dy = (p2[1] - p1[1]) * 0.001
                ax.annotate('', xy=(mx + dx, my + dy), xytext=(mx, my),
                            arrowprops=dict(arrowstyle="->", color=color, lw=2.0), zorder=7)
                
                # If sensor is ON, draw sensing footprint circle around waypoint
                if sensor_on and leg < individual.num_waypoints:
                    wp = traj[leg + 1]
                    sensor_circle = patches.Circle((wp[0], wp[1]), config.SENSOR_RADIUS,
                                                   linewidth=0.8, edgecolor=color, facecolor=color, alpha=0.15, zorder=4)
                    ax.add_patch(sensor_circle)

            # Scatter waypoints
            wps = individual.waypoints[d]
            ax.scatter(wps[:, 0], wps[:, 1], s=70, color=color, edgecolors='black', linewidth=1.0, zorder=8)
            for w_idx, (wx, wy) in enumerate(wps):
                ax.text(wx + 0.6, wy + 0.6, f"D{d+1}.{w_idx+1}", fontsize=7.5, color='black', fontweight='semibold', zorder=9)

        # Title and Metrics Display
        m = individual.metrics
        subtitle = (f"Fitness: {individual.fitness:.1f} | Priority Coverage: {m.get('coverage_score', 0):.1f} "
                    f"({m.get('detection_rate', 0)*100:.1f}%) | Energy: {m.get('total_fleet_energy', 0):.1f} kJ | "
                    f"NFZ Collisions: {m.get('nfz_violations', 0)}")
        
        ax.set_title(f"{title}\n{subtitle}", fontsize=12, fontweight='bold', pad=12)
        ax.set_xlim(-1, environment.size + 1)
        ax.set_ylim(-1, environment.size + 1)
        ax.set_xlabel("X Coordinate (Grid Cells)", fontsize=11)
        ax.set_ylabel("Y Coordinate (Grid Cells)", fontsize=11)
        ax.set_aspect('equal')
        ax.grid(True, linestyle=':', alpha=0.4)

        # Custom Legend
        custom_lines = [
            Line2D([0], [0], marker='*', color='w', markerfacecolor='gold', markeredgecolor='black', markersize=14, label='Base Station'),
            patches.Patch(facecolor='#525252', edgecolor='#252525', hatch='//', label='No-Fly Zone (NFZ)'),
            patches.Patch(facecolor='#fd8d3c', edgecolor='#d95f02', alpha=0.5, label='Hazard Zone'),
            Line2D([0], [0], color='black', linestyle='-', linewidth=2, label='Sensor ON (Active Scan)'),
            Line2D([0], [0], color='black', linestyle=':', linewidth=1.5, label='Sensor OFF (Transit)')
        ]
        for d in range(individual.num_drones):
            c = cls.DRONE_COLORS[d % len(cls.DRONE_COLORS)]
            custom_lines.append(Line2D([0], [0], color=c, lw=2.5, label=f'Drone {d+1} Trajectory'))
            
        ax.legend(handles=custom_lines, loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0., framealpha=0.95, fontsize=9.5)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Visualizer] Saved mission map to: {save_path}")
        plt.close(fig)

    @classmethod
    def plot_generational_evolution(cls, snapshots, environment, save_path=None):
        """
        Plots multi-panel comparison showing UAV flight paths evolving across generations:
        Initial Random Deployment (Gen 1) -> Mid Optimization -> Final Evolved Solution.
        """
        gen_keys = sorted(snapshots.keys())
        n_plots = len(gen_keys)
        fig, axes = plt.subplots(1, n_plots, figsize=(6.5 * n_plots, 6))
        if n_plots == 1:
            axes = [axes]
            
        fig.suptitle("UAV Fleet Trajectory Evolution Across Generations", fontsize=15, fontweight='bold', y=1.03)
        
        for idx, gen in enumerate(gen_keys):
            ax = axes[idx]
            ind = snapshots[gen]
            
            # Base heatmap
            ax.imshow(environment.priority_grid.T, origin='lower', cmap='YlGnBu', alpha=0.6, extent=[0, environment.size, 0, environment.size])
            
            # Obstacles
            for (min_x, max_x, min_y, max_y) in config.NO_FLY_ZONES:
                rect = patches.Rectangle((min_x, min_y), max_x - min_x, max_y - min_y, linewidth=1.2, edgecolor='#252525', facecolor='#525252', hatch='//', alpha=0.8)
                ax.add_patch(rect)
                
            # Hazards
            for (hx, hy, h_rad, intensity) in config.HAZARD_ZONES:
                circle = patches.Circle((hx, hy), h_rad, linewidth=1.0, edgecolor='#d95f02', facecolor='#fd8d3c', alpha=0.3, linestyle='--')
                ax.add_patch(circle)
                
            # Base
            bx, by = config.BASE_STATION
            ax.scatter([bx], [by], s=160, c='gold', marker='*', edgecolors='black', zorder=10)
            
            # Trajectories
            for d in range(ind.num_drones):
                color = cls.DRONE_COLORS[d % len(cls.DRONE_COLORS)]
                traj = ind.get_full_trajectory(d)
                ax.plot(traj[:, 0], traj[:, 1], color=color, linewidth=2.0, alpha=0.9, zorder=6)
                ax.scatter(traj[1:-1, 0], traj[1:-1, 1], s=40, color=color, edgecolors='black', zorder=7)
                
            m = ind.metrics
            ax.set_title(f"Generation {gen}\nFitness: {ind.fitness:.1f} | Cov: {m.get('coverage_score', 0):.0f} | NFZ Viol: {m.get('nfz_violations', 0)}", fontsize=11, fontweight='bold')
            ax.set_xlim(-1, environment.size + 1)
            ax.set_ylim(-1, environment.size + 1)
            ax.set_aspect('equal')
            ax.grid(True, linestyle=':', alpha=0.4)
            
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Visualizer] Saved generational evolution to: {save_path}")
        plt.close(fig)

    @classmethod
    def plot_baseline_comparison(cls, ga_history, random_history, save_path=None):
        """
        Plots comparative convergence: Genetic Algorithm vs. Baseline Random Search.
        """
        fig, ax = plt.subplots(figsize=(9, 5.5))
        
        # Evaluations or generations
        steps = range(1, len(ga_history['best_fitness']) + 1)
        
        ax.plot(steps, ga_history['best_fitness'], label='Genetic Algorithm (Best Fitness)', color='#2ca02c', linewidth=2.6)
        ax.plot(steps, ga_history['avg_fitness'], label='Genetic Algorithm (Population Avg)', color='#1f77b4', linestyle=':', linewidth=1.8)
        ax.plot(steps, random_history['best_fitness'], label='Baseline Random Search (Best-so-far)', color='#d62728', linestyle='--', linewidth=2.2)
        ax.plot(steps, random_history['avg_fitness'], label='Baseline Random Search (Sample Avg)', color='#ff7f0e', linestyle='-.', linewidth=1.5, alpha=0.8)
        
        ax.set_title("Comparative Optimization Performance: GA vs. Baseline Random Search", fontsize=13, fontweight='bold', pad=10)
        ax.set_xlabel("Generational Batch Equivalent", fontsize=11)
        ax.set_ylabel("Fitness Score", fontsize=11)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='lower right', framealpha=0.95, fontsize=10.5)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Visualizer] Saved baseline comparison plot to: {save_path}")
        plt.close(fig)

    @classmethod
    def plot_sensitivity_analysis(cls, sensitivity_data, save_path=None):
        """
        Generates 3-panel hyperparameter sensitivity curves:
          1. Population Size Sensitivity
          2. Mutation Rate Sensitivity
          3. Selection Pressure (Tournament Size) Sensitivity
        """
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle("Hyperparameter Sensitivity Analysis", fontsize=15, fontweight='bold', y=1.02)
        
        # 1. Population Size
        ax1 = axes[0]
        for pop_size, curve in sensitivity_data.get('pop_size', {}).items():
            ax1.plot(range(1, len(curve) + 1), curve, label=f'Pop Size = {pop_size}', linewidth=2.0)
        ax1.set_title("Impact of Population Size", fontsize=12, fontweight='bold')
        ax1.set_xlabel("Generation", fontsize=11)
        ax1.set_ylabel("Best Fitness", fontsize=11)
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.legend(loc='lower right', framealpha=0.9)
        
        # 2. Mutation Rate
        ax2 = axes[1]
        for m_rate, curve in sensitivity_data.get('mutation_rate', {}).items():
            ax2.plot(range(1, len(curve) + 1), curve, label=f'Mutation Rate = {m_rate}', linewidth=2.0)
        ax2.set_title("Impact of Mutation Rate", fontsize=12, fontweight='bold')
        ax2.set_xlabel("Generation", fontsize=11)
        ax2.set_ylabel("Best Fitness", fontsize=11)
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.legend(loc='lower right', framealpha=0.9)
        
        # 3. Tournament Size
        ax3 = axes[2]
        for t_size, curve in sensitivity_data.get('tournament_size', {}).items():
            ax3.plot(range(1, len(curve) + 1), curve, label=f'Tournament k = {t_size}', linewidth=2.0)
        ax3.set_title("Impact of Selection Pressure (Tournament Size)", fontsize=12, fontweight='bold')
        ax3.set_xlabel("Generation", fontsize=11)
        ax3.set_ylabel("Best Fitness", fontsize=11)
        ax3.grid(True, linestyle=':', alpha=0.6)
        ax3.legend(loc='lower right', framealpha=0.9)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Visualizer] Saved sensitivity analysis plot to: {save_path}")
        plt.close(fig)
