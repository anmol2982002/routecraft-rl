"""A dependency-free, Gymnasium-shaped courier task environment."""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path
from typing import Any

ACTIONS = ("north", "east", "south", "west")
DELTAS = {"north": (-1, 0), "east": (0, 1), "south": (1, 0), "west": (0, -1)}
CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "task_catalog.json"


def _catalog() -> dict[str, Any]:
    with CATALOG_PATH.open(encoding="utf-8") as stream:
        return json.load(stream)


def _neighbors(pos: tuple[int, int], size: int, walls: set[tuple[int, int]]):
    for action in ACTIONS:
        dr, dc = DELTAS[action]
        nxt = pos[0] + dr, pos[1] + dc
        if 0 <= nxt[0] < size and 0 <= nxt[1] < size and nxt not in walls:
            yield action, nxt


def _distance(start: tuple[int, int], goal: tuple[int, int], size: int,
              walls: set[tuple[int, int]]) -> int | None:
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        pos, distance = queue.popleft()
        if pos == goal:
            return distance
        for _, nxt in _neighbors(pos, size, walls):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, distance + 1))
    return None


class GridCourierEnv:
    """Move a courier to a parcel, then deliver it.

    ``reset`` returns an observation. ``step`` returns the five values used by
    modern Gymnasium-style APIs: observation, reward, terminated, truncated,
    and info. Observations contain the whole map and the current hazard phase,
    so the task is fully observable and suitable for planners or learned agents.
    """

    def __init__(self, task: str = "easy", seed: int = 0):
        self.catalog = _catalog()
        if task not in self.catalog["levels"]:
            raise ValueError(f"Unknown task {task!r}; choose from {sorted(self.catalog['levels'])}")
        self.task = task
        self.spec = self.catalog["levels"][task]
        self._seed = seed
        self._done = True
        self.reset(seed=seed)

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        if seed is not None:
            self._seed = seed
        self._generate_map(self._seed)
        self.position = self.start
        self.carrying = False
        self.battery = self.spec["battery"]
        self.steps = 0
        self.picked_up = False
        self.delivered = False
        self.terminal_reason = None
        self._done = False
        return self._observation()

    def _generate_map(self, seed: int) -> None:
        size = self.spec["size"]
        probability = self.spec["wall_probability"]
        hazard_cycle: list[tuple[int, int]] = []
        if self.spec["moving_hazard"]:
            row = size // 2
            lane = [(row, col) for col in range(1, size - 1)]
            hazard_cycle = lane + lane[-2:0:-1]
        protected = set(hazard_cycle)

        # Retry only generation, never the agent episode. This guarantees that
        # required tasks have a valid route and the stretch has a reachable parcel.
        for attempt in range(1000):
            rng = random.Random((seed, self.task, attempt).__repr__())
            walls = {
                (row, col)
                for row in range(size)
                for col in range(size)
                if (row, col) not in protected and rng.random() < probability
            }
            available = [
                (row, col)
                for row in range(size)
                for col in range(size)
                if (row, col) not in walls and (row, col) not in protected
            ]
            start, parcel, delivery = rng.sample(available, 3)
            first_leg = _distance(start, parcel, size, walls)
            second_leg = _distance(parcel, delivery, size, walls)
            if first_leg is None or second_leg is None:
                continue
            if self.task == "stretch" and first_leg > self.spec["battery"]:
                continue
            if self.task != "stretch" and first_leg + second_leg + 1 > self.spec["battery"]:
                continue
            if self.spec["moving_hazard"] and not self._has_safe_route(
                start, parcel, delivery, size, walls, hazard_cycle, self.spec["battery"]
            ):
                continue
            self.size = size
            self.walls = walls
            self.start = start
            self.parcel = parcel
            self.delivery = delivery
            self.hazard_cycle = hazard_cycle
            return
        raise RuntimeError(f"Could not generate a feasible {self.task} map for seed {seed}")

    @staticmethod
    def _has_safe_route(start: tuple[int, int], parcel: tuple[int, int],
                        delivery: tuple[int, int], size: int,
                        walls: set[tuple[int, int]], hazard_cycle: list[tuple[int, int]],
                        battery: int) -> bool:
        queue = deque([(start, False, 0, battery)])
        seen = {(start, False, 0, battery)}
        while queue:
            pos, carrying, phase, remaining = queue.popleft()
            if remaining <= 0:
                continue
            for _, nxt in _neighbors(pos, size, walls):
                next_phase = (phase + 1) % len(hazard_cycle)
                if nxt == hazard_cycle[next_phase]:
                    continue
                next_carrying = carrying or nxt == parcel
                if next_carrying and nxt == delivery:
                    return True
                state = (nxt, next_carrying, next_phase, remaining - 1)
                if state not in seen:
                    seen.add(state)
                    queue.append(state)
        return False

    def _observation(self) -> dict[str, Any]:
        hazard = self.hazard_cycle[self.steps % len(self.hazard_cycle)] if self.hazard_cycle else None
        return {
            "task": self.task,
            "size": self.size,
            "walls": [list(pos) for pos in sorted(self.walls)],
            "position": list(self.position),
            "parcel": list(self.parcel),
            "delivery": list(self.delivery),
            "carrying": self.carrying,
            "battery": self.battery,
            "battery_capacity": self.spec["battery"],
            "steps": self.steps,
            "max_steps": self.spec["max_steps"],
            "hazard": list(hazard) if hazard is not None else None,
            "hazard_cycle": [list(pos) for pos in self.hazard_cycle],
            "hazard_phase": self.steps % len(self.hazard_cycle) if self.hazard_cycle else 0,
        }

    def step(self, action: str):
        if self._done:
            raise RuntimeError("Episode is finished; call reset() before step()")
        if action not in ACTIONS:
            raise ValueError(f"Unknown action {action!r}; choose from {ACTIONS}")

        dr, dc = DELTAS[action]
        candidate = self.position[0] + dr, self.position[1] + dc
        legal = (
            0 <= candidate[0] < self.size
            and 0 <= candidate[1] < self.size
            and candidate not in self.walls
        )
        if legal:
            self.position = candidate

        self.steps += 1
        self.battery -= 1
        reward = -0.01 if legal else -0.05
        terminated = False
        truncated = False

        hazard = self.hazard_cycle[self.steps % len(self.hazard_cycle)] if self.hazard_cycle else None
        if hazard is not None and self.position == hazard:
            reward -= 1.0
            terminated = True
            self.terminal_reason = "hazard_collision"
        elif not self.carrying and self.position == self.parcel:
            self.carrying = True
            self.picked_up = True
            reward += 0.05

        if not terminated and self.carrying and self.position == self.delivery:
            self.delivered = True
            reward += 1.0
            terminated = True
            self.terminal_reason = "delivered"
        elif not terminated and self.battery <= 0:
            reward -= 0.5
            terminated = True
            self.terminal_reason = "battery_depleted"
        elif not terminated and self.steps >= self.spec["max_steps"]:
            truncated = True
            self.terminal_reason = "step_limit"

        self._done = terminated or truncated
        info = {
            "is_success": self.delivered,
            "picked_up": self.picked_up,
            "terminal_reason": self.terminal_reason,
            "steps": self.steps,
        }
        return self._observation(), reward, terminated, truncated, info
