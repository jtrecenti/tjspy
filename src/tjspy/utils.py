from datetime import datetime
import re

def date_pt(date_str):
    """
    Converts a date string from 'dd/mm/yyyy' to 'yyyy-mm-dd'.

    :param date_str: Date string in 'dd/mm/yyyy' format
    :return: Date string in 'yyyy-mm-dd' format or empty string if input is empty
    """
    if date_str == "":
        return ""
    return datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')

def build_id(id):
    """
    Build a process ID from the provided parts.

    :param id: A string representing the process ID
    :return: A formatted process ID string
    """
    def build(id_parts):
        return f"{id_parts['N']}-{id_parts['D']}.{id_parts['A']}.{id_parts['J']}.{id_parts['T']}.{id_parts['O']}"
    if id == "":
        return ""
    return ''.join(map(build, extract_parts(id)))

def extract_parts(id, parts=None):
    """
    Extract specific parts from a process ID.

    :param id: A string representing the process ID
    :param parts: A list of parts to extract. Defaults to ['N', 'D', 'A', 'J', 'T', 'O'].
    :return: A list of dictionaries with the extracted parts
    """
    if parts is None or "" in parts:
        parts = ["N", "D", "A", "J", "T", "O"]
    else:
        parts = list(set(parts))

    if any(part not in ["N", "D", "A", "J", "T", "O"] for part in parts):
        raise ValueError("Invalid parts")

    # Remove non-numeric characters and process IDs
    id = re.sub(r'[^0-9]', '', id)
    if len(id) == 18:
        id = calc_dig(id, build=True)  # Assuming calc_dig function exists and works as expected

    def get_parts(id, parts):
        out = {}
        for part in parts:
            if part == "N":
                out[part] = id[0:7]
            elif part == "D":
                out[part] = id[7:9]
            elif part == "A":
                out[part] = id[9:13]
            elif part == "J":
                out[part] = id[13:14]
            elif part == "T":
                out[part] = id[14:16]
            elif part == "O":
                out[part] = id[16:20]
        return out

    return [get_parts(id, parts)]

def calc_dig(num, build=False):
    """
    Calculate the check digit for the lawsuit ID and return it. Optionally, build and return the full ID with the check digit.

    :param num: A string representing the lawsuit ID without check digits (18 numerical digits).
    :param build: Boolean indicating whether to return the full ID with the check digit appended.
    :return: The check digit as a string, or the full ID with the check digit if build is True.
    """
    if len(num) != 18:
        raise ValueError("Lawsuit IDs without check digits should have 18 numerical digits.")

    NNNNNNN = num[0:7]
    AAAA = num[7:11]
    JTR = num[11:14]
    OOOO = num[14:18]

    n1 = f"{int(NNNNNNN) % 97:02d}"
    n2 = f"{int(f'{n1}{AAAA}{JTR}') % 97:02d}"
    n3 = f"{98 - (int(f'{n2}{OOOO}') * 100 % 97):02d}"

    dig = n3

    if build:
        return f"{num[0:7]}{dig}{num[7:18]}"

    return dig
