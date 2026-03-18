# C++ Compiler IDE

Un Entorno de Desarrollo Integrado (IDE) interactivo diseñado específicamente para la compilación y análisis de código fuente en C++. Desarrollado como proyecto para la materia de Compiladores (8vo Semestre) por Gabriel Alcaraz Suárez.

## Características Principales

- **Editor de Código**: Interfaz amigable para escribir y probar fragmentos de código en C++ con atajos útiles y numeración de líneas.
- **Análisis Léxico**: Tokenización del código fuente para identificar palabras clave, identificadores, operadores, y más.
- **Análisis Sintáctico (Parser)**: Validación de la estructura del código según las reglas gramaticales de C++.
- **Manejo de Errores**: Identificación precisa de errores léxicos, sintácticos y semánticos.
- **Tabla de Símbolos**: Rastreo de variables, funciones y otras estructuras declaradas en el programa.
- **Generación de Árbol de Análisis**: Visualización estructurada del código procesado.
- **Interfaz Gráfica Moderna**: Desarrollado utilizando `PySide6` para una experiencia de usuario fluida y reactiva, compatible con pantallas High DPI.

## Tecnologías Utilizadas

- **Python 3**: Lenguaje principal de desarrollo y lógica del compilador.
- **PySide6**: Framework utilizado para diseñar y construir la Interfaz Gráfica de Usuario (GUI).

## Requisitos Previos

Para ejecutar el IDE, necesitas tener instalado Python 3 y `PySide6` en tu sistema operativo local:

```bash
pip install PySide6
```

## Instrucciones de Uso

1. Copia o clona este repositorio en tu máquina local.
2. Abre una terminal y navega hasta el directorio del proyecto.
3. Ejecuta el archivo principal:

```bash
python ide_compiler.py
```

4. Escribe tu código C++ en el área izquierda o abre un archivo existente.
5. Usa las opciones del sistema para compilar o visualizar las diferentes etapas (Tabla de símbolos, Errores, Resultados, etc.)

## Autor
- **Gabriel Alcaraz Suárez** - Proyecto de Compiladores (8vo Semestre).
