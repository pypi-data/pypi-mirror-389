import py4pmapp.csvhelper as csv
import py4pmapp.runner as rnr
from py4pmapp.log import LogDict as log
import py4pmapp.utils as utils
import pandas as pd
from tqdm import tqdm
from typing import Callable

def addNamedEvents(l:log, df:pd.DataFrame, trace_id_col:str, 
                   activity_name:str,start_col:str, end_col:str=None,
                   trace_attr_map:dict=None, event_attr_map:dict=None, show_progress:bool=True, 
                   condition:Callable[[pd.DataFrame], pd.Series]=None, dynamic_activity_name:Callable[[pd.DataFrame], pd.Series]=None):
    return csv.add_events_from_dataframe(l, df, trace_id_col=trace_id_col,event_name_fixed=activity_name,
                                  start_col=start_col,end_col=end_col,
                                  trace_attr_map=trace_attr_map, event_attr_map=event_attr_map, show_progress=show_progress, condition=condition, dynamic_activity_name=dynamic_activity_name)

def addEvents(l:log, df:pd.DataFrame, trace_id_col:str, 
                   start_col:str, activity_name_col:str=None, fixedname:str=None, end_col:str=None,
                   trace_attr_map:dict=None, event_attr_map:dict=None, show_progress:bool=True, 
                   condition:Callable[[pd.DataFrame], pd.Series]=None, dynamic_activity_name:Callable[[pd.DataFrame], pd.Series]=None):
    return csv.add_events_from_dataframe(l, df, trace_id_col=trace_id_col, activity_name_col=activity_name_col, event_name_fixed=fixedname,
                                  start_col=start_col,end_col=end_col,
                                  trace_attr_map=trace_attr_map, event_attr_map=event_attr_map, show_progress=show_progress, condition=condition, dynamic_activity_name=dynamic_activity_name)