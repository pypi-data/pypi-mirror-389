import zipfile, io
from pathlib import Path
import os

def zip_writeallbytes(zip_path, internal_path, data_bytes):
    """
    Añade o reemplaza una entrada dentro de un ZIP existente (normal),
    sin borrar ni empaquetar el contenido anterior.
    data_bytes: bytes a escribir en la entrada.
    """
    # Si no existe el ZIP, se crea
    mode = "a" if Path(zip_path).exists() else "w"
    
    if (zip_exists_entry(zip_path, internal_path)):
        zip_delete_entry(zip_path, internal_path)

    # Abrir en modo append (NO sobrescribe, NO reempaqueta)
    with zipfile.ZipFile(zip_path, mode=mode, compression=zipfile.ZIP_DEFLATED) as zf:
        # Sobrescribe o crea solo la entrada indicada
        zf.writestr(internal_path, data_bytes)

def zip_delete_entry(zip_path, internal_path):
    """
    Elimina una entrada dentro de un ZIP existente.
    Crea un ZIP temporal sin la entrada y reemplaza el original.
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"El ZIP {zip_path} no existe")

    temp_path = zip_path.with_suffix(".tmp.zip")
    with zipfile.ZipFile(zip_path, "r") as zf_in, \
        zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf_out:
        for info in zf_in.infolist():
            if info.filename == internal_path:
                continue
            zf_out.writestr(info, zf_in.read(info.filename))
    # Reemplazamos el ZIP original con el nuevo
    os.replace(temp_path, zip_path)

def zip_exists_entry(zip_path, internal_path) -> bool:
    """
    Comprueba si una entrada existe dentro de un ZIP.
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        return False

    with zipfile.ZipFile(zip_path, "r") as zf:
        return internal_path in zf.namelist()


def zip_writefile(zip_path: str, internal_path: str, file_path: str):
    """
    Añade un archivo existente dentro de un ZIP.
    
    zip_path: ruta del ZIP a crear o modificar.
    internal_path: ruta dentro del ZIP (puede incluir carpetas, p. ej. "Resources/file.bin").
    file_path: ruta al archivo que quieres copiar dentro del ZIP.
    """
    zip_path = Path(zip_path)
    file_path = Path(file_path)

    # Leer bytes del archivo a copiar
    data_bytes = file_path.read_bytes()

    mode = "a" if zip_path.exists() else "w"
    with zipfile.ZipFile(zip_path, mode=mode, compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(internal_path, data_bytes)