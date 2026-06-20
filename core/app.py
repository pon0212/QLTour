from __future__ import annotations

# FILE GOM: Toan bo logic core duoc gom ve day de giam so luong file.


# ===== BEGIN core/activity_log.py =====

import json
import os
from datetime import datetime


def _resolve_log_file(datastore=None, log_file: str | None = None) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_resolve_log_file` ( resolve log file).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        log_file: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if log_file:
        return log_file
    if datastore is not None and getattr(datastore, "path", None):
        return os.path.join(os.path.dirname(datastore.path), "activity_logs.json")
    return os.path.join(os.getcwd(), "activity_logs.json")


def _load_entries(path: str) -> list[dict]:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_load_entries` ( load entries).
    Tham số:
        path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

    return data if isinstance(data, list) else []


def write_activity_log(
    action: str,
    actor: str,
    role: str,
    status: str,
    detail: str = "",
    datastore=None,
    log_file: str | None = None,
) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `write_activity_log` (write activity log).
    Tham số:
        action: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        detail: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        log_file: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    path = _resolve_log_file(datastore=datastore, log_file=log_file)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    entries = _load_entries(path)
    entries.append(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "actor": actor,
            "role": role,
            "action": action,
            "status": status,
            "detail": detail,
        }
    )

    with open(path, "w", encoding="utf-8") as file:
        json.dump(entries[-1000:], file, ensure_ascii=False, indent=2)

# ===== BEGIN core/validation.py =====

import re

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]{3,30}")
PHONE_PATTERN = re.compile(r"0\d{9}")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
VIETNAM_MOBILE_PREFIXES = {
    "032", "033", "034", "035", "036", "037", "038", "039",
    "052", "055", "056", "058", "059",
    "070", "076", "077", "078", "079",
    "081", "082", "083", "084", "085", "086", "087", "088", "089",
    "090", "091", "092", "093", "094", "096", "097", "098", "099",
}


def normalize_username(username: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_username` (normalize username).
    Tham số:
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return str(username or "").strip()


def normalize_fullname(fullname: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_fullname` (normalize fullname).
    Tham số:
        fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return " ".join(str(fullname or "").strip().split())


def normalize_phone(phone: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_phone` (normalize phone).
    Tham số:
        phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return str(phone or "").strip()


def is_valid_username(username: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_username` (is valid username).
    Tham số:
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return bool(USERNAME_PATTERN.fullmatch(normalize_username(username)))


def is_valid_password(password: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_password` (is valid password).
    Tham số:
        password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return len(str(password or "").strip()) >= 3


def is_valid_fullname(fullname: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_fullname` (is valid fullname).
    Tham số:
        fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return len(normalize_fullname(fullname)) >= 3


def is_valid_phone(phone: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_phone` (is valid phone).
    Tham số:
        phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    value = normalize_phone(phone)
    if not value:
        return True
    if not PHONE_PATTERN.fullmatch(value):
        return False
    return value[:3] in VIETNAM_MOBILE_PREFIXES


def is_valid_email(email: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_email` (is valid email).
    Tham số:
        email: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return bool(EMAIL_PATTERN.fullmatch(str(email or "").strip()))

# ===== BEGIN core/text_utils.py =====

import re

_SPACE_RE = re.compile(r"\s+")


def normalize_spaces(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return _SPACE_RE.sub(" ", text)


def normalize_title_case(value: str | None) -> str:
    text = normalize_spaces(value)
    if not text:
        return ""
    return " ".join(part[:1].upper() + part[1:].lower() for part in text.split(" "))


def normalize_tour_name(value: str | None) -> str:
    text = normalize_spaces(value)
    if not text:
        return ""
    normalized_tokens = []
    for token in text.split(" "):
        if not token:
            continue
        if any(ch.isdigit() for ch in token):
            normalized_tokens.append(token.upper())
        else:
            normalized_tokens.append(token[:1].upper() + token[1:].lower())
    return " ".join(normalized_tokens)


def normalize_code(value: str | None) -> str:
    if value is None:
        return ""
    text = _SPACE_RE.sub("", str(value))
    return text.upper().strip()


def normalize_email(value: str | None) -> str:
    if value is None:
        return ""
    text = _SPACE_RE.sub("", str(value))
    return text.lower().strip()

# ===== BEGIN core/tour_rules.py =====

from datetime import date, datetime, timedelta
import re



TOUR_STATUS_NOT_OPEN = "Sắp mở bán"
TOUR_STATUS_OPEN = "Đang mở bán"
TOUR_STATUS_FULL = "Đã đủ khách"
TOUR_STATUS_STARTED = "Đang diễn ra"
TOUR_STATUS_COMPLETED = "Đã kết thúc"
TOUR_STATUS_CANCELLED = "Đã hủy"

# Giữ alias để tương thích code cũ, nhưng không phát sinh trạng thái ngoài 6 trạng thái chuẩn.
TOUR_STATUS_HOLD = TOUR_STATUS_OPEN
TOUR_STATUS_INACTIVE = TOUR_STATUS_CANCELLED
TOUR_STATUS_HIDDEN = TOUR_STATUS_CANCELLED

TOUR_STATUS_CHOICES = [
    TOUR_STATUS_NOT_OPEN,
    TOUR_STATUS_OPEN,
    TOUR_STATUS_FULL,
    TOUR_STATUS_STARTED,
    TOUR_STATUS_COMPLETED,
    TOUR_STATUS_CANCELLED,
]

BOOKABLE_TOUR_STATUSES = {TOUR_STATUS_OPEN}
TERMINAL_TOUR_STATUSES = {
    TOUR_STATUS_COMPLETED,
    TOUR_STATUS_CANCELLED,
}
LOCKED_MANUAL_TOUR_STATUSES = {
    TOUR_STATUS_CANCELLED,
}
ACTIVE_TOUR_STATUSES_FOR_GUIDE = {
    TOUR_STATUS_NOT_OPEN,
    TOUR_STATUS_OPEN,
    TOUR_STATUS_FULL,
    TOUR_STATUS_STARTED,
}

_LEGACY_STATUS_MAP = {
    "Sắp mở bán": TOUR_STATUS_NOT_OPEN,
    "Đang mở bán": TOUR_STATUS_OPEN,
    "Đã đủ khách": TOUR_STATUS_FULL,
    "Đang diễn ra": TOUR_STATUS_STARTED,
    "Đã kết thúc": TOUR_STATUS_COMPLETED,
    "Đã hủy": TOUR_STATUS_CANCELLED,
    "Chưa mở": TOUR_STATUS_NOT_OPEN,
    "Đang mở đăng ký": TOUR_STATUS_OPEN,
    "Mở bán": TOUR_STATUS_OPEN,
    "Giữ chỗ": TOUR_STATUS_OPEN,
    "Đã chốt đoàn": TOUR_STATUS_FULL,
    "Đã chốt": TOUR_STATUS_FULL,
    "Đủ chỗ": TOUR_STATUS_FULL,
    "Chờ khởi hành": TOUR_STATUS_OPEN,
    "Đang đi": TOUR_STATUS_STARTED,
    "Đã khởi hành": TOUR_STATUS_STARTED,
    "Hoàn thành": TOUR_STATUS_COMPLETED,
    "Hoàn tất": TOUR_STATUS_COMPLETED,
    "Tạm hoãn": TOUR_STATUS_CANCELLED,
    "Ngừng hoạt động": TOUR_STATUS_CANCELLED,
    "Đã ẩn": TOUR_STATUS_CANCELLED,
}

_SO_NGAY_RE = re.compile(r"(\d+)")


def parse_ddmmyyyy(value: str | None) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def format_ddmmyyyy(value: date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%d/%m/%Y")


def normalize_tour_status(value: str | None, default: str = TOUR_STATUS_NOT_OPEN) -> str:
    text = normalize_spaces(value)
    if not text:
        return default
    if text in _LEGACY_STATUS_MAP:
        return _LEGACY_STATUS_MAP[text]
    if text in _LEGACY_STATUS_MAP.values():
        return text
    key_ascii = _normalize_status_key(text)
    if key_ascii in {"chua mo", "sap mo ban", "nhap", "draft"}:
        return TOUR_STATUS_NOT_OPEN
    if key_ascii in {"dang mo dang ky", "dang mo ban", "mo ban", "cho khoi hanh"}:
        return TOUR_STATUS_OPEN
    if key_ascii in {"giu cho"}:
        return TOUR_STATUS_OPEN
    if key_ascii in {"da chot doan", "da chot", "du cho"}:
        return TOUR_STATUS_FULL
    if key_ascii in {"dang di", "da khoi hanh", "dang dien ra"}:
        return TOUR_STATUS_STARTED
    if key_ascii in {"hoan tat", "hoan thanh", "da ket thuc"}:
        return TOUR_STATUS_COMPLETED
    if key_ascii in {"da huy", "cancelled"}:
        return TOUR_STATUS_CANCELLED
    if key_ascii in {"tam hoan", "paused", "ngung hoat dong", "da an", "hidden"}:
        return TOUR_STATUS_CANCELLED
    return default


def sync_ghi_chu_dieu_hanh(tour: dict):
    """
    Đồng bộ ghi chú điều hành phù hợp với trạng thái thực tế của tour.
    """
    if not isinstance(tour, dict):
        return
    status = normalize_tour_status(tour.get("trangThai", ""))
    note = str(tour.get("ghiChuDieuHanh", "")).strip()

    completed_note = "Tour đã hoàn tất đúng lịch, khách phản hồi tốt và không phát sinh sự cố điều hành."
    ongoing_note = "Tour đang diễn ra, hướng dẫn viên đang theo đoàn và lịch trình được theo dõi hằng ngày."
    open_note = "Tour đang mở bán, còn nhận thêm khách và ưu tiên nhóm gia đình."
    cancelled_note = "Tour đã bị hủy. Lịch trình không còn hiệu lực."
    not_open_note = "Tour sắp mở bán, đang chuẩn bị chương trình và lịch trình chi tiết."

    note_lower = note.lower()

    if status == TOUR_STATUS_COMPLETED:
        if not note or note_lower in ["không có", "", "không"] or "đang diễn ra" in note_lower or "đang mở bán" in note_lower or "sắp mở bán" in note_lower or "còn nhận thêm khách" in note_lower or "đã hủy" in note_lower:
            tour["ghiChuDieuHanh"] = completed_note
    elif status == TOUR_STATUS_CANCELLED:
        if not note or note_lower in ["không có", "", "không"] or "hoàn tất" in note_lower or "đang diễn ra" in note_lower or "đang mở bán" in note_lower or "sắp mở bán" in note_lower or "hoàn thành" in note_lower or "hoàn tất đúng lịch" in note_lower:
            tour["ghiChuDieuHanh"] = cancelled_note
    elif status == TOUR_STATUS_STARTED:
        if not note or note_lower in ["không có", "", "không"] or "đang mở bán" in note_lower or "sắp mở bán" in note_lower or "hoàn tất" in note_lower or "hoàn thành" in note_lower or "đã hủy" in note_lower:
            tour["ghiChuDieuHanh"] = ongoing_note
    elif status == TOUR_STATUS_OPEN:
        if not note or note_lower in ["không có", "", "không"] or "đang diễn ra" in note_lower or "hoàn tất" in note_lower or "hoàn thành" in note_lower or "đã hủy" in note_lower:
            tour["ghiChuDieuHanh"] = open_note
    elif status == TOUR_STATUS_NOT_OPEN:
        if not note or note_lower in ["không có", "", "không"] or "đang diễn ra" in note_lower or "hoàn tất" in note_lower or "hoàn thành" in note_lower or "đã hủy" in note_lower or "đang mở bán" in note_lower:
            tour["ghiChuDieuHanh"] = not_open_note




def parse_duration_days(value, default: int = 1) -> int:
    text = normalize_spaces(value)
    if not text:
        return max(1, int(default))
    match = _SO_NGAY_RE.search(text)
    if not match:
        return max(1, int(default))
    try:
        return max(1, int(match.group(1)))
    except ValueError:
        return max(1, int(default))


def compute_end_date(start: date | None, so_ngay: int) -> date | None:
    if start is None:
        return None
    days = max(1, int(so_ngay))
    return start + timedelta(days=days - 1)


def compute_duration_days(start: date | None, end: date | None, default: int = 1) -> int:
    if start is None or end is None:
        return max(1, int(default))
    if end < start:
        return 1
    return (end - start).days + 1


def derive_tour_status(
    *,
    current_status: str | None,
    start_date: date | None,
    end_date: date | None,
    occupied: int,
    capacity: int,
    today: date | None = None,
) -> str:
    current = normalize_tour_status(current_status)
    if current == TOUR_STATUS_CANCELLED:
        return current

    now = today or date.today()
    cap = max(1, safe_int(capacity))
    reg = max(0, safe_int(occupied))

    if start_date and end_date and end_date < start_date:
        end_date = start_date
    normalized_end = end_date or start_date

    if normalized_end and now > normalized_end:
        return TOUR_STATUS_COMPLETED
    if start_date and now >= start_date:
        if reg == 0:
            return TOUR_STATUS_CANCELLED
        return TOUR_STATUS_STARTED
    if reg >= cap:
        return TOUR_STATUS_FULL
    if current == TOUR_STATUS_NOT_OPEN:
        return TOUR_STATUS_NOT_OPEN
    return TOUR_STATUS_OPEN


def is_booking_allowed(
    status: str | None,
    start_date: date | None,
    occupied: int = 0,
    capacity: int = 1,
    today: date | None = None,
) -> bool:
    now = today or date.today()
    normalized = normalize_tour_status(status)
    if normalized not in BOOKABLE_TOUR_STATUSES:
        return False
    if start_date and now >= start_date:
        return False
    cap = max(1, safe_int(capacity))
    reg = max(0, safe_int(occupied))
    if reg >= cap:
        return False
    return True


def refresh_all_tour_statuses(datastore, today: date | None = None) -> list[dict]:
    now = today or date.today()
    tours = getattr(datastore, "list_tours", getattr(datastore, "data", {}).get("tours", []))
    bookings = getattr(datastore, "list_bookings", getattr(datastore, "data", {}).get("bookings", []))
    occupied_by_tour: dict[str, int] = {}
    for booking in bookings:
        if not isinstance(booking, dict):
            continue
        refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
        if booking.get("trangThai") in CANCEL_BOOKING_STATUSES and refund_status != "Từ chối":
            continue
        ma_tour = str(booking.get("maTour", "")).strip().upper()
        if not ma_tour:
            continue
        occupied_by_tour[ma_tour] = occupied_by_tour.get(ma_tour, 0) + max(0, safe_int(booking.get("soNguoi", 0)))

    changes: list[dict] = []
    for tour in tours:
        if not isinstance(tour, dict):
            continue
        ma = str(tour.get("ma", "")).strip()
        if not ma:
            continue
        old_status = normalize_tour_status(tour.get("trangThai", ""), default=TOUR_STATUS_NOT_OPEN)
        start_date = parse_ddmmyyyy(tour.get("ngay"))
        end_date = parse_ddmmyyyy(tour.get("ngayKetThuc"))
        if start_date and not end_date:
            so_ngay = parse_duration_days(tour.get("soNgay", 1), default=1)
            end_date = compute_end_date(start_date, so_ngay)
            if end_date:
                tour["ngayKetThuc"] = format_ddmmyyyy(end_date)
        occupied = max(0, occupied_by_tour.get(ma.upper(), 0))
        capacity = max(1, safe_int(tour.get("khach", 1)))
        tour["khach"] = str(capacity)
        new_status = derive_tour_status(
            current_status=old_status,
            start_date=start_date,
            end_date=end_date,
            occupied=occupied,
            capacity=capacity,
            today=now,
        )
        tour["trangThai"] = new_status
        sync_ghi_chu_dieu_hanh(tour)
        if old_status != new_status:
            reason = "điều chỉnh theo nghiệp vụ"
            if new_status == TOUR_STATUS_FULL:
                reason = "đã đủ số khách"
            elif new_status == TOUR_STATUS_CANCELLED and start_date and now >= start_date and occupied == 0:
                reason = "đã đến ngày khởi hành nhưng chưa có khách đăng ký"
            elif new_status == TOUR_STATUS_STARTED:
                reason = "đã đến thời gian khởi hành"
            elif new_status == TOUR_STATUS_COMPLETED:
                reason = "đã qua ngày kết thúc tour"
            elif new_status == TOUR_STATUS_OPEN:
                reason = "đã còn chỗ và chưa khởi hành"
            changes.append(
                {
                    "maTour": ma,
                    "tenTour": str(tour.get("ten", "")).strip(),
                    "oldStatus": old_status,
                    "newStatus": new_status,
                    "reason": reason,
                }
            )
    check_and_create_departure_notifications(datastore)
    return changes


def is_upcoming_or_ongoing(start_date: date | None, end_date: date | None, today: date | None = None) -> bool:
    if start_date is None:
        return False
    now = today or date.today()
    normalized_end = end_date if end_date and end_date >= start_date else start_date
    return start_date >= now or (start_date <= now <= normalized_end)

# ===== BEGIN core/state_machine.py =====

from dataclasses import dataclass


TOUR_STATE_DRAFT = "draft"
TOUR_STATE_OPEN = "open"
TOUR_STATE_FULL = "full"
TOUR_STATE_ONGOING = "ongoing"
TOUR_STATE_COMPLETED = "completed"
TOUR_STATE_CANCELLED = "cancelled"

BOOKING_STATE_PENDING = "pending"
BOOKING_STATE_CONFIRMED = "confirmed"
BOOKING_STATE_PAID = "paid"
BOOKING_STATE_CANCELLED = "cancelled"
BOOKING_STATE_COMPLETED = "completed"
BOOKING_STATE_REFUNDED = "refunded"

GUIDE_STATE_AVAILABLE = "available"
GUIDE_STATE_ASSIGNED = "assigned"
GUIDE_STATE_BUSY = "busy"
GUIDE_STATE_INACTIVE = "inactive"


TOUR_STATE_BY_STATUS = {
    "nhap": TOUR_STATE_DRAFT,
    "nháp": TOUR_STATE_DRAFT,
    "sap mo ban": TOUR_STATE_DRAFT,
    "sắp mở bán": TOUR_STATE_DRAFT,
    "chua mo": TOUR_STATE_DRAFT,
    "chưa mở": TOUR_STATE_DRAFT,
    "dang mo ban": TOUR_STATE_OPEN,
    "đang mở bán": TOUR_STATE_OPEN,
    "da du khach": TOUR_STATE_FULL,
    "đã đủ khách": TOUR_STATE_FULL,
    "dang dien ra": TOUR_STATE_ONGOING,
    "đang diễn ra": TOUR_STATE_ONGOING,
    "da ket thuc": TOUR_STATE_COMPLETED,
    "đã kết thúc": TOUR_STATE_COMPLETED,
    "giu cho": TOUR_STATE_OPEN,
    "giữ chỗ": TOUR_STATE_OPEN,
    "mo ban": TOUR_STATE_OPEN,
    "mở bán": TOUR_STATE_OPEN,
    "cho khoi hanh": TOUR_STATE_OPEN,
    "chờ khởi hành": TOUR_STATE_OPEN,
    "da chot doan": TOUR_STATE_FULL,
    "đã chốt đoàn": TOUR_STATE_FULL,
    "dang di": TOUR_STATE_ONGOING,
    "đang đi": TOUR_STATE_ONGOING,
    "hoan tat": TOUR_STATE_COMPLETED,
    "hoàn tất": TOUR_STATE_COMPLETED,
    "da huy": TOUR_STATE_CANCELLED,
    "đã hủy": TOUR_STATE_CANCELLED,
    "tam hoan": TOUR_STATE_CANCELLED,
    "tạm hoãn": TOUR_STATE_CANCELLED,
    "da an": TOUR_STATE_CANCELLED,
    "đã ẩn": TOUR_STATE_CANCELLED,
}

BOOKING_STATE_BY_STATUS = {
    "moi tao": BOOKING_STATE_PENDING,
    "mới tạo": BOOKING_STATE_PENDING,
    "cho xac nhan": BOOKING_STATE_PENDING,
    "chờ xác nhận": BOOKING_STATE_PENDING,
    "da coc": BOOKING_STATE_CONFIRMED,
    "đã cọc": BOOKING_STATE_CONFIRMED,
    "da xac nhan": BOOKING_STATE_CONFIRMED,
    "đã xác nhận": BOOKING_STATE_CONFIRMED,
    "da thanh toan": BOOKING_STATE_PAID,
    "đã thanh toán": BOOKING_STATE_PAID,
    "da huy": BOOKING_STATE_CANCELLED,
    "đã hủy": BOOKING_STATE_CANCELLED,
    "cho hoan tien": BOOKING_STATE_CANCELLED,
    "chờ hoàn tiền": BOOKING_STATE_CANCELLED,
    "hoan tien": BOOKING_STATE_REFUNDED,
    "hoàn tiền": BOOKING_STATE_REFUNDED,
    "da hoan thanh": BOOKING_STATE_COMPLETED,
    "đã hoàn thành": BOOKING_STATE_COMPLETED,
}

GUIDE_STATE_BY_STATUS = {
    "san sang": GUIDE_STATE_AVAILABLE,
    "sẵn sàng": GUIDE_STATE_AVAILABLE,
    "da phan cong": GUIDE_STATE_ASSIGNED,
    "đã phân công": GUIDE_STATE_ASSIGNED,
    "dang dan tour": GUIDE_STATE_BUSY,
    "đang dẫn tour": GUIDE_STATE_BUSY,
    "tam nghi": GUIDE_STATE_INACTIVE,
    "tạm nghỉ": GUIDE_STATE_INACTIVE,
    "ngung hoat dong": GUIDE_STATE_INACTIVE,
    "ngừng hoạt động": GUIDE_STATE_INACTIVE,
    "da khoa": GUIDE_STATE_INACTIVE,
    "đã khóa": GUIDE_STATE_INACTIVE,
    "da an": GUIDE_STATE_INACTIVE,
    "đã ẩn": GUIDE_STATE_INACTIVE,
}

DISPLAY_GUIDE_STATUS = {
    GUIDE_STATE_AVAILABLE: "Sẵn sàng",
    GUIDE_STATE_ASSIGNED: "Đã phân công",
    GUIDE_STATE_BUSY: "Đang dẫn tour",
    GUIDE_STATE_INACTIVE: "Tạm nghỉ",
}

DISPLAY_BOOKING_STATUS_COMPLETED = "Đã hoàn thành"
DISPLAY_BOOKING_STATUS_CANCELLED = "Đã hủy"
DISPLAY_BOOKING_STATUS_REFUND_PENDING = "Chờ hoàn tiền"
DISPLAY_BOOKING_STATUS_REFUNDED = "Hoàn tiền"


@dataclass(frozen=True)
class TransitionRule:
    state_from: str
    state_to: str


TOUR_TRANSITIONS = {
    TransitionRule(TOUR_STATE_DRAFT, TOUR_STATE_OPEN),
    TransitionRule(TOUR_STATE_OPEN, TOUR_STATE_FULL),
    TransitionRule(TOUR_STATE_OPEN, TOUR_STATE_ONGOING),
    TransitionRule(TOUR_STATE_OPEN, TOUR_STATE_CANCELLED),
    TransitionRule(TOUR_STATE_FULL, TOUR_STATE_ONGOING),
    TransitionRule(TOUR_STATE_FULL, TOUR_STATE_CANCELLED),
    TransitionRule(TOUR_STATE_ONGOING, TOUR_STATE_COMPLETED),
    TransitionRule(TOUR_STATE_ONGOING, TOUR_STATE_CANCELLED),
}

BOOKING_TRANSITIONS = {
    TransitionRule(BOOKING_STATE_PENDING, BOOKING_STATE_CONFIRMED),
    TransitionRule(BOOKING_STATE_PENDING, BOOKING_STATE_PAID),
    TransitionRule(BOOKING_STATE_PENDING, BOOKING_STATE_CANCELLED),
    TransitionRule(BOOKING_STATE_CONFIRMED, BOOKING_STATE_PAID),
    TransitionRule(BOOKING_STATE_CONFIRMED, BOOKING_STATE_CANCELLED),
    TransitionRule(BOOKING_STATE_PAID, BOOKING_STATE_COMPLETED),
    TransitionRule(BOOKING_STATE_PAID, BOOKING_STATE_CANCELLED),
    TransitionRule(BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED),
}

GUIDE_TRANSITIONS = {
    TransitionRule(GUIDE_STATE_AVAILABLE, GUIDE_STATE_ASSIGNED),
    TransitionRule(GUIDE_STATE_ASSIGNED, GUIDE_STATE_BUSY),
    TransitionRule(GUIDE_STATE_BUSY, GUIDE_STATE_AVAILABLE),
    TransitionRule(GUIDE_STATE_AVAILABLE, GUIDE_STATE_INACTIVE),
    TransitionRule(GUIDE_STATE_ASSIGNED, GUIDE_STATE_INACTIVE),
    TransitionRule(GUIDE_STATE_BUSY, GUIDE_STATE_INACTIVE),
    TransitionRule(GUIDE_STATE_INACTIVE, GUIDE_STATE_AVAILABLE),
}


def _normalize_key(value: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_key` ( normalize key).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return " ".join(str(value or "").strip().lower().split())


def tour_state_from_status(status: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `tour_state_from_status` (tour state from status).
    Tham số:
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return TOUR_STATE_BY_STATUS.get(_normalize_key(status), TOUR_STATE_OPEN)


def booking_state_from_status(status: str, refund_status: str = "") -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `booking_state_from_status` (booking state from status).
    Tham số:
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        refund_status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = _normalize_key(status)
    if normalized in BOOKING_STATE_BY_STATUS:
        return BOOKING_STATE_BY_STATUS[normalized]

    if _normalize_key(refund_status) in {"da hoan tien", "đã hoàn tiền"}:
        return BOOKING_STATE_REFUNDED
    return BOOKING_STATE_PENDING


def calculate_booking_total(booking: dict) -> int:
    """
    Trả về tổng tiền của booking dạng số nguyên an toàn.
    """
    return safe_int(booking.get("tongTien", 0))


def calculate_paid_amount(booking: dict) -> int:
    """
    Trả về số tiền đã thanh toán của booking dạng số nguyên an toàn.
    """
    return safe_int(booking.get("daThanhToan", booking.get("paidAmount", 0)))


def calculate_refunded_amount(booking: dict) -> int:
    """
    Trả về số tiền đã hoàn thật sự cho khách.
    Booking bị từ chối hoàn tiền không làm giảm doanh thu thực nhận.
    """
    status = str(booking.get("trangThai", "")).strip()
    refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
    normalized_refund = _normalize_key(refund_status)
    if normalized_refund in {"tu choi", "từ chối", "rejected"}:
        return 0

    booking_state = booking_state_from_status(status, refund_status)
    if booking_state != BOOKING_STATE_REFUNDED and normalized_refund not in {"da hoan tien", "đã hoàn tiền", "approved", "da hoan"}:
        return 0

    paid = max(0, calculate_paid_amount(booking))
    refunded = max(0, safe_int(booking.get("soTienHoan", booking.get("refundAmount", 0))))
    if refunded <= 0:
        refunded = paid
    return min(refunded, paid) if paid else refunded


def is_effective_booking(booking: dict) -> bool:
    """
    Booking còn hiệu lực là booking không bị hủy và chưa hoàn tiền thành công.
    """
    status = str(booking.get("trangThai", "")).strip()
    refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
    state = booking_state_from_status(status, refund_status)
    return state not in {BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED}


def calculate_remaining_amount(booking: dict) -> int:
    """
    Trả về số tiền còn nợ của booking.
    Nếu booking ở trạng thái Đã hủy hoặc Hoàn tiền, số nợ bằng 0.
    """
    if not is_effective_booking(booking):
        return 0
    total = calculate_booking_total(booking)
    paid = calculate_paid_amount(booking)
    return max(0, total - paid)


def show_wrapped_message(title: str, message: str, kind: str = "info", parent=None) -> bool | None:
    """
    Hiển thị thông báo qua tkinter messagebox với nội dung được tự động ngắt dòng 
    ở độ rộng tối đa 65 ký tự trên mỗi dòng.
    """
    import textwrap
    from tkinter import messagebox

    lines = str(message or "").split("\n")
    wrapped_lines = []
    for line in lines:
        if line.strip():
            wrapped_lines.extend(textwrap.wrap(line, width=65))
        else:
            wrapped_lines.append("")
    wrapped_message = "\n".join(wrapped_lines)

    if kind == "warning":
        messagebox.showwarning(title, wrapped_message, parent=parent)
        return None
    elif kind == "error":
        messagebox.showerror(title, wrapped_message, parent=parent)
        return None
    elif kind == "askyesno" or kind == "question":
        return messagebox.askyesno(title, wrapped_message, parent=parent)
    else:
        messagebox.showinfo(title, wrapped_message, parent=parent)
        return None


def show_detailed_notification_popup(parent, notif_data: dict, datastore=None):
    """
    Hiển thị cửa sổ popup chi tiết thông báo với giao diện chuyên nghiệp và nút Đóng bo tròn.
    """
    import tkinter as tk
    from tkinter import ttk
    from GUI.common.rounded_button import RoundedButton

    popup = tk.Toplevel(parent)
    popup.title("Chi tiết thông báo")
    popup.geometry("650x550")
    popup.minsize(550, 450)
    popup.configure(bg="#f1f5f9")
    popup.transient(parent)
    popup.grab_set()

    # Căn giữa popup
    popup.update_idletasks()
    w = popup.winfo_width()
    h = popup.winfo_height()
    x = (popup.winfo_screenwidth() // 2) - (w // 2)
    y = (popup.winfo_screenheight() // 2) - (h // 2)
    popup.geometry(f"+{x}+{y}")

    # Lấy thông tin an toàn
    def safe_get(keys, default="Không có"):
        for k in keys:
            if k in notif_data:
                val = notif_data[k]
                if val is not None and str(val).strip() != "":
                    return str(val).strip()
        return default

    evt_type = safe_get(["eventType", "loaiThongBao", "Loại thông báo", "eventTypeDisplay"], "Thông báo")
    date_display = safe_get(["date", "thoiGian", "ngayGui", "Ngày gửi", "Ngày nhận", "time"], "Không có")
    receiver = safe_get(["username", "nguoiNhan", "Người nhận", "receiver"], "Không có")
    role = safe_get(["role", "vaiTro", "Vai trò nhận", "receiverRole"], "Không có")
    ma_tour = safe_get(["maTour", "Mã tour", "ma_tour"], "Không có")
    ten_tour = safe_get(["tenTour", "Tên tour", "ten_tour"], "Không có")
    ma_booking = safe_get(["maBooking", "Mã booking", "ma_booking"], "Không có")
    ma_hdv = safe_get(["maHDV", "Mã HDV", "ma_hdv"], "Không có")

    ten_hdv = notif_data.get("tenHDV") or notif_data.get("Tên HDV") or notif_data.get("ten_hdv")
    if not ten_hdv and datastore and ma_hdv != "Không có":
        hdv = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
        if hdv:
            ten_hdv = hdv.get("tenHDV")
    ten_hdv = ten_hdv or "Không có"

    event_translations = {
        "Account Update": "Cập nhật tài khoản",
        "Refund Approved": "Hoàn tiền được duyệt",
        "Refund Declined": "Hoàn tiền bị từ chối",
        "tour_completed": "Tour hoàn thành",
        "booking_created": "Đặt tour thành công",
        "payment_success": "Thanh toán thành công",
        "HDV_profile_update": "HDV cập nhật hồ sơ",
        "TOUR_DEPARTURE_WARNING": "Cảnh báo khởi hành"
    }
    evt_display = event_translations.get(evt_type, evt_type)

    event_colors = {
        "Cập nhật tài khoản": "#0d9488",
        "Hoàn tiền được duyệt": "#22c55e",
        "Hoàn tiền bị từ chối": "#ef4444",
        "Tour hoàn thành": "#3b82f6",
        "Đặt tour thành công": "#a855f7",
        "Thanh toán thành công": "#10b981",
        "Account Update": "#0d9488",
        "Refund Approved": "#22c55e",
        "Refund Declined": "#ef4444",
        "tour_completed": "#3b82f6",
        "booking_created": "#a855f7",
        "payment_success": "#10b981",
        "default": "#2563eb"
    }
    accent_color = event_colors.get(evt_display, event_colors.get(evt_type, event_colors["default"]))

    accent_bar = tk.Frame(popup, height=6, bg=accent_color)
    accent_bar.pack(fill="x")

    pad_frame = tk.Frame(popup, bg="#ffffff", padx=20, pady=20)
    pad_frame.pack(fill="both", expand=True, padx=15, pady=15)

    title_lbl = tk.Label(
        pad_frame,
        text="Chi tiết thông báo",
        bg="#ffffff",
        fg="#0f172a",
        font=("Times New Roman", 14, "bold")
    )
    title_lbl.pack(anchor="w", pady=(0, 10))

    info_frame = tk.Frame(pad_frame, bg="#f8fafc", bd=1, relief="solid", highlightthickness=0)
    info_frame.configure(highlightbackground="#cbd5e1")
    info_frame.pack(fill="x", pady=(0, 15))

    info_inner = tk.Frame(info_frame, bg="#f8fafc", padx=12, pady=12)
    info_inner.pack(fill="both")

    details = [
        ("Loại thông báo:", evt_display),
        ("Ngày giờ:", date_display),
        ("Người nhận:", receiver),
        ("Vai trò nhận:", role),
        ("Mã tour:", ma_tour),
        ("Tên tour:", ten_tour),
        ("Mã booking:", ma_booking),
        ("Mã HDV:", ma_hdv),
        ("Tên HDV:", ten_hdv),
    ]

    row_idx = 0
    info_inner.grid_columnconfigure(0, weight=0, minsize=110)
    info_inner.grid_columnconfigure(1, weight=1)
    info_inner.grid_columnconfigure(2, weight=0, minsize=110)
    info_inner.grid_columnconfigure(3, weight=1)

    for lbl, val in details:
        if val and val != "Không có":
            r = row_idx // 2
            c = (row_idx % 2) * 2

            l_widget = tk.Label(info_inner, text=lbl, font=("Times New Roman", 10, "bold"), bg="#f8fafc", fg="#475569", anchor="w")
            l_widget.grid(row=r, column=c, sticky="w", pady=3, padx=(5, 5))

            v_widget = tk.Label(info_inner, text=val, font=("Times New Roman", 10), bg="#f8fafc", fg="#0f172a", anchor="w", wraplength=200, justify="left")
            v_widget.grid(row=r, column=c+1, sticky="w", pady=3, padx=(0, 10))

            row_idx += 1

    tk.Label(pad_frame, text="Nội dung thông báo:", font=("Times New Roman", 11, "bold"), bg="#ffffff", fg="#0f172a").pack(anchor="w", pady=(5, 5))

    txt_container = tk.Frame(pad_frame, bg="#ffffff", bd=1, relief="solid")
    txt_container.pack(fill="both", expand=True, pady=(0, 15))

    content_text = tk.Text(txt_container, bg="#f8fafc", fg="#1e293b", font=("Times New Roman", 11), wrap="word", bd=0, highlightthickness=0, padx=10, pady=10)
    text_scroll = ttk.Scrollbar(txt_container, orient="vertical", command=content_text.yview)
    content_text.configure(yscrollcommand=text_scroll.set)
    content_text.pack(side="left", fill="both", expand=True)
    text_scroll.pack(side="right", fill="y")

    full_content = safe_get(["content", "noiDung", "thongBao", "Nội dung thông báo"], "")
    content_text.insert("1.0", full_content)
    content_text.configure(state="disabled")

    btn_close = RoundedButton(
        pad_frame,
        text="Đóng",
        bg="#ef4444",
        fg="white",
        activebackground="#dc2626",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Times New Roman", 11, "bold"),
        padx=20,
        pady=8,
        command=popup.destroy
    )
    btn_close.pack(anchor="e")


def cleanup_deleted_tour_references(datastore, tour_code: str) -> None:
    """
    Dọn dẹp các tham chiếu của tour bị xóa cứng khỏi các bảng liên quan:
    - bookings: Xóa các booking của tour này.
    - reviews: Xóa các đánh giá thuộc về tour bị xóa.
    - notifications: Xóa các thông báo liên quan đến tour bị xóa.
    """
    if not tour_code:
        return

    tour_code_upper = str(tour_code).strip().upper()

    # 1. Dọn dẹp bookings
    if hasattr(datastore, "data") and isinstance(datastore.data, dict):
        bookings = datastore.data.get("bookings", [])
        if isinstance(bookings, list):
            datastore.data["bookings"] = [
                b for b in bookings 
                if str(b.get("maTour", "")).strip().upper() != tour_code_upper
            ]

    # 2. Dọn dẹp reviews
    if hasattr(datastore, "reviews") and isinstance(datastore.reviews, list):
        datastore.reviews = [
            r for r in datastore.reviews 
            if str(r.get("maTour", "")).strip().upper() != tour_code_upper
        ]

    # 3. Dọn dẹp notifications
    if hasattr(datastore, "notifications") and isinstance(datastore.notifications, list):
        datastore.notifications = [
            n for n in datastore.notifications 
            if str(n.get("maTour", "")).strip().upper() != tour_code_upper
        ]


def guide_state_from_status(status: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `guide_state_from_status` (guide state from status).
    Tham số:
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return GUIDE_STATE_BY_STATUS.get(_normalize_key(status), GUIDE_STATE_AVAILABLE)


def can_tour_transition(state_from: str, state_to: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `can_tour_transition` (can tour transition).
    Tham số:
        state_from: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        state_to: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return TransitionRule(state_from, state_to) in TOUR_TRANSITIONS or state_from == state_to


def can_booking_transition(state_from: str, state_to: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `can_booking_transition` (can booking transition).
    Tham số:
        state_from: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        state_to: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return TransitionRule(state_from, state_to) in BOOKING_TRANSITIONS or state_from == state_to


def can_guide_transition(state_from: str, state_to: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `can_guide_transition` (can guide transition).
    Tham số:
        state_from: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        state_to: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return TransitionRule(state_from, state_to) in GUIDE_TRANSITIONS or state_from == state_to


# ===== BEGIN core/security.py =====

import os
import hashlib
import re

import bcrypt

SHA256_PATTERN = re.compile(r"[a-fA-F0-9]{64}")
MASKED_PASSWORD = "********"
BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def legacy_sha256_hash(raw_password: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `legacy_sha256_hash` (legacy sha256 hash).
    Tham số:
        raw_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return hashlib.sha256(str(raw_password or "").encode("utf-8")).hexdigest()


def hash_password(raw_password: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `hash_password` (hash password).
    Tham số:
        raw_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    raw = str(raw_password or "").strip()
    if not raw:
        return ""
    try:
        configured_rounds = int(os.getenv("TRAVEL_BCRYPT_ROUNDS", "12"))
    except ValueError:
        configured_rounds = 12
    rounds = max(4, min(15, configured_rounds))
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def looks_like_sha256(value: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `looks_like_sha256` (looks like sha256).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return bool(SHA256_PATTERN.fullmatch(str(value).strip()))


def is_bcrypt_hash(value: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_bcrypt_hash` (is bcrypt hash).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = str(value or "").strip()
    return normalized.startswith(BCRYPT_PREFIXES)


def prepare_password_for_storage(password: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `prepare_password_for_storage` (prepare password for storage).
    Tham số:
        password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = str(password or "").strip()
    if not normalized:
        return ""
    if is_bcrypt_hash(normalized):
        return normalized
    if looks_like_sha256(normalized):
        return normalized
    return hash_password(normalized)


def password_matches(stored_password: str, input_password: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `password_matches` (password matches).
    Tham số:
        stored_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        input_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    stored = str(stored_password or "").strip()
    provided = str(input_password or "").strip()
    if not stored:
        return False
    if is_bcrypt_hash(stored):
        try:
            return bcrypt.checkpw(provided.encode("utf-8"), stored.encode("utf-8"))
        except ValueError:
            return False
    if looks_like_sha256(stored):
        return legacy_sha256_hash(provided) == stored
    return stored == provided


def upgrade_password_hash(stored_password: str, input_password: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `upgrade_password_hash` (upgrade password hash).
    Tham số:
        stored_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        input_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    stored = str(stored_password or "").strip()
    provided = str(input_password or "").strip()
    if not stored or not provided:
        return stored
    if is_bcrypt_hash(stored):
        return stored
    if password_matches(stored, provided):
        return hash_password(provided)
    return stored


def mask_password(_: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `mask_password` (mask password).
    Tham số:
        _: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return MASKED_PASSWORD

# ===== BEGIN core/normalizers.py =====


def _first_text(data: dict, keys: tuple[str, ...], default: str = "") -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_first_text` ( first text).
    Tham số:
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def normalize_review_item(
    review: dict,
    *,
    fullname_keys: tuple[str, ...] = ("fullname", "tenKhach", "hoTen"),
    content_keys: tuple[str, ...] = ("content", "comment", "noiDung"),
    date_keys: tuple[str, ...] = ("date", "thoiGian", "ngayGui", "ngay"),
    include_rating: bool = False,
    include_ma_hdv: bool = False,
) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_review_item` (normalize review item).
    Tham số:
        review: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fullname_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        content_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        date_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        include_rating: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        include_ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    username = _first_text(review, ("username", "user"))
    fullname = _first_text(review, fullname_keys)

    target = _first_text(review, ("target", "doiTuong"))
    if not target:
        if review.get("maHDV"):
            target = "HDV"
        elif review.get("maTour"):
            target = "Tour"
        else:
            target = "Công ty"

    normalized = {
        "maReview": _first_text(review, ("maReview", "reviewId", "id")),
        "username": username,
        "fullname": fullname,
        "target": target,
        "target_id": _first_text(review, ("target_id", "maHDV", "maTour")),
        "content": _first_text(review, content_keys),
        "date": _first_text(review, date_keys),
        "maBooking": _first_text(review, ("maBooking", "bookingCode", "booking_code")),
        "maTour": _first_text(review, ("maTour",)),
        "tenTour": _first_text(review, ("tenTour", "ten_tour")),
    }

    if include_rating or "rating" in review:
        normalized["rating"] = review.get("rating", "")
    if include_ma_hdv or "maHDV" in review:
        normalized["maHDV"] = _first_text(review, ("maHDV",))
    if "tenHDV" in review:
        normalized["tenHDV"] = _first_text(review, ("tenHDV", "ten_hdv"))
    for key in ("adminReply", "adminReplyDate", "adminReplyBy", "trangThai", "hidden"):
        if key in review:
            normalized[key] = review.get(key, "")
    return normalized


def normalize_notification_item(
    notification: dict,
    datastore=None,
    *,
    content_keys: tuple[str, ...] = ("content", "noiDung", "message"),
    date_keys: tuple[str, ...] = ("date", "thoiGian", "ngayGui", "ngay"),
) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_notification_item` (normalize notification item).
    Tham số:
        notification: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        content_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        date_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    ma_hdv = _first_text(notification, ("maHDV",))
    ma_tour = _first_text(notification, ("maTour",))

    ten_hdv = _first_text(notification, ("tenHDV",))
    ten_tour = _first_text(notification, ("tenTour",))

    if datastore is not None:
        if not ten_hdv and ma_hdv:
            guide = datastore.find_hdv(ma_hdv)
            if guide:
                ten_hdv = _first_text(guide, ("tenHDV",))
        if not ten_tour and ma_tour:
            tour = datastore.find_tour(ma_tour)
            if tour:
                ten_tour = _first_text(tour, ("ten",))

    res = {
        "eventType": _first_text(notification, ("eventType", "loai")),
        "maHDV": ma_hdv,
        "tenHDV": ten_hdv,
        "maTour": ma_tour,
        "tenTour": ten_tour,
        "content": _first_text(notification, content_keys),
        "date": _first_text(notification, date_keys),
    }
    username = _first_text(notification, ("username", "nguoiDung", "tenDangNhap"))
    if username:
        res["username"] = username
    ma_booking = _first_text(notification, ("maBooking", "soBooking"))
    if ma_booking:
        res["maBooking"] = ma_booking
    return res

# ===== BEGIN core/crud_logging.py =====



def collect_changed_fields(before: dict | None, after: dict | None, keys: list[str] | None = None) -> list[str]:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `collect_changed_fields` (collect changed fields).
    Tham số:
        before: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        after: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    before = before or {}
    after = after or {}

    if keys is None:
        keys = sorted(set(before.keys()) | set(after.keys()))

    changes = []
    for key in keys:
        if before.get(key) != after.get(key):
            changes.append(key)
    return changes


def write_crud_log(
    *,
    datastore,
    actor: str,
    role: str,
    entity: str,
    operation: str,
    target: str = "",
    status: str = "SUCCESS",
    detail: str = "",
) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `write_crud_log` (write crud log).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        entity: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        operation: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        target: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        detail: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    entity_name = str(entity or "").strip().upper()
    operation_name = str(operation or "").strip().upper()
    target_name = str(target or "").strip()

    detail_parts = []
    if target_name:
        detail_parts.append(f"Mã đối tượng: {target_name}")
    if detail:
        detail_parts.append(str(detail).strip())

    write_activity_log(
        action=f"{operation_name}_{entity_name}",
        actor=str(actor or "system").strip() or "system",
        role=str(role or "system").strip() or "system",
        status=status,
        detail=" | ".join(detail_parts),
        datastore=datastore,
    )

# ===== BEGIN core/business_rules.py =====


def _safe_int(value, default: int = 0) -> int:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_safe_int` ( safe int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def normalize_business_state(data: dict) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_business_state` (normalize business state).
    Tham số:
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not isinstance(data, dict):
        return data

    data.setdefault("tours", [])
    data.setdefault("bookings", [])
    data.setdefault("hdv", [])

    tours_by_code = {}
    for tour in data["tours"]:
        ma_tour = str(tour.get("ma", "")).strip()
        if not ma_tour:
            continue
        tour["tourState"] = tour_state_from_status(str(tour.get("trangThai", "")).strip())
        tours_by_code[ma_tour] = tour

    for booking in data["bookings"]:
        booking_state = booking_state_from_status(
            str(booking.get("trangThai", "")).strip(),
            str(booking.get("trangThaiHoanTien", "")).strip(),
        )
        tour = tours_by_code.get(str(booking.get("maTour", "")).strip())
        if tour:
            tour_state = tour.get("tourState", "")
            paid_amount = max(0, _safe_int(booking.get("daThanhToan", 0)))

            if tour_state == TOUR_STATE_CANCELLED and booking_state in {
                BOOKING_STATE_PENDING,
                BOOKING_STATE_CONFIRMED,
                BOOKING_STATE_PAID,
                BOOKING_STATE_COMPLETED,
            }:
                if paid_amount > 0:
                    booking["trangThai"] = DISPLAY_BOOKING_STATUS_REFUND_PENDING
                    booking["trangThaiHoanTien"] = "Chờ duyệt"
                    booking["soTienHoan"] = max(_safe_int(booking.get("soTienHoan", 0)), paid_amount)
                else:
                    booking["trangThai"] = DISPLAY_BOOKING_STATUS_CANCELLED
                    booking["trangThaiHoanTien"] = ""
                    booking["soTienHoan"] = 0
            elif tour_state == TOUR_STATE_COMPLETED and booking_state in {
                BOOKING_STATE_CONFIRMED,
                BOOKING_STATE_PAID,
            }:
                booking["trangThai"] = DISPLAY_BOOKING_STATUS_COMPLETED
                booking["trangThaiHoanTien"] = ""
                booking["soTienHoan"] = 0
        booking["bookingState"] = booking_state_from_status(
            str(booking.get("trangThai", "")).strip(),
            str(booking.get("trangThaiHoanTien", "")).strip(),
        )

    assignments: dict[str, str] = {}
    for tour in data["tours"]:
        ma_hdv = str(tour.get("hdvPhuTrach", "")).strip()
        if not ma_hdv:
            continue
        tour_state = tour.get("tourState", tour_state_from_status(tour.get("trangThai", "")))
        if tour_state in {TOUR_STATE_CANCELLED, TOUR_STATE_COMPLETED}:
            continue
        current = assignments.get(ma_hdv, GUIDE_STATE_AVAILABLE)
        if tour_state == "ongoing":
            assignments[ma_hdv] = GUIDE_STATE_BUSY
        elif current != GUIDE_STATE_BUSY:
            assignments[ma_hdv] = GUIDE_STATE_ASSIGNED

    for guide in data["hdv"]:
        ma_hdv = str(guide.get("maHDV", "")).strip()
        account_status = normalize_guide_status(guide.get("trangThai", guide.get("status", "")))
        existing_state = guide_state_from_status(str(guide.get("trangThai", "")).strip())
        if account_status in {GUIDE_STATUS_INACTIVE, GUIDE_STATUS_BLOCKED, GUIDE_STATUS_HIDDEN, GUIDE_STATUS_TEMP_OFF}:
            guide_state = GUIDE_STATE_INACTIVE
        else:
            guide_state = assignments.get(ma_hdv, GUIDE_STATE_AVAILABLE)

        guide["guideState"] = guide_state
        if account_status in {GUIDE_STATUS_INACTIVE, GUIDE_STATUS_BLOCKED, GUIDE_STATUS_HIDDEN}:
            guide["trangThai"] = account_status
        elif account_status == GUIDE_STATUS_TEMP_OFF:
            guide["trangThai"] = GUIDE_STATUS_TEMP_OFF
        else:
            guide["trangThai"] = DISPLAY_GUIDE_STATUS.get(guide_state, guide.get("trangThai", "Sẵn sàng"))

    for tour in data["tours"]:
        if "tourState" not in tour:
            tour["tourState"] = tour_state_from_status(str(tour.get("trangThai", "")).strip())

    return data

# ===== BEGIN core/booking_pricing.py =====


def safe_int(value, default=0):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `safe_int` (safe int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def normalize_passenger_breakdown(raw_breakdown, total_people):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_passenger_breakdown` (normalize passenger breakdown).
    Tham số:
        raw_breakdown: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        total_people: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    total = max(1, safe_int(total_people, 1))
    data = raw_breakdown if isinstance(raw_breakdown, dict) else {}

    child = max(0, safe_int(data.get("treEm", 0)))
    senior = max(0, safe_int(data.get("nguoiCaoTuoi", 0)))
    middle = max(0, safe_int(data.get("trungNien", 0)))

    if child + senior + middle != total:
        if child + senior > total:
            return None
        middle = total - child - senior

    return {
        "treEm": child,
        "trungNien": middle,
        "nguoiCaoTuoi": senior,
    }


def calculate_age_discount(price_per_person, breakdown):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `calculate_age_discount` (calculate age discount).
    Tham số:
        price_per_person: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        breakdown: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not isinstance(breakdown, dict):
        return 0

    price = max(0, safe_int(price_per_person))
    child = max(0, safe_int(breakdown.get("treEm", 0)))
    senior = max(0, safe_int(breakdown.get("nguoiCaoTuoi", 0)))

    return max(
        0,
        round(price * child * 0.20) + round(price * senior * 0.35),
    )

# ===== BEGIN core/voucher_service.py =====

from datetime import datetime



def safe_int(value, default=0):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `safe_int` (safe int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_ddmmyyyy(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `parse_ddmmyyyy` (parse ddmmyyyy).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return datetime.strptime(str(value or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def normalize_tour_scope(value) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_tour_scope` (normalize tour scope).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    def _scope_key(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(text or "").strip())
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_text = ascii_text.replace("_", " ").replace("-", " ")
        return " ".join(ascii_text.upper().split())

    global_scope_tokens = {
        "TAT CA",
        "TAT CA TOUR",
        "TAT CA TOURS",
        "TOAN BO",
        "TOAN BO TOUR",
        "ALL",
        "ALL TOUR",
        "ALL TOURS",
        "*",
    }

    raw_text = str(value or "").strip()
    if not raw_text:
        return ""

    items = []
    for part in raw_text.replace(";", ",").replace("\n", ",").split(","):
        token = part.strip()
        if not token:
            continue
        if _scope_key(token) in global_scope_tokens:
            # Bất kỳ biến thể "tất cả" nào đều quy về phạm vi toàn bộ tour.
            return ""
        normalized = token.upper()
        if normalized and normalized not in items:
            items.append(normalized)
    return ", ".join(items)


def parse_tour_scope(value) -> list[str]:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `parse_tour_scope` (parse tour scope).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = normalize_tour_scope(value)
    return [part.strip() for part in normalized.split(",") if part.strip()]


def resolve_voucher_discount(voucher, gross_total):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `resolve_voucher_discount` (resolve voucher discount).
    Tham số:
        voucher: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        gross_total: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not voucher:
        return 0

    gross_total = max(0, safe_int(gross_total))
    loai_giam = str(voucher.get("loaiGiam", "")).strip()
    raw_discount = str(voucher.get("giamGiaVoucher", "")).strip()

    if loai_giam == "Phần trăm":
        try:
            percent = float(raw_discount.replace("%", "").strip())
        except ValueError:
            return 0
        return min(gross_total, max(0, int(round(gross_total * percent / 100))))

    return min(gross_total, max(0, safe_int(raw_discount)))


def _list_vouchers(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_list_vouchers` ( list vouchers).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    vouchers = getattr(datastore, "list_vouchers", None)
    if vouchers is not None:
        return vouchers
    return datastore.data.get("maVoucher", [])


def _find_voucher(datastore, code):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_voucher` ( find voucher).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = str(code or "").strip().upper()
    if not normalized:
        return None

    finder = getattr(datastore, "find_voucher", None)
    if callable(finder):
        result = finder(normalized)
        if result:
            return result

    return next(
        (
            voucher
            for voucher in _list_vouchers(datastore)
            if str(voucher.get("maVoucher", "")).strip().upper() == normalized
        ),
        None,
    )


def _iter_active_voucher_bookings(datastore, code, exclude_booking=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_iter_active_voucher_bookings` ( iter active voucher bookings).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        exclude_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized_code = str(code or "").strip().upper()
    exclude_booking = str(exclude_booking or "").strip()

    for booking in getattr(datastore, "list_bookings", datastore.data.get("bookings", [])):
        if str(booking.get("maVoucher", "")).strip().upper() != normalized_code:
            continue

        booking_code = str(booking.get("maBooking", "")).strip()
        if exclude_booking and booking_code == exclude_booking:
            continue

        status = str(booking.get("trangThai", "")).strip()
        if status in {"Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}:
            continue

        yield booking


def get_voucher_usage(datastore, code, username="", ma_tour="", exclude_booking=None) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `get_voucher_usage` (get voucher usage).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        exclude_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized_username = str(username or "").strip().lower()
    normalized_tour = str(ma_tour or "").strip().upper()

    total = 0
    user_uses = 0
    tour_uses = 0

    for booking in _iter_active_voucher_bookings(datastore, code, exclude_booking=exclude_booking):
        total += 1

        booking_username = str(booking.get("usernameDat", "")).strip().lower()
        booking_tour = str(booking.get("maTour", "")).strip().upper()

        if normalized_username and booking_username == normalized_username:
            user_uses += 1
        if normalized_tour and booking_tour == normalized_tour:
            tour_uses += 1

    return {
        "total": total,
        "user_uses": user_uses,
        "tour_uses": tour_uses,
    }


def build_voucher_scope_label(voucher) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_voucher_scope_label` (build voucher scope label).
    Tham số:
        voucher: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tours = parse_tour_scope(voucher.get("tourApDung", ""))
    if not tours:
        return "Áp dụng toàn bộ tour"
    return "Chỉ áp dụng: " + ", ".join(tours)


def validate_voucher_payload(datastore, data, old_code=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_voucher_payload` (validate voucher payload).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    required = [
        "maVoucher",
        "tenVoucher",
        "loaiGiam",
        "giamGiaVoucher",
        "donToiThieu",
        "soLuong",
        "daSuDung",
        "ngayBatDau",
        "ngayKetThuc",
        "trangThai",
        "moTa",
    ]

    for key in required:
        if not str(data.get(key, "")).strip():
            return False, "Vui lòng nhập đầy đủ thông tin voucher."

    code = str(data.get("maVoucher", "")).strip().upper()
    if len(code) < 2:
        return False, "Mã voucher không hợp lệ."

    old_normalized = str(old_code or "").strip().upper()
    for voucher in _list_vouchers(datastore):
        if str(voucher.get("maVoucher", "")).strip().upper() == code and code != old_normalized:
            return False, "Mã voucher đã tồn tại."

    loai = str(data.get("loaiGiam", "")).strip()
    giam = str(data.get("giamGiaVoucher", "")).strip()
    if loai == "Phần trăm":
        if not giam.endswith("%"):
            return False, "Giảm giá phần trăm phải có dạng ví dụ: 10%."
        try:
            percent = float(giam.replace("%", "").strip())
        except ValueError:
            return False, "Giảm giá phần trăm không hợp lệ."
        if percent <= 0 or percent > 100:
            return False, "Phần trăm giảm phải từ 1% đến 100%."
    else:
        if not giam.isdigit() or int(giam) <= 0:
            return False, "Giảm giá tiền mặt phải là số dương."

    numeric_fields = {
        "donToiThieu": "Đơn tối thiểu",
        "soLuong": "Số lượng",
        "daSuDung": "Đã sử dụng",
        "gioiHanMoiUser": "Giới hạn mỗi user",
    }
    for field, label in numeric_fields.items():
        raw_value = str(data.get(field, "0") or "0").strip()
        if raw_value and (not raw_value.isdigit() or int(raw_value) < 0):
            return False, f"{label} phải là số >= 0."

    if safe_int(data.get("daSuDung", 0)) > safe_int(data.get("soLuong", 0)):
        return False, "Số đã sử dụng không được lớn hơn số lượng."

    start_date = parse_ddmmyyyy(data.get("ngayBatDau"))
    end_date = parse_ddmmyyyy(data.get("ngayKetThuc"))
    if not start_date or not end_date:
        return False, "Ngày bắt đầu / kết thúc không đúng định dạng dd/mm/yyyy."
    if end_date < start_date:
        return False, "Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu."

    normalized_scope = normalize_tour_scope(data.get("tourApDung", ""))
    if normalized_scope:
        known_tours = {
            str(tour.get("ma", "")).strip().upper()
            for tour in getattr(datastore, "list_tours", datastore.data.get("tours", []))
        }
        missing = [tour_code for tour_code in parse_tour_scope(normalized_scope) if tour_code not in known_tours]
        if missing:
            return False, f"Không tìm thấy tour áp dụng: {', '.join(missing)}."

    return True, ""


def build_voucher_quote(datastore, voucher_code, gross_total, username="", ma_tour="", exclude_booking=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_voucher_quote` (build voucher quote).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        voucher_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        gross_total: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        exclude_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    code = str(voucher_code or "").strip().upper()
    if not code:
        return {
            "ok": True,
            "voucher": None,
            "code": "",
            "discount": 0,
            "message": "Chưa áp dụng mã giảm giá.",
        }

    voucher = _find_voucher(datastore, code)
    if not voucher:
        return {
            "ok": False,
            "voucher": None,
            "code": code,
            "discount": 0,
            "message": "Mã giảm giá không tồn tại.",
        }

    status = str(voucher.get("trangThai", "")).strip().lower()
    start_date = parse_ddmmyyyy(voucher.get("ngayBatDau"))
    end_date = parse_ddmmyyyy(voucher.get("ngayKetThuc"))
    today_local = datetime.now().date()
    remaining = max(0, safe_int(voucher.get("soLuong", 0)) - safe_int(voucher.get("daSuDung", 0)))
    minimum_order = max(0, safe_int(voucher.get("donToiThieu", 0)))
    user_limit = max(0, safe_int(voucher.get("gioiHanMoiUser", 0)))
    allowed_tours = parse_tour_scope(voucher.get("tourApDung", ""))
    usage = get_voucher_usage(datastore, code, username=username, ma_tour=ma_tour, exclude_booking=exclude_booking)

    if "ngừng" in status:
        return {"ok": False, "voucher": voucher, "code": code, "discount": 0, "message": "Mã này đang tạm ngừng áp dụng."}
    if start_date and today_local < start_date:
        return {
            "ok": False,
            "voucher": voucher,
            "code": code,
            "discount": 0,
            "message": f"Mã này có hiệu lực từ {start_date.strftime('%d/%m/%Y')}.",
        }
    if end_date and today_local > end_date:
        return {"ok": False, "voucher": voucher, "code": code, "discount": 0, "message": "Mã này đã hết hạn."}
    if remaining <= 0:
        return {"ok": False, "voucher": voucher, "code": code, "discount": 0, "message": "Mã này đã dùng hết lượt."}
    if gross_total < minimum_order:
        return {
            "ok": False,
            "voucher": voucher,
            "code": code,
            "discount": 0,
            "message": f"Đơn tối thiểu để dùng mã là {minimum_order:,}đ.".replace(",", "."),
        }

    normalized_tour = str(ma_tour or "").strip().upper()
    if normalized_tour:
        tour = datastore.find_tour(normalized_tour) if hasattr(datastore, "find_tour") else None
        if tour:
            t_status = normalize_tour_status(tour.get("trangThai", ""))
            if t_status != TOUR_STATUS_OPEN:
                return {
                    "ok": False,
                    "voucher": voucher,
                    "code": code,
                    "discount": 0,
                    "message": "Chỉ có thể áp dụng voucher cho tour đang mở bán.",
                }

    if allowed_tours and normalized_tour and normalized_tour not in allowed_tours:
        return {
            "ok": False,
            "voucher": voucher,
            "code": code,
            "discount": 0,
            "message": f"Mã này chỉ áp dụng cho tour: {', '.join(allowed_tours)}.",
        }

    if allowed_tours and not normalized_tour:
        return {
            "ok": False,
            "voucher": voucher,
            "code": code,
            "discount": 0,
            "message": "Cần chọn tour trước khi áp dụng mã giảm giá này.",
        }

    if user_limit > 0:
        normalized_username = str(username or "").strip()
        if not normalized_username:
            return {
                "ok": False,
                "voucher": voucher,
                "code": code,
                "discount": 0,
                "message": "Mã này yêu cầu gắn với tài khoản khách hàng cụ thể.",
            }
        if usage["user_uses"] >= user_limit:
            return {
                "ok": False,
                "voucher": voucher,
                "code": code,
                "discount": 0,
                "message": f"Tài khoản này đã dùng mã tối đa {user_limit} lần.",
            }

    discount_amount = resolve_voucher_discount(voucher, gross_total)
    if discount_amount <= 0:
        return {"ok": False, "voucher": voucher, "code": code, "discount": 0, "message": "Mã giảm giá không hợp lệ."}

    success_parts = [f"Áp dụng {code} thành công, giảm {discount_amount:,}đ.".replace(",", ".")]
    if user_limit > 0:
        success_parts.append(f"Còn {max(user_limit - usage['user_uses'] - 1, 0)} lượt cho tài khoản này.")
    if allowed_tours:
        success_parts.append("Phạm vi: " + ", ".join(allowed_tours))

    return {
        "ok": True,
        "voucher": voucher,
        "code": code,
        "discount": discount_amount,
        "message": " ".join(success_parts),
        "remaining": remaining,
        "user_limit": user_limit,
        "allowed_tours": allowed_tours,
    }

# ===== BEGIN core/notification_service.py =====

from datetime import datetime


EVENT_BOOKING_CREATED = "booking_created"
EVENT_PAYMENT_SUCCESS = "payment_success"
EVENT_TOUR_CANCELLED = "tour_cancelled"
EVENT_GUIDE_ASSIGNED = "guide_assigned"
EVENT_TOUR_COMPLETED = "tour_completed"


def _notifications(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_notifications` ( notifications).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return getattr(datastore, "list_notifications", datastore.notifications)


def _tour_name(datastore, ma_tour: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_tour_name` ( tour name).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return ""
    return str(tour.get("ten", "")).strip()


def _guide_name(datastore, ma_hdv: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_guide_name` ( guide name).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    guide = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
    if not isinstance(guide, dict):
        return ""
    return str(guide.get("tenHDV", "")).strip()


def emit_notification(
    datastore,
    *,
    event_type: str,
    content: str,
    ma_tour: str = "",
    ma_hdv: str = "",
    persist: bool = False,
    username: str = "",
    ma_booking: str = "",
) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `emit_notification` (emit notification).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        event_type: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        content: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tên đăng nhập của khách hàng nhận thông báo (tùy chọn).
        ma_booking: Mã booking liên quan đến thông báo (tùy chọn).
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    payload = {
        "eventType": str(event_type or "").strip(),
        "maHDV": str(ma_hdv or "").strip(),
        "tenHDV": _guide_name(datastore, ma_hdv),
        "maTour": str(ma_tour or "").strip(),
        "tenTour": _tour_name(datastore, ma_tour),
        "content": str(content or "").strip(),
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    if username:
        payload["username"] = str(username).strip()
    if ma_booking:
        payload["maBooking"] = str(ma_booking).strip()
    _notifications(datastore).append(payload)
    if persist:
        datastore.save()
    return payload


def notify_booking_created(datastore, booking: dict, tour: dict, *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_booking_created` (notify booking created).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return emit_notification(
        datastore,
        event_type=EVENT_BOOKING_CREATED,
        ma_tour=str(booking.get("maTour", "")),
        ma_hdv=str(tour.get("hdvPhuTrach", "")),
        content=(
            f"Booking {booking.get('maBooking', '')} vừa được tạo cho tour "
            f"{tour.get('ten', booking.get('maTour', ''))}."
        ),
        persist=persist,
    )


def notify_payment_success(datastore, booking: dict, *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_payment_success` (notify payment success).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return emit_notification(
        datastore,
        event_type=EVENT_PAYMENT_SUCCESS,
        ma_tour=str(booking.get("maTour", "")),
        content=(
            f"Booking {booking.get('maBooking', '')} đã thanh toán "
            f"{int(booking.get('daThanhToan', 0)):,}đ.".replace(",", ".")
        ),
        persist=persist,
    )


def notify_tour_cancelled(datastore, tour: dict, reason: str = "", *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_tour_cancelled` (notify tour cancelled).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        reason: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    detail = f" Lý do: {reason.strip()}" if str(reason or "").strip() else ""
    return emit_notification(
        datastore,
        event_type=EVENT_TOUR_CANCELLED,
        ma_tour=str(tour.get("ma", "")),
        ma_hdv=str(tour.get("hdvPhuTrach", "")),
        content=f"Tour {tour.get('ten', tour.get('ma', ''))} đã bị hủy.{detail}",
        persist=persist,
    )


def notify_guide_assigned(datastore, tour: dict, guide: dict, *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_guide_assigned` (notify guide assigned).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        guide: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return emit_notification(
        datastore,
        event_type=EVENT_GUIDE_ASSIGNED,
        ma_tour=str(tour.get("ma", "")),
        ma_hdv=str(guide.get("maHDV", "")),
        content=(
            f"HDV {guide.get('tenHDV', guide.get('maHDV', ''))} được phân công cho "
            f"tour {tour.get('ten', tour.get('ma', ''))}."
        ),
        persist=persist,
    )


def notify_tour_completed(datastore, tour: dict, *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_tour_completed` (notify tour completed).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return emit_notification(
        datastore,
        event_type=EVENT_TOUR_COMPLETED,
        ma_tour=str(tour.get("ma", "")),
        ma_hdv=str(tour.get("hdvPhuTrach", "")),
        content=f"Tour {tour.get('ten', tour.get('ma', ''))} đã kết thúc.",
        persist=persist,
    )


def check_and_create_departure_notifications(datastore):
    """
    Quét và tạo cảnh báo đi tour tự động gửi đến Admin và HDV phụ trách đúng 2 ngày trước ngày khởi hành.
    """
    tours = getattr(datastore, "list_tours", getattr(datastore, "data", {}).get("tours", []))
    today_local = datetime.now().date()

    for tour in tours:
        if not isinstance(tour, dict):
            continue
        ma_tour = str(tour.get("ma", "")).strip()
        if not ma_tour:
            continue
        status = normalize_tour_status(tour.get("trangThai", ""))
        if status == TOUR_STATUS_CANCELLED:
            continue

        start_date = parse_ddmmyyyy(tour.get("ngay"))
        if not start_date:
            continue

        days_diff = (start_date - today_local).days
        if days_diff == 2:
            exists = False
            notifications_list = getattr(datastore, "list_notifications", getattr(datastore, "data", {}).get("notifications", []))
            for notif in notifications_list:
                if notif.get("eventType") == "TOUR_DEPARTURE_WARNING" and str(notif.get("maTour", "")).strip().upper() == ma_tour.upper():
                    exists = True
                    break
            if not exists:
                ma_hdv = str(tour.get("hdvPhuTrach", "")).strip()
                ten_hdv = ""
                if ma_hdv:
                    guide = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
                    if guide:
                        ten_hdv = str(guide.get("tenHDV", "")).strip()

                ten_tour = str(tour.get("ten", "")).strip()
                ngay_di_str = tour.get("ngay", "")

                content = (
                    f"Nhắc lịch: Tour {ma_tour} ({ten_tour}) khởi hành vào {ngay_di_str}. "
                    f"HDV phụ trách: {ten_hdv or 'Chưa phân công'} ({ma_hdv or 'N/A'}). "
                    f"Yêu cầu chuẩn bị và kiểm tra lịch trình."
                )

                emit_notification(
                    datastore,
                    event_type="TOUR_DEPARTURE_WARNING",
                    content=content,
                    ma_tour=ma_tour,
                    ma_hdv=ma_hdv,
                    persist=True
                )


def sync_completed_tour_bookings(datastore) -> bool:
    """
    Mục đích:
        Duyệt danh sách bookings, tự động chuyển trạng thái booking sang 'Đã hoàn thành'
        nếu tour liên quan có trạng thái 'Đã kết thúc' hoặc tourState == 'completed'.
        Tạo notification cho user và lưu lại thay đổi.
    Tham số:
        datastore: Đối tượng lưu trữ dữ liệu JSONDataStore/SQLiteDataStore.
    Giá trị trả về:
        True nếu có thay đổi và đã lưu thành công, ngược lại False.
    """
    datastore.load()
    bookings = getattr(datastore, "list_bookings", datastore.data.get("bookings", []))
    notifications = getattr(datastore, "list_notifications", datastore.notifications)
    has_changed = False

    for booking in bookings:
        if not isinstance(booking, dict):
            continue
        ma_tour = str(booking.get("maTour", "")).strip().upper()
        if not ma_tour:
            continue
        
        tour = datastore.find_tour(ma_tour)
        if not tour or not isinstance(tour, dict):
            continue

        tour_status = str(tour.get("trangThai", "")).strip()
        tour_state = str(tour.get("tourState", "")).strip()

        # Kiểm tra xem tour có kết thúc hay không
        if tour_status == "Đã kết thúc" or tour_state == "completed":
            booking_status = str(booking.get("trangThai", "")).strip()
            
            # Chỉ chuyển booking sang "Đã hoàn thành" nếu trạng thái hiện tại là "Đã cọc" hoặc "Đã thanh toán"
            if booking_status in {"Đã cọc", "Đã thanh toán"}:
                booking["trangThai"] = "Đã hoàn thành"
                booking["bookingState"] = "completed"
                has_changed = True

            # Tạo notification hoàn thành tour cho user nếu booking ở trạng thái "Đã hoàn thành"
            if booking.get("trangThai") == "Đã hoàn thành":
                username = str(booking.get("username", booking.get("usernameDat", ""))).strip()
                ma_booking = str(booking.get("maBooking", "")).strip()
                ten_tour = str(tour.get("ten", "")).strip()

                # Kiểm tra xem đã tạo notification chưa
                already_notified = booking.get("completedNotified") == True
                if not already_notified:
                    # Chống trùng bằng cách quét danh sách notifications hiện tại
                    for n in notifications:
                        if (
                            str(n.get("eventType", "")).strip() == "tour_completed"
                            and str(n.get("username", "")).strip() == username
                            and str(n.get("maBooking", "")).strip() == ma_booking
                            and str(n.get("maTour", "")).strip() == ma_tour
                        ):
                            already_notified = True
                            booking["completedNotified"] = True
                            has_changed = True
                            break

                if not already_notified:
                    # Tạo nội dung thông báo
                    content = f"Tour {ten_tour} của booking {ma_booking} đã hoàn thành. Cảm ơn bạn đã sử dụng dịch vụ. Bạn có thể đánh giá tour/HDV ngay bây giờ."
                    emit_notification(
                        datastore,
                        event_type="tour_completed",
                        content=content,
                        ma_tour=ma_tour,
                        username=username,
                        ma_booking=ma_booking,
                        persist=False
                    )
                    booking["completedNotified"] = True
                    has_changed = True

    if has_changed:
        datastore.save()

    return has_changed


def get_guide_assigned_tours(datastore, actor: str = "", role: str = "guide", include_history: bool = True) -> list[dict]:
    tours = getattr(datastore, "list_tours", datastore.data.get("tours", []))
    if _is_admin_role(role):
        return list(tours)
    if not _is_guide_role(role):
        return []
    guide_id = str(actor or "").strip()
    results = []
    for tour in tours:
        if not guide_assigned_to_tour(guide_id, tour):
            continue
        tour_status = normalize_tour_status(tour.get("trangThai", ""), default=TOUR_STATUS_NOT_OPEN)
        if not include_history and tour_status in {TOUR_STATUS_COMPLETED, TOUR_STATUS_CANCELLED}:
            continue
        results.append(tour)
    return results


def get_guide_tour_customers(
    datastore,
    ma_tour: str,
    actor: str = "",
    role: str = "guide",
    include_financial: bool = False,
) -> list[dict]:
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return []
    if not guide_can_access_tour(actor, role, tour):
        return []
    allowed_statuses = {"Đã cọc", "Đã thanh toán", "Đã hoàn thành"}
    rows = []
    for booking in getattr(datastore, "list_bookings", datastore.data.get("bookings", [])):
        if str(booking.get("maTour", "")).strip().upper() != str(ma_tour or "").strip().upper():
            continue
        status = str(booking.get("trangThai", "")).strip()
        if status not in allowed_statuses:
            continue
        row = {
            "maBooking": str(booking.get("maBooking", "")).strip(),
            "tenKhach": str(booking.get("tenKhach", "")).strip(),
            "sdt": str(booking.get("sdt", "")).strip(),
            "soNguoi": max(0, safe_int(booking.get("soNguoi", 0))),
            "ghiChu": str(booking.get("ghiChu", "")).strip(),
            "danhSachKhach": booking.get("danhSachKhach", []),
            "trangThai": status,
        }
        if include_financial:
            row["tongTien"] = max(0, safe_int(booking.get("tongTien", 0)))
            row["daThanhToan"] = max(0, safe_int(booking.get("daThanhToan", 0)))
            row["conNo"] = max(0, safe_int(booking.get("conNo", 0)))
        rows.append(row)
    return rows


def send_guide_notification(
    datastore,
    *,
    ma_tour: str,
    content: str,
    actor: str = "",
    role: str = "guide",
    title: str = "",
) -> dict:
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return {"success": False, "message": "Không tìm thấy tour cần gửi thông báo."}
    if not guide_can_access_tour(actor, role, tour):
        return {"success": False, "message": "Bạn không có quyền gửi thông báo cho tour này."}

    tour_status = normalize_tour_status(tour.get("trangThai", ""), default=TOUR_STATUS_NOT_OPEN)
    if tour_status == TOUR_STATUS_CANCELLED:
        return {"success": False, "message": f"Tour đang ở trạng thái '{tour_status}', không thể gửi thông báo."}
    if tour_status == TOUR_STATUS_COMPLETED:
        return {"success": False, "message": "Tour đã kết thúc, chỉ cho phép xem lịch sử."}

    body = str(content or "").strip()
    if not body:
        return {"success": False, "message": "Nội dung thông báo không được để trống."}
    title_text = str(title or "").strip()
    if title and not title_text:
        return {"success": False, "message": "Tiêu đề thông báo không hợp lệ."}

    recipients = get_guide_tour_customers(datastore, ma_tour, actor=actor, role=role, include_financial=False)
    if not recipients:
        return {"success": False, "message": "Không có khách hợp lệ để nhận thông báo."}

    ma_hdv = str(
        tour.get("hdvPhuTrach")
        or tour.get("maHDV")
        or tour.get("guideId")
        or actor
        or ""
    ).strip()
    message = f"{title_text}: {body}" if title_text else body
    payload = emit_notification(
        datastore,
        event_type="guide_message",
        ma_tour=str(tour.get("ma", "")).strip(),
        ma_hdv=ma_hdv,
        content=message,
        persist=False,
    )
    payload["nguoiGui"] = str(actor or ma_hdv).strip()
    payload["vaiTroNguoiGui"] = "guide" if not _is_admin_role(role) else "admin"
    payload["thoiGianGui"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    payload["noiDung"] = body
    payload["tieuDe"] = title_text
    payload["soNguoiNhan"] = len(recipients)
    datastore.save()
    return {"success": True, "message": "Gửi thông báo thành công.", "notification": payload}


def get_notifications_for_user(datastore, username: str, role: str = "user", actor: str = "") -> list[dict]:
    normalized = str(username or actor or "").strip().lower()
    if not normalized:
        return []
    if _is_admin_role(role):
        return list(getattr(datastore, "list_notifications", datastore.data.get("notifications", [])))
    if not _is_customer_role(role):
        return []

    my_tours = {
        str(booking.get("maTour", "")).strip()
        for booking in getattr(datastore, "list_bookings", datastore.data.get("bookings", []))
        if booking_belongs_to_user(booking, normalized)
    }
    results = []
    for notification in getattr(datastore, "list_notifications", datastore.data.get("notifications", [])):
        if bool(notification.get("internalOnly")) or str(notification.get("phamVi", "")).strip().lower() in {"internal", "noi bo", "nội bộ"}:
            continue
        ma_tour = str(notification.get("maTour", "")).strip()
        notif_user = str(notification.get("username", "")).strip().lower()
        if (ma_tour and ma_tour in my_tours) or (notif_user and notif_user == normalized):
            results.append(notification)
    return results


def get_reviews_for_guide(datastore, guide_id: str, actor: str = "", role: str = "guide") -> list[dict]:
    target_guide = str(guide_id or "").strip().upper()
    if not target_guide:
        return []
    if not (_is_admin_role(role) or _is_guide_role(role)):
        return []
    if _is_guide_role(role) and str(actor or "").strip().upper() != target_guide:
        return []
    reviews = getattr(datastore, "list_reviews", datastore.reviews)
    rows = []
    for review in reviews:
        review_status = str(review.get("trangThai", "")).strip().lower()
        if review_status in {"hidden", "deleted", "archived", "đã ẩn", "da an"}:
            continue
        if str(review.get("target", "")).strip().lower() not in {"hdv", "guide"}:
            continue
        ma_hdv = str(review.get("maHDV", "") or review.get("target_id", "")).strip().upper()
        if ma_hdv != target_guide:
            continue
        if str(review.get("trangThai", "")).strip().lower() in {"deleted", "hidden", "archived", "da an", "đã ẩn"}:
            continue
        normalized_rating = _normalize_review_rating(review.get("rating"))
        review["rating"] = normalized_rating if normalized_rating not in (None, "") else review.get("rating", "")
        rows.append(review)
    return rows


def update_tour_operational_note(
    datastore,
    *,
    ma_tour: str,
    note: str,
    actor: str = "",
    role: str = "guide",
) -> dict:
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return {"success": False, "message": "Không tìm thấy tour để cập nhật ghi chú."}
    if not (_is_admin_role(role) or guide_can_access_tour(actor, role, tour)):
        return {"success": False, "message": "Bạn không có quyền cập nhật ghi chú tour này."}

    tour_status = normalize_tour_status(tour.get("trangThai", ""), default=TOUR_STATUS_NOT_OPEN)
    if tour_status == TOUR_STATUS_CANCELLED:
        return {"success": False, "message": "Tour đã hủy, không thể cập nhật ghi chú vận hành."}
    if tour_status not in {TOUR_STATUS_STARTED, TOUR_STATUS_COMPLETED} and not _is_admin_role(role):
        return {"success": False, "message": "Chỉ cho phép cập nhật ghi chú khi tour đang diễn ra hoặc đã kết thúc."}

    text = str(note or "").strip()
    if not text:
        return {"success": False, "message": "Nội dung ghi chú không được để trống."}

    current = str(tour.get("ghiChuDieuHanh", "") or "").strip()
    stamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    author = str(actor or "system").strip() or "system"
    tour["ghiChuDieuHanh"] = f"{current}\n[{stamp}] {author}: {text}".strip()
    datastore.save()
    return {"success": True, "message": "Đã cập nhật ghi chú vận hành.", "tour": tour}


# ===== BEGIN core/review_service.py =====

from dataclasses import dataclass
from datetime import datetime
import unicodedata



@dataclass(slots=True)
class ReviewResult:
    success: bool
    message: str
    review: dict | None = None
    level: str = "info"


def _find_booking(datastore, ma_booking: str):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_booking` ( find booking).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    target = str(ma_booking or "").strip()
    for booking in getattr(datastore, "list_bookings", datastore.data.get("bookings", [])):
        if str(booking.get("maBooking", "")).strip() == target:
            return booking
    return None


def _safe_float(value, default: float = 0.0) -> float:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_safe_float` ( safe float).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _normalize_review_rating(rating_value):
    if rating_value is None or rating_value == "":
        return ""
    if isinstance(rating_value, dict):
        skill = _safe_float(rating_value.get("skill"), -1)
        attitude = _safe_float(rating_value.get("attitude"), -1)
        problem = _safe_float(rating_value.get("problem"), -1)
        if min(skill, attitude, problem) < 0:
            return None
        score_20 = max(0.0, min(20.0, skill)) + max(0.0, min(20.0, attitude)) + max(0.0, min(20.0, problem))
        normalized = round((score_20 / 60.0) * 5.0, 1)
        return max(1.0, min(5.0, normalized))

    numeric = _safe_float(rating_value, -1)
    if numeric < 0:
        return None
    if 0 < numeric <= 1:
        numeric = round(numeric * 5.0, 1)
    if numeric > 5:
        # Backward-compatibility: support legacy 1-20 and 1-60 scales.
        if numeric <= 20:
            numeric = round((numeric / 20.0) * 5.0, 1)
        else:
            numeric = round((min(numeric, 60.0) / 60.0) * 5.0, 1)
    if not 1 <= numeric <= 5:
        return None
    return round(numeric, 1)


def _update_guide_metrics(datastore, ma_hdv: str, rating: float) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_update_guide_metrics` ( update guide metrics).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        rating: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not ma_hdv:
        return
    guide = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
    if not isinstance(guide, dict):
        return

    reviews = getattr(datastore, "list_reviews", datastore.reviews)
    ratings: list[float] = []
    for review in reviews:
        if str(review.get("target", "")).strip().lower() not in {"hdv", "guide"}:
            continue
        if str(review.get("maHDV", "")).strip() != ma_hdv and str(review.get("target_id", "")).strip() != ma_hdv:
            continue
        value = review.get("rating")
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if 1 <= numeric <= 5:
            ratings.append(numeric)

    try:
        numeric_input = float(rating)
    except (TypeError, ValueError):
        numeric_input = -1
    if not ratings and 1 <= numeric_input <= 5:
        ratings.append(numeric_input)

    total = len(ratings)
    guide["total_reviews"] = total
    guide["avg_rating"] = round(sum(ratings) / total, 1) if total else 0


def find_review_by_id(datastore, ma_review):
    target = str(ma_review or "").strip().upper()
    if not target:
        return None
    for review in getattr(datastore, "list_reviews", getattr(datastore, "reviews", [])):
        if str(review.get("maReview", "")).strip().upper() == target:
            return review
    return None


def is_review_hidden(review) -> bool:
    if not review:
        return False
    return bool(review.get("hidden", False)) or str(review.get("trangThai", "")).strip() == "Đã ẩn"


def normalize_review_for_display(review, datastore=None):
    normalized = normalize_review_item(review or {}, include_rating=True, include_ma_hdv=True)
    ma_tour = str(normalized.get("maTour", "")).strip()
    ma_hdv = str(normalized.get("maHDV", "") or normalized.get("target_id", "")).strip()
    if datastore is not None:
        if ma_tour and not normalized.get("tenTour") and hasattr(datastore, "find_tour"):
            tour = datastore.find_tour(ma_tour)
            if isinstance(tour, dict):
                normalized["tenTour"] = str(tour.get("ten", "")).strip()
        if ma_hdv and not normalized.get("tenHDV") and hasattr(datastore, "find_hdv"):
            guide = datastore.find_hdv(ma_hdv)
            if isinstance(guide, dict):
                normalized["tenHDV"] = str(guide.get("tenHDV", "")).strip()
    
    # Resolve customer name if missing or blank
    username = normalized.get("username", "")
    if not normalized.get("fullname") and datastore is not None and username:
        user_info = datastore.find_user(username) if hasattr(datastore, "find_user") else None
        if not user_info and hasattr(datastore, "data"):
            users_list = datastore.data.get("users", [])
            user_info = next((u for u in users_list if str(u.get("username", "")).strip().lower() == str(username).strip().lower()), None)
        if user_info:
            normalized["fullname"] = str(user_info.get("fullname", user_info.get("name", ""))).strip()
            
    normalized["adminReply"] = str((review or {}).get("adminReply", "")).strip()
    normalized["adminReplyDate"] = str((review or {}).get("adminReplyDate", "")).strip()
    normalized["adminReplyBy"] = str((review or {}).get("adminReplyBy", "")).strip()
    
    # Hidden details fallback
    normalized["hiddenReason"] = str((review or {}).get("hiddenReason", "")).strip()
    normalized["hiddenDate"] = str((review or {}).get("hiddenDate", "")).strip()
    normalized["hiddenBy"] = str((review or {}).get("hiddenBy", "")).strip()
    
    # Status
    trang_thai = str((review or {}).get("trangThai", "")).strip()
    if not trang_thai:
        trang_thai = "Đã ẩn" if bool((review or {}).get("hidden", False)) else "Hiển thị"
    normalized["trangThai"] = trang_thai
    return normalized


def save_reviews(datastore):
    datastore.save()


def create_review_notification(
    datastore,
    username,
    content,
    ma_review="",
    ma_tour="",
    ten_tour="",
    ma_booking="",
):
    payload = emit_notification(
        datastore,
        event_type="review_reply",
        username=str(username or "").strip(),
        content=str(content or "").strip(),
        ma_tour=str(ma_tour or "").strip(),
        ma_booking=str(ma_booking or "").strip(),
        persist=False,
    )
    payload["maReview"] = str(ma_review or "").strip()
    if ten_tour:
        payload["tenTour"] = str(ten_tour or "").strip()
    return payload


def recalculate_hdv_review_stats(datastore, ma_hdv):
    guide_id = str(ma_hdv or "").strip()
    if not guide_id:
        return None
    guide = datastore.find_hdv(guide_id) if hasattr(datastore, "find_hdv") else None
    if not isinstance(guide, dict):
        return None

    ratings = []
    for review in getattr(datastore, "list_reviews", getattr(datastore, "reviews", [])):
        status = _normalize_key(review.get("trangThai", ""))
        if status in {"hidden", "deleted", "archived", "da an", "đã ẩn", "xoa", "đã xóa"}:
            continue
        if str(review.get("target", "")).strip().lower() not in {"hdv", "guide"}:
            continue
        review_hdv = str(review.get("maHDV", "") or review.get("target_id", "")).strip()
        if review_hdv.upper() != guide_id.upper():
            continue
        rating = _normalize_review_rating(review.get("rating"))
        if isinstance(rating, (int, float)) and 1 <= float(rating) <= 5:
            ratings.append(float(rating))

    guide["total_reviews"] = len(ratings)
    guide["avg_rating"] = round(sum(ratings) / len(ratings), 1) if ratings else 0
    return guide


def _next_review_code(datastore) -> str:
    """
    Mục đích:
        Sinh mã đánh giá kế tiếp theo dạng REVxx.
    """
    existing_ids = []
    for review in getattr(datastore, "list_reviews", datastore.reviews):
        code = str(review.get("maReview", "")).strip().upper()
        if not code.startswith("REV"):
            continue
        suffix = code[3:]
        if not suffix.isdigit():
            continue
        existing_ids.append(int(suffix))
    return f"REV{max(existing_ids, default=0) + 1:02d}"


def create_review(
    datastore,
    *,
    username: str,
    fullname: str,
    ma_booking: str,
    content: str,
    target: str = "Tour",
    target_id: str = "",
    rating: float | None = None,
) -> ReviewResult:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_review` (create review).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        content: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        target: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        target_id: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        rating: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return ReviewResult(False, "Không tìm thấy booking để đánh giá.", level="error")

    owner = str(booking.get("usernameDat", "")).strip().lower()
    if owner and owner != str(username or "").strip().lower():
        return ReviewResult(False, "Bạn không có quyền đánh giá booking này.", level="warning")
    user_record = datastore.find_user(username) if hasattr(datastore, "find_user") else None
    if isinstance(user_record, dict) and not is_user_active(user_record):
        return ReviewResult(False, "Tài khoản của bạn đang bị khóa hoặc tạm ngừng hoạt động.", level="warning")

    booking_status = str(booking.get("trangThai", "")).strip()
    if booking_status in {"Mới tạo", "Đã cọc", "Đã thanh toán", "Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}:
        return ReviewResult(False, "Booking ở trạng thái hiện tại không được phép đánh giá.", level="warning")

    booking_state = booking_state_from_status(
        booking_status,
        str(booking.get("trangThaiHoanTien", "")).strip(),
    )
    if booking_state in {BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED}:
        return ReviewResult(False, "Booking đã hủy/hoàn tiền nên không thể đánh giá.", level="warning")
    ma_tour = str(booking.get("maTour", "")).strip()
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    tour_status = normalize_tour_status(str((tour or {}).get("trangThai", "")).strip(), default=TOUR_STATUS_NOT_OPEN)
    if booking_state != BOOKING_STATE_COMPLETED and tour_status != TOUR_STATUS_COMPLETED:
        return ReviewResult(False, "Chỉ booking đã hoàn thành hoặc tour đã kết thúc mới được đánh giá.", level="warning")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        return ReviewResult(False, "Nội dung đánh giá không được để trống.", level="warning")
    if len(normalized_content) > 2000:
        return ReviewResult(False, "Nội dung đánh giá quá dài (tối đa 2000 ký tự).", level="warning")

    booking_code = str(ma_booking or "").strip()
    normalized_user = str(username or "").strip().lower()
    target_key = str(target or "").strip().lower()
    ten_hdv = ""
    if target_key in {"hdv", "guide"}:
        final_target = "HDV"
        if not target_id:
            target_id = str(tour.get("hdvPhuTrach", "")).strip() if isinstance(tour, dict) else ""
        if not target_id:
            return ReviewResult(False, "Tour này chưa có HDV để đánh giá.", level="warning")
        ma_hdv = str(target_id).strip()
        guide = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
        if guide:
            ten_hdv = str(guide.get("tenHDV", "")).strip()
    else:
        final_target = "Tour"
        ma_hdv = ""
        target_id = ma_tour

    for existing in getattr(datastore, "list_reviews", datastore.reviews):
        existing_booking = str(existing.get("maBooking", "")).strip()
        existing_user = str(existing.get("username", "")).strip().lower()
        existing_target = str(existing.get("target", "")).strip().lower()
        if existing_booking == booking_code and existing_user == normalized_user and existing_target == final_target.lower():
            return ReviewResult(False, f"Booking này đã có đánh giá cho mục {final_target}.", level="warning")

    final_rating = _normalize_review_rating(rating)
    if final_rating is None:
        return ReviewResult(False, "Điểm đánh giá phải nằm trong khoảng từ 1 đến 5.", level="warning")
    review = {
        "maReview": _next_review_code(datastore),
        "username": str(username or "").strip(),
        "fullname": str(fullname or "").strip() or str(booking.get("tenKhach", "")).strip(),
        "target": final_target,
        "target_id": str(target_id or "").strip(),
        "content": normalized_content,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "rating": final_rating,
        "maBooking": booking_code,
        "maTour": ma_tour,
        "maHDV": ma_hdv,
        "tenHDV": ten_hdv,
    }
    getattr(datastore, "list_reviews", datastore.reviews).append(review)

    if final_target == "HDV" and isinstance(final_rating, float):
        _update_guide_metrics(datastore, ma_hdv, final_rating)

    datastore.save()
    return ReviewResult(True, "Đã ghi nhận đánh giá thành công.", review=review)


# ===== BEGIN core/reporting.py =====



def _iter_bookings(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_iter_bookings` ( iter bookings).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return getattr(datastore, "list_bookings", datastore.data.get("bookings", []))


def _iter_tours(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_iter_tours` ( iter tours).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return getattr(datastore, "list_tours", datastore.data.get("tours", []))


def _find_tour_name(datastore, ma_tour):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_tour_name` ( find tour name).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    finder = getattr(datastore, "find_tour", None)
    if callable(finder):
        tour = finder(ma_tour)
        if tour:
            return str(tour.get("ten", "")).strip()

    for tour in _iter_tours(datastore):
        if str(tour.get("ma", "")).strip() == str(ma_tour or "").strip():
            return str(tour.get("ten", "")).strip()
    return ""


def _revenue_booking(booking, datastore=None) -> bool:
    """
    Mục đích:
        Xác định xem booking có phát sinh doanh thu hay không.
    """
    paid = max(0, safe_int(booking.get("daThanhToan", 0)))
    status = str(booking.get("trangThai", "")).strip()
    if paid > 0:
        return True
    if status not in CANCEL_BOOKING_STATUSES:
        return True
    return False


def _booking_gross_refund_net(booking, datastore=None) -> tuple[int, int, int]:
    paid = max(0, safe_int(booking.get("daThanhToan", 0)))
    refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
    if refund_status == "Từ chối":
        refunded = 0
    else:
        refunded = max(0, safe_int(booking.get("soTienHoan", 0)))
    refunded = min(refunded, paid)
    net = max(paid - refunded, 0)
    return paid, refunded, net


def _month_key(date_text):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_month_key` ( month key).
    Tham số:
        date_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        _day, month, year = str(date_text or "").strip().split("/")
        return f"{year}-{month}"
    except ValueError:
        return "Không rõ"


def _quarter_key(month_key):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_quarter_key` ( quarter key).
    Tham số:
        month_key: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if month_key == "Không rõ":
        return month_key

    year_text, month_text = month_key.split("-")
    month = max(1, min(12, safe_int(month_text, 1)))
    quarter = ((month - 1) // 3) + 1
    return f"{year_text}-Q{quarter}"


def _find_tour_name_with_booking(datastore, ma_tour, booking=None):
    if booking and booking.get("tenTour"):
        return str(booking.get("tenTour")).strip()
    name = _find_tour_name(datastore, ma_tour)
    return name if name else "Tour đã xóa"


def build_revenue_report(datastore, actor: str = "", role: str = "admin", month: str = None, year: str = None, query: str = None) -> dict:
    if not _is_admin_role(role):
        return {
            "overview": {
                "tongBooking": 0,
                "bookingHieuLuc": 0,
                "tongPhaiThu": 0,
                "doanhThuDuKien": 0,
                "daThu": 0,
                "conNo": 0,
                "dangChoHoan": 0,
                "soTienChoHoan": 0,
                "doanhThuGop": 0,
                "tongHoanTien": 0,
                "doanhThuThuan": 0,
            },
            "by_tour": [],
            "by_month": [],
            "by_quarter": [],
            "booking_details": [],
        }

    by_tour = {}
    by_month = {}
    by_quarter = {}

    overview = {
        "tongBooking": 0,
        "bookingHieuLuc": 0,
        "tongPhaiThu": 0,
        "doanhThuDuKien": 0,
        "daThu": 0,
        "conNo": 0,
        "dangChoHoan": 0,
        "soTienChoHoan": 0,
        "doanhThuGop": 0,
        "tongHoanTien": 0,
        "doanhThuThuan": 0,
    }
    booking_details = []

    for booking in _iter_bookings(datastore):
        ma_tour = str(booking.get("maTour", "")).strip()

        # 1. Lọc theo mã hoặc tên tour (query)
        if query:
            q = str(query).strip().lower()
            tour_name_lower = _find_tour_name_with_booking(datastore, ma_tour, booking).lower()
            if q not in ma_tour.lower() and q not in tour_name_lower:
                continue

        # 2. Trích xuất tháng và năm từ ngayDat
        ngay_dat = str(booking.get("ngayDat", "")).strip()
        month_val = ""
        year_val = ""
        if ngay_dat:
            try:
                parts = ngay_dat.split("/")
                if len(parts) >= 3:
                    month_val = parts[1].zfill(2)
                    year_val = parts[2].split()[0]
            except Exception:
                pass

        # Lọc theo tháng
        if month and month != "Tất cả":
            if month_val != month.zfill(2):
                continue

        # Lọc theo năm
        if year and year != "Tất cả":
            if year_val != year:
                continue

        overview["tongBooking"] += 1

        month_key = _month_key(booking.get("ngayDat"))
        quarter_key = _quarter_key(month_key)

        people = max(0, safe_int(booking.get("soNguoi", 0)))
        total = max(0, calculate_booking_total(booking))
        paid = max(0, calculate_paid_amount(booking))
        refunded = max(0, calculate_refunded_amount(booking))
        debt = max(0, calculate_remaining_amount(booking))
        is_active = is_effective_booking(booking)
        status = str(booking.get("trangThai", "")).strip()

        if status == "Chờ hoàn tiền":
            overview["dangChoHoan"] += 1
            overview["soTienChoHoan"] += max(safe_int(booking.get("soTienHoan", 0)), paid)

        tour_id = ma_tour or "Không rõ"
        tour_row = by_tour.setdefault(
            tour_id,
            {
                "maTour": tour_id,
                "tenTour": _find_tour_name_with_booking(datastore, ma_tour, booking),
                "tongBooking": 0,
                "bookingHieuLuc": 0,
                "tongKhach": 0,
                "tongPhaiThu": 0,
                "daThu": 0,
                "daHoan": 0,
                "conNo": 0,
                "doanhThuThucNhan": 0,
            },
        )
        month_row = by_month.setdefault(
            month_key,
            {
                "ky": month_key,
                "tongBooking": 0,
                "bookingHieuLuc": 0,
                "tongKhach": 0,
                "tongPhaiThu": 0,
                "daThu": 0,
                "daHoan": 0,
                "conNo": 0,
                "doanhThuThucNhan": 0,
            },
        )
        quarter_row = by_quarter.setdefault(
            quarter_key,
            {
                "ky": quarter_key,
                "tongBooking": 0,
                "bookingHieuLuc": 0,
                "tongKhach": 0,
                "tongPhaiThu": 0,
                "daThu": 0,
                "daHoan": 0,
                "conNo": 0,
                "doanhThuThucNhan": 0,
            },
        )

        if is_active:
            overview["bookingHieuLuc"] += 1
            overview["tongPhaiThu"] += total
            overview["doanhThuDuKien"] += total
            overview["daThu"] += paid
            overview["conNo"] += debt
            overview["doanhThuGop"] += paid
            overview["doanhThuThuan"] += paid
            
            for row in (tour_row, month_row, quarter_row):
                row["bookingHieuLuc"] += 1
                row["tongPhaiThu"] += total
                row["daThu"] += paid
                row["conNo"] += debt
                row["doanhThuThucNhan"] += paid
        else:
            overview["daThu"] += paid
            overview["tongHoanTien"] += refunded
            overview["doanhThuThuan"] += (paid - refunded)
            
            for row in (tour_row, month_row, quarter_row):
                row["daThu"] += paid
                row["daHoan"] += refunded
                row["doanhThuThucNhan"] += (paid - refunded)

        for row in (tour_row, month_row, quarter_row):
            row["tongBooking"] += 1
            row["tongKhach"] += people

        booking_details.append(
            {
                "maBooking": str(booking.get("maBooking", "")).strip(),
                "maTour": ma_tour or "Không rõ",
                "tenTour": _find_tour_name_with_booking(datastore, ma_tour, booking),
                "username": str(booking.get("usernameDat", booking.get("username", ""))).strip(),
                "tenKhach": str(booking.get("tenKhach", "")).strip(),
                "date": ngay_dat,
                "trangThai": status,
                "hieuLuc": is_active,
                "tongPhaiThu": total if is_active else 0,
                "daThu": paid,
                "daHoan": refunded,
                "conNo": debt,
                "doanhThuThucNhan": paid - refunded,
                "hinhThucThanhToan": str(booking.get("hinhThucThanhToan", "Chuyển Khoản")).strip(),
            }
        )

    by_month_processed = []
    for k, row in by_month.items():
        if k == "Không rõ":
            row["month"] = ""
            row["year"] = ""
            row["label"] = "Không rõ thời gian"
        else:
            try:
                y, m = k.split("-")
                row["month"] = m
                row["year"] = y
                row["label"] = f"{m}/{y}"
            except Exception:
                row["month"] = ""
                row["year"] = ""
                row["label"] = "Không rõ thời gian"
        by_month_processed.append(row)

    def month_sort_key(row):
        ky = row["ky"]
        if ky == "Không rõ":
            return ("", "")
        return tuple(ky.split("-"))

    by_month_sorted = sorted(by_month_processed, key=month_sort_key, reverse=True)

    return {
        "overview": overview,
        "by_tour": sorted(by_tour.values(), key=lambda row: row["maTour"]),
        "by_month": by_month_sorted,
        "by_quarter": sorted(by_quarter.values(), key=lambda row: row["ky"]),
        "booking_details": booking_details,
    }

# ===== BEGIN core/booking_service.py =====

from dataclasses import dataclass
from datetime import datetime


TOUR_BOOKABLE_STATUSES = {TOUR_STATUS_OPEN}
TOUR_LOCK_CANCEL_STATUSES = {TOUR_STATUS_STARTED, TOUR_STATUS_COMPLETED, TOUR_STATUS_CANCELLED}
ADMIN_ROLES = {"admin", "administrator", "system"}
CUSTOMER_ROLES = {"user", "customer", "khach", "khách", "guest"}
GUIDE_ROLES = {"guide", "hdv", "huongdanvien"}

USER_STATUS_ACTIVE = "Đang hoạt động"
USER_STATUS_BLOCKED = "Đã khóa"
USER_STATUS_INACTIVE = "Ngừng hoạt động"
USER_STATUS_HIDDEN = "Đã ẩn"
GUIDE_STATUS_ACTIVE = "Đang hoạt động"
GUIDE_STATUS_TEMP_OFF = "Tạm nghỉ"
GUIDE_STATUS_INACTIVE = "Ngừng hoạt động"
GUIDE_STATUS_BLOCKED = "Đã khóa"
GUIDE_STATUS_HIDDEN = "Đã ẩn"

_USER_STATUS_MAP = {
    "active": USER_STATUS_ACTIVE,
    "đang hoạt động": USER_STATUS_ACTIVE,
    "hoat dong": USER_STATUS_ACTIVE,
    "dang hoat dong": USER_STATUS_ACTIVE,
    "sẵn sàng": USER_STATUS_ACTIVE,
    "san sang": USER_STATUS_ACTIVE,
    "đã khóa": USER_STATUS_BLOCKED,
    "da khoa": USER_STATUS_BLOCKED,
    "khóa": USER_STATUS_BLOCKED,
    "khoa": USER_STATUS_BLOCKED,
    "ngừng hoạt động": USER_STATUS_INACTIVE,
    "ngung hoat dong": USER_STATUS_INACTIVE,
    "inactive": USER_STATUS_INACTIVE,
    "đã ẩn": USER_STATUS_HIDDEN,
    "da an": USER_STATUS_HIDDEN,
    "hidden": USER_STATUS_HIDDEN,
}

_GUIDE_STATUS_MAP = {
    "đang hoạt động": GUIDE_STATUS_ACTIVE,
    "dang hoat dong": GUIDE_STATUS_ACTIVE,
    "active": GUIDE_STATUS_ACTIVE,
    "sẵn sàng": GUIDE_STATUS_ACTIVE,
    "san sang": GUIDE_STATUS_ACTIVE,
    "đã phân công": GUIDE_STATUS_ACTIVE,
    "da phan cong": GUIDE_STATUS_ACTIVE,
    "đang dẫn tour": GUIDE_STATUS_ACTIVE,
    "dang dan tour": GUIDE_STATUS_ACTIVE,
    "tạm nghỉ": GUIDE_STATUS_TEMP_OFF,
    "tam nghi": GUIDE_STATUS_TEMP_OFF,
    "ngừng hoạt động": GUIDE_STATUS_INACTIVE,
    "ngung hoat dong": GUIDE_STATUS_INACTIVE,
    "đã khóa": GUIDE_STATUS_BLOCKED,
    "da khoa": GUIDE_STATUS_BLOCKED,
    "đã ẩn": GUIDE_STATUS_HIDDEN,
    "da an": GUIDE_STATUS_HIDDEN,
}


@dataclass(slots=True)
class BookingResult:
    success: bool
    message: str
    booking: dict | None = None
    level: str = "info"


def _normalize_role_name(role: str | None) -> str:
    return str(role or "").strip().lower()


def _is_admin_role(role: str | None) -> bool:
    return _normalize_role_name(role) in ADMIN_ROLES


def _is_customer_role(role: str | None) -> bool:
    return _normalize_role_name(role) in CUSTOMER_ROLES


def _is_guide_role(role: str | None) -> bool:
    return _normalize_role_name(role) in GUIDE_ROLES


def is_admin_role(role: str | None) -> bool:
    return _is_admin_role(role)


def is_guide_role(role: str | None) -> bool:
    return _is_guide_role(role)


def is_customer_role(role: str | None) -> bool:
    return _is_customer_role(role)


def normalize_user_status(status: str | None) -> str:
    raw = str(status or "")
    key = _normalize_key(raw)
    key_ascii = _normalize_status_key(raw)
    if not key and not key_ascii:
        return USER_STATUS_ACTIVE
    normalized = _USER_STATUS_MAP.get(key) or _USER_STATUS_MAP.get(key_ascii)
    if normalized:
        return normalized
    if "khoa" in key_ascii:
        return USER_STATUS_BLOCKED
    if "ngung" in key_ascii or "inactive" in key_ascii:
        return USER_STATUS_INACTIVE
    if "an" == key_ascii or "hidden" in key_ascii:
        return USER_STATUS_HIDDEN
    return USER_STATUS_ACTIVE


def normalize_guide_status(status: str | None) -> str:
    raw = str(status or "")
    key = _normalize_key(raw)
    key_ascii = _normalize_status_key(raw)
    if not key and not key_ascii:
        return GUIDE_STATUS_ACTIVE
    normalized = _GUIDE_STATUS_MAP.get(key) or _GUIDE_STATUS_MAP.get(key_ascii)
    if normalized:
        return normalized
    if "tam" in key_ascii and "nghi" in key_ascii:
        return GUIDE_STATUS_TEMP_OFF
    if "khoa" in key_ascii:
        return GUIDE_STATUS_BLOCKED
    if "ngung" in key_ascii or "inactive" in key_ascii:
        return GUIDE_STATUS_INACTIVE
    if key_ascii == "an" or "hidden" in key_ascii:
        return GUIDE_STATUS_HIDDEN
    return GUIDE_STATUS_ACTIVE


def _normalize_status_key(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    raw = raw.replace("đ", "d").replace("Đ", "d").replace("?", " ")
    raw = "".join(
        ch for ch in unicodedata.normalize("NFD", raw) if unicodedata.category(ch) != "Mn"
    )
    cleaned = []
    for ch in raw:
        if ch.isalnum():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    return " ".join("".join(cleaned).split())


def is_user_active(user: dict | None) -> bool:
    if not isinstance(user, dict):
        return False
    status = normalize_user_status(user.get("trangThai", user.get("status", "")))
    return status == USER_STATUS_ACTIVE


def is_guide_active(guide: dict | None) -> bool:
    if not isinstance(guide, dict):
        return False
    status = normalize_guide_status(guide.get("trangThai", guide.get("status", "")))
    return status == GUIDE_STATUS_ACTIVE


def booking_belongs_to_user(booking: dict | None, username: str | None) -> bool:
    if not isinstance(booking, dict):
        return False
    owner = str(
        booking.get("usernameDat")
        or booking.get("username")
        or booking.get("user")
        or booking.get("userId")
        or ""
    ).strip().lower()
    actor = str(username or "").strip().lower()
    if not owner or not actor:
        return False
    return owner == actor


def guide_assigned_to_tour(guide: str | dict | None, tour: dict | None) -> bool:
    if not isinstance(tour, dict):
        return False
    if isinstance(guide, dict):
        guide_id = str(guide.get("maHDV", "") or guide.get("guideId", "") or "").strip().upper()
    else:
        guide_id = str(guide or "").strip().upper()
    if not guide_id:
        return False
    tour_guide = str(
        tour.get("hdvPhuTrach")
        or tour.get("maHDV")
        or tour.get("guideId")
        or tour.get("hdv")
        or ""
    ).strip().upper()
    return tour_guide == guide_id


def user_can_access_booking(actor: str | None, role: str | None, booking: dict | None) -> bool:
    if not isinstance(booking, dict):
        return False
    if _is_admin_role(role):
        return True
    if _is_customer_role(role):
        return booking_belongs_to_user(booking, actor)
    return False


def guide_can_access_tour(actor: str | None, role: str | None, tour: dict | None) -> bool:
    if not isinstance(tour, dict):
        return False
    if _is_admin_role(role):
        return True
    if not _is_guide_role(role):
        return False
    return guide_assigned_to_tour(actor, tour)


def guide_can_access_booking(actor: str | None, role: str | None, booking: dict | None, tour: dict | None = None) -> bool:
    if not isinstance(booking, dict):
        return False
    if _is_admin_role(role):
        return True
    if not _is_guide_role(role):
        return False
    target_tour = tour
    if not isinstance(target_tour, dict):
        target_tour = {"ma": str(booking.get("maTour", "")).strip(), "hdvPhuTrach": str(booking.get("maHDV", "")).strip()}
    return guide_can_access_tour(actor, role, target_tour)


def _can_manage_booking(booking: dict, actor: str | None, role: str | None) -> tuple[bool, str]:
    if _is_admin_role(role):
        return True, ""
    if _is_guide_role(role):
        return False, "Hướng dẫn viên không có quyền thao tác nghiệp vụ tài chính booking."
    if _is_customer_role(role):
        owner = str(booking.get("usernameDat", "")).strip().lower()
        actor_name = str(actor or "").strip().lower()
        if not actor_name:
            return False, "Thiếu thông tin người thao tác."
        if not owner:
            return False, "Booking thiếu thông tin chủ sở hữu, không thể thao tác từ tài khoản khách."
        if owner and owner != actor_name:
            return False, "Bạn không có quyền thao tác booking của tài khoản khác."
        return True, ""
    return False, "Bạn không có quyền thao tác booking này."


def _calc_refund_rate(days_before_departure: int | None, company_cancelled: bool) -> float:
    if company_cancelled:
        return 1.0
    if days_before_departure is None:
        return 1.0
    if days_before_departure >= 15:
        return 1.0
    if days_before_departure >= 7:
        return 0.7
    return 0.0


def _get_bookings(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_get_bookings` ( get bookings).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return getattr(datastore, "list_bookings", datastore.data.get("bookings", []))


def _find_tour(datastore, ma_tour):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_tour` ( find tour).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    finder = getattr(datastore, "find_tour", None)
    if callable(finder):
        result = finder(ma_tour)
        if result:
            return result

    return next(
        (
            tour
            for tour in getattr(datastore, "list_tours", datastore.data.get("tours", []))
            if str(tour.get("ma", "")).strip() == str(ma_tour or "").strip()
        ),
        None,
    )


def _find_booking(datastore, ma_booking):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_booking` ( find booking).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return next(
        (
            booking
            for booking in _get_bookings(datastore)
            if str(booking.get("maBooking", "")).strip() == str(ma_booking or "").strip()
        ),
        None,
    )


def can_hard_delete_booking(datastore, booking: dict | None) -> tuple[bool, str]:
    """
    Chỉ cho phép xóa vật lý booking khi chưa phát sinh dòng tiền
    và tour chưa đi vào giai đoạn cần lưu vết nghiệp vụ.
    """
    if not isinstance(booking, dict):
        return False, "Không tìm thấy booking hợp lệ để xóa."

    status = str(booking.get("trangThai", "")).strip()
    refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
    paid_amount = max(0, safe_int(booking.get("daThanhToan", 0)))
    deposit_amount = max(0, safe_int(booking.get("tienCoc", 0)))
    refund_amount = max(0, safe_int(booking.get("soTienHoan", 0)))

    tour = _find_tour(datastore, booking.get("maTour"))
    tour_status = normalize_tour_status(str((tour or {}).get("trangThai", "")).strip(), default=TOUR_STATUS_NOT_OPEN)
    if tour_status in {TOUR_STATUS_STARTED, TOUR_STATUS_COMPLETED, TOUR_STATUS_CANCELLED}:
        return False, f"Tour đang ở trạng thái '{tour_status}', không được xóa cứng booking."

    if status in {"Đã cọc", "Đã thanh toán", "Đã hoàn thành", "Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}:
        return False, f"Booking đang ở trạng thái '{status}', cần hủy theo nghiệp vụ thay vì xóa cứng."

    if paid_amount > 0 or deposit_amount > 0:
        return False, "Booking đã có giao dịch thanh toán/cọc, không được xóa cứng."
    if refund_amount > 0 or refund_status:
        return False, "Booking đã phát sinh thông tin hoàn tiền, không được xóa cứng."

    return True, ""


def _next_booking_code(datastore) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_next_booking_code` ( next booking code).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    existing_ids = []
    for booking in _get_bookings(datastore):
        ma_booking = str(booking.get("maBooking", "")).strip().upper()
        if not ma_booking.startswith("BK"):
            continue
        try:
            existing_ids.append(int(ma_booking[2:]))
        except ValueError:
            continue
    return f"BK{max(existing_ids, default=0) + 1:02d}"


def _payment_status(total_amount, paid_amount):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_payment_status` ( payment status).
    Tham số:
        total_amount: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        paid_amount: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    total = max(0, safe_int(total_amount))
    paid = max(0, safe_int(paid_amount))
    if paid <= 0:
        return "Mới tạo"
    if total > 0 and paid < total:
        return "Đã cọc"
    return "Đã thanh toán"


def _occupied_seats(datastore, ma_tour):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_occupied_seats` ( occupied seats).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    getter = getattr(datastore, "get_occupied_seats", None)
    if callable(getter):
        return max(0, safe_int(getter(ma_tour)))

    total = 0
    for booking in _get_bookings(datastore):
        refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
        if booking.get("maTour") != ma_tour:
            continue
        if booking.get("trangThai") in CANCEL_BOOKING_STATUSES and refund_status != "Từ chối":
            continue
        total += max(0, safe_int(booking.get("soNguoi", 0)))
    return total


def create_booking(
    datastore,
    *,
    ma_tour,
    num_people,
    pay_now,
    payment_method,
    username,
    fullname,
    phone,
    voucher_code="",
    danh_sach_khach=None,
    passenger_breakdown=None,
    source="Khách lẻ",
    note="",
    actor="",
    role="user",
):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_booking` (create booking).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        num_people: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        pay_now: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        payment_method: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        voucher_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        danh_sach_khach: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        passenger_breakdown: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        source: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized_fullname = normalize_fullname(fullname)
    normalized_phone = normalize_phone(phone)
    if len(normalized_fullname) < 3:
        return BookingResult(False, "Tên khách hàng quá ngắn.", level="warning")
    if not is_valid_phone(normalized_phone):
        return BookingResult(False, "Số điện thoại khách hàng không hợp lệ.", level="warning")

    tour = _find_tour(datastore, ma_tour)
    if not tour:
        return BookingResult(False, "Không tìm thấy tour đã chọn.", level="error")

    people = max(0, safe_int(num_people))
    if people <= 0:
        return BookingResult(False, "Số người đi không hợp lệ.", level="warning")
    if _is_guide_role(role):
        return BookingResult(False, "Hướng dẫn viên không có quyền tạo booking.", level="warning")
    if _is_customer_role(role):
        actor_name = str(actor or "").strip().lower()
        user_name = str(username or "").strip().lower()
        if not user_name:
            return BookingResult(False, "Vui lòng đăng nhập trước khi đặt tour.", level="warning")
        if actor_name and user_name and actor_name != user_name:
            return BookingResult(False, "Bạn chỉ được tạo booking cho chính tài khoản của mình.", level="warning")
        user_record = datastore.find_user(username) if hasattr(datastore, "find_user") else None
        if not isinstance(user_record, dict):
            return BookingResult(False, "Không tìm thấy tài khoản khách hàng hợp lệ để đặt tour.", level="warning")
        if isinstance(user_record, dict) and not is_user_active(user_record):
            return BookingResult(False, "Tài khoản của bạn đang bị khóa hoặc tạm ngừng hoạt động.", level="warning")

    start_date = parse_ddmmyyyy(tour.get("ngay"))
    status = normalize_tour_status(str(tour.get("trangThai", "")).strip(), default=TOUR_STATUS_NOT_OPEN)
    if not is_booking_allowed(status, start_date, occupied=_occupied_seats(datastore, ma_tour), capacity=max(1, safe_int(tour.get("khach", 1)))):
        return BookingResult(False, f"Tour đang ở trạng thái '{status}', chưa thể đăng ký.", level="warning")

    occupied = _occupied_seats(datastore, ma_tour)
    capacity = max(1, safe_int(tour.get("khach", 1)))
    available = max(capacity - occupied, 0)
    if people > available:
        return BookingResult(False, f"Tour này chỉ còn {available} chỗ trống.", level="error")

    if isinstance(danh_sach_khach, list) and danh_sach_khach and len(danh_sach_khach) != people:
        return BookingResult(False, "Danh sách hành khách phải khớp với số người đã đăng ký.", level="warning")

    price_per_person = max(0, safe_int(tour.get("gia", 0)))
    gross_total = max(0, price_per_person * people)
    normalized_breakdown = normalize_passenger_breakdown(passenger_breakdown, people)
    if normalized_breakdown is None:
        return BookingResult(False, "Cơ cấu độ tuổi không hợp lệ (vượt quá tổng số người).", level="warning")

    age_discount = calculate_age_discount(price_per_person, normalized_breakdown)
    age_discount = max(0, min(gross_total, safe_int(age_discount)))
    subtotal_after_age_discount = max(gross_total - age_discount, 0)

    voucher_quote = build_voucher_quote(
        datastore,
        voucher_code,
        subtotal_after_age_discount,
        username=username,
        ma_tour=ma_tour,
    )
    if not voucher_quote["ok"]:
        return BookingResult(False, voucher_quote["message"], level="warning")

    total_after_discount = max(subtotal_after_age_discount - voucher_quote["discount"], 0)
    paid_now = max(0, safe_int(pay_now))
    if paid_now > total_after_discount:
        return BookingResult(False, "Số tiền thanh toán ngay không được lớn hơn tổng tiền sau giảm giá.", level="warning")

    applied_voucher = voucher_quote["voucher"] if voucher_quote["code"] else None
    booking = {
        "maBooking": _next_booking_code(datastore),
        "maTour": str(ma_tour).strip(),
        "tenKhach": normalized_fullname,
        "sdt": normalized_phone,
        "soNguoi": str(people),
        "trangThai": _payment_status(total_after_discount, paid_now),
        "ngayDat": datetime.now().strftime("%d/%m/%Y"),
        "tongTienGoc": gross_total,
        "giamGiaDoiTuong": age_discount,
        "tongTien": total_after_discount,
        "tienCoc": paid_now,
        "daThanhToan": paid_now,
        "conNo": max(total_after_discount - paid_now, 0),
        "hinhThucThanhToan": str(payment_method or "Tiền mặt").strip() or "Tiền mặt",
        "nguonKhach": str(source or "Khách lẻ").strip() or "Khách lẻ",
        "ghiChu": str(note or "").strip(),
        "usernameDat": str(username or "").strip(),
        "user": str(username or "").strip(),
        "danhSachKhach": danh_sach_khach if isinstance(danh_sach_khach, list) else [],
        "coCauDoTuoi": normalized_breakdown,
        "maVoucher": voucher_quote["code"],
        "tenVoucher": applied_voucher.get("tenVoucher", "") if applied_voucher else "",
        "giamGiaVoucher": voucher_quote["discount"],
        "trangThaiHoanTien": "",
        "soTienHoan": 0,
        "ngayYeuCauHoanTien": "",
        "ngayXuLyHoanTien": "",
        "nguoiXuLyHoanTien": "",
        "ghiChuHoanTien": "",
    }

    _get_bookings(datastore).append(booking)
    changes = refresh_all_tour_statuses(datastore)
    if changes:
        booking["tourStatusChanges"] = changes
    notify_booking_created(datastore, booking, tour, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or username or "system",
        role=role,
        entity="booking",
        operation="create",
        target=booking["maBooking"],
        detail=f"Tạo booking cho tour {booking['maTour']} | Số người: {booking['soNguoi']} | Voucher: {booking['maVoucher'] or 'Không'}",
    )
    return BookingResult(True, "Tạo booking thành công.", booking=booking)


def apply_payment(datastore, ma_booking, pay_more, method, actor="", role="user"):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `apply_payment` (apply payment).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        pay_more: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        method: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return BookingResult(False, "Không tìm thấy booking cần thanh toán.", level="error")
    can_manage, deny_message = _can_manage_booking(booking, actor, role)
    if not can_manage:
        return BookingResult(False, deny_message, level="warning")
    if _is_customer_role(role):
        user_record = datastore.find_user(actor) if hasattr(datastore, "find_user") else None
        if isinstance(user_record, dict) and not is_user_active(user_record):
            return BookingResult(False, "Tài khoản của bạn đang bị khóa hoặc tạm ngừng hoạt động.", level="warning")

    # Kiểm tra trạng thái của tour liên kết
    tour_code = booking.get("maTour", "")
    if tour_code:
        tour = datastore.find_tour(tour_code) if hasattr(datastore, "find_tour") else None
        if tour:
            tour_status = str(tour.get("trangThai", "")).strip().lower()
            if tour_status in {"đã kết thúc", "completed", "hoàn thành", "hoàn tất"}:
                return BookingResult(False, "Tour này đã hoàn thành, không thể sửa đổi thanh toán.", level="warning")

    booking_state = booking_state_from_status(
        str(booking.get("trangThai", "")).strip(),
        str(booking.get("trangThaiHoanTien", "")).strip(),
    )
    current_debt = calculate_remaining_amount(booking)
    if booking_state in {BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED}:
        return BookingResult(False, "Booking này không thể thanh toán thêm.", level="warning")
    if booking_state == BOOKING_STATE_COMPLETED and current_debt <= 0:
        return BookingResult(False, "Booking đã hoàn thành và không còn công nợ.", level="warning")

    amount = max(0, safe_int(pay_more))
    if amount <= 0:
        return BookingResult(False, "Số tiền thanh toán thêm phải lớn hơn 0.", level="warning")

    total_amount = calculate_booking_total(booking)
    paid_amount = calculate_paid_amount(booking)
    debt = calculate_remaining_amount(booking)
    if amount > debt:
        return BookingResult(False, "Số tiền thanh toán thêm không được vượt quá công nợ.", level="warning")

    new_paid = paid_amount + amount
    booking["daThanhToan"] = new_paid
    booking["paidAmount"] = new_paid
    if safe_int(booking.get("tienCoc", 0)) <= 0:
        booking["tienCoc"] = amount
    booking["conNo"] = max(total_amount - new_paid, 0)
    booking["hinhThucThanhToan"] = str(method or "Tiền mặt").strip() or "Tiền mặt"
    booking["trangThai"] = _payment_status(total_amount, new_paid)
    booking["trangThaiHoanTien"] = ""
    booking["soTienHoan"] = 0
    booking["refundStatus"] = ""
    booking["lastPaymentAt"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    booking["paidBy"] = str(actor or booking.get("usernameDat", "") or "system").strip() or "system"

    notify_payment_success(datastore, booking, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or booking.get("usernameDat", "") or "system",
        role=role,
        entity="booking",
        operation="update",
        target=str(ma_booking or ""),
        detail=f"Thanh toán thêm {amount:,}đ bằng {booking['hinhThucThanhToan']}".replace(",", "."),
    )
    return BookingResult(True, f"Đã cập nhật thanh toán cho booking {ma_booking}.", booking=booking)


def cancel_booking(datastore, ma_booking, actor="", role="user", note=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `cancel_booking` (cancel booking).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return BookingResult(False, "Không tìm thấy booking cần hủy.", level="error")

    can_manage, deny_message = _can_manage_booking(booking, actor, role)
    if not can_manage:
        return BookingResult(False, deny_message, level="warning")
    if _is_customer_role(role):
        user_record = datastore.find_user(actor) if hasattr(datastore, "find_user") else None
        if isinstance(user_record, dict) and not is_user_active(user_record):
            return BookingResult(False, "Tài khoản của bạn đang bị khóa hoặc tạm ngừng hoạt động.", level="warning")

    tour = _find_tour(datastore, booking.get("maTour"))
    tour_status = normalize_tour_status(str((tour or {}).get("trangThai", "")).strip(), default=TOUR_STATUS_NOT_OPEN)
    start_date = parse_ddmmyyyy((tour or {}).get("ngay"))
    today_local = datetime.now().date()

    if _is_customer_role(role) or role == "user":
        if tour_status in TOUR_LOCK_CANCEL_STATUSES:
            return BookingResult(False, f"Tour đang ở trạng thái '{tour_status}', bạn không thể tự hủy booking này.", level="warning")
        if start_date and today_local >= start_date:
            return BookingResult(False, "Tour đã khởi hành, bạn không thể tự hủy booking này.", level="warning")
        if start_date:
            days_left = (start_date - today_local).days
            if days_left < 3:
                return BookingResult(False, "Tour khởi hành trong vòng dưới 3 ngày, bạn không thể tự hủy booking này.", level="warning")

    current_status = str(booking.get("trangThai", "")).strip()
    booking_state = booking_state_from_status(
        current_status,
        str(booking.get("trangThaiHoanTien", "")).strip(),
    )
    if booking_state in {BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED}:
        return BookingResult(False, "Booking này đã ở trạng thái hủy hoặc hoàn tiền.", level="warning")
    if booking_state == BOOKING_STATE_COMPLETED:
        return BookingResult(False, "Booking đã hoàn thành nên không thể hủy.", level="warning")

    paid_amount = max(0, safe_int(booking.get("daThanhToan", 0)))
    deposit_amount = max(0, safe_int(booking.get("tienCoc", 0)))
    paid_or_deposit = max(paid_amount, deposit_amount)

    company_cancelled = tour_status == TOUR_STATUS_CANCELLED or "công ty" in str(note or "").lower() or "tour bị hủy" in str(note or "").lower()
    days_before_departure = (start_date - today_local).days if start_date else None

    refund_eligible = True
    if not company_cancelled and days_before_departure is not None and days_before_departure < 7:
        refund_eligible = False

    refund_rate = _calc_refund_rate(days_before_departure, company_cancelled)
    refund_amount = int(round(paid_or_deposit * refund_rate))

    if paid_or_deposit > 0 and refund_eligible:
        booking["trangThai"] = "Chờ hoàn tiền"
        booking["trangThaiHoanTien"] = "Chờ duyệt"
        booking["soTienHoan"] = min(refund_amount, paid_or_deposit)
        booking["ngayYeuCauHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        booking["refundStatus"] = "pending"
    else:
        booking["trangThai"] = "Đã hủy"
        booking["trangThaiHoanTien"] = "Từ chối" if not refund_eligible and paid_or_deposit > 0 else ""
        booking["soTienHoan"] = 0
        booking["ngayYeuCauHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M") if not refund_eligible and paid_or_deposit > 0 else ""
        booking["refundStatus"] = "rejected" if not refund_eligible and paid_or_deposit > 0 else ""

    booking["conNo"] = 0
    booking["cancelledAt"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    booking["cancelledBy"] = str(actor or booking.get("usernameDat", "") or "system").strip() or "system"
    booking["cancelReason"] = str(note or "").strip()
    if note:
        existing_note = str(booking.get("ghiChu", "") or "").strip()
        booking["ghiChu"] = f"{existing_note} {note}".strip()
        booking["ghiChuHoanTien"] = str(note).strip()

    refresh_all_tour_statuses(datastore, today=today_local)

    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or booking.get("usernameDat", "") or "system",
        role=role,
        entity="booking",
        operation="update",
        target=str(ma_booking or ""),
        detail=f"Hủy booking | Trạng thái mới: {booking['trangThai']}",
    )
    return BookingResult(True, f"Đã cập nhật trạng thái booking {ma_booking} thành '{booking['trangThai']}'.", booking=booking)


def approve_refund(datastore, ma_booking, actor="", note="", role=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `approve_refund` (approve refund).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return BookingResult(False, "Không tìm thấy booking cần duyệt hoàn tiền.", level="error")
    admin_username = str(getattr(datastore, "data", {}).get("admin", {}).get("username", "admin")).strip().lower()
    actor_name = str(actor or "").strip().lower()
    effective_admin = _is_admin_role(role) or (actor_name and actor_name == admin_username)
    if not effective_admin:
        return BookingResult(False, "Bạn không có quyền duyệt hoàn tiền.", level="warning")

    if str(booking.get("trangThai", "")).strip() != "Chờ hoàn tiền":
        return BookingResult(False, "Booking này không ở trạng thái chờ hoàn tiền.", level="warning")

    # Kiểm tra chặn duyệt hoàn nếu ngày hiện tại đến khởi hành < 7 ngày
    tour = _find_tour(datastore, booking.get("maTour"))
    start_date = parse_ddmmyyyy((tour or {}).get("ngay"))
    today_local = datetime.now().date()
    if start_date:
        days_left = (start_date - today_local).days
        if days_left < 7:
            return BookingResult(False, "Chặn duyệt hoàn tiền vì thời gian tới ngày khởi hành còn dưới 7 ngày.", level="warning")

    paid_amount = max(safe_int(booking.get("daThanhToan", 0)), safe_int(booking.get("tienCoc", 0)))
    refund_amount = max(safe_int(booking.get("soTienHoan", 0)), 0)
    refund_amount = min(refund_amount, paid_amount)
    booking["soTienHoan"] = refund_amount
    booking["trangThai"] = "Hoàn tiền"
    booking["trangThaiHoanTien"] = "Đã hoàn tiền"
    booking["ngayXuLyHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    booking["nguoiXuLyHoanTien"] = str(actor or "admin").strip() or "admin"
    booking["ghiChuHoanTien"] = str(note or booking.get("ghiChuHoanTien", "") or "").strip()
    booking["conNo"] = 0
    booking["refundStatus"] = "approved"
    booking["refundedAt"] = booking["ngayXuLyHoanTien"]
    booking["refundedBy"] = booking["nguoiXuLyHoanTien"]

    emit_notification(
        datastore,
        event_type="Refund Approved",
        content=f"Yêu cầu hoàn tiền cho booking {ma_booking} đã được duyệt thành công. Số tiền hoàn: {refund_amount:,}đ.".replace(",", "."),
        ma_tour=booking.get("maTour", ""),
        ma_booking=ma_booking,
        username=booking.get("usernameDat", ""),
        persist=False
    )

    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or "admin",
        role=role or "admin",
        entity="refund",
        operation="approve",
        target=str(ma_booking or ""),
        detail=f"Duyệt hoàn {refund_amount:,}đ".replace(",", "."),
    )
    return BookingResult(True, f"Đã duyệt hoàn tiền cho booking {ma_booking}.", booking=booking)


def reject_refund(datastore, ma_booking, actor="", note="", role=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `reject_refund` (reject refund).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return BookingResult(False, "Không tìm thấy booking cần từ chối hoàn tiền.", level="error")
    admin_username = str(getattr(datastore, "data", {}).get("admin", {}).get("username", "admin")).strip().lower()
    actor_name = str(actor or "").strip().lower()
    effective_admin = _is_admin_role(role) or (actor_name and actor_name == admin_username)
    if not effective_admin:
        return BookingResult(False, "Bạn không có quyền từ chối hoàn tiền.", level="warning")

    if str(booking.get("trangThai", "")).strip() != "Chờ hoàn tiền":
        return BookingResult(False, "Booking này không ở trạng thái chờ hoàn tiền.", level="warning")

    booking["trangThai"] = "Đã hủy"
    booking["trangThaiHoanTien"] = "Từ chối"
    booking["ngayXuLyHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    booking["nguoiXuLyHoanTien"] = str(actor or "admin").strip() or "admin"
    booking["ghiChuHoanTien"] = str(note or booking.get("ghiChuHoanTien", "") or "").strip()
    booking["conNo"] = 0
    booking["soTienHoan"] = 0
    booking["refundStatus"] = "rejected"

    emit_notification(
        datastore,
        event_type="Refund Rejected",
        content=f"Yêu cầu hoàn tiền cho booking {ma_booking} đã bị từ chối.",
        ma_tour=booking.get("maTour", ""),
        ma_booking=ma_booking,
        username=booking.get("usernameDat", ""),
        persist=False
    )

    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or "admin",
        role=role or "admin",
        entity="refund",
        operation="reject",
        target=str(ma_booking or ""),
        detail=booking["ghiChuHoanTien"] or "Từ chối yêu cầu hoàn tiền",
    )
    return BookingResult(True, f"Đã từ chối hoàn tiền cho booking {ma_booking}.", booking=booking)


def summarize_bookings_by_tour(datastore, actor: str = "", role: str = "admin") -> list[dict]:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `summarize_bookings_by_tour` (summarize bookings by tour).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not _is_admin_role(role):
        return []

    rows = []
    tours = getattr(datastore, "list_tours", datastore.data.get("tours", []))

    for tour in tours:
        ma_tour = str(tour.get("ma", "")).strip()
        tour_bookings = [booking for booking in _get_bookings(datastore) if str(booking.get("maTour", "")).strip() == ma_tour]
        customers = set()
        guest_total = 0
        active_guest_total = 0
        total_revenue = 0
        collected = 0
        refunded = 0
        pending_refunds = 0

        for booking in tour_bookings:
            customer_key = (
                str(booking.get("usernameDat", "")).strip().lower()
                or str(booking.get("sdt", "")).strip()
                or str(booking.get("tenKhach", "")).strip().lower()
            )
            if customer_key:
                customers.add(customer_key)

            guest_total += max(0, safe_int(booking.get("soNguoi", 0)))
            booking_paid, booking_refund, booking_net = _booking_gross_refund_net(booking)
            collected += booking_paid
            refunded += booking_refund

            refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
            if booking.get("trangThai") == "Chờ hoàn tiền":
                pending_refunds += 1
            if booking.get("trangThai") in CANCEL_BOOKING_STATUSES and refund_status != "Từ chối":
                continue

            active_guest_total += max(0, safe_int(booking.get("soNguoi", 0)))
            total_revenue += booking_net

        capacity = max(1, safe_int(tour.get("khach", 1)))
        rows.append(
            {
                "maTour": ma_tour,
                "tenTour": str(tour.get("ten", "")).strip(),
                "trangThai": str(tour.get("trangThai", "")).strip(),
                "tongBooking": len(tour_bookings),
                "tongKhachHang": len(customers),
                "tongNguoi": guest_total,
                "khachHieuLuc": active_guest_total,
                "choConLai": max(capacity - active_guest_total, 0),
                "doanhThu": total_revenue,
                "daThu": collected,
                "hoanTien": refunded,
                "doanhThuThuan": max(collected - refunded, 0),
                "choHoanTien": pending_refunds,
            }
        )

    return sorted(rows, key=lambda row: (row["maTour"], row["tenTour"]))

# ===== BEGIN core/tour_service.py =====

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TourResult:
    success: bool
    message: str
    tour: dict | None = None
    level: str = "info"


def _safe_int(value, default: int = 0) -> int:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_safe_int` ( safe int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _parse_ddmmyyyy(value: str | None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_parse_ddmmyyyy` ( parse ddmmyyyy).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def _is_overlapped(tour_a: dict, tour_b: dict) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_is_overlapped` ( is overlapped).
    Tham số:
        tour_a: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour_b: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    start_a = _parse_ddmmyyyy(tour_a.get("ngay"))
    end_a = _parse_ddmmyyyy(tour_a.get("ngayKetThuc")) or start_a
    start_b = _parse_ddmmyyyy(tour_b.get("ngay"))
    end_b = _parse_ddmmyyyy(tour_b.get("ngayKetThuc")) or start_b
    if not start_a or not end_a or not start_b or not end_b:
        return False
    return start_a <= end_b and start_b <= end_a


def _bookings(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_bookings` ( bookings).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return getattr(datastore, "list_bookings", datastore.data.get("bookings", []))


def assign_guide(datastore, ma_tour: str, ma_hdv: str, actor: str = "admin") -> TourResult:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `assign_guide` (assign guide).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return TourResult(False, "Không tìm thấy tour cần phân công.", level="error")
    tour_status = normalize_tour_status(str(tour.get("trangThai", "")).strip(), default=TOUR_STATUS_NOT_OPEN)
    if tour_status in {TOUR_STATUS_CANCELLED, TOUR_STATUS_COMPLETED}:
        return TourResult(False, f"Tour đang ở trạng thái '{tour_status}', không thể phân công HDV.", level="warning")
    if tour_status == TOUR_STATUS_STARTED and str(actor or "").strip().lower() != "admin":
        return TourResult(False, "Tour đang diễn ra, chỉ admin mới được đổi HDV.", level="warning")

    guide = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
    if not isinstance(guide, dict):
        return TourResult(False, "Không tìm thấy hướng dẫn viên.", level="error")

    guide_status = normalize_guide_status(guide.get("trangThai", guide.get("status", "")))
    if not is_guide_active(guide):
        return TourResult(False, f"Hướng dẫn viên đang ở trạng thái '{guide_status}', không thể phân công.", level="warning")

    active_statuses = {
        TOUR_STATUS_NOT_OPEN,
        TOUR_STATUS_OPEN,
        TOUR_STATUS_FULL,
        TOUR_STATUS_STARTED,
    }
    for other_tour in getattr(datastore, "list_tours", datastore.data.get("tours", [])):
        if str(other_tour.get("ma", "")).strip() == str(ma_tour or "").strip():
            continue
        if str(other_tour.get("hdvPhuTrach", "")).strip() != str(ma_hdv or "").strip():
            continue
        if normalize_tour_status(other_tour.get("trangThai", ""), default=TOUR_STATUS_NOT_OPEN) not in active_statuses:
            continue
        if _is_overlapped(tour, other_tour):
            return TourResult(
                False,
                f"HDV {ma_hdv} đang có tour trùng lịch ({other_tour.get('ma', '')}).",
                level="warning",
            )

    tour["hdvPhuTrach"] = str(ma_hdv or "").strip()
    warning_notes = []
    tour_region = str(tour.get("khuVuc", "")).strip().lower()
    guide_region = str(guide.get("khuVuc", "")).strip().lower()
    if tour_region and guide_region and tour_region != guide_region:
        warning_notes.append(f"[WARN] Khu vực tour ({tour.get('khuVuc', '')}) chưa khớp với HDV ({guide.get('khuVuc', '')}).")
    tour_lang = str(tour.get("ngoaiNgu", "") or tour.get("yeuCauNgoaiNgu", "")).strip().lower()
    guide_lang = str(guide.get("ngoaiNgu", "")).strip().lower()
    if tour_lang and guide_lang and tour_lang not in guide_lang:
        warning_notes.append(f"[WARN] Ngoại ngữ yêu cầu ({tour.get('ngoaiNgu', '') or tour.get('yeuCauNgoaiNgu', '')}) chưa khớp HDV.")
    tour_skill = str(tour.get("chuyenMon", "")).strip().lower()
    guide_skill = str(guide.get("chuyenMon", "")).strip().lower()
    if tour_skill and guide_skill and tour_skill not in guide_skill:
        warning_notes.append(f"[WARN] Chuyên môn tour ({tour.get('chuyenMon', '')}) chưa khớp HDV ({guide.get('chuyenMon', '')}).")
    if warning_notes:
        old_note = str(tour.get("ghiChuDieuHanh", "") or "").strip()
        tour["ghiChuDieuHanh"] = " ".join([old_note] + warning_notes).strip()
    avg_rating = _safe_float(guide.get("avg_rating", 0), 0.0)
    if avg_rating > 0 and avg_rating < 2.5:
        old_note = str(tour.get("ghiChuDieuHanh", "") or "").strip()
        low_rating_warning = f"[WARN] HDV có điểm đánh giá thấp ({avg_rating:.1f}/5)."
        if low_rating_warning not in old_note:
            tour["ghiChuDieuHanh"] = f"{old_note} {low_rating_warning}".strip()
    notify_guide_assigned(datastore, tour, guide, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=str(actor or "admin").strip() or "admin",
        role="admin",
        entity="tour",
        operation="assign_guide",
        target=str(tour.get("ma", "")),
        detail=f"Gán HDV {ma_hdv} cho tour",
    )
    return TourResult(True, f"Đã phân công HDV {ma_hdv} cho tour {tour.get('ma', '')}.", tour=tour)


def cancel_tour(datastore, ma_tour: str, actor: str = "admin", reason: str = "") -> TourResult:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `cancel_tour` (cancel tour).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        reason: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return TourResult(False, "Không tìm thấy tour cần hủy.", level="error")

    tour["trangThai"] = "Đã hủy"
    sync_ghi_chu_dieu_hanh(tour)
    if str(reason or "").strip():
        old_note = str(tour.get("ghiChuDieuHanh", "") or "").strip()
        tour["ghiChuDieuHanh"] = f"{old_note} [HỦY TOUR] {reason}".strip()

    pending_refunds = 0
    cancelled_free = 0
    for booking in _bookings(datastore):
        if str(booking.get("maTour", "")).strip() != str(ma_tour or "").strip():
            continue
        booking_state = booking_state_from_status(
            str(booking.get("trangThai", "")).strip(),
            str(booking.get("trangThaiHoanTien", "")).strip(),
        )
        if booking_state in {BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED}:
            continue

        paid = max(0, _safe_int(booking.get("daThanhToan", 0)))
        if paid > 0:
            booking["trangThai"] = "Chờ hoàn tiền"
            booking["trangThaiHoanTien"] = "Chờ duyệt"
            booking["soTienHoan"] = paid
            booking["ngayYeuCauHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            booking["refundStatus"] = "pending"
            pending_refunds += 1
        else:
            booking["trangThai"] = "Đã hủy"
            booking["trangThaiHoanTien"] = ""
            booking["soTienHoan"] = 0
            booking["refundStatus"] = ""
            cancelled_free += 1

    notify_tour_cancelled(datastore, tour, reason=reason, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=str(actor or "admin").strip() or "admin",
        role="admin",
        entity="tour",
        operation="cancel",
        target=str(tour.get("ma", "")),
        detail=f"Hủy tour | Chờ hoàn: {pending_refunds} | Hủy không hoàn: {cancelled_free}",
    )

    return TourResult(
        True,
        f"Đã hủy tour {tour.get('ma', '')}. Booking chờ hoàn: {pending_refunds}, booking hủy thẳng: {cancelled_free}.",
        tour=tour,
    )


def complete_tour(datastore, ma_tour: str, actor: str = "guide", note: str = "") -> TourResult:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `complete_tour` (complete tour).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return TourResult(False, "Không tìm thấy tour cần kết thúc.", level="error")
    actor_name = str(actor or "").strip()
    actor_role = "admin" if actor_name.lower() == "admin" else "guide"
    tour_status = normalize_tour_status(str(tour.get("trangThai", "")).strip(), default=TOUR_STATUS_NOT_OPEN)
    if tour_status == TOUR_STATUS_CANCELLED:
        return TourResult(False, f"Tour đang ở trạng thái '{tour_status}', không thể kết thúc.", level="warning")
    if tour_status == TOUR_STATUS_COMPLETED:
        return TourResult(False, "Tour đã kết thúc trước đó.", level="warning")
    if actor_role == "guide" and not guide_assigned_to_tour(actor_name, tour):
        return TourResult(False, "Bạn không được phân công cho tour này.", level="warning")
    today_local = datetime.now().date()
    start_date = _parse_ddmmyyyy(tour.get("ngay"))
    end_date = _parse_ddmmyyyy(tour.get("ngayKetThuc")) or start_date
    if end_date and today_local < end_date:
        if actor_name.lower() != "admin":
            return TourResult(False, f"Tour chưa đến ngày kết thúc ({end_date.strftime('%d/%m/%Y')}).", level="warning")
        if not str(note or "").strip():
            return TourResult(False, "Admin cần ghi rõ lý do khi kết thúc tour sớm.", level="warning")

    tour["trangThai"] = TOUR_STATUS_COMPLETED
    sync_ghi_chu_dieu_hanh(tour)
    tour["completedAt"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    tour["completedBy"] = actor_name or ("admin" if actor_role == "admin" else "guide")
    tour["completedByRole"] = actor_role
    if str(note or "").strip():
        old_note = str(tour.get("ghiChuDieuHanh", "") or "").strip()
        tour["ghiChuDieuHanh"] = f"{old_note} [KẾT THÚC] {note}".strip()

    completed_count = 0
    for booking in _bookings(datastore):
        if str(booking.get("maTour", "")).strip() != str(ma_tour or "").strip():
            continue
        booking_state = booking_state_from_status(
            str(booking.get("trangThai", "")).strip(),
            str(booking.get("trangThaiHoanTien", "")).strip(),
        )
        if booking_state not in {BOOKING_STATE_CONFIRMED, BOOKING_STATE_PAID}:
            continue
        booking["trangThai"] = "Đã hoàn thành"
        booking["trangThaiHoanTien"] = ""
        booking["soTienHoan"] = 0
        booking["refundStatus"] = ""
        completed_count += 1

    notify_tour_completed(datastore, tour, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=str(actor or "system").strip() or "system",
        role="guide" if actor != "admin" else "admin",
        entity="tour",
        operation="complete",
        target=str(tour.get("ma", "")),
        detail=f"Đóng tour, đánh dấu completed {completed_count} booking",
    )
    return TourResult(True, f"Đã kết thúc tour {tour.get('ma', '')}.", tour=tour)

# ===== BEGIN core/system_rules.py =====
# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta



VALID_BOOKING_STATUSES = {"Mới tạo", "Đã cọc", "Đã thanh toán", "Đã hoàn thành", "Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}
CANCEL_BOOKING_STATUSES = {"Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}
TERMINAL_TOUR_STATUSES = {TOUR_STATUS_COMPLETED, TOUR_STATUS_CANCELLED}
AUTO_CANCEL_UNPAID_DAYS = 15


def _safe_int(value, default=0):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_safe_int` ( safe int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _non_negative_int(value, default=0):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_non_negative_int` ( non negative int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return max(0, _safe_int(value, default))


def _parse_ddmmyyyy(value: str | None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_parse_ddmmyyyy` ( parse ddmmyyyy).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def _normalize_voucher_scope(raw_value) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_voucher_scope` ( normalize voucher scope).
    Tham số:
        raw_value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return normalize_tour_scope(raw_value)


def _normalize_booking(booking: dict, tours_by_code: dict[str, dict], today: date) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_booking` ( normalize booking).
    Tham số:
        booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tours_by_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        today: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour_code = str(booking.get("maTour", "")).strip()
    tour = tours_by_code.get(tour_code)

    so_nguoi = max(1, _safe_int(booking.get("soNguoi", 1), 1))
    booking["soNguoi"] = str(so_nguoi)

    price_per_person = _non_negative_int(tour.get("gia", 0)) if tour else _non_negative_int(booking.get("gia", 0))
    tong_tien_goc = (
        price_per_person * so_nguoi
        if price_per_person > 0
        else _non_negative_int(booking.get("tongTienGoc", booking.get("tongTien", 0)))
    )
    normalized_breakdown = normalize_passenger_breakdown(booking.get("coCauDoTuoi", {}), so_nguoi)
    if normalized_breakdown is None:
        normalized_breakdown = normalize_passenger_breakdown({}, so_nguoi) or {
            "treEm": 0,
            "trungNien": so_nguoi,
            "nguoiCaoTuoi": 0,
        }

    if price_per_person > 0:
        giam_gia_doi_tuong = calculate_age_discount(price_per_person, normalized_breakdown)
    else:
        giam_gia_doi_tuong = _non_negative_int(booking.get("giamGiaDoiTuong", 0))
    giam_gia_doi_tuong = min(giam_gia_doi_tuong, tong_tien_goc)

    giam_gia_voucher = _non_negative_int(booking.get("giamGiaVoucher", 0))
    giam_gia_voucher = min(giam_gia_voucher, max(tong_tien_goc - giam_gia_doi_tuong, 0))
    tong_tien = max(tong_tien_goc - giam_gia_doi_tuong - giam_gia_voucher, 0)
    da_thanh_toan = _non_negative_int(booking.get("daThanhToan", booking.get("tienCoc", 0)))
    tien_coc = _non_negative_int(booking.get("tienCoc", 0))

    if tong_tien > 0 and da_thanh_toan > tong_tien:
        da_thanh_toan = tong_tien
    if tien_coc > da_thanh_toan:
        tien_coc = da_thanh_toan

    auto_cancel_unpaid = False
    if tour and da_thanh_toan <= 0 and tien_coc <= 0:
        ngay_khoi_hanh = _parse_ddmmyyyy(tour.get("ngay"))
        if ngay_khoi_hanh:
            payment_deadline = ngay_khoi_hanh - timedelta(days=AUTO_CANCEL_UNPAID_DAYS)
            auto_cancel_unpaid = today >= payment_deadline
            if auto_cancel_unpaid:
                auto_note = f"[AUTO] Hủy do chưa đặt cọc/thanh toán trước hạn {payment_deadline.strftime('%d/%m/%Y')}."
                existing_note = str(booking.get("ghiChu", "") or "").strip()
                if auto_note not in existing_note:
                    booking["ghiChu"] = f"{auto_note} {existing_note}".strip()

    refund_status = str(booking.get("trangThaiHoanTien", "") or "").strip()
    refund_amount = _non_negative_int(booking.get("soTienHoan", 0))
    status = str(booking.get("trangThai", "") or "").strip()

    if status == "Chờ hoàn tiền" and not refund_status:
        refund_status = "Chờ duyệt"

    if status in CANCEL_BOOKING_STATUSES:
        if status == "Đã hủy":
            if da_thanh_toan > 0 and refund_status != "Từ chối":
                status = "Chờ hoàn tiền"
                refund_status = "Chờ duyệt"
                refund_amount = max(refund_amount, da_thanh_toan)
            con_no = 0
        elif status == "Chờ hoàn tiền":
            refund_status = "Chờ duyệt"
            refund_amount = max(refund_amount, da_thanh_toan)
            con_no = 0
        else:
            refund_status = "Đã hoàn tiền"
            if refund_amount <= 0 and da_thanh_toan > 0:
                refund_amount = da_thanh_toan
            refund_amount = min(max(refund_amount, 0), da_thanh_toan)
            con_no = 0
    elif auto_cancel_unpaid and status == "Mới tạo":
        status = "Đã hủy"
        refund_status = ""
        refund_amount = 0
        con_no = 0
    else:
        if status == "Đã hoàn thành":
            con_no = max(tong_tien - da_thanh_toan, 0)
            refund_status = ""
            refund_amount = 0
            booking["ngayYeuCauHoanTien"] = ""
            booking["ngayXuLyHoanTien"] = ""
            booking["nguoiXuLyHoanTien"] = ""
            booking["ghiChuHoanTien"] = ""
            booking["trangThai"] = status
            booking["trangThaiHoanTien"] = refund_status
            booking["soTienHoan"] = refund_amount
            booking["tongTienGoc"] = tong_tien_goc
            booking["giamGiaDoiTuong"] = giam_gia_doi_tuong
            booking["coCauDoTuoi"] = normalized_breakdown
            booking["tongTien"] = tong_tien
            booking["tienCoc"] = tien_coc
            booking["daThanhToan"] = da_thanh_toan
            booking["conNo"] = con_no
            if not str(booking.get("hinhThucThanhToan", "") or "").strip():
                booking["hinhThucThanhToan"] = "Chưa thanh toán" if da_thanh_toan <= 0 else "Tiền mặt"
            return
        if status in {"Mới tạo", "Đã cọc", "Đã thanh toán"}:
            if status == "Mới tạo":
                da_thanh_toan = min(da_thanh_toan, 0)
                tien_coc = min(tien_coc, da_thanh_toan)
            elif status == "Đã cọc" and da_thanh_toan <= 0:
                status = "Mới tạo"
            elif status == "Đã cọc" and tong_tien > 0 and da_thanh_toan >= tong_tien:
                status = "Đã thanh toán"
            elif status == "Đã thanh toán" and tong_tien > 0 and da_thanh_toan < tong_tien:
                da_thanh_toan = tong_tien
                tien_coc = min(tien_coc, da_thanh_toan)
        elif da_thanh_toan <= 0:
            status = "Mới tạo"
        elif tong_tien > 0 and da_thanh_toan < tong_tien:
            status = "Đã cọc"
        else:
            status = "Đã thanh toán"
        con_no = max(tong_tien - da_thanh_toan, 0)
        refund_status = ""
        refund_amount = 0
        booking["ngayYeuCauHoanTien"] = ""
        booking["ngayXuLyHoanTien"] = ""
        booking["nguoiXuLyHoanTien"] = ""
        booking["ghiChuHoanTien"] = ""

    ngay_dat = _parse_ddmmyyyy(booking.get("ngayDat"))
    if ngay_dat is None:
        booking["ngayDat"] = today.strftime("%d/%m/%Y")
        ngay_dat = today
    if tour:
        ngay_khoi_hanh = _parse_ddmmyyyy(tour.get("ngay"))
        if ngay_khoi_hanh and ngay_dat and ngay_dat > ngay_khoi_hanh:
            booking["ngayDat"] = ngay_khoi_hanh.strftime("%d/%m/%Y")

    booking.setdefault("hinhThucThanhToan", "Chưa thanh toán" if da_thanh_toan <= 0 else "Tiền mặt")
    booking.setdefault("nguonKhach", "Khách lẻ")
    booking.setdefault("ghiChu", "")
    if not str(booking.get("usernameDat", "")).strip():
        booking["usernameDat"] = str(
            booking.get("username")
            or booking.get("user")
            or booking.get("userId")
            or ""
        ).strip()
    booking.setdefault("usernameDat", "")
    booking.setdefault("username", booking.get("usernameDat", ""))
    booking.setdefault("danhSachKhach", [])
    if not isinstance(booking.get("danhSachKhach"), list):
        booking["danhSachKhach"] = []
    booking.setdefault("maVoucher", "")
    booking.setdefault("tenVoucher", "")
    booking.setdefault("giamGiaDoiTuong", 0)
    booking.setdefault("giamGiaVoucher", 0)
    booking.setdefault("coCauDoTuoi", {})
    booking.setdefault("trangThaiHoanTien", refund_status)
    booking.setdefault("soTienHoan", refund_amount)
    booking.setdefault("ngayYeuCauHoanTien", "")
    booking.setdefault("ngayXuLyHoanTien", "")
    booking.setdefault("nguoiXuLyHoanTien", "")
    booking.setdefault("ghiChuHoanTien", "")
    booking["tongTienGoc"] = tong_tien_goc
    booking["giamGiaDoiTuong"] = giam_gia_doi_tuong
    booking["coCauDoTuoi"] = normalized_breakdown
    booking["tongTien"] = tong_tien
    booking["tienCoc"] = tien_coc
    booking["daThanhToan"] = da_thanh_toan
    booking["conNo"] = con_no
    booking["trangThai"] = status
    booking["trangThaiHoanTien"] = refund_status
    booking["soTienHoan"] = refund_amount
    if status == "Chờ hoàn tiền":
        booking["refundStatus"] = "pending"
    elif status == "Hoàn tiền":
        booking["refundStatus"] = "approved"
    elif refund_status == "Từ chối":
        booking["refundStatus"] = "rejected"
    else:
        booking.setdefault("refundStatus", "")
    if not str(booking.get("hinhThucThanhToan", "") or "").strip():
        booking["hinhThucThanhToan"] = "Chưa thanh toán" if da_thanh_toan <= 0 else "Tiền mặt"


def _normalize_voucher(voucher: dict, used_count: int, today: date) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_voucher` ( normalize voucher).
    Tham số:
        voucher: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        used_count: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        today: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    voucher["maVoucher"] = str(voucher.get("maVoucher", "")).strip().upper()
    voucher.setdefault("tenVoucher", "")
    voucher.setdefault("loaiGiam", "Tiền mặt")
    voucher.setdefault("giamGiaVoucher", 0)
    voucher["donToiThieu"] = str(_non_negative_int(voucher.get("donToiThieu", 0)))

    so_luong = max(_non_negative_int(voucher.get("soLuong", 0)), used_count)
    voucher["soLuong"] = str(so_luong)
    voucher["daSuDung"] = str(max(0, used_count))
    voucher["gioiHanMoiUser"] = str(_non_negative_int(voucher.get("gioiHanMoiUser", 0)))
    voucher["tourApDung"] = _normalize_voucher_scope(voucher.get("tourApDung", ""))
    voucher.setdefault("ngayBatDau", "")
    voucher.setdefault("ngayKetThuc", "")
    voucher.setdefault("moTa", "")

    status = str(voucher.get("trangThai", "")).strip()
    status_lower = status.lower()
    start_date = _parse_ddmmyyyy(voucher.get("ngayBatDau"))
    end_date = _parse_ddmmyyyy(voucher.get("ngayKetThuc"))

    if "ngừng" in status_lower:
        normalized_status = "Ngừng áp dụng"
    elif end_date and today > end_date:
        normalized_status = "Hết hạn"
    elif so_luong > 0 and used_count >= so_luong:
        normalized_status = "Hết lượt"
    elif start_date and today < start_date:
        normalized_status = "Sắp áp dụng"
    else:
        normalized_status = "Đang áp dụng"

    voucher["trangThai"] = normalized_status


def _normalize_tour(tour: dict, occupied: int, today: date) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_tour` ( normalize tour).
    Tham số:
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        occupied: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        today: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    status = normalize_tour_status(str(tour.get("trangThai", "")).strip(), default=TOUR_STATUS_NOT_OPEN)

    valid_statuses = set(TOUR_STATUS_CHOICES)

    suc_chua = max(1, _safe_int(tour.get("khach", 1), 1), max(0, _safe_int(occupied, 0)))
    gia = _non_negative_int(tour.get("gia", 0))

    ngay_di = _parse_ddmmyyyy(tour.get("ngay"))
    ngay_ve = _parse_ddmmyyyy(tour.get("ngayKetThuc")) or ngay_di
    if ngay_di and ngay_ve and ngay_ve < ngay_di:
        ngay_ve = ngay_di

    if ngay_di and ngay_ve:
        so_ngay = (ngay_ve - ngay_di).days + 1
        so_dem = max(so_ngay - 1, 0)
        tour["soNgay"] = f"{so_ngay}N{so_dem}D"
        tour["ngayKetThuc"] = ngay_ve.strftime("%d/%m/%Y")

    auto_status = derive_tour_status(
        current_status=status,
        start_date=ngay_di,
        end_date=ngay_ve,
        occupied=max(0, _safe_int(occupied, 0)),
        capacity=suc_chua,
        today=today,
    )

    if status not in valid_statuses:
        status = auto_status
    elif status != TOUR_STATUS_CANCELLED:
        status = auto_status

    tour["trangThai"] = status
    tour["khach"] = str(suc_chua)
    tour["gia"] = str(gia)
    tour.pop("chiPhiDuKien", None)
    tour.pop("chiPhiThucTe", None)
    tour["ghiChuDieuHanh"] = str(tour.get("ghiChuDieuHanh", "") or "").strip()
    if not str(tour.get("hdvPhuTrach", "")).strip():
        tour["hdvPhuTrach"] = str(
            tour.get("maHDV")
            or tour.get("guideId")
            or tour.get("hdv")
            or ""
        ).strip()
    tour.setdefault("hdvPhuTrach", "")


def _normalize_guide(guide: dict, assignments: dict[str, dict]) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_guide` ( normalize guide).
    Tham số:
        guide: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        assignments: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    ma_hdv = str(guide.get("maHDV", "")).strip()
    current_status = str(guide.get("trangThai", "")).strip()
    assignment = assignments.get(ma_hdv, {"assigned": False, "in_progress": False})
    account_status = normalize_guide_status(current_status)
    guide["trangThaiTaiKhoan"] = account_status
    if account_status in {GUIDE_STATUS_INACTIVE, GUIDE_STATUS_BLOCKED, GUIDE_STATUS_HIDDEN, GUIDE_STATUS_TEMP_OFF}:
        guide["trangThai"] = account_status
    elif assignment["in_progress"]:
        guide["trangThai"] = "Đang dẫn tour"
    elif assignment["assigned"]:
        guide["trangThai"] = "Đã phân công"
    elif current_status in {"Sẵn sàng", "Đã phân công", "Đang dẫn tour"}:
        guide["trangThai"] = current_status
    else:
        guide["trangThai"] = "Sẵn sàng"

    guide.setdefault("password", "123")
    guide.setdefault("total_reviews", 0)
    guide.setdefault("avg_rating", 0)
    guide.setdefault("skill_score", 0)
    guide.setdefault("attitude_score", 0)
    guide.setdefault("problem_solving_score", 0)


def _normalize_record_list(records) -> list[dict]:
    """
    Chuẩn hóa dữ liệu danh sách bản ghi từ nhiều nguồn legacy.
    Hỗ trợ cả cấu trúc lồng một cấp như [[{...}, {...}]].
    """
    if not isinstance(records, list):
        return []

    normalized = []
    for item in records:
        if isinstance(item, dict):
            normalized.append(item)
            continue
        if isinstance(item, list):
            for nested in item:
                if isinstance(nested, dict):
                    normalized.append(nested)
    return normalized


def _voucher_booking_is_counted(booking: dict, include_pending_refund: bool = True) -> bool:
    status = str(booking.get("trangThai", "")).strip()
    if status in {"Đã hủy", "Hoàn tiền"}:
        return False
    if status == "Chờ hoàn tiền":
        return False
    return True


def _soft_revalidate_booking_vouchers(data: dict, today: date) -> None:
    vouchers_by_code = {
        str(voucher.get("maVoucher", "")).strip().upper(): voucher
        for voucher in data.get("maVoucher", [])
        if isinstance(voucher, dict)
    }
    usage_total: dict[str, int] = {}
    usage_by_user: dict[tuple[str, str], int] = {}
    usage_by_tour: dict[tuple[str, str], int] = {}

    for booking in data.get("bookings", []):
        if not isinstance(booking, dict):
            continue
        code = str(booking.get("maVoucher", "")).strip().upper()
        if not code:
            continue
        voucher = vouchers_by_code.get(code)
        if not voucher:
            booking["maVoucher"] = ""
            booking["tenVoucher"] = ""
            booking["giamGiaVoucher"] = 0
            continue
        if not _voucher_booking_is_counted(booking, include_pending_refund=True):
            booking["maVoucher"] = ""
            booking["tenVoucher"] = ""
            booking["giamGiaVoucher"] = 0
            continue

        start_date = _parse_ddmmyyyy(voucher.get("ngayBatDau"))
        end_date = _parse_ddmmyyyy(voucher.get("ngayKetThuc"))
        if start_date and today < start_date:
            booking["maVoucher"] = ""
            booking["tenVoucher"] = ""
            booking["giamGiaVoucher"] = 0
            continue
        if end_date and today > end_date:
            booking["maVoucher"] = ""
            booking["tenVoucher"] = ""
            booking["giamGiaVoucher"] = 0
            continue

        allowed_tours = set(parse_tour_scope(voucher.get("tourApDung", "")))
        booking_tour = str(booking.get("maTour", "")).strip().upper()
        if allowed_tours and booking_tour not in allowed_tours:
            booking["maVoucher"] = ""
            booking["tenVoucher"] = ""
            booking["giamGiaVoucher"] = 0
            continue

        subtotal = max(0, _non_negative_int(booking.get("tongTienGoc", booking.get("tongTien", 0))) - _non_negative_int(booking.get("giamGiaDoiTuong", 0)))
        if subtotal < max(0, _non_negative_int(voucher.get("donToiThieu", 0))):
            booking["maVoucher"] = ""
            booking["tenVoucher"] = ""
            booking["giamGiaVoucher"] = 0
            continue

        expected_discount = min(subtotal, resolve_voucher_discount(voucher, subtotal))
        current_discount = max(0, _non_negative_int(booking.get("giamGiaVoucher", 0)))
        if current_discount <= 0 or current_discount > subtotal or current_discount > expected_discount:
            booking["giamGiaVoucher"] = expected_discount
            if expected_discount <= 0:
                booking["maVoucher"] = ""
                booking["tenVoucher"] = ""
                continue

        limit_total = max(0, _non_negative_int(voucher.get("soLuong", 0)))
        if limit_total > 0 and usage_total.get(code, 0) >= limit_total:
            booking["maVoucher"] = ""
            booking["tenVoucher"] = ""
            booking["giamGiaVoucher"] = 0
            continue

        user_limit = max(0, _non_negative_int(voucher.get("gioiHanMoiUser", 0)))
        booking_user = str(booking.get("usernameDat", "")).strip().lower()
        if user_limit > 0:
            user_key = (code, booking_user)
            if not booking_user or usage_by_user.get(user_key, 0) >= user_limit:
                booking["maVoucher"] = ""
                booking["tenVoucher"] = ""
                booking["giamGiaVoucher"] = 0
                continue
            usage_by_user[user_key] = usage_by_user.get(user_key, 0) + 1

        tour_key = (code, booking_tour)
        usage_by_tour[tour_key] = usage_by_tour.get(tour_key, 0) + 1
        usage_total[code] = usage_total.get(code, 0) + 1


def apply_system_rules(data: dict, today: date | None = None) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `apply_system_rules` (apply system rules).
    Tham số:
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        today: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not isinstance(data, dict):
        return data

    today = today or date.today()
    data.setdefault("hdv", [])
    data.setdefault("tours", [])
    data.setdefault("bookings", [])
    data.setdefault("users", [])
    data.setdefault("admin", {})
    data.setdefault("maVoucher", [])
    data["hdv"] = _normalize_record_list(data.get("hdv"))
    data["tours"] = _normalize_record_list(data.get("tours"))
    data["bookings"] = _normalize_record_list(data.get("bookings"))
    data["users"] = _normalize_record_list(data.get("users"))
    data["maVoucher"] = _normalize_record_list(data.get("maVoucher"))

    active_tour_codes = {str(t.get("ma", "")).strip().upper() for t in data["tours"] if t.get("ma")}
    data["bookings"] = [b for b in data["bookings"] if str(b.get("maTour", "")).strip().upper() in active_tour_codes]

    tours_by_code = {}
    for tour in data["tours"]:
        ma_tour = str(tour.get("ma", "")).strip()
        if ma_tour:
            tours_by_code[ma_tour] = tour

    for booking in data["bookings"]:
        _normalize_booking(booking, tours_by_code, today)

    # Soft revalidation to drop stale voucher assignments after booking edits.
    _soft_revalidate_booking_vouchers(data, today)

    occupied_by_tour = {}
    for booking in data["bookings"]:
        _normalize_booking(booking, tours_by_code, today)
        ma_tour = str(booking.get("maTour", "")).strip()
        if ma_tour and booking.get("trangThai") not in CANCEL_BOOKING_STATUSES:
            occupied_by_tour[ma_tour] = occupied_by_tour.get(ma_tour, 0) + _safe_int(booking.get("soNguoi", 0))

    for tour in data["tours"]:
        ma_tour = str(tour.get("ma", "")).strip()
        occupied = occupied_by_tour.get(ma_tour, 0)
        _normalize_tour(tour, occupied, today)

    assignments = {}
    for tour in data["tours"]:
        ma_hdv = str(tour.get("hdvPhuTrach", "")).strip()
        if not ma_hdv:
            continue
        status = normalize_tour_status(tour.get("trangThai", ""), default=TOUR_STATUS_NOT_OPEN)
        if status in TERMINAL_TOUR_STATUSES:
            continue
        info = assignments.setdefault(ma_hdv, {"assigned": False, "in_progress": False})
        info["assigned"] = True
        if status == TOUR_STATUS_STARTED:
            info["in_progress"] = True

    for guide in data["hdv"]:
        _normalize_guide(guide, assignments)

    for user in data["users"]:
        user.setdefault("sdt", "")
        if not str(user.get("username", "")).strip():
            user["username"] = str(user.get("user", "")).strip()
        user["email"] = normalize_email(user.get("email", ""))
        user["trangThai"] = normalize_user_status(user.get("trangThai", user.get("status", "")))

    voucher_usage = {}
    for booking in data["bookings"]:
        if not _voucher_booking_is_counted(booking, include_pending_refund=True):
            continue
        voucher_code = str(booking.get("maVoucher", "")).strip().upper()
        if voucher_code:
            voucher_usage[voucher_code] = voucher_usage.get(voucher_code, 0) + 1

    for voucher in data["maVoucher"]:
        code = str(voucher.get("maVoucher", "")).strip().upper()
        _normalize_voucher(voucher, voucher_usage.get(code, 0), today)

    admin = data.get("admin", {})
    if isinstance(admin, dict):
        admin.setdefault("username", "admin")
        admin.setdefault("password", "123")

    return data


def sync_tour_booking_counts(datastore):
    """
    Đồng bộ lại số khách đã đặt cho các tour từ danh sách booking có hiệu lực,
    xóa hoặc vô hiệu hóa booking/review/notification của các tour đã bị xóa.
    """
    tours = getattr(datastore, "list_tours", [])
    active_tour_codes = {str(t.get("ma", "")).strip().upper() for t in tours if t.get("ma")}

    # 1. Xóa booking của tour đã bị xóa
    bookings = getattr(datastore, "list_bookings", [])
    valid_bookings = []
    for b in bookings:
        ma_tour_b = str(b.get("maTour", "")).strip().upper()
        if ma_tour_b in active_tour_codes:
            valid_bookings.append(b)
    datastore.data["bookings"] = valid_bookings

    # 2. Xóa review/notification của tour đã bị xóa
    if hasattr(datastore, "reviews") and datastore.reviews:
        datastore.reviews = [r for r in datastore.reviews if str(r.get("maTour", "")).strip().upper() in active_tour_codes]
    if hasattr(datastore, "notifications") and datastore.notifications:
        datastore.notifications = [n for n in datastore.notifications if not n.get("maTour") or str(n.get("maTour", "")).strip().upper() in active_tour_codes]

    # 3. Tính toán lại số khách đã đặt (soLuotDaDat) và sức chứa (soLuotMoBan)
    for tour in tours:
        ma_tour = tour.get("ma", "")
        occupied = datastore.get_occupied_seats(ma_tour)
        tour["soLuotDaDat"] = occupied
        tour["soLuotMoBan"] = max(0, _safe_int(tour.get("khach", 0)))
        # Xóa bỏ hoàn toàn chi phí dự kiến & thực tế khi đồng bộ
        tour.pop("chiPhiDuKien", None)
        tour.pop("chiPhiThucTe", None)


# ===== BEGIN core/datastore.py =====

import copy
import json
import os
import sqlite3
from collections.abc import Callable
from datetime import datetime



DEFAULT_DB_FILENAME = "travel_management.db"


class SQLiteDataStore:
    def __init__(
        self,
        path: str,
        rev_path: str | None = None,
        notif_path: str | None = None,
        *,
        db_path: str | None = None,
        default_data: dict | None = None,
        normalize_review_item: Callable | None = None,
        normalize_notification_item: Callable | None = None,
        text_normalizer: Callable | None = None,
    ):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `__init__` (  init  ).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            rev_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            notif_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            db_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            default_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            normalize_review_item: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            normalize_notification_item: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            text_normalizer: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        self.path = path
        self.rev_path = rev_path
        self.notif_path = notif_path
        self.db_path = db_path or os.path.join(os.path.dirname(path), DEFAULT_DB_FILENAME)
        self.default_data = copy.deepcopy(default_data or {"admin": {"username": "admin", "password": "123"}})
        self._normalize_review_item = normalize_review_item
        self._normalize_notification_item = normalize_notification_item
        self._text_normalizer = text_normalizer

        self.data = self._new_data_container()
        self.reviews: list[dict] = []
        self.notifications: list[dict] = []
        self.load()

    def _new_data_container(self) -> dict:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_new_data_container` ( new data container).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        data = copy.deepcopy(self.default_data)
        data.setdefault("hdv", [])
        data.setdefault("tours", [])
        data.setdefault("bookings", [])
        data.setdefault("users", [])
        data.setdefault("admin", {})
        data.setdefault("maVoucher", [])
        return data

    def _connect(self) -> sqlite3.Connection:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_connect` ( connect).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        folder = os.path.dirname(self.db_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_ensure_schema` ( ensure schema).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                state_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

    def _is_initialized(self, conn: sqlite3.Connection) -> bool:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_is_initialized` ( is initialized).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        row = conn.execute(
            "SELECT 1 FROM app_state WHERE state_key = ? LIMIT 1",
            ("data",),
        ).fetchone()
        return row is not None

    def _apply_text_normalizer(self, value):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_apply_text_normalizer` ( apply text normalizer).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if callable(self._text_normalizer):
            return self._text_normalizer(value)
        return value

    def _normalize_data_payload(self, data: dict) -> dict:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_normalize_data_payload` ( normalize data payload).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        payload = self._apply_text_normalizer(data)
        if not isinstance(payload, dict):
            payload = {}
        merged = self._new_data_container()
        merged.update(payload)
        system_normalized = apply_system_rules(merged)
        return normalize_business_state(system_normalized)

    def _normalize_collection(self, rows, normalizer: Callable | None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_normalize_collection` ( normalize collection).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            rows: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            normalizer: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if not isinstance(rows, list):
            return []
        normalized_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            item = self._apply_text_normalizer(row)
            if callable(normalizer):
                try:
                    item = normalizer(item, self)
                except TypeError:
                    item = normalizer(item)
            if isinstance(item, dict):
                normalized_rows.append(item)
        return normalized_rows

    def _read_legacy_json(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_read_legacy_json` ( read legacy json).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        data = self._new_data_container()
        reviews = []
        notifications = []

        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8-sig") as file:
                    loaded = json.load(file)
                if isinstance(loaded, dict):
                    data.update(loaded)
            except (OSError, json.JSONDecodeError):
                pass

        if self.rev_path and os.path.exists(self.rev_path):
            try:
                with open(self.rev_path, "r", encoding="utf-8-sig") as file:
                    loaded_reviews = json.load(file)
                if isinstance(loaded_reviews, list):
                    reviews = loaded_reviews
            except (OSError, json.JSONDecodeError):
                reviews = []

        if self.notif_path and os.path.exists(self.notif_path):
            try:
                with open(self.notif_path, "r", encoding="utf-8-sig") as file:
                    loaded_notifs = json.load(file)
                if isinstance(loaded_notifs, list):
                    notifications = loaded_notifs
            except (OSError, json.JSONDecodeError):
                notifications = []

        return data, reviews, notifications

    def _secure_password_fields(self, data: dict) -> dict:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_secure_password_fields` ( secure password fields).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        secured = copy.deepcopy(data)
        for guide in secured.get("hdv", []):
            guide["password"] = prepare_password_for_storage(guide.get("password", ""))
        for user in secured.get("users", []):
            user["password"] = prepare_password_for_storage(user.get("password", ""))

        admin = secured.get("admin", {})
        if isinstance(admin, dict):
            admin["password"] = prepare_password_for_storage(admin.get("password", ""))
        return secured

    def _write_payload(self, conn: sqlite3.Connection, key: str, value) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_write_payload` ( write payload).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            key: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        conn.execute(
            """
            INSERT INTO app_state (state_key, payload, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(state_key) DO UPDATE SET
                payload = excluded.payload,
                updated_at = excluded.updated_at
            """,
            (
                key,
                json.dumps(value, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

    def _bootstrap_from_legacy_json(self, conn: sqlite3.Connection) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bootstrap_from_legacy_json` ( bootstrap from legacy json).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        raw_data, raw_reviews, raw_notifications = self._read_legacy_json()
        normalized_data = self._normalize_data_payload(raw_data)
        secured_data = self._secure_password_fields(normalized_data)

        self._write_payload(conn, "data", secured_data)
        self._write_payload(
            conn,
            "reviews",
            self._normalize_collection(raw_reviews, self._normalize_review_item),
        )
        self._write_payload(
            conn,
            "notifications",
            self._normalize_collection(raw_notifications, self._normalize_notification_item),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO schema_migrations (migration_name, applied_at)
            VALUES (?, ?)
            """,
            ("json_to_sqlite", datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()

    def _read_payload(self, conn: sqlite3.Connection, key: str, fallback):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_read_payload` ( read payload).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            conn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            key: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fallback: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        row = conn.execute(
            "SELECT payload FROM app_state WHERE state_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return fallback
        try:
            return json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError):
            return fallback

    def load(self) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `load` (load).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        with self._connect() as conn:
            self._ensure_schema(conn)
            if not self._is_initialized(conn):
                self._bootstrap_from_legacy_json(conn)

            self.data = self._normalize_data_payload(self._read_payload(conn, "data", self._new_data_container()))
            self.reviews = self._normalize_collection(
                self._read_payload(conn, "reviews", []),
                self._normalize_review_item,
            )
            self.notifications = self._normalize_collection(
                self._read_payload(conn, "notifications", []),
                self._normalize_notification_item,
            )

    def save(self) -> None:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save` (save).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sync_tour_booking_counts(self)
        normalized_data = self._normalize_data_payload(self.data)
        secured_data = self._secure_password_fields(normalized_data)

        with self._connect() as conn:
            self._ensure_schema(conn)
            self._write_payload(conn, "data", secured_data)
            self._write_payload(conn, "reviews", self.reviews)
            self._write_payload(conn, "notifications", self.notifications)
            conn.commit()

        self.data = secured_data
        self._sync_legacy_json_files()

    def _sync_legacy_json_files(self) -> None:
        """
        Đồng bộ ngược dữ liệu về JSON legacy để tương thích với luồng UI cũ.
        Không raise exception để tránh làm gián đoạn thao tác nghiệp vụ chính.
        """
        try:
            if self.path:
                folder = os.path.dirname(self.path)
                if folder and not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)
                with open(self.path, "w", encoding="utf-8") as file:
                    json.dump(self.data, file, ensure_ascii=False, indent=2)
        except OSError:
            pass

        try:
            if self.rev_path:
                folder = os.path.dirname(self.rev_path)
                if folder and not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)
                with open(self.rev_path, "w", encoding="utf-8") as file:
                    json.dump(self.reviews, file, ensure_ascii=False, indent=2)
        except OSError:
            pass

        try:
            if self.notif_path:
                folder = os.path.dirname(self.notif_path)
                if folder and not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)
                with open(self.notif_path, "w", encoding="utf-8") as file:
                    json.dump(self.notifications, file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    @property
    def list_hdv(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_hdv` (list hdv).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["hdv"]

    @property
    def list_tours(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_tours` (list tours).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["tours"]

    @property
    def list_bookings(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_bookings` (list bookings).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["bookings"]

    @property
    def list_users(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_users` (list users).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["users"]

    @property
    def list_reviews(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_reviews` (list reviews).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.reviews

    @property
    def list_notifications(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_notifications` (list notifications).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.notifications

    @property
    def list_vouchers(self):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `list_vouchers` (list vouchers).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return self.data["maVoucher"]

    def find_admin(self, username):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_admin` (find admin).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        admin = self.data.get("admin", {})
        if isinstance(admin, dict) and str(admin.get("username", "")).strip() == str(username or "").strip():
            return admin
        return None

    def find_user(self, username):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_user` (find user).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(username or "").strip().lower()
        return next((u for u in self.list_users if str(u.get("username", "")).strip().lower() == normalized), None)

    def find_hdv(self, ma_hdv):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_hdv` (find hdv).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(ma_hdv or "").strip().upper()
        return next((h for h in self.list_hdv if str(h.get("maHDV", "")).strip().upper() == normalized), None)

    def get_users_for_actor(self, actor: str = "", role: str = "user"):
        if _is_admin_role(role):
            return list(self.list_users)
        if _is_customer_role(role):
            user = self.find_user(actor)
            return [user] if isinstance(user, dict) else []
        return []

    def find_tour(self, ma_tour):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_tour` (find tour).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(ma_tour or "").strip().upper()
        return next((t for t in self.list_tours if str(t.get("ma", "")).strip().upper() == normalized), None)

    def find_voucher(self, code):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `find_voucher` (find voucher).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(code or "").strip().upper()
        if not normalized:
            return None
        return next(
            (
                voucher
                for voucher in self.list_vouchers
                if str(voucher.get("maVoucher", "")).strip().upper() == normalized
            ),
            None,
        )

    def get_bookings_by_tour(self, ma_tour, actor: str = "", role: str = "admin"):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `get_bookings_by_tour` (get bookings by tour).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized = str(ma_tour or "").strip().upper()
        tour = self.find_tour(normalized)
        if _is_guide_role(role) and not guide_can_access_tour(actor, role, tour):
            return []
        if _is_customer_role(role):
            return [
                booking
                for booking in self.list_bookings
                if str(booking.get("maTour", "")).strip().upper() == normalized
                and booking_belongs_to_user(booking, actor)
            ]
        return [booking for booking in self.list_bookings if str(booking.get("maTour", "")).strip().upper() == normalized]

    def get_occupied_seats(self, ma_tour):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `get_occupied_seats` (get occupied seats).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        total = 0
        for booking in self.get_bookings_by_tour(ma_tour):
            refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
            if booking.get("trangThai") in CANCEL_BOOKING_STATUSES and refund_status != "Từ chối":
                continue
            try:
                total += int(str(booking.get("soNguoi", 0)).strip())
            except (TypeError, ValueError):
                continue
        return total

    def get_tours_for_user(self, actor: str = "", role: str = "user"):
        tours = []
        for tour in self.list_tours:
            status = normalize_tour_status(tour.get("trangThai", ""), default=TOUR_STATUS_NOT_OPEN)
            start_date = parse_ddmmyyyy(tour.get("ngay"))
            if _is_admin_role(role):
                tours.append(tour)
                continue
            if _is_guide_role(role):
                if guide_can_access_tour(actor, role, tour):
                    tours.append(tour)
                continue
            if status == TOUR_STATUS_CANCELLED:
                continue
            if status == TOUR_STATUS_NOT_OPEN:
                tours.append(tour)
                continue
            occupied = self.get_occupied_seats(tour.get("ma", ""))
            capacity = max(1, safe_int(tour.get("khach", 1)))
            if status in BOOKABLE_TOUR_STATUSES and is_booking_allowed(status, start_date, occupied=occupied, capacity=capacity):
                tours.append(tour)
                continue
            if status == TOUR_STATUS_FULL:
                tours.append(tour)
        return tours

    def get_notifications_for_actor(self, actor: str = "", role: str = "user"):
        if _is_admin_role(role):
            return list(self.list_notifications)
        if _is_guide_role(role):
            guide_id = str(actor or "").strip().upper()
            return [
                n
                for n in self.list_notifications
                if str(n.get("maHDV", "")).strip().upper() == guide_id
            ]
        return get_notifications_for_user(self, username=str(actor or "").strip(), role=role, actor=actor)


class JSONDataStore(SQLiteDataStore):
    """
    Biến thể datastore chỉ dùng JSON.
    Luôn đọc/ghi trực tiếp các file JSON legacy, không truy cập SQLite.
    """

    def load(self) -> None:
        raw_data, raw_reviews, raw_notifications = self._read_legacy_json()
        self.data = self._normalize_data_payload(raw_data)
        self.reviews = self._normalize_collection(raw_reviews, self._normalize_review_item)
        self.notifications = self._normalize_collection(raw_notifications, self._normalize_notification_item)

    def save(self) -> None:
        sync_tour_booking_counts(self)
        normalized_data = self._normalize_data_payload(self.data)
        self.data = self._secure_password_fields(normalized_data)
        self.reviews = self._normalize_collection(self.reviews, self._normalize_review_item)
        self.notifications = self._normalize_collection(self.notifications, self._normalize_notification_item)
        self._sync_legacy_json_files()

# ===== BEGIN core/auth.py =====

from dataclasses import dataclass


@dataclass(slots=True)
class ServiceResult:
    success: bool
    message: str
    level: str = "info"
    username: str = ""
    display_name: str = ""
    role: str = ""


class AuthService:
    def __init__(self, datastore):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `__init__` (  init  ).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        self.datastore = datastore

    def authenticate(self, role: str, username: str, password: str) -> ServiceResult:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `authenticate` (authenticate).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized_username = normalize_username(username)

        if not normalized_username or not str(password or "").strip():
            return ServiceResult(False, "Vui lòng nhập tài khoản và mật khẩu.", level="warning")

        self.datastore.load()
        record = self._resolve_account(role, normalized_username)

        if not record:
            write_activity_log(
                action="LOGIN",
                actor=normalized_username,
                role=role,
                status="FAILED",
                detail="Không tìm thấy tài khoản.",
                datastore=self.datastore,
            )
            return ServiceResult(False, "Sai tài khoản hoặc mật khẩu!", level="error")

        stored_password = record.get("password", "")
        if not password_matches(stored_password, password):
            write_activity_log(
                action="LOGIN",
                actor=normalized_username,
                role=role,
                status="FAILED",
                detail="Mật khẩu không hợp lệ.",
                datastore=self.datastore,
            )
            return ServiceResult(False, "Sai tài khoản hoặc mật khẩu!", level="error")

        if _is_guide_role(role):
            guide_status = normalize_guide_status(record.get("trangThai", record.get("status", "")))
            if guide_status in {GUIDE_STATUS_TEMP_OFF, GUIDE_STATUS_INACTIVE, GUIDE_STATUS_BLOCKED, GUIDE_STATUS_HIDDEN}:
                return ServiceResult(False, f"Tài khoản HDV đang ở trạng thái '{guide_status}', không thể đăng nhập.", level="warning")
        if _is_customer_role(role):
            user_status = normalize_user_status(record.get("trangThai", record.get("status", "")))
            if user_status in {USER_STATUS_BLOCKED, USER_STATUS_INACTIVE, USER_STATUS_HIDDEN}:
                return ServiceResult(False, f"Tài khoản khách hàng đang ở trạng thái '{user_status}', không thể đăng nhập.", level="warning")

        migrated = False
        secured_password = upgrade_password_hash(stored_password, password)
        if secured_password and secured_password != stored_password:
            record["password"] = secured_password
            migrated = True

        if migrated:
            self.datastore.save()

        result = ServiceResult(
            True,
            f"Chào mừng {self._display_name(role, record, normalized_username)}!",
            username=self._account_username(role, record, normalized_username),
            display_name=self._display_name(role, record, normalized_username),
            role=role,
        )

        write_activity_log(
            action="LOGIN",
            actor=normalized_username,
            role=role,
            status="SUCCESS",
            detail="Đăng nhập thành công.",
            datastore=self.datastore,
        )
        return result

    def register_user(
        self,
        username: str,
        password: str,
        fullname: str,
        phone: str,
        email: str = "",
    ) -> ServiceResult:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `register_user` (register user).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        normalized_username = normalize_username(username)
        normalized_fullname = normalize_fullname(fullname)
        normalized_phone = normalize_phone(phone)
        normalized_email = normalize_email(email)

        if not normalized_username or not str(password or "").strip() or not normalized_fullname:
            return ServiceResult(False, "Vui lòng nhập đủ các trường bắt buộc!", level="warning")

        if not is_valid_username(normalized_username):
            return ServiceResult(
                False,
                "Tên đăng nhập phải dài 3-30 ký tự và chỉ gồm chữ, số, dấu chấm, gạch dưới hoặc gạch ngang.",
                level="warning",
            )

        if not is_valid_password(password):
            return ServiceResult(False, "Mật khẩu phải có ít nhất 3 ký tự.", level="warning")

        if not is_valid_fullname(normalized_fullname):
            return ServiceResult(False, "Họ và tên phải có ít nhất 3 ký tự.", level="warning")

        if not is_valid_phone(normalized_phone):
            return ServiceResult(
                False,
                "Số điện thoại phải có 10 số, bắt đầu bằng 0 và dùng đầu số di động Việt Nam hợp lệ.",
                level="warning",
            )
        if normalized_email and not is_valid_email(normalized_email):
            return ServiceResult(False, "Email không đúng định dạng.", level="warning")

        self.datastore.load()
        users = getattr(self.datastore, "list_users", self.datastore.data.get("users", []))
        admin = self.datastore.data.get("admin", {})
        if str(admin.get("username", "")).strip().lower() == normalized_username.lower():
            return ServiceResult(False, "Tên đăng nhập đã tồn tại!", level="error")
        guide_conflict = next(
            (
                hdv
                for hdv in getattr(self.datastore, "list_hdv", self.datastore.data.get("hdv", []))
                if normalized_username.lower()
                in {
                    str(hdv.get("maHDV", "")).strip().lower(),
                    str(hdv.get("username", "")).strip().lower(),
                }
            ),
            None,
        )
        if guide_conflict:
            return ServiceResult(False, "Tên đăng nhập bị trùng với tài khoản hướng dẫn viên.", level="error")
        if self.datastore.find_user(normalized_username) or any(
            str(user.get("username", "")).lower() == normalized_username.lower()
            for user in users
        ):
            write_activity_log(
                action="REGISTER_USER",
                actor=normalized_username,
                role="user",
                status="FAILED",
                detail="Tên đăng nhập đã tồn tại.",
                datastore=self.datastore,
            )
            return ServiceResult(False, "Tên đăng nhập đã tồn tại!", level="error")
        if normalized_email and any(
            normalize_email(user.get("email", "")) == normalized_email
            for user in users
        ):
            return ServiceResult(False, "Email đã được sử dụng bởi tài khoản khác.", level="warning")
        if normalized_email:
            admin_email = normalize_email(admin.get("email", ""))
            if admin_email and admin_email == normalized_email:
                return ServiceResult(False, "Email đã được sử dụng bởi tài khoản khác.", level="warning")
            if any(
                normalize_email(hdv.get("email", "")) == normalized_email
                for hdv in getattr(self.datastore, "list_hdv", self.datastore.data.get("hdv", []))
            ):
                return ServiceResult(False, "Email đã được sử dụng bởi tài khoản khác.", level="warning")

        self.datastore.data.setdefault("users", []).append(
            {
                "username": normalized_username,
                "password": prepare_password_for_storage(password),
                "fullname": normalized_fullname,
                "sdt": normalized_phone,
                "email": normalized_email,
                "trangThai": USER_STATUS_ACTIVE,
            }
        )
        self.datastore.save()

        write_activity_log(
            action="REGISTER_USER",
            actor=normalized_username,
            role="user",
            status="SUCCESS",
            detail="Tạo tài khoản khách hàng mới.",
            datastore=self.datastore,
        )
        return ServiceResult(
            True,
            "Đăng ký tài khoản thành công!",
            username=normalized_username,
            display_name=normalized_fullname,
            role="user",
        )

    def _resolve_account(self, role: str, username: str):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_resolve_account` ( resolve account).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if _is_admin_role(role):
            admin = self.datastore.data.get("admin", {})
            return admin if str(username).lower() == str(admin.get("username", "")).lower() else None
        if _is_guide_role(role):
            account = self.datastore.find_hdv(username)
            if account:
                return account
            username_upper = str(username).upper()
            return next(
                (
                    h
                    for h in self.datastore.list_hdv
                    if username_upper
                    in {
                        str(h.get("maHDV", "")).upper(),
                        str(h.get("username", "")).upper(),
                    }
                ),
                None,
            )
        if _is_customer_role(role):
            account = self.datastore.find_user(username)
            if account:
                return account
            username_lower = str(username).lower()
            return next(
                (u for u in self.datastore.list_users if str(u.get("username", "")).lower() == username_lower),
                None,
            )
        return None

    @staticmethod
    def _account_username(role: str, record: dict, fallback: str) -> str:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_account_username` ( account username).
        Tham số:
            role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            record: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fallback: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if _is_guide_role(role):
            return record.get("maHDV", fallback)
        if _is_customer_role(role):
            return record.get("username", fallback)
        if _is_admin_role(role):
            return record.get("username", fallback)
        return fallback

    @staticmethod
    def _display_name(role: str, record: dict, fallback: str) -> str:
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_display_name` ( display name).
        Tham số:
            role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            record: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fallback: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Giá trị theo khai báo kiểu trả về của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if _is_guide_role(role):
            return record.get("tenHDV", fallback)
        if _is_customer_role(role):
            return record.get("fullname", fallback)
        if _is_admin_role(role):
            return record.get("fullname", fallback)
        return fallback

# ===== BEGIN core/tk_text.py =====

import re
import tkinter as tk
from tkinter import messagebox, ttk


_PATCHED = False
_MARKERS = (
    "\u00c3",
    "\u00c4",
    "\u00c2",
    "\u00ca",
    "\u00d4",
    "\u00c6",
    "\u00e1",
    "\u00e0",
    "\u00e2",
    "\u00f0",
    "\u2122",
    "\u0153",
    "\u0178",
    "\u00ba",
    "\u00bb",
    "\u2014",
    "\u2019",
    "\u201d",
    "\u0192",
    "\u201e",
    "\u02dc",
    "\u20ac",
)
# Chỉ tách whitespace chuẩn để giữ nguyên NBSP (\u00A0) trong token mojibake
# kiểu "Ã ", từ đó _fix_token có thể phục hồi đúng thành "à".
_TOKEN_SPLIT_RE = re.compile(r"([ \t\r\n]+)")
_SECOND_ORDER_REPLACEMENTS = (
    ("\u0102\u0192", "\u00c3"),
    ("\u0102\u201e", "\u00c4"),
    ("\u0102\u00c2", "\u00c2"),
    ("\u0102\u00ca", "\u00ca"),
    ("\u0102\u00d4", "\u00d4"),
    ("\u0102\u00c6", "\u00c6"),
    ("\u201e", "\u00c4"),
)
_MANUAL_REPLACEMENTS = {
    "\u00c2\u00a0": " ",
    "\u00e2\u20ac\u201c": "-",
    "\u00e2\u20ac\u201d": "\u2014",
    "\u00e2\u20ac\u2122": "'",
    "\u00e2\u20ac\u0153": '"',
    "\u00c3\u00c6": "\u00c3",
    "\u00e1\u00bb\u00c6": "\u1ec3",
    "\u00c1\u00bb\u00c6": "\u1ec2",
}
_CP1252_EXTENDED_CHARS = {
    "\u2018",
    "\u2019",
    "\u201c",
    "\u201d",
    "\u20ac",
    "\u2122",
    "\u0153",
    "\u0178",
    "\u0192",
    "\u201e",
    "\u02dc",
}
_MOJIBAKE_PAIR_LEADS = {
    "\u00c3",
    "\u00c4",
    "\u00c2",
    "\u00ca",
    "\u00d4",
    "\u00c6",
}


def _decode_mojibake_pairs(text: str) -> str:
    """
    Sửa nhanh các cặp ký tự mojibake phổ biến như:
    - Ã + NBSP -> à
    - Ä + ‘ -> đ
    """
    if not text:
        return text

    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if i + 1 < n and text[i] in _MOJIBAKE_PAIR_LEADS:
            pair = text[i : i + 2]
            repaired = None
            for enc in ("cp1252", "latin-1"):
                try:
                    candidate = pair.encode(enc).decode("utf-8")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue
                if candidate and candidate != pair:
                    repaired = candidate
                    break
            if repaired is not None:
                out.append(repaired)
                i += 2
                continue

        out.append(text[i])
        i += 1
    return "".join(out)


def _fix_token(token: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_fix_token` ( fix token).
    Tham số:
        token: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not token or not any(marker in token for marker in _MARKERS):
        return token

    normalized = token
    for broken, repaired in _SECOND_ORDER_REPLACEMENTS:
        normalized = normalized.replace(broken, repaired)
    if normalized != token:
        token = normalized

    for source_encoding in ("cp1252", "latin-1"):
        try:
            fixed = token.encode(source_encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if fixed != token:
            return fixed
    return token


def fix_mojibake(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `fix_mojibake` (fix mojibake).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if isinstance(value, str):
        # Bảo vệ chữ Việt hợp lệ: chỉ cố sửa khi có dấu hiệu mojibake rõ ràng.
        suspicious_markers = ("\u00c3", "\u00c4", "\u00c2", "\u00ca", "\u00d4", "\u00c6", "\ufffd")
        if not any(marker in value for marker in suspicious_markers):
            return value

        text = value.strip()
        if not text or not any(marker in text for marker in _MARKERS):
            return value
        # Xử lý theo các đoạn ký tự <= 255 để không bị lỗi khi token trộn giữa
        # mojibake (cp1252) và ký tự Unicode tiếng Việt hợp lệ (>255).
        buffer: list[str] = []
        normalized_parts: list[str] = []
        for ch in value:
            if ord(ch) <= 255 or ch in _CP1252_EXTENDED_CHARS:
                buffer.append(ch)
                continue
            if buffer:
                normalized_parts.append(_fix_token("".join(buffer)))
                buffer = []
            normalized_parts.append(ch)
        if buffer:
            normalized_parts.append(_fix_token("".join(buffer)))

        fixed = "".join(normalized_parts)
        fixed = _decode_mojibake_pairs(fixed)
        for broken, repaired in _MANUAL_REPLACEMENTS.items():
            fixed = fixed.replace(broken, repaired)
        return fixed
    if isinstance(value, (list, tuple)):
        fixed = [fix_mojibake(item) for item in value]
        return type(value)(fixed)
    if isinstance(value, dict):
        return {key: fix_mojibake(item) for key, item in value.items()}
    return value


def enable_tk_text_autofix():
    """
    Mục đích:
        Thực hiện xử lý cho hàm `enable_tk_text_autofix` (enable tk text autofix).
    Tham số:
        Không có.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    def patch_widget_init(widget_class):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `patch_widget_init` (patch widget init).
        Tham số:
            widget_class: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        original_init = widget_class.__init__

        def wrapped_init(self, *args, **kwargs):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `wrapped_init` (wrapped init).
            Tham số:
                self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                *args: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                **kwargs: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            if "text" in kwargs:
                kwargs["text"] = fix_mojibake(kwargs["text"])
            return original_init(self, *args, **kwargs)

        widget_class.__init__ = wrapped_init

    for widget_class in (
        tk.Label,
        tk.Button,
        tk.LabelFrame,
        tk.Checkbutton,
        tk.Radiobutton,
        tk.Message,
        ttk.Label,
        ttk.Button,
        ttk.Checkbutton,
        ttk.Radiobutton,
        ttk.LabelFrame,
    ):
        patch_widget_init(widget_class)

    original_tk_title = tk.Wm.title

    def wrapped_title(self, string=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_title` (wrapped title).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            string: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if string is not None:
            string = fix_mojibake(string)
        return original_tk_title(self, string)

    tk.Wm.title = wrapped_title

    original_tree_heading = ttk.Treeview.heading

    def wrapped_heading(self, column, option=None, **kwargs):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_heading` (wrapped heading).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            column: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            option: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            **kwargs: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if "text" in kwargs:
            kwargs["text"] = fix_mojibake(kwargs["text"])
        return original_tree_heading(self, column, option, **kwargs)

    ttk.Treeview.heading = wrapped_heading

    original_tree_insert = ttk.Treeview.insert

    def wrapped_insert(self, parent, index, iid=None, **kwargs):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_insert` (wrapped insert).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            index: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            iid: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            **kwargs: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if "values" in kwargs:
            kwargs["values"] = fix_mojibake(kwargs["values"])
        if "text" in kwargs:
            kwargs["text"] = fix_mojibake(kwargs["text"])
        return original_tree_insert(self, parent, index, iid=iid, **kwargs)

    ttk.Treeview.insert = wrapped_insert

    original_stringvar_init = tk.StringVar.__init__

    def wrapped_stringvar_init(self, master=None, value=None, name=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_stringvar_init` (wrapped stringvar init).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            master: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            name: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return original_stringvar_init(self, master=master, value=fix_mojibake(value), name=name)

    tk.StringVar.__init__ = wrapped_stringvar_init

    original_variable_set = tk.Variable.set

    def wrapped_variable_set(self, value):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_variable_set` (wrapped variable set).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return original_variable_set(self, fix_mojibake(value))

    tk.Variable.set = wrapped_variable_set

    original_showinfo = messagebox.showinfo
    original_showwarning = messagebox.showwarning
    original_showerror = messagebox.showerror
    original_askyesno = messagebox.askyesno

    def wrap_messagebox(func):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrap_messagebox` (wrap messagebox).
        Tham số:
            func: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        def wrapped(title=None, message=None, *args, **kwargs):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `wrapped` (wrapped).
            Tham số:
                title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                message: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                *args: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                **kwargs: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            return func(fix_mojibake(title), fix_mojibake(message), *args, **kwargs)

        return wrapped

    messagebox.showinfo = wrap_messagebox(original_showinfo)
    messagebox.showwarning = wrap_messagebox(original_showwarning)
    messagebox.showerror = wrap_messagebox(original_showerror)
    messagebox.askyesno = wrap_messagebox(original_askyesno)


