import pandas as pd
import inspect

class PipeContext:
    def __init__(self, **kwargs):
        self.data = dict(**kwargs)
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def pipe(self, func, *args, **kwargs):
        """
        Aplica una función al contexto y devuelve el contexto actualizado.
        - Si la función opera sobre DataFrame, pasa ctx["df"]
        - Si la función espera Context, pasa self
        """
        first_param = list(inspect.signature(func).parameters.values())[0].name

        # Si la función tiene un primer parámetro llamado 'df', le pasamos ctx["df"]
        if first_param in ["df", "dataframe"] and "df" in self.data:
            result = func(self.data["df"], *args, **kwargs)
            # Si devuelve un DataFrame, lo guardamos en ctx["df"]
            if isinstance(result, pd.DataFrame):
                self.data["df"] = result
                return self
            else:
                # si devuelve otra cosa, lo guardamos en "result"
                self.data["result"] = result
                return self
        else:
            # Función que espera el contexto completo
            result = func(self, *args, **kwargs)
            if isinstance(result, PipeContext):
                return result
            else:
                self.data["result"] = result
                return self
    
    def __or__(self, func):
        """
        Permite encadenar funciones usando el operador |
        """
        return self.pipe(func)
    
    def __repr__(self):
        return repr(self.data)
