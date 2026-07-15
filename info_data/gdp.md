# This is a guide file on where to download the GDP data and how to process it, in order to be use in the app.

## download

**production**: Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/historicos-producto-interno-bruto-pib) and under the column "Documentos y anexos producción" download "PIB a precios constantes". Finally, store it at 
```bash
/path/to/the/repo/colombia/data/original/dane/GDP/
```

**spend**: Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/historicos-producto-interno-bruto-pib) and under the column "Documentos y anexos gasto" download "PIB a precios constantes". Finally, store it at 
```bash
/path/to/the/repo/colombia/data/original/dane/GDP/
```

**Quarter growth** go to this [page](https://suameca.banrep.gov.co/descarga-multiple-de-datos/), go to "Actividad economica, mercado laboral y cuentas financieras", then "producto interno bruto", then "crecimiento PIB real, trimestral base 2015" and download it at:
```bash
/path/to/the/repo/colombia/data/original/banco_republica/GDP/quarter_growth.xlsx
```

**nominal_annual**: Go to this [page](https://suameca.banrep.gov.co/descarga-multiple-de-datos/), go to "Actividad economica, mercado laboral y cuentas financieras", then "producto interno bruto", "Producto Interno Bruto (PIB) nominal, Anual, metodología: 2015", download it as an excel file and store it at:
```bash
/path/to/the/repo/colombia/data/original/banco_republica/GDP/nominal_annual.xlsx
```

**real_annual**: Go to this [page](https://suameca.banrep.gov.co/descarga-multiple-de-datos/), go to "Actividad economica, mercado laboral y cuentas financieras", then "producto interno bruto", "Producto Interno Bruto (PIB) real, Anual, base: 2015 ", download it as an excel file and store it at:
```bash
/path/to/the/repo/colombia/data/original/banco_republica/GDP/real_annual.xlsx
```

## processing

### Production

**production**: go to google sheets and open the file, then go to "Cuadro 3" and copy all the rows from "concepto" to the end. Once you do that go to "PIB-production_2026" and in "Hoja 2" delete everything that is there and paste what you just copy. Remove any empty rows (if applied). Go to "Extensiones" and "App Script", there copy this code:
```
function unmergeAndFillYears() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var range = sheet.getActiveRange(); // Select the row with years before running
  var values = range.getValues()[0];
  
  // 1. Unmerge the selection
  range.breakApart();
  
  // 2. Fill the blanks with the value to the left
  var filledValues = [];
  var lastValue = "";
  
  for (var i = 0; i < values.length; i++) {
    if (values[i] !== "") {
      lastValue = values[i];
    }
    filledValues.push(lastValue);
  }
  
  // 3. Write the filled values back to the sheet
  range.setValues([filledValues]);
}
```

and give it permissions. Once you do that, go back to sheet and select the first row from the second column to the last. then go back to the script and execute it. Now, create a new row at the top and copy the following:
```
=ARRAYFORMULA(B2:CH2 & "-" & B3:CH3)
```

create another row above, copy all the content from the row bellow and copy it with "ctrl + shift + v" in the new row. set the first column as 'Concepto' and remove the three rows below. then select everything, go to "datos", "limpieza de datos", "quitar duplicados", select only the column "concepto" and accept.

finally, download it as csv and store it at:
```bash
/path/to/the/repo/colombia/data/dane/GDP/production/summarize.csv
```

### Spend

**summarize**: Go to google sheets and open the send file. There, go to "Cuadro 1", select all the info from the first box, copy it and paste it at "PIB_spend" in the sheet "summarize". Then, do the same steps as in production, except the one where it deletes duplicates. Store it as a csv at
```bash
/path/to/the/repo/colombia/data/dane/GDP/spend/summarize.csv
```

**goal home's spend**: Go to google sheets and open the send file. There, go to "Cuadro 3", select all the info from the first box, copy it and paste it at "PIB_spend" in the sheet "goal home's spend". Then, do the same steps as in production, except the one where it deletes duplicates. Store it as a csv at 
```bash
/path/to/the/repo/colombia/data/dane/GDP/spend/goal_homes_spend.csv
```

**durability home's spend**: Go to google sheets and open the send file. There, go to "Cuadro 3", select all the info from the second box, copy it and paste it at "PIB_spend" in the sheet "durability home's spend". Then, do the same steps as in production, except the one where it deletes duplicates. Store it as a csv at 
```bash
/path/to/the/repo/colombia/data/dane/GDP/spend/durability_homes_spend.csv
```

**capital formation**: Go to google sheets and open the send file. There, go to "Cuadro 5", select all the info from the first box, copy it and paste it at "PIB_spend" in the sheet "capital formation". Then, do the same steps as in production, except the one where it deletes duplicates. Store it as a csv at 
```bash
/path/to/the/repo/colombia/data/dane/GDP/spend/capital_formation.csv
```

**exports and imports**: Go to google sheets and open the send file. There, go to "Cuadro 7", select all the info from the first box, copy it and paste it at "PIB_spend" in the sheet "exports and imports". Then, do the same steps as in production, except the one where it deletes duplicates. Also, change the name of "bienes" and "servicios" under both "exportaciones" and "importaciones" to "E.Bienes", "E.Servicios", "I.Bienes", "I.Servicios" Store it as a csv at 
```bash
/path/to/the/repo/colombia/data/dane/GDP/spend/exports_and_imports.csv
```

### Others

**quarter growth**: execute
```bash
# run from inside clean_data/ (relative paths)
python quarter_growth_clean.py
```

**nominal_annual**: Open the file in excel, remove the second column, then move the second and third column from "Producto Interno Bruto (PIB) nominal, Anual, metodología: 2015(Dato fin de año), Producto Interno Bruto (PIB) nominal, Anual, metodología: 2015(Variación porcentual  anual)" to "PIB, Crecimiento".
Remove the autogenerated row at the bottom of the file, then select all the values from the second column and replace "." with nothing, then replace "," with ".". For the third column replace "," with ".". Finally, store it at: 
```bash
/path/to/the/repo/colombia/data/banco_republica/GDP/nominal_annual.csv
```

**real_annual**: Open the file in excel, remove the second column, then move the second and third column from "Producto Interno Bruto (PIB) real, Anual, base: 2015(Variación porcentual  anual), Producto Interno Bruto (PIB) real, Anual, base: 2015(Dato fin de año))" to "Crecimiento, PIB".
Remove the autogenerated row at the bottom of the file, then select all the values from the third column and replace "." with nothing, then replace "," with ".". For the second column replace "," with ".". Finally, store it at: 
```bash
/path/to/the/repo/colombia/data/banco_republica/GDP/real_annual.csv
```

## income

TODO: this dataset was added to the app before this guide was written — download/processing steps not documented yet.
