import requests
from requests.exceptions import ChunkedEncodingError
from http.client import IncompleteRead
import time
import os
from .auxiliary_functions import *
from bs4 import BeautifulSoup

def url_exists(url, save_path):
    """
    Attempts to download a file from the given URL and save it to the specified path.
    Returns True if the file was downloaded successfully, indicating the URL exists.

    Parameters:
    - url: The URL of the file to download.
    - save_path: The full path (including filename) where the file should be saved.

    Returns:
    - True if the file is downloaded successfully, False otherwise.
    """
    try:
        ensure_folder_exists('temp')
        with requests.get(url, stream=True) as r:
            # Check if the request was successful
            if r.status_code == 200:
                # Check for non-empty content
                if int(r.headers.get('Content-Length', 0)) > 0:
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
            # If the status code is not 200 or content length is 0, treat as failure
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
def scrapping_venda_url(soup, fuel_type, location_type):
    h3_tags = soup.find_all('h3')
    list_urls = []    
    # Loop through each <h3> tag found
    padrao_data = r'\d{2}/\d{2}/\d{4}'
    file_name = ""

    if location_type == "estado":
        for li_tag in soup.find_all('li'):
            a_tag = li_tag.find('a')
            if a_tag and "Vendas de derivados petróleo e etanol" in a_tag.get_text():
                if a_tag['href'].endswith('.csv'):
                    link = a_tag['href']
                    
                    span_tag = li_tag.find('span')
                    updated_at = span_tag.get_text() if span_tag else None
                    list_urls.append(link)
                    file_name = f'{unidecode(location_type)}_{updated_at}' 
                    
        return list_urls, file_name
    for h3 in h3_tags:
        if location_type in h3.text:
            # Find all <ul> tags that are after the <h3> tag
            ul_tags = h3.find_all_next('ul')
            for ul_tag in ul_tags:
                if ul_tag:
                    # Loop through all <li> tags in the <ul>
                    for li in ul_tag.find_all('li'):
                        # Look for <b> tags inside each <li>
                        b_tag = li.find('b')
                        if b_tag and fuel_type in b_tag.text:
                            # Now, find the next <ul> tag after the current <ul> and search for <a> with .csv link
                            next_ul = ul_tag.find_next('ul')
                            # print(next_ul)
                            if next_ul:
                                # Look for all <a> tags in the next <ul> with .csv in the href
                                a_tags = next_ul.find_all('a', href=True)
                                li_tags = next_ul.find_all('li')
                                # print(li_tags[1].text)
                                for index, a_tag in enumerate(a_tags):
                                    # print(a_tag)
                                    if a_tag and a_tag['href'].endswith('.csv'):
                                        link_csv = a_tag['href']
                                        
                                        # se for municipio pega correto o anual
                                        if unidecode(location_type) == "municipio":
                                            csv_file = link_csv.split("/")[-1]
                                            if unidecode(location_type) in csv_file:
                                                updated_at = re.findall(padrao_data, li_tags[index].text)[0]
                                                file_name = f'{unidecode(location_type)}_{fuel_type}_{updated_at}' 
                                                list_urls.append(a_tag['href']) 
                                            

    return list_urls, file_name


def scrapping_monthly_sales_state(soup):
    list_urls = []    
    file_names = []
    header = soup.find(lambda tag: tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"] and "Vendas de derivados de petróleo e etanol" in tag.text)
    if header:
        list_element = header.find_next("ul") or header.find_next("ol")
        list_items = list_element.find_all("li")
        for li_tag in list_items:
            a_tag = li_tag.find('a')
            if a_tag and "Vendas de derivados petróleo e etanol" in a_tag.get_text():
                if a_tag['href'].endswith('.csv'):
                    link = a_tag['href']
                    
                    span_tag = li_tag.find('span')
                    updated_at = span_tag.get_text() if span_tag else None
                    list_urls.append(link)
                    file_names.append(f'monthly_sales_state_{updated_at}')
                    
                    return list_urls, file_names
        
    # for li_tag in soup.find_all('li'):
    #     a_tag = li_tag.find('a')
        
    #     if a_tag and "Vendas de derivados petróleo e etanol" in a_tag.get_text():
    #         if a_tag['href'].endswith('.csv'):
    #             link = a_tag['href']
                
    #             span_tag = li_tag.find('span')
    #             updated_at = span_tag.get_text() if span_tag else None
    #             list_urls.append(link)
    #             file_name = f'monthly_sales_state_{updated_at}' 
                    
    return list_urls, file_names

def scrapping_yearly_sales_state(soup):
    list_urls = []    
    file_names = []

    header = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and 
                   'Vendas anuais de etanol hidratado e derivados de petróleo por estado (dados históricos)' in tag.text)

    if header:
        csv_links = header.find_all_next('a', href=True)

        list_urls = [link['href'] for link in csv_links if link['href'].endswith('.csv')]
        # file_names = [url.split("/")[-1].replace(".csv", "") for url in list_urls]
        for url in list_urls:
            filename = url.split("/")[-1].replace(".csv", "")
            seps = filename.split("-")
            anos = "-".join(seps[-2:])
            filename = "_".join(seps[0:-2])

            filename = filename+"_"+anos
            file_names.append(filename)
        return list_urls, file_names
        

def scrapping_yearly_sales_city(soup):
    h3_tags = soup.find_all('h3')
    list_urls = []    
    # Loop through each <h3> tag found
    padrao_data = r'\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}'
    file_names = []
    for h3 in h3_tags:
            # Find all <ul> tags that are after the <h3> tag
            ul_tags = h3.find_all_next('ul')
            for ul_tag in ul_tags:
                if ul_tag:
                    # Loop through all <li> tags in the <ul>
                    for li in ul_tag.find_all('li'):
                        # Look for <b> tags inside each <li>
                        b_tag = li.find('b')
                        if b_tag:
                            # Now, find the next <ul> tag after the current <ul> and search for <a> with .csv link
                            next_ul = ul_tag.find_next('ul')
                            # print(next_ul)
                            if next_ul:
                                # Look for all <a> tags in the next <ul> with .csv in the href
                                a_tags = next_ul.find_all('a', href=True)
                                li_tags = next_ul.find_all('li')
                                # print(li_tags[1].text)
                                for index, a_tag in enumerate(a_tags):
                                    # print(a_tag)
                                    if a_tag and a_tag['href'].endswith('.csv'):
                                        link_csv = a_tag['href']
                                        # se for municipio pega correto o anual
                                        if "municipio" in link_csv:
                                            derivado = (link_csv.split("/")[-2]).replace("-","")
                                            updated_at = re.findall(padrao_data, li_tags[index].text)
                                            updated_at = updated_at[0]
                                            file_names.append(f'yearly_sales_city_{derivado}_{updated_at}')
                                            list_urls.append(link_csv) 

            return list_urls, file_names

def scrapping_production_monthly(soup):
    list_urls = []    
    file_names = []
    # Expanded pattern to catch various date formats
    padrao_data = r'\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{4}-\d{1,2}-\d{1,2}'
    target_h3 = soup.find('h3', text="Produção de petróleo")
    
    if not target_h3:
        print("Warning: 'Produção de petróleo' heading not found. Trying alternative headings...")
        possible_headings = ["Produção de petróleo", "Produção de Petróleo", "Produção Nacional do Petróleo", "Produção"]
        for heading in possible_headings:
            target_h3 = soup.find('h3', string=lambda text: heading in text if text else False)
            if target_h3:
                print(f"Found alternative heading: {target_h3.text}")
                break

    if target_h3:
        ul_list = target_h3.find_all_next('ul')
        
        if not ul_list:
            print("Warning: No <ul> elements found after the heading. Trying to find links directly...")
            # Try to find the next div that might contain links
            next_div = target_h3.find_next('div')
            if next_div:
                for a_tag in next_div.find_all('a', href=lambda href: href and href.endswith('.csv')):
                    handle_csv_link(a_tag, a_tag.parent.text, list_urls, file_names)
        else:
            for ul in ul_list:
                for li in ul.find_all('li'):
                    for a_tag in li.find_all('a'):
                        if a_tag['href'].endswith('.csv'):
                            handle_csv_link(a_tag, li.text, list_urls, file_names)
        
        if not list_urls:
            print("Warning: No CSV links found. Looking for links across the entire page...")
            # Fallback: look for any CSV link on the page
            for a_tag in soup.find_all('a', href=lambda href: href and href.endswith('.csv')):
                handle_csv_link(a_tag, a_tag.parent.text, list_urls, file_names)
    else:
        print("Error: No suitable heading found. Searching for any CSV files on the page...")
        # Last resort: look for any CSV link on the page
        for a_tag in soup.find_all('a', href=lambda href: href and href.endswith('.csv')):
            handle_csv_link(a_tag, a_tag.parent.text, list_urls, file_names)
    
    if list_urls:
        print(f"Found {len(list_urls)} CSV files.")
        return list_urls, file_names
    else:
        # Create a dummy entry if nothing is found to prevent crashes
        print("Warning: No CSV files found. Creating a placeholder.")
        dummy_url = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/producao-mensal-petroleo-gas-natural-por-campo-2014-a-2021.csv"
        list_urls.append(dummy_url)
        file_names.append("producao_mensal_petroleo_gas_natural_por_campo_01-01-2023")
        return list_urls, file_names

def handle_csv_link(a_tag, text, list_urls, file_names):
    """Helper function to process CSV links and add them to the result lists."""
    # Try to find a date in the text
    padrao_data = r'\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{4}-\d{1,2}-\d{1,2}'
    date_matches = re.findall(padrao_data, text)
    
    if date_matches:
        updated_at = date_matches[0]
    else:
        # If no date found, use today's date
        from datetime import datetime
        updated_at = datetime.now().strftime("%d/%m/%Y")
        print(f"No date found in text: '{text[:50]}...' - Using current date: {updated_at}")
    
    # Format the name from the text
    formatted_name = formatar_monthly_oilgas_operations_by_state(text)
    if not formatted_name:
        # Extract a name from the href if text formatting fails
        href = a_tag['href']
        base_name = os.path.basename(href).split('.')[0]
        formatted_name = re.sub(r'[^\w]', '_', base_name).lower()
    
    file_name = f'{formatted_name}_{updated_at}'
    list_urls.append(a_tag['href'])
    file_names.append(file_name)                                          


def formatar_monthly_oilgas_operations_by_state(texto):
    """Format petroleum and gas related texts into a standardized snake_case format.
    
    Args:
        texto: The text to format, often contains product name followed by metadata in parentheses
        
    Returns:
        str: Formatted text in snake_case, or filename-friendly string derived from the input
    """
    if not texto or not isinstance(texto, str):
        return "petroleum_gas_data"
    
    # Try different patterns to extract a meaningful name
    patterns = [
        r"^(.*?) \(",               # Text before first parenthesis
        r"Produção de (.*?)(?:\s|$)",  # Text after "Produção de"
        r"dados de (.*?)(?:\s|$)",     # Text after "dados de"
        r"(petróleo|gás|natural).*"     # Any text containing key oil/gas terms
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            if nome:  # If we got a non-empty string
                nome_snake_case = re.sub(r"[^\w\s]", "", nome).replace(" ", "_").lower()
                return unidecode(nome_snake_case)
    
    # Fallback: just clean the whole text if no patterns match
    # First, truncate to a reasonable length
    texto_truncated = texto[:50]  
    # Remove special characters and convert spaces to underscores
    nome_snake_case = re.sub(r"[^\w\s]", "", texto_truncated).replace(" ", "_").lower()
    # Return the unidecoded version
    result = unidecode(nome_snake_case)
    
    # Make sure we have at least something reasonable
    if not result or len(result) < 3:
        return "petroleum_gas_data"
        
    return result

def scrape_for_file_links(url, data_type, frequency, location_type):
    """
    Scrape a given URL for links to files with specific extensions (.csv, .zip) and return a list of these file URLs.

    Args:
    url (str): The URL of the website to scrape.

    Returns:
    list: A list of URLs (str) pointing to files ending with .csv or .zip. The list will be empty if no such links are found or if the page fails to load.

    The function makes an HTTP GET request to the provided URL. If the request is successful, it parses the HTML content to find all anchor tags with an 'href' attribute that ends with '.csv' or '.zip'. It adds these URLs to a list which is then returned. If the request is unsuccessful, it prints an error message with the failed status code.
    """
    list_urls = []
    # Make a GET request to fetch the raw HTML content
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if data_type == "sales":
            if frequency == "monthly":
                return scrapping_monthly_sales_state(soup) 
            elif frequency == "yearly":
                if location_type == "city":
                    return scrapping_yearly_sales_city(soup)
                elif location_type == "state":
                     return scrapping_yearly_sales_state(soup)
        elif data_type == "production":
            if frequency == "monthly":
                return scrapping_production_monthly(soup)
        else:
            return "not exists"
        
        # Loop through all found <a> tags
        # for link in links:
        #     # Extract the URL from the 'href' attribute
        #     href = link['href']
            
        #     # Extract the text of the <a> tag
        #     text = link.get_text()

        #     if href.endswith('.csv') or href.endswith('.zip') :
        #         if type == "state":
        #             if href.contains("estado"):
        #                 list_urls.append(href)
        #         elif type == "city":
        #             if href.contains("municipio"):
        #                 list_urls.append(href)
    else:
        print(f"Failed to retrieve the website: status code {response.status_code}")
    return list_urls

def download_file_directly(url, folder, filename=None, max_retries=10):
    """
    Download a file from a specified URL directly to a given folder with optional retry logic.

    Args:
    url (str): The URL from which to download the file.
    folder (str): The local directory path where the file will be saved.
    filename (str, optional): The name to save the file as. If not provided, the name is taken from the last segment of the URL.
    max_retries (int, optional): The maximum number of retries if the download fails. Defaults to 20.

    Returns:
    str: A message indicating the success or failure of the download. Success messages include the path where the file was saved, and failure messages include an error code or description.

    This function attempts to download a file by making a GET request to the provided URL. If the request is successful and the server responds with a 200 status code, the file is written to the specified location in chunks. If the server response indicates a failure (any status code other than 200), or if an exception occurs during download, the function will retry the download up to `max_retries` times before giving up. The wait time between retries is 10 seconds.
    """
    attempts = 0
    
    while attempts < max_retries:
        try:
            if not filename:
                filename = url.split('/')[-1]
            file_path = os.path.join(folder, filename)
            # print(f"Downloading {url} to {file_path}...")
            exists = os.path.isfile(file_path)
            if not exists:
                
                splits = filename.split("_")[0:-1]
                name_file = "_".join(splits)
                for f in os.listdir(folder):
                    if f.endswith('.csv') and name_file in f:
                        old_file = os.path.join(folder, f)
                        os.remove(old_file) #remove old files unused
                
                with requests.get(url, stream=True) as response:
                    # print(f"Response Status Code: {response.status_code}")

                    if response.status_code == 200:
                        # print("Saving file...")
                        with open(file_path, 'wb') as file:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    file.write(chunk)
                        # print(f"\033[32mFile saved successfully at {file_path}\033[0m")
                        return True
                    else:
                        return False
                    
            return True
        except (ChunkedEncodingError, IncompleteRead) as e:
            print(f"\033[31mAn error occurred: {e}\033[0m. Retrying in 5 seconds...")
            time.sleep(10)  # Corrected to show 10 seconds as per your retry sleep
            attempts += 1
        except Exception as e:
            print(f"\033[31mAn error occurred: {e}\033[0m")
            return False

    return False

def download_github_backup(file_name, download_path='./'):
    """
    Download backup dataset files from GitHub when ANP website scraping fails.
    
    Args:
        file_name (str): Name of the backup file to download
        download_path (str): Directory where the file will be saved. Default is './'.
        
    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    try:
        import subprocess
        import tempfile
        import shutil
        
        print(f"Trying to download backup dataset {file_name}")
        
        temp_dir = tempfile.mkdtemp()
        
        clone_command = ["git", "clone", "https://github.com/lucas-castrow/datasets_streamfuels.git", temp_dir]
        subprocess.run(clone_command, check=True, capture_output=True)
        
        backup_file_path = os.path.join(temp_dir, file_name)
        if os.path.exists(backup_file_path):
            os.makedirs(download_path, exist_ok=True)
            
            target_path = os.path.join(download_path, file_name)
            shutil.copy2(backup_file_path, target_path)
            
            print(f"Successfully downloaded backup file {file_name} to {target_path}")
            
            shutil.rmtree(temp_dir)
            return target_path
        else:
            print(f"Error: Backup file {file_name} not found in GitHub repository")
            shutil.rmtree(temp_dir)
            return None
    except Exception as e:
        print(f"Error downloading backup file: {e}")
        return None

def download_anp_data(data_type="sales", location_type="state", frequency="monthly", download_path="./"):
    """
    Download data from various ANP URLs and organize it into specified folders.
    If ANP website fails, try to download backup files from GitHub repository.

    Args:
    folder_paths (list of str, optional): A base path list that determines where to create folders for each data category. Defaults to ['dados', 'raw_data'].
    data_type (str): Type of data to download ('sales', 'production', etc.)
    location_type (str): Location granularity ('state', 'city')
    frequency (str): Time frequency ('monthly', 'yearly')

    Returns:
    tuple: (file_names, isUpdated) - List of downloaded file names and a boolean indicating if data is updated
    """
    folder_paths=['dados', 'raw_data']
    dic = {
        'sales': 'https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/vendas-de-derivados-de-petroleo-e-biocombustiveis',
        # 'production_historic': 'https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/producao-de-petroleo-e-gas-natural-nacional',
        'production': 'https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/producao-de-petroleo-e-gas-natural-por-estado-e-localizacao',
        'import_export': 'https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/importacoes-e-exportacoes',
        'prices': 'https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis'
    }
    
    try:
        folder_path = os.path.join(*folder_paths, data_type)
        folder_path = ensure_folder_exists([folder_path])
        url = dic[data_type]
        links, file_names = scrape_for_file_links(url, data_type=data_type, frequency=frequency, location_type=location_type)
        
        if not links or not file_names:
            raise Exception("No links or file names found from ANP website")
            
        file_names = [file_name.replace("/", "-") + ".csv" for file_name in file_names]
        if len(links) != len(file_names):
            raise Exception("Problem loading url files from ANP website")
            
        isUpdated = False
        for i, link in enumerate(links):
            isUpdated = download_file_directly(url=link, filename=file_names[i], folder=folder_path)
            if '.zip' in link:
                file_name = link.split('/')[-1]
                unzip_and_delete(os.path.join(folder_path, file_name))
        return file_names, isUpdated
    
    except Exception as e:
        print(f"Failed to download data from ANP website: {e}")
        print("Using backup data from GitHub repository instead...")
        
        # Map the parameters to the corresponding backup file name
        backup_file_mapping = {
            ('sales', 'state', 'monthly'): 'monthly_fuel_sales_by_state.tsf',
            ('sales', 'state', 'yearly'): 'yearly_fuel_sales_by_state.tsf',
            ('sales', 'city', 'yearly'): 'yearly_fuel_sales_by_city.tsf',
            ('production', 'state', 'monthly'): 'monthly_oil_gas_operations_by_state.tsf'
        }
        
        backup_file = backup_file_mapping.get((data_type, location_type, frequency))
        
        if not backup_file:
            print(f"No backup file mapping for {data_type}, {location_type}, {frequency}")
            return [], False
            
        # Try to download the backup file
        backup_path = download_github_backup(backup_file, download_path=download_path)
        
        if backup_path:
            # Return a dummy file name and False for isUpdated since we're using backup data
            return [backup_file], False
        else:
            # If backup download also fails, return empty lists
            return [], False
# download_anp_data()