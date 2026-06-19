import os
import re
import base64
import math
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import threading
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import urlopen

from GUI.common.rounded_button import RoundedButton
from GUI.common.weather_popup import open_tour_weather_popup
from core.app import (
    apply_payment as service_apply_payment,
    build_voucher_quote as service_build_voucher_quote,
    calculate_age_discount,
    cancel_booking as service_cancel_booking,
    create_booking as service_create_booking,
    create_review as service_create_review,
    normalize_passenger_breakdown,
    BOOKING_STATE_COMPLETED,
    JSONDataStore,
    booking_state_from_status,
    fix_mojibake,
    is_booking_allowed,
    normalize_tour_status,
    normalize_notification_item as core_normalize_notification_item,
    normalize_review_item as core_normalize_review_item,
    prepare_password_for_storage,
    is_valid_fullname,
    is_valid_password,
    is_valid_phone,
    safe_int,
    TOUR_STATUS_NOT_OPEN,
    TOUR_STATUS_OPEN,
    TOUR_STATUS_FULL,
    TOUR_STATUS_STARTED,
    TOUR_STATUS_COMPLETED,
    TOUR_STATUS_CANCELLED,
    show_wrapped_message,
    show_detailed_notification_popup,
)

# =========================
# VALIDATION & HELPER
# =========================

def booking_payment_status(total_amount, paid_amount):
    total = max(0, safe_int(total_amount))
    paid = max(0, safe_int(paid_amount))
    if paid <= 0:
        return "Mới tạo"
    if total > 0 and paid < total:
        return "Đã cọc"
    return "Đã thanh toán"


def build_cash_policy_notice(ngay_khoi_hanh):
    base_msg = "Tiền mặt: nếu chưa đặt cọc/thanh toán trước hạn, booking sẽ bị hủy tự động."
    try:
        depart_date = datetime.strptime(str(ngay_khoi_hanh or "").strip(), "%d/%m/%Y")
        deadline = (depart_date - timedelta(days=15)).strftime("%d/%m/%Y")
        return f"Tiền mặt: hạn chót đặt cọc/thanh toán là {deadline}. Booking quá hạn sẽ bị hủy."
    except ValueError:
        return base_msg


def short_ui_error(exc, fallback="Không thể gọi API QR. Vui lòng thử lại sau."):
    text = " ".join(str(exc or "").split())
    if not text:
        return fallback
    return f"{text[:96]}..." if len(text) > 96 else text


def parse_ddmmyyyy(value):
    try:
        return datetime.strptime(str(value or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def is_tour_visible_to_user(tour, ql=None):
    """Kiểm tra tour có được hiển thị cho khách hàng hay không."""
    status = normalize_tour_status(str(tour.get("trangThai", "")).strip())
    if status != TOUR_STATUS_OPEN:
        return False

    depart_date = parse_ddmmyyyy(tour.get("ngay", ""))
    if depart_date is None or depart_date <= datetime.now().date():
        return False

    total = safe_int(tour.get("khach", 0))
    if "khach" not in tour and "soLuotMoBan" not in tour:
        total = 99
    
    booked = safe_int(ql.get_occupied_seats(tour.get("ma", ""))) if ql else safe_int(tour.get("soLuotDaDat", 0))
    open_slots = safe_int(tour.get("soLuotMoBan", total))
    capacity = open_slots if open_slots > 0 else total

    if capacity <= 0 or booked >= capacity:
        return False

    return True


# =========================
# THEME & CONSTANTS
# =========================
THEME = {
    "bg": "#f1f5f9",
    "surface": "#ffffff",
    "sidebar": "#0b1220",
    "sidebar_hover": "#16233b",
    "sidebar_active": "#1e3a8a",
    "primary": "#2563eb",
    "success": "#059669",
    "danger": "#dc2626",
    "warning": "#d97706",
    "text": "#0f172a",
    "muted": "#64748b",
    "border": "#d2dae6",
    "header_bg": "#ffffff",
    "status_bg": "#e8eef8",
    "heading_bg": "#e2e8f0",
    "note_bg": "#fff7ed",
    "note_fg": "#9a3412",
    "zebra_even": "#f8fbff",
    "zebra_odd": "#ffffff",
}

TOUR_BOOKABLE_STATUSES = [TOUR_STATUS_OPEN]
TOUR_LOCK_CANCEL_STATUSES = ["Đang diễn ra", "Đã kết thúc", "Đã hủy"]
BOOKING_CANCEL_STATUSES = ["Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]
PAYMENT_METHODS = ["Tiền mặt", "Chuyển khoản"]

TRANSFER_QR_CONFIG = {
    "bank_id": os.getenv("TRAVEL_BANK_ID", "ACB"),
    "account_no": os.getenv("TRAVEL_BANK_ACCOUNT", "41389377"),
    "account_name": os.getenv("TRAVEL_BANK_NAME", "VIETNAM TRAVEL"),
    "template": os.getenv("TRAVEL_QR_TEMPLATE", "compact"),
}

def build_transfer_qr_url(amount, transfer_content):
    bank_id = str(TRANSFER_QR_CONFIG.get("bank_id", "")).strip()
    account_no = str(TRANSFER_QR_CONFIG.get("account_no", "")).strip()
    account_name = str(TRANSFER_QR_CONFIG.get("account_name", "")).strip()
    template = str(TRANSFER_QR_CONFIG.get("template", "compact2")).strip() or "compact2"

    if not bank_id or not account_no:
        raise ValueError("Thiếu cấu hình ngân hàng nhận chuyển khoản.")

    amount_value = max(0, safe_int(amount))
    add_info = quote_plus(str(transfer_content or "").strip())
    account_name_q = quote_plus(account_name)
    return (
        f"https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.png"
        f"?amount={amount_value}&addInfo={add_info}&accountName={account_name_q}"
    )


def scale_photo_to_square(photo, max_size_px=220):
    max_size = max(80, safe_int(max_size_px))
    width = max(1, photo.width())
    height = max(1, photo.height())
    ratio = max(width / max_size, height / max_size)
    step = max(1, math.ceil(ratio))
    if step > 1:
        return photo.subsample(step, step)
    return photo


def fetch_transfer_qr_photo(qr_url, max_size_px=220):
    with urlopen(qr_url, timeout=10) as response:
        payload = response.read()
    if not payload:
        raise ValueError("API QR không trả dữ liệu ảnh.")
    raw_photo = tk.PhotoImage(data=base64.b64encode(payload).decode("ascii"))
    return scale_photo_to_square(raw_photo, max_size_px)

# =========================
# PATH DỮ LIỆU
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
RAW_DATA_DIR = os.getenv("TRAVEL_DATA_DIR", os.path.join(PROJECT_DIR, "data"))
DATA_DIR = RAW_DATA_DIR if os.path.isabs(RAW_DATA_DIR) else os.path.join(PROJECT_DIR, RAW_DATA_DIR)
DATA_FILE = os.path.join(DATA_DIR, "vietnam_travel_data.json")
REVIEWS_FILE = os.path.join(DATA_DIR, "vietnam_travel_reviews.json")
NOTIF_FILE = os.path.join(DATA_DIR, "vietnam_travel_notifications.json")

DEFAULT_DATA = {
    "hdv": [
        {
            "maHDV": "HDV01", "tenHDV": "Nguyễn Văn Anh", "sdt": "0901234567",
            "email": "anh@travel.com", "kn": "5", "gioiTinh": "Nam",
            "khuVuc": "Miền Bắc", "trangThai": "Sẵn sàng", "password": "123",
            "total_reviews": 0, "avg_rating": 0, "skill_score": 0,
            "attitude_score": 0, "problem_solving_score": 0
        }
    ],
    "tours": [],
    "bookings": [],
    "users": [],
    "admin": {"username": "admin", "password": "123"}
}


# =========================
# DATA STORE
# =========================

def normalize_notification_item(n, datastore=None):
    return core_normalize_notification_item(
        n, datastore=datastore,
        content_keys=("content", "noiDung", "thongBao", "message", "moTa"),
    )

def normalize_review_item(r):
    return core_normalize_review_item(r, include_rating=True, include_ma_hdv=True)


class DataStore(JSONDataStore):
    def __init__(self, path=DATA_FILE, rev_path=REVIEWS_FILE, notif_path=NOTIF_FILE):
        super().__init__(
            path=path,
            rev_path=rev_path,
            notif_path=notif_path,
            default_data=DEFAULT_DATA,
            normalize_review_item=normalize_review_item,
            normalize_notification_item=normalize_notification_item,
            text_normalizer=fix_mojibake,
        )


# =========================
# UI HELPER
# =========================
def apply_zebra(tree):
    tree.tag_configure("odd", background=THEME["zebra_odd"])
    tree.tag_configure("even", background=THEME["zebra_even"])
    for i, item in enumerate(tree.get_children()):
        tree.item(item, tags=(("even" if i % 2 == 0 else "odd"),))

def copy_to_clipboard(root, text, button_widget=None, original_text=""):
    root.clipboard_clear()
    root.clipboard_append(text)
    if button_widget and original_text:
        button_widget.config(text="Đã sao chép!")
        root.after(1500, lambda: button_widget.config(text=original_text))

def style_button(parent, text, bg, command, fg="white"):
    return RoundedButton(
        parent, text=text, bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
        relief="flat", bd=0, cursor="hand2", font=("Times New Roman", 11, "bold"),
        padx=14, pady=9, highlightthickness=1, highlightbackground=bg,
        highlightcolor=bg, command=command,
    )

def configure_ui_fonts(root):
    default_font = ("Times New Roman", 12)
    heading_font = ("Times New Roman", 12, "bold")
    root.option_add("*Font", default_font)
    style = ttk.Style(root)
    style.configure("TLabel", font=default_font)
    style.configure("TButton", font=heading_font)
    style.configure("TEntry", font=default_font)
    style.configure("TCombobox", font=default_font)

def bind_autohide_scrollbar(widget, scrollbar, orient="vertical"):
    """Tự động ẩn/hiện scrollbar theo trạng thái tràn nội dung."""
    is_vertical = str(orient).lower().startswith("v")
    pack_side = "right" if is_vertical else "bottom"
    pack_fill = "y" if is_vertical else "x"
    state = {"visible": False}

    def _show():
        if not state["visible"]:
            scrollbar.pack(side=pack_side, fill=pack_fill, padx=0, pady=0)
            state["visible"] = True

    def _hide():
        if state["visible"]:
            scrollbar.pack_forget()
            state["visible"] = False

    def _set(first, last):
        scrollbar.set(first, last)
        try:
            start, end = float(first), float(last)
        except (TypeError, ValueError):
            _show()
            return
        if start <= 0.0 and end >= 1.0:
            _hide()
        else:
            _show()

    if is_vertical:
        widget.configure(yscrollcommand=_set)
    else:
        widget.configure(xscrollcommand=_set)

    def _refresh():
        try:
            start, end = widget.yview() if is_vertical else widget.xview()
            _set(start, end)
        except (tk.TclError, ValueError, TypeError, AttributeError):
            _show()

    _show()
    widget.after_idle(_refresh)
    return _refresh


# =========================
# USER UI
# =========================

def khoi_tao_khach(root, user_data=None):
    if not user_data:
        user_data = {"username": "Khach", "name": "Khách hàng", "fullname": "Khách hàng", "sdt": ""}

    app = {
        "root": root,
        "ql": DataStore(),
        "user": user_data,
        "container": None,
        "content_canvas": None,
        "tv_tours": None,
        "detail_var": tk.StringVar(value="Chọn một tour để xem chi tiết và đăng ký."),
        "active_menu_btn": None,
        "page_title_var": tk.StringVar(value="Khách hàng"),
        "page_subtitle_var": tk.StringVar(value="Khám phá tour, theo dõi booking và quản lý thông tin tài khoản."),
        "status_var": tk.StringVar(value="Sẵn sàng"),
        "status_label": None,
        "header_badge": None,
        "login_time": datetime.now(),
        "login_time_var": tk.StringVar(),
        "current_tab": "tour",
        "current_view": None,
        "sidebar_collapsed": False,
    }

    app["login_time_var"].set("Đăng nhập lúc: " + app["login_time"].strftime("%d/%m/%Y - %H:%M:%S"))

    try:
        from core.app import sync_completed_tour_bookings
        sync_completed_tour_bookings(app["ql"])
    except Exception as e:
        print(f"Error syncing completed bookings at init: {e}")

    for widget in root.winfo_children():
        widget.destroy()

    root.title("VIETNAM TRAVEL - KHÁCH HÀNG")
    root.geometry("1320x780")
    root.minsize(1120, 700)
    root.configure(bg=THEME["bg"])
    configure_ui_fonts(root)

    # Styles Config...
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", font=("Times New Roman", 12), rowheight=38, background=THEME["surface"], fieldbackground=THEME["surface"], foreground=THEME["text"], bordercolor=THEME["border"], relief="flat")
    style.configure("Treeview.Heading", font=("Times New Roman", 12, "bold"), background=THEME["heading_bg"], foreground=THEME["text"], relief="flat", padding=(8, 10))
    style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", THEME["text"])])
    style.configure("TScrollbar", bordercolor="#1e293b", troughcolor="#1e293b", background="#475569", darkcolor="#475569", lightcolor="#475569", arrowcolor="#1e293b", arrowsize=10, relief="flat", gripcount=0)

    username = user_data.get("username", "Khach")
    display_name = user_data.get("fullname") or user_data.get("name", "Khách hàng")

    SIDEBAR_EXPANDED_WIDTH = 300
    SIDEBAR_COLLAPSED_WIDTH = 92
    SIDEBAR_BG = "#020f2a"
    SIDEBAR_CARD_BG = "#0f1e3d"
    SIDEBAR_BORDER = "#2a3e66"
    SIDEBAR_BTN_HOVER = "#102547"
    SIDEBAR_BTN_ACTIVE = "#2563eb"
    sidebar_outer = tk.Frame(root, bg=SIDEBAR_BG, width=SIDEBAR_EXPANDED_WIDTH)
    sidebar_outer.pack(side="left", fill="y")
    sidebar_outer.pack_propagate(False)

    brand = tk.Frame(sidebar_outer, bg=SIDEBAR_BG)
    brand.pack(fill="x", padx=18, pady=(18, 10))
    brand_top = tk.Frame(brand, bg=SIDEBAR_BG)
    brand_top.pack(fill="x")
    brand_title = tk.Label(brand_top, text="VIETNAM TRAVEL", justify="left", anchor="w", bg=SIDEBAR_BG, fg="#34d399", font=("Times New Roman", 21, "bold"))
    brand_title.pack(side="left", fill="x", expand=True)
    
    collapse_btn = RoundedButton(brand_top, text="\u2630", bg=SIDEBAR_BG, fg="#dbeafe", activebackground=SIDEBAR_BTN_ACTIVE, activeforeground="white", relief="flat", bd=0, cursor="hand2", font=("Times New Roman", 12, "bold"), padx=8, pady=3)
    collapse_btn.pack(side="right")
    collapse_btn.bind("<Enter>", lambda _e: collapse_btn.configure(bg=SIDEBAR_BG))
    collapse_btn.bind("<Leave>", lambda _e: collapse_btn.configure(bg=SIDEBAR_BG))
    
    brand_subtitle = tk.Label(brand, text="Customer Service Center", justify="left", anchor="w", bg=SIDEBAR_BG, fg="#93c5fd", font=("Times New Roman", 11, "italic"))
    brand_subtitle.pack(fill="x", pady=(2, 0))

    account_card = tk.Frame(sidebar_outer, bg=SIDEBAR_CARD_BG, highlightbackground=SIDEBAR_BORDER, highlightthickness=1)
    account_card.pack(fill="x", padx=16, pady=(0, 8))

    tk.Label(account_card, text="TÀI KHOẢN KHÁCH HÀNG", bg=SIDEBAR_CARD_BG, fg="#dbeafe", font=("Times New Roman", 11, "bold")).pack(fill="x", pady=(10, 0))
    tk.Label(account_card, text=f"{display_name}", bg=SIDEBAR_CARD_BG, fg="white", font=("Times New Roman", 13, "bold"), pady=6).pack(fill="x")
    tk.Label(account_card, text=f"Username: {username}", bg=SIDEBAR_CARD_BG, fg="#93c5fd", font=("Times New Roman", 10, "italic")).pack(fill="x")
    tk.Label(account_card, textvariable=app["login_time_var"], bg=SIDEBAR_CARD_BG, fg="#93c5fd", font=("Times New Roman", 10, "italic"), pady=8, wraplength=220, justify="center").pack(fill="x")
    tk.Label(account_card, text="Đang hoạt động", bg=SIDEBAR_CARD_BG, fg="#22c55e", font=("Times New Roman", 10, "bold")).pack(pady=(4, 10))

    util = tk.Frame(sidebar_outer, bg=SIDEBAR_BG)
    util.pack(side="bottom", fill="x", padx=12, pady=14)
    tk.Frame(util, bg="#22365b", height=1).pack(fill="x", pady=(0, 12))
    logout_btn = RoundedButton(util, text="  🚪  Đăng xuất", bg="#b91c1c", fg="white", activebackground="#dc2626", activeforeground="white", relief="flat", bd=0, cursor="hand2", anchor="w", font=("Times New Roman", 13, "bold"), padx=14, pady=12, command=lambda: logout_user(root))
    logout_btn.pack(fill="x")

    menu_scroll = ttk.Scrollbar(sidebar_outer, orient="vertical")
    menu_canvas = tk.Canvas(sidebar_outer, bg=SIDEBAR_BG, highlightthickness=0, bd=0, yscrollcommand=menu_scroll.set)
    menu_scroll.configure(command=menu_canvas.yview)
    bind_autohide_scrollbar(menu_canvas, menu_scroll, "vertical")
    menu_canvas.pack(side="left", fill="both", expand=True)

    menu_inner = tk.Frame(menu_canvas, bg=SIDEBAR_BG)
    menu_window = menu_canvas.create_window((0, 0), window=menu_inner, anchor="nw")

    def on_menu_configure(event):
        menu_canvas.configure(scrollregion=menu_canvas.bbox("all"))

    def on_menu_resize(event):
        menu_canvas.itemconfig(menu_window, width=event.width)

    menu_inner.bind("<Configure>", on_menu_configure)
    menu_canvas.bind("<Configure>", on_menu_resize)

    menu_inner.bind("<Enter>", lambda _e: menu_canvas.bind_all("<MouseWheel>", lambda ev: menu_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")))
    menu_inner.bind("<Leave>", lambda _e: menu_canvas.unbind_all("<MouseWheel>"))

    menu = tk.Frame(menu_inner, bg=SIDEBAR_BG)
    menu.pack(fill="x", padx=12, pady=(2, 0))

    right_panel = tk.Frame(root, bg=THEME["bg"])
    right_panel.pack(side="left", fill="both", expand=True)

    header = tk.Frame(right_panel, bg=THEME["header_bg"], height=96, highlightbackground=THEME["border"], highlightthickness=1)
    header.pack(side="top", fill="x", padx=18, pady=(18, 12))
    header.pack_propagate(False)

    head_left = tk.Frame(header, bg=THEME["header_bg"])
    head_left.pack(side="left", fill="both", expand=True, padx=18, pady=12)
    tk.Label(head_left, textvariable=app["page_title_var"], bg=THEME["header_bg"], fg=THEME["text"], font=("Times New Roman", 24, "bold"), anchor="w").pack(anchor="w")
    tk.Label(head_left, textvariable=app["page_subtitle_var"], bg=THEME["header_bg"], fg=THEME["muted"], font=("Times New Roman", 12, "italic"), anchor="w", wraplength=760, justify="left").pack(anchor="w", pady=(3, 0))

    head_right = tk.Frame(header, bg=THEME["header_bg"])
    head_right.pack(side="right", padx=18, pady=16)
    app["header_badge"] = tk.Label(head_right, text="KHÁCH HÀNG", bg="#dbeafe", fg="#1d4ed8", font=("Times New Roman", 11, "bold"), padx=14, pady=7)
    app["header_badge"].pack(anchor="e", pady=(0, 8))

    content_shell = tk.Frame(right_panel, bg=THEME["bg"])
    content_shell.pack(fill="both", expand=True, padx=18)

    content_canvas = tk.Canvas(content_shell, bg=THEME["bg"], highlightthickness=0, bd=0)
    outer_sy = ttk.Scrollbar(content_shell, orient="vertical", command=content_canvas.yview)
    bind_autohide_scrollbar(content_canvas, outer_sy, "vertical")
    content_canvas.pack(side="left", fill="both", expand=True)

    content_area = tk.Frame(content_canvas, bg=THEME["bg"], padx=4, pady=4)
    canvas_window = content_canvas.create_window((0, 0), window=content_area, anchor="nw")

    def on_content_configure(_event):
        content_canvas.configure(scrollregion=content_canvas.bbox("all"))

    def on_canvas_resize(event):
        content_canvas.itemconfigure(canvas_window, width=max(event.width - 2, 1))

    def on_outer_mousewheel(event):
        try:
            content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    content_area.bind("<Configure>", on_content_configure)
    content_canvas.bind("<Configure>", on_canvas_resize)
    content_canvas.bind("<Enter>", lambda _e: content_canvas.bind_all("<MouseWheel>", on_outer_mousewheel))
    content_canvas.bind("<Leave>", lambda _e: content_canvas.unbind_all("<MouseWheel>"))

    app["container"] = content_area
    app["content_canvas"] = content_canvas

    status_bar = tk.Frame(right_panel, bg=THEME["status_bg"], height=36, highlightbackground=THEME["border"], highlightthickness=1)
    status_bar.pack(side="bottom", fill="x", padx=18, pady=(0, 16))
    status_bar.pack_propagate(False)

    app["status_label"] = tk.Label(status_bar, textvariable=app["status_var"], bg=THEME["status_bg"], fg=THEME["primary"], anchor="w", padx=14, font=("Times New Roman", 11, "italic"))
    app["status_label"].pack(fill="both", expand=True)

    def set_status(text, color=THEME["primary"]):
        app["status_var"].set(text)
        if app.get("status_label"):
            app["status_label"].config(fg=color)

    def set_badge(text, bg="#dbeafe", fg="#1d4ed8"):
        if app.get("header_badge"):
            app["header_badge"].config(text=text, bg=bg, fg=fg)

    def set_active_menu(button):
        prev = app.get("active_menu_btn")
        if prev and prev.winfo_exists() and prev is not button:
            prev.configure(bg=SIDEBAR_BG, fg="#dbe4f5")
        app["active_menu_btn"] = button
        button.configure(bg=SIDEBAR_BTN_ACTIVE, fg="white")

    def menu_btn(text, cmd, icon=""):
        label = f"  {icon}  {text}" if icon else f"  {text}"
        btn = RoundedButton(
            menu, text=label, bg=SIDEBAR_BG, fg="#dbe4f5", activebackground=SIDEBAR_BTN_ACTIVE,
            activeforeground="white", relief="flat", bd=0, cursor="hand2", anchor="w",
            justify="left", wraplength=210, font=("Times New Roman", 13, "bold"),
            padx=14, pady=13, command=cmd,
        )
        btn._full_text = text
        btn._icon = icon

        def _sync_wrap(_event=None, button=btn):
            if app.get("sidebar_collapsed"):
                button.configure(wraplength=40)
                return
            button.configure(wraplength=max(150, button.winfo_width() - 36))

        btn.bind("<Configure>", _sync_wrap)
        btn.after_idle(_sync_wrap)
        btn.bind("<Enter>", lambda _e, b=btn: b.configure(bg=SIDEBAR_BTN_HOVER) if app.get("active_menu_btn") is not b else None)
        btn.bind("<Leave>", lambda _e, b=btn: b.configure(bg=SIDEBAR_BG) if app.get("active_menu_btn") is not b else None)
        return btn

    def clear_container():
        for widget in content_area.winfo_children():
            widget.destroy()
        if app.get("content_canvas"):
            app["content_canvas"].yview_moveto(0)

    def get_current_user():
        return app["ql"].find_user(user_data.get("username", ""))

    def my_bookings():
        username_local = user_data.get("username", "")
        return [b for b in app["ql"].list_bookings if b.get("usernameDat") == username_local]

    def responsive_wraplength(base_offset=360, minimum=320):
        current_width = max(content_area.winfo_width(), right_panel.winfo_width(), root.winfo_width())
        return max(minimum, current_width - base_offset)

    def format_currency(value):
        return f"{safe_int(value):,}đ".replace(",", ".")

    def build_voucher_quote(voucher_code, gross_total, ma_tour=""):
        return service_build_voucher_quote(
            app["ql"], voucher_code, gross_total,
            username=user_data.get("username", ""), ma_tour=ma_tour,
        )

    def build_stat_card(parent, title, value, note, accent):
        card = tk.Frame(parent, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=7)
        tk.Frame(card, bg=accent, height=4).pack(fill="x")
        body = tk.Frame(card, bg=THEME["surface"], padx=16, pady=14)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=title, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "bold")).pack(anchor="w")
        tk.Label(body, text=value, bg=THEME["surface"], fg=accent, font=("Times New Roman", 22, "bold")).pack(anchor="w", pady=(6, 4))
        tk.Label(body, text=note, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 10, "italic"), wraplength=220, justify="left").pack(anchor="w")
        return card

    def make_section(parent, title, subtitle="", accent=None):
        section = tk.Frame(parent, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        section.pack(fill="x", pady=(0, 14))
        if accent:
            tk.Frame(section, bg=accent, height=4).pack(fill="x")
        head = tk.Frame(section, bg=THEME["surface"])
        head.pack(fill="x", padx=18, pady=(14, 8))
        tk.Label(head, text=title, bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 18, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(head, text=subtitle, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "italic"), wraplength=920, justify="left").pack(anchor="w", pady=(2, 0))
        body = tk.Frame(section, bg=THEME["surface"])
        body.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        return section, body

    def tab_danh_sach_tour():
        clear_container()
        app["current_tab"] = "tour"

        stats_wrap = tk.Frame(content_area, bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))

        visible_tours = [t for t in app["ql"].list_tours if is_tour_visible_to_user(t, app["ql"])]
        visible_tours.sort(key=lambda t: parse_ddmmyyyy(t.get("ngay", "")) or datetime.max.date())
        all_open_tours = [t for t in visible_tours if normalize_tour_status(t.get("trangThai", "")) in TOUR_BOOKABLE_STATUSES]
        total_open = len(all_open_tours)
        total_visible = len(visible_tours)
        
        my_total_bookings = len(my_bookings())

        build_stat_card(stats_wrap, "Tour hiển thị", str(total_visible), "Các tour sắp diễn ra mà bạn có thể theo dõi trên hệ thống.", THEME["primary"])
        build_stat_card(stats_wrap, "Tour mở bán", str(total_open), "Các tour còn có thể đăng ký ngay lúc này.", THEME["success"])
        build_stat_card(stats_wrap, "Booking của bạn", str(my_total_bookings), "Số booking bạn đang theo dõi trong hệ thống.", THEME["warning"])

        _, body = make_section(
            content_area, "Khám phá các tour du lịch",
            "Xem lịch khởi hành, số chỗ còn trống và đăng ký tour trực tiếp ở ngay bên dưới.",
            accent="#2563eb",
        )

        wrapper = tk.Frame(body, bg=THEME["surface"], bd=1, relief="solid")
        wrapper.pack(fill="x")

        cols = ("ma", "ten", "ngay", "gia", "khach", "tt")
        tv_height = 5 if root.winfo_height() < 820 else 6
        tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=tv_height)
        app["tv_tours"] = tv

        tv.heading("ma", text="Mã")
        tv.heading("ten", text="Tên Tour Du Lịch")
        tv.heading("ngay", text="Khởi hành")
        tv.heading("gia", text="Giá vé")
        tv.heading("khach", text="Chỗ trống")
        tv.heading("tt", text="Trạng thái")

        tv.column("ma", width=60, anchor="center")
        tv.column("ten", width=300, anchor="w")
        tv.column("ngay", width=120, anchor="center")
        tv.column("gia", width=120, anchor="center")
        tv.column("khach", width=100, anchor="center")
        tv.column("tt", width=120, anchor="center")

        for t in visible_tours:
            occupied = app["ql"].get_occupied_seats(t["ma"])
            available = max(safe_int(t["khach"]) - occupied, 0)
            tv.insert("", "end", values=(
                t["ma"], t["ten"], t["ngay"], format_currency(t['gia']), f"{available} chỗ", t["trangThai"]
            ))

        apply_zebra(tv)
        sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
        sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
        bind_autohide_scrollbar(tv, sy, "vertical")
        bind_autohide_scrollbar(tv, sx, "horizontal")
        tv.pack(side="left", fill="both", expand=True)

        if not visible_tours:
            tv.insert("", "end", values=("", "Hiện chưa có tour phù hợp để hiển thị", "", "", "", ""))

        detail_section, detail_body_container = make_section(
            content_area, "Chi tiết tour và đăng ký",
            "Chọn tour ở bảng phía trên để xem chi tiết và thực hiện đăng ký ngay.",
            accent="#d97706",
        )

        detail_fr = tk.Frame(detail_body_container, bg=THEME["surface"])
        detail_fr.pack(fill="x")
        detail_fr.grid_rowconfigure(0, weight=1)
        detail_fr.grid_columnconfigure(0, weight=1)
        detail_fr.grid_columnconfigure(1, minsize=320)

        detail_body = tk.Frame(detail_fr, bg=THEME["surface"], bd=1, relief="solid")
        detail_body.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        detail_body.grid_rowconfigure(0, weight=1)
        detail_body.grid_columnconfigure(0, weight=1)

        detail_scroll = ttk.Scrollbar(detail_body, orient="vertical")
        detail_text = tk.Text(
            detail_body, wrap="word", font=("Times New Roman", 13), bg=THEME["surface"],
            fg=THEME["text"], relief="flat", bd=0, padx=10, pady=8,
            yscrollcommand=detail_scroll.set, height=6
        )
        detail_scroll.config(command=detail_text.yview)
        detail_text.grid(row=0, column=0, sticky="nsew")
        detail_scroll.grid(row=0, column=1, sticky="ns")

        def set_detail_content(content):
            app["detail_var"].set(content)
            detail_text.config(state="normal")
            detail_text.delete("1.0", "end")
            detail_text.insert("1.0", content)
            detail_text.config(state="disabled")

        set_detail_content(app["detail_var"].get())

        action_fr = tk.Frame(detail_fr, bg=THEME["surface"], bd=1, relief="solid", padx=12, pady=12)
        action_fr.grid(row=0, column=1, sticky="nsew")
        action_fr.grid_columnconfigure(0, weight=0, minsize=132)
        action_fr.grid_columnconfigure(1, weight=1)

        tk.Label(action_fr, text="ĐĂNG KÝ TOUR", font=("Times New Roman", 13, "bold"), bg=THEME["surface"], fg=THEME["success"], anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        tk.Label(action_fr, text="Số người đi:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=1, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        spn_people = tk.Spinbox(action_fr, from_=1, to=50, font=("Times New Roman", 12), relief="solid", bd=1, justify="center")
        spn_people.grid(row=1, column=1, sticky="ew", ipady=4, pady=(0, 10))

        tk.Label(action_fr, text="Cơ cấu độ tuổi:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=2, column=0, sticky="nw", pady=(0, 10), padx=(0, 10))
        age_group_fr = tk.Frame(action_fr, bg=THEME["surface"])
        age_group_fr.grid(row=2, column=1, sticky="ew", pady=(0, 10))
        age_group_fr.grid_columnconfigure(1, weight=1)

        tk.Label(age_group_fr, text="Trẻ em (<12):", font=("Times New Roman", 11), bg=THEME["surface"]).grid(row=0, column=0, sticky="w")
        spn_child = tk.Spinbox(age_group_fr, from_=0, to=50, font=("Times New Roman", 11), relief="solid", bd=1, justify="center", width=8)
        spn_child.grid(row=0, column=1, sticky="e", pady=(0, 4))

        tk.Label(age_group_fr, text="Trung niên:", font=("Times New Roman", 11), bg=THEME["surface"]).grid(row=1, column=0, sticky="w")
        spn_middle = tk.Spinbox(age_group_fr, from_=0, to=50, font=("Times New Roman", 11), relief="solid", bd=1, justify="center", width=8)
        spn_middle.grid(row=1, column=1, sticky="e", pady=(0, 4))

        tk.Label(age_group_fr, text="Người cao tuổi (>65):", font=("Times New Roman", 11), bg=THEME["surface"]).grid(row=2, column=0, sticky="w")
        spn_senior = tk.Spinbox(age_group_fr, from_=0, to=50, font=("Times New Roman", 11), relief="solid", bd=1, justify="center", width=8)
        spn_senior.grid(row=2, column=1, sticky="e")

        tk.Label(action_fr, text="Thanh toán ngay (đ):", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=3, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        pay_now_frame = tk.Frame(action_fr, bg=THEME["surface"])
        pay_now_frame.grid(row=3, column=1, sticky="ew", pady=(0, 10))
        ent_pay_now = tk.Entry(pay_now_frame, font=("Times New Roman", 12), relief="solid", bd=1, justify="right")
        ent_pay_now.insert(0, "0")
        ent_pay_now.pack(side="top", fill="x", ipady=4)
        
        quick_pay_frame = tk.Frame(pay_now_frame, bg=THEME["surface"])
        quick_pay_frame.pack(side="top", fill="x", pady=(4, 0))
        
        def set_pay_amount(percent):
            booking_context = refresh_booking_quote()
            if booking_context:
                total = booking_context["final_total"]
                amount = int(total * percent)
                ent_pay_now.delete(0, "end")
                ent_pay_now.insert(0, str(amount))
                update_transfer_qr()
                
        btn_deposit = tk.Button(quick_pay_frame, text="Cọc 30%", font=("Times New Roman", 9), relief="solid", bd=1, cursor="hand2", bg=THEME["surface"], command=lambda: set_pay_amount(0.3))
        btn_deposit.pack(side="left", padx=(0, 4))
        btn_full = tk.Button(quick_pay_frame, text="Đủ 100%", font=("Times New Roman", 9), relief="solid", bd=1, cursor="hand2", bg=THEME["surface"], command=lambda: set_pay_amount(1.0))
        btn_full.pack(side="left")

        tk.Label(action_fr, text="Hình thức thanh toán:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=4, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        pay_method_var = tk.StringVar(value=PAYMENT_METHODS[0])
        cmb_pay_method = ttk.Combobox(action_fr, textvariable=pay_method_var, values=PAYMENT_METHODS, state="readonly", font=("Times New Roman", 11))
        cmb_pay_method.grid(row=4, column=1, sticky="ew", pady=(0, 10))

        tk.Label(action_fr, text="Mã giảm giá:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=5, column=0, sticky="w", pady=(0, 8), padx=(0, 10))
        voucher_var = tk.StringVar()
        ent_voucher = tk.Entry(action_fr, textvariable=voucher_var, font=("Times New Roman", 12), relief="solid", bd=1)
        ent_voucher.grid(row=5, column=1, sticky="ew", ipady=4, pady=(0, 8))

        voucher_feedback_var = tk.StringVar(value="Để trống nếu bạn chưa có mã giảm giá. Có thể thử: TRAVEL17 hoặc TRAVEL19.")
        voucher_feedback_lbl = tk.Label(action_fr, textvariable=voucher_feedback_var, font=("Times New Roman", 10, "italic"), bg=THEME["surface"], fg=THEME["muted"], justify="left", wraplength=260)
        voucher_feedback_lbl.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        booking_summary_var = tk.StringVar(value="Tổng tạm tính: 0đ | Giảm: 0đ | Cần thanh toán: 0đ")
        booking_summary_lbl = tk.Label(action_fr, textvariable=booking_summary_var, font=("Times New Roman", 10, "bold"), bg=THEME["surface"], fg=THEME["success"], justify="left", wraplength=260)
        booking_summary_lbl.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        info_note = tk.Label(action_fr, text="Chọn tour ở bảng phía trên, nhập cơ cấu độ tuổi. Trẻ em (<12) giảm 20%, người cao tuổi (>65) giảm 35%.", font=("Times New Roman", 10, "italic"), bg=THEME["surface"], fg=THEME["muted"], justify="left", wraplength=260)
        info_note.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(2, 10))

        cash_policy_var = tk.StringVar(value="")
        cash_policy_lbl = tk.Label(action_fr, textvariable=cash_policy_var, font=("Times New Roman", 10, "bold"), bg=THEME["surface"], fg=THEME["warning"], justify="left", wraplength=260)
        cash_policy_lbl.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        qr_box = tk.Frame(action_fr, bg=THEME["note_bg"], bd=1, relief="solid", padx=8, pady=8)
        qr_box.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        tk.Label(qr_box, text="QR Chuyển khoản", font=("Times New Roman", 12, "bold"), bg=THEME["note_bg"], fg=THEME["note_fg"]).pack(anchor="w")

        qr_image_lbl = tk.Label(qr_box, text="", bg=THEME["note_bg"], fg=THEME["muted"], justify="center", wraplength=240)
        qr_image_lbl.pack(anchor="center", pady=(6, 6))

        qr_status_var = tk.StringVar(value="")
        qr_status_lbl = tk.Label(qr_box, textvariable=qr_status_var, font=("Times New Roman", 10), bg=THEME["note_bg"], fg=THEME["note_fg"], justify="left", wraplength=260)
        qr_status_lbl.pack(anchor="w")

        # Bank details panel
        bank_details_fr = tk.Frame(qr_box, bg=THEME["note_bg"])
        bank_details_fr.pack(fill="x", pady=(5, 5))

        stk_row = tk.Frame(bank_details_fr, bg=THEME["note_bg"])
        stk_row.pack(fill="x", pady=2)
        tk.Label(stk_row, text="Số tài khoản: 41389377 (ACB)", font=("Times New Roman", 10, "bold"), bg=THEME["note_bg"], fg=THEME["text"]).pack(side="left")
        btn_copy_stk = tk.Button(stk_row, text="Sao chép", font=("Times New Roman", 8), bg=THEME["surface"], bd=1, relief="solid", cursor="hand2", command=lambda: copy_to_clipboard(root, "41389377", btn_copy_stk, "Sao chép"))
        btn_copy_stk.pack(side="right", padx=(5, 0))

        nd_row = tk.Frame(bank_details_fr, bg=THEME["note_bg"])
        nd_row.pack(fill="x", pady=2)
        tk.Label(nd_row, text="Nội dung CK: ", font=("Times New Roman", 10, "bold"), bg=THEME["note_bg"], fg=THEME["text"]).pack(side="left")
        
        qr_transfer_content_var = tk.StringVar(value="-")
        lbl_transfer_content = tk.Label(nd_row, textvariable=qr_transfer_content_var, font=("Times New Roman", 10, "bold"), bg=THEME["note_bg"], fg=THEME["primary"])
        lbl_transfer_content.pack(side="left")

        btn_copy_nd = tk.Button(nd_row, text="Sao chép", font=("Times New Roman", 8), bg=THEME["surface"], bd=1, relief="solid", cursor="hand2", command=lambda: copy_to_clipboard(root, qr_transfer_content_var.get(), btn_copy_nd, "Sao chép"))
        btn_copy_nd.pack(side="right", padx=(5, 0))

        qr_note_var = tk.StringVar(value="")
        qr_note_lbl = tk.Label(qr_box, textvariable=qr_note_var, font=("Times New Roman", 9, "italic"), bg=THEME["note_bg"], fg=THEME["muted"], justify="left", wraplength=260)
        qr_note_lbl.pack(anchor="w", pady=(3, 0))

        qr_box.grid_remove()
        qr_request_id = {"value": 0}

        action_btn_row = tk.Frame(action_fr, bg=THEME["surface"])
        action_btn_row.grid(row=11, column=0, columnspan=2, sticky="ew")

        def get_selected_tour_and_amount():
            sel = tv.selection()
            if not sel:
                return None, 0, max(1, safe_int(spn_people.get()))
            ma = tv.item(sel[0])["values"][0]
            tour = app["ql"].find_tour(ma)
            num_people = max(1, safe_int(spn_people.get()))
            pay_now = max(0, safe_int(ent_pay_now.get()))
            return tour, pay_now, num_people

        def get_age_breakdown():
            return {
                "treEm": max(0, safe_int(spn_child.get())),
                "trungNien": max(0, safe_int(spn_middle.get())),
                "nguoiCaoTuoi": max(0, safe_int(spn_senior.get())),
            }

        def normalize_age_breakdown(num_people):
            breakdown = normalize_passenger_breakdown(get_age_breakdown(), num_people)
            if breakdown is None:
                return None
            spn_middle.delete(0, "end")
            spn_middle.insert(0, str(breakdown["trungNien"]))
            return breakdown

        def refresh_booking_quote(show_error=False):
            tour, pay_now, num_people = get_selected_tour_and_amount()
            if not tour:
                voucher_feedback_var.set("Chọn tour để kiểm tra mã giảm giá.")
                voucher_feedback_lbl.config(fg=THEME["muted"])
                booking_summary_var.set("Tổng tạm tính: 0đ | Giảm: 0đ | Cần thanh toán: 0đ")
                booking_summary_lbl.config(fg=THEME["success"])
                return None

            breakdown = normalize_age_breakdown(num_people)
            if breakdown is None:
                booking_summary_var.set("Cơ cấu độ tuổi vượt quá số người đi. Vui lòng kiểm tra lại.")
                booking_summary_lbl.config(fg=THEME["danger"])
                return None

            price_per_person = max(0, safe_int(tour.get("gia", 0)))
            gross_total = max(0, price_per_person * num_people)
            age_discount = calculate_age_discount(price_per_person, breakdown)
            age_discount = max(0, min(gross_total, safe_int(age_discount)))
            subtotal_after_age = max(gross_total - age_discount, 0)
            normalized_code = str(voucher_var.get() or "").strip().upper()
            if normalized_code != voucher_var.get():
                voucher_var.set(normalized_code)
            quote = build_voucher_quote(normalized_code, subtotal_after_age, tour.get("ma", ""))
            final_total = max(subtotal_after_age - quote["discount"], 0)
            total_discount = age_discount + quote["discount"]

            booking_summary_var.set(
                f"Tổng tạm tính: {format_currency(gross_total)} | "
                f"Giảm đối tượng: {format_currency(age_discount)} | "
                f"Voucher: {format_currency(quote['discount'])} | "
                f"Tổng giảm: {format_currency(total_discount)} | "
                f"Cần thanh toán: {format_currency(final_total)}"
            )
            booking_summary_lbl.config(fg=THEME["success"])

            if quote["ok"]:
                voucher_feedback_lbl.config(fg=THEME["success"] if quote["code"] else THEME["muted"])
            else:
                voucher_feedback_lbl.config(fg=THEME["danger"])
                if show_error and quote["code"]:
                    messagebox.showwarning("Mã giảm giá", quote["message"])

            voucher_feedback_var.set(quote["message"])

            return {
                "tour": tour, "pay_now": pay_now, "num_people": num_people,
                "breakdown": breakdown, "gross_total": gross_total,
                "age_discount": age_discount, "quote": quote, "final_total": final_total,
            }

        def update_transfer_qr():
            booking_context = refresh_booking_quote()
            if pay_method_var.get().strip() != "Chuyển khoản":
                qr_request_id["value"] += 1
                qr_box.grid_remove()
                qr_image_lbl.config(image="", text="")
                qr_image_lbl.image = None
                qr_status_var.set("")
                qr_note_var.set("")
                tour = booking_context["tour"] if booking_context else None
                cash_policy_var.set(build_cash_policy_notice(tour.get("ngay", "")) if tour else build_cash_policy_notice(""))
                return

            cash_policy_var.set("")
            qr_box.grid()
            if not booking_context:
                qr_image_lbl.config(image="", text="Chọn tour để tạo QR")
                qr_image_lbl.image = None
                qr_status_var.set("Vui lòng chọn tour ở bảng phía trên.")
                qr_note_var.set("")
                return

            tour = booking_context["tour"]
            pay_now = booking_context["pay_now"]

            if pay_now <= 0:
                pay_now = booking_context["final_total"]

            if pay_now <= 0:
                qr_image_lbl.config(image="", text="Không đủ dữ liệu để tạo QR")
                qr_image_lbl.image = None
                qr_status_var.set("Số tiền thanh toán phải lớn hơn 0.")
                qr_note_var.set("")
                return

            transfer_content = f"{tour.get('ma', '')}-{user_data.get('username', 'KH')}-{pay_now}"
            qr_transfer_content_var.set(transfer_content)
            qr_request_id["value"] += 1
            current_request_id = qr_request_id["value"]
            qr_image_lbl.config(image="", text="Đang tải QR...")
            qr_image_lbl.image = None
            qr_status_var.set("Đang tải mã chuyển khoản, vui lòng chờ...")
            qr_note_var.set("")

            def worker():
                try:
                    qr_url = build_transfer_qr_url(pay_now, transfer_content)
                    qr_photo = fetch_transfer_qr_photo(qr_url, max_size_px=190)
                except (OSError, URLError, ValueError, tk.TclError) as exc:
                    error_message = short_ui_error(exc)

                    def apply_error():
                        if current_request_id != qr_request_id["value"] or pay_method_var.get().strip() != "Chuyển khoản":
                            return
                        qr_image_lbl.config(image="", text="(Không tải được QR)")
                        qr_image_lbl.image = None
                        qr_status_var.set("Không thể gọi API QR. Vui lòng thử lại sau.")
                        qr_note_var.set(error_message)

                    root.after(0, apply_error)
                    return

                def apply_success():
                    if current_request_id != qr_request_id["value"] or pay_method_var.get().strip() != "Chuyển khoản":
                        return
                    qr_image_lbl.config(image=qr_photo, text="")
                    qr_image_lbl.image = qr_photo
                    qr_status_var.set(f"Quét mã để chuyển khoản {pay_now:,}đ".replace(",", "."))
                    qr_note_var.set("Nội dung CK được tạo tự động theo mã tour và tài khoản khách.")

                root.after(0, apply_success)

            threading.Thread(target=worker, daemon=True).start()

        cmb_pay_method.bind("<<ComboboxSelected>>", lambda _e: update_transfer_qr())
        ent_pay_now.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        ent_voucher.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        ent_voucher.bind("<FocusOut>", lambda _e: update_transfer_qr())
        spn_people.config(command=update_transfer_qr)
        spn_people.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        spn_child.config(command=update_transfer_qr)
        spn_middle.config(command=update_transfer_qr)
        spn_senior.config(command=update_transfer_qr)
        spn_child.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        spn_middle.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        spn_senior.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        update_transfer_qr()

        def sync_detail_layout(event=None):
            width = detail_fr.winfo_width()
            height = root.winfo_height()
            compact_mode = width < 1120 or height < 820
            tv.configure(height=5 if height < 820 else 6)

            if compact_mode:
                detail_body.grid_configure(row=0, column=0, padx=0, pady=(0, 10), sticky="nsew")
                action_fr.grid_configure(row=1, column=0, padx=0, pady=0, sticky="ew")
                detail_fr.grid_columnconfigure(0, weight=1, minsize=0)
                detail_fr.grid_columnconfigure(1, weight=0, minsize=0)
                detail_fr.grid_rowconfigure(0, weight=1)
                detail_fr.grid_rowconfigure(1, weight=0)
                detail_text.config(height=5)
                wrap_size = max(210, min(action_fr.winfo_width() - 32, width - 64))
            else:
                detail_body.grid_configure(row=0, column=0, padx=(0, 12), pady=0, sticky="nsew")
                action_fr.grid_configure(row=0, column=1, padx=0, pady=0, sticky="nsew")
                detail_fr.grid_columnconfigure(0, weight=1, minsize=0)
                detail_fr.grid_columnconfigure(1, weight=0, minsize=320)
                detail_fr.grid_rowconfigure(0, weight=1)
                detail_fr.grid_rowconfigure(1, weight=0)
                detail_text.config(height=6)
                wrap_size = max(240, min(action_fr.winfo_width() - 32, 340))

            info_note.config(wraplength=wrap_size)
            voucher_feedback_lbl.config(wraplength=wrap_size)
            booking_summary_lbl.config(wraplength=wrap_size)
            cash_policy_lbl.config(wraplength=wrap_size)
            qr_image_lbl.config(wraplength=wrap_size)
            qr_status_lbl.config(wraplength=wrap_size)
            qr_note_lbl.config(wraplength=wrap_size)

        detail_fr.bind("<Configure>", sync_detail_layout)
        sync_detail_layout()

        def on_select(event):
            sel = tv.selection()
            if not sel:
                return

            ma = tv.item(sel[0])["values"][0]
            t = app["ql"].find_tour(ma)
            if not t:
                return

            hdv = app["ql"].find_hdv(t.get("hdvPhuTrach"))
            occupied = app["ql"].get_occupied_seats(ma)
            available = max(safe_int(t["khach"]) - occupied, 0)
            spn_people.config(to=max(1, available))
            spn_child.config(to=max(0, available))
            spn_middle.config(to=max(0, available))
            spn_senior.config(to=max(0, available))
            spn_child.delete(0, "end"); spn_child.insert(0, "0")
            spn_senior.delete(0, "end"); spn_senior.insert(0, "0")
            spn_middle.delete(0, "end"); spn_middle.insert(0, str(max(1, safe_int(spn_people.get()))))

            tour_status = normalize_tour_status(t.get("trangThai", ""))
            can_book = is_booking_allowed(
                tour_status,
                parse_ddmmyyyy(t.get("ngay", "")),
                occupied=occupied,
                capacity=max(1, safe_int(t.get("khach", 1))),
            )
            if tour_status == TOUR_STATUS_NOT_OPEN:
                action_label = "CHƯA MỞ BÁN"
            elif tour_status == TOUR_STATUS_FULL:
                action_label = "ĐÃ ĐỦ KHÁCH"
            elif can_book:
                action_label = "ĐĂNG KÝ NGAY"
            else:
                action_label = "KHÔNG THỂ ĐẶT"
            action_book_btn.configure(text=action_label, state=("normal" if can_book else "disabled"))

            info = [
                f"TOUR: {t['ten']} ({t['ma']})",
                f"Lộ trình: {t.get('diemDi', '')} → {t.get('diemDen', '')}",
                f"Khởi hành: {t['ngay']} | Kết thúc: {t.get('ngayKetThuc', '')} | Số ngày: {t.get('soNgay', '')}",
                f"Giá: {format_currency(t['gia'])}",
                f"Hướng dẫn viên: {hdv['tenHDV'] if hdv else 'Chưa phân công'} - SĐT: {hdv['sdt'] if hdv else 'N/A'}",
                f"Trạng thái: {t['trangThai']} | Còn trống: {available} chỗ",
                f"Ghi chú điều hành: {t.get('ghiChuDieuHanh', '') or 'Không có'}"
            ]
            lich_trinh = t.get("lichTrinh", [])
            if isinstance(lich_trinh, list) and lich_trinh:
                info.append("")
                info.append("Lịch trình:")
                for item in lich_trinh:
                    if not isinstance(item, dict):
                        continue
                    ngay = str(item.get("ngay", "")).strip()
                    tieu_de = str(item.get("tieuDe", "")).strip()
                    dia_diem = item.get("diaDiem", [])
                    if isinstance(dia_diem, str):
                        dia_diem = [p.strip() for p in dia_diem.split(",") if p.strip()]
                    info.append(f"- {ngay} {tieu_de}".strip())
                    if dia_diem:
                        info.append(f"  Điểm đến: {', '.join(dia_diem)}")
                    mo_ta = str(item.get("moTa", "")).strip()
                    if mo_ta:
                        info.append(f"  {mo_ta}")
            set_detail_content("\n".join(info))
            update_transfer_qr()

        tv.bind("<<TreeviewSelect>>", on_select)
        
        def on_tour_double_click(event):
            sel = tv.selection()
            if not sel:
                return
            ma = tv.item(sel[0])["values"][0]
            tour = app["ql"].find_tour(ma)
            if tour:
                open_tour_weather_popup(app["root"], tour, app["ql"])
        
        tv.bind("<Double-1>", on_tour_double_click)

        def dang_ky_tour():
            sel = tv.selection()
            if not sel:
                return messagebox.showwarning("Chú ý", "Vui lòng chọn một tour để đăng ký!")

            ma = tv.item(sel[0])["values"][0]
            t = app["ql"].find_tour(ma)
            if not t:
                return messagebox.showerror("Lỗi", "Không tìm thấy thông tin tour!")

            status = str(t.get("trangThai", "")).strip()
            if status != TOUR_STATUS_OPEN:
                return messagebox.showwarning("Lỗi", "Tour này hiện chưa mở bán hoặc không còn nhận đăng ký.")

            depart_date = parse_ddmmyyyy(t.get("ngay", ""))
            if not depart_date:
                return messagebox.showerror("Lỗi", "Tour lỗi ngày tháng.")
            if depart_date <= datetime.now().date():
                return messagebox.showwarning("Lỗi", "Tour đã khởi hành hoặc đã kết thúc, không thể đăng ký.")

            try:
                num_people = safe_int(spn_people.get())
            except Exception:
                num_people = 0
            if num_people <= 0:
                return messagebox.showwarning("Lỗi", "Số người đăng ký không hợp lệ.")

            occupied = app["ql"].get_occupied_seats(ma)
            total = safe_int(t.get("khach", 0))
            open_slots = safe_int(t.get("soLuotMoBan", total))
            capacity = open_slots if open_slots > 0 else total
            available = max(capacity - occupied, 0)
            if num_people > available:
                return messagebox.showwarning("Lỗi", "Số người đăng ký vượt quá số chỗ còn lại.")

            age_breakdown = normalize_age_breakdown(num_people)
            if age_breakdown is None:
                return messagebox.showwarning("Lỗi", "Danh sách hành khách không khớp số người đăng ký.")

            user_info = get_current_user()
            fullname = user_info.get("fullname", user_data.get("fullname", user_data.get("name", "Khách hàng"))) if user_info else user_data.get("fullname", "Khách hàng")
            sdt_khach = user_info.get("sdt", "Chưa cập nhật") if user_info else user_data.get("sdt", "Chưa cập nhật")

            pay_now = max(0, safe_int(ent_pay_now.get()))
            payment_method = pay_method_var.get().strip() or PAYMENT_METHODS[0]
            if payment_method == "Tiền mặt":
                messagebox.showinfo("Lưu ý thanh toán tiền mặt", build_cash_policy_notice(t.get("ngay", "")))

            result = service_create_booking(
                app["ql"], ma_tour=ma, num_people=num_people, pay_now=pay_now,
                payment_method=payment_method, username=user_data.get("username", ""),
                fullname=fullname, phone=sdt_khach, voucher_code=voucher_var.get(),
                passenger_breakdown=age_breakdown, actor=user_data.get("username", ""), role="user",
            )
            if not result.success:
                return messagebox.showwarning("Không thể đăng ký", result.message)

            created_booking = result.booking or {}
            discount_line = ""
            age_discount_line = ""
            if safe_int(created_booking.get("giamGiaDoiTuong", 0)) > 0:
                age_discount_line = f"\nGiảm theo độ tuổi: {format_currency(created_booking.get('giamGiaDoiTuong', 0))}"
            if created_booking.get("maVoucher"):
                discount_line = f"\nMã giảm giá: {created_booking.get('maVoucher')}\nĐã giảm: {format_currency(created_booking.get('giamGiaVoucher', 0))}"

            messagebox.showinfo(
                "Thành công",
                f"Bạn đã đăng ký tour {t['ten']} cho {num_people} người thành công!\n"
                f"Mã đặt chỗ: {created_booking.get('maBooking', '')}\n"
                f"Hình thức thanh toán: {payment_method}\n"
                f"Cơ cấu độ tuổi: Trẻ em {age_breakdown.get('treEm', 0)} | Trung niên {age_breakdown.get('trungNien', 0)} | Cao tuổi {age_breakdown.get('nguoiCaoTuoi', 0)}"
                f"{age_discount_line}\n"
                f"Tổng thanh toán: {format_currency(created_booking.get('tongTien', 0))}"
                f"{discount_line}\n"
                f"Đã thanh toán: {format_currency(created_booking.get('daThanhToan', 0))}"
            )
            tab_danh_sach_tour()

        action_book_btn = style_button(action_btn_row, "ĐĂNG KÝ NGAY", THEME["success"], dang_ky_tour)
        action_book_btn.pack(fill="x", pady=(2, 0))
        action_book_btn.configure(state="disabled")
        set_status("Đang ở mục: Khám phá Tour", THEME["primary"])

    def tab_tour_da_dat():
        clear_container()
        app["current_tab"] = "booked"

        bookings = [b for b in my_bookings() if b.get("trangThai") != "Đã hoàn thành" and b.get("bookingState") != "completed"]
        stats_wrap = tk.Frame(content_area, bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))

        paid_total = sum(safe_int(b.get("daThanhToan", 0)) for b in bookings)
        debt_total = sum(safe_int(b.get("conNo", 0)) for b in bookings)
        active_total = len([b for b in bookings if b.get("trangThai") not in BOOKING_CANCEL_STATUSES])

        build_stat_card(stats_wrap, "Tổng booking", str(len(bookings)), "Số booking bạn đã tạo trong hệ thống.", THEME["primary"])
        build_stat_card(stats_wrap, "Booking còn hiệu lực", str(active_total), "Các booking chưa hủy hoặc chưa hoàn tiền.", THEME["success"])
        build_stat_card(stats_wrap, "Đã thanh toán", format_currency(paid_total), "Tổng số tiền bạn đã thanh toán.", THEME["warning"])
        build_stat_card(stats_wrap, "Còn nợ", format_currency(debt_total), "Số tiền còn lại của các booking.", "#7c3aed")

        _, body = make_section(
            content_area, "Lịch sử đặt tour của bạn",
            "Theo dõi trạng thái thanh toán, cập nhật công nợ và tự hủy booking khi còn được phép.",
            accent="#7c3aed",
        )

        if not bookings:
            tk.Label(body, text="Bạn chưa tham gia tour nào.", font=("Times New Roman", 13), bg=THEME["surface"], fg=THEME["muted"]).pack(pady=40)
            return

        list_area = tk.Frame(body, bg=THEME["surface"])
        list_area.pack(fill="both", expand=True)

        for b in bookings:
            t = app["ql"].find_tour(b["maTour"])
            if not t: continue

            card = tk.Frame(list_area, bg=THEME["surface"], bd=1, relief="solid", padx=15, pady=12)
            card.pack(fill="x", pady=6)

            left = tk.Frame(card, bg=THEME["surface"])
            left.pack(side="left", fill="both", expand=True)

            tk.Label(left, text=f"{t['ten']}", font=("Times New Roman", 14, "bold"), bg=THEME["surface"], fg=THEME["primary"]).pack(anchor="w")

            voucher_text = f" | Voucher: {b.get('maVoucher')} (-{format_currency(b.get('giamGiaVoucher', 0))})" if str(b.get("maVoucher", "")).strip() else ""
            age_discount_text = ""
            if safe_int(b.get("giamGiaDoiTuong", 0)) > 0:
                age_cfg = b.get("coCauDoTuoi", {}) if isinstance(b.get("coCauDoTuoi"), dict) else {}
                age_discount_text = f" | Độ tuổi: TE {safe_int(age_cfg.get('treEm', 0))}/TN {safe_int(age_cfg.get('trungNien', 0))}/CT {safe_int(age_cfg.get('nguoiCaoTuoi', 0))} (-{format_currency(b.get('giamGiaDoiTuong', 0))})"
            refund_text = f" | Hoàn tiền: {b.get('trangThaiHoanTien')}" if str(b.get("trangThaiHoanTien", "")).strip() else ""

            booking_label = tk.Label(
                left,
                text=(
                    f"Mã: {b['maBooking']} | Ngày: {t['ngay']} | Số người: {b['soNguoi']} | "
                    f"Trạng thái: {b['trangThai']} | Hình thức TT: {b.get('hinhThucThanhToan', 'Tiền mặt')} | "
                    f"Đã thanh toán: {format_currency(b.get('daThanhToan', 0))} | Còn nợ: {format_currency(b.get('conNo', 0))}"
                    f"{age_discount_text}{voucher_text}{refund_text}"
                ),
                font=("Times New Roman", 12), bg=THEME["surface"],
                wraplength=responsive_wraplength(base_offset=420, minimum=300), justify="left"
            )
            booking_label.pack(anchor="w", pady=(4, 0))

            def sync_booking_wrap(event, label=booking_label):
                label.config(wraplength=max(300, event.width - 230))
            card.bind("<Configure>", sync_booking_wrap)

            cancel_allowed = True
            try:
                dep_date = datetime.strptime(str(t.get("ngay", "")).strip(), "%d/%m/%Y").date()
                if (dep_date - datetime.now().date()).days < 3:
                    cancel_allowed = False
            except Exception:
                pass

            if b.get("trangThai") not in BOOKING_CANCEL_STATUSES:
                if safe_int(b.get("conNo", 0)) > 0:
                    style_button(card, "Thanh toán", THEME["primary"], lambda m=b["maBooking"]: cap_nhat_thanh_toan(m)).pack(side="right", padx=(0, 8))
                
                if cancel_allowed:
                    style_button(card, "Hủy", THEME["danger"], lambda m=b["maBooking"]: huy_tour(m)).pack(side="right")
                else:
                    btn_huy = style_button(card, "Hủy", "#94a3b8", lambda: messagebox.showwarning("Không thể hủy", "Tour khởi hành trong vòng dưới 3 ngày, bạn không thể tự hủy booking này."))
                    try: btn_huy.config(state="disabled", cursor="arrow")
                    except Exception: pass
                    btn_huy.pack(side="right")

        set_status("Đang ở mục: Tour đã đặt", THEME["primary"])

    def tab_lich_su_booking():
        clear_container()
        app["current_tab"] = "history"

        bookings = [b for b in my_bookings() if b.get("trangThai") == "Đã hoàn thành" or b.get("bookingState") == "completed"]
        stats_wrap = tk.Frame(content_area, bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))

        paid_total = sum(safe_int(b.get("daThanhToan", 0)) for b in bookings)
        build_stat_card(stats_wrap, "Số tour đã đi", str(len(bookings)), "Số tour bạn đã hoàn thành.", THEME["success"])
        build_stat_card(stats_wrap, "Tổng tiền đã trả", format_currency(paid_total), "Tổng chi phí các chuyến đi đã hoàn tất.", THEME["primary"])

        _, body = make_section(
            content_area, "Lịch sử booking của bạn",
            "Xem lại các chuyến đi đã hoàn thành và trải nghiệm tuyệt vời cùng Vietnam Travel.",
            accent="#059669",
        )

        if not bookings:
            tk.Label(body, text="Bạn chưa có chuyến đi nào hoàn thành.", font=("Times New Roman", 13), bg=THEME["surface"], fg=THEME["muted"]).pack(pady=40)
            return

        list_area = tk.Frame(body, bg=THEME["surface"])
        list_area.pack(fill="both", expand=True)

        for b in bookings:
            t = app["ql"].find_tour(b["maTour"])
            tour_name = t['ten'] if t else "Không tìm thấy thông tin tour"
            tour_date = t['ngay'] if t else b.get("ngayDat", "")

            card = tk.Frame(list_area, bg=THEME["surface"], bd=1, relief="solid", padx=15, pady=12)
            card.pack(fill="x", pady=6)

            left = tk.Frame(card, bg=THEME["surface"])
            left.pack(side="left", fill="both", expand=True)

            tk.Label(left, text=f"{tour_name}", font=("Times New Roman", 14, "bold"), bg=THEME["surface"], fg=THEME["success"]).pack(anchor="w")

            voucher_text = f" | Voucher: {b.get('maVoucher')} (-{format_currency(b.get('giamGiaVoucher', 0))})" if str(b.get("maVoucher", "")).strip() else ""
            age_discount_text = ""
            if safe_int(b.get("giamGiaDoiTuong", 0)) > 0:
                age_cfg = b.get("coCauDoTuoi", {}) if isinstance(b.get("coCauDoTuoi"), dict) else {}
                age_discount_text = f" | Độ tuổi: TE {safe_int(age_cfg.get('treEm', 0))}/TN {safe_int(age_cfg.get('trungNien', 0))}/CT {safe_int(age_cfg.get('nguoiCaoTuoi', 0))} (-{format_currency(b.get('giamGiaDoiTuong', 0))})"

            booking_label = tk.Label(
                left,
                text=(
                    f"Mã: {b['maBooking']} | Ngày khởi hành: {tour_date} | Ngày đặt: {b.get('ngayDat', '')} | Số người: {b['soNguoi']} | "
                    f"Trạng thái: {b['trangThai']} | Hình thức TT: {b.get('hinhThucThanhToan', 'Tiền mặt')} | "
                    f"Tổng tiền: {format_currency(b.get('tongTien', 0))} | Đã thanh toán: {format_currency(b.get('daThanhToan', 0))}"
                    f"{age_discount_text}{voucher_text}"
                ),
                font=("Times New Roman", 12), bg=THEME["surface"],
                wraplength=responsive_wraplength(base_offset=420, minimum=300), justify="left"
            )
            booking_label.pack(anchor="w", pady=(4, 0))

            def sync_booking_wrap(event, label=booking_label):
                label.config(wraplength=max(300, event.width - 50))
            card.bind("<Configure>", sync_booking_wrap)

        set_status("Đang ở mục: Lịch sử booking", THEME["primary"])

    def cap_nhat_thanh_toan(ma_booking):
        booking = next((b for b in app["ql"].list_bookings if b["maBooking"] == ma_booking), None)
        if not booking: return

        if booking.get("trangThai") in BOOKING_CANCEL_STATUSES:
            return messagebox.showwarning("Không thể thanh toán", "Booking này đang ở trạng thái hủy/hoàn tiền.")

        tong_tien = safe_int(booking.get("tongTien", 0))
        tong_tien_goc = safe_int(booking.get("tongTienGoc", tong_tien))
        giam_doi_tuong = safe_int(booking.get("giamGiaDoiTuong", 0))
        giam_voucher = safe_int(booking.get("giamGiaVoucher", 0))
        da_thanh_toan = safe_int(booking.get("daThanhToan", 0))
        con_no = max(tong_tien - da_thanh_toan, 0)

        if con_no <= 0:
            return messagebox.showinfo("Đã hoàn tất", "Booking này đã thanh toán đủ.")

        top = tk.Toplevel(root)
        top.title(f"Thanh toán booking {ma_booking}")
        screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
        top.geometry(f"{min(620, max(520, screen_w - 80))}x{min(760, max(560, screen_h - 120))}")
        top.configure(bg=THEME["bg"])
        top.transient(root)
        top.grab_set()

        canvas = tk.Canvas(top, bg=THEME["bg"], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(top, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        card = tk.Frame(canvas, bg=THEME["surface"], bd=1, relief="solid", padx=20, pady=20)
        card_window = canvas.create_window((0, 0), window=card, anchor="nw")

        def on_card_configure(event):
            try:
                sync_payment_layout()
            except Exception:
                pass
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_resize(event):
            canvas.itemconfig(card_window, width=max(event.width - 2, 1))

        card.bind("<Configure>", on_card_configure)
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Bind mousewheel to the Toplevel window so scrolling works smoothly everywhere inside the popup
        top.bind("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units"))

        tk.Label(card, text=f"Booking: {ma_booking}", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 14, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(
            card,
            text=(
                f"Tổng gốc: {format_currency(tong_tien_goc)}\n"
                f"Giảm độ tuổi: {format_currency(giam_doi_tuong)}\n"
                f"Giảm voucher: {format_currency(giam_voucher)}" + (f" ({booking.get('maVoucher', '')})\n" if str(booking.get("maVoucher", "")).strip() else "\n") +
                f"Tổng tiền: {format_currency(tong_tien)}\n"
                f"Đã thanh toán: {format_currency(da_thanh_toan)}\n"
                f"Còn nợ: {format_currency(con_no)}"
            ),
            bg=THEME["surface"], fg=THEME["text"], justify="left", font=("Times New Roman", 12),
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(card, text="Hình thức thanh toán:", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 12, "bold")).pack(anchor="w")
        current_method = booking.get("hinhThucThanhToan", PAYMENT_METHODS[0])
        if current_method not in PAYMENT_METHODS: current_method = PAYMENT_METHODS[0]
        method_var = tk.StringVar(value=current_method)
        cmb_method = ttk.Combobox(card, textvariable=method_var, values=PAYMENT_METHODS, state="readonly", font=("Times New Roman", 11), width=28)
        cmb_method.pack(anchor="w", pady=(4, 12))

        tour_for_booking = app["ql"].find_tour(booking.get("maTour", ""))
        cash_policy_var = tk.StringVar(value="")
        cash_policy_lbl = tk.Label(card, textvariable=cash_policy_var, bg=THEME["surface"], fg=THEME["warning"], justify="left", font=("Times New Roman", 11, "bold"), wraplength=460)
        cash_policy_lbl.pack(anchor="w", pady=(0, 10))

        tk.Label(card, text="Số tiền thanh toán thêm:", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 12, "bold")).pack(anchor="w")
        pay_more_frame = tk.Frame(card, bg=THEME["surface"])
        pay_more_frame.pack(anchor="w", pady=(4, 10), fill="x")
        amount_entry = tk.Entry(pay_more_frame, font=("Times New Roman", 12), relief="solid", bd=1)
        amount_entry.insert(0, str(con_no))
        amount_entry.pack(side="top", fill="x", ipady=4)

        quick_pay_more_fr = tk.Frame(pay_more_frame, bg=THEME["surface"])
        quick_pay_more_fr.pack(side="top", fill="x", pady=(4, 0))

        def set_pay_more(percent):
            val = int(con_no * percent)
            amount_entry.delete(0, "end")
            amount_entry.insert(0, str(val))
            update_payment_qr()

        btn_pay_50 = tk.Button(quick_pay_more_fr, text="Trả 50% nợ", font=("Times New Roman", 9), relief="solid", bd=1, cursor="hand2", bg=THEME["surface"], command=lambda: set_pay_more(0.5))
        btn_pay_50.pack(side="left", padx=(0, 4))
        btn_pay_all = tk.Button(quick_pay_more_fr, text="Trả hết nợ", font=("Times New Roman", 9), relief="solid", bd=1, cursor="hand2", bg=THEME["surface"], command=lambda: set_pay_more(1.0))
        btn_pay_all.pack(side="left")

        qr_box = tk.Frame(card, bg=THEME["note_bg"], bd=1, relief="solid", padx=8, pady=8)
        qr_box.pack(fill="x", pady=(0, 10))
        tk.Label(qr_box, text="QR Chuyển khoản", font=("Times New Roman", 12, "bold"), bg=THEME["note_bg"], fg=THEME["note_fg"]).pack(anchor="w")

        qr_image_lbl = tk.Label(qr_box, text="", bg=THEME["note_bg"], fg=THEME["muted"], justify="center", wraplength=240)
        qr_image_lbl.pack(anchor="center", pady=(6, 6))
        qr_status_var = tk.StringVar(value="")
        qr_status_lbl = tk.Label(qr_box, textvariable=qr_status_var, font=("Times New Roman", 10), bg=THEME["note_bg"], fg=THEME["note_fg"], justify="left", wraplength=420)
        qr_status_lbl.pack(anchor="w")

        # Bank details panel (dialog)
        bank_details_dialog_fr = tk.Frame(qr_box, bg=THEME["note_bg"])
        bank_details_dialog_fr.pack(fill="x", pady=(5, 5))

        stk_dialog_row = tk.Frame(bank_details_dialog_fr, bg=THEME["note_bg"])
        stk_dialog_row.pack(fill="x", pady=2)
        tk.Label(stk_dialog_row, text="Số tài khoản: 41389377 (ACB)", font=("Times New Roman", 10, "bold"), bg=THEME["note_bg"], fg=THEME["text"]).pack(side="left")
        btn_copy_stk_dialog = tk.Button(stk_dialog_row, text="Sao chép", font=("Times New Roman", 8), bg=THEME["surface"], bd=1, relief="solid", cursor="hand2", command=lambda: copy_to_clipboard(root, "41389377", btn_copy_stk_dialog, "Sao chép"))
        btn_copy_stk_dialog.pack(side="right", padx=(5, 0))

        nd_dialog_row = tk.Frame(bank_details_dialog_fr, bg=THEME["note_bg"])
        nd_dialog_row.pack(fill="x", pady=2)
        tk.Label(nd_dialog_row, text="Nội dung CK: ", font=("Times New Roman", 10, "bold"), bg=THEME["note_bg"], fg=THEME["text"]).pack(side="left")
        
        qr_transfer_content_var = tk.StringVar(value="-")
        lbl_transfer_content_dialog = tk.Label(nd_dialog_row, textvariable=qr_transfer_content_var, font=("Times New Roman", 10, "bold"), bg=THEME["note_bg"], fg=THEME["primary"])
        lbl_transfer_content_dialog.pack(side="left")

        btn_copy_nd_dialog = tk.Button(nd_dialog_row, text="Sao chép", font=("Times New Roman", 8), bg=THEME["surface"], bd=1, relief="solid", cursor="hand2", command=lambda: copy_to_clipboard(root, qr_transfer_content_var.get(), btn_copy_nd_dialog, "Sao chép"))
        btn_copy_nd_dialog.pack(side="right", padx=(5, 0))

        qr_note_var = tk.StringVar(value="")
        qr_note_lbl = tk.Label(qr_box, textvariable=qr_note_var, font=("Times New Roman", 9, "italic"), bg=THEME["note_bg"], fg=THEME["muted"], justify="left", wraplength=420)
        qr_note_lbl.pack(anchor="w", pady=(3, 0))
        payment_qr_request_id = {"value": 0}

        def sync_payment_layout(_event=None):
            wrap_size = max(260, card.winfo_width() - 56)
            cash_policy_lbl.config(wraplength=wrap_size)
            qr_image_lbl.config(wraplength=wrap_size)
            qr_status_lbl.config(wraplength=wrap_size)
            qr_note_lbl.config(wraplength=wrap_size)

        sync_payment_layout()

        def update_payment_qr():
            if method_var.get().strip() != "Chuyển khoản":
                payment_qr_request_id["value"] += 1
                qr_box.pack_forget()
                qr_image_lbl.config(image="", text="")
                qr_image_lbl.image = None
                qr_status_var.set("")
                qr_note_var.set("")
                cash_policy_var.set(build_cash_policy_notice(tour_for_booking.get("ngay", "")) if tour_for_booking else build_cash_policy_notice(""))
                try:
                    top.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                except Exception:
                    pass
                return

            cash_policy_var.set("")
            qr_box.pack(fill="x", pady=(0, 10), before=btns)
            pay_more = max(0, safe_int(amount_entry.get()))
            if pay_more <= 0:
                qr_image_lbl.config(image="", text="Nhập số tiền để tạo QR")
                qr_image_lbl.image = None
                qr_status_var.set("Số tiền thanh toán thêm phải lớn hơn 0.")
                qr_note_var.set("")
                try:
                    top.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                except Exception:
                    pass
                return

            transfer_content = f"{ma_booking}-{user_data.get('username', 'KH')}-{pay_more}"
            qr_transfer_content_var.set(transfer_content)
            payment_qr_request_id["value"] += 1
            current_request_id = payment_qr_request_id["value"]
            qr_image_lbl.config(image="", text="Đang tải QR...")
            qr_image_lbl.image = None
            qr_status_var.set("Đang tải mã chuyển khoản, vui lòng chờ...")
            qr_note_var.set("")
            try:
                top.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            except Exception:
                pass

            def worker():
                try:
                    qr_url = build_transfer_qr_url(pay_more, transfer_content)
                    qr_photo = fetch_transfer_qr_photo(qr_url, max_size_px=220)
                except (OSError, URLError, ValueError, tk.TclError) as exc:
                    error_message = short_ui_error(exc)

                    def apply_error():
                        if current_request_id != payment_qr_request_id["value"] or method_var.get().strip() != "Chuyển khoản": return
                        qr_image_lbl.config(image="", text="(Không tải được QR)"); qr_image_lbl.image = None
                        qr_status_var.set("Không thể gọi API QR. Vui lòng thử lại sau.")
                        qr_note_var.set(error_message)
                        try:
                            top.update_idletasks()
                            canvas.configure(scrollregion=canvas.bbox("all"))
                        except Exception:
                            pass

                    root.after(0, apply_error)
                    return

                def apply_success():
                    if current_request_id != payment_qr_request_id["value"] or method_var.get().strip() != "Chuyển khoản": return
                    qr_image_lbl.config(image=qr_photo, text=""); qr_image_lbl.image = qr_photo
                    qr_status_var.set(f"Quét mã để thanh toán thêm {pay_more:,}đ".replace(",", "."))
                    qr_note_var.set("Nội dung CK được tạo tự động theo mã booking.")
                    try:
                        top.update_idletasks()
                        canvas.configure(scrollregion=canvas.bbox("all"))
                    except Exception:
                        pass

                root.after(0, apply_success)

            threading.Thread(target=worker, daemon=True).start()

        cmb_method.bind("<<ComboboxSelected>>", lambda _e: update_payment_qr())
        amount_entry.bind("<KeyRelease>", lambda _e: update_payment_qr())

        def submit_payment():
            result = service_apply_payment(
                app["ql"], ma_booking, amount_entry.get(),
                method_var.get().strip() or PAYMENT_METHODS[0],
                actor=user_data.get("username", ""), role="user",
            )
            if not result.success:
                return messagebox.showwarning("Lỗi", result.message, parent=top)
            top.destroy()
            messagebox.showinfo("Thành công", result.message)
            tab_tour_da_dat()

        btns = tk.Frame(card, bg=THEME["surface"])
        btns.pack(fill="x", pady=(8, 0))
        style_button(btns, "Xác nhận", THEME["success"], submit_payment).pack(side="left", fill="x", expand=True, padx=(0, 6))
        style_button(btns, "Đóng", THEME["muted"], top.destroy).pack(side="left", fill="x", expand=True)
        update_payment_qr()

    def huy_tour(ma_booking):
        booking = next((b for b in app["ql"].list_bookings if b["maBooking"] == ma_booking), None)
        if booking:
            tour = app["ql"].find_tour(booking.get("maTour"))
            if tour:
                try:
                    dep_date = datetime.strptime(str(tour.get("ngay", "")).strip(), "%d/%m/%Y").date()
                    if (dep_date - datetime.now().date()).days < 3:
                        messagebox.showerror("Lỗi", "Tour khởi hành trong vòng dưới 3 ngày, bạn không thể tự hủy booking này.")
                        return
                except Exception:
                    pass

        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn hủy đặt chỗ {ma_booking}?"):
            result = service_cancel_booking(
                app["ql"], ma_booking, actor=user_data.get("username", ""), role="user",
            )
            if not result.success:
                return messagebox.showwarning("Không thể hủy", result.message)

            messagebox.showinfo("Thành công", result.message)
            tab_tour_da_dat()

    def tab_gui_danh_gia():
        clear_container()
        app["current_tab"] = "review"

        _, body = make_section(
            content_area, "Gửi ý kiến phản hồi",
            "Góp ý chất lượng dịch vụ hoặc đánh giá riêng cho hướng dẫn viên đã đồng hành cùng bạn.",
            accent="#059669",
        )

        card = tk.Frame(body, bg=THEME["surface"], padx=25, pady=25)
        card.pack(fill="both", expand=True)
        sent_reviews_frame = tk.Frame(body, bg=THEME["surface"], padx=18, pady=18)
        sent_reviews_frame.pack(fill="both", expand=True, pady=(12, 0))

        booking_sel_fr = tk.Frame(card, bg=THEME["surface"])
        booking_sel_fr.pack(fill="x", pady=(0, 15))
        tk.Label(booking_sel_fr, text="Chọn Booking đủ điều kiện đánh giá:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"]).pack(anchor="w", pady=(0, 5))
        
        tour_sel_var = tk.StringVar()
        tour_sel_map = {}
        tour_sel_cb = ttk.Combobox(booking_sel_fr, textvariable=tour_sel_var, values=[], state="readonly", width=60, font=("Times New Roman", 11))
        tour_sel_cb.pack(fill="x", expand=True)

        warning_label = tk.Label(card, text="Bạn chỉ có thể đánh giá sau khi tour đã hoàn thành.", font=("Times New Roman", 13, "bold"), bg=THEME["surface"], fg=THEME["danger"])
        info_fr = tk.LabelFrame(card, text="Thông tin chi tiết booking", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg=THEME["primary"], padx=15, pady=10)
        
        lbl_ma_booking = tk.Label(info_fr, text="Mã booking: -", font=("Times New Roman", 12), bg=THEME["surface"], fg=THEME["text"]); lbl_ma_booking.pack(anchor="w", pady=2)
        lbl_ten_tour = tk.Label(info_fr, text="Tên tour: -", font=("Times New Roman", 12), bg=THEME["surface"], fg=THEME["text"]); lbl_ten_tour.pack(anchor="w", pady=2)
        lbl_ten_hdv = tk.Label(info_fr, text="Hướng dẫn viên: Không có", font=("Times New Roman", 12), bg=THEME["surface"], fg=THEME["text"]); lbl_ten_hdv.pack(anchor="w", pady=2)
        lbl_trang_thai = tk.Label(info_fr, text="Trạng thái booking: -", font=("Times New Roman", 12), bg=THEME["surface"], fg=THEME["text"]); lbl_trang_thai.pack(anchor="w", pady=2)

        dynamic_forms_container = tk.Frame(card, bg=THEME["surface"])
        dynamic_forms_container.pack(fill="both", expand=True)

        btn_fr = tk.Frame(card, bg=THEME["surface"])
        submit_btn = style_button(btn_fr, "GỬI ĐÁNH GIÁ", THEME["primary"], lambda: gui_review())
        submit_btn.pack()

        review_inputs = {
            "show_tour": False, "show_hdv": False, "tour_rating_var": None,
            "txt_tour": None, "scores": {}, "txt_hdv": None, "hdv_code": ""
        }

        def get_eligible_bookings():
            eligible = []
            for booking in my_bookings():
                tour = app["ql"].find_tour(booking.get("maTour", ""))
                booking_status = str(booking.get("trangThai", "")).strip()
                if booking_status in {"Mới tạo", "Đã cọc", "Đã thanh toán", "Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}:
                    continue
                
                booking_state = booking_state_from_status(booking_status, str(booking.get("trangThaiHoanTien", "")).strip())
                tour_status = str((tour or {}).get("trangThai", "")).strip()
                tour_state = str((tour or {}).get("tourState", "")).strip()

                is_completed = (booking_status == "Đã hoàn thành" or booking_state == BOOKING_STATE_COMPLETED or tour_status == "Đã kết thúc" or tour_state == "completed")
                if not is_completed: continue

                has_tour_review = any(
                    str(review.get("maBooking", "")).strip() == str(booking.get("maBooking", "")).strip()
                    and str(review.get("username", "")).strip().lower() == str(user_data.get("username", "")).strip().lower()
                    and str(review.get("target", "")).strip().lower() == "tour"
                    for review in app["ql"].list_reviews
                )

                hdv_code = str((tour or {}).get("hdvPhuTrach", "")).strip()
                has_hdv = bool(hdv_code)
                has_hdv_review = False
                if has_hdv:
                    has_hdv_review = any(
                        str(review.get("maBooking", "")).strip() == str(booking.get("maBooking", "")).strip()
                        and str(review.get("username", "")).strip().lower() == str(user_data.get("username", "")).strip().lower()
                        and str(review.get("target", "")).strip().lower() == "hdv"
                        for review in app["ql"].list_reviews
                    )

                if not has_tour_review or (has_hdv and not has_hdv_review):
                    eligible.append(booking)
            return eligible

        def on_booking_selected(*args):
            for widget in dynamic_forms_container.winfo_children(): widget.destroy()

            selected_display = tour_sel_var.get()
            booking = tour_sel_map.get(selected_display)
            
            review_inputs.update({"show_tour": False, "show_hdv": False, "tour_rating_var": None, "txt_tour": None, "scores": {}, "txt_hdv": None, "hdv_code": ""})

            if not booking:
                lbl_ma_booking.config(text="Mã booking: -")
                lbl_ten_tour.config(text="Tên tour: -")
                lbl_ten_hdv.config(text="Hướng dẫn viên: Không có")
                lbl_trang_thai.config(text="Trạng thái booking: -")
                btn_fr.pack_forget()
                return

            tour = app["ql"].find_tour(booking.get("maTour", ""))
            lbl_ma_booking.config(text=f"Mã booking: {booking.get('maBooking', '-')}")
            lbl_trang_thai.config(text=f"Trạng thái booking: {booking.get('trangThai', '-')}")
            
            hdv_code = ""
            if tour:
                lbl_ten_tour.config(text=f"Tên tour: {tour.get('ten', '-')}")
                hdv_code = str(tour.get("hdvPhuTrach", "")).strip()
                if hdv_code:
                    h = app["ql"].find_hdv(hdv_code)
                    lbl_ten_hdv.config(text=f"Hướng dẫn viên: {hdv_code} - {h.get('tenHDV') if h else hdv_code}")
                else:
                    lbl_ten_hdv.config(text="Hướng dẫn viên: Không có")
            else:
                lbl_ten_tour.config(text="Tên tour: -")
                lbl_ten_hdv.config(text="Hướng dẫn viên: Không có")

            review_inputs["hdv_code"] = hdv_code

            has_tour_review = any(
                str(review.get("maBooking", "")).strip() == str(booking.get("maBooking", "")).strip()
                and str(review.get("username", "")).strip().lower() == str(user_data.get("username", "")).strip().lower()
                and str(review.get("target", "")).strip().lower() == "tour"
                for review in app["ql"].list_reviews
            )

            has_hdv = bool(hdv_code)
            has_hdv_review = False
            if has_hdv:
                has_hdv_review = any(
                    str(review.get("maBooking", "")).strip() == str(booking.get("maBooking", "")).strip()
                    and str(review.get("username", "")).strip().lower() == str(user_data.get("username", "")).strip().lower()
                    and str(review.get("target", "")).strip().lower() == "hdv"
                    for review in app["ql"].list_reviews
                )

            need_tour = not has_tour_review
            need_hdv = has_hdv and not has_hdv_review

            layout_fr = tk.Frame(dynamic_forms_container, bg=THEME["surface"])
            layout_fr.pack(fill="both", expand=True)

            if need_tour and need_hdv:
                layout_fr.columnconfigure(0, weight=1, uniform="group1")
                layout_fr.columnconfigure(1, weight=1, uniform="group1")
                tour_lf = tk.LabelFrame(layout_fr, text="ĐÁNH GIÁ DỊCH VỤ TOUR", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg="#0284c7", padx=10, pady=10)
                tour_lf.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
                hdv_lf = tk.LabelFrame(layout_fr, text="ĐÁNH GIÁ HƯỚNG DẪN VIÊN (HDV)", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg="#7c3aed", padx=10, pady=10)
                hdv_lf.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
                _build_tour_inputs(tour_lf)
                _build_hdv_inputs(hdv_lf)
            else:
                if need_tour:
                    tour_lf = tk.LabelFrame(layout_fr, text="ĐÁNH GIÁ DỊCH VỤ TOUR", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg="#0284c7", padx=15, pady=10)
                    tour_lf.pack(fill="x", pady=5)
                    _build_tour_inputs(tour_lf)
                elif has_tour_review:
                    tk.Label(layout_fr, text="✓ Bạn đã gửi đánh giá cho Tour của booking này.", font=("Times New Roman", 11, "italic"), bg=THEME["surface"], fg="#059669").pack(anchor="w", pady=5)

                if need_hdv:
                    hdv_lf = tk.LabelFrame(layout_fr, text="ĐÁNH GIÁ HƯỚNG DẪN VIÊN (HDV)", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg="#7c3aed", padx=15, pady=10)
                    hdv_lf.pack(fill="x", pady=5)
                    _build_hdv_inputs(hdv_lf)
                elif not has_hdv:
                    tk.Label(layout_fr, text="ℹ Tour này không có Hướng dẫn viên phụ trách.", font=("Times New Roman", 11, "italic"), bg=THEME["surface"], fg=THEME["muted"]).pack(anchor="w", pady=5)
                else:
                    tk.Label(layout_fr, text="✓ Bạn đã gửi đánh giá cho Hướng dẫn viên của booking này.", font=("Times New Roman", 11, "italic"), bg=THEME["surface"], fg="#059669").pack(anchor="w", pady=5)

            btn_fr.pack(fill="x", pady=10)

        def _build_tour_inputs(parent_frame):
            review_inputs["show_tour"] = True
            tour_rating_var = tk.StringVar(value="5")
            review_inputs["tour_rating_var"] = tour_rating_var
            
            rating_row = tk.Frame(parent_frame, bg=THEME["surface"])
            rating_row.pack(fill="x", pady=4)
            tk.Label(rating_row, text="Điểm đánh giá dịch vụ (1-5):", font=("Times New Roman", 11, "bold"), bg=THEME["surface"]).pack(side="left", padx=(0, 10))
            ttk.Combobox(rating_row, textvariable=tour_rating_var, values=["1", "2", "3", "4", "5"], state="readonly", width=6, font=("Times New Roman", 11)).pack(side="left")
            
            tk.Label(parent_frame, text="Nhận xét chất lượng dịch vụ:", font=("Times New Roman", 11, "bold"), bg=THEME["surface"]).pack(anchor="w", pady=(10, 4))
            txt_tour = tk.Text(parent_frame, height=3, font=("Times New Roman", 11), relief="solid", bd=1, wrap="word")
            txt_tour.pack(fill="both", expand=True)
            review_inputs["txt_tour"] = txt_tour

        def _build_hdv_inputs(parent_frame):
            review_inputs["show_hdv"] = True
            scores = {}
            for label, key in [("Kiến thức chuyên môn", "skill"), ("Thái độ phục vụ", "attitude"), ("Xử lý tình huống", "problem")]:
                row = tk.Frame(parent_frame, bg=THEME["surface"])
                row.pack(fill="x", pady=3)
                tk.Label(row, text=label, anchor="w", justify="left", bg=THEME["surface"], font=("Times New Roman", 11)).pack(fill="x", anchor="w")
                s = tk.Scale(row, from_=0, to=100, orient="horizontal", bg=THEME["surface"], showvalue=True, highlightthickness=0, length=200)
                s.set(80); s.pack(fill="x", expand=True, pady=(2, 0))
                scores[key] = s
            
            review_inputs["scores"] = scores
            tk.Label(parent_frame, text="Nhận xét về Hướng dẫn viên:", font=("Times New Roman", 11, "bold"), bg=THEME["surface"]).pack(anchor="w", pady=(8, 4))
            txt_hdv = tk.Text(parent_frame, height=3, font=("Times New Roman", 11), relief="solid", bd=1, wrap="word")
            txt_hdv.pack(fill="both", expand=True)
            review_inputs["txt_hdv"] = txt_hdv

        tour_sel_var.trace_add("write", on_booking_selected)

        def refresh_ui():
            eligible_bookings = get_eligible_bookings()
            tour_sel_map.clear()
            options = []
            
            for booking in eligible_bookings:
                ma_booking, ma_tour = str(booking.get("maBooking", "")).strip(), str(booking.get("maTour", "")).strip()
                tour = app["ql"].find_tour(ma_tour)
                ten_tour = str((tour or {}).get("ten", "")).strip()
                display = f"{ma_booking} | {ma_tour} - {ten_tour}" if ten_tour else f"{ma_booking} | {ma_tour}"
                options.append(display)
                tour_sel_map[display] = booking
            
            tour_sel_cb["values"] = options
            if options:
                warning_label.pack_forget()
                booking_sel_fr.pack(fill="x", pady=(0, 15))
                info_fr.pack(fill="x", pady=(0, 15))
                dynamic_forms_container.pack(fill="both", expand=True)
                tour_sel_var.set(options[0])
                on_booking_selected()
            else:
                booking_sel_fr.pack_forget()
                info_fr.pack_forget()
                dynamic_forms_container.pack_forget()
                btn_fr.pack_forget()
                warning_label.pack(pady=40)
                tour_sel_var.set("")
                on_booking_selected()
            render_sent_reviews()

        def render_sent_reviews():
            for widget in sent_reviews_frame.winfo_children(): widget.destroy()

            def _short(value, limit=40):
                text = str(value or "").strip()
                return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."

            tk.Label(sent_reviews_frame, text="Đánh giá đã gửi", font=("Times New Roman", 14, "bold"), bg=THEME["surface"], fg=THEME["text"]).pack(anchor="w")

            username = str(user_data.get("username", "")).strip().lower()
            my_reviews = [normalize_review_item(r) for r in app["ql"].list_reviews if str(r.get("username", "")).strip().lower() == username]

            wrapper = tk.Frame(sent_reviews_frame, bg=THEME["surface"], bd=1, relief="solid")
            wrapper.pack(fill="both", expand=True, pady=(8, 0))
            cols = ("ma", "booking", "tour", "target", "date", "rating", "content", "reply")
            tree = ttk.Treeview(wrapper, columns=cols, show="headings", height=6)
            headers = {"ma": "Mã", "booking": "Booking", "tour": "Tour", "target": "Đối tượng", "date": "Ngày gửi", "rating": "Điểm", "content": "Nội dung", "reply": "Phản hồi Admin"}
            widths = {"ma": 85, "booking": 90, "tour": 180, "target": 90, "date": 125, "rating": 65, "content": 240, "reply": 260}
            for col in cols:
                tree.heading(col, text=headers[col])
                tree.column(col, width=widths[col], minwidth=60, anchor="center" if col not in {"tour", "content", "reply"} else "w", stretch=col in {"tour", "content", "reply"})

            review_by_id = {}
            for review in my_reviews:
                ma_review = str(review.get("maReview", "")).strip()
                review_by_id[ma_review] = review
                reply = str(review.get("adminReply", "")).strip()
                tree.insert("", "end", values=(
                    _short(ma_review, 16), _short(review.get("maBooking", ""), 16),
                    _short(review.get("tenTour", "") or review.get("maTour", ""), 28),
                    _short(review.get("target", ""), 12), _short(review.get("date", ""), 16),
                    _short(review.get("rating", ""), 8), _short(review.get("content", ""), 38),
                    _short(reply, 42) if reply else "Chưa có phản hồi",
                ), tags=(ma_review,))

            if not my_reviews:
                tree.insert("", "end", values=("Chưa có đánh giá", "", "", "", "", "", "", ""))

            sy, sx = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview), ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
            bind_autohide_scrollbar(tree, sy, "vertical"); bind_autohide_scrollbar(tree, sx, "horizontal")
            tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
            tree.pack(side="left", fill="both", expand=True)
            sy.pack(side="right", fill="y"); sx.pack(side="bottom", fill="x")
            apply_zebra(tree)

            def show_review_detail(_event=None):
                sel = tree.selection()
                if not sel: return
                tags = tree.item(sel[0], "tags")
                review = review_by_id.get(tags[0]) if tags else None
                if not review: return
                top = tk.Toplevel(root)
                top.title("Chi tiết đánh giá")
                top.geometry("650x520"); top.configure(bg=THEME["bg"])
                top.transient(root); top.grab_set()
                box = tk.Frame(top, bg=THEME["surface"], padx=18, pady=16)
                box.pack(fill="both", expand=True, padx=16, pady=16)
                for label, value in [("Mã đánh giá", review.get("maReview", "")), ("Booking", review.get("maBooking", "")), ("Tour", review.get("tenTour", "") or review.get("maTour", "")), ("Đối tượng", review.get("target", "")), ("Ngày gửi", review.get("date", "")), ("Điểm", review.get("rating", "")), ("Nội dung", review.get("content", "")), ("Phản hồi", review.get("adminReply", "") or "Chưa có phản hồi")]:
                    row = tk.Frame(box, bg=THEME["surface"]); row.pack(fill="x", pady=4)
                    tk.Label(row, text=f"{label}:", width=16, anchor="nw", bg=THEME["surface"], font=("Times New Roman", 11, "bold")).pack(side="left")
                    tk.Label(row, text=str(value), anchor="w", justify="left", wraplength=430, bg=THEME["surface"], font=("Times New Roman", 11)).pack(side="left", fill="x", expand=True)
                style_button(box, "ĐÓNG", THEME["danger"], top.destroy).pack(anchor="e", pady=(10, 0))

            tree.bind("<Double-1>", show_review_detail)

        def gui_review():
            booking = tour_sel_map.get(tour_sel_var.get())
            if not booking: return messagebox.showwarning("Lỗi", "Bạn chỉ có thể đánh giá sau khi tour đã hoàn thành.")

            ma_booking, ma_tour = booking.get("maBooking", ""), booking.get("maTour", "")
            fullname = user_data.get("fullname") or user_data.get("name", "Khách hàng")
            username = str(user_data.get("username", "")).strip()

            success_messages, error_messages = [], []

            if review_inputs["show_tour"]:
                content_tour = review_inputs["txt_tour"].get("1.0", "end").strip()
                if not content_tour: return messagebox.showwarning("Lỗi", "Vui lòng nhập nội dung nhận xét Tour!")
                if len(content_tour) > 2000: return messagebox.showwarning("Lỗi", "Nội dung nhận xét Tour quá dài!")
                
                try: rating_tour = float(review_inputs["tour_rating_var"].get())
                except ValueError: rating_tour = 5.0

                res = service_create_review(app["ql"], username=username, fullname=fullname, ma_booking=ma_booking, content=content_tour, target="Tour", target_id=ma_tour, rating=rating_tour)
                (success_messages if res.success else error_messages).append("Đánh giá Tour thành công." if res.success else f"Lỗi: {res.message}")

            if review_inputs["show_hdv"]:
                content_hdv = review_inputs["txt_hdv"].get("1.0", "end").strip()
                if not content_hdv: return messagebox.showwarning("Lỗi", "Vui lòng nhập nội dung nhận xét HDV!")
                if len(content_hdv) > 2000: return messagebox.showwarning("Lỗi", "Nội dung nhận xét HDV quá dài!")

                hdv_code = review_inputs["hdv_code"]
                scores = review_inputs["scores"]
                rating_hdv = round((scores["skill"].get() + scores["attitude"].get() + scores["problem"].get()) / 60, 1)

                res = service_create_review(app["ql"], username=username, fullname=fullname, ma_booking=ma_booking, content=content_hdv, target="HDV", target_id=hdv_code, rating=rating_hdv)
                (success_messages if res.success else error_messages).append("Đánh giá HDV thành công." if res.success else f"Lỗi: {res.message}")

            if error_messages: messagebox.showwarning("Lỗi", "\n".join(error_messages))
            elif success_messages: messagebox.showinfo("Cảm ơn", "\n".join(success_messages))
            tab_gui_danh_gia()

        refresh_ui()
        set_status("Đang ở mục: Gửi đánh giá", THEME["primary"])

    def tab_ho_so():
        clear_container()
        app["current_tab"] = "profile"

        user_info = get_current_user()

        _, body = make_section(
            content_area, "Thông tin hồ sơ cá nhân",
            "Cập nhật họ tên, số điện thoại và đổi mật khẩu nếu cần.",
            accent="#dc2626",
        )

        if not user_info:
            tk.Label(body, text="Lỗi: Không tìm thấy thông tin tài khoản!", fg=THEME["danger"], bg=THEME["surface"], font=("Times New Roman", 13, "bold")).pack()
            return

        main_container = tk.Frame(body, bg=THEME["surface"])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Thông tin tài khoản
        info_card = tk.Frame(main_container, bg="#eff6ff", highlightbackground="#93c5fd", highlightthickness=2, padx=20, pady=15)
        info_card.pack(fill="x", pady=(0, 20))
        tk.Label(info_card, text="THÔNG TIN TÀI KHOẢN", bg="#eff6ff", fg=THEME["primary"], font=("Times New Roman", 14, "bold")).pack(anchor="w", pady=(0, 12))
        
        for label, value in [("Tên đăng nhập", user_info.get("username", "-")), ("Vai trò", "Khách hàng"), ("Ngày tạo", user_info.get("ngayTao", "-"))]:
            f = tk.Frame(info_card, bg="#eff6ff"); f.pack(fill="x", pady=5)
            tk.Label(f, text=f"{label}:", bg="#eff6ff", fg=THEME["muted"], font=("Times New Roman", 11, "bold"), width=20, anchor="w").pack(side="left")
            tk.Label(f, text=str(value), bg="#eff6ff", fg=THEME["text"], font=("Times New Roman", 11), anchor="w").pack(side="left", fill="x", expand=True)

        # Thông tin cá nhân
        personal_card = tk.Frame(main_container, bg="#ffffff", highlightbackground="#22c55e", highlightthickness=2, padx=20, pady=15)
        personal_card.pack(fill="x", pady=(0, 20))
        tk.Label(personal_card, text="THÔNG TIN CÁ NHÂN", bg="#ffffff", fg="#16a34a", font=("Times New Roman", 14, "bold")).pack(anchor="w", pady=(0, 12))

        widgets = {}
        for label, key in [("Họ và tên", "fullname"), ("Số điện thoại", "sdt")]:
            f = tk.Frame(personal_card, bg="#ffffff"); f.pack(fill="x", pady=8)
            tk.Label(f, text=label, width=18, anchor="w", bg="#ffffff", font=("Times New Roman", 12, "bold")).pack(side="left")
            e = tk.Entry(f, font=("Times New Roman", 12), relief="solid", bd=1, width=40)
            e.pack(side="left", fill="x", expand=True, ipady=5)
            e.insert(0, user_info.get(key, ""))
            widgets[key] = e

        # Bảo mật
        security_card = tk.Frame(main_container, bg="#fff7ed", highlightbackground="#fb923c", highlightthickness=2, padx=20, pady=15)
        security_card.pack(fill="x", pady=(0, 20))
        tk.Label(security_card, text="BẢO MẬT TÀI KHOẢN", bg="#fff7ed", fg="#c2410c", font=("Times New Roman", 14, "bold")).pack(anchor="w", pady=(0, 10))
        tk.Label(security_card, text="Lưu ý: Để trống nếu giữ nguyên mật khẩu hiện tại.", bg="#fff7ed", fg="#9a3412", font=("Times New Roman", 10, "italic")).pack(anchor="w", pady=(0, 12))
        
        pass_frame = tk.Frame(security_card, bg="#fff7ed"); pass_frame.pack(fill="x")
        tk.Label(pass_frame, text="Mật khẩu mới", width=18, anchor="w", bg="#fff7ed", font=("Times New Roman", 12, "bold")).pack(side="left")
        pass_entry = tk.Entry(pass_frame, font=("Times New Roman", 12), relief="solid", bd=1, width=40, show="*")
        pass_entry.pack(side="left", fill="x", expand=True, ipady=5)
        widgets["password"] = pass_entry

        actions_card = tk.Frame(main_container, bg=THEME["surface"])
        actions_card.pack(fill="x", pady=(10, 0))

        def save_profile():
            new_fn, new_phone, new_pass = widgets["fullname"].get().strip(), widgets["sdt"].get().strip(), widgets["password"].get().strip()
            if not is_valid_fullname(new_fn): return messagebox.showwarning("Lỗi", "Họ tên tối thiểu 3 ký tự.")
            if not is_valid_phone(new_phone): return messagebox.showwarning("Lỗi", "SĐT không hợp lệ (10 số, bắt đầu bằng 0).")
            if new_pass and not is_valid_password(new_pass): return messagebox.showwarning("Lỗi", "Mật khẩu tối thiểu 3 ký tự.")

            for u in app["ql"].list_users:
                if u.get("username") != user_info.get("username") and u.get("sdt") == new_phone:
                    return messagebox.showwarning("Lỗi", "Số điện thoại đã tồn tại ở tài khoản khác.")

            user_info.update({"fullname": new_fn, "sdt": new_phone})
            if new_pass: user_info["password"] = prepare_password_for_storage(new_pass)
            user_data.update({"fullname": new_fn, "name": new_fn, "sdt": new_phone})

            app["ql"].save()
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin cá nhân!")
            khoi_tao_khach(root, user_data)

        style_button(actions_card, "LƯU THÔNG TIN", THEME["success"], save_profile).pack(side="left", padx=(0, 8))
        style_button(actions_card, "LÀM MỚI", THEME["primary"], tab_ho_so).pack(side="left")
        set_status("Đang ở mục: Hồ sơ cá nhân", THEME["primary"])

    def tab_thong_bao():
        clear_container()
        app["current_tab"] = "notification"

        _, body = make_section(
            content_area, "Thông báo từ hệ thống",
            "Cập nhật các thông báo mới nhất từ các tour bạn đã đăng ký.",
            accent="#d97706",
        )

        container = tk.Frame(body, bg=THEME["surface"]); container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, bg=THEME["surface"], bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=THEME["surface"])
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")))
        scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        my_tour_codes = {str(b.get("maTour", "")).strip() for b in app["ql"].list_bookings if str(b.get("usernameDat", "")).strip() == str(user_data.get("username", "")).strip() and b.get("maTour")}
        relevant_notifs, seen_notifs = [], set()
        my_username = str(user_data.get("username", "")).strip().lower()

        for n in app["ql"].list_notifications:
            norm = normalize_notification_item(n, datastore=app["ql"])
            ma_tour = str(norm.get("maTour", "")).strip()
            notif_user = str(norm.get("username", "")).strip().lower()
            if ma_tour in my_tour_codes or (notif_user and notif_user == my_username):
                sig = (ma_tour, notif_user, str(norm.get("content", "")).strip(), str(norm.get("date", "")).strip())
                if sig not in seen_notifs:
                    seen_notifs.add(sig); relevant_notifs.append(norm)

        def parse_date(d_str):
            try: return datetime.strptime(d_str, "%d/%m/%Y %H:%M")
            except: 
                try: return datetime.strptime(d_str, "%d/%m/%Y")
                except: return datetime.min

        relevant_notifs.sort(key=lambda x: parse_date(x.get("date") or x.get("thoiGian") or ""), reverse=True)

        event_colors = {
            "Account Update": {"bg": "#f0fdfa", "border": "#ccfbf1", "tag_bg": "#0d9488", "tag_fg": "#ffffff"},
            "Refund Approved": {"bg": "#f0fdf4", "border": "#bbf7d0", "tag_bg": "#22c55e", "tag_fg": "#ffffff"},
            "Refund Declined": {"bg": "#fef2f2", "border": "#fecaca", "tag_bg": "#ef4444", "tag_fg": "#ffffff"},
            "tour_completed": {"bg": "#eff6ff", "border": "#bfdbfe", "tag_bg": "#3b82f6", "tag_fg": "#ffffff"},
            "booking_created": {"bg": "#faf5ff", "border": "#e9d5ff", "tag_bg": "#a855f7", "tag_fg": "#ffffff"},
            "default": {"bg": "#f8fafc", "border": "#e2e8f0", "tag_bg": "#64748b", "tag_fg": "#ffffff"},
        }
        event_type_translations = {"Account Update": "Cập nhật tài khoản", "Refund Approved": "Hoàn tiền", "Refund Declined": "Từ chối hoàn", "tour_completed": "Hoàn thành", "booking_created": "Đặt tour"}

        def show_notif_detail(n):
            popup = tk.Toplevel(body.winfo_toplevel())
            popup.title("Chi tiết thông báo")
            popup.geometry("600x450"); popup.configure(bg="#ffffff")
            popup.transient(body.winfo_toplevel()); popup.grab_set()

            e_type = n.get("eventType") or "default"
            colors = event_colors.get(e_type, event_colors["default"])
            tk.Frame(popup, height=6, bg=colors["tag_bg"]).pack(fill="x")
            
            pad_frame = tk.Frame(popup, bg="#ffffff", padx=25, pady=20)
            pad_frame.pack(fill="both", expand=True)

            meta = tk.Frame(pad_frame, bg="#ffffff"); meta.pack(fill="x", pady=(0, 15))
            tk.Label(meta, text=event_type_translations.get(e_type, e_type.upper()), bg=colors["tag_bg"], fg=colors["tag_fg"], font=("Times New Roman", 10, "bold"), padx=8, pady=3).pack(side="left")
            tk.Label(meta, text=n.get("date") or n.get("thoiGian") or "", bg="#ffffff", fg="#64748b", font=("Times New Roman", 11)).pack(side="right")

            info = tk.Frame(pad_frame, bg="#f8fafc", bd=1, relief="solid", highlightbackground="#e2e8f0"); info.pack(fill="x", pady=(0, 15))
            info_inner = tk.Frame(info, bg="#f8fafc", padx=12, pady=12); info_inner.pack(fill="both")

            r_idx = 0
            def add_row(lbl, val):
                nonlocal r_idx
                if val:
                    tk.Label(info_inner, text=lbl, font=("Times New Roman", 11, "bold"), bg="#f8fafc").grid(row=r_idx, column=0, sticky="w", pady=2)
                    tk.Label(info_inner, text=val, font=("Times New Roman", 11), bg="#f8fafc").grid(row=r_idx, column=1, sticky="w", pady=2, padx=(10, 0))
                    r_idx += 1

            t_str = f"[{n.get('maTour')}] {n.get('tenTour')}" if n.get('maTour') and n.get('tenTour') else (n.get('maTour') or n.get('tenTour'))
            add_row("Tour:", t_str)
            add_row("Mã BK:", n.get("maBooking"))
            hdv = app["ql"].find_hdv(n.get("maHDV"))
            add_row("HDV:", n.get("tenHDV") or (hdv.get("tenHDV") if hdv else "") or n.get("maHDV"))

            tk.Label(pad_frame, text="Nội dung:", font=("Times New Roman", 12, "bold"), bg="#ffffff").pack(anchor="w", pady=(0, 5))
            txt_container = tk.Frame(pad_frame, bg="#ffffff", bd=1, relief="solid"); txt_container.pack(fill="both", expand=True, pady=(0, 15))
            ct = tk.Text(txt_container, bg="#ffffff", font=("Times New Roman", 12), wrap="word", bd=0, padx=10, pady=10)
            s = ttk.Scrollbar(txt_container, orient="vertical", command=ct.yview); ct.configure(yscrollcommand=s.set)
            ct.pack(side="left", fill="both", expand=True); s.pack(side="right", fill="y")
            ct.insert("1.0", str(n.get("content") or n.get("noiDung") or n.get("thongBao") or "").strip())
            ct.configure(state="disabled")
            ttk.Button(pad_frame, text="Đóng", command=popup.destroy).pack(anchor="e")

        if not relevant_notifs:
            tk.Label(scrollable_frame, text="Bạn chưa có thông báo nào.", bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 13, "italic")).pack(anchor="w", pady=20, padx=10)
        else:
            for n in relevant_notifs:
                colors = event_colors.get(n.get("eventType") or "default", event_colors["default"])
                card = tk.Frame(scrollable_frame, bg=colors["bg"], highlightbackground=colors["border"], highlightthickness=1)
                card.pack(fill="x", pady=8, padx=15)
                inner = tk.Frame(card, bg=colors["bg"], padx=15, pady=12); inner.pack(fill="both", expand=True)

                h_fr = tk.Frame(inner, bg=colors["bg"]); h_fr.pack(fill="x")
                tk.Label(h_fr, text=event_type_translations.get(n.get("eventType") or "default", "Thông báo"), bg=colors["tag_bg"], fg=colors["tag_fg"], font=("Times New Roman", 10, "bold"), padx=6).pack(side="left")
                if n.get("maTour"): tk.Label(h_fr, text=f" Tour: {n.get('maTour')}", font=("Times New Roman", 12, "bold"), bg=colors["bg"], fg=THEME["primary"]).pack(side="left", padx=5)
                tk.Label(h_fr, text=str(n.get("date") or n.get("thoiGian") or ""), font=("Times New Roman", 11), bg=colors["bg"], fg=THEME["muted"]).pack(side="right")

                t_title = n.get("tenTour", "").strip() or n.get("maTour", "").strip()
                if t_title and t_title != n.get("maTour"): tk.Label(inner, text=t_title, font=("Times New Roman", 12, "bold"), bg=colors["bg"]).pack(anchor="w", pady=(5, 2))

                text = str(n.get("content") or n.get("noiDung") or n.get("thongBao") or "").strip()
                msg = tk.Label(inner, text=(text[:147] + "..." if len(text) > 150 else text), font=("Times New Roman", 12), bg=colors["bg"], justify="left", wraplength=700)
                msg.pack(anchor="w", pady=(0, 5))

                for w in [card, inner, h_fr, msg]: w.bind("<Double-1>", lambda e, notif=n: show_notif_detail(notif))

        set_status("Đang ở mục: Thông báo", THEME["primary"])

    def open_view(title, subtitle, current_tab, view_fn, menu_button, badge_text="KHÁCH HÀNG", badge_bg="#dbeafe", badge_fg="#1d4ed8"):
        try:
            from core.app import sync_completed_tour_bookings
            sync_completed_tour_bookings(app["ql"])
        except Exception as e:
            pass

        app["page_title_var"].set(title)
        app["page_subtitle_var"].set(subtitle)
        app["current_tab"] = current_tab
        app["current_view"] = {"title": title, "subtitle": subtitle, "current_tab": current_tab, "view_fn": view_fn, "menu_button": menu_button, "badge_text": badge_text, "badge_bg": badge_bg, "badge_fg": badge_fg}
        set_badge(badge_text, badge_bg, badge_fg)
        set_active_menu(menu_button)
        view_fn()
        set_status(f"Đang ở mục: {title}", THEME["primary"])

    def reload_current_page():
        app["ql"].load()
        cv = app.get("current_view")
        if cv: open_view(cv["title"], cv["subtitle"], cv["current_tab"], cv["view_fn"], cv["menu_button"], cv["badge_text"], cv["badge_bg"], cv["badge_fg"])
        set_status("Đã tải lại dữ liệu", THEME["success"])

    style_button(head_right, "Tải lại", THEME["primary"], reload_current_page).pack(anchor="e")

    nav_buttons, nav_views = [], [
        ("Khám phá Tour", "Xem danh sách tour mở bán và đăng ký nhanh.", "tour", tab_danh_sach_tour, "🗺", "DANH SÁCH TOUR", "#dbeafe", "#1d4ed8"),
        ("Tour đã đặt", "Theo dõi lịch sử booking và trạng thái thanh toán.", "booked", tab_tour_da_dat, "🧾", "BOOKING", "#ede9fe", "#7c3aed"),
        ("Lịch sử booking", "Xem các tour bạn đã hoàn thành.", "history", tab_lich_su_booking, "📜", "LỊCH SỬ", "#e2e8f0", "#475569"),
        ("Thông báo", "Cập nhật thông báo mới nhất từ đoàn và hướng dẫn viên.", "notification", tab_thong_bao, "🔔", "THÔNG BÁO", "#fef3c7", "#d97706"),
        ("Gửi đánh giá", "Góp ý dịch vụ và đánh giá chất lượng hướng dẫn viên.", "review", tab_gui_danh_gia, "⭐", "ĐÁNH GIÁ", "#dcfce7", "#059669"),
        ("Hồ sơ cá nhân", "Quản lý thông tin cá nhân và bảo mật tài khoản.", "profile", tab_ho_so, "👤", "TÀI KHOẢN", "#fee2e2", "#dc2626"),
    ]

    for idx, (title, subtitle, current_tab, view_fn, icon, badge_text, badge_bg, badge_fg) in enumerate(nav_views):
        btn = menu_btn(title, lambda t=title, s=subtitle, c=current_tab, f=view_fn, b_idx=idx, bt=badge_text, bbg=badge_bg, bfg=badge_fg: open_view(t, s, c, f, nav_buttons[b_idx], bt, bbg, bfg), icon=icon)
        btn.pack(fill="x", pady=4); nav_buttons.append(btn)

    def _refresh_menu_button_layout(button):
        if app.get("sidebar_collapsed"): button.configure(text=getattr(button, "_icon", "") or getattr(button, "_full_text", "")[:1].upper(), anchor="center", justify="center", padx=4, pady=12, wraplength=40)
        else: button.configure(text=f"  {getattr(button, '_icon', '')}  {getattr(button, '_full_text', '')}" if getattr(button, "_icon", "") else f"  {getattr(button, '_full_text', '')}", anchor="w", justify="left", padx=14, pady=13, wraplength=210)

    # util and logout_btn are defined earlier to guarantee layout hierarchy


    def apply_sidebar_mode():
        collapsed = app.get("sidebar_collapsed", False)
        sidebar_outer.configure(width=SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_EXPANDED_WIDTH)

        if collapsed:
            brand_title.configure(text="VNT", font=("Times New Roman", 12, "bold"))
            if brand_subtitle.winfo_manager(): brand_subtitle.pack_forget()
            if account_card.winfo_manager(): account_card.pack_forget()
            brand.pack_configure(padx=4)
            collapse_btn.configure(text="\u2630"); util.pack_configure(padx=8, pady=10); menu.pack_configure(padx=8)
            logout_btn.configure(text="🚪", anchor="center", padx=8)
        else:
            brand_title.configure(text="VIETNAM TRAVEL", font=("Times New Roman", 16, "bold"))
            if not brand_subtitle.winfo_manager(): brand_subtitle.pack(fill="x", pady=(2, 0))
            if not account_card.winfo_manager(): account_card.pack(fill="x", padx=16, pady=(0, 8), before=menu)
            brand.pack_configure(padx=18)
            collapse_btn.configure(text="\u2630"); util.pack_configure(padx=12, pady=14); menu.pack_configure(padx=12)
            logout_btn.configure(text="🚪  Đăng xuất", anchor="w", padx=14)

        for btn in nav_buttons: _refresh_menu_button_layout(btn)

    collapse_btn.configure(command=lambda: (app.update({"sidebar_collapsed": not app.get("sidebar_collapsed")}), apply_sidebar_mode()))
    apply_sidebar_mode()

    if nav_buttons: open_view(*nav_views[0][:3], nav_views[0][3], nav_buttons[0], *nav_views[0][5:])


def logout_user(root):
    if messagebox.askyesno("Xác nhận", "Bạn có muốn đăng xuất?"):
        for widget in root.winfo_children(): widget.destroy()
        try:
            from main import TravelSystem
            root.configure(bg=THEME["bg"])
            TravelSystem(root)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể quay lại màn hình đăng nhập.\n{e}")

if __name__ == "__main__":
    win = tk.Tk()
    win.title("Vietnam Travel 2026")
    win.geometry("1240x760")
    win.minsize(1040, 660)
    # Cần tạo hàm mock DataStore hoặc file data.json thì file này mới có thể chạy độc lập
    win.mainloop()