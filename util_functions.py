
def get_float(s: str) -> float:
    """
    Get a float from a string.
    :param s: The string to convert to a float.
    :return: The float.
    """
    try:
        return float(s.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def get_month(t):
    """
    Get the month number from a month name
    :param t: name of the month in danish
    :return: number of the month starting from 1
    """
    return {
        "januar": 1,
        "februar": 2,
        "marts": 3,
        "april": 4,
        "maj": 5,
        "juni": 6,
        "juli": 7,
        "august": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "december": 12
    }[t]
