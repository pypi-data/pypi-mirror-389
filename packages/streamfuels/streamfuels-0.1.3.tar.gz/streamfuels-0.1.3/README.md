# StreamFuels

StreamFuels is a collection of updated fuel sales datasets for forecasting,
classification, and pattern analysis, focusing on petroleum derivatives, natural gas, and biofuels market across different regions of Brazil.


***monthly_sales_state()***: 
Monthly fuel sales data by state from the ANP database
    
***yearly_sales_state()***: 
Yearly fuel sales data by state from ANP database

***yearly_sales_city()***: 
Yearly fuel sales data by city from ANP database

***monthly_operations_state()***: 
Monthly oil production, NGL production, natural gas production, reinjection, flaring and losses, self-consumption, and available natural gas. It provides a comprehensive view of petroleum and gas operations.
  
**fuel_type_classification()**
Comprises 14,032 time series, each with a fixed length of 12 observations (i.e., one year of sales) and eight possible class labels.

## Installation

```bash
pip install streamfuels
```


<!-- To run locally, in your target python environment and in this project folder type:
```bash
pip install -e .
``` -->


After that you can import using the target python environment:

```python
from streamfuels.datasets import DatasetLoader
loader = DatasetLoader()
result, flag = loader.yearly_sales_state()

df, metadata = loader.read_tsf(path_tsf=result)
```

### Yearly sales of petroleum derivatives in the states of Brazil.
```python
result, flag = loader.yearly_sales_state()
```
![image](https://github.com/user-attachments/assets/ab1d0ac8-9574-4229-81e6-2e3ef32e959c)

### Monthly sales of petroleum derivatives in the states of Brazil.
```python
result, flag = loader.monthly_sales_state()
```
![image](https://github.com/user-attachments/assets/4894d0cf-eb92-421b-8b8a-d0a1522ccc0d)

### Monthly oil and gas operations in the states of Brazil.
```python
result, flag = loader.monthly_operations_state()
```
![image](https://github.com/user-attachments/assets/ab9b18b5-54ee-41f8-8948-9458b6e96343)

### Yearly sales of petroleum derivatives in the cities of Brazil.
```python
result, flag = loader.yearly_sales_city()
```
![image](https://github.com/user-attachments/assets/26ac0d96-73f9-43a8-b9bf-47106cafeba4)

### Fuel Type Classification dataset
```python
df = loader.fuel_type_classification()
```
![image](https://github.com/user-attachments/assets/d3b6f550-3435-48b7-873c-5be0bd658b96)


## 📚 Interactive Example Notebooks

You can explore practical use cases of the library directly via Binder:

- **🔍 Fuel Type Classification**  
  Demonstrates how to use classification algorithms to identify the fuel type.  
  [![Open in Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/lucas-castrow/StreamFuels/HEAD?urlpath=%2Fdoc%2Ftree%2Fexamples%2FClassification.ipynb)

- **📈 Time Series Forecasting**  
  Shows how to perform time series forecasting using statistical and machine learning models.  
  [![Open in Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/lucas-castrow/StreamFuels/HEAD?urlpath=%2Fdoc%2Ftree%2Fexamples%2FForecasting.ipynb)

- **📊 Dataset Loading and Visualization**  
  Explains how to load datasets and visualize key information graphically.  
  [![Open in Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/lucas-castrow/StreamFuels/HEAD?urlpath=%2Fdoc%2Ftree%2Fexamples%2FLoad+datatasets+and+visualization.ipynb)

- **🧠 Motif Discovery and Visualization**  
  Demonstrates how to identify and visualize repeating patterns (motifs) in time series data.  
  [![Open in Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/lucas-castrow/StreamFuels/HEAD?urlpath=%2Fdoc%2Ftree%2Fexamples%2FMotif+discovery.ipynb)
