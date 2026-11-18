"""Small baseline agents used for the smoke evaluation."""

from __future__ import annotations

import random
from collections import deque
from typing import Any

from .env import ACTIONS, DELTAS, GridCourierEnv


class RandomAgent:
    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def act(self, observation: dict[str, Any]) -> str:
        return self.rng.choice(ACTIONS)


class ShortestPathAgent:
    """Plan in the fully observed map using BFS over position and hazard phase."""

    def act(self, observation: dict[str, Any]) -> str:
        walls = {tuple(cell) for cell in observation["walls"]}
        size = observation["size"]
        hazard_cycle = [tuple(cell) for cell in observation["hazard_cycle"]]
        phase = observation["hazard_phase"]
        position = tuple(observation["position"])
        parcel = tuple(observation["parcel"])
        delivery = tuple(observation["delivery"])
        carrying = observation["carrying"]
        battery = observation["battery"]

        path = self._search(position, carrying, phase, battery, size, walls,
                            parcel, delivery, hazard_cycle, target="delivery")
        if path:
            return path[0]
        if not carrying:
            path = self._search(position, False, phase, battery, size, walls,
                                parcel, delivery, hazard_cycle, target="parcel")
            if path:
                return path[0]
        # A finite fallback keeps the interface valid when the remaining
        # battery cannot reach another objective.
        return "north"

    @staticmethod
    def _search(start: tuple[int, int], carrying: bool, phase: int, battery: int,
                size: int, walls: set[tuple[int, int]], parcel: tuple[int, int],
                delivery: tuple[int, int], hazard_cycle: list[tuple[int, int]],
                target: str) -> list[str] | None:
        queue = deque([(start, carrying, phase, battery, [])])
        seen = {(start, carrying, phase, battery)}
        while queue:
            pos, has_parcel, current_phase, remaining, path = queue.popleft()
            if remaining <= 0:
                continue
            for action in ACTIONS:
                dr, dc = DELTAS[action]
                nxt = pos[0] + dr, pos[1] + dc
                if not (0 <= nxt[0] < size and 0 <= nxt[1] < size) or nxt in walls:
                    continue
                next_phase = (current_phase + 1) % len(hazard_cycle) if hazard_cycle else 0
                if hazard_cycle and nxt == hazard_cycle[next_phase]:
                    continue
                next_carrying = has_parcel or nxt == parcel
                next_path = path + [action]
                if target == "parcel" and nxt == parcel:
                    return next_path
                if target == "delivery" and next_carrying and nxt == delivery:
                    return next_path
                state = (nxt, next_carrying, next_phase, remaining - 1)
                if state not in seen:
                    seen.add(state)
                    queue.append((*state, next_path))
        return None


class MemorizedAgent:
    """Replays the action trace for the public default easy map."""

    def __init__(self):
        env = GridCourierEnv("easy", seed=0)
        observation = env.reset(seed=0)
        planner = ShortestPathAgent()
        actions: list[str] = []
        for _ in range(env.spec["max_steps"]):
            action = planner.act(observation)
            actions.append(action)
            observation, _, terminated, truncated, _ = env.step(action)
            if terminated or truncated:
                break
        self.actions = actions
        self.index = 0

    def act(self, observation: dict[str, Any]) -> str:
        del observation
        if self.index < len(self.actions):
            action = self.actions[self.index]
            self.index += 1
            return action
        return "north"


def make_agent(name: str, seed: int = 0):
    if name == "planner":
        return ShortestPathAgent()
    if name == "random":
        return RandomAgent(seed)
    if name == "memorized":
        return MemorizedAgent()
    raise ValueError(f"Unknown agent {name!r}; choose planner, random, or memorized")
