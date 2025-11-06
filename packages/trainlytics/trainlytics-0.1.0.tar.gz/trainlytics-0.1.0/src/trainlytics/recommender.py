# src/trainlytics/recommender.py
def suggest_progression(df):
    """Sugere aumento de carga baseado no volume atual."""
    df['suggested_weight'] = df['weight'] * 1.05
    return df[['exercise', 'weight', 'suggested_weight']]
