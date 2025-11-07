import pandas as pd

def limpiar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina filas con valores nulos."""
    return df.dropna()

def eliminar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina filas duplicadas."""
    return df.drop_duplicates()
