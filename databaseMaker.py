import os
import sqlite3
import base64

# Funkce pro vytvoření tabulky v SQLite databázi
def create_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS library (
            folder_id INTEGER PRIMARY KEY,
            file_1_base64 TEXT,
            file_1_hist BLOB,
            file_1_png BLOB,
            file_1_shape BLOB,
            file_2_base64 TEXT,
            file_2_hist BLOB,
            file_2_png BLOB,
            file_2_shape BLOB
        )
    ''')

# Funkce pro načtení souboru jako BLOB nebo text
def load_file(file_path, as_text=False):
    with open(file_path, 'rb') as f:
        data = f.read()
        if as_text:
            return data.decode('utf-8')
        return data

# Hlavní funkce pro vytvoření databáze
def create_database(library_path, db_path):
    # Připojení k databázi (nebo její vytvoření)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Vytvoření tabulky
    create_table(cursor)

    # Iterace přes složky v 'Library'
    for folder_name in os.listdir(library_path):
        folder_path = os.path.join(library_path, folder_name)
        
        if os.path.isdir(folder_path):
            data = {
                'file_1_base64': None,
                'file_1_hist': None,
                'file_1_png': None,
                'file_1_shape': None,
                'file_2_base64': None,
                'file_2_hist': None,
                'file_2_png': None,
                'file_2_shape': None,
            }
            
            # Prohledávání souborů ve složce
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                
                if file_name.startswith('1.') or file_name.startswith('2.'):
                    prefix, suffix = file_name.split('.', 1)
                    key = f'file_{prefix}_{suffix}'
                    
                    if suffix == 'base64':
                        data[key] = load_file(file_path, as_text=True)
                    else:
                        data[key] = load_file(file_path)
            
            # Vložení dat do tabulky
            cursor.execute('''
                INSERT INTO library (file_1_base64, file_1_hist, file_1_png, file_1_shape, 
                                     file_2_base64, file_2_hist, file_2_png, file_2_shape)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['file_1_base64'], data['file_1_hist'], data['file_1_png'], data['file_1_shape'],
                data['file_2_base64'], data['file_2_hist'], data['file_2_png'], data['file_2_shape']
            ))

    # Uložení změn a zavření databáze
    conn.commit()
    conn.close()

# Použití funkce
library_path = 'Library'  # cesta k hlavní složce Library
db_path = 'library.db'  # cesta k SQLite databázi
create_database(library_path, db_path)
