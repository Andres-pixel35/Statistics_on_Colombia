<p align="center">
  <img src="logo/logo_text.svg" alt="Statistics on Colombia" width="400">
</p>

<p align="center">
  <a href="README.md">🇬🇧 English</a> | 🇪🇸 Español
</p>

<a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue" alt="Licencia: GPL-3.0"></a>

# Statistics on Colombia

**Statistics on Colombia** es un proyecto de código abierto que presenta
estadísticas de Colombia de forma sencilla e interactiva: PIB, inflación
(IPC), mercado laboral, productividad, deuda y déficit públicos, pobreza y
demografía (población, nacimientos, defunciones y migración), entre otras.

## Índice

- [Demo en vivo](#demo-en-vivo)
- [Estado](#estado)
- [Funcionalidades](#funcionalidades)
  - [Página de inicio](#página-de-inicio)
  - [Macroeconomía](#macroeconomía)
  - [Demografía](#demografía)
  - [Misceláneo](#misceláneo)
  - [Pobreza](#pobreza)
  - [En toda la aplicación](#en-toda-la-aplicación)
- [Tecnologías](#tecnologías)
- [Fuentes de datos](#fuentes-de-datos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Flujo de datos](#flujo-de-datos)
- [Descarga e instalación](#descarga-e-instalación)
- [Licencia](#licencia)
- [Contacto](#contacto)

## Demo en vivo

- **Aplicación web:** https://statisticsoncolombia.streamlit.app/
- **Instagram:** https://www.instagram.com/statisticscolombia/

## Estado

Los datos se mantienen actualizados con las últimas publicaciones de cada
fuente, errores encontrados serán arreglados y nuevos datos
o nuevas funcionalidades pueden ser añadidos con el tiempo.

La interfaz de la aplicación está completamente disponible en **español**.

## Funcionalidades

### Página de inicio

Un tablero de tarjetas KPI con el último valor, la variación frente al
periodo anterior y una minigráfica de tendencia para cada serie principal,
agrupadas en Indicadores Principales, Indicadores Económicos, Finanzas
Públicas, Pobreza y Desigualdad, y Demografía — con enlaces rápidos a cada
página completa.

### Macroeconomía

- **PIB** — niveles y crecimiento desde las perspectivas de gasto,
  producción e ingreso; crecimiento anual, anual por trimestre y trimestre a
  trimestre; vista per cápita; vista intra-anual (por trimestres).
- **IPC (inflación)** — series nacionales, por ciudad y por categoría de
  gasto, con las canastas de 15 y 20 productos básicos.
- **Mercado laboral** — desempleo (original y desestacionalizado), fuerza
  laboral, departamentos y regiones (con mapas coropléticos), formalidad
  laboral y trabajo infantil.
- **Productividad** — tablas de productividad total de los factores del
  DANE: por persona empleada, por hora trabajada, valor agregado, producción
  y por actividad económica.
- **Deuda** — deuda bruta del Gobierno Nacional Central: saldos (también
  como % del PIB o del total), fuentes, tasas, moneda, perfil de
  vencimientos e indicadores.
- **Déficit** — balance fiscal con frecuencia anual, trimestral y mensual,
  en COP o como % del PIB, con comparación de ingresos frente a gastos.
- **ISE** — el indicador mensual de seguimiento a la economía (original y
  desestacionalizado), por categoría y rama de actividad.

### Demografía

- **Población** — nacional, por departamento y por municipio; pirámides
  poblacionales; proyecciones oficiales mostradas con línea punteada; tasas
  de natalidad y mortalidad.
- **Migración** — migración neta y entradas/salidas de viajeros por país,
  dirección y género, incluyendo un mapa mundial.
- **Nacimientos** — por género, edad de la madre (con pirámide de
  nacimientos), educación, departamento y municipio.
- **Defunciones** — por género, grupo de edad (con pirámide de
  defunciones), área, causa de muerte, departamento y municipio, con tasas
  opcionales por cada 1.000 habitantes.

### Misceláneo

- **Tasa de cambio** (COP/USD), **tasa de política monetaria**, **salario
  mínimo** (nominal, real o en USD), **tasa de colocación** y el **índice de
  miseria** (fórmula de Hanke).

### Pobreza

- **Indicadores** — pobreza monetaria y extrema, brecha, severidad, líneas
  de pobreza, Gini e ingreso per cápita, por agregados nacionales y ciudades
  capitales, incluyendo un mapa coroplético.
- **Perfil del hogar** — pobreza según características del hogar y del jefe
  de hogar.
- **Por sexo** — indicadores de pobreza para hombres y mujeres por dominio.

### En toda la aplicación

- Compara cualquier serie entre **periodos presidenciales** con un eje
  relativo de "año de mandato".
- **Tema claro/oscuro** y gráficas **adaptadas a móviles**.
- **Mapas coropléticos** de Colombia por departamento y región.

## Tecnologías

- **Streamlit** — aloja la aplicación y renderiza la interfaz interactiva
- **Python** + **pandas** — limpieza y manipulación de datos
- **Plotly** — gráficas

## Fuentes de datos

- **DANE** — Departamento Administrativo Nacional de Estadística
- **Banco de la República** — banco central de Colombia
- **Ministerio de Hacienda** — deuda pública y balance fiscal
- **Banco Mundial** — migración neta
- **Migración Colombia / Datos Abiertos** — entradas/salidas de viajeros, a
  través de la plataforma de datos abiertos de Colombia

## Estructura del proyecto

```
streamlit_app.py      ← punto de entrada
app_pages/            ← un script por página + página de inicio
  tabs/               ← lógica de cada vista (macroeconomía, demografía, …)
  helpers/            ← limpieza/pivoteo de datos + constructores de gráficas Plotly
generalities/         ← diccionarios de configuración (etiquetas, filtros, rutas)
clean_data/           ← scripts que convierten los archivos originales en CSV limpios
data/                 ← CSV limpios que lee la aplicación, agrupados por fuente
  original/           ← archivos originales tal como se descargan de cada fuente
info_data/            ← notas sobre el origen de cada dato y cómo se actualiza
logo/                 ← logo de la aplicación (SVG)
```

## Flujo de datos

Los archivos originales descargados de cada fuente están en
`data/original/`. Los scripts de `clean_data/` los transforman en los CSV
limpios de `data/` que lee la aplicación:

- La mayoría de los scripts se ejecutan desde dentro de `clean_data/`
  (p. ej. `cd clean_data && python clean_borns.py`).
- `clean_deaths.py` y `clean_job_market.py` se ejecutan como módulos desde
  la raíz del repositorio (p. ej. `python -m clean_data.clean_job_market`).

Algunos CSV del Banco de la República (tasa de cambio, tasa de política
monetaria, salario mínimo, PIB anual) se mantienen a mano — los pasos están
documentados en `info_data/`.

## Descarga e instalación

Para descargar el proyecto y ejecutarlo localmente:

```bash
# 1. Clona el repositorio (o usa "Code → Download ZIP" en GitHub)
git clone https://github.com/Andres-pixel35/Statistics_on_Colombia.git
cd Statistics_on_Colombia

# 2. Instala las dependencias
pip install -r requirements.txt
#    …o con conda:
# conda env create -f environment.yml

# 3. Ejecuta la aplicación
streamlit run streamlit_app.py
```

La aplicación se abre en tu navegador en `http://localhost:8501`.

## Licencia

Este proyecto está licenciado bajo la **Licencia Pública General de GNU
v3.0 (GPL-3.0)** — consulta el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

¿Preguntas, sugerencias o cualquier tema relacionado con este proyecto?
Escríbeme a **statistics-colombia@proton.me**.
