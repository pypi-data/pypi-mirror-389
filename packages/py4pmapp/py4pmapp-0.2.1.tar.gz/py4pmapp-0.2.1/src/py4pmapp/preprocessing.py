import pandas as pd

def convertir_fechas(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Convierte una columna a tipo datetime."""
    df[columna] = pd.to_datetime(df[columna], errors='coerce')
    return df

def normalizar_columna(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Normaliza los valores de una columna numérica entre 0 y 1."""
    min_val = df[columna].min()
    max_val = df[columna].max()
    df[columna] = (df[columna] - min_val) / (max_val - min_val)
    return df
