import pandas as pd
from datetime import datetime
import os
import tkinter as tk
from tkinter import filedialog
import unicodedata

def normalizar_encabezado(texto):
    """Elimina tildes, espacios y normaliza nombres de columnas."""
    if not isinstance(texto, str): return texto
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto.lower().strip()

class Estudiante:
    def __init__(self, codigo, nombre, especialidad, ubicacion, nivel):
        self.codigo = str(codigo).strip()
        self.nombre = nombre
        self.especialidad = especialidad
        self.ubicacion = str(ubicacion).strip().lower()
        self.nivel = str(nivel).strip().upper()

    def esta_en_universidad(self):
        return self.ubicacion == "dentro de la universidad"

class SistemaComedor:
    def __init__(self, archivo_alumnos, archivo_turnos):
        self.archivo_alumnos = archivo_alumnos
        self.archivo_turnos = archivo_turnos
        self.df_alumnos = self._cargar_csv_robusto(archivo_alumnos)
        self.df_turnos = self._cargar_csv_robusto(archivo_turnos)
        
        # Diccionario de horarios por turno
        self.horarios = {
            1: "12:00 - 12:15", 2: "12:15 - 12:30", 3: "12:30 - 12:45",
            4: "12:45 - 13:00", 5: "13:00 - 13:15", 6: "13:15 - 13:30",
            7: "13:30 - 13:45", 8: "13:45 - 14:00", 9: "14:00 - 14:15",
            10: "14:15 - 14:30"
        }

    def _cargar_csv_robusto(self, ruta):
        try:
            df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(ruta, sep=None, engine='python', encoding='latin1')
        
        mapeo = {}
        for col in df.columns:
            norm = normalizar_encabezado(col)
            if 'codigo' in norm: mapeo[col] = 'Código de estudiante'
            elif 'nombre' in norm: mapeo[col] = 'Nombre Completo'
            elif 'especialidad' in norm: mapeo[col] = 'Especialidad'
            elif 'ubicacion' in norm: mapeo[col] = 'Ubicación'
            elif 'nivel' in norm: mapeo[col] = 'Nivel Socioeconómico'
        
        return df.rename(columns=mapeo)

    def verificar_horario_nivel(self, nivel):
        ahora = datetime.now()
        tiempo_actual = ahora.hour * 60 + ahora.minute
        
        # Horarios de registro (mañana)
        inicio = 6 * 60 + 30      # 06:30
        bloque_bc = 7 * 60        # 07:00
        bloque_abc = 7 * 60 + 30  # 07:30
        fin = 8 * 60              # 08:00

        if inicio <= tiempo_actual < bloque_bc:
            return nivel == 'C'
        elif bloque_bc <= tiempo_actual < bloque_abc:
            return nivel in ['B', 'C']
        elif bloque_abc <= tiempo_actual <= fin:
            return nivel in ['A', 'B', 'C']
        return False

    def verificar_duplicado(self, codigo):
        for i in range(1, 11):
            col = f"Turno {i}"
            if col in self.df_turnos.columns:
                if codigo in self.df_turnos[col].astype(str).values:
                    return col, self.horarios[i]
        return None, None

    def mostrar_disponibilidad(self):
        print("\n--- 📊 DISPONIBILIDAD Y HORARIOS DE COMEDOR ---")
        for i in range(1, 11):
            col = f"Turno {i}"
            horario = self.horarios[i]
            if col in self.df_turnos.columns:
                ocupados = self.df_turnos[col].count()
                libres = max(0, 100 - ocupados)
                print(f"[{i}] {col} ({horario}): {libres} cupos libres")

    def registrar_cupo(self):
        print("\n--- 🎫 PROCESO DE REGISTRO ---")
        codigo_buscado = input("🔍 Ingrese código de estudiante: ").strip()
        
        datos = self.df_alumnos[self.df_alumnos['Código de estudiante'].astype(str) == codigo_buscado]
        if datos.empty:
            print("❌ Error: Estudiante no encontrado.")
            return

        row = datos.iloc[0]
        est = Estudiante(row['Código de estudiante'], row['Nombre Completo'], 
                         row['Especialidad'], row['Ubicación'], row['Nivel Socioeconómico'])

        # Validación de duplicado
        turno_ya, hora_ya = self.verificar_duplicado(est.codigo)
        if turno_ya:
            print(f"⚠️ DENEGADO: {est.nombre} ya está registrado en el {turno_ya} ({hora_ya}).")
            return

        if not est.esta_en_universidad():
            print(f"❌ Denegado: {est.nombre} debe estar DENTRO del campus.")
            return

        if not self.verificar_horario_nivel(est.nivel):
            print(f"❌ Denegado: Su nivel ({est.nivel}) aún no tiene permiso de acceso.")
            return

        print(f"\n✅ Acceso permitido: {est.nombre}")
        self.mostrar_disponibilidad()

        try:
            op = input("\n👉 Seleccione el NÚMERO del turno deseado: ").strip()
            if not op.isdigit():
                print("❌ Error: Ingrese solo el número.")
                return
            
            op = int(op)
            if op not in self.horarios:
                print("❌ Error: Turno inválido.")
                return

            col_sel = f"Turno {op}"
            horario_sel = self.horarios[op]

            mask_vacia = self.df_turnos[col_sel].isna()
            if mask_vacia.any():
                idx = mask_vacia.idxmax()
                self.df_turnos.at[idx, col_sel] = est.codigo
            else:
                nueva_fila = pd.DataFrame([{col_sel: est.codigo}])
                self.df_turnos = pd.concat([self.df_turnos, nueva_fila], ignore_index=True)

            self.df_turnos.to_csv(self.archivo_turnos, index=False, encoding='utf-8-sig')
            
            print("\n" + "="*40)
            print(f"✅ ¡REGISTRO EXITOSO!")
            print(f"👤 Estudiante: {est.nombre}")
            print(f"🍽️ Turno: {op}")
            print(f"⏰ Horario de Comedor: {horario_sel}")
            print("="*40)

        except Exception as e:
            print(f"❌ Error: {e}")

def obtener_ruta(titulo):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    print(f"📂 Seleccionando: {titulo}...")
    ruta = filedialog.askopenfilename(title=titulo, filetypes=[("Archivos CSV", "*.csv")])
    root.destroy()
    return ruta

if __name__ == "__main__":
    r_alum = obtener_ruta("Archivo de ESTUDIANTES")
    r_turn = obtener_ruta("Archivo de TURNOS")
    if r_alum and r_turn:
        sistema = SistemaComedor(r_alum, r_turn)
        while True:
            print("\n1. Registrar Cupo\n2. Ver Disponibilidad\n3. Salir")
            op = input("Opción: ")
            if op == "1": sistema.registrar_cupo()
            elif op == "2": sistema.mostrar_disponibilidad()
            elif op == "3": break
