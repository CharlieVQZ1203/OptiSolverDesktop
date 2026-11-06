# OptiSolver Desktop

Aplicación de escritorio para Windows que resuelve problemas de programación
lineal con Simplex Primal y Simplex Dual. Muestra la tabla inicial, cada pivote,
las variables básicas finales y el valor óptimo cuando existe.

## Requisitos

- Windows de 64 bits y Microsoft Edge WebView2 Runtime para la interfaz.
- Python 3.12 de 64 bits para ejecutar desde el código fuente o generar el ejecutable.

## Ejecutar desde el código fuente

Abre CMD en la carpeta que contiene `index.html` y ejecuta:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python OptiSolverDesktop.py
```

## Generar el ejecutable

Con el entorno virtual activo, ejecuta:

```cmd
python -m PyInstaller --onefile --windowed --name OptiSolverDesktop --add-data "index.html:." --add-data "estilos.css:." --add-data "app.js:." OptiSolverDesktop.py
```

El archivo generado queda en `dist\OptiSolverDesktop.exe`.
Para abrirlo, haz doble clic sobre él.

## Uso

1. Selecciona Maximizar o Minimizar y el método Simplex.
2. Define el número de variables y restricciones.
3. Captura los coeficientes, los signos y los lados derechos.
4. Pulsa **Resolver problema** y recorre las tablas con **Anterior** y **Siguiente**.

El Simplex Dual parte de una base de holguras. Si esa base no cumple la
condición para iniciar el método, la aplicación muestra un aviso y puedes
seleccionar Simplex Primal.