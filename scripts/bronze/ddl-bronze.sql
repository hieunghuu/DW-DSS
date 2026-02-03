-- Bronze layer: raw Kaggle Walmart data

DROP TABLE IF EXISTS bronze.kaggle_features;
DROP TABLE IF EXISTS bronze.kaggle_stores;
DROP TABLE IF EXISTS bronze.kaggle_train;

CREATE TABLE bronze.kaggle_features (
  Store INTEGER,
  Date DATE,
  Temperature DOUBLE PRECISION,
  Fuel_Price DOUBLE PRECISION,
  MarkDown1 DOUBLE PRECISION,
  MarkDown2 DOUBLE PRECISION,
  MarkDown3 DOUBLE PRECISION,
  MarkDown4 DOUBLE PRECISION,
  MarkDown5 DOUBLE PRECISION,
  CPI DOUBLE PRECISION,
  Unemployment DOUBLE PRECISION,
  IsHoliday BOOLEAN
);

CREATE TABLE bronze.kaggle_stores (
  Store INTEGER,
  Type CHAR(1),
  Size INTEGER
);

CREATE TABLE bronze.kaggle_train (
  Store INTEGER,
  Dept INTEGER,
  Date DATE,
  Weekly_Sales DOUBLE PRECISION,
  IsHoliday BOOLEAN
);

