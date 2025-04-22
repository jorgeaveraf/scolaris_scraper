import unicodedata

def normalizar_texto(texto):
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII").strip().upper()
