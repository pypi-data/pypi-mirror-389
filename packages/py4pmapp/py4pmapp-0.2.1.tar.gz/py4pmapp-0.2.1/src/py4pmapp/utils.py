def to_map(cols):
    """
    Convierte un array/lista en un diccionario {col: col}.

    Parámetros:
    -----------
    cols : list, tuple o array-like
        Lista de nombres de columnas.

    Devuelve:
    ---------
    dict
        Diccionario {col: col} para usar como map.
    """
    if cols is None:
        return None
    if isinstance(cols, (list, tuple)):
        return {col: col for col in cols}
    if isinstance(cols, dict):
        return cols  # ya es un map
    raise ValueError("cols debe ser list, tuple, dict o None")