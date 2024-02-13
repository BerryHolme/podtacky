import os
import shutil

def move_files(base_folder):
    # Procházení kořenové složky a jejích podsložek
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            # Zjištění, zda soubor nekončí na .png
            if not file.endswith('.png'):
                # Vytvoření cesty pro složku "usage" v aktuální podsložce
                usage_folder = os.path.join(root, 'usage')
                # Pokud složka "usage" neexistuje, vytvoří se
                if not os.path.exists(usage_folder):
                    os.makedirs(usage_folder)
                # Původní cesta souboru
                original_file_path = os.path.join(root, file)
                # Nová cesta souboru ve složce "usage"
                new_file_path = os.path.join(usage_folder, file)
                # Přesun souboru
                shutil.move(original_file_path, new_file_path)
                print(f'Soubor {file} byl přesunut do {new_file_path}')

# Cesta k základní složce "Library"
base_folder = 'Library'
move_files(base_folder)
