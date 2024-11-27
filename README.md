# Gestión de Empleados

## Objetivo General

Desarrollar un sistema Web que permita la gestión de asistencias automatizada de los empleados de una empresa mediante la aplicación de un modelo de Inteligencia Artificial.

## Requisitos del Sistema

- **FN.1** - Inicio de sesión.
- **FN.2** - Gestión de usuarios.
- **FN.3** - Gestión de datos biométricos.
- **FN.4** - Gestión de horarios de los empleados.
- **FN.5** - Gestión de justificantes.
- **FN.6** - Registro de asistencia mediante reconocimiento facial.
- **FN.7** - Subir evidencia para justificante.
- **FN.8** - Generación de reportes.

## Instalación

1. Clona el repositorio:
    ```sh
    git clone https://github.com/kvsneo/GestionEmpleados.git
    ```
2. Navega al directorio del proyecto:
    ```sh
    cd GestionEmpleados
    ```
3. Instala las dependencias utilizando `requirements.txt`:
    ```sh
    pip install -r requirements.txt
    ```
4. Configura la base de datos en MySQL. Ejecuta los comando en la consola de MySQL para crear la base de datos (basegestionempleados.sql).

5. Ejecuta las migraciones de Django para crear las tablas necesarias en la base de datos:
    ```sh
    python manage.py migrate
    ```

## Uso

1. Configura el entorno de desarrollo con las variables necesarias.
2. Inicia la aplicación:
    ```sh
    python manage.py runserver
    ```
3. Accede a la aplicación desde tu navegador en `http://localhost:8000`.
