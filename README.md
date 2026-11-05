# SystemBioTrack ⏱
**Sistema de Control de Asistencia Biométrico (ISAPI/HTTP)**


Plataforma Fullstack para automatizar, registrar y auditar la asistencia del personal mediante la integración en tiempo real con un reloj biométrico Hikvision (protocolo ISAPI/HTTP).


---

##  Stack Tecnológico
* **Frontend:** React + Vite (JavaScript)
* **Backend:** FastAPI (Python)
* **Base de Datos:** PostgreSQL 16

##  Equipo y Módulos
* **Módulo 1: Autenticación y Roles** — Ricardo
* **Módulo 2: Personal y Horarios** — Jhon
* **Módulo 3: Motor Biométrico (Core)** — Pablo
* **Módulo 4: Permisos y Justificativos** — Yandro
* **Módulo 5: Dashboard y Reportes** — Norielys

---

##  Guía Paso a Paso: Configuración Inicial (Primera vez tras clonar)

Abre la terminal en Visual Studio Code y ejecuta los comandos en el siguiente orden:

### Paso 1: Clonar el repositorio y entrar al proyecto
git clone [https://github.com/Jhonmcr/SystemBioTrack-ETI.git]
cd SystemBioTrack-ETI

### Paso 2: Configurar el Frontend (React)
# 1. Entrar a la carpeta del frontend
cd frontend

# 2. Instalar las dependencias de JavaScript
npm install

# 3. Volver a la raíz del proyecto
cd ..

### Paso 3: Configurar el Backend (FastAPI)
# 1. Entrar a la carpeta del backend
cd backend

# 2. Crear el entorno virtual (la burbuja de Python)
python -m venv venv

# 3. Activar el entorno virtual (En Windows)
venv\Scripts\activate
# (Si estás en Mac/Linux usa: source venv/bin/activate)

# 4. Instalar las librerías de Python
pip install -r requirements.txt

# 5. Volver a la raíz del proyecto
cd ..


### Rutina Diaria de Trabajo (Cómo encender el proyecto cada día)

### Terminal 1: Para la interfaz visual (Frontend)
cd frontend
npm run dev

### Terminal 2: Para el servidor de datos (Backend)
cd backend
venv\Scripts\activate
uvicorn main:app --reload