"""Independent objective evaluator for action-only environment policies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from .agents import make_agent
from .env import GridCourierEnv

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "task_catalog.json"


def read_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open(encoding="utf-8") as stream:
        return json.load(stream)


def run_episode(task: str, seed: int, agent_name: str) -> dict[str, Any]:
    env = GridCourierEnv(task, seed=seed)
    observation = env.reset(seed=seed)
    agent = make_agent(agent_name, seed=seed)
    for _ in range(env.spec["max_steps"]):
        action = agent.act(observation)
        observation, _, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
    return info


def objective_score(task: str, info: dict[str, Any], catalog: dict[str, Any] | None = None) -> float:
    catalog = catalog or read_catalog()
    if info["is_success"]:
        return 1.0
    if catalog["levels"][task]["partial_credit"] and info["picked_up"]:
        return catalog["stretch_pickup_credit"]
    return 0.0


def evaluate(task: str, agent_name: str, split: str = "evaluation") -> dict[str, Any]:
    catalog = read_catalog()
    seeds = catalog["seed_splits"][split]
    episodes = [run_episode(task, seed, agent_name) for seed in seeds]
    scores = [objective_score(task, item, catalog) for item in episodes]
    successes = sum(item["is_success"] for item in episodes)
    if catalog["levels"][task]["partial_credit"]:
        threshold = catalog["stretch_passing_threshold"]
    else:
        threshold = catalog["passing_threshold"]
    return {
        "task": task,
        "agent": agent_name,
        "split": split,
        "episodes": len(episodes),
        "successes": successes,
        "pickups": sum(item["picked_up"] for item in episodes),
        "success_rate": successes / len(episodes),
        "mean_objective_score": mean(scores),
        "mean_steps": mean(item["steps"] for item in episodes),
        "threshold": threshold,
        "passed": mean(scores) >= threshold,
    }


def format_row(result: dict[str, Any]) -> str:
    status = "PASS" if result["passed"] else "FAIL"
    return (
        f"{result['task']:<8} deliveries={result['successes']:>2}/{result['episodes']:<2}  "
        f"pickups={result['pickups']:>2}/{result['episodes']:<2}  "
        f"score={result['mean_objective_score']:.2f}  "
        f"mean_steps={result['mean_steps']:.1f}  {status}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=("planner", "random", "memorized"), default="planner")
    parser.add_argument("--task", choices=("all", "easy", "medium", "hard", "stretch"), default="all")
    parser.add_argument("--split", choices=("development", "evaluation"), default="evaluation")
    args = parser.parse_args()
    catalog = read_catalog()
    tasks = list(catalog["levels"]) if args.task == "all" else [args.task]
    results = [evaluate(task, args.agent, args.split) for task in tasks]
    print(f"RouteCraft objective grade | agent={args.agent} | split={args.split}")
    for result in results:
        print(format_row(result))
    print(f"Overall: {'PASS' if all(item['passed'] for item in results) else 'FAIL'}")
    return 0 if all(item["passed"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
