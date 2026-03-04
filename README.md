# 🍽️ Sistema Inteligente de Gestión de Comedor Universitario

## 📖 Descripción

Este proyecto implementa un sistema digital para la gestión eficiente de cupos en un comedor universitario.  

El sistema controla el acceso de estudiantes en la franja crítica de 6:30 a.m. a 8:00 a.m., valida su presencia dentro del campus y permite la asignación dinámica de turnos con visualización en tiempo real de los cupos disponibles.

Su objetivo es reducir colas innecesarias, evitar conflictos con horarios académicos y garantizar una distribución equitativa del servicio.

---

## 🚀 Características Principales

- ✔ Registro automatizado por código de estudiante
- ✔ Validación de ubicación (dentro / fuera del campus)
- ✔ Control de acceso por nivel socioeconómico y horario
- ✔ Prevención de registros duplicados
- ✔ Visualización de cupos disponibles por turno
- ✔ Persistencia de datos en archivos CSV
- ✔ Carga robusta de archivos (detección automática de separador y codificación)
- ✔ Implementación con Programación Orientada a Objetos

---

## 🏗️ Arquitectura del Sistema

El proyecto está dividido en dos módulos principales:

### 1️⃣ Sistema de Asistencia
- Controla el flujo de ingreso y salida del estudiante.
- Actualiza su estado en tiempo real.
- Garantiza que solo estudiantes dentro del campus puedan acceder al comedor.

### 2️⃣ Sistema de Comedor
- Verifica identidad del estudiante.
- Aplica política de acceso por nivel socioeconómico y horario.
- Permite seleccionar turno disponible.
- Registra el cupo y actualiza la base de datos.

---

## 🛠️ Tecnologías Utilizadas

- Python 3
- Pandas
- Tkinter (selección de archivos)
- Manejo robusto de CSV
- Programación Orientada a Objetos (POO)

---

## 📂 Requisitos

Instalar dependencias necesarias:

```bash
pip install pandas
pip install Pillow
