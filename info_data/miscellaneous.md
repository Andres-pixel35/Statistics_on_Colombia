# This is a guide file on where to download the miscellaneous data and how to process it, in order to be use in the app.

### Download

**TRM**: go to this [page](https://suameca.banrep.gov.co/estadisticas-economicas/informacionSerie/1/tasa_cambio_peso_colombiano_trm_dolar_usd), download it and store it at
```bash
/path/to/the/repo/colombia/data/banco_republica/miscellaneous//trm.csv
```

**tasa_monetaria**: Go to this [page](https://suameca.banrep.gov.co/estadisticas-economicas/tablasPreconstruidas), go to "Tasas de interés y sector financiero". then to "Tasas de interés de política monetaria" and click "Serie histórica diaria". Once in, download it as xlsx and store it at:
```bash
/path/to/the/repo/colombia/data/original/banco_republica/miscellaneous/tasa_monetaria.xlsx
```

## Processing

**TRM**: open trm.csv in excel, then change the columns name from ("Periodo(MMM DD, AAAA)", "Tasa Representativa del Mercado (TRM)") to ("Fecha", "trm"), then store it at 
```bash
/path/to/the/repo/colombia/data/banco_republica/miscellaneous//trm.csv
```

**minimum wage**: Mannually search and add the data, then store it at
```bash
/path/to/the/repo/colombia/data/banco_republica/miscellaneous//salario_minimo.csv
```

Note: unlike everything else in this guide, only tmr has any page/tab in the app yet.


