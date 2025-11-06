import unittest
from trainlytics import model
import pandas as pd

class TestModel(unittest.TestCase):
    def test_detect_plateau(self):
        df = pd.DataFrame({'sets': [3], 'reps': [10], 'weight': [80]})
        result = model.detect_plateau(df)
        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
