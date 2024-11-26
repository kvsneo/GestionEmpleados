import datetime

import cv2
import face_recognition
import mysql.connector
import numpy as np


def obtener_rostros_conocidos(db_name='basegestionempleados'):
    conn = mysql.connector.connect(host='localhost', user='root',  # Cambia a tu usuario de MySQL
                                   password='',  # Cambia a tu contraseña de MySQL
                                   database=db_name)
    c = conn.cursor()
    c.execute("SELECT name, encoding FROM faces")
    rows = c.fetchall()
    known_faces = []
    known_names = []
    for row in rows:
        name, encoding = row
        known_faces.append(np.frombuffer(encoding, dtype=np.float64))
        known_names.append(name)
    conn.close()
    return known_faces, known_names


def comparar_rostros(known_faces, known_names, captured_image_path):
    captured_image = face_recognition.load_image_file(captured_image_path)
    captured_image_encoding = face_recognition.face_encodings(captured_image)

    if not captured_image_encoding:
        raise ValueError("No se encontraron rostros en la imagen capturada.")

    for known_face, name in zip(known_faces, known_names):
        match = face_recognition.compare_faces([known_face], captured_image_encoding[0])
        if match[0]:
            # Insert match information into the database
            conn = mysql.connector.connect(host='localhost', user='root', password='', database='basegestionempleados')
            c = conn.cursor()
            match_time = datetime.datetime.now()
            c.execute("INSERT INTO match_info (name, match_time) VALUES (%s, %s)", (name, match_time))
            conn.commit()
            conn.close()
            return name
    return None


def capturar_img_de_camara(known_faces, known_names):
    video_capture = cv2.VideoCapture(1)
    while True:
        try:
            ret, frame = video_capture.read()
            cv2.imshow('Video', frame)

            # presiona 'q' para salir de la transmisión de la cámara
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # presiona la barra espaciadora para capturar la imagen
            if cv2.waitKey(1) & 0xFF == ord(' '):
                if ret:
                    cv2.imwrite('imagen_capturada.jpg', frame)
                    match_name = comparar_rostros(known_faces, known_names, 'imagen_capturada.jpg')
                    if match_name:
                        print(f"Rostro Coincide : {match_name}")
                    else:
                        print("No se encontró coincidencia.")
                else:
                    raise Exception("Error al capturar la imagen de la cámara")
        except Exception as e:
            print(f"Error: {e}")

    video_capture.release()
    cv2.destroyAllWindows()


def main_reconocimineto_usuarios():
    known_faces, known_names = obtener_rostros_conocidos()
    capturar_img_de_camara(known_faces, known_names)


if __name__ == "__main__":
    main_reconocimineto_usuarios()
