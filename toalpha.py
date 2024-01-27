import os
from PIL import Image

UPLOAD_FOLDER = 'Library'
DATASET_FOLDER = 'dataset'

# Vytvoření složky dataset, pokud neexistuje
if not os.path.exists(DATASET_FOLDER):
    os.makedirs(DATASET_FOLDER)

# Projde složku Library a najde všechny PNG soubory
all_files = [os.path.join(root, file) for root, dirs, files in os.walk(UPLOAD_FOLDER) 
             for file in files if file.endswith('.png')]

for file_path in all_files:
    try:
        # Načtení obrázku
        image = Image.open(file_path).convert("RGBA")
        
        # Extrahování alfa kanálu
        alpha = image.split()[-1]
        
        # Složení nového jména souboru
        folder_number = os.path.basename(os.path.dirname(file_path))
        new_name = f"{folder_number}-{os.path.basename(file_path)}"
        new_path = os.path.join(DATASET_FOLDER, new_name)
        
        # Uložení alfa kanálu
        alpha.save(new_path)
    except Exception as e:
        print(f"Chyba při zpracování souboru {file_path}: {e}")
