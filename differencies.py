import os
import concurrent.futures
from PIL import Image
from PIL import Image, ImageOps
import numpy as np

DATASET_FOLDER = 'dataset/train/squares'

# Funkce pro úpravu a uložení obrázku
def process_image(file_path, idx):
    try:
        # Načtení obrázku
        image = Image.open(file_path)
        width, height = image.size

        for i in range(1, 11):
            # Náhodná rotace
            angle = np.random.randint(0, 360)
            rotated_image = image.rotate(angle, expand=True)

            # Vytvoření nového obrázku s původním rozlišením a vložení otáčeného obrázku
            result_image = Image.new("RGBA", (width, height), (0, 0, 0, 255))
            result_image.paste(rotated_image, ((width - rotated_image.width) // 2, (height - rotated_image.height) // 2))

            # Nahrazení prázdných pixelů černou barvou
            result_image = result_image.convert("RGB")

            # Vytvoření nového jména souboru
            new_name = f"{os.path.splitext(os.path.basename(file_path))[0]}-{i}.png"
            new_path = os.path.join(DATASET_FOLDER, new_name)

            # Uložení nového obrázku
            result_image.save(new_path)

    except Exception as e:
        print(f"Chyba při zpracování souboru {file_path}: {e}")

# Získání seznamu obrázků
all_files = [os.path.join(DATASET_FOLDER, file) for file in os.listdir(DATASET_FOLDER) if file.endswith('.png')]

# Rozdělení práce mezi vlákna
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    for idx, file_path in enumerate(all_files):
        executor.submit(process_image, file_path, idx)

print("Zpracování obrázků dokončeno.")
