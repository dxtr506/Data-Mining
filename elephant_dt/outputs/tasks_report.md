# Bốn câu hỏi cho Decision Tree về hành vi di chuyển của voi

Dữ liệu GPS 14 voi, 08/2007–08/2009, cửa sổ 90 phút. Chia theo thời gian: fit 08/2007–06/2008, validation 07–12/2008,
2009 chỉ để đối chiếu (đã được xem ở các phiên bản trước nên không dùng để chọn cấu hình). Feature chỉ lấy từ GPS tại hoặc
trước mốc dự báo; cây không biết voi vừa làm gì để không chỉ học quán tính.

## Câu hỏi 1. Voi nghỉ hay di chuyển trong 90 phút tới?

**Nghỉ** = tổng đường đi < 75 m trong 90 phút (dưới mức này độ thẳng quỹ đạo gần như nhiễu GPS). Chưa khẳng định ngủ.
Tỉ lệ nghỉ: 7,3% (fit), 6,7% (2009).

| Mô hình | macro-F1 validation | macro-F1 2009 (đối chiếu) | Accuracy 2009 |
|---|---:|---:|---:|
| Cây (6 luật) | 0,61 | 0,60 | 80,2% |
| Luôn đoán lớp đông nhất | 0,48 | 0,48 | 93,3% |

| Bỏ nhóm feature | macro-F1 validation | macro-F1 2009 |
|---|---:|---:|
| Không bỏ | 0,61 | 0,60 |
| Giờ | 0,49 | 0,49 |
| Nhiệt độ | 0,61 | 0,62 |
| Mùa | 0,61 | 0,60 |
| Khoảng cách tới nước | 0,61 | 0,60 |
| Cây gỗ | 0,61 | 0,60 |
| Chất lượng GPS | 0,61 | 0,60 |

### Luật
| Dự đoán | Điều kiện | Mẫu (voi) | Lift fit / val / 2009 | Voi lift > 1 (2007–08 · 2009) | Ổn định |
|---|---|---:|---|---|---|
| Nghỉ (ít di chuyển) | 00:45 < Giờ địa phương ≤ 03:45 | 6,817 (14) | 4,74 / 3,63 / 4,62 | 14/14 · 10/10 | có |
| Nghỉ (ít di chuyển) | Giờ địa phương ≤ 00:45 | 3,705 (14) | 2,04 / 1,92 / 2,03 | 14/14 · 7/9 | có |
| Nghỉ (ít di chuyển) | Giờ địa phương > 20:15 · Nhiệt độ so với 3 giờ trước (°C) > -3,50 | 2,561 (14) | 1,34 / 1,29 / 0,87 | 10/14 · 4/9 | chưa |
| Di chuyển | 03:45 < Giờ địa phương ≤ 20:15 · mùa mưa | 20,481 (14) | 1,06 / 1,07 / 1,06 | 14/14 · 10/10 | chưa |
| Di chuyển | 03:45 < Giờ địa phương ≤ 20:15 · mùa khô | 20,565 (14) | 1,04 / 1,04 / 1,04 | 14/14 · 10/10 | chưa |
| Di chuyển | Giờ địa phương > 20:15 · Nhiệt độ so với 3 giờ trước (°C) ≤ -3,50 | 5,078 (14) | 1,03 / 1,00 / 1,02 | 13/14 · 7/10 | chưa |

### Nghỉ xảy ra khi nào, ở gần hay xa nước? (2007–2008)
| Vị trí | Giờ | Số cửa sổ | Tỉ lệ nghỉ |
|---|---|---:|---:|
| Xa nước (> 200 m) | 00:00–04:30 | 9,116 | 27,7% |
| Xa nước (> 200 m) | 04:30–06:00 | 3,088 | 7,2% |
| Xa nước (> 200 m) | 06:00–18:00 | 21,949 | 2,0% |
| Xa nước (> 200 m) | 18:00–24:00 | 12,126 | 5,3% |
| Ở nguồn nước (≤ 200 m) | 00:00–04:30 | 1,406 | 26,6% |
| Ở nguồn nước (≤ 200 m) | 04:30–06:00 | 405 | 7,9% |
| Ở nguồn nước (≤ 200 m) | 06:00–18:00 | 7,973 | 3,4% |
| Ở nguồn nước (≤ 200 m) | 18:00–24:00 | 3,144 | 6,1% |

Nghỉ tập trung từ nửa đêm tới khoảng 4 giờ sáng và xảy ra gần như nhau ở gần lẫn xa nguồn nước: nghỉ không gắn với việc ở cạnh nước.

Ban đêm (00:00–04:30), cây gỗ càng rậm càng nghỉ nhiều:
| Cây gỗ % | Số mẫu | Tỉ lệ nghỉ |
|---|---:|---:|
| 0–15 | 629 | 21,3% |
| 15–30 | 3,093 | 23,3% |
| 30–45 | 4,843 | 28,0% |
| 45–60 | 1,323 | 37,5% |
| > 60 | 41 | 48,8% |

Ban ngày (09:00–15:00), nhiệt độ không đổi nhiều tỉ lệ nghỉ:
| °C | Số mẫu | Tỉ lệ nghỉ |
|---|---:|---:|
| < 25 | 1,877 | 2,6% |
| 25–30 | 3,343 | 2,3% |
| 30–35 | 6,823 | 3,6% |
| 35–40 | 6,308 | 3,0% |
| ≥ 40 | 332 | 5,1% |

## Câu hỏi 2. Voi đang ở xa nước (> 200 m) có quay lại vùng nước trong 3 giờ tới không?

**Về nước** = có điểm GPS trong vùng 200 m quanh nguồn nước trong 3 giờ tới (GPS không trống > 60 phút). Đây là xu hướng
quay lại nước, chưa quan sát được voi có uống hay không. Tỉ lệ về nước: 22,0% (fit), 24,3% (2009).

| Mô hình | macro-F1 validation | macro-F1 2009 (đối chiếu) | Accuracy 2009 |
|---|---:|---:|---:|
| Cây (14 luật) | 0,70 | 0,69 | 73,2% |
| Luôn đoán lớp đông nhất | 0,44 | 0,43 | 75,7% |

| Bỏ nhóm feature | macro-F1 validation | macro-F1 2009 |
|---|---:|---:|
| Không bỏ | 0,70 | 0,69 |
| Giờ | 0,67 | 0,68 |
| Nhiệt độ | 0,65 | 0,66 |
| Mùa | 0,70 | 0,69 |
| Khoảng cách tới nước | 0,57 | 0,58 |
| Cây gỗ | 0,70 | 0,69 |
| Chất lượng GPS | 0,70 | 0,69 |
| Thời gian rời nước | 0,68 | 0,69 |

Khoảng cách tới nước là yếu tố mạnh nhất nhưng hiển nhiên (càng gần càng dễ về). Vì vậy các bảng dưới cố định giờ (06:00–16:00)
và khoảng cách (0,3–1,5 km): n = 9,585, tỉ lệ chung 43,2%.

| Nhiệt độ vòng cổ °C | Số mẫu | Xác suất về nước trong 3 giờ |
|---|---:|---:|
| ≤ 25 | 3,027 | 36,5% |
| 25–30 | 2,102 | 43,7% |
| 30–35 | 2,368 | 46,5% |
| 35–40 | 2,013 | 48,7% |
| > 40 | 75 | 49,3% |

Nhiệt độ cao đi kèm xu hướng quay lại nước nhiều hơn dù đã cố định giờ và khoảng cách.

| Cây gỗ % | Số mẫu | Xác suất về nước trong 3 giờ |
|---|---:|---:|
| 0–25 | 1,587 | 47,2% |
| 25–35 | 2,220 | 49,0% |
| 35–45 | 3,658 | 41,9% |
| > 45 | 1,744 | 36,2% |
| Mùa (lịch quy ước) | Số mẫu | Xác suất về nước trong 3 giờ |
|---|---:|---:|
| Mùa khô | 4,069 | 37,4% |
| Mùa mưa | 5,516 | 47,5% |
| Thời gian đã rời nước | Số mẫu | Xác suất về nước trong 3 giờ |
|---|---:|---:|
| < 3 h | 2,646 | 45,8% |
| 3–6 | 958 | 39,1% |
| 6–12 | 1,863 | 38,9% |
| 12–24 | 2,947 | 48,2% |
| 24–48 | 765 | 36,2% |
| > 48 h | 406 | 32,5% |

Theo khoảng cách (06:00–16:00):
| Khoảng cách tới nước | Số mẫu | Xác suất về nước trong 3 giờ |
|---|---:|---:|
| < 0,3 km | 1,475 | 78,8% |
| 0,3–0,6 | 3,402 | 61,4% |
| 0,6–1 | 3,130 | 40,0% |
| 1–2 | 5,152 | 22,5% |
| 2–4 | 4,579 | 7,2% |
| > 4 km | 953 | 1,1% |

### Luật
| Dự đoán | Điều kiện | Mẫu (voi) | Lift fit / val / 2009 | Voi lift > 1 (2007–08 · 2009) | Ổn định |
|---|---|---:|---|---|---|
| Chưa về nước | Khoảng cách tới nguồn nước gần nhất (km) > 2,82 · Nhiệt độ so với 3 giờ trước (°C) ≤ 0,50 | 4,216 (13) | 1,27 / 1,26 / 1,31 | 12/12 · 6/6 | có |
| Chưa về nước | 0,80 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 1,71 · Nhiệt độ so với 3 giờ trước (°C) ≤ 0,50 · Giờ địa phương ≤ 03:45 | 2,786 (14) | 1,23 / 1,25 / 1,28 | 14/14 · 9/9 | có |
| Chưa về nước | 1,71 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 2,82 · Nhiệt độ so với 3 giờ trước (°C) ≤ 0,50 | 5,612 (14) | 1,23 / 1,23 / 1,27 | 14/14 · 11/11 | có |
| Chưa về nước | Khoảng cách tới nguồn nước gần nhất (km) > 2,55 · Nhiệt độ so với 3 giờ trước (°C) > 0,50 | 2,947 (13) | 1,23 / 1,21 / 1,23 | 12/12 · 6/6 | có |
| Chưa về nước | 0,44 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,80 · Giờ địa phương ≤ 03:45 | 1,644 (14) | 1,13 / 1,18 / 1,15 | 13/13 · 6/7 | có |
| Chưa về nước | 0,80 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 1,71 · Nhiệt độ so với 3 giờ trước (°C) ≤ 0,50 · Giờ địa phương > 03:45 | 6,973 (14) | 1,10 / 1,11 / 1,12 | 13/14 · 11/11 | có |
| Về nước trong 3 giờ | Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,54 · 03:45 < Giờ địa phương ≤ 17:15 | 5,500 (14) | 2,99 / 2,96 / 2,62 | 14/14 · 11/11 | có |
| Về nước trong 3 giờ | 0,54 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,80 · 03:45 < Giờ địa phương ≤ 17:15 | 3,052 (14) | 2,05 / 1,86 / 1,83 | 14/14 · 9/9 | có |
| Về nước trong 3 giờ | Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,46 · Giờ địa phương > 17:15 | 2,095 (14) | 2,06 / 1,83 / 1,63 | 13/13 · 9/9 | có |
| Về nước trong 3 giờ | 0,80 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 1,20 · Nhiệt độ so với 3 giờ trước (°C) > 0,50 | 2,025 (14) | 1,53 / 1,63 / 1,43 | 13/14 · 6/7 | có |
| Về nước trong 3 giờ | Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,44 · Giờ địa phương ≤ 03:45 | 1,134 (14) | 1,49 / 1,39 / 1,38 | 12/13 · 4/6 | có |
| Chưa về nước | 1,71 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 2,55 · Nhiệt độ so với 3 giờ trước (°C) > 0,50 | 2,019 (14) | 1,09 / 1,08 / 1,10 | 11/12 · 5/7 | chưa |
| Chưa về nước | 0,46 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,80 · Giờ địa phương > 17:15 | 2,307 (14) | 0,99 / 1,03 / 0,99 | 8/14 · 5/9 | chưa |
| Về nước trong 3 giờ | 1,20 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 1,71 · Nhiệt độ so với 3 giờ trước (°C) > 0,50 | 1,997 (14) | 1,05 / 0,97 / 0,96 | 7/13 · 3/7 | chưa |

## Câu hỏi 3. Ban ngày, khi voi đi, đi nhanh hay chậm?

Chỉ xét cửa sổ 06:00–18:00 mà voi đi (đường đi ≥ 75 m). **Nhanh** = đường đi 90 phút trên 652 m (trung vị của dữ liệu học).
Ví dụ: voi cho cây dự đoán tốc độ *nếu* nó đi; cây không biết trước voi có đi hay không.

| Mô hình | macro-F1 validation | macro-F1 2009 (đối chiếu) | Accuracy 2009 |
|---|---:|---:|---:|
| Cây (17 luật) | 0,57 | 0,62 | 62,5% |
| Luôn đoán lớp đông nhất | 0,39 | 0,34 | 50,9% |

| Bỏ nhóm feature | macro-F1 validation | macro-F1 2009 |
|---|---:|---:|
| Không bỏ | 0,57 | 0,62 |
| Giờ | 0,58 | 0,60 |
| Nhiệt độ | 0,57 | 0,62 |
| Mùa | 0,56 | 0,60 |
| Khoảng cách tới nước | 0,57 | 0,62 |
| Cây gỗ | 0,58 | 0,62 |
| Chất lượng GPS | 0,57 | 0,62 |
| Thời gian rời nước | 0,56 | 0,62 |

Tỉ lệ đi nhanh theo cây gỗ ~300 m (2007–2008):
| Cây gỗ % | Số mẫu | Đi nhanh |
|---|---:|---:|
| 0–25 | 4,736 | 53,5% |
| 25–35 | 7,582 | 49,7% |
| 35–45 | 12,279 | 41,9% |
| > 45 | 3,215 | 34,1% |
Theo mùa:
| Mùa | Số mẫu | Đi nhanh |
|---|---:|---:|
| Mùa khô | 14,507 | 35,7% |
| Mùa mưa | 14,705 | 53,4% |
Theo nhiệt độ vòng cổ:
| °C | Số mẫu | Đi nhanh |
|---|---:|---:|
| ≤ 25 | 7,576 | 37,5% |
| 25–30 | 5,319 | 45,3% |
| 30–35 | 8,151 | 46,7% |
| 35–40 | 7,798 | 49,1% |
| > 40 | 368 | 40,0% |

### Luật
| Dự đoán | Điều kiện | Mẫu (voi) | Lift fit / val / 2009 | Voi lift > 1 (2007–08 · 2009) | Ổn định |
|---|---|---:|---|---|---|
| Đi chậm | mùa khô · Giờ địa phương ≤ 14:15 · Độ che phủ cây gỗ trung bình ~300 m (%) > 45,10 | 1,039 (14) | 1,44 / 1,33 / 1,62 | 10/10 · 4/4 | có |
| Đi chậm | mùa khô · Giờ địa phương ≤ 14:15 · Độ che phủ cây gỗ trung bình ~300 m (%) ≤ 45,10 · 5,49 < Thời gian ngoài vùng gần nước (giờ) ≤ 14,99 | 4,322 (14) | 1,32 / 1,18 / 1,31 | 14/14 · 9/9 | có |
| Đi nhanh | mùa mưa · Độ che phủ cây gỗ tại GPS (%) ≤ 34,88 · Khoảng cách tới nguồn nước gần nhất (km) > 0,31 · Thời gian ngoài vùng gần nước (giờ) ≤ 3,74 | 1,258 (14) | 1,49 / 1,93 / 1,56 | 8/8 · 6/6 | có |
| Đi nhanh | mùa mưa · Độ che phủ cây gỗ tại GPS (%) ≤ 34,88 · Khoảng cách tới nguồn nước gần nhất (km) > 0,31 · Thời gian ngoài vùng gần nước (giờ) > 3,74 · Nhiệt độ vòng cổ (°C) > 28,50 | 1,602 (14) | 1,36 / 1,68 / 1,52 | 9/9 · 5/5 | có |
| Đi nhanh | mùa mưa · Độ che phủ cây gỗ tại GPS (%) ≤ 34,88 · Khoảng cách tới nguồn nước gần nhất (km) > 0,31 · Thời gian ngoài vùng gần nước (giờ) > 3,74 · Nhiệt độ vòng cổ (°C) ≤ 28,50 | 1,256 (14) | 1,27 / 1,26 / 1,56 | 7/7 · 3/3 | có |
| Đi nhanh | mùa mưa · Độ che phủ cây gỗ tại GPS (%) ≤ 34,88 · 0,08 < Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,31 | 1,388 (14) | 1,19 / 1,37 / 1,37 | 9/11 · 4/5 | có |
| Đi nhanh | mùa mưa · Độ che phủ cây gỗ tại GPS (%) > 34,88 · Giờ địa phương > 14:15 | 1,944 (14) | 1,16 / 1,34 / 1,22 | 10/13 · 4/4 | có |
| Đi chậm | mùa khô · Giờ địa phương ≤ 14:15 · Độ che phủ cây gỗ trung bình ~300 m (%) ≤ 45,10 · Thời gian ngoài vùng gần nước (giờ) > 14,99 · Khoảng cách tới nguồn nước gần nhất (km) > 1,30 | 3,230 (14) | 1,26 / 1,04 / 1,19 | 12/12 · 7/8 | chưa |
| Đi chậm | mùa khô · Giờ địa phương > 14:15 · Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,14 | 1,007 (14) | 1,11 / 1,10 / 1,29 | 6/10 · 5/5 | chưa |
| Đi chậm | mùa mưa · Độ che phủ cây gỗ tại GPS (%) > 46,16 · Giờ địa phương ≤ 14:15 · Thời gian ngoài vùng gần nước (giờ) > 4,23 | 1,235 (14) | 1,21 / 1,07 / 1,19 | 10/12 · 1/3 | chưa |
| Đi chậm | mùa khô · Giờ địa phương ≤ 14:15 · Độ che phủ cây gỗ trung bình ~300 m (%) ≤ 45,10 · Thời gian ngoài vùng gần nước (giờ) ≤ 5,49 | 1,103 (14) | 1,09 / 1,03 / 1,29 | 10/13 · 6/6 | chưa |
| Đi chậm | mùa khô · Giờ địa phương > 14:15 · Khoảng cách tới nguồn nước gần nhất (km) > 0,14 · Độ che phủ cây gỗ trung bình ~300 m (%) > 38,31 | 1,086 (14) | 1,09 / 1,02 / 1,29 | 4/11 · 2/4 | chưa |
| Đi chậm | mùa mưa · 34,88 < Độ che phủ cây gỗ tại GPS (%) ≤ 46,16 · Giờ địa phương ≤ 14:15 · Thời gian ngoài vùng gần nước (giờ) > 4,23 | 3,696 (14) | 1,07 / 0,95 / 1,00 | 7/14 · 1/7 | chưa |
| Đi nhanh | mùa mưa · Độ che phủ cây gỗ tại GPS (%) > 34,88 · Giờ địa phương ≤ 14:15 · Thời gian ngoài vùng gần nước (giờ) ≤ 4,23 | 1,323 (14) | 1,03 / 1,53 / 1,02 | 11/13 · 3/4 | chưa |
| Đi nhanh | mùa khô · Giờ địa phương > 14:15 · Khoảng cách tới nguồn nước gần nhất (km) > 0,14 · Độ che phủ cây gỗ trung bình ~300 m (%) ≤ 38,31 | 1,578 (14) | 1,12 / 1,24 / 0,97 | 9/12 · 2/6 | chưa |
| Đi nhanh | mùa mưa · Độ che phủ cây gỗ tại GPS (%) ≤ 34,88 · Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,08 | 1,003 (14) | 1,14 / 0,97 / 1,19 | 6/8 · 1/2 | chưa |
| Đi nhanh | mùa khô · Giờ địa phương ≤ 14:15 · Độ che phủ cây gỗ trung bình ~300 m (%) ≤ 45,10 · Thời gian ngoài vùng gần nước (giờ) > 14,99 · Khoảng cách tới nguồn nước gần nhất (km) ≤ 1,30 | 1,142 (14) | 1,05 / 1,17 / 0,92 | 8/13 · 3/6 | chưa |

## Câu hỏi 4. Voi đang ở trong vùng nước (≤ 200 m) ở lại hay rời đi?

**Ở lại** = đi dưới 150 m trong 90 phút tới. Chưa phân biệt được uống nước, tắm hay nghỉ.

| Mô hình | macro-F1 validation | macro-F1 2009 (đối chiếu) | Accuracy 2009 |
|---|---:|---:|---:|
| Cây (8 luật) | 0,63 | 0,60 | 71,6% |
| Luôn đoán lớp đông nhất | 0,44 | 0,46 | 86,5% |

| Bỏ nhóm feature | macro-F1 validation | macro-F1 2009 |
|---|---:|---:|
| Không bỏ | 0,63 | 0,60 |
| Giờ | 0,54 | 0,53 |
| Nhiệt độ | 0,63 | 0,60 |
| Mùa | 0,63 | 0,66 |
| Khoảng cách tới nước | 0,63 | 0,60 |
| Cây gỗ | 0,62 | 0,64 |
| Chất lượng GPS | 0,63 | 0,60 |

Tỉ lệ ở lại theo giờ (2007–2008):
| Giờ | Số mẫu | Ở lại |
|---|---:|---:|
| 00h | 1,617 | 35,8% |
| 03h | 401 | 59,1% |
| 06h | 1,462 | 11,2% |
| 09h | 809 | 12,4% |
| 12h | 3,600 | 14,1% |
| 15h | 1,323 | 7,3% |
| 18h | 2,992 | 9,7% |
| 21h | 724 | 17,4% |

### Luật
| Dự đoán | Điều kiện | Mẫu (voi) | Lift fit / val / 2009 | Voi lift > 1 (2007–08 · 2009) | Ổn định |
|---|---|---:|---|---|---|
| Ở lại vùng nước | 00:45 < Giờ địa phương ≤ 03:45 · Độ che phủ cây gỗ tại GPS (%) > 36,65 | 398 (14) | 5,21 / 2,93 / 4,03 | 5/5 · 0/0 | có |
| Ở lại vùng nước | 00:45 < Giờ địa phương ≤ 03:45 · Độ che phủ cây gỗ tại GPS (%) ≤ 36,65 | 454 (14) | 3,62 / 2,39 / 3,45 | 6/6 · 0/0 | có |
| Ở lại vùng nước | Giờ địa phương ≤ 00:45 · Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,06 | 278 (14) | 3,16 / 2,37 / 2,41 | 2/2 · 0/0 | có |
| Ở lại vùng nước | Giờ địa phương ≤ 00:45 · Khoảng cách tới nguồn nước gần nhất (km) > 0,06 | 276 (14) | 2,26 / 1,54 / 2,18 | 2/2 · 0/0 | có |
| Ở lại vùng nước | Giờ địa phương > 03:45 · mùa khô · Độ che phủ cây gỗ tại GPS (%) > 37,27 | 2,281 (14) | 1,08 / 1,28 / 1,34 | 11/13 · 6/7 | có |
| Rời đi | Giờ địa phương > 03:45 · mùa mưa · Khoảng cách tới nguồn nước gần nhất (km) > 0,07 | 2,954 (14) | 1,08 / 1,19 / 1,10 | 14/14 · 8/10 | chưa |
| Rời đi | Giờ địa phương > 03:45 · mùa mưa · Khoảng cách tới nguồn nước gần nhất (km) ≤ 0,07 | 3,196 (14) | 1,04 / 1,05 / 1,08 | 13/14 · 8/8 | chưa |
| Rời đi | Giờ địa phương > 03:45 · mùa khô · Độ che phủ cây gỗ tại GPS (%) ≤ 37,27 | 3,091 (14) | 1,02 / 1,09 / 1,03 | 10/13 · 4/7 | chưa |

## Chuyến đi giữa hai lần ghé nước (Hình 2 của paper), 2007–2008
2,233 chuyến (mùa khô 1,158, mùa mưa 1,075). Trung vị thời lượng 22.0 giờ (khô) và
19.0 giờ (mưa); đường đi 7.4 / 7.5 km; xa nước nhất 2.2 / 1.7 km.

## Giới hạn
- Nhãn là hình học quỹ đạo và khoảng cách tới lớp nước của dự án; không quan sát được ngủ, ăn hay uống.
- Cửa sổ 90 phút có ~4 điểm GPS; GPS thiếu làm đường đi ngắn đi (đã loại cửa sổ trống > 60 phút).
- "Ổn định" = lift > 1,1 ở validation và 2009, và > 1 ở ít nhất 2/3 số voi đủ mẫu. Lift fit/validation là trong mẫu.
- Mùa theo lịch quy ước; cây gỗ là bề mặt nội suy của tác giả; liên hệ không đồng nghĩa nhân quả.
