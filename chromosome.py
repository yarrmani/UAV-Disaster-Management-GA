"""
Chromosome module for UAV Fleet Path Optimization.
Implements a hybrid multi-segment encoding scheme encapsulating:
  - Spatial flight waypoints (continuous real-valued coordinates)
  - Speed adjustments (discrete velocity choices per leg)
  - Sensor activation profiles (binary activation bit-strings)
"""

import numpy as np
import config


class UAVChromosome:
    """
    Hybrid multi-segment chromosome representing a full fleet surveillance plan.
    
    Structure:
      - waypoints: np.ndarray shape (num_drones, num_waypoints, 2) [Real-valued]
      - speeds:    np.ndarray shape (num_drones, num_waypoints + 1) [Discrete choice]
      - sensors:   np.ndarray shape (num_drones, num_waypoints)     [Binary: 0 or 1]
    """
    def __init__(self, num_drones=config.NUM_DRONES, num_waypoints=config.NUM_WAYPOINTS_PER_DRONE):
        self.num_drones = num_drones
        self.num_waypoints = num_waypoints
        
        # Segment 1: Spatial coordinates (x, y) for intermediate waypoints
        self.waypoints = np.zeros((num_drones, num_waypoints, 2), dtype=float)
        
        # Segment 2: Speed level for each leg (including return leg to base)
        self.speeds = np.ones((num_drones, num_waypoints + 1), dtype=float) * 2.0
        
        # Segment 3: Sensor power profile (1 = Active/Scanning, 0 = Standby/Transit)
        self.sensors = np.ones((num_drones, num_waypoints), dtype=int)
        
        # Evaluation attributes
        self.fitness = None
        self.metrics = {}

    @classmethod
    def create_random(cls, environment, num_drones=config.NUM_DRONES, num_waypoints=config.NUM_WAYPOINTS_PER_DRONE):
        """Factory method: generates a valid randomly initialized individual."""
        ind = cls(num_drones, num_waypoints)
        
        # Initialize waypoints uniformly across grid, avoiding immediate obstacles
        for d in range(num_drones):
            for w in range(num_waypoints):
                rx = np.random.uniform(2.0, environment.size - 2.0)
                ry = np.random.uniform(2.0, environment.size - 2.0)
                rx, ry = environment.repair_coordinate(rx, ry)
                ind.waypoints[d, w] = [rx, ry]
                
            # Randomize speeds from available speed levels
            ind.speeds[d] = np.random.choice(config.SPEED_LEVELS, size=num_waypoints + 1)
            
            # Randomize sensor profiles (e.g. 70% probability active initially)
            ind.sensors[d] = np.random.choice([0, 1], size=num_waypoints, p=[0.25, 0.75])
            
        return ind

    def copy(self):
        """Creates a deep copy of the chromosome."""
        clone = UAVChromosome(self.num_drones, self.num_waypoints)
        clone.waypoints = np.copy(self.waypoints)
        clone.speeds = np.copy(self.speeds)
        clone.sensors = np.copy(self.sensors)
        clone.fitness = self.fitness
        clone.metrics = dict(self.metrics)
        return clone

    def repair(self, environment):
        """
        Dynamic constraint handling repair mechanism:
        Snaps out-of-boundary coordinates and relocates waypoints landing in No-Fly Zones.
        """
        for d in range(self.num_drones):
            for w in range(self.num_waypoints):
                x, y = self.waypoints[d, w]
                rx, ry = environment.repair_coordinate(x, y)
                self.waypoints[d, w] = [rx, ry]

    def get_full_trajectory(self, drone_idx):
        """
        Returns full ordered list of coordinates for drone_idx:
        [Base Station -> Waypoint_1 -> ... -> Waypoint_K -> Base Station]
        """
        base = np.array(config.BASE_STATION, dtype=float)
        wps = self.waypoints[drone_idx]
        return np.vstack([base, wps, base])
