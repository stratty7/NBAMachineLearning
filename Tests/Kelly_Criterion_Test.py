import unittest
from src.Utils import Kelly_Criterion as kc


class TestKellyCriterion(unittest.TestCase):

    def test_calculate_kelly_criterion_1(self):
        result = kc.calculate_kelly_criterion(1.91, .6)
        self.assertEqual(result, 16.04)

    def test_calculate_kelly_criterion_7(self):
        result = kc.calculate_kelly_criterion(110, .6)
        self.assertEqual(result, 16.04)

    def test_calculate_kelly_criterion_2(self):
        result = kc.calculate_kelly_criterion(1.91, .4)
        self.assertEqual(result, 0)

    def test_calculate_kelly_criterion_3(self):
        result = kc.calculate_kelly_criterion(5, .35)
        self.assertEqual(result, 18.75)

    def test_calculate_kelly_criterion_4(self):
        result = kc.calculate_kelly_criterion(1.2, .85)
        self.assertEqual(result, 10)

    def test_calculate_kelly_criterion_5(self):
        result = kc.calculate_kelly_criterion(2, .99)
        self.assertEqual(result, 98)
