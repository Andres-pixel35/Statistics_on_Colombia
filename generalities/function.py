from generalities.dictionaries import presidents

def get_valid_presidents(tmp_years) -> list:
    return [
        name for name, pres_years in presidents.items()
        if not set(pres_years).isdisjoint(tmp_years)
    ]

def find_key_by_value(d, value):
    return next((k for k, v in d.items() if v == value), None)
