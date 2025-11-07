import pandas as pd

class ECSVLog:
    """
    Clase para manejar logs en formato ECSV (Event CSV unificado).
    Estructura esperada:
      ID | EID | START | END | CODE | VALUE | TYPE
    """

    def __init__(self, df: pd.DataFrame):
        required = ["ID", "EID", "START", "END", "CODE", "VALUE", "TYPE"]
        if not all(col in df.columns for col in required):
            raise ValueError(f"El DataFrame debe contener las columnas: {required}")
        self.df = df.copy()

    # ----------------------------------------------------------
    # 🔹 Lectura / escritura
    # ----------------------------------------------------------

    @classmethod
    def from_csv(cls, path: str):
        df = pd.read_csv(path)
        return cls(df)

    def to_csv(self, path: str, index=False):
        self.df.to_csv(path, index=index)

    # ----------------------------------------------------------
    # 🔹 Extracción por nivel
    # ----------------------------------------------------------

    def get_log_attributes(self) -> pd.DataFrame:
        """Filtra filas de nivel log (sin ID, sin EID, sin START/END)"""
        mask = self.df["ID"].isna() & self.df["EID"].isna()
        return self.df[mask][["CODE", "VALUE", "TYPE"]]

    def get_trace_attributes(self, trace_id=None) -> pd.DataFrame:
        """Filtra filas de nivel traza (con ID pero sin EID)"""
        mask = self.df["ID"].notna() & self.df["EID"].isna()
        if trace_id:
            mask &= self.df["ID"] == trace_id
        return self.df[mask][["ID", "CODE", "VALUE", "TYPE"]]

    def get_event_attributes(self, trace_id=None, event_id=None) -> pd.DataFrame:
        """Filtra filas de nivel evento"""
        mask = self.df["EID"].notna()
        if trace_id:
            mask &= self.df["ID"] == trace_id
        if event_id:
            mask &= self.df["EID"] == event_id
        return self.df[mask][["ID", "EID", "START", "END", "CODE", "VALUE", "TYPE"]]

    # ----------------------------------------------------------
    # 🔹 Transformaciones
    # ----------------------------------------------------------

    def to_event_table(self) -> pd.DataFrame:
        """
        Convierte los eventos (EID) en una tabla tabular con columnas CODE->VALUE.
        Similar a un pivot, útil para análisis rápido.
        """
        df_events = self.get_event_attributes()
        return df_events.pivot_table(
            index=["ID", "EID", "START", "END"],
            columns="CODE",
            values="VALUE",
            aggfunc="first"
        ).reset_index()

    def __repr__(self):
        nlog = len(self.get_log_attributes())
        ntrace = len(self.get_trace_attributes())
        nevent = len(self.get_event_attributes())
        return f"<ECSVLog: {nlog} log attrs, {ntrace} trace attrs, {nevent} event rows>"
