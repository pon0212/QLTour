import json
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Dict, List

# Cache lưu trữ dữ liệu thời tiết để tránh gọi API quá nhiều lần
_CACHE: Dict[str, Dict] = {}
# Thời gian sống của cache (10 phút)
_CACHE_TTL_SECONDS = 600

# Ánh xạ tên địa danh tiếng Việt sang tên chuẩn tiếng Anh hoặc không dấu tương ứng phục vụ tìm kiếm địa lý
LOCATION_ALIASES = {
    "phú quốc": "Phu Quoc",
    "tp.hcm": "Ho Chi Minh City",
    "tphcm": "Ho Chi Minh City",
    "đà lạt": "Da Lat",
    "đà nẵng": "Da Nang",
    "hà nội": "Hanoi",
    "chợ đêm phú quốc": "Phu Quoc Night Market",
    "sapa": "Sa Pa Lào Cai Việt Nam",
    "sa pa": "Sa Pa Lào Cai Việt Nam",
    "chợ sapa": "Chợ Sa Pa Lào Cai Việt Nam",
    "cho sapa": "Cho Sa Pa Lao Cai Viet Nam",
    "chợ sa pa": "Chợ Sa Pa Lào Cai Việt Nam",
    "nhà thờ đá sapa": "Nhà thờ đá Sa Pa Lào Cai Việt Nam",
    "bản cát cát": "Bản Cát Cát Sa Pa Lào Cai Việt Nam",
    "fansipan": "Fansipan Sa Pa Lào Cai Việt Nam",
    "an giang": "An Giang Việt Nam",
    "chau doc": "Châu Đốc An Giang Việt Nam",
    "châu đốc": "Châu Đốc An Giang Việt Nam",
}

# Gợi ý từ khóa để lọc các kết quả định vị chính xác theo điểm đến mong đợi của tour
DESTINATION_HINTS = {
    "sapa": ["sa pa", "sapa", "lao cai", "lao cai"],
    "sa pa": ["sa pa", "sapa", "lao cai", "lao cai"],
    "phu quoc": ["phu quoc", "kien giang", "an giang"],
    "da lat": ["da lat", "lam dong"],
    "ha long": ["ha long", "quang ninh"],
    "an giang": ["an giang", "chau doc", "long xuyen"],
    "chau doc": ["an giang", "chau doc"],
    "da nang": ["da nang"],
    "hoi an": ["hoi an", "quang nam"],
}


def strip_vietnamese_accents(value):
    """
    Loại bỏ dấu tiếng Việt khỏi chuỗi văn bản đầu vào.
    
    Args:
        value: Chuỗi văn bản tiếng Việt có dấu.
        
    Returns:
        Chuỗi văn bản không dấu (ví dụ: "đà nẵng" -> "da nang").
    """
    text = str(value or "")
    normalized = unicodedata.normalize("NFD", text)
    no_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return no_marks.replace("đ", "d").replace("Đ", "D")


def normalize_vietnam_location_name(text):
    """
    Chuẩn hóa địa danh Việt Nam theo các quy tắc và bổ sung hậu tố quốc gia nếu thiếu.
    
    Args:
        text: Tên địa danh cần chuẩn hóa.
        
    Returns:
        Tên địa danh đã được chuẩn hóa kèm tỉnh thành hoặc quốc gia.
    """
    if not text:
        return ""
    text = str(text).strip()

    lower_text = text.lower()
    common_mappings = {
        "đà lạt": "Đà Lạt, Lâm Đồng, Việt Nam",
        "sapa": "Sa Pa, Lào Cai, Việt Nam",
        "sa pa": "Sa Pa, Lào Cai, Việt Nam",
        "hạ long": "Hạ Long, Quảng Ninh, Việt Nam",
        "phú quốc": "Phú Quốc, Kiên Giang, Việt Nam",
        "đà nẵng": "Đà Nẵng, Việt Nam",
        "hội an": "Hội An, Quảng Nam, Việt Nam",
        "huế": "Huế, Thừa Thiên Huế, Việt Nam",
        "nha trang": "Nha Trang, Khánh Hòa, Việt Nam",
        "cần thơ": "Cần Thơ, Việt Nam"
    }

    if lower_text in common_mappings:
        return common_mappings[lower_text]

    # Bổ sung hậu tố Việt Nam nếu chưa có
    if not (lower_text.endswith("việt nam") or lower_text.endswith("vietnam")):
        text = f"{text}, Việt Nam"

    return text


def normalize_location_key(value):
    """
    Tạo khóa tìm kiếm chuẩn hóa bằng cách bỏ dấu tiếng Việt, viết thường và thu gọn khoảng trắng.
    
    Args:
        value: Chuỗi địa danh gốc.
        
    Returns:
        Khóa tìm kiếm đã chuẩn hóa dưới dạng chữ thường không dấu.
    """
    return " ".join(strip_vietnamese_accents(value).lower().split())


def normalize_location_query(value):
    """
    Chuẩn hóa chuỗi truy vấn địa điểm bằng cách ánh xạ thông qua danh sách bí danh địa danh.
    
    Args:
        value: Tên địa điểm người dùng nhập.
        
    Returns:
        Tên địa điểm sau khi đã xử lý khoảng trắng và thay thế bằng tên chuẩn (bí danh) nếu có.
    """
    text = " ".join(str(value or "").strip().split())
    if not text:
        return ""
    return LOCATION_ALIASES.get(text.lower(), text)


def build_weather_location_query(tour, place_name):
    """
    Xây dựng chuỗi truy vấn vị trí tối ưu để gửi tới API thời tiết dựa trên điểm tham quan và điểm đến của tour.
    
    Args:
        tour: Dictionary chứa thông tin tour (có trường 'diemDen').
        place_name: Tên địa điểm/điểm tham quan cụ thể.
        
    Returns:
        Chuỗi truy vấn vị trí đầy đủ (Ví dụ: "Chợ Đêm, Phú Quốc, Việt Nam").
    """
    place = " ".join(str(place_name or "").strip().split())
    destination = " ".join(str((tour or {}).get("diemDen", "")).strip().split())

    # Loại bỏ các hậu tố quốc gia lặp lại để tránh làm loãng truy vấn
    for suffix in [", Việt Nam", " Việt Nam", ", Vietnam", " Vietnam"]:
        if place.endswith(suffix):
            place = place[:-len(suffix)].strip()
        if destination.endswith(suffix):
            destination = destination[:-len(suffix)].strip()

    if not place:
        return f"{destination}, Việt Nam" if destination else "Việt Nam"
    if destination:
        return f"{place}, {destination}, Việt Nam"
    return f"{place}, Việt Nam"


def build_query_variants(query, expected_destination=""):
    """
    Tạo các biến thể truy vấn khác nhau cho một địa danh nhằm tăng tỷ lệ tìm kiếm chính xác trên các API bản đồ.
    
    Args:
        query: Truy vấn địa điểm gốc.
        expected_destination: Điểm đến dự kiến của tour (ví dụ: "Phú Quốc").
        
    Returns:
        Danh sách các chuỗi truy vấn biến thể đã lọc trùng.
    """
    variants: List[str] = []
    base = " ".join(str(query or "").strip().split())
    expected = " ".join(str(expected_destination or "").strip().split())
    if not base:
        return variants

    def push(v):
        value = " ".join(str(v or "").strip().split())
        if value and value not in variants:
            variants.append(value)

    base_ascii = " ".join(strip_vietnamese_accents(base).split())
    key = normalize_location_key(base)
    expected_key = normalize_location_key(expected)

    # Xử lý các trường hợp đặc biệt thường gặp
    if key in ("cho sapa", "cho sa pa"):
        return [
            "Chợ Sa Pa Lào Cai Việt Nam",
            "Chợ Sa Pa, Lào Cai, Việt Nam",
            "Sa Pa Market, Lao Cai, Vietnam",
            "Sa Pa, Lào Cai, Việt Nam",
            "Sa Pa Lao Cai Vietnam",
        ]
    if key in ("sapa", "sa pa") or expected_key in ("sapa", "sa pa"):
        return [
            "Sa Pa Lào Cai Việt Nam",
            "Sa Pa, Lào Cai, Việt Nam",
            "Sa Pa Lao Cai Vietnam",
            "Lào Cai Việt Nam",
        ]

    push(base)
    push(base_ascii)
    if expected:
        push(f"{base}, {expected}, Việt Nam")
        push(f"{base_ascii}, {strip_vietnamese_accents(expected)}, Vietnam")

    # Bổ sung các biến thể cho các danh lam thắng cảnh đặc thù ở Phú Quốc
    if "sunset sanato" in key:
        if expected:
            push(f"Sunset Sanato {expected}")
            push(f"Bai Truong {expected}")
        push("Phu Quoc")
    if "bai sao" in key and expected:
        push(f"Bai Sao {strip_vietnamese_accents(expected)}")
    if "dinh cau" in key and expected:
        push(f"Dinh Cau {strip_vietnamese_accents(expected)}")
    if expected:
        push(expected)
        push(strip_vietnamese_accents(expected))

    return variants


def is_vietnam_result(item):
    """
    Kiểm tra xem kết quả định vị trả về từ API có thực sự nằm trong lãnh thổ Việt Nam hay không.
    
    Args:
        item: Dictionary chứa thông tin vị trí (latitude, longitude, country_code, name...).
        
    Returns:
        True nếu vị trí thuộc Việt Nam, ngược lại False.
    """
    lat = item.get("latitude")
    lon = item.get("longitude")
    if lat is not None and lon is not None:
        try:
            lat_f = float(lat)
            lon_f = float(lon)
            # Giới hạn tọa độ địa lý hộp biên (bounding box) của Việt Nam
            if not (8.0 <= lat_f <= 24.0 and 102.0 <= lon_f <= 110.0):
                return False
        except (ValueError, TypeError):
            pass

    text_parts = [
        item.get("name", ""),
        item.get("resolved_name", ""),
        item.get("display_name", ""),
        item.get("admin1", ""),
        item.get("admin2", ""),
        item.get("admin3", ""),
        item.get("country", ""),
    ]
    address = item.get("address", {}) or {}
    if isinstance(address, dict):
        text_parts.extend(str(v) for v in address.values())
    text = " ".join(str(x or "") for x in text_parts)
    text_key = normalize_location_key(text)
    country_code = str(item.get("country_code", "") or item.get("countrycode", "")).upper()

    if country_code and country_code != "VN":
        return False
    
    # Loại bỏ các quốc gia lân cận có thể bị trùng tên hoặc kết quả nhầm lẫn
    for blocked in ("philippines", "taiwan", "china", "indonesia", "thailand"):
        if blocked in text_key:
            return False
            
    return (
        country_code == "VN"
        or "viet nam" in text_key
        or "vietnam" in text_key
    )


def fetch_json(url, timeout=10):
    """
    Thực hiện gửi yêu cầu HTTP GET đến URL và phân giải dữ liệu trả về dưới dạng JSON.
    
    Args:
        url: Đường dẫn API cần gọi.
        timeout: Thời gian tối đa chờ phản hồi (giây).
        
    Returns:
        Dữ liệu JSON sau khi giải mã.
    """
    print("[travel_api] geocode url:", url) if "search" in url else print("[travel_api] forecast url:", url)
    request = Request(
        url,
        headers={"User-Agent": "VietnamTravelTkinter/1.0 (student project)"}
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def is_location_match_expected_destination(item, expected_destination):
    """
    Đối chiếu kết quả vị trí tìm được với điểm đến mong đợi để tránh tìm nhầm địa danh trùng tên ở tỉnh thành khác.
    
    Args:
        item: Kết quả vị trí tìm kiếm được từ API bản đồ.
        expected_destination: Tên điểm đến của tour (ví dụ: "Sapa").
        
    Returns:
        True nếu kết quả trùng khớp hoặc có chứa gợi ý điểm đến tương ứng, ngược lại False.
    """
    if not is_vietnam_result(item):
        return False

    expected_key = normalize_location_key(expected_destination)
    if not expected_key:
        return True

    text_parts = [
        item.get("name", ""),
        item.get("resolved_name", ""),
        item.get("display_name", ""),
        item.get("admin1", ""),
        item.get("admin2", ""),
        item.get("admin3", ""),
        item.get("country", ""),
    ]
    address = item.get("address", {}) or {}
    if isinstance(address, dict):
        text_parts.extend(str(v) for v in address.values())
    whole_text = normalize_location_key(" ".join(str(x) for x in text_parts))

    hints = DESTINATION_HINTS.get(expected_key, [])
    if hints:
        has_hint = any(normalize_location_key(h) in whole_text for h in hints)
        if not has_hint:
            return False
        # Xử lý phủ định cho An Giang / Châu Đốc để tránh nhầm với Gia Lai hay các tỉnh miền Trung
        if expected_key in ("an giang", "chau doc"):
            blocked = ("gia lai", "phu my", "binh dinh")
            if any(token in whole_text for token in blocked):
                return False
        return True
    return expected_key in whole_text or "viet nam" in whole_text


def should_prefer_nominatim(query):
    """
    Kiểm tra xem tên địa điểm có chứa các từ khóa đặc trưng của địa danh cụ thể (chợ, nhà thờ, bản, chùa...)
    để ưu tiên tìm kiếm bằng dịch vụ Nominatim của OpenStreetMap (tốt hơn về địa điểm chi tiết) thay vì Open-Meteo.
    
    Args:
        query: Chuỗi địa danh truy vấn.
        
    Returns:
        True nếu nên ưu tiên sử dụng Nominatim trước, ngược lại False.
    """
    key = normalize_location_key(query)
    keywords = [
        "cho", "nha tho", "quang truong", "vuon hoa", "bai", "dinh", "ban",
        "dinh", "lang", "khu", "chua", "pho co", "safari", "beach", "grand world",
        "vinpearl", "fansipan",
    ]
    return any(k in key for k in keywords)


def geocode_with_open_meteo(query, expected_destination=""):
    """
    Thực hiện tìm kiếm tọa độ (Geocoding) bằng API của dịch vụ Open-Meteo.
    
    Args:
        query: Từ khóa truy vấn địa điểm.
        expected_destination: Tên điểm đến của tour để kiểm tra giới hạn kết quả.
        
    Returns:
        Dictionary chứa trạng thái thành công, thông tin tọa độ và mô tả lỗi nếu có.
    """
    params = urlencode({
        "name": query,
        "count": 10,
        "language": "vi",
        "format": "json",
    })
    url = f"https://geocoding-api.open-meteo.com/v1/search?{params}"
    try:
        data = fetch_json(url, timeout=10)
        results = data.get("results") or []
    except HTTPError as exc:
        return {"ok": False, "error": f"Lỗi HTTP {exc.code} từ Open-Meteo API."}
    except (URLError, OSError, TimeoutError) as exc:
        err_str = str(exc).lower()
        if "timed out" in err_str or "timeout" in err_str:
            return {"ok": False, "error": "API timeout: Thời gian kết nối quá hạn."}
        return {"ok": False, "error": "Mất mạng: Không thể kết nối tới máy chủ Geocoding (Open-Meteo)."}
    except Exception as exc:
        return {"ok": False, "error": f"Lỗi Open-Meteo: {exc}"}

    candidates = []
    for row in results:
        item = {
            "name": row.get("name", ""),
            "admin1": row.get("admin1", ""),
            "admin2": row.get("admin2", ""),
            "admin3": row.get("admin3", ""),
            "country": row.get("country", ""),
            "country_code": str(row.get("country_code", "")).upper(),
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
        }
        if not is_vietnam_result(item):
            continue
        if not is_location_match_expected_destination(item, expected_destination):
            continue
        candidates.append(item)

    if not candidates:
        return {"ok": False, "error": "Open-Meteo không tìm thấy vị trí phù hợp."}

    selected = None
    for item in candidates:
        if item.get("country_code") == "VN":
            selected = item
            break
    if selected is None:
        selected = candidates[0]

    print("[travel_api] provider:", "Open-Meteo Geocoding")
    print("[travel_api] geocode selected:", selected)
    return {
        "ok": True,
        "query": query,
        "matched_query": query,
        "provider": "Open-Meteo Geocoding",
        "resolved_name": selected.get("name", ""),
        "admin1": selected.get("admin1", ""),
        "admin2": selected.get("admin2", ""),
        "admin3": selected.get("admin3", ""),
        "country": selected.get("country", ""),
        "country_code": selected.get("country_code", ""),
        "latitude": selected.get("latitude"),
        "longitude": selected.get("longitude"),
    }


def geocode_with_nominatim(query, expected_destination=""):
    """
    Thực hiện tìm kiếm tọa độ (Geocoding) bằng API của dịch vụ Nominatim (OpenStreetMap).
    
    Args:
        query: Từ khóa truy vấn địa điểm.
        expected_destination: Tên điểm đến của tour để lọc kết quả.
        
    Returns:
        Dictionary chứa trạng thái thành công, thông tin tọa độ chi tiết và mô tả lỗi nếu có.
    """
    query_key = normalize_location_key(query)
    q_value = query
    if "viet nam" not in query_key and "vietnam" not in query_key:
        q_value = f"{query}, Việt Nam"
    params = urlencode({
        "q": q_value,
        "format": "json",
        "addressdetails": 1,
        "limit": 10,
        "countrycodes": "vn",
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    request = Request(
        url,
        headers={
            "User-Agent": "VietnamTravelTkinter/1.0 (student project)",
            "Accept-Language": "vi",
        },
    )
    try:
        print("[travel_api] geocode url:", url)
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return {"ok": False, "error": f"Lỗi HTTP {exc.code} từ Nominatim API."}
    except (URLError, OSError, TimeoutError) as exc:
        err_str = str(exc).lower()
        if "timed out" in err_str or "timeout" in err_str:
            return {"ok": False, "error": "API timeout: Thời gian kết nối quá hạn."}
        return {"ok": False, "error": "Mất mạng: Không thể kết nối tới máy chủ Geocoding (Nominatim)."}
    except Exception as exc:
        return {"ok": False, "error": f"Lỗi Nominatim: {exc}"}

    candidates = []
    for row in data or []:
        address = row.get("address", {}) or {}
        admin1 = (
            address.get("state")
            or address.get("province")
            or address.get("city")
            or address.get("county")
            or address.get("town")
            or address.get("village")
            or ""
        )
        item = {
            "display_name": row.get("display_name", ""),
            "resolved_name": row.get("display_name", ""),
            "admin1": admin1,
            "country": address.get("country", "Việt Nam"),
            "country_code": str(address.get("country_code", "vn")).upper(),
            "latitude": float(row.get("lat")) if row.get("lat") is not None else None,
            "longitude": float(row.get("lon")) if row.get("lon") is not None else None,
            "address": address,
        }
        if not is_vietnam_result(item):
            continue
        if not is_location_match_expected_destination(item, expected_destination):
            continue
        candidates.append(item)

    if not candidates:
        return {"ok": False, "error": "Nominatim không tìm thấy vị trí phù hợp."}

    selected = candidates[0]
    print("[travel_api] provider:", "Nominatim")
    print("[travel_api] geocode selected:", selected)
    return {
        "ok": True,
        "query": query,
        "matched_query": query,
        "provider": "Nominatim",
        "resolved_name": selected.get("resolved_name", ""),
        "display_name": selected.get("display_name", ""),
        "address": selected.get("address", ""),
        "admin1": selected.get("admin1", ""),
        "admin2": "",
        "admin3": "",
        "country": selected.get("country", "Việt Nam"),
        "country_code": selected.get("country_code", "VN"),
        "latitude": selected.get("latitude"),
        "longitude": selected.get("longitude"),
    }


def extract_google_address_components(address_components):
    """
    Trích xuất các cấp hành chính (quốc gia, tỉnh thành, quận huyện, xã phường) từ danh sách địa chỉ trả về của Google Maps Geocoding API.
    
    Args:
        address_components: Danh sách thành phần địa chỉ của Google API.
        
    Returns:
        Tuple chứa: (quốc gia, mã quốc gia, cấp hành chính 1, cấp hành chính 2, cấp hành chính 3).
    """
    country = "Việt Nam"
    country_code = "VN"
    admin1 = ""
    admin2 = ""
    admin3 = ""

    for comp in address_components:
        types = comp.get("types", [])
        if "country" in types:
            country = comp.get("long_name", "")
            country_code = comp.get("short_name", "").upper()
        elif "administrative_area_level_1" in types:
            admin1 = comp.get("long_name", "")
        elif "administrative_area_level_2" in types:
            admin2 = comp.get("long_name", "")
        elif "administrative_area_level_3" in types:
            admin3 = comp.get("long_name", "")

    return country, country_code, admin1, admin2, admin3


def geocode_with_google_maps(query, expected_destination="", api_key=""):
    """
    Tìm kiếm tọa độ bằng dịch vụ Google Maps Geocoding API (đòi hỏi API key có hiệu lực).
    
    Args:
        query: Từ khóa truy vấn địa điểm cần geocode.
        expected_destination: Điểm đến mong đợi để lọc kết quả.
        api_key: Khóa kích hoạt Google Maps API.
        
    Returns:
        Dictionary chứa kết quả định dạng chuẩn hoặc báo lỗi chi tiết.
    """
    params = urlencode({
        "address": query,
        "key": api_key,
        "language": "vi"
    })
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"

    try:
        req = Request(
            url,
            headers={"User-Agent": "VietnamTravelTkinter/1.0 (student project)"}
        )
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        status = data.get("status")
        if status == "OK":
            results = data.get("results", [])
            if not results:
                return {"ok": False, "error": "Google Maps không trả về kết quả."}

            candidates = []
            for row in results:
                geo = row.get("geometry", {}).get("location", {})
                lat = geo.get("lat")
                lng = geo.get("lng")
                addr_comps = row.get("address_components", [])
                country, country_code, admin1, admin2, admin3 = extract_google_address_components(addr_comps)

                item = {
                    "display_name": row.get("formatted_address", ""),
                    "resolved_name": row.get("formatted_address", ""),
                    "admin1": admin1,
                    "admin2": admin2,
                    "admin3": admin3,
                    "country": country,
                    "country_code": country_code,
                    "latitude": lat,
                    "longitude": lng,
                    "address": row.get("formatted_address", "")
                }

                if not is_vietnam_result(item):
                    continue
                if not is_location_match_expected_destination(item, expected_destination):
                    continue
                candidates.append(item)

            if not candidates:
                return {"ok": False, "error": "Không tìm thấy địa điểm tương ứng."}

            selected = candidates[0]
            return {
                "ok": True,
                "query": query,
                "matched_query": query,
                "provider": "Google Maps",
                "resolved_name": selected.get("resolved_name", ""),
                "display_name": selected.get("display_name", ""),
                "address": selected.get("address", ""),
                "admin1": selected.get("admin1", ""),
                "admin2": selected.get("admin2", ""),
                "admin3": selected.get("admin3", ""),
                "country": selected.get("country", "Việt Nam"),
                "country_code": selected.get("country_code", "VN"),
                "latitude": selected.get("latitude"),
                "longitude": selected.get("longitude"),
            }
        elif status == "ZERO_RESULTS":
            return {"ok": False, "error": "Không tìm thấy địa điểm tương ứng."}
        elif status == "REQUEST_DENIED":
            return {"ok": False, "error": "Lỗi xác thực API Key Google Maps hoặc yêu cầu bị từ chối."}
        elif status == "OVER_QUERY_LIMIT":
            return {"ok": False, "error": "Hết hạn ngạch (quota) cuộc gọi Google Maps API."}
        else:
            return {"ok": False, "error": f"Lỗi Google Maps API status: {status}"}

    except HTTPError as exc:
        if exc.code == 403:
            return {"ok": False, "error": "Lỗi xác thực API Key Google Maps."}
        return {"ok": False, "error": f"Lỗi HTTP {exc.code} từ Google Maps API."}
    except URLError:
        return {"ok": False, "error": "Không thể kết nối Internet. Vui lòng kiểm tra kết nối mạng."}
    except TimeoutError:
        return {"ok": False, "error": "Thời gian kết nối quá hạn. Vui lòng thử lại sau."}
    except Exception as exc:
        return {"ok": False, "error": f"Lỗi không xác định khi kết nối Google Maps: {str(exc)}"}


def geocode_location(location_name, expected_destination=""):
    """
    Định vị địa điểm từ tên văn bản bằng cơ chế gọi Google Maps API trước (nếu có key môi trường),
    hoặc tự động chuyển sang cơ chế Fallback (gọi Nominatim và Open-Meteo luân phiên tùy thuộc đặc thù từ khóa).
    
    Args:
        location_name: Tên địa điểm cần tìm kiếm tọa độ.
        expected_destination: Điểm đến mong đợi của tour.
        
    Returns:
        Dictionary chứa tọa độ (latitude, longitude) và thông tin vị trí đã được giải mã hoặc lỗi chi tiết.
    """
    location_name = normalize_vietnam_location_name(location_name)
    expected_destination = normalize_vietnam_location_name(expected_destination)

    query = normalize_location_query(location_name)
    if not query:
        return {
            "ok": False,
            "error": "Không thể xác định vị trí chính xác của điểm đến. Vui lòng thử lại sau."
        }

    variants = build_query_variants(query, expected_destination)
    expected_key = normalize_location_key(expected_destination)

    # 1. Thử nghiệm với Google Maps Geocoding nếu được cung cấp key trong biến môi trường
    import os
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if api_key:
        print("[travel_api] Sử dụng Google Maps Geocoding API...")
        for variant in variants:
            result = geocode_with_google_maps(variant, expected_destination, api_key)
            if result.get("ok"):
                result["matched_query"] = variant
                return result
            else:
                err_msg = result.get("error", "")
                if "Lỗi xác thực" in err_msg or "API Key" in err_msg:
                    return {"ok": False, "error": f"API key sai: {err_msg}"}
                print(f"[travel_api] Google Maps thất bại: {err_msg}")

    # 2. Cơ chế Fallback miễn phí khi không có Google Maps API key
    print("[travel_api] Đang sử dụng cơ chế fallback...")
    prefer_nominatim_first = should_prefer_nominatim(query) or expected_key in ("an giang", "chau doc")

    fallback_res = None
    if prefer_nominatim_first:
        for variant in variants:
            result = geocode_with_nominatim(variant, expected_destination)
            if result.get("ok"):
                fallback_res = result
                break
        if not fallback_res:
            for variant in variants:
                result = geocode_with_open_meteo(variant, expected_destination)
                if result.get("ok"):
                    fallback_res = result
                    break
    else:
        for variant in variants:
            result = geocode_with_open_meteo(variant, expected_destination)
            if result.get("ok"):
                fallback_res = result
                break
        if not fallback_res:
            for variant in variants:
                result = geocode_with_nominatim(variant, expected_destination)
                if result.get("ok"):
                    fallback_res = result
                    break

    if fallback_res and fallback_res.get("ok"):
        provider = fallback_res.get("provider", "")
        if "(Fallback)" not in provider:
            fallback_res["provider"] = f"{provider} (Fallback)"
        return fallback_res

    return {
        "ok": False,
        "error": "Không thể xác định vị trí chính xác của điểm đến. Vui lòng thử lại sau."
    }


def weather_code_to_vietnamese(code):
    """
    Chuyển đổi mã trạng thái thời tiết số (WMO code) từ Open-Meteo API thành mô tả tiếng Việt thân thiện.
    
    Args:
        code: Mã thời tiết dạng số hoặc chuỗi.
        
    Returns:
        Chuỗi mô tả thời tiết tiếng Việt (ví dụ: "Trời quang", "Mưa rào", "Dông"...).
    """
    try:
        code_val = int(code)
    except (TypeError, ValueError):
        return "Không xác định"

    if code_val == 0:
        return "Trời quang"
    elif code_val in (1, 2, 3):
        return "Ít mây / Có mây"
    elif code_val in (45, 48):
        return "Sương mù"
    elif code_val in (51, 53, 55):
        return "Mưa phùn"
    elif code_val in (61, 63, 65):
        return "Mưa"
    elif code_val in (80, 81, 82):
        return "Mưa rào"
    elif code_val in (95, 96, 99):
        return "Dông"
    else:
        return "Không xác định"


def fetch_current_weather(latitude, longitude):
    """
    Lấy dữ liệu thời tiết thực tế từ Open-Meteo Forecast API dựa vào kinh độ vĩ độ.
    
    Args:
        latitude: Vĩ độ của điểm cần lấy thời tiết.
        longitude: Kinh độ của điểm cần lấy thời tiết.
        
    Returns:
        Dictionary chứa thông tin thời tiết (nhiệt độ, mã thời tiết, văn bản mô tả, sức gió...) hoặc thông báo lỗi.
    """
    params = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "timezone": "auto",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    try:
        data = fetch_json(url, timeout=10)
    except HTTPError as exc:
        return {"ok": False, "error": f"Lỗi HTTP {exc.code} từ máy chủ thời tiết (Open-Meteo)."}
    except (URLError, OSError, TimeoutError) as exc:
        err_str = str(exc).lower()
        if "timed out" in err_str or "timeout" in err_str:
            return {"ok": False, "error": "API timeout: Thời gian kết nối quá hạn (Weather API)."}
        return {"ok": False, "error": "Mất mạng: Không thể kết nối tới máy chủ thời tiết."}
    except Exception as exc:
        return {"ok": False, "error": f"Lỗi thời tiết: {exc}"}

    current = data.get("current") or {}
    print("[travel_api] forecast current:", current)
    temperature = current.get("temperature_2m")
    weather_code = current.get("weather_code")
    wind_speed = current.get("wind_speed_10m")
    time_value = current.get("time")

    if not current or temperature is None:
        return {
            "ok": False,
            "error": "Đã lấy được tọa độ từ API nhưng Forecast API không trả nhiệt độ."
        }
    return {
        "ok": True,
        "temperature": temperature,
        "weather_code": weather_code,
        "weather_text": weather_code_to_vietnamese(weather_code),
        "wind_speed": wind_speed,
        "time": time_value,
    }


def get_location_weather(location_name, expected_destination="", timeout=20):
    """
    Hàm giao tiếp chính bên ngoài: Truy vấn toàn bộ thông tin địa lý và thời tiết hiện tại của một địa điểm.
    Hỗ trợ cơ chế lưu cache kết quả trong vòng 10 phút để tối ưu hóa hiệu năng và hạn chế chạm giới hạn API.
    
    Args:
        location_name: Tên địa điểm/điểm du lịch cần truy vấn.
        expected_destination: Điểm đến mong đợi để kiểm soát độ chính xác của kết quả.
        timeout: Không sử dụng, giữ lại vì tương thích ngược.
        
    Returns:
        Dictionary chứa đầy đủ thông tin địa điểm (tọa độ, địa chỉ chuẩn hóa) và thời tiết (nhiệt độ, bầu trời, gió...).
    """
    del timeout
    normalized_query = normalize_location_query(location_name)
    cache_key = f"{normalize_location_key(normalized_query)}|{normalize_location_key(expected_destination)}"
    now = time.time()
    cached = _CACHE.get(cache_key)
    if cached and now - cached.get("cached_at", 0) <= _CACHE_TTL_SECONDS:
        result = dict(cached["data"])
        result["from_cache"] = True
        return result

    geo = geocode_location(normalized_query, expected_destination=expected_destination)
    if not geo.get("ok"):
        return {"ok": False, "query": location_name, "error": geo.get("error", "Không thể xác định vị trí chính xác của điểm đến. Vui lòng thử lại sau.")}

    lat = geo.get("latitude")
    lon = geo.get("longitude")
    if lat is None or lon is None:
        return {"ok": False, "query": location_name, "error": "Không thể xác định vị trí chính xác của điểm đến. Vui lòng thử lại sau."}
    if not is_vietnam_result(geo) or not is_location_match_expected_destination(geo, expected_destination):
        return {
            "ok": False,
            "query": location_name,
            "matched_query": geo.get("matched_query", ""),
            "provider": geo.get("provider", ""),
            "resolved_name": geo.get("resolved_name", ""),
            "country": geo.get("country", ""),
            "country_code": geo.get("country_code", ""),
            "latitude": lat,
            "longitude": lon,
            "error": "Không thể xác định vị trí chính xác của điểm đến. Vui lòng thử lại sau."
        }

    weather = fetch_current_weather(lat, lon)
    if not weather.get("ok"):
        return {
            "ok": False,
            "query": location_name,
            "matched_query": geo.get("matched_query", ""),
            "provider": geo.get("provider", ""),
            "resolved_name": geo.get("resolved_name", ""),
            "admin1": geo.get("admin1", ""),
            "admin2": geo.get("admin2", ""),
            "admin3": geo.get("admin3", ""),
            "country": geo.get("country", ""),
            "country_code": geo.get("country_code", ""),
            "latitude": lat,
            "longitude": lon,
            "error": weather.get("error", "Không thể tải dữ liệu thời tiết hiện tại. Vui lòng kiểm tra kết nối mạng hoặc thử lại sau.")
        }

    result = {
        "ok": True,
        "query": normalized_query,
        "matched_query": geo.get("matched_query", ""),
        "provider": geo.get("provider", ""),
        "resolved_name": geo.get("resolved_name", ""),
        "display_name": geo.get("display_name", ""),
        "address": geo.get("address", ""),
        "admin1": geo.get("admin1", ""),
        "admin2": geo.get("admin2", ""),
        "admin3": geo.get("admin3", ""),
        "country": geo.get("country", ""),
        "country_code": geo.get("country_code", ""),
        "latitude": lat,
        "longitude": lon,
        "temperature": weather.get("temperature"),
        "weather_code": weather.get("weather_code"),
        "weather_text": weather.get("weather_text"),
        "wind_speed": weather.get("wind_speed"),
        "time": weather.get("time"),
        "source": f"{geo.get('provider', 'Geocoding')} + Open-Meteo Forecast",
        "from_cache": False,
    }
    if result.get("temperature") is None:
        return {
            "ok": False,
            "query": normalized_query,
            "error": "Đã lấy được tọa độ từ API nhưng Forecast API không trả nhiệt độ."
        }

    _CACHE[cache_key] = {"cached_at": now, "data": result}
    return result


def clear_cache():
    """
    Xóa toàn bộ dữ liệu thời tiết trong bộ nhớ cache.
    """
    _CACHE.clear()


def get_cache_stats():
    """
    Thống kê trạng thái của bộ nhớ cache thời tiết bao gồm số lượng cache còn hiệu lực và hết hạn.
    
    Returns:
        Dictionary chứa: total (tổng số cache), valid (số cache còn hạn), expired (số cache đã hết hạn).
    """
    now = time.time()
    valid_count = 0
    expired_count = 0
    for value in _CACHE.values():
        cache_time = value.get("cached_at", 0)
        if now - cache_time <= _CACHE_TTL_SECONDS:
            valid_count += 1
        else:
            expired_count += 1
    return {"total": len(_CACHE), "valid": valid_count, "expired": expired_count}


def fetch_weather_by_coordinates(lat, lon):
    """
    Lấy thông tin thời tiết trực tiếp thông qua vĩ độ (latitude) và kinh độ (longitude).
    
    Args:
        lat: Vĩ độ.
        lon: Kinh độ.
        
    Returns:
        Kết quả thời tiết tương tự fetch_current_weather hoặc báo lỗi nếu tọa độ không hợp lệ.
    """
    try:
        lat_val = float(lat)
        lon_val = float(lon)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "error": "Tọa độ không hợp lệ."
        }
    return fetch_current_weather(lat_val, lon_val)


def build_google_maps_url(lat, lon, location_name=""):
    """
    Tạo chuỗi liên kết (URL) Google Maps để hiển thị vị trí trên trình duyệt dựa trên tọa độ.
    
    Args:
        lat: Vĩ độ.
        lon: Kinh độ.
        location_name: Không dùng, giữ lại vì tương thích ngược.
        
    Returns:
        Đường dẫn URL Google Maps hoặc chuỗi rỗng nếu thiếu tọa độ.
    """
    if lat is None or lon is None:
        return ""
    return f"https://www.google.com/maps?q={lat},{lon}"
