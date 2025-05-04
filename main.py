import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QComboBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from fer import FER
from deepface import DeepFace
import sqlite3
from datetime import datetime, timedelta
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from tkcalendar import DateEntry  # Usando tkcalendar para el selector de fechas
import csv
from openpyxl import Workbook
from openpyxl.styles import Font, Color, PatternFill
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Base de datos SQLite
DB_NAME = "emociones.db"

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emociones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emocion TEXT,
        porcentaje REAL,
        fecha_hora TEXT,
        fecha TEXT,
        imagen_path TEXT
    )''')
    conn.commit()
    conn.close()

# Guardar resultados en SQLite
def guardar_resultado_sqlite(emocion, porcentaje):
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO emociones (emocion, porcentaje, fecha_hora, fecha) VALUES (?, ?, ?, ?)",
              (emocion, round(porcentaje * 100, 2), fecha_hora, fecha))
    conn.commit()
    conn.close()

def guardar_resultado_con_imagen(emocion, porcentaje, imagen_path=None):
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO emociones (emocion, porcentaje, fecha_hora, fecha, imagen_path)
        VALUES (?, ?, ?, ?, ?)
    """, (emocion, round(porcentaje * 100, 2), fecha_hora, fecha, imagen_path))
    conn.commit()
    conn.close()

# Función para buscar emociones por fecha
def buscar_emociones_por_fecha(inicio, fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Convertir las fechas a formato de cadena compatible con SQLite
    inicio_str = inicio.strftime('%Y-%m-%d')
    fin_str = fin.strftime('%Y-%m-%d')
    
    c.execute("SELECT emocion, porcentaje, fecha_hora FROM emociones WHERE imagen_path is NULL and fecha BETWEEN ? AND ?", (inicio_str, fin_str))
    resultados = c.fetchall()
    conn.close()
    return resultados

# Configuración para guardar las imágenes
image_save_folder = "capturas_tristeza"  # Carpeta donde se guardarán las capturas
if not os.path.exists(image_save_folder):
    os.makedirs(image_save_folder)  # Crear la carpeta si no existe

# Función para guardar la imagen cuando se detecta la emoción
def guardar_imagen_tristeza(frame):
    # Crear un nombre único para la imagen con la fecha y hora actual
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = os.path.join(image_save_folder, f"tristeza_{timestamp}.jpg")
    
    # Guardar la imagen
    cv2.imwrite(image_filename, frame)
    print(f"Imagen guardada como {image_filename}")
    return image_filename

# Función para exportar los resultados a un archivo CSV
def exportar_a_csv():
    try:
        # Obtener el texto de la caja de resultados
        data = resultado_text.get("1.0", tk.END).strip().split("\n")
        
        if not data:
            messagebox.showwarning("Advertencia", "No hay datos para exportar.")
            return
        
        # Abrir un cuadro de diálogo para que el usuario elija la ubicación y el nombre del archivo
        archivo_guardado = filedialog.asksaveasfilename(
            defaultextension=".csv", 
            filetypes=[("Archivos CSV", "*.csv")],
            title="Guardar archivo CSV"
        )
        
        if archivo_guardado:  # Si el usuario elige una ubicación
            # Abrir el archivo CSV en modo de escritura
            with open(archivo_guardado, mode="w", newline='') as archivo:
                writer = csv.writer(archivo)
                
                # Escribir los encabezados del CSV
                writer.writerow(["Emoción", "Porcentaje", "FechaHora"])
                
                # Escribir cada línea de datos (ignoramos la primera línea vacía o de encabezado)
                for line in data:
                    if line:
                        parts = line.split(", ")
                        emocion = parts[0].replace("Emoción: ", "")
                        porcentaje = parts[1].replace("Porcentaje: ", "").replace("%", "")
                        fecha_hora = parts[2].replace("Fecha: ", "")
                        writer.writerow([emocion, porcentaje, fecha_hora])
            
            messagebox.showinfo("Éxito", "Datos exportados correctamente.")
        else:
            messagebox.showwarning("Advertencia", "No se seleccionó ninguna ubicación para guardar el archivo.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al exportar los datos: {str(e)}")
        
def exportar_a_excel():
    try:
        # Obtener el texto de la caja de resultados
        data = resultado_text.get("1.0", tk.END).strip().split("\n")
        
        if not data:
            messagebox.showwarning("Advertencia", "No hay datos para exportar.")
            return
        
        # Preparar los datos para el DataFrame de pandas
        rows = []
        for line in data:
            if line:
                parts = line.split(", ")
                emocion = parts[0].replace("Emoción: ", "")
                porcentaje = parts[1].replace("Porcentaje: ", "").replace("%", "")
                fecha_hora = parts[2].replace("Fecha: ", "")
                rows.append([emocion, porcentaje, fecha_hora])
        
        # Crear un DataFrame de pandas
        df = pd.DataFrame(rows, columns=["Emoción", "Porcentaje", "FechaHora"])

        # Abrir un cuadro de diálogo para que el usuario elija la ubicación y el nombre del archivo
        archivo_guardado = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Archivos Excel", "*.xlsx")],
            title="Guardar archivo Excel"
        )
        
        if archivo_guardado:  # Si el usuario elige una ubicación
            # Crear un libro de trabajo (workbook) con openpyxl
            wb = Workbook()
            ws = wb.active
            ws.title = "Emociones"

            # Escribir los encabezados de columna en mayúsculas y con color de fondo
            headers = ["Emoción", "Porcentaje", "FechaHora"]
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num, value=header.upper())  # Títulos en mayúsculas
                cell.font = Font(bold=True)  # Negrita
                cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")  # Fondo amarillo

            # Escribir los datos en las celdas
            for row_num, row in enumerate(df.itertuples(index=False, name=None), 2):
                for col_num, value in enumerate(row, 1):
                    ws.cell(row=row_num, column=col_num, value=value)

            # Guardar el archivo Excel
            wb.save(archivo_guardado)
            
            messagebox.showinfo("Éxito", "Datos exportados correctamente.")
        else:
            messagebox.showwarning("Advertencia", "No se seleccionó ninguna ubicación para guardar el archivo.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al exportar los datos: {str(e)}")

# Iniciar la interfaz de búsqueda de fechas con Tkinter
def iniciar_gui_tkinter():
    def buscar_por_fecha():
        try:
            # Convertir las entradas a tipo datetime
            fecha_inicio = pd.to_datetime(entry_inicio.get())
            fecha_fin = pd.to_datetime(entry_fin.get())

            # Llamar la función para obtener los resultados
            resultados = buscar_emociones_por_fecha(fecha_inicio, fecha_fin)

            resultado_text.delete("1.0", tk.END)  # Limpiar el campo de texto antes de mostrar los nuevos resultados
            if not resultados:
                resultado_text.insert(tk.END, "No hay resultados en ese rango.")
            else:
                # Mostrar los resultados
                for row in resultados:
                    emocion, porcentaje, fecha_hora = row
                    resultado_text.insert(tk.END, f"Emoción: {emocion}, Porcentaje: {porcentaje}%, Fecha: {fecha_hora}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar las fechas.\n{str(e)}")

    ventana = tk.Tk()
    ventana.title("Buscar emociones por fecha")
    ventana.geometry("600x500")

    ttk.Label(ventana, text="Fecha Inicio:").pack(pady=5)
    global entry_inicio
    entry_inicio = DateEntry(ventana, date_pattern='yyyy-mm-dd')
    entry_inicio.pack()

    ttk.Label(ventana, text="Fecha Fin:").pack(pady=5)
    global entry_fin
    entry_fin = DateEntry(ventana, date_pattern='yyyy-mm-dd')
    entry_fin.pack()

    ttk.Button(ventana, text="Buscar", command=buscar_por_fecha).pack(pady=10)

    # Crear un frame para contener la barra de desplazamiento y el widget de texto
    frame = ttk.Frame(ventana)
    frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    # Crear el widget de Scrollbar
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Crear el widget de Text
    global resultado_text
    resultado_text = tk.Text(frame, height=15, width=70)
    resultado_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Asociar el Scrollbar con el Text widget
    scrollbar.config(command=resultado_text.yview)
    resultado_text.config(yscrollcommand=scrollbar.set)

    # Crear el botón de Exportar a CSV
    # export_button = ttk.Button(ventana, text="Exportar a CSV", command=exportar_a_csv)
    export_button = ttk.Button(ventana, text="Exportar a EXCEL", command=exportar_a_excel)
    export_button.pack(pady=10)

    ventana.mainloop()
    
# Función para enviar correo electrónico
def enviar_correo(subject, body, to_email):
    # Configuración de correo
    from_email = "richardalvarezruiz.1997@gmail.com"  # Tu correo de Gmail
    password = "kobh lpxw mzcf vwqb"  # Tu contraseña de Gmail o contraseña de aplicación

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)

        mensaje = MIMEMultipart()
        mensaje["From"] = from_email
        mensaje["To"] = to_email
        mensaje["Subject"] = subject
        mensaje.attach(MIMEText(body, "plain"))

        server.sendmail(from_email, to_email, mensaje.as_string())
        print("Correo enviado correctamente.")
    except smtplib.SMTPAuthenticationError as e:
            print("Error de autenticación SMTP:", e)
    except Exception as e:
            print("Error enviando el correo:", e)
    finally:
            server.quit()
    
def verificar_y_enviar_correo(emotion, porcentaje):
    if emotion in ['sad', 'fear', 'angry', 'disgust']:
        subject = "⚠️ Alerta: Emoción Negativa Detectada"
        body = f"Se ha detectado una emoción negativa: {emotion.capitalize()}.\n\nPorcentaje: {porcentaje * 100:.2f}%"
        to_email = "gianella.taboada@gmail.com"  # Correo a donde se enviará la alerta
        enviar_correo(subject, body, to_email)
        print(f"Correo enviado:")

# Mostrar gráfico de emociones
class EmotionHistoryPlot(QWidget):
    def __init__(self):
        super().__init__()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_plot(self, emotions_count):
        self.ax.clear()
        emotions = list(emotions_count.keys())
        counts = list(emotions_count.values())

        self.ax.bar(emotions, counts, color='skyblue')
        self.ax.set_ylabel('Frecuencia')
        self.ax.set_title('Historial de Emociones')

        for i, count in enumerate(counts):
            self.ax.text(i, count, f'({count})', ha='center', va='bottom')

        self.canvas.draw()

# Clase principal de la aplicación PyQt5
class DepressionDetector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detección de Conductas Depresivas")
        self.setGeometry(200, 200, 1500, 600)

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.start_button = QPushButton("Iniciar Detección", self)
        self.start_button.clicked.connect(self.start_detection)

        self.search_button = QPushButton("Buscar por Fecha", self)
        self.search_button.clicked.connect(self.abrir_busqueda_por_fecha)

        self.model_selector = QComboBox(self)
        self.model_selector.addItem("FER")
        self.model_selector.addItem("DeepFace")

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Selecciona el modelo:"))
        left_layout.addWidget(self.model_selector)
        left_layout.addWidget(self.video_label)
        left_layout.addWidget(self.start_button)
        left_layout.addWidget(self.search_button)

        stats_layout = QVBoxLayout()
        self.dominant_emotion_label = QLabel("Emociones Dominantes: ", self)
        stats_layout.addWidget(self.dominant_emotion_label)

        self.average_emotion_label = QLabel("Promedio de Emociones: ", self)
        stats_layout.addWidget(self.average_emotion_label)

        self.alert_label = QLabel("", self)
        stats_layout.addWidget(self.alert_label)

        self.emotion_history_plot = EmotionHistoryPlot()
        stats_layout.addWidget(self.emotion_history_plot)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(stats_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.all_list_emotions = {
            'sad': 'Tristeza', 'fear': 'Miedo', 'angry': 'Enojo', 'disgust': 'Desprecio',
            'happy': 'Feliz', 'surprise': 'Sorpresa', 'neutral': 'Neutral'
        }
        self.depressive_emotions = {
            'sad': 'Tristeza', 'fear': 'Miedo', 'angry': 'Enojo', 'disgust': 'Desprecio'
        }
        
        self.ultima_captura_tristeza = datetime.min  # Inicializa con la fecha mínima posible
        self.intervalo_captura = timedelta(seconds=2) # Intervalo de tiempo en segundos entre capturas

        self.fer_detector = FER()
        self.emotion_history = []
        self.emotions_count = {emotion: 0 for emotion in self.all_list_emotions.values()}
        self.negative_emotion_history = []
        self.max_history_size = 100

    def start_detection(self):
        self.timer.start(100)

    def abrir_busqueda_por_fecha(self):
        threading.Thread(target=iniciar_gui_tkinter).start()

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        selected_model = self.model_selector.currentText()
        emotions_count = {emotion: 0 for emotion in self.all_list_emotions.values()}

        if selected_model == "FER":
            faces = self.fer_detector.detect_emotions(rgb_image)
            if len(faces) == 0:
                return 
            for face in faces:
                (x, y, w, h) = face["box"]
                emociones = face["emotions"]
                emotion = max(emociones, key=emociones.get)
                porcentaje = emociones[emotion]
                
                if w < 50 or h < 50:
                    continue  # Ignora regiones demasiado pequeñas
                    
                if porcentaje >= 0.60:
                    
                    if emotion in ['sad', 'fear', 'angry', 'disgust']:  # Si detecta emoción triste
                        # Enviar correo
                        verificar_y_enviar_correo(emotion, porcentaje)
                
                    if emotion == 'sad' or emotion == 'fear' or emotion == 'angry' or emotion == 'disgust':
                        ahora = datetime.now()
                        if ahora - self.ultima_captura_tristeza > self.intervalo_captura:
                            imagen_path = guardar_imagen_tristeza(frame)
                            guardar_resultado_con_imagen(emotion, porcentaje, imagen_path)
                            self.ultima_captura_tristeza = ahora
                    # else:
                    #     guardar_resultado_con_imagen(emotion, porcentaje, None)
                    
                    if emotion in self.depressive_emotions:
                        color = (255, 0, 0)
                        emocion_cast = self.depressive_emotions[emotion]
                    else:
                        color = (0, 255, 0)
                        emocion_cast = emotion
                    cv2.rectangle(rgb_image, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(rgb_image, f"{emocion_cast}: {porcentaje*100:.2f}%", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                    if emocion_cast in emotions_count:
                        emotions_count[emocion_cast] += 1
                    
                    if emotion == 'sad' or emotion == 'fear' or emotion == 'angry' or emotion == 'disgust':
                        guardar_resultado_sqlite(emocion_cast, porcentaje)

        elif selected_model == "DeepFace":
            # result = DeepFace.analyze(rgb_image, actions=['emotion'], enforce_detection=True)
            # faces = result if isinstance(result, list) else [result]
            # for face_info in faces:
            #     emotion = face_info['dominant_emotion']
            #     porcentaje = face_info['emotion'][emotion] / 100
            #     region = face_info.get('region', {'x': 0, 'y': 0, 'w': 0, 'h': 0})
            #     x, y, w, h = region['x'], region['y'], region['w'], region['h']
            #     emocion_cast = self.all_list_emotions.get(emotion, emotion)

            #     # if w < 50 or h < 50:
            #     #     continue 
                
            #     color = (255, 0, 0) if emotion in self.depressive_emotions else (0, 255, 0)
            #     cv2.rectangle(rgb_image, (x, y), (x + w, y + h), color, 2)
            #     cv2.putText(rgb_image, emocion_cast, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            #     emotions_count[emocion_cast] += 1
            #     guardar_resultado_sqlite(emocion_cast, porcentaje)
            try:
                result = DeepFace.analyze(rgb_image, actions=['emotion'], enforce_detection=True)
            except ValueError as e:
                # print("No se detectó una cara en este frame. Frame descartado.")
                # return  # Salta este frame
                print("No se detectó una cara en este frame. Mostrando sin análisis.")
                height, width, channel = rgb_image.shape
                qimg = QImage(rgb_image.data, width, height, 3 * width, QImage.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(qimg))
                return

            faces = result if isinstance(result, list) else [result]
            for face_info in faces:
                emotion = face_info['dominant_emotion']
                porcentaje = face_info['emotion'][emotion] / 100
                porcentaje2 = face_info['emotion'][emotion]
                region = face_info.get('region', {'x': 0, 'y': 0, 'w': 0, 'h': 0})
                x, y, w, h = region['x'], region['y'], region['w'], region['h']
                emocion_cast = self.all_list_emotions.get(emotion, emotion)
                
                if w < 100 or h < 100:
                    continue 
                
                if porcentaje <= 0.60:
                    return
                
                print("Prueba de porcentaje", porcentaje2)
                color = (255, 0, 0) if emotion in self.depressive_emotions else (0, 255, 0)
                cv2.rectangle(rgb_image, (x, y), (x + w, y + h), color, 2)
                # cv2.putText(rgb_image, emocion_cast, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                cv2.putText(rgb_image, f"{emocion_cast}: {porcentaje*100:.2f}%", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                emotions_count[emocion_cast] += 1
                guardar_resultado_sqlite(emocion_cast, porcentaje)

        # Mostrar en GUI
        height, width, channel = rgb_image.shape
        qimg = QImage(rgb_image.data, width, height, 3 * width, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

        for emotion, count in emotions_count.items():
            if emotion in self.emotions_count:
                self.emotions_count[emotion] += count

        if emotions_count:
            emotions_to_remove = ['Neutral', 'Feliz', 'Sorpresa']
            filtered_emotions = {k: v for k, v in self.emotions_count.items() if k not in emotions_to_remove}
            sorted_emotions = dict(sorted(filtered_emotions.items(), key=lambda item: item[1], reverse=True))
            dominant_emotions_text = "\n".join([f"{emotion}: {count}" for emotion, count in sorted_emotions.items()])
            self.dominant_emotion_label.setText(f"Emociones Dominantes:\n{dominant_emotions_text}")

            emotion_values = {
                'Tristeza': -1.0, 'Miedo': -1.0, 'Enojo': -1.0, 'Desprecio': -1.0,
                'Feliz': 1.0, 'Sorpresa': 1.0, 'Neutral': 0.0
            }
            total_emotions_value = sum(emotion_values.get(e, 0) * c for e, c in emotions_count.items())
            average_emotion = total_emotions_value / sum(emotions_count.values()) if sum(emotions_count.values()) else 0
            self.average_emotion_label.setText(f"Promedio de Emociones: {average_emotion:.2f}")

            self.negative_emotion_history.append(average_emotion)
            if len(self.negative_emotion_history) > self.max_history_size:
                self.negative_emotion_history.pop(0)
            smoothed_avg = sum(self.negative_emotion_history) / len(self.negative_emotion_history)
            self.alert_label.setText("Alerta: Predominan emociones negativas." if smoothed_avg < 0 else "")

            self.emotion_history_plot.update_plot(filtered_emotions)

    def closeEvent(self, event):
        self.cap.release()
        self.timer.stop()
        event.accept()

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = DepressionDetector()
    window.show()
    print("Script terminado correctamente.")
    sys.exit(app.exec_())
