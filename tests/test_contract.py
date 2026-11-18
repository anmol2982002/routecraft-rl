import unittest

from gridcourier.env import ACTIONS, GridCourierEnv
from gridcourier.grade import objective_score


class EnvironmentContractTests(unittest.TestCase):
    def test_reset_is_reproducible_and_observation_is_complete(self):
        env = GridCourierEnv("hard", seed=12)
        first = env.reset(seed=12)
        second = env.reset(seed=12)
        self.assertEqual(first, second)
        self.assertIn("walls", first)
        self.assertIn("hazard_phase", first)
        self.assertEqual(set(ACTIONS), {"north", "east", "south", "west"})

    def test_step_uses_five_value_interface(self):
        env = GridCourierEnv("easy", seed=2)
        observation = env.reset(seed=2)
        result = env.step("north")
        self.assertEqual(len(result), 5)
        self.assertIsInstance(result[0], dict)
        self.assertIsInstance(result[1], float)
        self.assertEqual(result[0]["steps"], observation["steps"] + 1)

    def test_grader_gives_pickup_only_partial_credit_on_stretch(self):
        info = {"is_success": False, "picked_up": True}
        self.assertEqual(objective_score("stretch", info), 0.35)
        self.assertEqual(objective_score("easy", info), 0.0)


if __name__ == "__main__":
    unittest.main()
