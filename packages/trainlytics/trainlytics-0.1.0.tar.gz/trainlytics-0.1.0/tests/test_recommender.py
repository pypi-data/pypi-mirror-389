import unittest
from trainlytics import recommender
import pandas as pd

class TestRecommender(unittest.TestCase):
    def test_suggest_progression(self):
        df = pd.DataFrame({'sets': [3], 'reps': [10], 'weight': [80]})
        result = recommender.suggest_progression(df)
        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
