import pandas as pd
import uuid
from datetime import datetime, timedelta,date
from tqdm import tqdm  # pip install tqdm si no la tienes
import json

class LogDict:
    """
    Versión de Log basada en diccionarios para comparar performance.
    """
    def __init__(self, log_attrs=None):
        self.log_attrs = log_attrs or {}
        self.traces = {}  # {trace_id: {"attrs": {}, "events": {event_id: {"base": {}, "extra": {}}}}}

    # ---------------------------
    # 🔹 Traces
    # ---------------------------
    def add_trace(self, trace_id, **attrs):
        if trace_id in self.traces:
            self.traces[trace_id]["attrs"].update(attrs)
        else:
            self.traces[trace_id] = {"attrs": attrs.copy(), "events": {}}
        return trace_id

    def add_trace_attr(self, trace_id, **attrs):
        if trace_id not in self.traces:
            self.add_trace(trace_id, **attrs)
        self.traces[trace_id]["attrs"].update(attrs)

    # ---------------------------
    # 🔹 Events
    # ---------------------------
    def add_event(self, trace_id, activity_name, start=None, end=None, event_id=None, _tolerance=None, **extra_attrs):
        if trace_id not in self.traces:
            self.add_trace(trace_id)
        event_id = event_id or str(uuid.uuid4())[:8]
        if _tolerance:
            # Buscar eventos existentes con tolerancia
            matched_events = self.find_event(trace_id, activity_name, start, _tolerance)
            if matched_events:
                self.add_event_attr(trace_id, matched_events[0], **extra_attrs)
                return matched_events[0]  # devolver el primero que coincida
        start = start or datetime.now().isoformat()
        end = end or start
        base_attrs = {"ActivityName": activity_name, "start": start, "end": end}
        self.traces[trace_id]["events"][event_id] = {"base": base_attrs, "extra": extra_attrs.copy()}
        return event_id

    def add_event_attr(self, trace_id, event_id, **extra_attrs):
        if trace_id not in self.traces or event_id not in self.traces[trace_id]["events"]:
            raise ValueError(f"Evento '{event_id}' de traza '{trace_id}' no existe")
        self.traces[trace_id]["events"][event_id]["extra"].update(extra_attrs)


    # ----------------------------------------------------------
    # 🔹 Eventos de Encontrar
    # ----------------------------------------------------------

    def find_event_ids(self, trace_id=None, activity_name=None, date=None):
        """
        Devuelve una lista de event_id que coincidan con los criterios.
        - trace_id opcional
        - ActivityName opcional
        - date opcional (YYYY-MM-DD)
        """
        df = self.df_event_base
        mask = pd.Series(True, index=df.index)

        if trace_id is not None:
            mask &= df["trace_id"] == trace_id
        if activity_name is not None:
            mask &= df.get("ActivityName") == activity_name
        if date is not None:
            mask &= df["time:start"].str.startswith(date)
        
        return df.loc[mask, "event_id"].tolist()

    def find_event(self, trace_id, activity_name=None, date=None, tolerance=None):
        """
        Encuentra eventos de una traza según varios criterios.

        Parámetros:
        -----------
        trace_id : str
            ID de la traza a filtrar.
        activity_name : str, opcional
            Nombre de la actividad (ActivityName) a filtrar.
        date : str o datetime, opcional
            Fecha de referencia para filtrar.
        tolerance : str o timedelta, opcional
            Ventana temporal alrededor de date. Ej: '5m', '30s', '1h', '2d'.

        Devuelve:
        ---------
        list[str] : Lista de event_id que cumplen los criterios.
        """
        if trace_id not in self.traces:
            return []

        # Convertir date a datetime si es string
        if date is not None and isinstance(date, str):
            date = datetime.fromisoformat(date)

        # Interpretar tolerancia
        delta = None
        if tolerance:
            if isinstance(tolerance, str):
                unit = tolerance[-1].lower()
                value = int(tolerance[:-1])
                if unit == 's':
                    delta = timedelta(seconds=value)
                elif unit == 'm':
                    delta = timedelta(minutes=value)
                elif unit == 'h':
                    delta = timedelta(hours=value)
                elif unit == 'd':
                    delta = timedelta(days=value)
                else:
                    raise ValueError("Unidad de tolerancia inválida. Usa 's', 'm', 'h' o 'd'.")
            elif isinstance(tolerance, timedelta):
                delta = tolerance
            else:
                raise ValueError("tolerance debe ser str o timedelta")

        matched_events = []

        for eid, ev in self.traces[trace_id]["events"].items():
            # Filtrar por ActivityName
            if activity_name and ev["base"]["ActivityName"] != activity_name:
                continue

            # Filtrar por fecha y tolerancia
            if date and delta:
                ev_start = ev["base"]["start"]
                if isinstance(ev_start, str):
                    ev_start = datetime.fromisoformat(ev_start)
                if abs((ev_start - date)) > delta:
                    continue
            elif date:  # Si hay date pero no tolerance, buscar exacto
                ev_start = ev["base"]["start"]
                if isinstance(ev_start, str):
                    ev_start = datetime.fromisoformat(ev_start)
                if ev_start != date:
                    continue

            matched_events.append(eid)

        return matched_events




    # ---------------------------
    # 🔹 Exportación a ECSV
    # ---------------------------
    def _infer_type(self, val):
        """Infiera tipo de dato ECSV según el valor"""
        if isinstance(val, int):
            return "xs:int"
        elif isinstance(val, float):
            return "xs:double"

        try:
            # Intentar parsear como datetime
            pd.to_datetime(val)
            return "xs:datetime"
        except (ValueError, TypeError):
            pass
        return "xs:string"

    def to_ecsv(self):
        rows = []
        self.log_attrs["_ECSVTraceCount"]=len(self.traces)
        # Log attrs
        for k, v in self.log_attrs.items():
            rows.append({
                "ID": None,
                "EID": None,
                "START": None,
                "END": None,
                "CODE": k,
                "VALUE": v,
                "TYPE": self._infer_type(v)
            })

        # Cada traza
        for trace_id, trace in tqdm(self.traces.items(), desc="Exportando a ECSV", total=len(self.traces)):
            # Metadatos de la traza
            for k, v in trace["attrs"].items():
                rows.append({
                    "ID": trace_id,
                    "EID": None,
                    "START": None,
                    "END": None,
                    "CODE": k,
                    "VALUE": v,
                    "TYPE": self._infer_type(v)
                })
            # Eventos
            for event_id, ev in trace["events"].items():
                start, end = ev["base"]["start"], ev["base"]["end"]
                # Atributos base del evento
                for k, v in ev["base"].items():
                    if k in ("start", "end"): continue
                    rows.append({
                        "ID": trace_id,
                        "EID": event_id,
                        "START": start,
                        "END": end,
                        "CODE": k,
                        "VALUE": v,
                        "TYPE": self._infer_type(v)
                    })
                # Atributos extra del evento
                for k, v in ev["extra"].items():
                    rows.append({
                        "ID": trace_id,
                        "EID": event_id,
                        "START": start,
                        "END": end,
                        "CODE": k,
                        "VALUE": v,
                        "TYPE": self._infer_type(v)
                    })

        return pd.DataFrame(rows, columns=["ID", "EID", "START", "END", "CODE", "VALUE", "TYPE"])

    def to_jsonl(self, filepath):
        """
        Serializa cada traza individualmente a un archivo JSON Lines.
        Cada línea del archivo es un objeto JSON de una sola traza.
        """
        def datetime_handler(obj):
            """Maneja la serialización de objetos datetime a ISO 8601."""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, timedelta):
                return obj.total_seconds()
            raise TypeError(f"Objeto de tipo {type(obj)} no serializable por JSON.")

        with open(filepath, 'w', encoding='utf-8') as f:
            # Puedes incluir los log_attrs globales como el primer objeto del archivo
            # si son necesarios en C# antes de las trazas.
            global_attrs = {"_LogAttrs": self.log_attrs}
            f.write(json.dumps(global_attrs, default=datetime_handler) + '\n')

            # Itera sobre cada traza y escríbela como una nueva línea JSON
            for trace_id, trace_data in self.traces.items():
                trace_object = {
                    "trace_id": str(trace_id),
                    "attrs": trace_data["attrs"],
                    "events": trace_data["events"]
                }
                # dumps() genera el JSON string, y añadimos el salto de línea
                f.write(json.dumps(trace_object, default=datetime_handler) + '\n')


