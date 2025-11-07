import pandas as pd
from py4pmapp import limpiar_nulos, eliminar_duplicados, convertir_fechas, normalizar_columna
import py4pmapp.csvhelper as csv
import py4pmapp.runner as rnr
from py4pmapp.log import LogDict as log
import py4pmapp.utils as utils
from tqdm import tqdm
import zipfile


def test_limpieza():
    df = pd.DataFrame({"a": [1, None, 3], "b": [4, 5, None]})
    assert limpiar_nulos(df).shape[0] == 1

def test_duplicados():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    assert eliminar_duplicados(df).shape[0] == 2

def test_fechas():
    df = pd.DataFrame({"fecha": ["2025-01-01", "invalid"]})
    df2 = convertir_fechas(df, "fecha")
    assert pd.isna(df2.loc[1, "fecha"])

def test_normalizar():
    df = pd.DataFrame({"val": [0, 5, 10]})
    df2 = normalizar_columna(df, "val")
    assert df2["val"].iloc[-1] == 1.0



def complex_test():
    datafile = r"D:\Drives\OneDrive - UPV\DatosPalia\Hospital General\urgencias 2023\Urgencias2\UrgDeimos2019.csv"
    salida = r"D:\Drives\OneDrive - UPV\DatosPalia\Hospital General\urgencias 2023\Urgencias2\salida.ecsv"
    zipSalida= r"D:\Drives\OneDrive - UPV\DatosPalia\Hospital General\urgencias 2023\Urgencias2\baseexample.rnr.zip"

    rnr.list_zip_info(zipSalida)
    df = csv.LoadCSV(datafile, sep=";")\
        .pipe(csv.TrimAllSpaces)\
        .pipe(csv.RejectRepeatedRows)\
        .pipe(csv.CastColumnToType, "Medico/Equipo", str)\
        .pipe(csv.CastColumntoInt, "ano")\
        .pipe(csv.CastColumntoDateTime, "entrada_fecha")
    df = csv.RejectRowsbyNulls(df, "entrada_fecha")
    df = csv.RejectRowsbyNulls(df, "numero")
    df = csv.RejectRowsbyNulls(df,"triaje_nivel")
    #csv.PrintVariablePosibilities(df, "Medico/Equipo")
    

    df1 = csv.FilterDataFramebyCondition(df, lambda d: d["Medico/Equipo"].str.startswith("MEDICO 1")) 
    df2 = csv.FilterDataFramebyCondition(df, lambda d: d["Medico/Equipo"].str.startswith("MEDICO 2")) 
    #df1.info()
    #df2.info()
    l = log()

    csv.add_events_from_dataframe(l, df, trace_id_col="numero",
            trace_attr_map={"Medico/Equipo": "medico", "triaje_nivel": "triaje", "ano": "year"},
            event_name_fixed="Entrada",
            start_col="entrada_fecha",
            event_attr_map=utils.to_map(["triaje_nivel"]),
            tolerance="1m",)

    #for i in tqdm(df.iterrows(),total=len(df), desc="Añadiendo eventos"):
    #    index, row = i
    #    l.add_trace(row["numero"],medico=row["Medico/Equipo"],triaje=row["triaje_nivel"],year=row["ano"])
    #    l.add_event(row["numero"],"Entrada",start=row["entrada_fecha"],_tolerance="1m")

    
    #e = l.to_ecsv()
    l.to_jsonl(r"D:\Drives\OneDrive - UPV\DatosPalia\Hospital General\urgencias 2023\Urgencias2\salida.jsonl")
    #print(e.head(100))
    #e.to_csv(zipSalida, sep=";", index=False)

    #csv.add_csv_to_zip(zipSalida, "Resources/salida.ecsv", e)
    
  
    rnr.list_zip_info(zipSalida)
    #l.add_events_from_dataframe(df,"Entrada","numero","entrada_fecha",attr_cols=["Medico/Equipo","triaje_nivel","ano"])
    #e = l.to_ecsv()
    pass
    

def TestEPOC():
    f0 = r"D:\Drives\OneDrive - UPV\DatosPalia\MINEGUIDE\bronquitis\EPOC\URGENCIAS CIE-10.csv"
    f1 = r"D:\Drives\OneDrive - UPV\DatosPalia\MINEGUIDE\bronquitis\EPOC\URGENCIAS-INFORMES.csv"
    f2 = r"D:\Drives\OneDrive - UPV\DatosPalia\MINEGUIDE\bronquitis\EPOC\URGENCIAS-LABORATORIO.csv"
    f3 = r"D:\Drives\OneDrive - UPV\DatosPalia\MINEGUIDE\bronquitis\EPOC\URGENCIAS-TRIAJE.csv"

    df0 = csv.LoadCSV(f0, sep=",")
    l = log()

    ## LLEGADA DE URGENCIAS
    df0 = csv.CastColumntoDateTime(df0, "FENTRADA")
    df0 = csv.CastColumntoDateTime(df0, "FALTA")
    df0 = csv.CastColumnToType(df0, "NHC", str)
    csv.add_events_from_dataframe(l, df0, trace_id_col="NHC",
            trace_attr_map={},
            #event_name_fixed="Urgencias",
            activity_name_col="SERVICIO",
            start_col="FENTRADA",
            end_col="FALTA",
            event_attr_map={"SERVICIO":"Servicio","CIE_Codigo":"CIE","CIE_Descripcion":"CIE_desc","CIE_Orden":"CIE_Orden"},
            tolerance="1m",)
    

    #INFORMES
    df1 = csv.LoadCSV(f1, sep=",")
    df1.info()
    df1 = csv.CastColumnToType(df1, "nhc", str)

    #LABORATORIO
    df2 = csv.LoadCSV(f2, sep=",")
    df2.info()
    df2 = csv.CastColumnToType(df2, "nhc", str)\
        .pipe(csv.CastColumntoNumeric,"RES_LIR")\
        .pipe(csv.RejectRowsbyNulls, "RES_LIR")\
    

    print(df2)
    

    l.to_jsonl(r"D:\Drives\OneDrive - UPV\DatosPalia\MINEGUIDE\bronquitis\EPOC\epoc_urgencias.jsonl")



TestEPOC()