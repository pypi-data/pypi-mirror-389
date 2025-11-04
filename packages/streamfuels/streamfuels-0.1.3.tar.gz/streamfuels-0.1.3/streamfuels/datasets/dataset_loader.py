import pandas as pd
from .extract import *
from .transform import *
from distutils.util import strtobool
from datetime import datetime


class DatasetLoader:
    """Handle datasets provided by CISIA

    monthly_sales_state(): monthly fuel sales data by state from the ANP database

    yearly_sales_state(): yearly fuel sales data by state from ANP database

    yearly_sales_city(): yearly fuel sales data by city from ANP database

    monthly_operations_state(): monthly oil production, NGL production, natural gas production, reinjection, flaring and losses, self-consumption, and available natural gas. It provides a comprehensive view of petroleum and gas operations.

    """

    @staticmethod
    def monthly_sales_state(download_path="./", data_prepared=True):
        """
        Processes and returns the path to the TSF file containing monthly sales data by state from the ANP database.
        It also indicates if the data is the most recently updated.

         Args:
             download_path (str): Directory where the TSF file will be saved after download and processing. Default is './'.
             data_prepared (bool): Indicates whether the dataset should be processed and ready for use.

                                 - True: The dataset will be cleaned, removing missing values and outliers.
                                 - False: The dataset will include missing values and outliers.

         Returns:
             str: Path to the processed TSF file.
             bool: If the dataset returned is the last update.
        """
        filenames, isUpdated = download_anp_data(
            data_type="sales",
            location_type="state",
            frequency="monthly",
            download_path=download_path,
        )

        # Check if we got a backup .tsf file directly
        if filenames and filenames[0].endswith(".tsf"):
            # Backup file was used, return the path to it
            backup_path = os.path.join(download_path, filenames[0])
            if os.path.exists(backup_path):
                print(f"Using backup dataset: {backup_path}")
                return backup_path, isUpdated

        # If we have normal CSV files or backup file wasn't found
        if not filenames:
            print("Failed to get data files and backup was not available.")
            return None, False

        if len(filenames) > 1:
            print(
                "Warning: Multiple files found from ANP website, using the first one."
            )

        tsf_path = processar_dpee_mes_estado(
            download_path, filenames=filenames, data_prepared=data_prepared
        )
        print(f"Dataset downloaded at: {tsf_path}")
        return tsf_path, isUpdated

    @staticmethod
    def yearly_sales_state(download_path="./", data_prepared=True):
        """
        Processes and returns the path to the TSF file containing yearly sales data by state from ANP database.
        It also indicates if the data is the most recently updated.

        Args:
            download_path (str): Directory where the TSF file will be saved after download and processing. Default is './'.
            data_prepared (bool): Indicates whether the dataset should be processed and ready for use.

                                - True: The dataset will be cleaned, removing missing values and outliers.
                                - False: The dataset will include missing values and outliers.

        Returns:
            str: Path to the processed TSF file.
            bool: If the dataset returned is the last update.
        """
        filenames, isUpdated = download_anp_data(
            data_type="sales",
            location_type="state",
            frequency="yearly",
            download_path=download_path,
        )

        # Check if we got a backup .tsf file directly
        if filenames and filenames[0].endswith(".tsf"):
            # Backup file was used, return the path to it
            backup_path = os.path.join(download_path, filenames[0])
            if os.path.exists(backup_path):
                print(f"Using backup dataset: {backup_path}")
                return backup_path, isUpdated

        # If we have normal CSV files or backup file wasn't found
        if not filenames:
            print("Failed to get data files and backup was not available.")
            return None, False

        tsf_path = processar_dpee_ano_estado(
            download_path, filenames=filenames, data_prepared=data_prepared
        )
        print(f"Dataset downloaded at: {tsf_path}")
        return tsf_path, isUpdated

    @staticmethod
    def yearly_sales_city(download_path="./", data_prepared=True):
        """
        Processes and returns the path to the TSF file containing yearly sales data by city from ANP database.
        It also indicates if the data is the most recently updated.

        Args:
            download_path (str): Directory where the TSF file will be saved after download and processing. Default is './'.
            data_prepared (bool): Indicates whether the dataset should be processed and ready for use.

                                - True: The dataset will be cleaned, removing missing values and outliers.
                                - False: The dataset will include missing values and outliers.

        Returns:
            str: Path to the processed TSF file.
            bool: If the dataset returned is the last update.
        """
        filenames, isUpdated = download_anp_data(
            data_type="sales",
            location_type="city",
            frequency="yearly",
            download_path=download_path,
        )

        # Check if we got a backup .tsf file directly
        if filenames and filenames[0].endswith(".tsf"):
            # Backup file was used, return the path to it
            backup_path = os.path.join(download_path, filenames[0])
            if os.path.exists(backup_path):
                print(f"Using backup dataset: {backup_path}")
                return backup_path, isUpdated

        # If we have normal CSV files or backup file wasn't found
        if not filenames:
            print("Failed to get data files and backup was not available.")
            return None, False

        tsf_path = processar_derivados_municipio_ano(
            download_path=download_path,
            filenames=filenames,
            data_prepared=data_prepared,
        )
        print(f"Dataset downloaded at: {tsf_path}")
        return tsf_path, isUpdated

    @staticmethod
    def monthly_operations_state(download_path="./"):
        """
        Processes and returns the path to the TSF file containing monthly oil production, NGL production, natural gas production, reinjection, flaring and losses, self-consumption, and available natural gas. It provides a comprehensive view of petroleum and gas operations.
        It also indicates if the data is the most recently updated.

         Args:
             download_path (str): Directory where the TSF file will be saved after download and processing. Default is './'.
         Returns:
             str: Path to the processed TSF file.
             bool: If the dataset returned is the last update.
        """
        filenames, isUpdated = download_anp_data(
            data_type="production",
            location_type="state",
            frequency="monthly",
            download_path=download_path,
        )

        # Check if we got a backup .tsf file directly
        if filenames and filenames[0].endswith(".tsf"):
            # Backup file was used, return the path to it
            backup_path = os.path.join(download_path, filenames[0])
            if os.path.exists(backup_path):
                print(f"Using backup dataset: {backup_path}")
                return backup_path, isUpdated

        # If we have normal CSV files or backup file wasn't found
        if not filenames:
            print("Failed to get data files and backup was not available.")
            return None, False

        tsf_path = processar_producao(download_path, filenames=filenames)
        print(f"Dataset downloaded at: {tsf_path}")
        return tsf_path, isUpdated

    @staticmethod
    def download_anp(
        download_path="./", transaction_type=None, location_type=None, fuel_type=None
    ):
        """
        Downloads actual data from ANP based on the transaction type, location type, and fuel type.

        Parameters:
            transaction_type (str): The type of transaction. Can be one of the following:
                - "sales": Data about sales of petroleum derivatives and ethanol, fuel sales by segment and type, and annual sales by municipality and state.
                - "import": Data on imports of petroleum, natural gas, petroleum derivatives, and ethanol.
                - "export": Data on exports of petroleum, natural gas, petroleum derivatives, and ethanol.
                - "price": Data on fuel prices, including automotive fuels and liquefied petroleum gas (LPG) in 13 kg cylinders, collected through a weekly survey conducted by a contracted company.

            location_type (str): The type of location for the data. It can be:
                - "state": Data on a state level.
                - "city": Data on a city level (will include `fuel_type` when "sales" transaction type).

            fuel_type (str, optional): The type of fuel. This parameter is required when `transaction_type` is "sales" and `location_type` is "city". Possible values are:
                - "ethanol": Ethanol data.
                - "gasoline-r": Regular gasoline data
                - "gasoline-a": Aviation gasoline data
                - "diesel": Diesel oil data.
                - "LPG": Liquefied petroleum gas data.
                - "oil": Fuel oil data.
                - "kerosene-i": Illuminating kerosene data.
                - "kerosene-a": Aviation kerosene

        This method will download the respective dataset based on the provided parameters and then process the data.
        """
        if (
            transaction_type == "sales"
            and location_type == "city"
            and fuel_type is None
        ):
            raise ValueError(
                "fuel_type is required when transaction_type is 'sales' and location_type is 'city'. Please provide a valid fuel_type."
            )

        filename = download_anp_data(
            transaction_type=transaction_type,
            location_type=location_type,
            fuel_type=fuel_type,
        )

        if location_type == "state":
            tsf_path = processar_dpee_mes_estado(download_path, filename=filename)
        elif location_type == "city":
            tsf_path = processar_derivados_municipio_ano(
                download_path=download_path, filename=filename, fuel_type=fuel_type
            )

        return tsf_path

    @staticmethod
    def fuel_type_classification(window_size=12, step=6, download_path="./"):
        filename = "fuel_type_classification.tsf"

        # Try to download directly from GitHub first as a backup
        # from .extract import download_github_backup
        # backup_path = download_github_backup('fuel_type_classification.tsf', download_path=download_path)

        # if backup_path:
        #     print(f"Using backup dataset for fuel_type_classification: {backup_path}")
        #     try:
        #         df_backup = pd.read_csv(backup_path)
        #         return df_backup
        #     except Exception as e:
        #         print(f"Error reading backup file: {e}")
        #         print("Trying to generate from raw data...")

        # If backup failed or doesn't exist, try normal approach
        try:
            filenames, _ = download_anp_data(
                data_type="sales",
                location_type="state",
                frequency="monthly",
                download_path=download_path,
            )

            # If we got a backup TSF file for monthly_sales_state
            if (
                filenames
                and filenames[0].endswith(".tsf")
                and "monthly" in filenames[0]
            ):
                backup_path = os.path.join(download_path, filenames[0])
                if os.path.exists(backup_path):
                    print(
                        f"Using backup sales dataset to generate classification: {backup_path}"
                    )
                    tsf_path = backup_path
                else:
                    if not filenames:
                        print("Failed to get data files and backup was not available.")
                        return None
                    if len(filenames) > 1:
                        print(
                            "Warning: Multiple files found from ANP website, using the first one."
                        )
                    tsf_path = processar_dpee_mes_estado(
                        download_path, filenames=filenames, data_prepared=True
                    )
            else:
                if not filenames:
                    print("Failed to get data files and backup was not available.")
                    return None
                if len(filenames) > 1:
                    print(
                        "Warning: Multiple files found from ANP website, using the first one."
                    )
                tsf_path = processar_dpee_mes_estado(
                    download_path, filenames=filenames, data_prepared=True
                )

            df, metadata = DatasetLoader.read_tsf(path_tsf=tsf_path)
            targets = []
            windows = []
            for i in range(len(df)):
                series = np.array(df.iloc[i]["series_value"])
                target = df.iloc[i]["product"]
                for start in range(0, len(series) - window_size + 1, step):
                    window = znorm(series[start : start + window_size])
                    if not np.all(window) == 0:
                        windows.append(window)
                        targets.append(target)

            if not windows or not targets:
                raise Exception(
                    "Failed to create windows and targets for classification"
                )

            data = np.array(windows)
            n_features = data.shape[1]
            column_names = [f"t{i+1}" for i in range(n_features)]
            df = pd.DataFrame(data, columns=column_names)
            df["label"] = targets

            output_path = os.path.join(download_path, filename)
            df.to_csv(output_path, index=False)
            print(f"Dataset generated at: {output_path}")
            return df

        except Exception as e:
            print(f"Error generating fuel type classification: {e}")
            return None

    @staticmethod
    def read_tsf(
        path_tsf,
        replace_missing_vals_with="NaN",
        value_column_name="series_value",
    ):
        col_names = []
        col_types = []
        all_data = {}
        line_count = 0
        frequency = None
        forecast_horizon = None
        contain_missing_values = None
        contain_equal_length = None
        found_data_tag = False
        found_data_section = False
        started_reading_data_section = False

        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1", "windows-1252"]
        file_content = None

        for encoding in encodings:
            try:
                with open(path_tsf, "r", encoding=encoding) as file:
                    file_content = file.readlines()
                break
            except UnicodeDecodeError:
                continue

        if file_content is None:
            with open(path_tsf, "r", encoding="utf-8", errors="ignore") as file:
                file_content = file.readlines()

        for line in file_content:
            line = line.strip()

            if line:
                if line.startswith("@"):
                    if not line.startswith("@data"):
                        line_content = line.split(" ")
                        if line.startswith("@attribute"):
                            if (
                                len(line_content) != 3
                            ):  # Attributes have both name and type
                                raise Exception("Invalid meta-data specification.")

                            col_names.append(line_content[1])
                            col_types.append(line_content[2])
                        else:
                            if (
                                len(line_content) != 2
                            ):  # Other meta-data have only values
                                raise Exception("Invalid meta-data specification.")

                            if line.startswith("@frequency"):
                                frequency = line_content[1]
                            elif line.startswith("@horizon"):
                                forecast_horizon = int(line_content[1])
                            elif line.startswith("@missing"):
                                contain_missing_values = bool(
                                    strtobool(line_content[1])
                                )
                            elif line.startswith("@equallength"):
                                contain_equal_length = bool(strtobool(line_content[1]))

                    else:
                        if len(col_names) == 0:
                            raise Exception(
                                "Missing attribute section. Attribute section must come before data."
                            )

                        found_data_tag = True
                elif not line.startswith("#"):
                    if len(col_names) == 0:
                        raise Exception(
                            "Missing attribute section. Attribute section must come before data."
                        )
                    elif not found_data_tag:
                        raise Exception("Missing @data tag.")
                    else:
                        if not started_reading_data_section:
                            started_reading_data_section = True
                            found_data_section = True
                            all_series = []

                            for col in col_names:
                                all_data[col] = []

                        full_info = line.split(":")

                        if len(full_info) != (len(col_names) + 1):
                            raise Exception("Missing attributes/values in series.")

                        series = full_info[len(full_info) - 1]
                        series = series.split(",")

                        if len(series) == 0:
                            raise Exception(
                                "A given series should contains a set of comma separated numeric values. At least one numeric value should be there in a series. Missing values should be indicated with ? symbol"
                            )

                        numeric_series = []

                        for val in series:
                            if val == "?":
                                numeric_series.append(replace_missing_vals_with)
                            else:
                                numeric_series.append(float(val))

                        if numeric_series.count(replace_missing_vals_with) == len(
                            numeric_series
                        ):
                            raise Exception(
                                "All series values are missing. A given series should contains a set of comma separated numeric values. At least one numeric value should be there in a series."
                            )

                        all_series.append(pd.Series(numeric_series).array)

                        for i in range(len(col_names)):
                            att_val = None
                            if col_types[i] == "numeric":
                                att_val = int(full_info[i])
                            elif col_types[i] == "string":
                                att_val = str(full_info[i])
                            elif col_types[i] == "date":
                                att_val = datetime.strptime(
                                    full_info[i], "%Y-%m-%d %H-%M-%S"
                                )
                            else:
                                raise Exception("Invalid attribute type.")

                            if att_val is None:
                                raise Exception("Invalid attribute value.")
                            else:
                                all_data[col_names[i]].append(att_val)

                line_count = line_count + 1

        if line_count == 0:
            raise Exception("Empty file.")
        if len(col_names) == 0:
            raise Exception("Missing attribute section.")
        if not found_data_section:
            raise Exception("Missing series information under data section.")

        all_data[value_column_name] = all_series
        loaded_data = pd.DataFrame(all_data)

        return (
            loaded_data,
            {
                "frequency": frequency,
                "horizon": forecast_horizon,
                "missing_values": contain_missing_values,
                "equal_length": contain_equal_length,
            },
        )
