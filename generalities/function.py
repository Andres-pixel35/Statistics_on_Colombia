from generalities.presidents import presidents


def get_valid_presidents(tmp_years) -> list:
    return [
        name for name, pres_years in presidents.items()
        if not set(pres_years).isdisjoint(tmp_years)
    ]
