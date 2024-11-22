import os

import cv2
import face_recognition
import mysql.connector
import numpy as np


def guardar_promedio_rostro_datos(name, encodings, photo_count, db_name='basegestionempleados'):
    if encodings:
        average_encoding = np.mean(encodings, axis=0)
        conn = mysql.connector.connect(host='localhost', user='root', password='', database=db_name)
        c = conn.cursor()
        c.execute("SELECT id FROM faces WHERE name = %s", (name,))
        result = c.fetchone()
        if result:
            c.execute("UPDATE faces SET encoding = %s, photo_count = %s WHERE name = %s",
                      (average_encoding.tobytes(), photo_count, name))
        else:
            c.execute("INSERT INTO faces (name, encoding, photo_count) VALUES (%s, %s, %s)",
                      (name, average_encoding.tobytes(), photo_count))
        conn.commit()
        conn.close()


def tecnica_training(image):
    # tecnicas de aumento de datos
    augmented_images = [image]
    # rotaciones
    for angle in [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]:
        augmented_images.append(cv2.rotate(image, angle))
    # ajustes de brillo
    for alpha in [0.5, 1.5]:
        augmented_images.append(cv2.convertScaleAbs(image, alpha=alpha, beta=0))
    return augmented_images


def cargar_img_conocidad_directorio(directory, db_name='basegestionempleados'):
    conn = mysql.connector.connect(host='localhost', user='root', password='', database=db_name)
    c = conn.cursor()

    for subdir, _, files in os.walk(directory):
        encodings = []
        photo_count = len([f for f in files if f.endswith('.jpg') or f.endswith('.png')])
        if photo_count == 0:
            continue

        name = os.path.basename(subdir)
        c.execute("SELECT photo_count FROM faces WHERE name = %s", (name,))
        result = c.fetchone()

        if result and result[0] == photo_count:
            print(f"Skipping {name}, no new photos.")
            continue

        for filename in files:
            if filename.endswith('.jpg') or filename.endswith('.png'):
                image_path = os.path.join(subdir, filename)
                image = face_recognition.load_image_file(image_path)
                augmented_images = tecnica_training(image)
                for img in augmented_images:
                    face_encodings = face_recognition.face_encodings(img)
                    if face_encodings:
                        encodings.append(face_encodings[0])

        if encodings:
            guardar_promedio_rostro_datos(name, encodings, photo_count, db_name)

    conn.close()


if __name__ == "__main__":
    cargar_img_conocidad_directorio('UsuariosImagenes')
