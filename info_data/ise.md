# This is a guide file on where to download the ISE data and how to process it, in order to be use in the app.

## Download

**ise**: Go to this [link](https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/indicador-de-seguimiento-a-la-economia-ise), then scroll down and download "Anexo (9 actividades)" and store it at:
```bash
"/path/to/the/repo/colombia/data/original/dane/ISE/anex-ISE-9actividades-{current_month}{current_year}.xlsx"
```

## Processing 

**ise**: 
```bash
# run from inside clean_data/ (relative paths)
python clean_ise.py
```
