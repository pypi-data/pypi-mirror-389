# src/trainlytics/features.py
def compute_volume(df):
    """Calcula volume total por exercício."""
    df['volume'] = df['sets'] * df['reps'] * df['weight']
    return df.groupby('exercise')['volume'].sum().reset_index()
