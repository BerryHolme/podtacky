import os
import concurrent.futures
from PIL import Image
import numpy as np

DATASET_FOLDER = 'dataset'

# Funkce pro úpravu a uložení obrázku
def process_image(file_path, idx):
    try:
        # Načtení obrázku
        image = Image.open(file_path)
        width, height = image.size
        print (os.path.basename(file_path))

        # Pět různých úprav
        for i in range(1, 11):
            # Náhodná rotace a změna velikosti
            angle = np.random.randint(0, 360)
            scale = 1 + np.random.uniform(-0.2, 0.2)
            x = np.random.randint(-500, 500)
            y = np.random.randint(-500, 500)
            new_width, new_height = int(width * scale), int(height * scale)

            # Rotace a změna velikosti
            new_image = image.rotate(angle, expand=True).resize((new_width, new_height))

            # Vytvoření nového jména souboru
            new_name = f"{os.path.splitext(os.path.basename(file_path))[0]}-{i}.png"
            new_path = os.path.join(DATASET_FOLDER, new_name)

            # Uložení nového obrázku
            new_image.save(new_path)

    except Exception as e:
        print(f"Chyba při zpracování souboru {file_path}: {e}")

# Získání seznamu obrázků
all_files = [os.path.join(DATASET_FOLDER, file) for file in os.listdir(DATASET_FOLDER) if file.endswith('.png')]

# Rozdělení práce mezi vlákna
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    for idx, file_path in enumerate(all_files):
        executor.submit(process_image, file_path, idx)

print("Zpracování obrázků dokončeno.")
