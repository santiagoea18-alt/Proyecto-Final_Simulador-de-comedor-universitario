import pandas as pd
from datetime import datetime
import os
import tkinter as tk
from tkinter import filedialog, Toplevel, Label
from PIL import Image, ImageTk  # Requiere: pip install Pillow
import unicodedata

def normalizar_encabezado(texto):
    if not isinstance(texto, str): return texto
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto.lower().strip()

class Estudiante:
    def _init_(self, codigo, nombre, especialidad, ubicacion, nivel):
        self.codigo = str(codigo).strip()
        self.nombre = nombre
        self.especialidad = especialidad
        self.ubicacion = str(ubicacion).strip().lower()
        self.nivel = str(nivel).strip().upper()

class SistemaComedor:
    def _init_(self, archivo_alumnos, archivo_turnos, ruta_menu):
        self.archivo_alumnos = archivo_alumnos
        self.archivo_turnos = archivo_turnos
        self.ruta_menu = ruta_menu
        self.df_alumnos = self._cargar_csv_robusto(archivo_alumnos)
        self.df_turnos = self._cargar_csv_robusto(archivo_turnos)
        
        self.horarios = {
            1: "12:00-12:15", 2: "12:15-12:30", 3: "12:30-12:45",
            4: "12:45-13:00", 5: "13:00-13:15", 6: "13:15-13:30",
            7: "13:30-13:45", 8: "13:45-14:00", 9: "14:00-14:15",
            10: "14:15-14:30"
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
            elif 'ubicacion' in norm: mapeo[col] = 'Ubicación'
            elif 'nivel' in norm: mapeo[col] = 'Nivel Socioeconómico'
            elif 'especialidad' in norm: mapeo[col] = 'Especialidad'
        return df.rename(columns=mapeo)

    def mostrar_imagen(self, ruta, titulo="Información", persistente=False):
        if not os.path.exists(ruta):
            print(f"⚠️ Imagen no encontrada en: {ruta}")
            return
        ventana_img = Toplevel()
        ventana_img.title(titulo)
        ventana_img.attributes("-topmost", True)
        try:
            img = Image.open(ruta)
            img.thumbnail((500, 500))
            img_tk = ImageTk.PhotoImage(img)
            label_img = Label(ventana_img, image=img_tk)
            label_img.image = img_tk 
            label_img.pack(padx=10, pady=10)
            if not persistente:
                ventana_img.after(4000, ventana_img.destroy)
        except Exception as e:
            print(f"❌ Error al abrir imagen: {e}")
            ventana_img.destroy()

    def ver_menu_dia(self):
        print("\n🖼️ Abriendo imagen del menú del día...")
        self.mostrar_imagen(self.ruta_menu, "Menú del Día", persistente=True)

    def mostrar_disponibilidad(self):
        print("\n--- 📊 ESTADO DE CUPOS Y HORARIOS ---")
        for i in range(1, 11):
            col = f"Turno {i}"
            if col in self.df_turnos.columns:
                libres = 100 - self.df_turnos[col].count()
                print(f"[{i}] {col} ({self.horarios[i]}): {max(0, libres)} libres")

    def verificar_horario_nivel(self, nivel):
        ahora = datetime.now()
        t = ahora.hour * 60 + ahora.minute
        # C (06:30), B (07:00), A (07:30)
        if 390 <= t < 420: return nivel == 'C'
        if 420 <= t < 450: return nivel in ['B', 'C']
        if 450 <= t <= 480: return nivel in ['A', 'B', 'C']
        return False

    def verificar_duplicado(self, codigo):
        for i in range(1, 11):
            col = f"Turno {i}"
            if col in self.df_turnos.columns:
                if str(codigo) in self.df_turnos[col].astype(str).values:
                    return col, self.horarios[i]
        return None, None

    def registrar_cupo(self):
        print("\n--- 🎫 REGISTRO DE CUPO ---")
        cod_buscado = input("🔍 Ingrese su código de estudiante: ").strip()
        
        datos = self.df_alumnos[self.df_alumnos['Código de estudiante'].astype(str) == cod_buscado]
        if datos.empty:
            print("❌ Error: Estudiante no registrado."); return

        row = datos.iloc[0]
        est = Estudiante(row['Código de estudiante'], row['Nombre Completo'], 
                         row['Especialidad'], row['Ubicación'], row['Nivel Socioeconómico'])

        # Validaciones
        dup_t, dup_h = self.verificar_duplicado(est.codigo)
        if dup_t:
            print(f"⚠️ DENEGADO: Ya tienes cupo en el {dup_t} ({dup_h})."); return

        if est.ubicacion != "dentro de la universidad":
            print(f"❌ DENEGADO: Debes estar en el campus."); return

        if not self.verificar_horario_nivel(est.nivel):
            print(f"❌ DENEGADO: Nivel {est.nivel} no puede registrarse a esta hora."); return

        print(f"\n✅ ACCESO PERMITIDO: {est.nombre}")
        self.mostrar_disponibilidad()

        try:
            op = int(input("\n👉 Seleccione el número de turno: "))
            col_sel = f"Turno {op}"
            if op not in self.horarios: raise ValueError

            mask = self.df_turnos[col_sel].isna()
            if mask.any():
                self.df_turnos.at[mask.idxmax(), col_sel] = est.codigo
            else:
                nueva = pd.DataFrame([{col_sel: est.codigo}])
                self.df_turnos = pd.concat([self.df_turnos, nueva], ignore_index=True)

            self.df_turnos.to_csv(self.archivo_turnos, index=False, encoding='utf-8-sig')
            print(f"✅ ¡ÉXITO! Registrado en {col_sel} ({self.horarios[op]})")
        except:
            print("❌ Opción de turno inválida.")

# --- INICIO DEL PROGRAMA ---
def seleccionar_ruta(titulo, tipos):
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    ruta = filedialog.askopenfilename(title=titulo, filetypes=tipos)
    root.destroy(); return ruta

if _name_ == "_main_":
    print("=== CONFIGURACIÓN INICIAL DEL SISTEMA ===")
    r_alumnos = seleccionar_ruta("Seleccione el CSV de Estudiantes", [("CSV", "*.csv")])
    r_turnos = seleccionar_ruta("Seleccione el CSV de Turnos", [("CSV", "*.csv")])
    r_menu_img = seleccionar_ruta("Seleccione la Imagen del Menú del Día", [("Imágenes", "*.png *.jpg *.jpeg")])
    
    if r_alumnos and r_turnos and r_menu_img:
        sistema = SistemaComedor(r_alumnos, r_turnos, r_menu_img)
        
        while True:
            print("\n" + "="*30)
            print("   MENÚ PRINCIPAL COMEDOR")
            print("="*30)
            print("1. Ver Menú del Día (Imagen)")
            print("2. Registrar Cupo")
            print("3. Ver Cupos Disponibles")
            print("4. Salir")
            print("="*30)
            
            opcion = input("Elija una opción (1-4): ")
            
            if opcion == "1":
                sistema.ver_menu_dia()
            elif opcion == "2":
                sistema.registrar_cupo()
            elif opcion == "3":
                sistema.mostrar_disponibilidad()
            elif opcion == "4":
                print("👋 Saliendo del sistema...")
                break
            else:
                print("❌ Opción no válida, intente de nuevo.")
    else:
        print("❌ Error: Faltan archivos para iniciar el sistema.")
            if op == "1": sistema.registrar_cupo()
            elif op == "2": sistema.mostrar_disponibilidad()
            elif op == "3": break
