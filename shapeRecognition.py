import os
import PIL
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Nastavení cesty ke složkám s daty
base_dir = 'dataset'  # Nahraďte 'path_to_your_data' cestou k vašim datům
train_dir = os.path.join(base_dir, 'Train')
test_dir = os.path.join(base_dir, 'Test')

# Předzpracování dat - augmentace a normalizace
train_datagen = ImageDataGenerator(rescale=1./255, rotation_range=40, width_shift_range=0.2,
                                   height_shift_range=0.2, shear_range=0.2, zoom_range=0.2,
                                   horizontal_flip=True, fill_mode='nearest')
test_datagen = ImageDataGenerator(rescale=1./255)

# Tok trénovacích a validačních dat
train_generator = train_datagen.flow_from_directory(
    train_dir, 
    target_size=(400, 300), 
    batch_size=32, 
    class_mode='categorical'
)
test_generator = test_datagen.flow_from_directory(
    test_dir, 
    target_size=(400, 300),
    batch_size=32, 
    class_mode='categorical'
)


# Definování modelu
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(400, 300, 3)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(512, activation='relu'),
    layers.Dense(3, activation='softmax')  # Výstup pro 3 třídy: Circle, Square, Hexagon
])

# Kompilace modelu
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Trénink modelu
history = model.fit(
    train_generator, 
    steps_per_epoch=train_generator.samples // train_generator.batch_size,  # Dynamicky vypočítáno
    epochs=30, 
    validation_data=test_generator, 
    validation_steps=test_generator.samples // test_generator.batch_size  # Dynamicky vypočítáno
)

