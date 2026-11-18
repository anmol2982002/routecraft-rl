# RouteCraft: GridCourier

RouteCraft is a small, dependency-free RL environment for route planning in a procedurally generated warehouse. An agent must collect a parcel and deliver it while managing walls, a step budget, and (on the hard task) a moving hazard. The environment is designed to make the transition contract and grading rules easy to inspect.

## Quick start

Requires Python 3.10 or newer. No third-party Python packages are needed.

Run the baseline comparison:

```bash
python -m gridcourier.demo
```

Run the objective grader:

```bash
python -m gridcourier.grade --agent planner --task all --split evaluation
```

Reproduce the anti-gaming demonstrations:

```bash
python -m gridcourier.exploits
```

Run the small contract checks:

```bash
python -m unittest discover -s tests -v
```

## Environment contract

`GridCourierEnv.reset(seed)` returns an observation. `GridCourierEnv.step(action)` returns `(observation, reward, terminated, truncated, info)`. The four string actions are `north`, `east`, `south`, and `west`. Each observation exposes the complete map, courier position, parcel and delivery coordinates, whether the parcel is carried, remaining battery, and the current hazard phase. This is a fully observable task; the map and hazard cycle are not hidden from the policy.

The courier picks up the parcel automatically when it enters that cell. Delivery succeeds only when the courier reaches the delivery cell while carrying the parcel. A move costs a small amount of reward; invalid movement, hazard collision, and battery depletion are penalized. Delivery terminates the episode. The grader uses delivery and pickup milestones from `info`, not the accumulated shaped reward, as its score.

| Task | Map | Added challenge | Objective |
| --- | --- | --- | --- |
| `easy` | 4 x 4, open | None | Deliver within the step budget |
| `medium` | 6 x 6, generated walls | Route planning | Deliver within the step budget |
| `hard` | 7 x 7, generated walls | Moving hazard with observed phase | Deliver without collision |
| `stretch` | 7 x 7, generated walls | Tight battery budget | Full credit for delivery; 0.35 partial credit for pickup |

Map layouts are generated from the seed and the task configuration in [`data/task_catalog.json`](data/task_catalog.json). The dataset is self-made and procedural; it contains no employer or third-party data. Development seeds and a separate evaluation seed split are listed there for reproducibility. Since both the generator and evaluation seeds are public, the split is a demonstration of generalization checks, not a secret benchmark.

## Grading and anti-gaming

The objective evaluator replays a policy on each seed and scores success from the environment's terminal outcome. The three required tasks need a mean objective score of at least 0.90. The optional stretch task uses the same milestone score with a 0.60 threshold. `tests/` contains useful local contract checks, but the grader never imports them, so changing a local assertion cannot change the score.

The exploit script demonstrates two limited attacks: changing a local test to always pass, and replaying a fixed action sequence from the default map. The first can make the local test command green, but it does not affect objective scoring. The second is evaluated on new seeds and must still meet the same threshold. This is not a secure sandbox for arbitrary submitted Python: the demonstration grader accepts named in-repository policies. For untrusted code, the policy runner and scoring harness should run in separate, restricted containers, with read-only evaluator files and fresh server-side evaluation seeds.

## Docker

Build and run the same baseline without installing dependencies:

```bash
docker build -t routecraft-gridcourier .
docker run --rm --read-only routecraft-gridcourier
docker run --rm --read-only routecraft-gridcourier python -m gridcourier.grade --agent planner --task all --split evaluation
```

The image runs as a non-root user. `--read-only` makes the container root filesystem read-only during these runs.

## Results and limits

[`SCOPE.md`](SCOPE.md) describes the task design. [`RESULTS.md`](RESULTS.md) records the baseline runs, exploit attempts, limits, and a proposed training-effectiveness study. The included `ShortestPathAgent` is a model-based planner, not a learned policy. These runs validate the task interface and grader on the sample seeds; they do not show that training on RouteCraft improves a model.

## AI assistance

OpenAI Codex (GPT-6) assisted with implementation, experiment scripting, and documentation. The project is new work for this assignment and is not represented as a pre-existing portfolio project. See [`AI_TOOLS.md`](AI_TOOLS.md) for the tool-use note.
