# Precurso - Python esencial

## Qué falta para completar la clase 2

1. Abrí esta carpeta en VS Code.
2. Activá el entorno: `env\Scripts\Activate.ps1`.
3. Instalá Jupyter: `python -m pip install jupyterlab ipykernel`.
4. Copiá el notebook de la clase en `notebooks/precurso_2_python_esencial.ipynb` y seleccioná el kernel `env`.

## Prácticas resueltas

Las soluciones de los tres ejercicios y el proyecto integrador están en
`src/practicas_python_esencial.py`.

Desde esta carpeta, ejecutá:

```powershell
env\Scripts\python.exe src\practicas_python_esencial.py
env\Scripts\python.exe -m unittest discover -s src -p "test_*.py"
```

El primer comando muestra los resultados y crea `conversacion_demo.json`. El segundo
verifica automáticamente las soluciones.
