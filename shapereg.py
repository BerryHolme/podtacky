import cv2
import numpy as np

def detect_shape(image_path):
    # Načtení obrázku
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    # Získání alfa kanálu
    alpha_channel = image[:, :, 3]
    # Prahování alfa kanálu pro získání masky tvaru
    _, mask = cv2.threshold(alpha_channel, 0, 255, cv2.THRESH_BINARY)
    # Hledání kontur v masce
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Aproximace kontury
        approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
        area = cv2.contourArea(contour)
        bounding_rect = cv2.boundingRect(contour)
        bounding_rect_area = bounding_rect[2] * bounding_rect[3]
        area_ratio = area / bounding_rect_area

        # Určení tvaru na základě poměru oblasti
        if len(approx) >= 4 and area_ratio > 0.8:
            return "Square"
        elif len(approx) < 10 and area_ratio > 0.8:
            return "Circle"
    return "Unknown"

# Zde si představme, že 'image_path' je cesta k obrázku, který chceme analyzovat
image_path = "Library/108/1.png"
shape = detect_shape(image_path)
print(f"Detected shape: {shape}")
