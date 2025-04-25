import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)


def subir_csv_a_google_sheets(csv_path, sheet_id, hoja):
    client = get_gspread_client()
    sheet = client.open_by_key(sheet_id)
    df = pd.read_csv(csv_path, skiprows=1, header=None)

    # Buscar hoja insensible a mayúsculas
    hoja_normalizada = hoja.strip().lower()
    try:
        worksheet = next(
            ws for ws in sheet.worksheets()
            if ws.title.strip().lower() == hoja_normalizada
        )
    except StopIteration:
        # Si no existe, la creamos
        worksheet = sheet.add_worksheet(title=hoja, rows=str(len(df) + 10), cols=str(len(df.columns)))

    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    print(f"✅ Subido a Google Sheets → Hoja: '{hoja}' ({len(df)} filas)")


def subir_csv_a_google_sheets_append(
    csv_path: str,
    sheet_id: str,
    hoja: str,
    start_col: str = "A",
    skip_header: bool = False
):
    """
    Añade las filas de un CSV al final de la hoja indicada,
    empezando en la columna `start_col` (p.ej. "B", "C", ...).
    skip_header=True hace que se descarten los nombres de columna.
    """
    # 1) Lee el CSV
    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError:
        print(f"⚠️ El archivo {csv_path} está vacío. Nada que subir.")
        return

    if skip_header:
        if "nombre" in df.iloc[0].values:
            df = df.iloc[1:]
        
    if df.empty:
        print("⚠️ No hay filas para subir después de aplicar skip_header.")
        return

    # 2) Autenticación y abrir hoja
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(sheet_id)

    # 3) Localizar o crear la worksheet
    norm = hoja.strip().lower()
    try:
        ws = next(w for w in sh.worksheets() if w.title.strip().lower() == norm)
    except StopIteration:
        ws = sh.add_worksheet(title=hoja,
                              rows=str(len(df) + 10),
                              cols=str(len(df.columns) + ord(start_col.upper()) - ord("A")))

    # 4) Preparar padding (celdas vacías antes de los datos)
    pad = ord(start_col.upper()) - ord("A")
    rows_to_append = []

    # (Opcional) incluir cabecera desplazada
    if not skip_header:
        header = df.columns.tolist()
        rows_to_append.append([""] * pad + header)

    # datos
    for row in df.values.tolist():
        rows_to_append.append([""] * pad + row)

    # 5) Append_rows
    ws.append_rows(rows_to_append, value_input_option="USER_ENTERED")
    print(f"📌 {len(rows_to_append)} filas añadidas a '{hoja}' desde la columna {start_col}.")




def leer_hoja_como_df(sheet_id, hoja):
    client = get_gspread_client()

    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(hoja)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def actualizar_status_en_hoja(sheet_id, hoja, columna_busqueda_1, valor_1, columna_busqueda_2, valor_2, columna_estado, nuevo_estado):
    client = get_gspread_client()

    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(hoja)

    # Buscar datos en toda la hoja
    data = worksheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    col_idx_1 = headers.index(columna_busqueda_1)
    col_idx_2 = headers.index(columna_busqueda_2)
    col_idx_estado = headers.index(columna_estado)

    for i, row in enumerate(rows, start=2):  # índice de fila en GSheets empieza en 2 (después de encabezado)
        if row[col_idx_1].strip() == valor_1.strip() and row[col_idx_2].strip() == valor_2.strip():
            worksheet.update_cell(i, col_idx_estado + 1, nuevo_estado)
            print(f"📌 Estado actualizado en fila {i}: {valor_1} - {valor_2} → {nuevo_estado}")
            return

    print(f"⚠️ No se encontró coincidencia para {valor_1} / {valor_2} en la hoja {hoja}")

def resetear_estado_hoja(sheet_id, hoja, columna_estado="status", nuevo_estado="pendiente"):
    client = get_gspread_client()

    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(hoja)

    data = worksheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    try:
        col_idx_estado = headers.index(columna_estado)
    except ValueError:
        print(f"⚠️ La columna '{columna_estado}' no existe en la hoja '{hoja}'")
        return

    for i in range(len(rows)):
        worksheet.update_cell(i + 2, col_idx_estado + 1, nuevo_estado)

    print(f"🔄 Estado de todas las filas de la hoja '{hoja}' reiniciado a '{nuevo_estado}'.")

