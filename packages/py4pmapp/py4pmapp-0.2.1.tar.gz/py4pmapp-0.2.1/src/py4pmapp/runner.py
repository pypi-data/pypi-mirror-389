import zipfile
from pathlib import Path
import shutil
import zipfile
from io import BytesIO

def list_zip_info(zip_path):
    """Lista las entradas del ZIP con tamaño y muestra si empiezan por la firma PK."""
    zip_path = Path(zip_path)
    if not zip_path.exists():
        print("ZIP no existe:", zip_path)
        return

    with zipfile.ZipFile(zip_path, "r") as zf:
        print(f"Contenido de {zip_path}:")
        for info in zf.infolist():
            name = info.filename
            size = info.file_size
            comp = info.compress_size
            # leer los primeros bytes para inspección
            with zf.open(info, "r") as f:
                header = f.read(8)
            is_embedded_zip = header.startswith(b"PK")
            print(f" - {name:50} size={size:8} comp={comp:8} header={header[:4]!r} embedded_zip={is_embedded_zip}")

def inspect_entry(zip_path, entry_name, nbytes=256):
    """Muestra los primeros nbytes de una entrada concreta (útil para ver si contiene un ZIP)."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        if entry_name not in zf.namelist():
            print("No existe la entrada:", entry_name)
            return
        with zf.open(entry_name, "r") as f:
            data = f.read(nbytes)
    print(f"Primeros {len(data)} bytes de {entry_name}:")
    print(data[:64])
    # Indicar si parece un ZIP
    if data.startswith(b"PK"):
        print("-> Esta entrada parece contener un ZIP (firma PK).")
    if data[:3].isalpha():
        # simplilla heurística para CSV/text
        print("-> Parece texto (csv/tsv).")



def repair_zip_merge_internal_zip(zip_path, repaired_path=None):
    """
    Crea un ZIP 'reparado' donde:
     - copia entradas normales tal cual,
     - si encuentra una entrada cuyo contenido comienza con PK.. (otro ZIP),
       intenta abrirla como ZIP y **extrae sus entradas internas** al ZIP nuevo.
    Devuelve la ruta del ZIP resultante.
    """
    zip_path = Path(zip_path)
    if repaired_path is None:
        repaired_path = zip_path.with_suffix(".repaired.zip")
    else:
        repaired_path = Path(repaired_path)

    with zipfile.ZipFile(zip_path, "r") as zf_in, \
         zipfile.ZipFile(repaired_path, "w", compression=zipfile.ZIP_DEFLATED) as zf_out:

        for info in zf_in.infolist():
            name = info.filename
            raw = zf_in.read(name)

            # Si la entrada misma parece un ZIP (comienza por PK..), intentar abrirla
            if raw.startswith(b"PK"):
                try:
                    with zipfile.ZipFile(BytesIO(raw), "r") as inner:
                        for inner_info in inner.infolist():
                            inner_name = inner_info.filename
                            # Si ya existe una entrada con el mismo nombre en zf_out, lo renombramos para evitar sobrescribir
                            target_name = inner_name
                            i = 1
                            while target_name in zf_out.namelist():
                                target_name = f"{Path(inner_name).stem}_{i}{Path(inner_name).suffix}"
                                i += 1
                            zf_out.writestr(target_name, inner.read(inner_info.filename))
                            print(f"  [inner] extraído {inner_info.filename} -> {target_name}")
                        # saltar la escritura directa del raw (evita meter zip dentro)
                        continue
                except zipfile.BadZipFile:
                    # no es un ZIP válido, escribir como archivo normal
                    pass

            # Escribir la entrada tal cual (archivo normal)
            # Evitar sobrescribir: si ya existe, renombrar
            target_name = name
            i = 1
            while target_name in zf_out.namelist():
                target_name = f"{Path(name).stem}_{i}{Path(name).suffix}"
                i += 1
            zf_out.writestr(target_name, raw)
            print(f"  [copy] {name} -> {target_name}")

    print("Reparado a:", repaired_path)
    return repaired_path




def safe_add_csv_to_zip(zip_path, internal_path, df, overwrite=True):
    """
    Añade un CSV a zip_path en internal_path de forma segura.
    Si overwrite=True reemplaza la entrada (crea ZIP nuevo internamente para evitar duplicados).
    Si overwrite=False usa append (puede crear entradas duplicadas si ya existía).
    """
    zip_path = Path(zip_path)
    # serializar a bytes
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    if not zip_path.exists():
        # crear de cero
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(internal_path, csv_bytes)
        return

    if overwrite:
        # usar la estrategia segura: crear ZIP temporal copiando todo excepto internal_path
        temp_path = zip_path.with_suffix(".tmp.zip")
        with zipfile.ZipFile(zip_path, "r") as zf_in, \
             zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf_out:

            for info in zf_in.infolist():
                if info.filename == internal_path:
                    continue
                zf_out.writestr(info, zf_in.read(info.filename))
            zf_out.writestr(internal_path, csv_bytes)
        shutil.move(temp_path, zip_path)
    else:
        # append (puede crear entradas duplicadas, normalmente no recomendado)
        with zipfile.ZipFile(zip_path, "a", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(internal_path, csv_bytes)
