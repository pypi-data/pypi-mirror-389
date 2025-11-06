# src/trainlytics/ingest.py
import pandas as pd

def load_workout_log(filepath):
    """Carrega o CSV com os dados de treino."""
    return pd.read_csv(filepath)
