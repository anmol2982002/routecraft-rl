# Results note

## Agent runs

The evaluator ran a random legal-action baseline and a shortest-path planner over the same 20 evaluation seeds per task. The planner is map-aware and uses breadth-first search over position, parcel possession, and hazard phase. It is a planning baseline, not an RL-trained policy. Results below come from `python -m gridcourier.demo`.

| Task | Random deliveries / pickups | Planner deliveries / pickups | Planner objective score |
| --- | ---: | ---: | ---: |
| Easy | 3/20 / 9/20 | 20/20 / 20/20 | 1.00 |
| Medium | 2/20 / 9/20 | 20/20 / 20/20 | 1.00 |
| Hard | 1/20 / 3/20 | 20/20 / 20/20 | 1.00 |
| Stretch | 0/20 / 1/20 | 8/20 / 20/20 | 0.61 |

The stretch objective score is 1.00 for delivery, 0.35 for parcel pickup without delivery, and 0.00 otherwise. Its 0.60 pass threshold is intentionally lower because the battery budget makes some evaluation layouts pickup-only. The other tasks score 1.00 only for delivery. Mean planner steps were 5.2 (easy), 9.1 (medium), 11.2 (hard), and 8.9 (stretch); mean random-agent steps were 22.9, 39.5, 32.8, and 10.0 respectively.

The three local contract checks passed. Docker and Podman were unavailable in the workspace, so the Docker image was not built here; the Dockerfile and read-only run commands are included for a Docker-enabled machine.

## Deliberate exploit attempts

1. **Edit the local tests.** The demonstration replaces a local test in a temporary directory with an unconditional passing test. That local test passes, but the random policy still scores 3/20 on the easy evaluation seeds, below the 0.90 threshold. The tests are not an input to the evaluator.
2. **Hardcode the default route.** A policy replays the action trace for the public default easy map. It delivered on 0 of 20 evaluation seeds, below the 0.90 score threshold.

These checks block the two attempted shortcuts in this repository's action-only demonstration. They do not establish security against arbitrary candidate code. The code and seed catalogue are public, and the grader uses trusted in-repository agent implementations. A production setup would run candidate code in an isolated container with no access to the evaluator files, and would generate fresh server-side evaluation seeds.

## What the runs establish

These small seeded runs show that an objective policy evaluator can distinguish a general map-aware planner from a random baseline and a single memorized route. They do not show that an RL algorithm learned, that the task is representative of a real customer codebase, or that performance will transfer to another domain. Twenty episodes per task are useful for a smoke comparison but too few for a strong statistical claim.

## Measuring training value

Train a policy on a fixed development-seed budget, then compare it with the random baseline and planner on held-out seeds from multiple map families. Repeat training with several independent seeds. Report success rate and objective score against environment steps, plus confidence intervals. To test transfer, hold out map-generation rules rather than only random seeds, then evaluate whether training improves task completion without access to the new layouts during training.

## Extension to a customer codebase

For a customer codebase, first define a narrow, reproducible task such as repairing one failing behavior from an issue report. Provide an action interface for proposing a patch, observations that expose relevant files and test feedback, and a grader that runs independent hidden tests in a sandbox. Keep reward tied to behavior that matters to the customer and audit common shortcuts such as editing tests, special-casing visible examples, or weakening checks. Start with synthetic or public repositories and use customer data only after access, licensing, and isolation requirements are explicit.
