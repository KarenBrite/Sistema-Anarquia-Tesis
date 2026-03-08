# Tesis Final | Práctica Profesionalizante II

🍸 Sistema de Gestión - Anarquía Gin
+ Estudiantes: Brite Karen, Robert Lara y Mariana Salazar

Este proyecto es un sistema de gestión de stock y ventas desarrollado en Django con base de datos MySQL.

🚀 Guía de Instalación y Despliegue
# Clonación del Proyecto
Primero, cloná tu repositorio y entrá a la carpeta:
git clone https://github.com/KarenBrite/Sistema-Anarquia-Tesis.git

## Creación del entorno virtual
Para aislar las librerías del proyecto, ejecutá:
python -m venv venv

### Activación del entorno virtual
Activá el entorno según tu sistema:
+ En Windows:
.\venv\Scripts\activate
+ En Unix o macOS:
source venv/bin/activate

#### Instalación de requerimientos
Instalá las dependencias necesarias:
pip install -r requirements.txt
pip install setuptools

##### Migraciones de la Base de Datos
Prepará las tablas de la base de datos MySQL:
python manage.py makemigrations
python manage.py migrate

###### Ejecución del servidor
Iniciá el servidor de desarrollo:
python manage.py runserver

###### Acceso al sistema
Abrí tu navegador y navegá a la siguiente URL:
http://127.0.0.1:8000/