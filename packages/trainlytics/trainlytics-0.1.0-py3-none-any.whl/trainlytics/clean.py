# src/trainlytics/clean.py
import pandas as pd

def clean_workout_data(df):
    """Remove valores nulos e padroniza colunas."""
    df = df.dropna()
    df.columns = [col.strip().lower() for col in df.columns]
    return df