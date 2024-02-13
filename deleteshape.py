import os

def delete_shape_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".shape"):
                os.remove(os.path.join(root, file))
                print(f"Deleted: {os.path.join(root, file)}")

# Nahraďte 'root_folder_path' cestou ke kořenové složce vašeho projektu
root_folder_path = 'Library'
delete_shape_files(root_folder_path)

# Pokud chcete provést to samé i ve složce 'usage'
usage_folder_path = 'usage'
delete_shape_files(usage_folder_path)
