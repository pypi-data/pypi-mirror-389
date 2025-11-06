import unittest
from trainlytics import ingest

class TestIngest(unittest.TestCase):
    def test_load_workout_csv(self):
        df = ingest.load_workout_csv('data/sample_workout_log.csv')
        self.assertFalse(df.empty)

if __name__ == '__main__':
    unittest.main()
