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

Ngày lễ trong dữ liệu
- **Super Bowl** : 12-Feb-10, 11-Feb-11, 10-Feb-12, 8-Feb-13
- **Labor Day**: 10-Sep-10, 9-Sep-11, 7-Sep-12, 6-Sep-13
- **Thanksgiving**: 26-Nov-10, 25-Nov-11, 23-Nov-12, 29-Nov-13
- **Christmas**: 31-Dec-10, 30-Dec-11, 28-Dec-12, 27-Dec-13

---

#### 3.2 test.csv  


!!! info Không sử dụng `test.csv` này trong dự án này

Dữ liệu cho các giai đoạn tương lai, nơi doanh số theo tuần cần được dự báo.

| Tên cột | Kiểu dữ liệu | Mô tả |
|--------|--------------|-------|
| Store  | int          | Mã định danh cửa hàng |
| Dept   | int          | Mã định danh bộ phận |
| Date   | date         | Ngày theo tuần |
| IsHoliday | bool | Cho biết tuần đó có phải là tuần lễ / ngày nghỉ hay không (True/False) |

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

Cách tính CPI
```
CPI_t​=Cost of Basket_base/​Cost of Basket_​​×100
```
!!! infor Chỉ số giá tiêu dùng CPI là chỉ số dùng để đo lường số tiền trung bình một người dân sử dụng để tiêu dùng các loại hàng hóa và dịch vụ. Chỉ số CPI phản ánh xu hướng và mức độ biến động giá theo thời gian của các mặt hàng trong rổ hàng hóa và dịch vụ tiêu dùng đại diện.


Trong bối cảnh dữ liệu Walmart, CPI đại diện cho mức lạm phát tại khu vực cửa hàng, ảnh hưởng trực tiếp đến:
- Sức mua của người tiêu dùng
- Doanh số bán lẻ theo thời gian

CPI tăng → giá cả tăng → có thể giảm nhu cầu mua sắm
CPI giảm / ổn định → sức mua tốt hơn → doanh số tăng

CPI không phải giá tuyệt đối

!!! note CPI = 211 có nghĩa là Mức giá hiện tại cao hơn ~111% so với năm gốc (base year = 100)



----

```
MarkDown* == "NA" -> MarkDown* = 0 (Transform)
```
Markdowns : hạ giá sản phẩm trong cửa hàng bán lẻ.

Markdowns xảy ra khi giá bán lẻ ban đầu của sản phẩm bị giảm xuống để cửa hàng có thể nhanh chóng bán hết chúng đi.

Điều này có thể xảy ra khi nhà bán lẻ đã lỡ mua quá nhiều hàng hóa, hoặc khi bắt đầu một mùa mới thì cửa hàng cần phải nhanh chóng di chuyển các sản phẩm của mùa cũ đi.
> Các biến MarkDown đại diện cho những hình thức giảm giá/khuyến mãi khác nhau được áp dụng trong một tuần cụ thể.  
> Giá trị bị thiếu cho biết tuần đó không có chương trình khuyến mãi.

**Công thức tính tỉ lệ markdown**
```
Tỉ lệ markdown = Số tiền giảm / Giá bán ban đầu
```
Ví dụ: Toàn bộ một dãy áo sơ mi được thiết kế riêng có giá 100 USD đang được giảm giá xuống còn 60 USD trong hai ngày cuối tuần.
```
Tỉ lệ markdown = 40/100 = 40%
```
---

#### 3.4 stores.csv  
Siêu dữ liệu mô tả các cửa hàng Walmart.

| Tên cột | Kiểu dữ liệu | Mô tả |
|--------|--------------|-------|
| Store  | int          | Mã định danh cửa hàng |
| Type   | categorical  | Loại cửa hàng (A, B, C) |
| Size   | int          | Diện tích cửa hàng (feet vuông) |
