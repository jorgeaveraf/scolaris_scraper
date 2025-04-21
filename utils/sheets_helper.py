import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

start_col = 'B'
start_row = 1
start_cell = f"{start_col}{start_row}"

def subir_csv_a_google_sheets(csv_path, sheet_id, hoja):
    import gspread
    import pandas as pd
    from oauth2client.service_account import ServiceAccountCredentials

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
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

def subir_csv_a_google_sheets_append(csv_path, sheet_id, hoja):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)
    df = pd.read_csv(csv_path)

    hoja_normalizada = hoja.strip().lower()
    try:
        worksheet = next(
            ws for ws in sheet.worksheets()
            if ws.title.strip().lower() == hoja_normalizada
        )
    except StopIteration:
        worksheet = sheet.add_worksheet(title=hoja, rows="1000", cols=str(len(df.columns)))

    # Agregar cada fila al final
    worksheet.update(
        'B2',
        [df.columns.values.tolist()] + df.values.tolist(),
        value_input_option="USER_ENTERED"
    )

    print(f"📌 {len(df)} filas cargadas a la hoja '{hoja}' desde la columna B.")
