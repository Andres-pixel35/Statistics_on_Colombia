# This is a guide file on where to download the population data and how to process it, in order to be use in the app.

## Population

### Download

**inbound_co**: Go to this [page](https://www.datos.gov.co/Estad-sticas-Nacionales/Entradas-de-extranjeros-a-Colombia/96sh-4v8d/about_data), click 'Exportar' and store it as csv at
```bash
/path/to/the/repo/colombia/data/original/datos_abiertos/Entradas_de_extranjeros_a_Colombia_20260520.csv
```

**outbound_co**: Go to this [page](https://www.datos.gov.co/Estad-sticas-Nacionales/Salidas-de-colombianos-desde-el-territorio-naciona/efw5-jiej/about_data), click 'Exportar' and store it as csv at
```bash
/path/to/the/repo/colombia/data/original/datos_abiertos/Salidas_de_colombianos_desde_el_territorio_nacional_20260520.csv
``` 

**Net migration**: go to this [page](https://data.worldbank.org/indicator/SM.POP.NETM?locations=CO), donwload it as an excel file asn store it at:
```bash
/path/to/the/repo/colombia/data/original/world_bank/net_migration.xls
```

**Borns**: Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/salud/nacimientos-y-defunciones/nacimientos), select the missing year in your database and download it. Store it at:
```bash
/path/to/the/repo/colombia/data/original/dane/borns/year # being year 2026 or 2027 or whatever
```

**deaths**: Go this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/salud/nacimientos-y-defunciones/defunciones), , select the missing year in your database and download it. Store it at:
```bash
/path/to/the/repo/colombia/data/original/dane/deaths/year # being year 2026 or 2027 or whatever
```

**departamental**: Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion) and donwload the missing file from "Serie departamental de poblacion por área, sexo y edad para el periodo YYYY-YYYY" and store it at:
```bash
/path/to/the/repo/colombia/data/original/dane/population/departamental/YYYY-YYYY
```

**Nacional**: Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion) and donwload the missing file from "Serie nacional de población por área, sexo y edad para el periodo YYYY-YYYY" and store it at:
```bash
/path/to/the/repo/colombia/data/original/dane/population/nacional/YYYY-YYYY
```

**Municipal**: Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion) and donwload the missing file from "Serie municipal de población por área, sexo y edad para el periodo YYYY-YYYY" and store it at:
```bash
/path/to/the/repo/colombia/data/original/dane/population/municipal/YYYY-YYYY
```

### Processing

**Migration**: 
```bash
# run from inside clean_data/ (relative paths)
python migration_clean.py
```

**net migration**: 
```bash
# run from inside clean_data/ (relative paths)
python net_migration.py
```

**borns**: 
```bash
# run from inside clean_data/ (relative paths)
python clean_borns.py
```
**deaths**: 
```bash
# run from repo root (module, not a plain script path)
python -m clean_data.clean_deaths
```

**Departamental, municipal, nacional**:
```bash
# run from inside clean_data/ (relative paths). Only one of the ors, you can also write a for loop if you want to execute all in the same command
python population_clean.py municipal OR departamental OR nacional
```
