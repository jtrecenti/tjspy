import tjspy.utils
import tjspy.cjpg
import pytest
import os
import pandas as pd
from tjspy.utils import build_id
import urllib3

# Disable the warning for insecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_date_pt():
    assert tjspy.utils.date_pt('01/01/2023') == '2023-01-01'
    assert tjspy.utils.date_pt('31/12/2022') == '2022-12-31'
    assert tjspy.utils.date_pt('15/06/1990') == '1990-06-15'

    with pytest.raises(ValueError):
        tjspy.utils.date_pt('2023/01/01')  # Invalid format

    with pytest.raises(ValueError):
        tjspy.utils.date_pt('32/01/2023')  # Invalid date

def test_tjsp_cjpg_download():
    # Test parameters
    busca = "teste"
    dir = "test_downloads"
    pagina_ini = 1
    pagina_fim = 2

    # Run the function
    result = tjspy.cjpg.download(busca=busca, dir=dir, pagina_ini=pagina_ini, pagina_fim=pagina_fim)

    # Assertions
    assert len(result) == 3  # search.html + 2 result pages
    assert all(os.path.exists(path) for path in result)
    assert all(path.endswith('.html') for path in result)
    assert any('search.html' in path for path in result)
    assert any('pag_00001.html' in path for path in result)
    assert any('pag_00002.html' in path for path in result)

    # Clean up
    for file_path in result:
        os.remove(file_path)
    os.rmdir(dir)

def test_build_id():
    # Test case 1: Normal input
    input_id = "0000000-00.0000.0.00.0000"
    expected_output = "0000000-00.0000.0.00.0000"
    assert tjspy.utils.build_id(input_id) == expected_output

    # Test case 2: Input without separators
    input_id = "000000000000000000000"
    expected_output = "0000000-00.0000.0.00.0000"
    assert tjspy.utils.build_id(input_id) == expected_output

    # Test case 3: Input with different separators
    input_id = "0000000/00_0000_0_00_0000"
    expected_output = "0000000-00.0000.0.00.0000"
    assert tjspy.utils.build_id(input_id) == expected_output

    # Test case 4: Empty input
    input_id = ""
    expected_output = ""
    assert tjspy.utils.build_id(input_id) == expected_output

    # Test case 5: Input with extra characters
    input_id = "abcd0000000-00.0000.0.00.0000xyz"
    expected_output = "0000000-00.0000.0.00.0000"
    assert tjspy.utils.build_id(input_id) == expected_output

def test_download_and_parse():
    # Download a single page
    busca = "teste"
    dir = "test_downloads"
    downloaded_files = tjspy.cjpg.download(busca=busca, dir=dir, pagina_ini=1, pagina_fim=1)

    # Ensure at least one file was downloaded
    assert len(downloaded_files) > 0, "No files were downloaded"

    # Parse the downloaded file
    parsed_data = tjspy.cjpg.parse([downloaded_files[0]])

    # Check if the parsed data is a DataFrame
    assert isinstance(parsed_data, pd.DataFrame), "Parsed data is not a DataFrame"

    # Check if the DataFrame is not empty
    assert not parsed_data.empty, "Parsed DataFrame is empty"

    # Check if expected columns are present
    expected_columns = ['n_processo', 'codigo', 'classe', 'assunto', 'magistrado', 'comarca', 'foro', 'vara', 'data_de_disponibilizacao', 'resumo']
    for col in expected_columns:
        assert col in parsed_data.columns, f"Expected column '{col}' not found in parsed data"

    # Clean up downloaded files
    for file in downloaded_files:
        os.remove(file)
    os.rmdir(dir)


