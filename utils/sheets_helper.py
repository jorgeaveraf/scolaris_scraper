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

def subir_csv_a_google_sheets_append(csv_path, sheet_id, hoja, start_col='A', skip_header=False):
    client = get_gspread_client()

    sheet = client.open_by_key(sheet_id)
    
    df = pd.read_csv(csv_path)

    # Si se desea ignorar encabezado
    if skip_header:
        df = df.iloc[1:]

    hoja_normalizada = hoja.strip().lower()
    try:
        worksheet = next(
            ws for ws in sheet.worksheets()
            if ws.title.strip().lower() == hoja_normalizada
        )
    except StopIteration:
        worksheet = sheet.add_worksheet(title=hoja, rows="1000", cols=str(len(df.columns)))

    start_col = 'B'
    start_row = 2
    col_offset = ord(start_col.upper()) - ord('A')  # Ej: B -> 1
    start_cell = f"{start_col}{start_row}"

    # Escribir datos en el rango calculado
    data_to_upload = df.values.tolist() if skip_header else [df.columns.values.tolist()] + df.values.tolist()

    worksheet.update(
        start_cell,
        data_to_upload,
        value_input_option="USER_ENTERED"
    )


    print(f"📌 {len(df)} filas cargadas a la hoja '{hoja}' desde la columna {start_col}.")



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

