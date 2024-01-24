from flask import Flask, request, render_template_string, send_from_directory, session, redirect, url_for
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


UPLOAD_FOLDER = 'Library'
TEMP_FOLDER = 'temp'

app = Flask(__name__)

app.secret_key = 'tajný_klíč'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app) 



os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML = '''
<!doctype html>
<html>
<head>
    <title>Nahrání podtácků</title>
        <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            font-size: 50px;
        }
        .container {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            width: 90%; /* Menší šířka pro PC */
            
            font-size: 50px;
        }
        input[type=file], input[type=submit] {
            margin-bottom: 10px;
            width: 100%;
            padding: 10px 20px; /* Standardní velikost paddingu */
            font-size: 50px;
        }
        input[type=submit] {
            background-color: red;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 50px;
        }
        input[type=submit]:hover {
            background-color: darkred;
        }

        /* Media query pro malé obrazovky (např. mobily) */
        @media (max-width: 600px) {
            body {
                font-size: 20px; /* Větší písmo pro mobily */
            }
            .container {
                width: 80%; /* Větší šířka pro mobily */
                max-width: none;
            }
            input[type=file], input[type=submit] {
                padding: 15px 30px; /* Větší tlačítka pro mobily */
            }
        }
    </style>
</head>
<body>
<div class="container">
    <h2>Nahrajte dva obrázky podtácku z obou stran</h2>
    {% if message %}
    <p>{{ message }}</p>
    {% endif %}
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file1" required><br><br>
        <input type="file" name="file2" required><br><br>
        <input type="submit" value="Nahrát">
    </form>
</div>
</body>
</html>
'''

RESULTS_HTML = '''
<!doctype html>
<html>
<head>
    <title>Výsledky porovnání podtácků</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            font-size: 50px; /* Zvětšení písma */
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        @media (max-width: 400px) {
            body {
                font-size: 16px;
            }
        }
        .header, .uploaded-images, .results-container {
            width: 90%; /* Zvětšení šířky */
            max-width: 1000px; /* Zvětšení maximální šířky */
            text-align: center;
            margin-bottom: 20px;
        }
        .container {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            margin: 10px;
            flex: 1; 
        }
        .results-container {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
        }
        .images img {
            max-width: 100%;
            max-height: 250px; /* Zvětšení velikosti obrázků */
            margin: 0 10px;
        }

        .buttons{
            flex-direction: row;
            align-items: center;
        }

        button {
            background-color: red;
            color: white;
            border: none;
            padding: 12px 24px; /* Zvětšení tlačítka */
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
            font-size: 50px; /* Zvětšení textu tlačítka */
        }
        button:hover {
            background-color: darkred;
        }
        @media (max-width: 300px) {
            /* Kontejnery pod sebou na menších obrazovkách */
            .results-container {
                flex-direction: row;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Výsledky porovnání podtácků</h2>
    </div>
<div class="buttons">
    <a href="/"><button>Uložit podtácek</button></a>
    <a href="/delete"><button>Vymazat podtácek</button></a>
</div>
    <div class="uploaded-images">
        <h2>Nově nahraný podtácek</h2>
        {% if uploaded_images %}
            {% for image_base64 in uploaded_images %}
                <img src="data:image/png;base64,{{ image_base64 }}" alt="Nahraný obrázek" style="max-width: 400px; margin: 10px;">
            {% endfor %}
        {% endif %}
    </div>
    <div class="results-container">
    <div class="container">
        <h3>Podobné podtácky 1:</h3>
        {% if similarities %}
        <ul>
            {% for similarity, path, image_base64 in similarities %}
            <li>{{ similarity|round(2) }}% shoda - {{ path }}<br>
            <img src="data:image/png;base64,{{ image_base64 }}" alt="Obrázek" style="max-width: 200px;"><br></li>
            {% endfor %}
        </ul>
        {% else %}
        <p>Žádné podobné podtácky nebyly nalezeny.</p>
        {% endif %}
    </div>
    <div class="container">
        <h3>Podobné podtácky 2:</h3>
        {% if similarities2 %}
        <ul>
            {% for similarity, path, image_base64 in similarities2 %}
            <li>{{ similarity|round(2) }}% shoda - {{ path }}<br>
            <img src="data:image/png;base64,{{ image_base64 }}" alt="Obrázek" style="max-width: 200px;"><br></li>
            {% endfor %}
        </ul>
        {% else %}
        <p>Žádné podobné podtácky nebyly nalezeny.</p>
        {% endif %}
    </div>
</div>

</body>
</html>


'''
PROCESS_HTML = '''
<!doctype html>
<html>
<head>
    <title>Probíhá proces obrázků</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            font-size: 50px; /* Zvětšení písma */
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        @media (max-width: 400px) {
            body {
                font-size: 16px;
            }
        }
        .header, .uploaded-images, .results-container {
            width: 90%; /* Zvětšení šířky */
            max-width: 1000px; /* Zvětšení maximální šířky */
            text-align: center;
            margin-bottom: 20px;
        }
        .container {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            margin: 10px;
            flex: 1; 
        }
        .results-container {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
        }
        .images img {
            max-width: 100%;
            max-height: 250px; /* Zvětšení velikosti obrázků */
            margin: 0 10px;
        }

        .buttons{
            flex-direction: row;
            align-items: center;
        }

        button {
            background-color: red;
            color: white;
            border: none;
            padding: 12px 24px; /* Zvětšení tlačítka */
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
            font-size: 50px; /* Zvětšení textu tlačítka */
        }
        button:hover {
            background-color: darkred;
        }
        @media (max-width: 300px) {
            /* Kontejnery pod sebou na menších obrazovkách */
            .results-container {
                flex-direction: row;
                align-items: center;
            }
        }
    </style>

    <script>
    // Funkce pro provedení AJAX požadavku na procesování obrázků
    function startImageProcessing() {
        $.ajax({
            url: "/process", // URL pro procesování
            type: "POST",
            success: function (data) {
                // Po úspěšném zpracování přesměrování na stránku s výsledky
                window.location.href = "/results";
            },
            error: function () {
                alert("Chyba při zpracování obrázků.");
            }
        });
    }

    // Po načtení stránky spustit procesování automaticky
    $(document).ready(function () {
        startImageProcessing();
    });
</script>

</head>
<body>
    <div class="header">
        <h2>Výsledky porovnání podtácků</h2>
    </div>
Probíhá konverze obrázků

</body>
</html>


'''

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

    
    return render_template_string(HTML)

@app.route('/process_page', methods=['GET'])
def process_page():
    return render_template_string(PROCESS_HTML)

@app.route('/process', methods=['POST'])
def process():
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
        image = Image.open(file.stream)
        image = image.convert('RGB')  # Odstranění alfa kanálu pro PNG
        file_path = os.path.join(next_folder, f'{index}.png')
        image.save(file_path, 'PNG', quality=95, optimize=True, exif='')

        print("Odstraňuju pozadí...")
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
        uploaded_files_base64.append(result1[1])
        uploaded_files_paths.append(result2[0])
        uploaded_files_base64.append(result2[1])

    # Paralelní hledání podobných obrázků
    with ProcessPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(find_similar_images, uploaded_files_paths[0])
        future2 = executor.submit(find_similar_images, uploaded_files_paths[1])
        similarities = future1.result()
        similarities2 = future2.result()

    print("Dokončeno")

    message = 'Soubory byly úspěšně nahrány'
    if similarities:
        message += ' a nalezeny podobné obrázky'

    session['uploaded_images'] = uploaded_files_base64
    session['similarities'] = similarities
    session['similarities2'] = similarities2
    return "success"  # Návratová hodnota pro AJAX požadavek




@app.route('/results')
def results():
    similarities = session.get('similarities', [])
    similarities2 = session.get('similarities2', [])
    uploaded_images = session.get('uploaded_images', [])

    return render_template_string(RESULTS_HTML, similarities=similarities, similarities2=similarities2, uploaded_images=uploaded_images)


def calculate_similarity(image1, image2):
    # Převod na šedotónové
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # Výpočet histogramu
    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])

    # Normalizace histogramu
    hist1 = cv2.normalize(hist1, hist1).flatten()
    hist2 = cv2.normalize(hist2, hist2).flatten()

    # Výpočet podobnosti
    similarity = cosine_similarity([hist1], [hist2])
    return similarity[0][0]

def find_similar_images(new_image_path):
    similarities = []
    new_image_folder = os.path.dirname(new_image_path)

    # Vytvoření seznamu všech souborů PNG pro zpracování
    all_files = [os.path.join(root, file) for root, dirs, files in os.walk(UPLOAD_FOLDER) for file in files if file.endswith('.png')]
    
    # Použití tqdm pro progress bar
    for file_path in tqdm(all_files, desc="Hledání podobností", unit="soubor"):
        if file_path == new_image_path or os.path.dirname(file_path) == new_image_folder:
            continue
        new_image_data = cv2.imread(new_image_path)
        existing_image_data = cv2.imread(file_path)
        similarity = calculate_similarity(new_image_data, existing_image_data)
        if similarity > 0.998:
            relative_path = os.path.relpath(file_path, UPLOAD_FOLDER)
            image_base64 = image_to_base64(file_path)
            similarities.append((similarity*100, file_path, image_base64))

    return similarities



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