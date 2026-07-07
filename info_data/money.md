# This is a guide file on where to download the TRM and minimum wage data and how to process it, in order to be use in the app.

## Download

**TRM**: go to this [page](https://suameca.banrep.gov.co/estadisticas-economicas/informacionSerie/1/tasa_cambio_peso_colombiano_trm_dolar_usd), download it and store it at
```bash
/home/riosandres/Documents/coding/genius/colombia/data/banco_republica/money/trm.csv
```

## Processing

**TRM**: open trm.csv in excel, then change the columns name from ("Periodo(MMM DD, AAAA)", "Tasa Representativa del Mercado (TRM)") to ("Fecha", "trm"), then store it at 
```bash
/home/riosandres/Documents/coding/genius/colombia/data/banco_republica/money/trm.csv
```

**minimum wage**: Mannually search and add the data, then store it at
```bash
/home/riosandres/Documents/coding/genius/colombia/data/banco_republica/money/salario_minimo.csv
```

Note: unlike everything else in this guide, neither TRM nor minimum wage is currently consumed by any page/tab in the app yet.
