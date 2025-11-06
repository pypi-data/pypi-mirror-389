import unittest
from trainlytics import clean
import pandas as pd

class TestClean(unittest.TestCase):
    def test_clean_workout_data(self):
        df = pd.DataFrame({'date': ['2025-11-01'], 'sets': [3], 'reps': [10], 'weight': [80]})
        df_clean = clean.clean_workout_data(df)
        self.assertIn('date', df_clean.columns)

if __name__ == '__main__':
    unittest.main()
