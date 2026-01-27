# RAW DATA DESCRIPTION  
## Walmart Recruiting – Store Sales Forecasting Dataset

### 1. Data Source
- **Source**: Kaggle  
- **Dataset name**: Walmart Recruiting – Store Sales Forecasting  
- **URL**: https://www.kaggle.com/c/walmart-recruiting-store-sales-forecasting/data  
- **Data type**: Structured data (CSV files)  
- **Domain**: Retail / Sales / Decision Support Systems  
- **Date**: from 2010-02-05 to 2012-10-26

---

### 2. Overview
This dataset contains historical weekly sales data for Walmart stores across multiple departments, combined with additional information such as store characteristics, holidays, promotions (markdowns), and economic indicators.  

---

### 3. Data Files Description

#### 3.1 train.csv
Historical sales data used for analysis and model building.

| Column Name     | Data Type | Description |
|-----------------|-----------|-------------|
| Store           | int       | Unique identifier of the store |
| Dept            | int       | Department identifier |
| Date            | date      | Week date (YYYY-MM-DD) |
| Weekly_Sales    | float     | Total weekly sales (target variable) |
| IsHoliday       | bool      | Indicates whether the week is a holiday (True/False) |

---

#### 3.2 test.csv
we will not using this file for this project
Future periods where weekly sales need to be predicted.


| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| Store       | int       | Store identifier |
| Dept        | int       | Department identifier |
| Date        | date      | Week date |
| IsHoliday   | bool      | Holiday indicator |

> Note: The `Weekly_Sales` column is not available in this file.

---

#### 3.3 features.csv
Additional features that may affect sales performance.


| Column Name      | Data Type        | Description |
|------------------|------------------|-------------|
| Store            | int              | Store identifier |
| Date             | date             | Week date |
| Temperature      | float            | Average temperature in the region |
| Fuel_Price       | float            | Fuel price |
| CPI              | float            | Consumer Price Index |
| Unemployment     | float            | Unemployment rate |
| IsHoliday        | bool             | Holiday indicator |
| MarkDown1        | float (nullable) | Promotional markdown type 1 |
| MarkDown2        | float (nullable) | Promotional markdown type 2 |
| MarkDown3        | float (nullable) | Promotional markdown type 3 |
| MarkDown4        | float (nullable) | Promotional markdown type 4 |
| MarkDown5        | float (nullable) | Promotional markdown type 5 |

> MarkDown variables represent different types of promotional discounts applied during a specific week. Missing values indicate no promotion.

---

#### 3.4 stores.csv
Metadata describing Walmart stores.


| Column Name | Data Type | Description |
|------------|-----------|-------------|
| Store      | int       | Store identifier |
| Type       | categorical | Store type (A, B, C) |
| Size       | int       | Store size (square feet) |

---

### 4. Data Granularity
- **Temporal granularity**: Weekly
- **Business granularity**: Store – Department – Week

Each observation represents the sales performance of one department in one store for one specific week.

---

### 5. Data Usage in Data Warehouse & DSS
The raw data serves as the input for:
- ETL processes
- Data warehouse construction (Star Schema)
- OLAP analysis
- Decision support for sales planning and promotion strategies

---

### 6. Data Quality Notes
- MarkDown variables contain missing values
- Sales values may in
