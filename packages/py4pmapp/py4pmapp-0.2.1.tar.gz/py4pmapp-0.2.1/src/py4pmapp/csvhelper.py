import pandas as pd
import chardet
from .contextpipeline import * 
from tqdm import tqdm
from .filehelper import * 
from typing import Union, List, Any, Tuple, Dict, Optional, Callable



def detect_encoding(filepath, nbytes=10000):
    with open(filepath, "rb") as f:
        rawdata = f.read(nbytes)
    return chardet.detect(rawdata)['encoding']

def LoadCSV(filepath: str, sep =",") -> pd.DataFrame:
    """Carga un archivo CSV en un DataFrame de pandas."""
    enc = detect_encoding(filepath)   
    print(f"Detected encoding: {enc}")
    return pd.read_csv(filepath, encoding=enc, sep=sep, low_memory=False) 

def RejectRepeatedRows(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina filas duplicadas de un DataFrame."""
    return df.drop_duplicates()

def RejectRepeatedRowsbycolumns(
    df: pd.DataFrame,
    columns: Union[str, List[str]]
) -> Tuple[pd.DataFrame, List[dict]]:
    """
    Elimina filas duplicadas basadas en una o varias columnas,
    conservando la primera aparición.
    
    Devuelve:
        (DataFrame sin duplicados, lista de reportes con las filas eliminadas)
    """
    if isinstance(columns, str):
        columns = [columns]  # permite pasar una sola columna o lista

    # Identificar duplicados (excepto la primera aparición)
    duplicated_mask = df.duplicated(subset=columns, keep="first")

    # Generar reporte
    report = []
    for idx, row in df[duplicated_mask].iterrows():
        duplicate_values = {col: row[col] for col in columns}
        report.append({
            "code": "RepeatedRow",
            "line": int(idx),
            "columns": columns,
            "values": duplicate_values
        })

    # Eliminar duplicados y resetear índice
    filtered_df = df.drop_duplicates(subset=columns, keep="first").reset_index(drop=True)

    return filtered_df, report

def RepeatedRowsReportbycolumns(df: pd.DataFrame, columns: Union[str, List[str]]) -> List[dict]:
    """
    Genera un reporte de filas repetidas basado en una o varias columnas.
    Devuelve una lista de diccionarios con el código 'RepeatedRow' y el número de línea (índice original).
    """
    if isinstance(columns, str):
        columns = [columns]  # permite pasar una sola columna o lista

    # Detectar duplicados (manteniendo la primera aparición)
    duplicated_mask = df.duplicated(subset=columns, keep="first")

    # Obtener índices de filas repetidas
    repeated_indices = df[duplicated_mask].index

    # Crear lista de reportes
    report = [{"code": "RepeatedRow", "line": int(idx)} for idx in repeated_indices]

    return report

def RejectAllExceptValues(df: pd.DataFrame, column: str, values: list) -> pd.DataFrame:
    """Mantiene solo las filas donde la columna especificada tiene ciertos valores."""
    return df[df[column].isin(values)]

def MergeCSVs(df1: pd.DataFrame, df2: pd.DataFrame, on: str, how: str ="left") -> pd.DataFrame:
    """Fusiona dos DataFrames en función de una columna común."""
    """how: inner (solo los que estan en los dos), outer (todos poniendo NaN donde no se Sabe), left (todas las de df1), right(todas las de df2)"""
    return pd.merge(df1, df2, on=on, how=how)


def ConcatCSVs(dfs: list[pd.DataFrame], axis: int = 0, ignore_index: bool = True) -> pd.DataFrame:
    """
    Concatena varios DataFrames en uno solo.

    Args:
        dfs: lista de DataFrames a concatenar
        axis: 0 para filas (default), 1 para columnas
        ignore_index: True para resetear el índice
6
    Returns:
        DataFrame concatenado
    """
    return pd.concat(dfs, axis=axis, ignore_index=ignore_index)

def RejectRowsbyNulls(
    df: pd.DataFrame, 
    columns: Union[str, List[str]]
) -> Tuple[pd.DataFrame, List[dict]]:
    """
    Elimina filas donde una o varias columnas tienen valores nulos.
    Devuelve el DataFrame filtrado y un reporte de las filas eliminadas.
    
    Retorna:
        (DataFrame sin nulos, lista de reportes con las filas eliminadas)
    """
    if isinstance(columns, str):
        columns = [columns]  # permite pasar una sola columna o lista

    # Máscara de filas con valores nulos en las columnas dadas
    null_mask = df[columns].isna().any(axis=1)

    # Generar el reporte
    report = []
    for idx, row in df[null_mask].iterrows():
        null_cols = [col for col in columns if pd.isna(row[col])]
        report.append({
            "code": "NullValue",
            "line": int(idx),
            "columns": null_cols
        })

    # Filtrar el DataFrame (mantener solo las filas sin nulos)
    filtered_df = df[~null_mask].reset_index(drop=True)

    return filtered_df, report

def RejectRowsbyValues(df: pd.DataFrame, column: str, values: list) -> pd.DataFrame:
    """Elimina filas donde la columna especificada tiene ciertos valores."""
    return df[~df[column].isin(values)]

def RejectRowsbyCondition(df: pd.DataFrame, condition) -> pd.DataFrame:
    """Elimina filas que cumplen una condición dada."""
    return df[~condition(df)]


def RejectRowsbyRegex(df: pd.DataFrame, column: str, pattern: str) -> pd.DataFrame:
    """Elimina filas donde la columna especificada coincide con un patrón regex."""
    return df[~df[column].str.contains(pattern, regex=True, na=False)]

def TrimSpaces(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Elimina espacios en blanco al inicio y al final de los valores en una columna."""
    df[column] = df[column].str.strip()
    return df

def TrimAllSpaces(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina espacios en blanco al inicio y al final de los valores en todas las columnas de tipo string."""
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
    return df


def PrintDateTimeInfo(df: pd.DataFrame, column: str):
    """Muestra información descriptiva sobre una columna de tipo datetime."""
    series = df[column]

    # Asegurarse de que sea tipo datetime
    if not pd.api.types.is_datetime64_any_dtype(series):
        print(f"⚠️ La columna '{column}' no es de tipo datetime")
        return

    print(f"\n📅 Información de la columna '{column}':")
    print("-" * 50)
    print(f"Total de valores: {len(series)}")
    print(f"Valores nulos: {series.isna().sum()}")
    print(f"Valores únicos: {series.nunique(dropna=True)}")

    if series.notna().any():
        print(f"Fecha mínima: {series.min()}")
        print(f"Fecha máxima: {series.max()}")
        print(f"Rango de fechas: {(series.max() - series.min()).days} días")


def PrintNumericInfo(df: pd.DataFrame, column: str):
    """Muestra información descriptiva sobre una columna numérica."""
    series = df[column]

    # Asegurarse de que sea numérica
    if not pd.api.types.is_numeric_dtype(series):
        print(f"⚠️ La columna '{column}' no es numérica")
        return

    print(f"\n🔢 Información de la columna '{column}':")
    print("-" * 50)
    print(f"Total de valores: {len(series)}")
    print(f"Valores nulos: {series.isna().sum()}")
    print(f"Valores únicos: {series.nunique(dropna=True)}")

    if series.notna().any():
        print(f"Valor mínimo: {series.min()}")
        print(f"Valor máximo: {series.max()}")
        print(f"Media: {series.mean()}")
        print(f"Mediana: {series.median()}")
        print(f"Desviación estándar: {series.std()}")
        print(f"Percentiles (25%, 50%, 75%): {series.quantile([0.25, 0.5, 0.75]).to_dict()}")

        print("\nDistribución de frecuencias (top 10 valores):")
        print(series.value_counts(dropna=False).head(10))
    else:
        print("❌ No hay valores numéricos válidos para mostrar información.")

def PrintVariablePosibilities(df: pd.DataFrame, column: str):
    """Imprime las posibles valores únicos de una columna y su frecuencia."""
    print(df[column].value_counts(dropna=False))

def CastColumnToType(df: pd.DataFrame, columns: Union[str, List[str]], dtype: Any) -> pd.DataFrame:
    """Convierte una o varias columnas a un tipo de dato especificado."""
    if isinstance(columns, str):
        columns = [columns]  # permite pasar una sola columna o una lista

    for column in columns:
        if dtype in ["datetime", pd.Timestamp]:
            df[column] = pd.to_datetime(df[column], errors="coerce")
        else:
            try:
                df[column] = df[column].astype(dtype)
            except Exception:
                print(f"⚠️ No se pudo convertir la columna '{column}' a {dtype}. Se mantiene sin cambios.")
    return df

def CastColumntoDateTime(df: pd.DataFrame, columns: Union[str, List[str]]) -> pd.DataFrame:
    """Convierte una o varias columnas a tipo datetime."""
    if isinstance(columns, str):
        columns = [columns]  # convierte un solo nombre en lista
    
    for column in columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")
    
    return df



def MergeReports(*reports: Union[List[dict], None]) -> List[dict]:
    """
    Combina dos o más reportes de errores (listas de diccionarios) en uno solo.
    
    Ignora valores None o entradas no válidas.
    
    Ejemplo:
        MergeReports(report1, report2, report3)
    """
    merged = []
    for r in reports:
        if isinstance(r, list):
            merged.extend(r)
    return merged

def CastAndReportDateTime(
    df: pd.DataFrame,
    columns: Union[str, List[str]],
    formats: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[dict]]:
    """
    Convierte una o varias columnas a tipo datetime (con fecha y hora) usando uno o varios formatos.
    Genera un reporte de los valores que no pudieron convertirse.

    Parámetros:
        df       : DataFrame de entrada.
        columns  : Nombre o lista de columnas a convertir.
        formats  : Lista de formatos datetime aceptados (ej: ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"]).
                   Si es None, se usa el parseo automático de pandas.

    Retorna:
        (DataFrame casteado, lista de errores)
    """
    if isinstance(columns, str):
        columns = [columns]

    report = []

    for column in columns:
        original = df[column].copy()

        if formats is None:
            # Conversión automática (detecta fecha y hora)
            converted = pd.to_datetime(original, errors="coerce", infer_datetime_format=True)
        else:
            # Intentar parsear con múltiples formatos
            converted = pd.Series(pd.NaT, index=df.index)
            for fmt in formats:
                # Solo intenta convertir los que aún son NaT
                mask = converted.isna() & original.notna()
                if mask.any():
                    try:
                        converted.loc[mask] = pd.to_datetime(
                            original.loc[mask],
                            format=fmt,
                            errors="coerce"
                        )
                    except Exception:
                        pass

        # Detectar conversiones fallidas
        failed_mask = converted.isna() & original.notna()

        for idx, value in df.loc[failed_mask, column].items():
            report.append({
                "code": "UncastableDateTime",
                "column": column,
                "line": int(idx),
                "value": str(value)
            })

        df[column] = converted

    return df, report

def CastAndReportNumeric(
    df: pd.DataFrame,
    columns: Union[str, List[str]]
) -> Tuple[pd.DataFrame, List[dict]]:
    """
    Convierte una o varias columnas a tipo numérico y genera un reporte
    de los valores que no pudieron convertirse.
    
    Retorna:
        (DataFrame casteado, lista de errores)
    """
    if isinstance(columns, str):
        columns = [columns]

    report = []

    for column in columns:
        original = df[column].copy()
        converted = pd.to_numeric(original, errors="coerce")

        failed_mask = converted.isna() & original.notna()

        for idx, value in df.loc[failed_mask, column].items():
            report.append({
                "code": "UncastableNumeric",
                "column": column,
                "line": int(idx),
                "value": str(value)
            })

        df[column] = converted

    return df, report


def CastColumntoInt(df: pd.DataFrame, column: str, allow_na: bool = True) -> pd.DataFrame:
    """Convierte una columna a tipo entero (maneja NaN si allow_na=True)."""
    df[column] = pd.to_numeric(df[column], errors="coerce")
    if allow_na:
        df[column] = df[column].astype("Int64")
    else:
        df[column] = df[column].fillna(0).astype(int)
    return df

def CastColumntoNumeric(df: pd.DataFrame, columns: Union[str, List[str]]) -> pd.DataFrame:
    """Convierte una o varias columnas a tipo numérico."""
    if isinstance(columns, str):
        columns = [columns]  # convierte un solo nombre en lista
    
    for column in columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    
    return df

def FilterDataFramebyCondition(df: pd.DataFrame, condition) -> pd.DataFrame:
    """Filtra un DataFrame según una condición dada."""
    return df[condition(df)]


def IterateRows(df: pd.DataFrame, desc: str ="Iterando filas" ):
    """Generador que itera sobre las filas de un DataFrame."""
    for index, row in df.iterrows():
        yield index, row


def add_events_from_dataframe(
    log,
    df: pd.DataFrame,
    trace_id_col: str,
    trace_attr_map: Optional[dict] = None,
    activity_name_col: Optional[str] = None,
    start_col: Optional[str] = None,
    end_col: Optional[str] = None,
    event_attr_map: Optional[dict] = None,
    event_name_fixed: Optional[str] = None,
    tolerance: Optional[str] = None,
    condition: Optional[Callable[[pd.Series], bool]] = None,
    dynamic_activity_name: Optional[Callable[[pd.Series], str]] = None,
    show_progress: bool = True
) -> pd.DataFrame:
    """
    Añade trazas y eventos desde un DataFrame de manera generalizable,
    con soporte para condición por fila y nombre de evento dinámico.

    Parámetros:
    -----------
    log : LogDict
        Instancia de tu log (debe tener métodos add_trace y add_event).
    df : pd.DataFrame
        DataFrame de origen.
    trace_id_col : str
        Columna que contiene el ID de la traza.
    trace_attr_map : dict, opcional
        Mapa de columnas del df a nombres de atributos de la traza.
    activity_name_col : str, opcional
        Columna del df que contiene el nombre de la actividad del evento.
    event_name_fixed : str, opcional
        Nombre fijo del evento si no se usa activity_name_col.
    dynamic_activity_name : Callable[[pd.Series], str], opcional
        Función que recibe una fila (pd.Series) y devuelve dinámicamente
        el nombre del evento (tiene prioridad sobre las otras opciones).
    start_col : str
        Columna con la fecha/hora de inicio.
    end_col : str, opcional
        Columna con la fecha/hora de fin.
    event_attr_map : dict, opcional
        Mapa de columnas a atributos del evento.
    tolerance : str, opcional
        Tolerancia para add_event.
    condition : Callable[[pd.Series], bool], opcional
        Función que recibe una fila (pd.Series) y devuelve True/False.
        Solo si devuelve True se añade el evento. Si None, siempre se añade.
    show_progress : bool
        Si True, muestra barra de progreso.

    Retorna:
    --------
    El mismo DataFrame original.
    """
    name = activity_name_col if activity_name_col else event_name_fixed
    iterator = tqdm(df.iterrows(), total=len(df), desc=f"Añadiendo eventos {name}") if show_progress else df.iterrows()

    for _, row in iterator:
        # Evaluar la condición (si existe)
        if condition and not condition(row):
            continue  # no añade el evento si la condición no se cumple

        trace_id = row[trace_id_col]

        # --- Añadir o actualizar traza ---
        trace_attrs = {}
        if trace_attr_map:
            for col, attr_name in trace_attr_map.items():
                if col in df.columns and pd.notna(row[col]):
                    trace_attrs[attr_name] = row[col]
        log.add_trace(trace_id, **trace_attrs)

        # --- Determinar nombre del evento ---
        if dynamic_activity_name:
            activity_name = dynamic_activity_name(row)
        elif activity_name_col:
            activity_name = row[activity_name_col]
        else:
            activity_name = event_name_fixed

        if not activity_name or not isinstance(activity_name, str):
            raise ValueError(f"No se pudo determinar el nombre del evento en fila {_}.")

        # --- Atributos del evento ---
        ev_attrs = {}
        if event_attr_map:
            for col, attr_name in event_attr_map.items():
                if col in df.columns and pd.notna(row[col]):
                    ev_attrs[attr_name] = row[col]

        # --- Añadir evento ---
        log.add_event(
            trace_id,
            activity_name,
            start=row[start_col],
            end=row[end_col] if end_col else None,
            _tolerance=tolerance,
            **ev_attrs
        )

    return df


def add_csv_to_zip(zip_path, internal_path, df):
    """
    Añade o reemplaza un CSV dentro de un ZIP existente (normal),
    sin borrar ni empaquetar el contenido anterior.
    """
    # Serializar el DataFrame a memoria
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False,sep=";")
    data = csv_buffer.getvalue().encode("utf-8")
    zip_writeallbytes(zip_path, internal_path, data)

