import requests
import urllib3
from bs4 import BeautifulSoup, NavigableString
from pathlib import Path
import os
import tjspy.tjspy
import tjspy.utils
import pandas as pd
import re
from unidecode import unidecode

# Disable the warning for insecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download(busca, dir=".", classe="", assunto="", comarca="", n_processo="", data_ini="", data_fim="", pagina_ini=1, pagina_fim=float('inf')):
    """
    Download jurisprudence of the first instance from TJSP.

    :param busca: Query to be made
    :param dir: Directory where HTML files will be saved
    :param classe: List with class IDs
    :param assunto: List with subject IDs
    :param comarca: List with district IDs
    :param n_processo: String with the process number
    :param data_ini: Minimum date for the results
    :param data_fim: Maximum date for the results
    :param pagina_ini: First page to download
    :param pagina_fim: Last page to download
    :return: List of file paths of the downloaded HTML files
    """
    assert pagina_ini <= pagina_fim, "The initial page must be less than or equal to the final page."

    strings = [",".join(lst) for lst in [classe, assunto, comarca]]
    dates = [tjspy.utils.date_pt(date) for date in [data_ini, data_fim]]
    n_processo = tjspy.utils.build_id(n_processo) if n_processo != "" else n_processo

    query_post = {
        "conversationId": "",
        "dadosConsulta.pesquisaLivre": busca,
        "tipoNumero": "UNIFICADO",
        "numeroDigitoAnoUnificado": n_processo[:15],
        "foroNumeroUnificado": n_processo[-4:],
        "dadosConsulta.nuProcesso": n_processo,
        "classeTreeSelection.values": strings[0],
        "assuntoTreeSelection.values": strings[1],
        "contadoragente": 0,
        "contadorMaioragente": 0,
        "dadosConsulta.dtInicio": dates[0],
        "dadosConsulta.dtFim": dates[1],
        "varasTreeSelection.values": strings[2],
        "dadosConsulta.ordenacao": "DESC"
    }

    os.makedirs(dir, exist_ok=True)
    path = Path(dir).resolve()
    file_path = path / "search.html"

    ses = requests.Session()

    response = ses.post("https://esaj.tjsp.jus.br/cjpg/pesquisar.do",
                        data=query_post,
                        verify=False,
                        headers={'User-Agent': tjspy.tjspy.esaj_ua()})

    with open(file_path, 'wb') as f:
        f.write(response.content)

    soup = BeautifulSoup(response.content, 'html.parser')
    n_results = soup.select_one("#resultados > table:nth-child(1)").text

    numbers = re.findall(r' (\d+)', n_results)
    total_results = int(numbers[-1])
    n_pages = (total_results + 9) // 10
    n_pages = min(n_pages, pagina_fim)

    def download_pages(page, path):
        query_get = {
            "pagina": page,
            "conversationId": ""
        }

        file_name = path / f"pag_{str(page).zfill(5)}.html"
        response = ses.get("https://esaj.tjsp.jus.br/cjpg/trocarDePagina.do",
                            params=query_get,
                            verify=False,
                            headers={'User-Agent': tjspy.tjspy.esaj_ua()})

        with open(file_name, 'wb') as f:
            f.write(response.content)

        return str(file_name)

    files = [download_pages(page, path) for page in range(pagina_ini, n_pages + 1)]
    return [str(file_path)] + files

def parse(arq):
    """
    Parse first instance decisions from TJSP.

    :param arq: File downloaded by tjsp_cjpg_download()
    :return: DataFrame with parsed lawsuit information
    """
    assert len(arq) == 1, "Only one file should be provided."

    with open(arq[0], 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    nodes = soup.select(".fundocinza1")

    parsed_data = pd.concat([parse_cjpg_lawsuit(node) for node in nodes], ignore_index=True)

    return parsed_data

def parse_cjpg_lawsuit(node):
    """
    Parse a single lawsuit node.

    :param node: A BeautifulSoup element representing a lawsuit
    :return: A DataFrame with the parsed information
    """

    cd = node.select_one("a[title='Visualizar Inteiro Teor']").get("name").strip()

    id_text = node.select_one("a[title='Visualizar Inteiro Teor']").text.strip()
    id_num = re.sub(r"[^0-9]", "", id_text)

    tx = node.select_one("table div[style='display: none;']").text.strip()

    keys = [unidecode(re.sub(r"[^a-z ]", "", re.sub(r"\s+", "_", k.text.strip().lower())))
            for k in node.select("table tr td strong")]

    keys = [k for k in keys if k != ""]
    # Replace "datadedisponibilizao" with "data_de_disponibilizacao" in keys
    keys = ['data_de_disponibilizacao' if k == 'datadedisponibilizao' else k for k in keys]

    vals = []
    for strong_tag in node.select("table tr td strong"):
        next_sibling = strong_tag.next_sibling
        if isinstance(next_sibling, NavigableString):
            vals.append(next_sibling.strip())

    infos = pd.DataFrame([dict(zip(keys, vals))])

    data = pd.DataFrame({'n_processo': [id_num], 'codigo': [cd]})
    result = pd.concat([data, infos], axis=1)
    result['resumo'] = tx

    return result
