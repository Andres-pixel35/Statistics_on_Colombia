# This is a guide file on where to download the productivity data and how to process it, in order to be use in the app.

## Download

**productividad** Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/productividad) and dpwnload "Anexo: Productividad", then store it at
```bash
/home/riosandres/Documents/coding/genius/colombia/data/original/dane/productivity/anex-PTF-Productividad-2025.xlsx
```

**laboral**: Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/productividad) and dpwnload "Anexo: Productividad laboral ", then store it at 
```bash
/home/riosandres/Documents/coding/genius/colombia/data/original/dane/productivity/anex-PTF-ProductividadLaboral-2025.xlsx
```

## Processing 

**productividad laboral**:
Writes CSVs to all four category dirs (`valor_agregado/`, `produccion/nacional/`, `produccion/actividad_economica/`, `laboral/`), though only `laboral/` and `valor_agregado` are currently wired into the Productivity tab UI.
```bash
# run from inside clean_data/ (relative paths)
python clean_productivity.py
```
