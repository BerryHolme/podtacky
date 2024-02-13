import os
import shutil

def delete_usage_folders(base_path):
    # Projít všechny podsložky v zadané cestě
    for root, dirs, files in os.walk(base_path):
        # Kontrola, zda mezi podsložkami existuje složka s názvem "usage"
        if 'usage' in dirs:
            # Vytvoření plné cesty ke složce "usage"
            usage_path = os.path.join(root, 'usage')
            # Odstranění složky "usage" a jejího obsahu
            shutil.rmtree(usage_path)
            #print(f'Složka {usage_path} byla úspěšně vymazána.')

# Zadejte základní cestu ke složce "Library"
base_path = 'Library'
delete_usage_folders(base_path)
