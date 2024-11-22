import os
import time

import cv2
import face_recognition


def capture_images(nombre, num_photos=5):
    directorio = os.path.join('ImgUsuarios', nombre)
    os.makedirs(directorio, exist_ok=True)

    # Obtener numero de imagenes en el directorio
    fotos_existentes = [f for f in os.listdir(directorio) if f.endswith('.jpg')]
    contador_fotos = len(fotos_existentes)

    captura_video = cv2.VideoCapture(1)

    while contador_fotos < len(fotos_existentes) + num_photos:
        ret, frame = captura_video.read()
        cv2.imshow('Video', frame)

        if ret:
            # Verificar si hay rostros en el frame
            face_locations = face_recognition.face_locations(frame)
            if face_locations:
                photo_path = os.path.join(directorio, f'{nombre}_{contador_fotos + 1}.jpg')
                cv2.imwrite(photo_path, frame)
                print(f"Foto {contador_fotos + 1} capturada y almacenada en {photo_path}")
                contador_fotos += 1
                time.sleep(1)  # Captura cada 1 segundo
        else:
            raise Exception("Error al capturar imagen de la camara")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    captura_video.release()
    cv2.destroyAllWindows()


def main_capturar_usuario(name):
    video_capture = cv2.VideoCapture(1)
    print("Presione la barra espaciadora para comenzar a capturar fotos.")
    print(f"Capturando fotos para el usuario: {name}")
    while True:
        ret, frame = video_capture.read()
        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord(' '):
            video_capture.release()
            cv2.destroyAllWindows()
            capture_images(name)
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
