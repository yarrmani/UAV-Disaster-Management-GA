"""
Configuration module for UAV Fleet Disaster Management GA Optimization.
Defines grid parameters, drone characteristics, energy models, and GA hyperparameters.
"""

# ==========================================
# 1. Grid & Mission Space Configuration
# ==========================================
GRID_SIZE = 50  # 50x50 cell discretized mission area

# Base station where UAVs are deployed from and return to
BASE_STATION = (0.0, 0.0)

# Disaster high-priority zones (clusters with priority values 1 to 10)
# Format: (center_x, center_y, radius, priority_weight, description)
TARGET_ZONES = [
    (15, 35, 6.0, 9.0, "Trapped Survivors (Sector Alpha)"),
    (38, 40, 5.0, 8.5, "Chemical Plant Leak (Sector Beta)"),
    (35, 12, 6.0, 7.5, "Submerged Hospital Substation (Sector Gamma)"),
    (12, 15, 4.0, 6.0, "Collapsed Bridge / Evac Route (Sector Delta)"),
    (25, 25, 4.5, 7.0, "Damaged Power Grid (Sector Epsilon)")
]

# Environmental hazard zones (continuous risk e.g., radiation, smoke, strong turbulence)
# Format: (center_x, center_y, radius, hazard_intensity [0.0 - 1.0])
HAZARD_ZONES = [
    (20, 28, 7.0, 0.75),   # Dense toxic smoke plume
    (32, 22, 6.0, 0.60),   # Severe wind shear / turbulence
    (10, 40, 5.0, 0.85),   # Radiation hot-spot
    (40, 30, 5.5, 0.70)    # Active wildfire boundary
]

# No-Fly Zones (NFZ) / Obstacles (Hard blocked cells e.g. collapsed skyscrapers, military zones)
# Format: (min_x, max_x, min_y, max_y)
NO_FLY_ZONES = [
    (22, 28, 10, 16),      # Collapsed high-rise cluster
    (5, 10, 22, 28),       # Active electrical substation fire
    (30, 36, 32, 38)       # Restricted airspace corridor
]


# ==========================================
# 2. UAV Fleet Specifications
# ==========================================
NUM_DRONES = 3                    # Fleet size
NUM_WAYPOINTS_PER_DRONE = 5       # Intermediate exploration waypoints per drone
SENSOR_RADIUS = 4.0               # Sensing footprint radius (cells)
MAX_BATTERY_ENERGY = 220.0        # Max allowable battery energy capacity per drone

# Available discrete speed levels (cells per time unit)
SPEED_LEVELS = [1.0, 2.0, 3.0]    # 1.0 = Slow/Thorough, 2.0 = Medium/Cruise, 3.0 = High/Dash


# ==========================================
# 3. Energy & Physics Model Parameters
# ==========================================
PROPULSION_BASE_COST = 1.0        # Base energy per unit distance
PROPULSION_SPEED_FACTOR = 0.25    # Non-linear energy expenditure factor proportional to v^2
SENSOR_POWER_COST = 0.75          # Energy per time unit when sensor is actively scanning
HAZARD_ENERGY_PENALTY = 1.40      # Energy multiplier when traversing through hazard pockets


# ==========================================
# 4. Multi-Objective Evaluation Weights
# ==========================================
W_COVERAGE = 1.20                 # Maximization weight for priority area coverage
W_ENERGY = 0.35                   # Minimization weight for fleet battery consumption
W_TIME = 0.25                     # Minimization weight for total mission completion time
W_HAZARD = 0.50                   # Minimization weight for cumulative hazard exposure

# Hard constraint violation penalties
PENALTY_NFZ = 600.0               # Severe penalty per violation of No-Fly Zone
PENALTY_BATTERY = 400.0           # Severe penalty for draining battery beyond max capacity


# ==========================================
# 5. Genetic Algorithm Default Hyperparameters
# ==========================================
DEFAULT_POP_SIZE = 50             # Population size
DEFAULT_GENERATIONS = 60          # Number of iterations / generations
DEFAULT_CROSSOVER_RATE = 0.80     # Probability of mating crossover
DEFAULT_MUTATION_RATE = 0.15      # Probability of gene mutation
DEFAULT_TOURNAMENT_SIZE = 3       # Selection pressure
DEFAULT_ELITISM_COUNT = 2         # Best individuals preserved unchanged per generation
RANDOM_SEED = 42                  # Reproducibility seed
