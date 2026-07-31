# This is a guide file on where to download the poverty data and how to process it, in order to be use in the app.

## Download

**poverty**: Go to this [page](https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/pobreza-monetaria), scroll down to the table beneath the chart, then donwload the file "Anexo pobreza monetaria nacional" and store it at:
```bash
/path/to/the/repo/colombia/data/original/dane/poverty/poverty.xlsx
```

## Processing

**poverty**: 
```bash
# run from inside clean_data/ (relative paths)
python clean_poverty.py
```
