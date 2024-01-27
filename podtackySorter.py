from flask import Flask, request, render_template_string, send_from_directory, session, redirect, url_for
from flask import render_template 
from flask_session import Session 
import os
from rembg import remove
import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
import io
from urllib.parse import quote
import base64
from tqdm import tqdm
import shutil
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from werkzeug.datastructures import FileStorage
import asyncio
from flask import jsonify
from threading import Lock

processing_status = {"picture1": "Nahrávání...", "picture2": "Nahrávání..."}
status_lock = Lock()


UPLOAD_FOLDER = 'Library'
TEMP_FOLDER = 'temp'

app = Flask(__name__)

app.secret_key = 'tajný_klíč'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app) 



os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/getNumber', methods=['GET'])
def getNumber():
    number = 0
    for folder in os.listdir(UPLOAD_FOLDER):
        if folder.isdigit():
            number += 1
            
    number = max(number, int(folder))
    data = {
        'number': number
    }

    return jsonify(data) 

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_next_folder_name():
    max_folder = 0
    for folder in os.listdir(UPLOAD_FOLDER):
        if folder.isdigit():
            max_folder = max(max_folder, int(folder))
    return str(max_folder + 1)
   

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    message = None
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']

        if file1 and file2:
            file1.save(os.path.join(TEMP_FOLDER, '1' + os.path.splitext(file1.filename)[1]))
            file2.save(os.path.join(TEMP_FOLDER, '2' + os.path.splitext(file2.filename)[1]))


        return redirect(url_for('process_page'))

    
    return render_template('index.html')

@app.route('/process_page', methods=['GET'])
def process_page():
    session['picture1'] = ''
    session['picture2'] = ''
    return render_template('results.html')

@app.route('/process', methods=['POST'])
def process():
    with status_lock:
        processing_status["picture1"] = "Nahrávám..."
        processing_status["picture1"] = "Nahrávám..."
    similarities = []
    similarities2 = []
    next_folder_name = get_next_folder_name()
    next_folder = os.path.join(UPLOAD_FOLDER, next_folder_name)
    os.makedirs(next_folder, exist_ok=True)

    file1_path = os.path.join(TEMP_FOLDER, '1.jpg')
    file2_path = os.path.join(TEMP_FOLDER, '2.jpg')

    file1 = FileStorage(stream=open(file1_path, 'rb'), filename='file1')
    file2 = FileStorage(stream=open(file2_path, 'rb'), filename='file2')

    def process_image(file, index):
        print("Konvertuju...")
        global processing_status
        with status_lock:
            processing_status[f"picture{index}"] = "Konvertuju..."

        image = Image.open(file.stream)
        image = image.convert('RGB')  # Odstranění alfa kanálu pro PNG
        file_path = os.path.join(next_folder, f'{index}.png')
        image.save(file_path, 'PNG', quality=95, optimize=True, exif='')

        print("Odstraňuju pozadí...")
        with status_lock:
            processing_status[f"picture{index}"] = "Odstraňuju pozadí..."

        # Odstranění pozadí pomocí rembg
        with open(file_path, 'rb') as img_file:
            input_image = img_file.read()
        output_image = remove(input_image)
        with open(file_path, 'wb') as f:
            f.write(output_image)

        return file_path, image_to_base64(file_path)

    uploaded_files_paths = []
    uploaded_files_base64 = []


    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(process_image, file1, 1)
        future2 = executor.submit(process_image, file2, 2)
        result1 = future1.result()
        result2 = future2.result()
        uploaded_files_paths.append(result1[0])
        uploaded_files_base64.append(image_to_base64_resized(result1[0]))
        uploaded_files_paths.append(result2[0])
        uploaded_files_base64.append(image_to_base64_resized(result2[0]))

    # Paralelní hledání podobných obrázků
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(find_similar_images, uploaded_files_paths[0])
        future2 = executor.submit(find_similar_images, uploaded_files_paths[1])
        similarities = future1.result()
        similarities2 = future2.result()


    print("Dokončeno")



    message = 'Soubory byly úspěšně nahrány'
    if similarities:
        message += ' a nalezeny podobné obrázky'

        
    with status_lock:
        processing_status["picture1"] = "Posílám..."
        processing_status["picture2"] = "Posílám..."

    data = {
        'uploaded_images': uploaded_files_base64,
        'similarities': similarities,
        'similarities2':similarities2
    }

    return jsonify(data) 


@app.route('/getStatus', methods=['GET'])
def getStatus():
    with status_lock:
        status_copy = processing_status.copy()
    return jsonify(status_copy)




def calculate_similarity(hist1, file_path):
    # Check if the histogram file for the second image exists
    hist_file = os.path.splitext(file_path)[0] + '.hist.npy'
    
    if os.path.exists(hist_file):
        # Load the histogram from the file
        hist2 = np.load(hist_file)
    else:
        # Read the second image
        image2 = cv2.imread(file_path)
        gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # Calculate the histogram
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])

        # Normalize the histogram
        hist2 = cv2.normalize(hist2, hist2).flatten()

        # Save the histogram to a file
        np.save(hist_file, hist2)

    # Calculate the cosine similarity
    similarity = cosine_similarity([hist1], [hist2])
    return similarity[0][0]


def find_similar_images(new_image_path):
    global processing_status
    image_index = os.path.basename(new_image_path).replace('.png', '')

    similarities = []
    new_image_folder = os.path.dirname(new_image_path)
    all_files = [os.path.join(root, file) for root, dirs, files in os.walk(UPLOAD_FOLDER) for file in files if file.endswith('.png')]

    total_files = len(all_files)
    processed_files = 0

    new_image_data = cv2.imread(new_image_path)
    gray1 = cv2.cvtColor(new_image_data, cv2.COLOR_BGR2GRAY)
    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist1 = cv2.normalize(hist1, hist1).flatten()
    
    for file_path in all_files:
        if file_path == new_image_path or os.path.dirname(file_path) == new_image_folder:
            continue

        processed_files += 1
        progress = (processed_files / total_files) * 100
        with status_lock:
            processing_status[f"picture{image_index}"] = f"Zpracovávám {processed_files}/{total_files} souborů ({progress:.2f}%)"

        #existing_image_data = cv2.imread(file_path) 

        similarity = calculate_similarity(hist1, file_path)
        if similarity > 0.998:
            relative_path = os.path.relpath(file_path, UPLOAD_FOLDER)
            image_base64 = image_to_base64_resized(file_path)
            similarities.append((similarity*100, file_path, image_base64))

    with status_lock:
        processing_status[f"picture{image_index}"] = "Dokončeno"

    return similarities

def image_to_base64_resized(image_path, scale_factor=0.2):
    image = Image.open(image_path)
    # Zmenšení obrázku
    resized_image = image.resize((int(image.width * scale_factor), int(image.height * scale_factor)), Image.ANTIALIAS)
    buffered = io.BytesIO()
    resized_image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')




@app.route('/delete')
def delete_latest_uploaded_images():
    max_folder_num = -1
    max_folder_path = None

    # Procházení složek ve složce UPLOAD_FOLDER a hledání nejvyššího čísla
    for folder in os.listdir(UPLOAD_FOLDER):
        if folder.isdigit() and int(folder) > max_folder_num:
            max_folder_num = int(folder)
            max_folder_path = os.path.join(UPLOAD_FOLDER, folder)

    if max_folder_path and os.path.exists(max_folder_path):
        # Odstranění složky a jejího obsahu
        shutil.rmtree(max_folder_path)
        message = "Nejnovější obrázky byly úspěšně vymazány."
    else:
        message = "Nebyly nalezeny žádné obrázky k vymazání."

    # Resetování session proměnných
    session.pop('uploaded_images', None)
    session.pop('similarities', None)
    session.pop('similarities2', None)

    # Přesměrování zpět na hlavní stránku s případným zprávou
    return redirect(url_for('upload_file', message=message))




@app.route('/static/<path:path>')
def static_dir(path):
    return send_from_directory('Library', path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)