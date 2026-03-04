import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog

class Estudiante:
    def __init__(self, codigo, nombre, especialidad, ubicacion, nivel_socio):
        self.codigo = str(codigo).strip()
        self.nombre = nombre
        self.especialidad = especialidad
        self.ubicacion = str(ubicacion).strip().lower()
        self.nivel_socio = nivel_socio

    def alternar_ubicacion(self):
        estados = {
            "dentro de la universidad": "fuera de la universidad",
            "fuera de la universidad": "dentro de la universidad"
        }
        self.ubicacion = estados.get(self.ubicacion, "fuera de la universidad")
        return self.ubicacion

    def to_dict(self):
        return {
            'Código de estudiante': self.codigo,
            'Nombre Completo': self.nombre,
            'Especialidad': self.especialidad,
            'Ubicación': self.ubicacion,
            'Nivel Socioeconómico': self.nivel_socio
        }

class GestorAsistencia:
    def __init__(self):
        self.estudiantes = []
        self.archivo_origen = ""

    def seleccionar_archivo(self):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        path = filedialog.askopenfilename(
            title="Seleccione el archivo de estudiantes",
            filetypes=[("Archivos CSV", "*.csv")]
        )
        root.destroy()

        if path:
            try:
                # Intentar detectar el separador y la codificación
                # Usamos sep=None y engine='python' para que Pandas adivine si es ',' o ';'
                try:
                    df = pd.read_csv(path, sep=None, engine='python', encoding='utf-8')
                except:
                    df = pd.read_csv(path, sep=None, engine='python', encoding='latin1')

                # LIMPIEZA CRÍTICA: Quitar espacios en blanco de los nombres de las columnas
                df.columns = df.columns.str.strip()

                # Mostrar las columnas detectadas para ayudar al usuario si falla
                print(f"📋 Columnas encontradas: {list(df.columns)}")

                self.archivo_origen = path
                self.estudiantes = [
                    Estudiante(
                        row['Código de estudiante'], 
                        row['Nombre Completo'], 
                        row['Especialidad'], 
                        row['Ubicación'], 
                        row['Nivel Socioeconómico']
                    )
                    for _, row in df.iterrows()
                ]
                print(f"✅ Éxito: {len(self.estudiantes)} estudiantes cargados.")
                return True
            except KeyError as e:
                print(f"❌ Error: No se encontró la columna {e}")
                print("👉 Asegúrate de que el CSV tenga exactamente: 'Código de estudiante', 'Nombre Completo', etc.")
                return False
            except Exception as e:
                print(f"❌ Error al procesar el archivo: {e}")
                return False
        return False

    def registrar_flujo(self):
        print("\n--- MODO DE REGISTRO ACTIVO (Escriba 'salir') ---")
        while True:
            cod = input("\n🔍 Ingrese código: ").strip()
            if cod.lower() == 'salir': break
                
            est = next((e for e in self.estudiantes if e.codigo == cod), None)
            if est:
                nuevo_estado = est.alternar_ubicacion()
                self.guardar_datos()
                print(f"✨ REGISTRO: {est.nombre} -> {nuevo_estado.upper()}")
            else:
                print(f"❌ Código '{cod}' no registrado.")

    def guardar_datos(self):
        df_final = pd.DataFrame([e.to_dict() for e in self.estudiantes])
        dir_name = os.path.dirname(self.archivo_origen)
        nombre_salida = os.path.join(dir_name, f"updated_{os.path.basename(self.archivo_origen)}")
        df_final.to_csv(nombre_salida, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    app = GestorAsistencia()
    if app.seleccionar_archivo():
        app.registrar_flujo()
