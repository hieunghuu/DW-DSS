### 1. Data Source
- **Source**: Kaggle  
- **Dataset name**: Walmart Recruiting – Store Sales Forecasting  
- **URL**: https://www.kaggle.com/c/walmart-recruiting-store-sales-forecasting/data  
- **Data type**: Structured data (CSV files)  
- **Domain**: Retail / Sales / Decision Support Systems  
- **Date**: from 2010-02-05 to 2012-10-26


### 3. Mô tả các tệp dữ liệu

#### 3.1 train.csv  
Dữ liệu doanh số lịch sử, được sử dụng cho phân tích và xây dựng mô hình.

| Tên cột        | Kiểu dữ liệu | Mô tả |
|----------------|--------------|-------|
| Store          | int          | Mã định danh duy nhất của cửa hàng |
| Dept           | int          | Mã định danh bộ phận |
| Date           | date         | Ngày theo tuần (YYYY-MM-DD) |
| Weekly_Sales   | float        | Tổng doanh số theo tuần (biến mục tiêu) |
| IsHoliday      | bool         | Cho biết tuần đó có phải là tuần lễ / ngày nghỉ hay không (True/False) |

---

#### 3.2 test.csv  
**Không sử dụng tệp này trong dự án này.**  
Dữ liệu cho các giai đoạn tương lai, nơi doanh số theo tuần cần được dự báo.

| Tên cột | Kiểu dữ liệu | Mô tả |
|--------|--------------|-------|
| Store  | int          | Mã định danh cửa hàng |
| Dept   | int          | Mã định danh bộ phận |
| Date   | date         | Ngày theo tuần |
| IsHoliday | bool      | Chỉ báo ngày lễ |

> Cột `Weekly_Sales` không tồn tại trong tệp này.

---

#### 3.3 features.csv  
Các biến đặc trưng bổ sung có thể ảnh hưởng đến hiệu quả bán hàng.

| Tên cột         | Kiểu dữ liệu        | Mô tả |
|-----------------|---------------------|-------|
| Store           | int                 | Mã định danh cửa hàng |
| Date            | date                | Ngày theo tuần |
| Temperature     | float               | Nhiệt độ trung bình của khu vực |
| Fuel_Price      | float               | Giá nhiên liệu |
| CPI             | float               | Chỉ số giá tiêu dùng (Consumer Price Index) |
| Unemployment    | float               | Tỷ lệ thất nghiệp |
| IsHoliday       | bool                | Chỉ báo ngày lễ |
| MarkDown1       | float (có thể rỗng) | Loại khuyến mãi giảm giá 1 |
| MarkDown2       | float (có thể rỗng) | Loại khuyến mãi giảm giá 2 |
| MarkDown3       | float (có thể rỗng) | Loại khuyến mãi giảm giá 3 |
| MarkDown4       | float (có thể rỗng) | Loại khuyến mãi giảm giá 4 |
| MarkDown5       | float (có thể rỗng) | Loại khuyến mãi giảm giá 5 |

> Các biến MarkDown đại diện cho những hình thức giảm giá/khuyến mãi khác nhau được áp dụng trong một tuần cụ thể.  
> Giá trị bị thiếu cho biết tuần đó không có chương trình khuyến mãi.

---

#### 3.4 stores.csv  
Siêu dữ liệu mô tả các cửa hàng Walmart.

| Tên cột | Kiểu dữ liệu | Mô tả |
|--------|--------------|-------|
| Store  | int          | Mã định danh cửa hàng |
| Type   | categorical  | Loại cửa hàng (A, B, C) |
| Size   | int          | Diện tích cửa hàng (feet vuông) |
