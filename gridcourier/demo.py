"""Compare a random baseline with a map-aware planner on the evaluation split."""

from .grade import evaluate, format_row, read_catalog


def main() -> None:
    catalog = read_catalog()
    print("RouteCraft baseline run (same evaluation seeds for both agents)")
    for task in catalog["levels"]:
        for agent in ("random", "planner"):
            print(format_row(evaluate(task, agent, "evaluation")))


if __name__ == "__main__":
    main()
