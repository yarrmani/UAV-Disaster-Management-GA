"""
Environment module for UAV Fleet Disaster Management Simulation.
Models a 2D discretized matrix grid with disaster priority zones,
environmental hazard fields (smoke, winds, radiation), and No-Fly Zones (NFZ).
"""

import numpy as np
import config


class GridEnvironment:
    """
    Represents the operational disaster surveillance environment.
    Translates continuous spatial flight coordinates into discretized grid cells.
    """
    def __init__(self, size=config.GRID_SIZE):
        self.size = size
        self.priority_grid = np.zeros((size, size), dtype=float)
        self.hazard_grid = np.zeros((size, size), dtype=float)
        self.obstacle_mask = np.zeros((size, size), dtype=bool)
        
        # Precompute circular relative offsets for sensing footprint calculation
        r = int(np.ceil(config.SENSOR_RADIUS))
        self.sensor_offsets = [
            (dx, dy) for dx in range(-r, r + 1)
            for dy in range(-r, r + 1)
            if (dx * dx + dy * dy) <= (config.SENSOR_RADIUS ** 2)
        ]
        
        self._initialize_zones()
        
    def _initialize_zones(self):
        """Populates targets, hazards, and obstacles from configuration."""
        # 1. Populate Target Priority Zones
        for (cx, cy, radius, priority, desc) in config.TARGET_ZONES:
            r_int = int(np.ceil(radius))
            x_min = max(0, int(cx - r_int))
            x_max = min(self.size, int(cx + r_int + 1))
            y_min = max(0, int(cy - r_int))
            y_max = min(self.size, int(cy + r_int + 1))
            
            for x in range(x_min, x_max):
                for y in range(y_min, y_max):
                    dist = np.hypot(x - cx, y - cy)
                    if dist <= radius:
                        val = priority * (1.0 - 0.3 * (dist / radius))
                        self.priority_grid[x, y] = max(self.priority_grid[x, y], val)
                        
        # 2. Populate Environmental Hazard Zones (smoke, wind, radiation)
        for (hx, hy, h_rad, intensity) in config.HAZARD_ZONES:
            r_int = int(np.ceil(h_rad))
            x_min = max(0, int(hx - r_int))
            x_max = min(self.size, int(hx + r_int + 1))
            y_min = max(0, int(hy - r_int))
            y_max = min(self.size, int(hy + r_int + 1))
            
            for x in range(x_min, x_max):
                for y in range(y_min, y_max):
                    dist = np.hypot(x - hx, y - hy)
                    if dist <= h_rad:
                        h_val = intensity * np.exp(-0.5 * (dist / (h_rad / 2.0)) ** 2)
                        self.hazard_grid[x, y] = max(self.hazard_grid[x, y], float(h_val))
                        
        # 3. Populate No-Fly Zones (NFZ / Obstacles)
        for (min_x, max_x, min_y, max_y) in config.NO_FLY_ZONES:
            x_start = max(0, min_x)
            x_end = min(self.size, max_x)
            y_start = max(0, min_y)
            y_end = min(self.size, max_y)
            self.obstacle_mask[x_start:x_end, y_start:y_end] = True
            self.priority_grid[x_start:x_end, y_start:y_end] = 0.0

    def is_inside_bounds(self, x, y):
        """Check if coordinates fall strictly within grid bounds."""
        return 0 <= x < self.size and 0 <= y < self.size

    def is_obstacle(self, x, y):
        """Check if grid cell is marked as obstacle or restricted airspace."""
        ix, iy = int(round(np.clip(x, 0, self.size - 1))), int(round(np.clip(y, 0, self.size - 1)))
        return self.obstacle_mask[ix, iy]

    def repair_coordinate(self, x, y):
        """
        Dynamically repairs waypoints violating physical boundaries or No-Fly Zones.
        Clamps within grid bounds and nudges away from obstacles.
        """
        rx = float(np.clip(x, 0.0, self.size - 1.0))
        ry = float(np.clip(y, 0.0, self.size - 1.0))
        
        if self.is_obstacle(rx, ry):
            for step in range(1, 10):
                for dx in [-step, 0, step]:
                    for dy in [-step, 0, step]:
                        nx, ny = rx + dx, ry + dy
                        if self.is_inside_bounds(nx, ny) and not self.is_obstacle(nx, ny):
                            return float(nx), float(ny)
        return rx, ry

    def fast_sample_line(self, p1, p2, step_size=2.0):
        """
        Fast line-segment sampler for collision and hazard integration.
        Uses pure arithmetic for minimal overhead.
        """
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dist = float(np.hypot(dx, dy))
        if dist < 1e-4:
            return [(p1[0], p1[1])], dist
        
        num_steps = max(2, int(np.ceil(dist / step_size)))
        step_x = dx / (num_steps - 1)
        step_y = dy / (num_steps - 1)
        points = [(p1[0] + i * step_x, p1[1] + i * step_y) for i in range(num_steps)]
        return points, dist

    def get_priority_cells_in_footprint(self, center_x, center_y):
        """
        Ultra-fast priority scanner: returns only priority-bearing cells covered by sensor footprint.
        """
        ix = int(round(center_x))
        iy = int(round(center_y))
        priority_cells = set()
        
        for dx, dy in self.sensor_offsets:
            nx = ix + dx
            ny = iy + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if self.priority_grid[nx, ny] > 0.0:
                    priority_cells.add((nx, ny))
                    
        return priority_cells
