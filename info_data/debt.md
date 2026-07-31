# This is a guide file on where to download the debt data and how to process it, in order to be use in the app.

## Download

**debt**: Go to this [page](https://www.irc.gov.co/deuda-publica/perfil-deuda-publica-gnc), scroll down to "documentos" and download the file "Histórico Total currentMonthCurrentYear"; then store it at:
```bash
"/path/to/the/repo/colombia/data/original/hacienda/debt/Histórico Total currentMonthCurrentYear.xls"
```

## Processing

**debt**: 
```bash
# run from inside clean_data/ (relative paths)
python clean_debt.py
```
