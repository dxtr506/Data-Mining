# Voi Kruger và Decision Tree: nội dung, slide và kịch bản

File gồm ba phần, đọc theo thứ tự:

1. **Nội dung:** dữ liệu là gì, xử lý thế nào, nhãn và cây học ra sao, kết quả. Đây là kiến thức nền để bạn nắm chắc và trả lời câu hỏi.
2. **Nội dung slide:** chọn lọc từ Phần 1 để đặt lên slide.
3. **Kịch bản:** lời thoại từng slide và kịch bản demo.

---

## PHẦN 1. NỘI DUNG

### 1.1. Bài toán

- Nguồn: nghiên cứu Thaker et al. (2019), *Fine-scale tracking of ambient temperature and movement reveals shuttling behavior of elephants to water*, *Frontiers in Ecology and Evolution*.
- Câu hỏi của đồ án: dùng Decision Tree trên dữ liệu GPS của voi để **tìm pattern di chuyển** (voi nghỉ khi nào, quay lại nguồn nước khi nào, đi nhanh hay chậm ở đâu).
- Cách làm: đặt nhãn tổng quát từ GPS → cây học nhãn → đọc luật của cây để suy ra pattern → kiểm tra pattern ở năm sau.

### 1.2. Dữ liệu GPS gốc

Dữ liệu đăng trên Movebank (Slotow, Thaker và Vanak, 2019), file CSV gồm các cột:

| Cột | Ý nghĩa |
| --- | --- |
| `timestamp` | Thời điểm ghi (giờ UTC) |
| `location-long`, `location-lat` | Vị trí GPS (kinh độ, vĩ độ) |
| `external-temperature` | Nhiệt độ đo bởi cảm biến ở vòng cổ |
| `individual-local-identifier` | Mã từng con voi (AM91, AM105...) |
| `sensor-type`, `tag-local-identifier` | Loại cảm biến và mã thiết bị |

Quy mô:

- **283.688** điểm GPS, **14 voi cái** (mỗi con thuộc một đàn khác nhau), từ **13/08/2007 đến 12/08/2009**.
- Thường ghi **30 phút một điểm**, có những đoạn mất tín hiệu.
- Số điểm mỗi con từ khoảng 10 nghìn đến 32 nghìn. AM253 và AM255 hết dữ liệu trước 2009, AM306 chỉ còn vài điểm trong 2009.

Lưu ý về nhiệt độ: đây là nhiệt độ ở vòng cổ, không phải nhiệt độ không khí chuẩn hay thân nhiệt voi. Paper đã kiểm tra nó đi theo nhiệt độ không khí.

### 1.3. Dữ liệu bổ sung

| Dữ liệu | Nguồn | Ghi chú |
| --- | --- | --- |
| **Hố nước** | SANParks (bản đồ Zambatis 2011), qua kho code của tác giả | Chỉ dùng hố nước đang mở trong vùng nghiên cứu: **124** hố |
| **Sông, suối** | OpenStreetMap, qua kho code của tác giả | **939** đoạn, trong đó 468 đoạn có nước quanh năm |
| **Độ che phủ cây gỗ** | Bề mặt nội suy từ kho code của tác giả (`woodland_clip.tif`) | Pixel khoảng 100 m, giá trị 0,04–79,5%, trung vị khoảng 35% |
| **Mùa mưa / khô** | Tự quy ước | Mùa mưa từ 13/10 đến 21/04 (không có số liệu mưa gốc) |
| **Mặt nước nền bản đồ** | OpenStreetMap | Chỉ để hiển thị, không dùng để tính |

Hai điểm cần nói đúng:

- **Cây gỗ không phải bản đồ Bucini gốc** mà paper dùng, mà là bề mặt nội suy do tác giả tạo. Độ che phủ là phần trăm diện tích, không phải số cây.
- **Mốc mùa là ước lượng**, chọn sao cho số điểm mùa khô và mùa mưa khớp con số paper báo cáo.

### 1.4. Xử lý dữ liệu

#### Bước 1. Làm sạch và chuẩn hóa

- Bỏ dòng thiếu giá trị và dòng trùng (cùng voi, cùng thời điểm). Sắp xếp theo voi và thời gian.
- Đổi giờ UTC sang giờ Kruger (UTC+2).
- Chuyển tọa độ sang hệ mét (UTM 36S) để tính khoảng cách.
- Gán mùa mưa hoặc khô theo ngày.

#### Bước 2. Khoảng cách tới nguồn nước gần nhất

- Mùa khô: tính sông có nước quanh năm và hố nước đang mở. Mùa mưa: tính thêm sông theo mùa (đúng quy tắc của paper).
- Với mỗi điểm GPS: khoảng cách thẳng tới nguồn nước gần nhất, và vị trí nguồn nước đó.
- Vùng gần nước: trong phạm vi **200 m** quanh nguồn nước (đúng ngưỡng của paper).
- **Thời gian đã rời nước:** tính từ điểm GPS đầu tiên ra khỏi vùng 200 m sau lần voi ở trong vùng đó.

#### Bước 3. Gắn độ che phủ cây gỗ

- Lấy giá trị tại pixel chứa điểm GPS, và trung bình trong ô khoảng 300 m quanh điểm.
- Khoảng 6,2% điểm GPS không có giá trị cây gỗ. Chỗ thiếu được giữ là thiếu, không điền 0.

#### Bước 4. Gom thành cửa sổ 90 phút

- Mỗi voi được đặt lên các mốc cách nhau 90 phút (00:00, 01:30, 03:00...).
- Tại mỗi mốc chỉ dùng điểm GPS đã biết, cũ không quá 30 phút (không dùng thông tin tương lai cho đặc trưng).
- Cửa sổ tương lai (chỉ để tạo nhãn) lấy từ điểm GPS tại mốc đến điểm GPS gần 90 phút sau.
- Loại cửa sổ có khoảng trống GPS quá dài hoặc bước nhảy bất thường (khoảng 5,9% bị loại).
- Kết quả: **80.487** cửa sổ, trong đó **75.738** đủ chất lượng để dùng.

### 1.5. Thiết kế dữ liệu cho cây học

#### 1.5.1. Một mẫu dữ liệu là gì?

**Một hàng = một cửa sổ 90 phút của một con voi**, tại một mốc thời gian. Mỗi hàng có ba phần:

| Phần | Nội dung | Lấy từ đâu |
| --- | --- | --- |
| **Đặc trưng X** (đầu vào của cây) | Giờ, nhiệt độ, mùa, khoảng cách tới nước, cây gỗ, ... | GPS **tại hoặc trước** mốc dự báo |
| **Nhãn y** (đáp án để cây học) | Nghỉ hay di chuyển, về nước hay chưa, ... | GPS **sau** mốc dự báo (90 phút hoặc 3 giờ tới) |
| Thông tin tra cứu (không đưa vào cây) | Mã voi, thời điểm | Dùng để chia train/test và tìm ví dụ trên bản đồ |

Quy tắc quan trọng: **đặc trưng chỉ dùng thông tin đã có tại thời điểm dự báo; tương lai chỉ dùng để tạo nhãn.** Cây cũng không được biết "voi vừa làm gì" (vừa đi bao xa, hướng nào), vì khi đó cây chỉ học quán tính.

**Bốn cây dùng chung nguồn 80.487 cửa sổ**, nhưng mỗi cây chỉ lấy *những cửa sổ phù hợp với câu hỏi của nó*. Vì vậy một cửa sổ có thể xuất hiện ở nhiều cây, mỗi cây là một mô hình độc lập.

**Các đặc trưng có thể dùng:**

| Đặc trưng | Ý nghĩa |
| --- | --- |
| `hour` | Giờ địa phương của mốc dự báo (0–24) |
| `temp` | Nhiệt độ vòng cổ (°C) |
| `wet` | Mùa: 1 = mùa mưa, 0 = mùa khô (theo lịch quy ước) |
| `dw_km` | Khoảng cách tới nguồn nước gần nhất (km) |
| `woody` | Độ che phủ cây gỗ tại điểm GPS (%) |
| `woody_mean_300m` | Độ che phủ cây gỗ trung bình quanh điểm, ô ~300 m (%) |
| `temp_change_90`, `temp_change_180` | Nhiệt độ hiện tại trừ nhiệt độ 90 phút và 3 giờ trước (°C) |
| `woody_missing` | Cờ: 1 nếu không có dữ liệu cây gỗ tại điểm này |
| `fix_age_min` | Tuổi của điểm GPS tại mốc (phút), kiểm soát chất lượng |
| `hours_since_water` | Số giờ đã rời vùng nước 200 m (chỉ cây 2 và 3 dùng) |

**Xử lý giá trị thiếu:** giá trị thiếu được thay bằng trung vị của tập học (không lấy từ 2009). Riêng độ che phủ cây gỗ còn có cờ `woody_missing` để cây biết chỗ nào là số điền thay (khoảng 5% mẫu).

#### 1.5.2. Cây 1: Nghỉ hay di chuyển?

| Mục | Mô tả |
| --- | --- |
| **Câu hỏi** | Trong 90 phút tới, voi nghỉ hay di chuyển? |
| **Mẫu nào được dùng** | **Mọi** cửa sổ đủ chất lượng (voi ở đâu cũng được) |
| **Số mẫu** | Fit 37.206 · Validation 22.001 · 2009 16.517 |
| **Nhãn** | **Nghỉ** nếu tổng đường đi trong 90 phút tới **dưới 75 m**; ngược lại là **Di chuyển** |
| **Đặc trưng (10)** | `hour`, `temp`, `wet`, `dw_km`, `woody`, `woody_mean_300m`, `temp_change_90`, `temp_change_180`, `woody_missing`, `fix_age_min` |
| **Không dùng** | `hours_since_water` (không liên quan đến nghỉ) |
| **Tỉ lệ nhãn** | Nghỉ chỉ chiếm 7,3% (fit), 9,0% (validation), 6,7% (2009): **lớp rất hiếm** |
| **Cách xử lý mất cân bằng** | `class_weight="balanced"` để cây không bỏ qua lớp "nghỉ" |

Ví dụ một hàng thật (AM108):

| Đặc trưng | Giá trị | Nhãn |
| --- | --- | --- |
| Giờ 01:30 · mùa mưa · nhiệt độ 24°C (giảm 2°C so với 90 phút trước) · cách nước 0,86 km · cây gỗ 34% | Đường đi 90 phút tới: **29 m** | **Nghỉ** |

#### 1.5.3. Cây 2: Có quay lại nước không?

| Mục | Mô tả |
| --- | --- |
| **Câu hỏi** | Voi đang ở xa nước có quay lại vùng nước trong 3 giờ tới không? |
| **Mẫu nào được dùng** | Chỉ cửa sổ voi **đang ở xa nước** (trên 200 m) và biết thời gian đã rời nước |
| **Số mẫu** | Fit 28.877 · Validation 15.430 · 2009 12.299 |
| **Nhãn** | **Về nước** nếu trong 3 giờ tới có điểm GPS nằm trong vùng 200 m quanh nguồn nước. **Chưa về nước** nếu không có điểm nào như vậy |
| **Cửa sổ bị bỏ** | Không biết chắc nhãn vì GPS mất tín hiệu hơn 60 phút trong 3 giờ tới |
| **Đặc trưng (11)** | 10 đặc trưng cơ bản và `hours_since_water` |
| **Tỉ lệ nhãn** | Về nước 22,0% (fit), 21,7% (validation), 24,3% (2009) |

Ví dụ một hàng thật (AM108):

| Đặc trưng | Giá trị | Nhãn |
| --- | --- | --- |
| Giờ 09:00 · mùa khô · nhiệt độ 25°C · cách nước 1,18 km · đã rời nước 14 giờ · cây gỗ 36% | GPS 3 giờ tới có điểm trong vùng 200 m quanh nước | **Về nước** |

Lưu ý: "về nước" là xu hướng đi vào vùng 200 m quanh nguồn nước, chưa quan sát được voi có uống nước hay không.

#### 1.5.4. Cây 3: Đi nhanh hay chậm?

| Mục | Mô tả |
| --- | --- |
| **Câu hỏi** | Ban ngày, khi voi đang đi, voi đi nhanh hay chậm? |
| **Mẫu nào được dùng** | Cửa sổ **ban ngày (06:00–18:00)** và voi **đang đi** (đường đi từ 75 m trở lên, tức không phải "nghỉ") |
| **Số mẫu** | Fit 18.559 · Validation 10.653 · 2009 8.107 |
| **Nhãn** | **Nhanh** nếu đường đi trong 90 phút tới **trên 652 m**; **Chậm** nếu từ 652 m trở xuống |
| **Cách chọn mốc 652 m** | Trung vị đường đi của tập fit, nên fit chia đều 50/50 |
| **Đặc trưng (11)** | 10 đặc trưng cơ bản và `hours_since_water` (thiếu khoảng 25% mẫu, điền trung vị 14 giờ) |
| **Tỉ lệ nhãn "nhanh"** | 50,0% (fit), 35,3% (validation), 49,1% (2009) |

Ví dụ một hàng thật (AM108, cùng cửa sổ 09:00 ở trên):

| Đặc trưng | Giá trị | Nhãn |
| --- | --- | --- |
| Giờ 09:00 · mùa khô · cây gỗ 36% · đã rời nước 14 giờ | Đường đi 90 phút tới: **736 m** (trên 652 m) | **Nhanh** |

Lưu ý: cây dự đoán tốc độ *nếu* voi đi, và chỉ cho ban ngày. Tỉ lệ "nhanh" ở validation thấp hơn hẳn (35%), nghĩa là tốc độ thay đổi theo giai đoạn (có thể theo mùa); cần nhớ khi đọc kết quả.

#### 1.5.5. Cây 4: Ở lại hay rời vùng nước?

| Mục | Mô tả |
| --- | --- |
| **Câu hỏi** | Voi đang ở trong vùng nước sẽ ở lại hay rời đi? |
| **Mẫu nào được dùng** | Chỉ cửa sổ voi **đang ở trong vùng 200 m** quanh nguồn nước |
| **Số mẫu** | Fit 7.017 · Validation 5.911 · 2009 3.327 (**ít nhất** trong bốn cây) |
| **Nhãn** | **Ở lại** nếu đường đi trong 90 phút tới **dưới 150 m**; ngược lại là **Rời đi** |
| **Đặc trưng (10)** | 10 đặc trưng cơ bản |
| **Không dùng** | `hours_since_water`, vì khi voi đang trong vùng nước thì giá trị này gần như luôn thiếu (khoảng 95%) |
| **Tỉ lệ nhãn "ở lại"** | 12,3% (fit), 20,9% (validation), 13,5% (2009) |

Ví dụ một hàng thật (AM107):

| Đặc trưng | Giá trị | Nhãn |
| --- | --- | --- |
| Giờ 10:30 · mùa khô · nhiệt độ 34°C · cách nước 0,14 km (trong vùng 200 m) · cây gỗ 50% | Đường đi 90 phút tới: **146 m** (dưới 150 m) | **Ở lại** |

Lưu ý: do ít mẫu nên cây 4 kém chắc hơn ba cây còn lại. "Ở lại" chưa phân biệt được uống nước, tắm hay nghỉ.

#### 1.5.6. So sánh nhanh bốn cây

| | Cây 1 | Cây 2 | Cây 3 | Cây 4 |
| --- | --- | --- | --- | --- |
| Câu hỏi | Nghỉ hay di chuyển | Có về nước không | Nhanh hay chậm | Ở lại hay rời nước |
| Mẫu lấy từ | Mọi cửa sổ | Voi xa nước | Ban ngày, voi đang đi | Voi trong vùng nước |
| Cửa sổ nhãn nhìn tới | 90 phút | 3 giờ | 90 phút | 90 phút |
| Số mẫu fit | 37.206 | 28.877 | 18.559 | 7.017 |
| Số đặc trưng | 10 | 11 | 11 | 10 |
| Lớp đáng chú ý | Nghỉ (7%) | Về nước (22%) | Nhanh (50%) | Ở lại (12%) |

#### 1.5.7. Đặc trưng cho vào và đặc trưng cây thực sự dùng

Các đặc trưng hiện trên nút của cây là những đặc trưng cây **thực sự dùng để chia nhánh**. Đó chỉ là một phần trong số đã cho vào, vì cây tự chọn những đặc trưng giúp tách nhãn tốt nhất.

| Cây | Cho vào | Cây dùng để chia nhánh | Cây không dùng |
| --- | --- | --- | --- |
| 1. Nghỉ / di chuyển | 10 | giờ, mùa, nhiệt độ so với 3 giờ trước | nhiệt độ, khoảng cách tới nước, cây gỗ (cả hai loại), nhiệt độ so với 90 phút trước, cờ thiếu cây gỗ, tuổi GPS |
| 2. Về nước | 11 | khoảng cách tới nước, giờ, nhiệt độ so với 3 giờ trước | nhiệt độ, mùa, cây gỗ, thời gian đã rời nước, và các đặc trưng còn lại |
| 3. Nhanh / chậm | 11 | thời gian đã rời nước, khoảng cách tới nước, giờ, cây gỗ (cả hai loại), mùa, nhiệt độ | nhiệt độ thay đổi, cờ thiếu cây gỗ, tuổi GPS |
| 4. Ở lại / rời nước | 10 | giờ, khoảng cách tới nước, cây gỗ, mùa | nhiệt độ, cây gỗ ~300 m, nhiệt độ thay đổi, và các đặc trưng còn lại |

Hai điều cần nói đúng:

- **"Cây không dùng" không có nghĩa là đặc trưng đó vô nghĩa.** Chỉ có nghĩa là trong cây nông này, đặc trưng đó không giúp chia nhãn tốt hơn các đặc trưng đã chọn. Ví dụ ở cây 1, nghỉ gần như do giờ quyết định, nên các đặc trưng khác không còn chỗ.
- **Cây gỗ chỉ xuất hiện trong luật của cây 3 và cây 4.** Cây 1 (nghỉ) và cây 2 (về nước) hoàn toàn không dùng cây gỗ.

### 1.6. Cách chia dữ liệu và huấn luyện

Chia theo **thời gian** (giờ địa phương), cho cả bốn cây:

| Giai đoạn | Thời gian | Số cửa sổ (tất cả) | Dùng để |
| --- | --- | --- | --- |
| Fit | 08/2007 – 06/2008 | 39.252 | Học cây khi chọn tham số |
| Validation | 07/2008 – 12/2008 | 23.299 | Chọn độ sâu cây, số mẫu tối thiểu ở lá |
| **Test 2009** | 01/2009 – 08/2009 | 17.923 (11 voi) | Đối chiếu pattern |

- Cửa sổ mà cửa sổ nhãn chạm sang giai đoạn sau thì bị bỏ khỏi giai đoạn trước (không để nhãn lẫn thông tin của test).
- Mô hình cuối **học lại trên toàn bộ 2007–2008** (fit + validation) với tham số đã chọn, rồi dự đoán 2009.
- Test 2009 chỉ giữ những voi có ít nhất một ngày dữ liệu (11 voi; AM253 và AM255 hết dữ liệu trước 2009, AM306 chỉ có vài điểm).
- Cây dùng `class_weight="balanced"`, nên lớp hiếm như "nghỉ" không bị bỏ qua.
- Độ sâu cây chọn theo validation: cây 1 độ sâu 3 (6 luật), cây 2 độ sâu 4 (14 luật), cây 3 độ sâu 5 (17 luật), cây 4 độ sâu 3 (8 luật). Khi hai cấu hình gần nhau, chọn cây ít luật hơn cho dễ đọc.
- **Năm 2009 không phải test mù hoàn toàn:** số liệu 2009 đã được xem ở các phiên bản trước, nên đây là phép đối chiếu, không dùng để chọn cấu hình.

### 1.7. Kết quả

Điểm đo: macro-F1 (trung bình điểm F1 của các lớp, công bằng hơn accuracy khi lớp mất cân bằng). So với mức "luôn đoán lớp đông nhất".

| Cây | Validation | 2009 | Luôn đoán lớp đông nhất (val / 2009) |
| --- | --- | --- | --- |
| 1. Nghỉ hay di chuyển | 0,61 | 0,60 | 0,48 / 0,48 |
| 2. Quay lại nước | 0,70 | 0,69 | 0,44 / 0,43 |
| 3. Đi nhanh hay chậm | 0,57 | 0,62 | 0,39 / 0,34 |
| 4. Ở lại hay rời vùng nước | 0,63 | 0,60 | 0,44 / 0,46 |

Cả bốn cây đều hơn hẳn mức đoán bừa, nhưng mức độ là vừa phải. Pattern là **xu hướng**, không phải quy tắc chắc chắn.

### 1.8. Pattern rút ra từ cây

| Cây | Pattern | Cách diễn giải (giả thuyết) |
| --- | --- | --- |
| 1. Nghỉ / di chuyển | **Từ 00:45 đến 03:45 voi nghỉ (ít di chuyển).** Nghỉ khoảng 34% số lần trong khung này, so với khoảng 8% bình thường. Đúng ở cả 14 voi | Có thể voi đang ngủ hoặc nghỉ ngơi |
| 2. Quay lại nước | Ban ngày, voi cách nước gần (dưới khoảng 540 m) thì có xu hướng quay lại nước trong 3 giờ | Có thể voi đi uống nước |
| 3. Nhanh / chậm | Ở nơi cây gỗ dày, voi đi chậm hơn. Mùa khô đi chậm hơn mùa mưa | Có thể voi vừa đi vừa kiếm ăn. Khớp với kết quả của paper |
| 4. Ở lại / rời nước | Ban đêm, ở nơi cây gỗ quanh nước dày, voi ở lại vùng nước nhiều | Có thể voi nghỉ hoặc tắm gần nước |

Về cây gỗ và nghỉ: cây 1 **không** dùng cây gỗ trong luật. Việc "cây gỗ càng dày, ban đêm nghỉ càng nhiều" là phân tích mô tả trong dữ liệu (tab Pattern của cây 1, mục 3), không phải do cây 1 tìm ra. Khi trình bày cần nói rõ là phân tích mô tả.

Pattern nghỉ ban đêm là pattern **vững nhất**: đúng ở cả ba giai đoạn dữ liệu (fit, validation, 2009) và ở cả 14 voi. Các pattern còn lại yếu hơn.

Nhiệt độ ít xuất hiện trong luật vì nhiệt độ đi cùng giờ trong ngày (trưa nóng, đêm mát). Khi đã biết giờ thì nhiệt độ thêm rất ít thông tin.

### 1.9. Giới hạn cần nói thẳng

- **GPS chỉ là ước lượng.** Mỗi cửa sổ chỉ có khoảng 4 điểm và có sai số, nên vẫn thấy di chuyển nhỏ ở khung giờ nghỉ, và nhãn là ước lượng.
- **Nhãn không phải hành vi quan sát.** "Nghỉ" không có nghĩa là ngủ. "Về nước" không có nghĩa là uống nước. Mọi diễn giải như vậy chỉ là giả thuyết.
- **Năm 2009 chỉ là phép đối chiếu**, không phải test hoàn toàn mù.
- **Cây gỗ là bề mặt nội suy của tác giả**, không phải bản đồ gốc. Mùa là mốc quy ước.
- **Liên hệ không phải nhân quả.** Cây gỗ dày đi cùng voi đi chậm chưa chứng minh cây gỗ làm voi đi chậm.
- **Mức chính xác vừa phải.** Pattern là xu hướng.

---

## PHẦN 2. NỘI DUNG SLIDE

Cấu trúc: 5 slide và phần demo.

### Slide 1. Mở đầu

**Tiêu đề:** Khai phá pattern di chuyển của voi Kruger bằng Decision Tree

**Nội dung trên slide:**

- Dữ liệu từ nghiên cứu: Thaker et al. (2019), *Frontiers in Ecology and Evolution*.
- Vườn quốc gia Kruger, Nam Phi.
- Mục tiêu: dùng Decision Tree để tìm pattern di chuyển của voi.

**Hình gợi ý:** ảnh bản đồ tổng quan chụp từ web (bản đồ ở chế độ kiểm tra, phím `P`).

### Slide 2. Dữ liệu

**Tiêu đề:** Dữ liệu

**Nội dung trên slide:**

- 14 voi cái, 08/2007 – 08/2009, hơn 280 nghìn điểm GPS (30 phút một điểm).
- Nhiệt độ đo ở vòng cổ.
- Nguồn nước: 124 hố nước đang mở, sông và suối.
- Độ che phủ cây gỗ (%).

**Chú thích nhỏ cuối slide:** độ che phủ cây gỗ là bề mặt nội suy từ kho code của tác giả, không phải bản đồ gốc.

**Hình gợi ý:** ảnh bản đồ có sông, hố nước và vệt đường đi của voi.

### Slide 3. Xử lý dữ liệu

**Tiêu đề:** Từ GPS đến cửa sổ 90 phút

**Nội dung trên slide:**

- Gom GPS thành cửa sổ 90 phút (80 nghìn cửa sổ).
- Mỗi cửa sổ có: giờ, nhiệt độ, mùa, khoảng cách tới nước, độ che phủ cây gỗ, thời gian đã rời nước.
- Nhãn lấy từ chuyển động trong cửa sổ kế tiếp.

**Hình gợi ý:** sơ đồ ba khối nối nhau: "Điểm GPS 30 phút" → "Cửa sổ 90 phút" → "Đặc trưng (đã biết)" và "Nhãn (90 phút tiếp theo)".

### Slide 4. Ý tưởng: nhãn tổng quát và bốn cây

**Tiêu đề:** Một nhãn tổng quát, một cây, một câu hỏi

**Nội dung trên slide:**

| Cây | Câu hỏi | Mẫu lấy từ | Nhãn |
| --- | --- | --- | --- |
| 1 | Nghỉ hay di chuyển? | Mọi cửa sổ | Nghỉ = đi dưới 75 m trong 90 phút |
| 2 | Có quay lại nước không? | Voi đang xa nước | Về tới vùng 200 m quanh nước trong 3 giờ |
| 3 | Đi nhanh hay chậm? | Ban ngày, voi đang đi | Nhanh = đi trên ~650 m trong 90 phút |
| 4 | Ở lại hay rời vùng nước? | Voi đang trong vùng nước | Ở lại = đi dưới 150 m trong 90 phút |

**Dòng nhấn mạnh:** cây không biết voi vừa làm gì, chỉ biết bối cảnh (giờ, nhiệt độ, mùa, khoảng cách tới nước, cây gỗ).

### Slide 5. Cách chia dữ liệu

**Tiêu đề:** Học trên quá khứ, kiểm tra trên năm sau

**Nội dung trên slide:**

- **Train:** 08/2007 – 12/2008 (14 voi): cây học và rút ra pattern.
- **Test:** 2009 (11 voi): xem pattern có còn đúng không.
- Nhãn là hình dạng quỹ đạo GPS, không khẳng định ăn, ngủ hay uống nước.

**Hình gợi ý:** thanh dòng thời gian hai màu, mốc 01/01/2009 ở giữa.

### Phần 6. Demo

**Nội dung trên slide:** một dòng "Demo".

---

## PHẦN 3. KỊCH BẢN

### 3.1. Lời thoại từng slide

**Slide 1.**
"Em dùng dữ liệu GPS từ nghiên cứu của Thaker và cộng sự năm 2019 về voi ở Vườn quốc gia Kruger, Nam Phi. Mục tiêu của em là dùng Decision Tree để tìm pattern di chuyển của voi: voi nghỉ khi nào, khi nào quay lại nguồn nước, đi nhanh hay chậm ở đâu."

**Slide 2.**
"Mỗi con voi đeo vòng cổ ghi vị trí 30 phút một lần, kèm nhiệt độ. Em ghép thêm vị trí sông, hố nước của vườn và độ che phủ cây gỗ. Lưu ý là bản đồ cây gỗ em dùng là bề mặt nội suy từ kho code của tác giả, không phải bản đồ gốc."

**Slide 3.**
"GPS chỉ là ước lượng vị trí, nên em không đọc từng điểm mà gom thành cửa sổ 90 phút. Với mỗi cửa sổ, em biết bối cảnh lúc đó: giờ nào, nóng hay mát, gần hay xa nước. Nhãn là điều xảy ra trong 90 phút tiếp theo."

**Slide 4.**
"Em đặt nhãn tổng quát từ GPS rồi để cây học. Mỗi câu hỏi có một cây riêng. Từ các luật của cây, em suy ra pattern. Có một điểm quan trọng: cây không biết voi vừa làm gì, chỉ biết bối cảnh. Nếu cho biết, cây sẽ chỉ học quán tính: đang đi thì tiếp tục đi, và không cho em biết điều gì về hành vi của voi."

**Slide 5.**
"Cây chỉ học dữ liệu 2007 đến 2008. Từ đó em đọc ra pattern. Sau đó em mở năm 2009, dữ liệu cây chưa học, để xem pattern có còn đúng không. Em nói thẳng là năm 2009 em đã xem số liệu ở các phiên bản trước, nên nó là phép đối chiếu hơn là một bài kiểm tra hoàn toàn mù. Ngoài ra, nhãn chỉ là hình dạng quỹ đạo GPS, em không khẳng định đó là ăn, ngủ hay uống nước."

**Slide 6.**
"Bây giờ em xin chuyển sang demo."

### 3.2. Kịch bản demo (khoảng 6 đến 8 phút)

**Chuẩn bị trước:** mở `elephant_dt\web\index.html` bằng Chrome hoặc Edge, bấm `F` toàn màn hình. Mỗi cây làm hai việc: mở **Cây** để chỉ ô **Pattern**, rồi bấm `P` để kiểm tra pattern đó trên 2009 (bấm `P` lần nữa để quay về màn hình thường).

| Bước | Thời gian | Thao tác | Lời nói |
| --- | --- | --- | --- |
| 1. Giới thiệu bản đồ | 30 giây | Chỉ biểu tượng voi, vệt trắng, sông và hố nước | "Đây là 11 voi năm 2009. Vệt trắng là đường đi thật. Huy hiệu cạnh mỗi voi là dự đoán của cây." |
| 2. Cây 1: Nghỉ hay di chuyển | 1,5 phút | Bấm **Cây**, chỉ nhánh tô vàng từ gốc tới lá (lá có nhãn **Pattern**) và ô **Pattern**. Đóng sơ đồ, bấm `P`, bấm vào một con voi trong ô kiểm tra, bấm **Chạy 90 phút tới** | "Pattern rõ nhất: từ 00:45 đến 03:45, voi nghỉ (ít di chuyển). Ô kiểm tra cho biết trong 2009 pattern này đúng bao nhiêu phần trăm so với mức chung, và với con voi này thực tế ra sao. Từ đây em suy ra có thể voi đang ngủ hoặc nghỉ ngơi." |
| 3. Cây 2: Về nước | 1,5 phút | Bấm phím `2`. Mở sơ đồ, chỉ ô Pattern. Bấm `P`, chọn một con voi, chỉ đường mảnh nối voi tới nguồn nước | "Ban ngày, voi càng gần nước thì càng có xu hướng quay lại nước trong 3 giờ tới." |
| 4. Cây 3: Tốc độ | 1 phút | Bấm phím `3`. Mở sơ đồ, chỉ pattern, bấm `P` kiểm tra | "Ở nơi cây gỗ dày, voi đi chậm hơn. Điều này khớp với kết quả của paper. Đây là liên hệ trong dữ liệu, em không khẳng định là nguyên nhân." |
| 5. Cây 4: Ở nước | 1 phút | Bấm phím `4`. Mở sơ đồ, chỉ pattern, bấm `P` kiểm tra | "Ban đêm voi ở lại gần nước nhiều. Dữ liệu không phân biệt được uống nước, tắm hay nghỉ." |
| 6. Tab Pattern và Luật | 30 giây (nếu còn thời gian) | Bấm **Pattern**, chỉ biểu đồ theo giờ | "Biểu đồ cho thấy pattern có thật trong dữ liệu." |

**Lời kết sau demo** (vì không có slide kết luận):
"Tóm lại, pattern rõ nhất em tìm được là voi ít di chuyển vào khoảng 00:45 đến 03:45, và pattern này vẫn đúng ở dữ liệu 2009. Các pattern khác yếu hơn và mang tính xu hướng."

### 3.3. Phím tắt và lưu ý khi trình bày

**Phím tắt:**

- `1` đến `4`: chọn cây. `[` và `]`: chuyển qua lại giữa các cây.
- `P`: chế độ kiểm tra pattern trên 2009 (chỉ còn bản đồ và một ô: pattern, độ đúng chung, vài con voi tiêu biểu, một ví dụ).
- `F`: toàn màn hình. `H`: ẩn giao diện chỉ còn bản đồ.
- Phím cách: chạy hoặc dừng.

**Lưu ý:**

- Chạy thử trước một lượt ở đúng độ phân giải của máy chiếu.
- Ảnh vệ tinh cần Internet. Khi mất mạng, voi, vệt đi và sơ đồ cây vẫn chạy trên nền tối.
- Trước demo, bấm `P` ở từng cây, thử vài con voi và nút **Ví dụ khác** để biết trước ô kiểm tra dẫn tới đâu.

### 3.4. Câu hỏi dễ gặp và gợi ý trả lời

**Vì sao năm 2009 chưa phải test hoàn toàn?**
"Em đã xem số liệu 2009 ở các phiên bản trước để so sánh, nên em gọi nó là phép đối chiếu. Pattern ban đêm thì đúng ở cả 14 voi và cả ba giai đoạn dữ liệu, nên em tin nó vững."

**Có chắc voi đang ngủ không?**
"Không. Dữ liệu chỉ cho thấy voi ít di chuyển theo GPS. Em gợi ý là có thể voi ngủ hoặc nghỉ, và đó là giả thuyết cần thêm quan sát."

**Vì sao vẫn thấy voi di chuyển trong khung giờ nghỉ?**
"Vì GPS có sai số, nên một đoạn nhỏ vẫn được tính là di chuyển. Em dùng ngưỡng 75 m để loại phần nhiễu."

**Độ che phủ cây gỗ lấy từ đâu?**
"Từ kho code của tác giả, là bề mặt nội suy, không phải bản đồ gốc mà paper dùng."

**Cây gỗ có liên quan tới việc nghỉ không?**
"Trong dữ liệu, ban đêm cây gỗ càng dày thì voi càng nghỉ nhiều. Nhưng cây 1 không dùng cây gỗ trong luật, nên em chỉ nói đây là liên hệ mô tả, không phải do cây tìm ra, và cũng chưa chứng minh nguyên nhân."

**Vì sao nhiệt độ ít xuất hiện trong luật?**
"Nhiệt độ và giờ trong ngày đi cùng nhau. Khi đã biết giờ thì nhiệt độ thêm rất ít thông tin."

**Vì sao không cho cây biết voi vừa làm gì?**
"Nếu cho biết, cây chỉ học quán tính: voi đang đi thì tiếp tục đi. Cây sẽ đoán khá đúng nhưng không cho em biết điều gì về hành vi hay bối cảnh."
