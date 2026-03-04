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
        
        inicio = 0      # 06:30
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
        """Busca si el código ya existe en cualquiera de las columnas de turnos."""
        for i in range(1, 11):
            col = f"Turno {i}"
            if col in self.df_turnos.columns:
                # Comparamos como string para evitar errores de tipo
                if codigo in self.df_turnos[col].astype(str).values:
                    return col
        return None

    def mostrar_disponibilidad(self):
        print("\n--- 📊 DISPONIBILIDAD ACTUAL DE TURNOS ---")
        for i in range(1, 11):
            col = f"Turno {i}"
            if col in self.df_turnos.columns:
                ocupados = self.df_turnos[col].count()
                libres = max(0, 100 - ocupados)
                print(f"[{i}] {col}: {libres} cupos libres")

    def registrar_cupo(self):
        print("\n--- 🎫 REGISTRO DE CUPO ---")
        codigo_buscado = input("🔍 Ingrese código de estudiante: ").strip()
        
        # 1. Buscar Estudiante
        datos = self.df_alumnos[self.df_alumnos['Código de estudiante'].astype(str) == codigo_buscado]
        if datos.empty:
            print("❌ Error: Estudiante no encontrado en la base de datos.")
            return

        row = datos.iloc[0]
        est = Estudiante(row['Código de estudiante'], row['Nombre Completo'], 
                         row['Especialidad'], row['Ubicación'], row['Nivel Socioeconómico'])

        # 2. VALIDACIÓN DE REGISTRO ÚNICO (NUEVA)
        turno_existente = self.verificar_duplicado(est.codigo)
        if turno_existente:
            print(f"⚠️ DENEGADO: El estudiante {est.nombre} ya tiene un cupo en el {turno_existente}.")
            print("Solo se permite un registro por persona al día.")
            return

        # 3. Validaciones de Ubicación y Horario
        if not est.esta_en_universidad():
            print(f"❌ Denegado: {est.nombre} debe estar DENTRO de la universidad.")
            return

        if not self.verificar_horario_nivel(est.nivel):
            print(f"❌ Denegado: El nivel {est.nivel} no tiene acceso a las {datetime.now().strftime('%H:%M')}.")
            return

        # 4. Mostrar disponibilidad y selección
        print(f"\n✅ Bienvenido, {est.nombre} (Nivel {est.nivel})")
        self.mostrar_disponibilidad()

        try:
            op = input("\n👉 Seleccione el NÚMERO del turno deseado: ").strip()
            if not op.isdigit():
                print("❌ Error: Debe ingresar solo el número.")
                return
            
            op = int(op)
            col_sel = f"Turno {op}"
            
            if col_sel not in self.df_turnos.columns:
                print(f"❌ Error: El turno {op} no existe.")
                return

            # Lógica de registro
            mask_vacia = self.df_turnos[col_sel].isna()
            if mask_vacia.any():
                idx = mask_vacia.idxmax()
                self.df_turnos.at[idx, col_sel] = est.codigo
            else:
                nueva_fila = pd.DataFrame([{col_sel: est.codigo}])
                self.df_turnos = pd.concat([self.df_turnos, nueva_fila], ignore_index=True)

            # 5. Guardado
            self.df_turnos.to_csv(self.archivo_turnos, index=False, encoding='utf-8-sig')
            print(f"✅ ¡REGISTRO EXITOSO! {est.nombre} asignado al {col_sel}.")

        except Exception as e:
            print(f"❌ Error durante el registro: {e}")

def obtener_ruta(titulo):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    print(f"📂 Seleccionando: {titulo}...")
    ruta = filedialog.askopenfilename(title=titulo, filetypes=[("Archivos CSV", "*.csv")])
    root.destroy()
    if not ruta: exit()
    return ruta

if __name__ == "__main__":
    print("=== SISTEMA DE COMEDOR UNIVERSITARIO v5.0 ===")
    r_alum = obtener_ruta("Seleccione archivo de ALUMNOS")
    r_turn = obtener_ruta("Seleccione archivo de TURNOS")
    
    sistema = SistemaComedor(r_alum, r_turn)

    while True:
        print("\n--- MENÚ PRINCIPAL ---")
        print("1. Iniciar Proceso de Registro")
        print("2. Ver Disponibilidad de Cupos")
        print("3. Salir")
        opcion = input("Elija una opción: ")
        if opcion == "1": sistema.registrar_cupo()
        elif opcion == "2": sistema.mostrar_disponibilidad()
        elif opcion == "3": break
