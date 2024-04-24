import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk
import cv2
import dlib
from PIL.Image import Resampling

# Función para convertir imágenes de OpenCV a formatos compatibles con Tkinter
def cv2_to_tkimage(cv2_image):
    cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(cv2_image)
    tk_image = ImageTk.PhotoImage(pil_image)
    return tk_image


def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))

def on_exit(event=None):
    root.attributes("-fullscreen", False)
    root.quit()

def comparar(imagen1, imagen2):
    try:
        # Convertir imágenes a escala de grises
        gray1 = cv2.cvtColor(imagen1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(imagen2, cv2.COLOR_BGR2GRAY)

        # Inicializar el detector y extractor SIFT
        sift = cv2.SIFT_create()

        # Detectar keypoints y calcular descriptores
        keypoints1, descriptors1 = sift.detectAndCompute(gray1, None)
        keypoints2, descriptors2 = sift.detectAndCompute(gray2, None)

        # Inicializar el matcher de fuerza bruta
        bf = cv2.BFMatcher()

        # Emparejar descriptores
        matches = bf.knnMatch(descriptors1, descriptors2, k=2)

        # Filtrar los buenos matches según la relación de distancia
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        # Calcular el porcentaje de emparejamiento
        match_percentage = (len(good_matches) / max(len(keypoints1), len(keypoints2))) * 100
    except:
        match_percentage = 0.0
    return match_percentage

contador = 0
array_imagenes = []

def detectar_rostros():
    global contador, array_imagenes

    ret, frame = cap.read()
    if ret:
        # Convertir la imagen a escala de grises si es en color
        if len(frame.shape) > 2 and frame.shape[2] == 3:
            imagen_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            imagen_gris = frame

        # Detectar rostros en la imagen utilizando Dlib
        rostros = detector(imagen_gris, 1)
        print(len(rostros))
        for rostro in rostros:
            #print("Rostro detectado")
            # Obtener las coordenadas del rostro
            x1 = rostro.left()
            y1 = rostro.top()
            x2 = rostro.right()
            y2 = rostro.bottom()
            

            # Ampliar la región de interés del rostro
            ampliacion = 0.2  # Porcentaje de ampliación
            delta_w = int((x2 - x1) * ampliacion)
            delta_h = int((y2 - y1) * ampliacion)
            x1 -= delta_w
            y1 -= delta_h
            x2 += delta_w
            y2 += delta_h

            # Asegurar que las coordenadas ampliadas no sean negativas
            x1 = max(0, x1)
            y1 = max(0, y1)

            # Capturar la imagen del rostro ampliado
            rostro_img = frame[y1:y2, x1:x2]

            # Dibujar un rectángulo alrededor del rostro detectado en el fotograma original
            #cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

            # Superponer la imagen del rostro en el fotograma original
            frame[y1:y2, x1:x2] = rostro_img
            is_new_face = True
            
            if len(array_imagenes) > 0:                   
                for img in array_imagenes:
                    print(comparar(rostro_img, img))
                    if comparar(rostro_img, img) > 0.0:
                        is_new_face = False
                        break 
                
                if is_new_face:
                    array_imagenes.append(rostro_img)
                             
            elif len(array_imagenes) == 0:
                array_imagenes.append(rostro_img)

    
            print(len(array_imagenes))
            # Mostrar las últimas tres imágenes capturadas
            if len(array_imagenes) >= 1:      
                imagenes_tk = []              
                for i, img in enumerate(array_imagenes[-3:]):
                   
                    x = (i % num_cols) * col_width
                    y = (i // num_cols) * row_height
                    
                    # Tamaño deseado para las imágenes (ancho x alto)
                    nuevo_ancho = 300
                    nuevo_alto = 300
                    # Lista para almacenar las referencias a las imágenes de Tkinter

                    x = 100 + (i % num_cols) * col_width
                    y = 60 + (i // num_cols) * row_height
                    
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(img)

                    # Redimensionar la imagen al tamaño deseado
                    imagen_resized = img.resize((nuevo_ancho, nuevo_alto), resample=Resampling.LANCZOS)

                    # Convertir la imagen redimensionada a PhotoImage
                    imagen_resized_tk = ImageTk.PhotoImage(imagen_resized)
                    imagenes_tk.append(imagen_resized_tk)  # Agregar la referencia a la lista

                    # Crear la imagen en la posición correcta del lienzo
                    canvas_secondary.create_image(x, y, anchor=tk.NW, image=imagen_resized_tk)
                    canvas_secondary.image = imagenes_tk  # Asignar la lista de referencias al atributo image
                
                if len(array_imagenes) >= 3:  
                    array_imagenes.pop(0)
                
              
        # Mostrar el fotograma
        tk_image = cv2_to_tkimage(frame)
        # Centrar la imagen principal en el lienzo               
        x_main = (screen_width - tk_image.width()) / 2
        y_main = (screen_height*0.6 - tk_image.height()) / 2
       
        canvas_main.create_image(x_main, y_main, anchor=tk.NW, image=tk_image)
        canvas_main.image = tk_image  

    # Llamar a esta función nuevamente después de un breve retraso
    root.after(10, detectar_rostros)

# Inicializar la captura de vídeo
cap = cv2.VideoCapture(0)

# Ruta al archivo shape_predictor_68_face_landmarks.dat
predictor_path = "shape_predictor_68_face_landmarks.dat"

# Cargar el detector de rostros
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

# Crear la ventana principal
root = tk.Tk()
root.attributes("-fullscreen", True)

# Obtener dimensiones de la ventana
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Crear un lienzo para la imagen principal
canvas_main = tk.Canvas(root, width=screen_width, height=screen_height*0.6)
canvas_main.pack()

# Crear un lienzo para las imágenes secundarias
canvas_secondary = tk.Canvas(root, width=screen_width, height=screen_height*0.4, bg="white")  # Fondo blanco
canvas_secondary.pack()

# Dividir el lienzo secundario en una cuadrícula
num_cols = 3
col_width = screen_width // num_cols
row_height = screen_height // num_cols

# Atajos de teclado para salir de pantalla completa
root.bind("<Escape>", on_exit)
root.bind("<F11>", toggle_fullscreen)  
    
# Comenzar la detección de rostros
detectar_rostros()

# Ejecutar el bucle principal
root.mainloop()

# Liberar la captura de video
cap.release()

