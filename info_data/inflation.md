# This is a guide file on where to download the inflation data and how to process it, in order to be use in the app.

## CPI

### Download

**Inflation 15**: Go to the this [page](https://suameca.banrep.gov.co/descarga-multiple-de-datos/), there select "Precios e inflación", then "Inflación al consumidor" and "Inflation núcleo 15". Download it as an excel file and store it at 
```bash
~/Documents/coding/genius/colombia/data/original/banco_republica/CPI/inflacion_15.xlsx 
```

**City**: Go to this [page](https://suameca.banrep.gov.co/estadisticas-economicas/tablasPreconstruidas), there select "Precios e inflación", then "Índice de Precios al Consumidor (IPC)", now "Base 2018" and "Por ciudad". Download it as an excel file and store it at 
```bash
~/Documents/coding/genius/colombia/data/original/banco_republica/CPI/1_IPC_2018_por_ciudad_iqy.xlsx 
```

**spend_category**: Go to this [page](https://suameca.banrep.gov.co/estadisticas-economicas/tablasPreconstruidas), there select "Precios e inflación", then "Índice de Precios al Consumidor (IPC)", now "Base 2018" and "Total y por división de gasto. Download it as an excel file and store it at 
```bash
~/Documents/coding/genius/colombia/data/original/banco_republica/CPI/2_IPC_2018_por_division_de_gasto_iqy.xlsx 
```

**Inflation 20**: Go to the this [page](https://suameca.banrep.gov.co/descarga-multiple-de-datos/), there select "Precios e inflación", then "Inflación al consumidor" and "Inflation núcleo 20". Download it as an excel file and store it at 
```bash
~/Documents/coding/genius/colombia/data/original/banco_republica/CPI/inflacion_20.xlsx 
```

**goal**: Go to the this [page](https://suameca.banrep.gov.co/descarga-multiple-de-datos/), there select "Precios e inflación", then "Inflación al consumidor" and "Meta de inflación". Download it as an excel file and store it at 
```bash
~/Documents/coding/genius/colombia/data/original/banco_republica/CPI/goal.xlsx 
```
 
### Processing
**Inflation 15**: Open the excel file, then delete the second row and replace "Inflación núcleo 15(Dato fin de mes)" with "Inflación". Afterwards, go to the bottom of the file and delete the extra row generated automatically by Banco de la República. Finally, select all the values from the secon column, press "Ctrl + h" and replace "," with ".".

Now store it as a csv at
```bash
~/Documents/coding/genius/colombia/data/banco_republica/CPI/inflacion_15.csv
```

**City**: Open the excel file, delete the first 4 rows, go to the bottom of the file and delete the extra row generated automatically by Banco de la República. Then store it at 
```bash
~/Documents/coding/genius/colombia/data/original/banco_republica/CPI/1_IPC_2018_por_ciudad_iqy.xlsx 
```
Now go to the directory *clean_data*, open the file *inflation_clean.py*, make sure the paths for both read and save are correct, then execute the file
```bash
# run from inside clean_data/ (relative paths)
python inflation_clean.py
```
Cleaned output lands at `data/banco_republica/CPI/city/*.csv` (one file per city). Finally go to the directory *city*, remove "Bogotá,_D.C.csv" and delete the extra dot in the new Bogota's file.

**spend_category**: Open the excel file, delete the first 4 rows, go to the bottom of the file and delete the extra row generated automatically by Banco de la República. Then store it at 
```bash
~/Documents/coding/genius/colombia/data/original/banco_republica/CPI/2_IPC_2018_por_division_de_gasto_iqy.xlsx
```
Now go to the directory *clean_data*, open the file *inflation_clean.py*, make sure the paths for both read and save are correct, then execute the file
```bash
# run from inside clean_data/ (relative paths)
python inflation_clean.py
```
Cleaned output lands at `data/banco_republica/CPI/spend_category/*.csv` (one file per spend category).

**Inflation 20**: Open the excel file, then delete the second row and replace "Inflación núcleo 20(Dato fin de mes)" with "Inflación". Afterwards, go to the bottom of the file and delete the extra row generated automatically by Banco de la República. Finally, select all the values from the secon column, press "Ctrl + h" and replace "," with ".".

Now store it as a csv at
```bash
~/Documents/coding/genius/colombia/data/banco_republica/CPI/inflacion_20.csv
```

**goal**:  Open the excel file, then delete the second row and replace "Meta de inflación(Dato fin de año)" with "Inflación". Afterwards, go to the bottom of the file and delete the extra row generated automatically by Banco de la República. Finally, select all the values from the secon column, press "Ctrl + h" and replace "," with ".".

Now store it as a csv at
```bash
~/Documents/coding/genius/colombia/data/banco_republica/CPI/goal.csv
```
