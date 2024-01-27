import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Nahraďte 'model_path' cestou k vašemu natrénovanému modelu
model_path = 'models/shapereg.model.h5'

# Načtení natrénovaného modelu
model = load_model(model_path)

def predict_shape(image_path, model):
    # Načtení obrázku a převedení na alpha kanál
    img = Image.open(image_path).convert('RGBA')
    alpha = img.split()[-1]

    # Vytvoření nového obrázku s třemi identickými kanály z alfa kanálu
    alpha_resized = alpha.resize((400, 300))
    new_img = Image.merge("RGB", (alpha_resized, alpha_resized, alpha_resized))

    new_img.save('upgrade.png')

    # Převedení obrázku na pole vhodné pro model
    img_array = image.img_to_array(new_img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # Přidání dimenze batch

    # Predikce modelu
    predictions = model.predict(img_array)
    return predictions


# Zde budete moci nahrát obrázek a získat predikce
# Nahraďte 'image_path' cestou k obrázku, který chcete klasifikovat
image_path = "Library/63/1.png"
predictions = predict_shape(image_path, model)

# Výpis predikcí pro každý tvar
shapes = ['Circle', 'Square']  # Přizpůsobte podle tříd, které váš model zná
percentage_predictions = {shape: float(predictions[0][i]) * 100 for i, shape in enumerate(shapes)}

print(percentage_predictions)
