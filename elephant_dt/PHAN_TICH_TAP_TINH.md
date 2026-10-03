# Phân tích sâu: bốn cây nói gì về tập tính của voi

Tài liệu này đi sâu vào pattern của từng cây: cây tìm ra điều gì, số liệu nào chống đỡ điều đó, có thể diễn giải thành tập tính nào của voi, và điều gì **không** được phép nói.
Phần giải thích dữ liệu, cách chia train/test và kịch bản thuyết trình nằm ở `KICH_BAN_SLIDE.md`. Mọi bảng số liệu ở đây lấy từ `outputs/behavior_stats.md` (tạo bởi `09_behavior_stats.py`) và `outputs/tasks_report.md`.

## 0. Cách đọc tài liệu này

**Ba loại thông tin, không được trộn với nhau.**

| Loại | Nghĩa | Ví dụ |
| --- | --- | --- |
| **Cây tìm ra** | Một luật (một lá) của cây, đã kiểm trên 2008 và 2009 | "00:45–03:45 → nghỉ" |
| **Số liệu mô tả** | Tôi đếm thêm trên cùng dữ liệu để xem pattern có đúng không, chi tiết hơn cây | "80% đợt nghỉ chỉ kéo dài một cửa sổ" |
| **Diễn giải** | Giả thuyết về hành vi, GPS không quan sát trực tiếp | "voi đang ngủ" |

**Quy ước số liệu.**
- Một mẫu là một cửa sổ 90 phút, đặt trên lưới 90 phút (00:00, 01:30, 03:00, …). Giờ ghi trong bảng là **giờ bắt đầu cửa sổ** (giờ địa phương); nhãn nói về 90 phút *sau* mốc đó. Vì vậy "mốc 03:00" nghĩa là voi ở trạng thái đó trong khoảng 03:00–04:30.
- "học" là 08/2007–12/2008 (cây được học và chọn cấu hình trên đó). "2009" là năm đối chiếu, **đã được xem ở các phiên bản trước** nên không phải bài kiểm tra mù.
- Một pattern đáng tin khi **giữ nguyên ở cả "học" và "2009"**, và có ở đa số voi.
- Lift = tỉ lệ nhãn trong nhánh ÷ tỉ lệ chung. Lift 3 nghĩa là nhãn đó xảy ra gấp 3 lần mức chung.

**Giới hạn chung (áp dụng cho cả bốn cây).**
- GPS có sai số nên "nghỉ", "ở lại" chỉ là *ít di chuyển*, không phải chắc chắn voi đứng im hay ngủ.
- Cây chỉ nhìn đại lượng hình học (khoảng cách đi, khoảng cách tới nước, giờ, nhiệt độ vòng cổ, cây gỗ, mùa). Không có dữ liệu về thức ăn, thú săn mồi, người, trăng, đàn hay tuổi.
- Mùa là mốc theo lịch (mùa mưa 13/10–21/04), không phải số liệu mưa thật.
- Cây gỗ là bề mặt do tác giả nội suy, độ phân giải khoảng 100 m.
- Nhiệt độ là nhiệt độ **vòng cổ**, gồm cả nhiệt do mạch điện và thân nhiệt voi. Paper cảnh báo không dùng nó như nhiệt độ môi trường thật.
- Tất cả là liên hệ trong dữ liệu, không phải nhân quả.

---

## 1. Cây 1: Nghỉ hay di chuyển (nhịp nghỉ / ngủ)

### 1.1 Cây tìm ra gì

| Luật | Mẫu | Lift (học / val / 2009) | Voi lift > 1 (2007–08 · 2009) |
| --- | ---: | --- | --- |
| 00:45 < giờ ≤ 03:45 → **nghỉ** | 6.817 | 4,74 / 3,63 / 4,62 | 14/14 · 10/10 |
| giờ ≤ 00:45 → nghỉ | 3.705 | 2,04 / 1,92 / 2,03 | 14/14 · 7/9 |
| giờ > 20:15 và nhiệt độ so với 3 giờ trước > −3,5 °C → nghỉ | 2.561 | 1,34 / 1,29 / 0,87 | 10/14 · 4/9 (chưa ổn định) |
| 03:45 < giờ ≤ 20:15 → di chuyển (cả mùa khô lẫn mùa mưa) | ~41.000 | ~1,05 | 14/14 · 10/10 |

Cây chỉ thực sự dùng **giờ**; bỏ giờ thì macro-F1 rơi từ 0,61 xuống 0,49, còn bỏ mùa, nước, cây gỗ, nhiệt độ gần như không đổi. Nghĩa là **nghỉ là chuyện của đồng hồ, không phải chuyện của chỗ ở**.

### 1.2 Số liệu đi sâu

**a. Nhịp theo giờ.** Tỉ lệ cửa sổ "nghỉ" theo giờ bắt đầu:

| Giờ bắt đầu | 22:30 | 00:00 | 01:30 | 03:00 | 04:30 | 06:00 | 12:00 | 15:00 | 18:00 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| học | 9,2% | 15,8% | 29,9% | **38,2%** | 7,3% | 0,9% | 4,5% | 1,4% | 1,9% |
| 2009 | 6,3% | 13,7% | 25,6% | **36,8%** | 9,3% | 1,2% | 2,8% | 0,4% | 1,5% |

Hình dạng: nghỉ tăng dần từ khoảng 22:30, đạt đỉnh ở mốc 03:00 (khoảng 03:00–04:30), rồi **rơi đột ngột** sang mốc 04:30 (38% → 7%). 67% số cửa sổ nghỉ của cả dữ liệu (74% ở 2009) rơi vào bốn mốc 00:00–04:30. Ban ngày (06:00–18:00) nghỉ chỉ 2,4% (2009: 1,6%).

**b. Nghỉ ban đêm ít hơn người ta tưởng.** Ngay trong khung vàng, voi cũng **không nghỉ phần lớn thời gian**: chỉ 30–38% cửa sổ nghỉ. Xét từng đêm của từng voi (đêm có đủ 4 cửa sổ 00:00–06:00): 66% đêm có ít nhất một cửa sổ nghỉ, 22% đêm có từ hai cửa sổ nghỉ trở lên, **34% đêm không có cửa sổ nghỉ nào** (2009: 60% / 19% / 40%). Pattern là xu hướng thống kê, không phải "đêm nào voi cũng nghỉ".

**c. Mỗi đợt nghỉ ngắn.** Đợt nghỉ = các cửa sổ nghỉ liên tiếp.

| Số cửa sổ liên tiếp | 1 (≈ 1,5 giờ) | 2 (≈ 3 giờ) | 3 | ≥ 4 |
| --- | ---: | ---: | ---: | ---: |
| Tỉ lệ đợt (học) | 79,7% | 17,4% | 2,4% | 0,5% |
| Tỉ lệ đợt (2009) | 80,0% | 17,5% | 2,4% | 0 |

Đợt dài nhất chỉ 5 cửa sổ (khoảng 7,5 giờ), và chỉ vài lần. Trong các ngày có đủ dữ liệu cả 16 cửa sổ, tổng thời gian "nghỉ" trung vị khoảng **1,5 giờ/ngày**, trung bình 2,0 giờ (học) và 1,6 giờ (2009). Lưu ý: cửa sổ nằm trên lưới 90 phút nên các con số này thô, và chỉ tính những ngày GPS đủ liền mạch (1.799 ngày-voi học, 332 ngày-voi 2009).

**d. Nghỉ có gắn với nước không? Không.** Ban đêm (00:00–06:00), tỉ lệ nghỉ theo khoảng cách tới nước gần như phẳng:

| Cách nước | ≤ 0,2 km | 0,2–0,5 | 0,5–1 | 1–2 | > 2 km |
| --- | ---: | ---: | ---: | ---: | ---: |
| học | 22,4% | 21,8% | 21,2% | 23,6% | 23,0% |
| 2009 | 21,5% | 22,4% | 23,8% | 20,7% | 18,1% |

Hơn nữa phần lớn cửa sổ ban đêm nằm **xa** nước (khoảng 87% cửa sổ 00:00–06:00 cách nước hơn 200 m). Voi nghỉ ở chỗ nó đang đứng, không đi tới nước để nghỉ.

**e. Mùa.** Trong khung 00:45–03:45: mùa khô 34,9% và mùa mưa 33,0% (học); 27,7% và 34,3% (2009). Không có khác biệt ổn định.

**f. Cây gỗ (không do cây tìm ra, đây là phân tích mô tả).** Ban đêm, cây gỗ tại điểm GPS càng dày thì tỉ lệ nghỉ nhìn chung càng cao (ở 2009 nhóm 0–15% cao hơn nhóm 15–30%, nên không đều):

| Cây gỗ (%) | 0–15 | 15–30 | 30–45 | 45–60 | > 60 |
| --- | ---: | ---: | ---: | ---: | ---: |
| học | 17,4% | 19,2% | 22,8% | 29,9% | 38,1% (n = 63) |
| 2009 | 18,8% | 13,3% | 24,0% | 30,5% | 46,2% (n = 13) |

Xu hướng chung cùng chiều nhưng hai nhóm cao nhất có ít mẫu. Cây không dùng đặc trưng này vì thêm nó không cải thiện dự đoán.

**g. Nhiệt độ.** Ban ngày (09:00–15:00) nhiệt độ từ dưới 25 đến trên 40 °C gần như không đổi tỉ lệ nghỉ (2–5%). Nhiệt độ liên quan tới nghỉ chủ yếu vì nó đi cùng giờ (đêm mát, ngày nóng).

**h. Khác biệt giữa từng voi.** Tỉ lệ nghỉ trong khung 00:45–03:45 dao động từ 16,7% (AM105) đến 43,7% (AM108) ở dữ liệu học, và từ 15,9% (AM107) đến 48,0% (AM108) năm 2009. AM108 và AM254 luôn thuộc nhóm nghỉ nhiều, AM105 luôn nghỉ ít; nhưng AM107 từ 32% xuống 16%, tức khác biệt cá thể có phần không ổn định. Cây không dùng danh tính voi nên khác biệt này không nằm trong luật.

**i. Một chi tiết nhỏ ban ngày.** Mốc 10:30–12:00 có một chỗ nhô nhẹ (4,3% nghỉ, so với ~1–2% buổi sáng sớm và chiều muộn). Có thể là nghỉ giữa trưa lúc nóng, nhưng chỗ nhô này nhỏ và yếu hơn ở 2009 (3,2%), chỉ nên coi là gợi ý.

### 1.3 Diễn giải thành tập tính

1. **Voi có một "cửa sổ nghỉ" ban đêm khá hẹp**, tập trung khoảng 01:30–04:30, đỉnh 03:00–04:30. Pattern giữ nguyên ở cả hai giai đoạn và ở đa số voi.
2. **Kết thúc nghỉ rất dứt khoát lúc 04:30–06:00**: tỉ lệ nghỉ rơi từ 38% xuống 7% trong một mốc 90 phút. Voi dậy và bắt đầu đi trước khi trời sáng hẳn (mặt trời ở Kruger mọc khoảng 05:00–07:00 tùy mùa; số này là kiến thức chung, không nằm trong dữ liệu).
3. **Nghỉ ngắn và vụn**: khoảng 80% đợt nghỉ chỉ dài một cửa sổ. Ước lượng thô khoảng 1,5–2 giờ "ít di chuyển" mỗi ngày. Nếu một số nghiên cứu khác ghi nhận voi hoang dã ngủ rất ít (cỡ vài giờ mỗi ngày, ví dụ Gravett và cộng sự 2017, PLoS ONE), kết quả này không mâu thuẫn. **Cần kiểm lại nguồn trước khi đưa lên slide.**
4. **Nghỉ không phụ thuộc có ở gần nước hay không**, cũng không khác theo mùa. Có xu hướng nghỉ nhiều hơn ở nơi cây gỗ dày (có thể là chỗ kín, có bóng cây; giả thuyết).
5. **Ban ngày voi hầu như luôn di chuyển** (97,6% cửa sổ có đi từ 75 m trở lên), dù trời nóng.

### 1.4 Không nói được

- Không nói "voi ngủ". GPS chỉ cho thấy voi ít di chuyển; voi có thể đứng ngủ, đứng nghỉ, ăn tại chỗ hay cảnh giới. Cách nói an toàn: "voi **ít di chuyển**, có thể là ngủ hoặc nghỉ ngơi".
- Không nói "voi ngủ khoảng 2 giờ". Con số 1,5–2 giờ chỉ là thời gian GPS gần như đứng yên theo lưới 90 phút.
- Không nói "mỗi đêm voi nghỉ". Một phần ba số đêm không có cửa sổ nghỉ nào.
- Không nói cây gỗ làm voi nghỉ nhiều hơn.

### 1.5 Câu có thể nói

> "Voi nghỉ tập trung vào khoảng 01:30 đến 04:30 đêm, đỉnh ở 03:00–04:30. Trong khung đó, khả năng voi ít di chuyển gấp khoảng 4 lần bình thường (3,6 đến 4,7 lần tùy giai đoạn), và pattern này vẫn đúng ở 2009. Sau 04:30 voi nhanh chóng quay lại di chuyển."

---

## 2. Cây 2: Có quay lại nước không (nhịp đi uống nước)

Chỉ xét cửa sổ mà voi đang cách nước hơn 200 m. Nhãn "về nước" = trong 3 giờ tới có một điểm GPS nằm trong vùng 200 m quanh nguồn nước. Tỉ lệ chung khoảng 22–24%.

### 2.1 Cây tìm ra gì

| Luật | Mẫu | Lift (học / val / 2009) | Voi lift > 1 (2007–08 · 2009) |
| --- | ---: | --- | --- |
| cách nước ≤ 540 m, 03:45 < giờ ≤ 17:15 → **về nước** | 5.500 | 2,99 / 2,96 / 2,62 | 14/14 · 11/11 |
| cách nước 540–800 m, 03:45 < giờ ≤ 17:15 → về nước | 3.052 | 2,05 / 1,86 / 1,83 | 14/14 · 9/9 |
| cách nước ≤ 460 m, giờ > 17:15 → về nước | 2.095 | 2,06 / 1,83 / 1,63 | 13/13 · 9/9 |
| cách nước ≤ 440 m, giờ ≤ 03:45 → về nước | 1.134 | 1,49 / 1,39 / 1,38 | 12/13 · 4/6 |
| cách nước 0,8–1,2 km, nhiệt độ **tăng** hơn 0,5 °C so với 3 giờ trước → về nước | 2.025 | 1,53 / 1,63 / 1,43 | 13/14 · 6/7 |
| cách nước > 2,8 km (nhiệt độ không tăng) → chưa về nước | 4.216 | 1,27 / 1,26 / 1,31 | 12/12 · 6/6 |

Bỏ khoảng cách tới nước thì macro-F1 rơi từ 0,70 xuống 0,57: đây là yếu tố mạnh nhất. Bỏ nhiệt độ rơi xuống 0,65, bỏ giờ xuống 0,67. Mùa và cây gỗ không giúp thêm.
Chú ý: đặc trưng nhiệt độ mà cây dùng là **mức thay đổi trong 3 giờ qua**, nên nó mô tả "trời đang ấm lên" (buổi sáng), không phải nhiệt độ tuyệt đối.

### 2.2 Số liệu đi sâu

**a. Khoảng cách: hiển nhiên nhưng có thể đo.** Xác suất về nước trong 3 giờ theo khoảng cách tới nước (mọi giờ):

| Cách nước | 0,2–0,3 km | 0,3–0,6 | 0,6–1 | 1–2 | 2–4 | > 4 km |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| học | 63,7% | 43,7% | 24,4% | 13,0% | 4,4% | 0,9% |
| 2009 | 62,4% | 45,0% | 26,3% | 13,7% | 5,0% | 2,1% |

Xác suất giảm rất nhanh khi xa nước: khoảng 44% ở cỡ 0,5 km, 13% ở 1–2 km, 4–5% ở 2–4 km. Voi hiếm khi đi tới nước trong 3 giờ từ cách trên 2 km.

**b. Giờ: đây mới là phần "tập tính".** Cố định khoảng cách 0,3–1,5 km để so sánh công bằng:

| Giờ bắt đầu | 00:00 | 01:30 | 03:00 | 04:30 | 06:00 | 07:30 | 09:00 | 10:30 | 12:00 | 13:30 | 15:00 | 16:30 | 18:00 | 19:30 | 21:00 | 22:30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| học | 10% | 6% | 11% | 25% | 35% | 43% | 48% | **48%** | 45% | 42% | 43% | 38% | 26% | 18% | 16% | 14% |
| 2009 | 12% | 8% | 9% | 27% | 40% | 40% | 52% | **55%** | 52% | 45% | 43% | 31% | 30% | 22% | 18% | 12% |

Hình dạng: rất thấp giữa đêm (6–12% ở các mốc 00:00–03:00), bắt đầu leo từ 04:30, **đỉnh vào buổi sáng 09:00–12:00**, giữ cao đến 15:00 rồi giảm dần về tối. Gộp lại: ban ngày (06–18h) 42,5% (2009: 44,5%), ban đêm (18–06h) chỉ 15,9% (2009: 17,6%), cùng khoảng cách.

**c. Chu kỳ một chuyến đi (từ hai lần ghé nước liên tiếp).** Có 2.913 chuyến của 14 voi (2007–2009).

| | Mùa khô | Mùa mưa |
| --- | ---: | ---: |
| Số chuyến | 1.500 | 1.413 |
| Thời lượng trung vị | 22,0 giờ | 19,0 giờ |
| Đường đi trung vị | 7,3 km | 7,9 km |
| Xa nước nhất (trung vị) | 2,2 km | 1,8 km |

| Khung giờ | 00–03 | 03–06 | 06–09 | 09–12 | 12–15 | 15–18 | 18–21 | 21–24 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Giờ **rời** nước | 6% | 2% | 4% | 5% | 14% | **31%** | **26%** | 12% |
| Giờ **về** nước | 2% | 3% | 17% | **26%** | 22% | 15% | 10% | 5% |

57% số chuyến **rời** nước vào lúc 15:00–21:00; 65% số chuyến **về** nước vào lúc 06:00–15:00. Một chuyến điển hình kéo dài cỡ một ngày (19–22 giờ), đi khoảng 7–8 km nhưng chỉ cách nước tối đa khoảng 2 km: voi **đi vòng quanh nguồn nước**, không đi xa rồi mới quay về.

**d. Nóng lên thì về nước nhiều hơn, nhưng tác động khiêm tốn.** Ban ngày (06–18h), cách nước 0,3–1,5 km:

| Nhiệt độ vòng cổ | ≤ 25 °C | 25–30 | 30–35 | > 35 |
| --- | ---: | ---: | ---: | ---: |
| học | 36,4% | 43,3% | 44,9% | 46,3% |
| 2009 | 36,2% | 50,2% | 48,6% | 43,7% |

Từ ≤ 25 lên 25–30 °C xác suất tăng 7–14 điểm, sau đó **không tăng thêm** (năm 2009 còn giảm nhẹ ở > 35 °C). Dạng "bậc thang rồi bằng" chứ không phải càng nóng càng về nước. Nhớ rằng nhiệt độ vòng cổ đi cùng giờ trong ngày.

**e. Mùa.** Cùng khoảng cách 0,3–1,5 km, mùa mưa về nước nhiều hơn mùa khô: 31,2% so với 23,8% (học), 34,8% so với 24,8% (2009). Ngược với trực giác "mùa khô khát hơn". Giả thuyết: mùa mưa có nhiều vũng nước nhỏ nên voi ghé nước thường hơn và đổi nguồn nhanh; hoặc "nguồn nước gần nhất" thay đổi theo mùa nên cùng khoảng cách mà ý nghĩa khác nhau. Chưa kiểm.

**f. Đã rời nước bao lâu.**

| Đã rời nước | < 3 giờ | 3–6 | 6–12 | 12–24 | 24–48 | > 48 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| học | 28,0% | 19,8% | 24,2% | **42,6%** | 28,2% | 22,6% |
| 2009 | 30,6% | 23,5% | 26,1% | **44,7%** | 29,4% | 26,2% |

Đỉnh ở 12–24 giờ sau khi rời nước, khớp với chu kỳ cỡ một ngày. Không có dấu hiệu "càng lâu không uống càng khát": đã ngoài 24 giờ thì xác suất về nước **giảm**. Nhưng 12–24 giờ sau chuyến rời nước chiều tối chính là sáng hôm sau, nên kết quả này phần lớn là hiệu ứng giờ trong ngày.

### 2.3 Diễn giải thành tập tính

1. **Voi có nhịp đi uống nước theo ngày**: rời nước vào chiều tối (15:00–21:00), ở lại xa nước qua đêm, về nước từ khoảng 06:00 và nhiều nhất vào buổi sáng (09:00–12:00). Chu kỳ khoảng một ngày. Đây là cùng bức tranh "shuttling" mà paper mô tả (chu kỳ đỉnh 10–30 giờ; rời nước khoảng 13:00–14:00 và về khoảng 10:00–11:00 theo trung bình của paper). Con số của chúng tôi lệch đôi chút (rời muộn hơn) nhưng cùng hình dạng, vì định nghĩa chuyến và cách tính khác nhau.
2. **Ban đêm voi ít chủ động đi tới nước**: 6–12% cho ba mốc giữa đêm, so với 45–55% buổi sáng. Voi chỉ ghé nước ban đêm khi đã ở rất gần (≤ 460 m).
3. **Voi sống quanh nước trong bán kính khoảng 2 km**: chuyến điển hình đi 7–8 km nhưng xa nước nhất khoảng 2 km.
4. **Nhiệt độ có tác động nhỏ**: buổi sáng trời ấm dần thì voi cách nước 0,8–1,2 km có xu hướng đi về nước. Paper nhấn mạnh nhiệt độ là động lực chính; dữ liệu của chúng tôi chỉ ủng hộ ở mức khiêm tốn và thấy rõ nhất khi so với trời mát.

### 2.4 Không nói được

- Không nói "voi đi uống nước". Cây chỉ biết voi **vào vùng 200 m quanh nước**. Có thể voi uống, tắm, bôi bùn, hoặc chỉ đi dọc sông (vùng 200 m quanh các đoạn sông dài rất rộng).
- Không nói "voi khát". Không có đo lượng nước hay mất nước.
- Không nói "nóng là nguyên nhân". Nhiệt độ vòng cổ đi cùng giờ, và hiệu ứng bão hòa.
- Không rút kết luận "mùa khô voi khát hơn mùa mưa": dữ liệu cho kết quả ngược lại và chưa giải thích được.
- Khoảng cách tới nước là yếu tố mạnh nhất nhưng hiển nhiên; đừng trình bày nó như phát hiện.

### 2.5 Câu có thể nói

> "Voi có nhịp đi lại quanh nguồn nước theo ngày: chiều tối rời nước, ban đêm ở xa, rồi từ sáng sớm quay lại, nhiều nhất vào buổi sáng. Ban đêm gần như không có chuyện voi chủ động đi tới nước từ xa. Em chỉ nói được voi quay lại *vùng nước*, GPS không cho biết voi có uống hay không."

---

## 3. Cây 3: Đi nhanh hay chậm (cách voi di chuyển ban ngày)

Chỉ xét ban ngày (06:00–18:00) và khi voi có đi (≥ 75 m trong 90 phút; 97,6% cửa sổ ban ngày thỏa). "Nhanh" = đường đi > 653 m / 90 phút (trung vị của tập fit). Đây là cây yếu nhất về độ chính xác: macro-F1 0,57 (val) và 0,62 (2009), so với 0,39 và 0,34 khi luôn đoán một lớp.

Tốc độ trung bình khi voi đi cỡ 0,4 km/giờ (trung vị 585 m / 90 phút ở dữ liệu học, 640 m ở 2009). Paper báo cáo tốc độ trung bình 0,4 km/giờ, cùng cỡ.

**Một điểm cần nhớ:** ngưỡng "nhanh" cố định theo tập fit, nên tỉ lệ nhanh khác nhau giữa các giai đoạn (fit ≈ 50%, validation ≈ 35%, 2009 ≈ 49%). Khi so sánh "học" với "2009", chiều hướng quan trọng hơn con số tuyệt đối.

### 3.1 Cây tìm ra gì

| Luật | Mẫu | Lift (học / val / 2009) | Voi lift > 1 (2007–08 · 2009) |
| --- | ---: | --- | --- |
| mùa khô, trước 14:15, cây gỗ ~300 m > 45% → **chậm** | 1.039 | 1,44 / 1,33 / 1,62 | 10/10 · 4/4 |
| mùa khô, trước 14:15, cây gỗ ≤ 45%, đã rời nước 5,5–15 giờ → chậm | 4.322 | 1,32 / 1,18 / 1,31 | 14/14 · 9/9 |
| mùa mưa, cây gỗ ≤ 35%, cách nước > 310 m, đã rời nước ≤ 3,7 giờ → **nhanh** | 1.258 | 1,49 / 1,93 / 1,56 | 8/8 · 6/6 |
| mùa mưa, cây gỗ ≤ 35%, cách nước 80–310 m → nhanh | 1.388 | 1,19 / 1,37 / 1,37 | 9/11 · 4/5 |
| mùa mưa, cây gỗ > 35%, sau 14:15 → nhanh | 1.944 | 1,16 / 1,34 / 1,22 | 10/13 · 4/4 |

Cả mùa, cây gỗ, giờ và thời gian đã rời nước đều xuất hiện trong cây; bỏ từng nhóm đều không thay đổi nhiều (± 0,02). Cây tốc độ dựa vào **nhiều tín hiệu yếu cộng lại** hơn là một tín hiệu mạnh.

### 3.2 Số liệu đi sâu

**a. Cây gỗ: tín hiệu rõ nhất và nhất quán nhất.** Tỉ lệ đi nhanh theo độ che phủ cây gỗ trong ~300 m quanh voi:

| Cây gỗ ~300 m | 0–25% | 25–35% | 35–45% | > 45% |
| --- | ---: | ---: | ---: | ---: |
| học | 53,5% | 49,7% | 41,9% | 34,1% |
| 2009 | 69,9% | 51,9% | 41,3% | 29,9% |

Giảm đều theo độ dày cây gỗ, ở cả hai giai đoạn. Và hiệu ứng **có trong cả hai mùa**:

| Cây gỗ ~300 m | mùa khô (học / 2009) | mùa mưa (học / 2009) |
| --- | --- | --- |
| ≤ 35% | 40,0% / 46,5% | 61,2% / 71,8% |
| 35–45% | 35,1% / 26,5% | 49,3% / 54,6% |
| > 45% | 23,4% / 20,2% | 42,3% / 41,3% |

**b. Mùa: lớn nhất.** Tỉ lệ đi nhanh: mùa khô 35,7% (2009: 36,2%), mùa mưa 53,4% (2009: 61,2%). Mùa mưa voi đi nhanh hơn rõ rệt. Paper cũng báo cáo mùa mưa nhanh hơn một chút (0,42 so với 0,39 km/giờ) và gợi ý do voi gặm cỏ nhiều hơn là hái lá, nhưng đó là giả thuyết của tác giả, chúng tôi không kiểm.

**c. Giờ trong ngày: sáng đều, chiều tăng tốc.**

| Giờ bắt đầu | 06:00 | 07:30 | 09:00 | 10:30 | 12:00 | 13:30 | 15:00 | 16:30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| học | 40,8% | 41,8% | 42,9% | 42,7% | 41,3% | 42,1% | 49,3% | **55,7%** |
| 2009 | 47,9% | 49,0% | 46,2% | 48,7% | 46,7% | 46,2% | 52,1% | **55,8%** |

Phẳng từ sáng tới 13:30 rồi tăng mạnh từ 15:00 và cao nhất lúc 16:30. Khung giờ này trùng với lúc phần lớn chuyến **rời nước** bắt đầu (15:00–21:00, xem Cây 2).

**d. Đã rời nước bao lâu (mùa khô có dạng chữ U).**

| Đã rời nước | < 3 giờ | 3–6 | 6–15 | > 15 giờ |
| --- | --- | --- | --- | --- |
| mùa khô (học / 2009) | 45,1% / 38,7% | 36,0% / 34,3% | **29,1% / 31,7%** | 39,8% / 41,0% |
| mùa mưa (học / 2009) | 61,1% / 66,1% | 55,5% / 58,5% | 51,9% / 61,2% | 54,1% / 62,5% |

Mùa khô: vừa rời nước thì đi nhanh, giữa chuyến (6–15 giờ) chậm nhất, về cuối chuyến (> 15 giờ) lại nhanh. Mùa mưa gần như phẳng.

**e. Nhiệt độ.** ≤ 25 °C: 37,5% (2009: 38,8%); 25–30 °C: 45,3% (55,2%); 30–35 °C: 46,7% (50,9%); > 35 °C: 48,7% (52,4%). Nóng hơn thì đi nhanh hơn, tác động nhỏ. Nhiệt độ cũng đi cùng giờ và mùa.

### 3.3 Diễn giải thành tập tính

1. **Voi đi chậm hơn ở nơi cây gỗ dày** và nhanh hơn ở nơi thưa, ở cả hai mùa và cả hai giai đoạn. Cách hiểu hợp lý: đi chậm lại để ăn hoặc đứng dưới bóng cây; qua chỗ trống thì đi nhanh. Paper cũng báo cáo tốc độ thấp hơn ở nơi nhiều cây và cho rằng voi đang kiếm ăn hoặc tìm bóng.
2. **Voi đi nhanh hơn vào mùa mưa.** Ở đây trùng với paper.
3. **Chiều tối voi tăng tốc**, cùng lúc voi rời nguồn nước. Hợp với việc đi tới khu kiếm ăn sau khi đã ở gần nước giữa ngày.
4. **Mùa khô có nhịp "đi nhanh rời nước, đi chậm kiếm ăn xa, đi nhanh trở lại"** (dạng U). Đây là giả thuyết đẹp nhưng chỉ có một luật hỗ trợ (4.322 mẫu) và mức tăng nhỏ, nên chỉ nên nêu như gợi ý.
5. **Ban ngày voi hầu như luôn đi, nhưng đi chậm** (~0,4 km/giờ, hợp với việc vừa đi vừa ăn).

Paper còn báo cáo voi đi nhanh nhất lúc vừa rời nước và lúc tới gần nước, chậm nhất ở giữa chuyến; dữ liệu 90 phút của chúng tôi chỉ thấy lờ mờ điều này (dạng U ở mùa khô), vì cửa sổ dài và có nhiều giờ trong ngày bị gộp.

### 3.4 Không nói được

- Không nói "voi đi chậm để kiếm ăn". GPS chỉ cho thấy đường đi ngắn; còn có thể là đứng bóng, nghỉ ngắn, đàn con đi chậm.
- Không nói "cây gỗ làm voi chậm lại" (liên hệ, không phải nhân quả). Cây gỗ ~300 m quanh voi cũng có thể phản ánh loại đất, cỏ, độ dốc.
- Không nói "mùa mưa voi đi nhanh vì ...": chúng tôi không có dữ liệu thức ăn. Mùa lại là mốc theo lịch.
- Độ chính xác của cây này thấp (macro-F1 ~0,6), nên đừng trình bày từng dự đoán cụ thể như đáng tin; trình bày pattern chung.

### 3.5 Câu có thể nói

> "Ban ngày voi đi chậm, khoảng 0,4 km một giờ. Ở nơi cây gỗ dày voi đi chậm hơn rõ rệt, và vào mùa mưa voi đi nhanh hơn mùa khô. Chiều muộn voi tăng tốc, đúng lúc rời nguồn nước. Em coi đây là liên hệ trong dữ liệu, không phải nguyên nhân."

---

## 4. Cây 4: Ở lại hay rời vùng nước (voi làm gì khi đã ở nước)

Chỉ xét cửa sổ mà voi đang trong vùng 200 m quanh nước. "Ở lại" = đi dưới 150 m trong 90 phút tới. Đây là cây có **ít mẫu nhất** (khoảng 12.900 cửa sổ học gồm fit và validation, 3.327 cửa sổ 2009) và bằng chứng yếu nhất ở cấp độ từng voi. Tỉ lệ ở lại chung khoảng 12–21%.

### 4.1 Cây tìm ra gì

| Luật | Mẫu | Lift (học / val / 2009) | Voi lift > 1 (2007–08) |
| --- | ---: | --- | --- |
| 00:45 < giờ ≤ 03:45, cây gỗ tại GPS > 36,7% → **ở lại** | 398 | 5,21 / 2,93 / 4,03 | 5/5 |
| 00:45 < giờ ≤ 03:45, cây gỗ ≤ 36,7% → ở lại | 454 | 3,62 / 2,39 / 3,45 | 6/6 |
| giờ ≤ 00:45, cách nước ≤ 60 m → ở lại | 278 | 3,16 / 2,37 / 2,41 | 2/2 |
| giờ ≤ 00:45, cách nước > 60 m → ở lại | 276 | 2,26 / 1,54 / 2,18 | 2/2 |
| giờ > 03:45, mùa khô, cây gỗ > 37% → ở lại | 2.281 | 1,08 / 1,28 / 1,34 | 11/13 |

Bỏ giờ thì macro-F1 rơi từ 0,63 xuống 0,54; các nhóm khác gần như không đổi. Nghĩa là **cây này chủ yếu học "ban đêm thì ở lại"**. Cột "voi lift > 1" cho 2009 hầu như trống (0/0) vì mỗi voi có quá ít cửa sổ ban đêm trong vùng nước để đánh giá; chỉ có thể nói tổng thể, không nói được "đa số voi".

### 4.2 Số liệu đi sâu

**a. Giờ.** Trong số các cửa sổ voi đang ở vùng nước, tỉ lệ ở lại theo giờ bắt đầu:

| Giờ bắt đầu | 00:00 | 01:30 | 03:00 | 04:30 | 06:00 | 09:00 | 12:00 | 15:00 | 18:00 | 21:00 | 22:30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| học | 37,0% | 49,9% | **59,1%** | 23,0% | 4,6% | 12,4% | 15,2% | 7,3% | 9,2% | 17,4% | 24,2% |
| 2009 | 30,9% | 40,5% | **59,6%** | 19,8% | 5,7% | 10,9% | 11,2% | 4,4% | 11,4% | 17,9% | 22,4% |

Đỉnh đúng lúc 03:00 (≈ 59% ở cả hai giai đoạn), trùng với đỉnh nghỉ của Cây 1. Ban ngày, voi trong vùng nước chủ yếu **ghé qua** (chỉ 4–16% ở lại).

**b. Voi có mặt ở vùng nước vào giờ nào.** Tỉ lệ cửa sổ voi ở trong vùng 200 m quanh nước (mọi cửa sổ):

| Giờ bắt đầu | 00:00 | 03:00 | 06:00 | 09:00 | 12:00 | 13:30 | 15:00 | 18:00 | 21:00 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| học | 15,0% | 11,9% | 12,5% | 21,2% | 33,8% | **36,1%** | 35,8% | 25,7% | 18,9% |
| 2009 | 13,3% | 12,3% | 10,5% | 20,3% | 31,5% | 33,5% | **34,4%** | 23,5% | 17,6% |

Ban ngày 06:00–18:00 khoảng 25–27% cửa sổ nằm trong vùng nước, ban đêm (00:00–06:00) chỉ khoảng 12–13%. Đỉnh ở 13:30–15:00, thấp nhất 03:00–06:00. Tổng thể voi ở trong vùng nước khoảng một phần năm thời gian, khớp với paper (21,6%).

**c. Cây gỗ quanh nơi ở lại ban đêm.** Ban đêm (00:00–06:00), tỉ lệ ở lại theo cây gỗ tại GPS:

| Cây gỗ | 0–25% | 25–37% | 37–50% | > 50% |
| --- | ---: | ---: | ---: | ---: |
| học | 44,4% | 42,3% | 51,7% | **61,5%** (n = 135) |
| 2009 | 38,9% | 39,3% | 46,0% | **58,3%** (n = 24) |

Cùng chiều ở hai giai đoạn: cây gỗ dày thì ở lại nhiều hơn. Nhóm cao nhất rất ít mẫu (n = 24 ở 2009).

**d. Mùa.** Ban đêm: mùa khô 50,1% / mùa mưa 45,2% (học); 36,3% / 50,0% (2009). Ngược chiều giữa hai giai đoạn, **không có pattern theo mùa**. Cây có dùng "mùa khô" trong một luật ban ngày (lift 1,28–1,34 nhưng chỉ ~1,1 ở dữ liệu học), nên coi là yếu.

### 4.3 Diễn giải thành tập tính

1. **Ban đêm, voi đang ở vùng nước thì hay ở lại tại chỗ** (50–60% quanh 01:30–04:30, so với khoảng 12% ban ngày). Cách hiểu hợp lý nhất: đây là **cùng nhịp nghỉ đêm của Cây 1**, xảy ra ở chỗ mà voi tình cờ đang đứng gần nước. Không phải voi đi tới nước để ngủ (Cây 1 cho thấy phần lớn nghỉ xảy ra xa nước).
2. **Ban đêm ít voi có mặt ở vùng nước (khoảng 12%), nhưng số ít đó ở lại lâu**; còn ban ngày nhiều voi ghé (khoảng 25–36%) nhưng chỉ ghé qua rồi đi.
3. **Giữa trưa tới đầu chiều là lúc voi tập trung ở vùng nước nhất** (33–36% cửa sổ), nhưng không phải để đứng yên (chỉ 4–15% ở lại). Khớp với việc về nước nhiều vào buổi sáng ở Cây 2 và với paper (voi ở gần nước nhất vào lúc nóng nhất trong ngày).
4. Cây gỗ dày hơn → ở lại nhiều hơn là xu hướng ở cả hai giai đoạn, nhưng dựa trên rất ít mẫu.

### 4.4 Không nói được

- Không nói "voi uống nước, tắm hay ngủ". Dữ liệu không phân biệt. Cách nói an toàn: "voi ở lại gần nước, ít di chuyển".
- Không nói "ngủ cạnh nước". Chỉ 12% cửa sổ ban đêm ở trong vùng nước.
- "Vùng nước" gồm cả bờ sông dài (hơn 900 đoạn sông OSM). Ở lại trong vùng 200 m quanh một đoạn sông chưa chắc là voi đang ở cạnh mặt nước.
- Không nói pattern đúng cho "đa số voi" (mẫu theo từng voi quá ít). Không rút kết luận theo mùa.
- Không dùng pattern cây gỗ của cây này làm điểm nhấn: mẫu ít và đã có dấu hiệu lệch giữa hai giai đoạn.

### 4.5 Câu có thể nói

> "Ban đêm, nếu voi đang ở gần nước thì nhiều khả năng nó ở lại tại chỗ, tỉ lệ cao nhất khoảng 03:00. Ban ngày voi ghé vùng nước nhiều hơn nhưng chủ yếu chỉ ghé qua. Em xem đây là cùng nhịp nghỉ đêm của cây thứ nhất, GPS không cho biết voi đang uống, tắm hay ngủ."

---

## 5. Ghép bốn cây thành một ngày của voi

Số liệu theo giờ bắt đầu cửa sổ (giờ địa phương). "Nghỉ" từ Cây 1; "về nước" Cây 2 (khoảng cách 0,3–1,5 km); "ở vùng nước" là tỉ lệ cửa sổ voi nằm trong vùng 200 m; "nhanh" từ Cây 3.

| Khoảng giờ | Nghỉ (học) | Về nước trong 3 giờ | Có mặt ở vùng nước | Đi nhanh | Chuyện gì đang xảy ra |
| --- | ---: | ---: | ---: | ---: | --- |
| 22:30–01:30 | 9 → 16% | 14 → 10% | 16 → 15% | — | Voi đang xa nước, giảm dần di chuyển; một phần chuyến rời nước còn tiếp diễn (12% lúc 21–24h) |
| 01:30–04:30 | **30–38%** | 6–11% | 12–13% | — | **Cửa sổ nghỉ đêm**. Hầu như không đi tới nước. Voi đã ở nước thì ở lại (50–59%) |
| 04:30–06:00 | 7% | 25% | 12% | — | Nghỉ kết thúc đột ngột; bắt đầu quay lại nước |
| 06:00–12:00 | 1–4% | 35 → 48% | 12 → 34% | 41–43% | Di chuyển liên tục và chậm; **đỉnh về nước 09:00–10:30**; voi tập trung dần về nguồn nước |
| 12:00–16:30 | 1–4% | 45 → 38% | **31–36%** | 41 → 56% | Nhiều voi nhất ở vùng nước (13:30–15:00), nhưng chỉ ghé qua; chiều muộn đi nhanh dần, bắt đầu rời nước |
| 16:30–21:00 | 1 → 6% | 38 → 16% | 32 → 19% | — | **Rời nước** (57% chuyến rời vào 15:00–21:00); nhịp nghỉ bắt đầu tăng lại |

Có thể kể thành một câu chuyện liền mạch: voi sống theo chu kỳ khoảng một ngày quanh nguồn nước. Sáng quay lại nước, trưa chiều tập trung quanh nước, chiều tối rời nước đi kiếm ăn (đi nhanh hơn lúc đầu), ban đêm ở xa nước và có một đợt nghỉ ngắn khoảng 01:30–04:30, rồi lại quay về nước vào sáng hôm sau.

Đây là câu chuyện ghép từ **bốn cây và số liệu mô tả**; từng mảnh đều có số liệu, nhưng cách ghép thành "một ngày" là diễn giải.

## 6. Mức bằng chứng của từng pattern

| # | Pattern | Cây | Mức bằng chứng | Lý do |
| --- | --- | --- | --- | --- |
| 1 | Nghỉ tập trung 01:30–04:30, rơi mạnh lúc 04:30 | 1 | **Mạnh** | Lift 3,6–4,7 ở cả ba giai đoạn; 14/14 voi và 10/10 voi |
| 2 | Ban ngày voi hầu như luôn di chuyển | 1 | **Mạnh** | 97,6% (2009: 98,4%) cửa sổ ban ngày |
| 3 | Nghỉ không phụ thuộc gần nước hay mùa | 1 | Khá mạnh | Phẳng ở cả hai giai đoạn |
| 4 | Đợt nghỉ ngắn (80% một cửa sổ) | 1 | Vừa | Rất nhất quán, nhưng phụ thuộc lưới 90 phút |
| 5 | Nghỉ nhiều hơn ở nơi cây gỗ dày | 1 (mô tả) | Yếu–vừa | Cùng chiều nhưng không đều ở 2009, nhóm cao có ít mẫu; cây không dùng |
| 6 | Về nước nhiều vào ban ngày/sáng, gần như không về ban đêm | 2 | **Mạnh** | Lift ~2,6–3,0; 14/14 và 11/11 voi |
| 7 | Chu kỳ ~1 ngày: rời nước chiều tối, về nước sáng | 2 | **Mạnh** | 2.913 chuyến; khớp paper |
| 8 | Voi quanh nước trong bán kính ~2 km | 2 | Khá mạnh | Trung vị 1,8–2,2 km |
| 9 | Nóng lên → về nước nhiều hơn | 2 | Yếu–vừa | Bậc thang rồi phẳng; 2009 giảm ở > 35 °C |
| 10 | Mùa mưa về nước nhiều hơn mùa khô | 2 | Yếu | Cùng chiều ở hai giai đoạn nhưng ngược trực giác và chưa giải thích |
| 11 | Cây gỗ dày → đi chậm hơn | 3 | **Mạnh** | Nhất quán cả hai mùa, cả hai giai đoạn; khớp paper |
| 12 | Mùa mưa đi nhanh hơn | 3 | Khá mạnh | 53% / 61% so với 36%; khớp paper |
| 13 | Chiều muộn voi tăng tốc | 3 | Vừa | Cùng chiều ở hai giai đoạn |
| 14 | Mùa khô: nhanh – chậm – nhanh theo thời gian rời nước | 3 | Yếu | Một luật, mức tăng nhỏ |
| 15 | Ban đêm voi ở vùng nước thì ở lại (đỉnh 03:00) | 4 | Vừa | Đỉnh 59% ở cả hai giai đoạn, nhưng ít mẫu và không đánh giá được theo từng voi 2009 |
| 16 | Cây gỗ dày → ở lại nhiều hơn ban đêm | 4 | **Yếu** | Rất ít mẫu (n = 24 ở 2009) |
| 17 | Ở lại theo mùa | 4 | **Không có** | Ngược chiều giữa hai giai đoạn |

Gợi ý khi trình bày: ưu tiên các pattern **Mạnh** (1, 2, 6, 7, 11); nêu pattern **Vừa** kèm cụm "xu hướng"; không đưa pattern **Yếu / Không có** lên slide, trừ khi cố ý dùng làm ví dụ cho giới hạn của phương pháp.

## 7. So với paper gốc

Những chỗ kết quả của chúng tôi **khớp** với Thaker và cộng sự (2019):

| Điều | Paper | Dự án này |
| --- | --- | --- |
| Chu kỳ đi–về nước | Có nhịp tuần hoàn, đỉnh quay lại 10–30 giờ | Chuyến trung vị 19–22 giờ |
| Giờ rời / về nước | Rời khoảng 13:00–14:00, về khoảng 10:00–11:00 (trung bình) | Rời nhiều nhất 15:00–21:00, về nhiều nhất 06:00–15:00 (đỉnh 09:00–12:00) |
| Gần nước nhất lúc nóng nhất | Có | Có mặt ở vùng nước đỉnh lúc 13:30–15:00 |
| Chậm hơn ở nơi cây gỗ dày | Có | Có (Cây 3, mạnh nhất) |
| Nhanh hơn vào mùa mưa | Có (0,42 so với 0,39 km/giờ) | Có (53–61% so với 36%) |
| Nhanh hơn khi nóng | Có (ngược trực giác) | Có, nhỏ |
| Tốc độ trung bình | khoảng 0,4 km/giờ | 0,39–0,44 km/giờ |
| Thời gian ở vùng 200 m quanh nước | 21,6% | khoảng 22% |

Những chỗ **khác hoặc chưa so được**:
- Paper phân tích tốc độ theo từng điểm GPS 30 phút bằng mô hình GAMM; chúng tôi dùng cửa sổ 90 phút và cây quyết định, nên hiệu ứng nhỏ bị làm mờ.
- Paper báo cáo voi ở nước lâu hơn vào mùa khô (3,5 giờ so với 2,6 giờ); Cây 4 không cho thấy pattern theo mùa ổn định.
- Paper không phân tích giấc nghỉ ban đêm; Cây 1 là phần mà dự án này tự thêm vào, không có số liệu đối chiếu trực tiếp từ paper.

## 8. Câu hỏi dễ gặp khi trình bày phần này

**"Pattern này là tìm ra mới hay đã biết?"** Phần lớn khớp với paper (Cây 2, 3) hoặc là kiến thức chung về voi (nghỉ ban đêm). Giá trị của dự án là cho thấy một mô hình đơn giản, đọc được, tự tìm lại các pattern đó từ GPS và kiểm lại trên năm sau.

**"Sao Cây 4 không nói được nhiều như Cây 1?"** Cây 4 chỉ có khoảng 7.000 mẫu học và 3.300 mẫu 2009, mỗi voi vài chục mẫu ban đêm. Số mẫu nhỏ làm bằng chứng yếu hơn; em chỉ trình bày pattern mạnh nhất và nói rõ điều đó.

**"Voi có thực sự ngủ khi 'nghỉ' không?"** Dữ liệu không cho biết. GPS chỉ cho thấy voi ít di chuyển; để biết voi ngủ cần thêm cảm biến vận động hoặc quan sát trực tiếp.

**"Tại sao 34% số đêm không có nghỉ nào?"** Pattern là xu hướng thống kê: trong khung 01:30–04:30, voi ít di chuyển gấp khoảng 4 lần bình thường, nhưng vẫn có những đêm voi đi suốt (đi kiếm ăn, bị quấy rầy, vận chuyển giữa các vùng). Cây không có thông tin để phân biệt những đêm đó.

**"Nhiệt độ có phải nguyên nhân voi về nước không?"** Dữ liệu chỉ cho thấy liên hệ nhỏ và bão hòa trên 30 °C, và nhiệt độ vòng cổ đi cùng giờ trong ngày. Paper cũng cảnh báo nhiệt độ vòng cổ không phải nhiệt độ môi trường thật.

**"Vì sao mùa mưa voi về nước nhiều hơn?"** Chưa giải thích được; mùa là mốc theo lịch, mùa mưa có nhiều nguồn nước nhỏ, và "nguồn nước gần nhất" thay đổi theo mùa. Em ghi lại như một quan sát cần kiểm thêm.
