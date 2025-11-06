import unittest
from trainlytics import features
import pandas as pd

class TestFeatures(unittest.TestCase):
    def test_compute_metrics(self):
        df = pd.DataFrame({'sets': [3], 'reps': [10], 'weight': [80]})
        df_feat = features.compute_metrics(df)
        self.assertIn('volume', df_feat.columns)

if __name__ == '__main__':
    unittest.main()
