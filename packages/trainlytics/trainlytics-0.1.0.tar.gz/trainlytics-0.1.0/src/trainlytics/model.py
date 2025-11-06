# src/trainlytics/model.py
def detect_plateau(df):
    """Detecta se o volume está estagnado nas últimas semanas."""
    recent = df.tail(3)['volume']
    return recent.std() < 0.1 * recent.mean()
