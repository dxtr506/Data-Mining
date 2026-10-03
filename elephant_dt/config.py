"""Cấu hình chung cho pipeline: đường dẫn, hằng số lấy từ paper Thaker et al. (2019)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent          # elephant_dt/
DATA_ROOT = ROOT.parent                         # Data_Mining/
ELEMOVE_DATA = DATA_ROOT / "elemove" / "data"

GPS_CSV = DATA_ROOT / "ThermochronTracking Elephants Kruger 2007.csv"
KRUGER_SHP = ELEMOVE_DATA / "kruger_clip" / "kruger_clip.shp"
RIVERS_SHP = ELEMOVE_DATA / "river_crop" / "kruger_rivers_cropped.shp"
WATERHOLES_SHP = ELEMOVE_DATA / "waterholes" / "waterpoints_zambatis_2011.shp"
LANDSAT_TIF = ELEMOVE_DATA / "kruger_temp_200m.tif"
# Độ che phủ cây (%). File Bucini do người dùng cung cấp có ưu tiên.
# Mặc định là bề mặt woody nội suy trong kho tác giả, KHÔNG xác nhận là raster Bucini gốc.
WOODY_BUCINI = ELEMOVE_DATA / "treecover.tif"
WOODY_AUTHOR = ROOT / "data" / "woody_author_interpolated.tif"
WOODY_TIF = WOODY_BUCINI if WOODY_BUCINI.exists() else WOODY_AUTHOR
WOODY_METADATA = ROOT / "data" / "woody_source.json"
WOODY_SMOOTH_M = 150        # bán kính cửa sổ vuông: bề rộng ~300 m

OUT = ROOT / "outputs"
WEB_DATA = ROOT / "web" / "data"

UTM = "EPSG:32736"          # WGS84 / UTM 36S, CRS paper dùng để tính khoảng cách
LOCAL_UTC_OFFSET_H = 2      # timestamp Movebank là UTC; Nam Phi = UTC+2

# Mùa mưa: 13/10 → 21/04 (gồm cả hai đầu). Không có số liệu mưa gốc của paper; mốc này
# được chọn để số điểm mùa khô/mưa khớp con số paper báo cáo (138.764 / 144.973).
WET_START = (10, 13)
WET_END = (4, 22)           # ngày đầu tiên của mùa khô

WATER_BUFFER_M = 200        # vùng "ở nguồn nước"
MAX_SEGMENT_H = 120         # bỏ chuyến dài hơn 120 h
MIN_SEGMENT_POINTS = 25     # 25 điểm = 12,5 h, yêu cầu tối thiểu của bước phân đoạn
MAX_GAP_H = 6.0             # chuyến có khoảng mất tín hiệu > 6 h bị loại (khớp số chuyến paper nhất)
MIN_PHASE_POINTS = 5        # mỗi pha hành vi dài ít nhất 5 điểm (2,5 h)
MAX_PHASES = 5              # tối đa 4 lần đổi trạng thái
PHASE_NET_M = 500           # pha đổi khoảng cách tới nước ≥ 500 m mới tính là rời xa / tiến về

STATE_NAMES = {0: "Đi xa nước", 1: "Quanh quẩn", 2: "Về nước"}
AT_WATER = 3                # mã cho điểm ở trong vùng 200 m quanh nguồn nước
OUTSIDE = -1                # điểm không thuộc chuyến hợp lệ

# Chia train / test theo thời gian (giờ địa phương): học 08/2007–12/2008, dự đoán năm 2009.
SPLIT_DATE = "2009-01-01"

def utf8_stdout():
    """Console Windows mặc định không in được tiếng Việt."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
