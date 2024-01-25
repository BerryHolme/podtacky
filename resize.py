from PIL import Image
import os
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

def resize_image(image_path, new_size=(400, 300)):
    with Image.open(image_path) as img:
        resized_img = img.resize(new_size, Image.ANTIALIAS)
        resized_img.save(image_path)

def process_images(directory):
    images = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                images.append(os.path.join(root, file))

    with ThreadPoolExecutor(max_workers=10) as executor:
        list(tqdm(executor.map(resize_image, images), total=len(images)))

# Příklad použití
directory_path = 'dataset/train'  # Nahraďte cestou k vašemu adresáři se složkami obsahujícími obrázky
process_images(directory_path)
