
import os
import zipfile
from unidecode import unidecode
import re
import pandas as pd
import numpy as np

def znorm(x):
    std = np.std(x)
    if std == 0:
        return x - np.mean(x)
    return (x - np.mean(x)) / std

def translate_fuel_name(fuel_name):
    fuel_mapping = {
        'ethanol': 'Etanol hidratado',
        'gasoline-r': 'Gasolina C',
        'gasoline-a': 'Gasolina de aviação',
        'fuel oil': 'Óleo combustível',
        'LPG': 'GLP',
        'diesel': 'Óleo diesel',
        'kerosene-i': 'Querosene iluminante',
        'kerosene-a': 'Querosene de aviação',
        'etanol': 'ethanol'
    }
    if fuel_name.lower() not in fuel_mapping:
        print(f"Fuel name '{fuel_name}' not found in mapping.")
    return fuel_mapping.get(fuel_name.lower(), "Invalid")

def prod_to_en(prod):
    prods = {
        'petroleo': 'petroleum',
        'lgn': 'NGL',      
        'gasnatural': 'natural gas'
        
    }
    return prods.get(prod.lower(), "Invalid")


def fuel_pt_to_en(fuel_name):
    fuel_mapping = {
        'etanolhidratado':'ethanol',
        'gasolinac':'gasoline-r',
        'gasolinadeaviacao':'gasoline-a',
        'oleocombustivel':'fuel oil',
        'glp':'LPG', 
        'oleodiesel':'diesel',
        'queroseneiluminante':'kerosene-i',
        'querosenedeaviacao':'kerosene-a',
        'asfalto':'asphalt',
        'etanol': 'ethanol'
    }
    if fuel_name.lower() not in fuel_mapping:
        print(f"Fuel name '{fuel_name}' not found in mapping.")
    return fuel_mapping.get(fuel_name.lower(), "Invalid")


def get_default_download_dir():
    """Return the default directory for downloads."""
    default_dir = os.path.join(os.path.expanduser("~"), ".streamfuels")
    if not os.path.exists(default_dir):
        os.makedirs(default_dir)
    return default_dir
def unzip_and_delete(zip_file_path):
    """
    Unzips a ZIP file and deletes the original ZIP file after extraction.
    
    Parameters:
    - zip_file_path: Path to the ZIP file.
    """
    # Check if the file exists and is a zip file
    if not zipfile.is_zipfile(zip_file_path):
        print(f"The file at {zip_file_path} is not a valid zip file.")
        return

    try:
        # Create a ZipFile object in read mode
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Extract all the contents into the directory of the zip file
            extract_path = os.path.dirname(zip_file_path)
            zip_ref.extractall(extract_path)
            print(f"Extracted all contents to {extract_path}")

        # Remove the original ZIP file
        os.remove(zip_file_path)
        print(f"Deleted original zip file: {zip_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def parse_string(string):
    return re.sub(r'[^a-zA-Z0-9]', '', unidecode(str(string).lower()))

def mes_para_numero(mes):
    """Convert month name to number, handling different input types.
    
    Args:
        mes: Month name as string, float, or other type. If float, will be converted to string first.
        
    Returns:
        str: Two-digit month number as string
    """
    # Handle different input types
    if mes is None or pd.isna(mes):
        return '01'  # Default to January if None or NaN
    
    # Convert to string if needed
    if not isinstance(mes, str):
        mes = str(mes)
    
    # Remove decimal part if present
    if '.' in mes:
        mes = mes.split('.')[0]
    
    # Map of month names to numbers
    meses = {
        'JAN': '01', 'FEV': '02', 'MAR': '03', 'ABR': '04',
        'MAI': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
        'SET': '09', 'OUT': '10', 'NOV': '11', 'DEZ': '12',
        # Add direct number mapping for numeric months
        '1': '01', '2': '02', '3': '03', '4': '04',
        '5': '05', '6': '06', '7': '07', '8': '08',
        '9': '09', '10': '10', '11': '11', '12': '12'
    }
    
    # Try to get the month number, defaulting to '01' if not found
    try:
        return meses.get(mes.upper(), '01')
    except AttributeError:
        # If any other error occurs, default to January
        return '01'

def ensure_folder_exists(parts):
    """
    Checks if a folder exists, and creates it (including any necessary parent directories)
    if it doesn't.

    Parameters:
    - folder_path: The path to the folder to check and create.
    """
    file_path = get_default_download_dir()
    p = os.path.join(file_path, *parts)
    
    if not os.path.exists(p):
        os.makedirs(p)
    return p

def estado_para_sigla(estado):
    # Mapeamento dos nomes dos estados para suas siglas
    estados = {
        'acre': 'ac',
        'alagoas': 'al',
        'amapa': 'ap',
        'amazonas': 'am',
        'bahia': 'ba',
        'ceara': 'ce',
        'distritofederal': 'df',
        'espiritosanto': 'es',
        'goias': 'go',
        'maranhao': 'ma',
        'matogrosso': 'mt',
        'matogrossodosul': 'ms',
        'minasgerais': 'mg',
        'para': 'pa',
        'paraiba': 'pb',
        'parana': 'pr',
        'pernambuco': 'pe',
        'piaui': 'pi',
        'riodejaneiro': 'rj',
        'riograndedonorte': 'rn',
        'riograndedosul': 'rs',
        'rondonia': 'ro',
        'roraima': 'rr',
        'santacatarina': 'sc',
        'saopaulo': 'sp',
        'sergipe': 'se',
        'tocantins': 'to'
    }
    
    return estados.get(estado, 'Undefined')

def obter_max_min_datas(df, col_data, mes_ou_ano):
    """Get the maximum and minimum dates from a DataFrame column.
    
    Args:
        df: DataFrame containing the data
        col_data: Column name containing date information
        mes_ou_ano: Type of date information ('ano' for year, any other value for month)
        
    Returns:
        tuple: (max_date, min_date)
    """
    # Make a copy to avoid changing the original DataFrame
    date_series = df[col_data].copy()
    
    # Filter out any NaN values
    date_series = date_series[~pd.isna(date_series)]
    
    if date_series.empty:
        print(f"Warning: No valid dates found in column {col_data}")
        # Return default values if no valid dates are found
        return ('2020', '2000') if mes_ou_ano == 'ano' else ('202001', '200001')
    
    # Process differently based on date type
    if mes_ou_ano == 'ano':
        try:
            # Try to convert directly to int
            date_series = date_series.astype(int)
        except ValueError:
            # If that fails, clean the data first
            date_series = date_series.astype(str)
            # Extract just the year part if there's a decimal
            date_series = date_series.apply(lambda x: x.split('.')[0] if '.' in x else x)
            # Remove any non-digit characters
            date_series = date_series.str.extract(r'(\d+)', expand=False)
            # Convert to integer
            date_series = pd.to_numeric(date_series, errors='coerce')
            # Drop any NaN values that might have been introduced
            date_series = date_series.dropna()
        
        max_date = date_series.max()
        min_date = date_series.min()
    else:
        # For monthly data
        try:
            # Clean the data first
            date_series = date_series.astype(str)
            # Remove dashes to get format YYYYMM
            clean_dates = date_series.str.replace("-", "")
            # Convert to numeric and handle errors
            numeric_dates = pd.to_numeric(clean_dates, errors='coerce')
            # Drop any NaN values
            numeric_dates = numeric_dates.dropna()
            
            max_date = numeric_dates.max()
            min_date = numeric_dates.min()
        except Exception as e:
            print(f"Error processing dates: {e}")
            print("Sample dates:", date_series.head())
            # Use default values if processing fails
            max_date = 202001
            min_date = 200001
    
    return max_date, min_date

def kg_to_m3(material, kg):
    #https://www.gov.br/anp/pt-br/centrais-de-conteudo/publicacoes/anuario-estatistico/arquivos-anuario-estatistico-2022/outras-pecas-documentais/fatores-conversao-2022.pdf
    densidades = { #em TERA / M3
        'etanolanidro': 0.79100,
        'etanolhidratado': 0.80900,
        'asfalto': 1025.00,
        'biodieselb100': 880.00,
        'gasolinac': 754.25,
        'gasolinadeaviacao': 726.00,
        'glp': 552.00,
        'lgn': 580.00,
        'oleodiesel': 840.00,
        'oleocombustivel': 1013.00,
        'petroleo': 849.76,
        'querosenedeaviacao': 799.00,
        'queroseneiluminante': 799.00,
        'solventes': 741.00
    }
    
    if material in densidades:
        densidade = densidades[material] / 1e3  # Convertendo para kg/m³
        m3 = kg / densidade
        return m3
    else:
        return "Material não encontrado na lista."

def registrar_meses_duplicados(df, produto, local, tempo):
    #os.remove(f'timestamps_duplicadas_{tempo}.csv') if os.path.exists(f'timestamps_duplicadas_{tempo}.csv') else None
    df_c = df.copy()
    df_c['duplicatas'] = df_c.groupby('timestamp')['timestamp'].transform('count') - 1
    df_c = df_c[df_c['duplicatas']>=1]
    df_c['derivado'] = produto
    df_c['local'] = local
    df_c.to_csv(f'timestamps_duplicadas_{tempo}.csv', mode='a', header=False, index=False)
    
def combinar_valores_unicos_colunas(df, colunas):
    # Agrupar pelo conjunto de colunas e resetar o índice para transformar em DataFrame
    df_unicos = df[colunas].drop_duplicates().reset_index(drop=True)
    
    # Converter o DataFrame resultante em uma lista de tuplas
    combinacoes_existentes = [tuple(x) for x in df_unicos.values]
    
    return combinacoes_existentes

def first_non_nan_value(df, column_name):
    """
    Find the first non-NaN value in the specified column of a DataFrame.

    Args:
    df (DataFrame): The pandas DataFrame.
    column_name (str): The name of the column to search for non-NaN values.

    Returns:
    The first non-NaN value in the specified column, or None if no non-NaN values are found.
    """
    first_non_nan_index = df[column_name].first_valid_index()
    if first_non_nan_index is not None:
        return df[column_name].iloc[first_non_nan_index]
    else:
        return None
    
def last_non_nan_value(df, column_name):
    """
    Find the last non-NaN value in the specified column of a DataFrame.

    Args:
    df (DataFrame): The pandas DataFrame.
    column_name (str): The name of the column to search for non-NaN values.

    Returns:
    The last non-NaN value in the specified column, or None if no non-NaN values are found.
    """
    last_non_nan_index = df[column_name].last_valid_index()
    if last_non_nan_index is not None:
        return df[column_name].iloc[last_non_nan_index]
    else:
        return None

def find_first_sequence(arr):
    """
    Find the first sequence of consecutive elements in the given array.

    Args:
        arr (list): The input list of integers.

    Returns:
        list: The list containing the first sequence of consecutive elements.
    """
    if not arr:
        return []  # Return an empty list if the input array is empty
    
    sequence = [arr[0]]  # Start with the first element
    for i in range(1, len(arr)):
        # If the current element is consecutive with the previous one, add it to the sequence
        if arr[i] == sequence[-1] + 1:
            sequence.append(arr[i])
        else:
            break  # Break the loop when the sequence breaks
    return sequence

def find_last_sequence(arr):
    """
    Find the last sequence of consecutive elements in the given array.

    Args:
        arr (list): The input list of integers.

    Returns:
        list: The list containing the last sequence of consecutive elements.
    """
    if not arr:
        return []  # Return an empty list if the input array is empty
    
    sequence = [arr[-1]]  # Start with the last element
    for i in range(len(arr) - 2, -1, -1):
        # If the current element is consecutive with the next one, add it to the sequence
        if arr[i] == sequence[-1] - 1:
            sequence.append(arr[i])
        else:
            break  # Break the loop when the sequence breaks
    sequence.reverse()  # Reverse the sequence to have it in ascending order
    return sequence
    