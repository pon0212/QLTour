import os
import re
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from GUI.common.rounded_button import RoundedButton
from GUI.common.weather_popup import open_tour_weather_popup

from core.app import (
    JSONDataStore,
    fix_mojibake,
    normalize_tour_status,
    normalize_notification_item as core_normalize_notification_item,
    normalize_review_item as core_normalize_review_item,
    prepare_password_for_storage,
    is_valid_email as feature_is_valid_email,
    is_valid_password as feature_is_valid_password,
    is_valid_phone as feature_is_valid_phone,
    safe_int as feature_safe_int,
    TOUR_STATUS_CANCELLED,
    TOUR_STATUS_STARTED,
)

# =========================
# VALIDATION
# =========================
def is_valid_phone(phone):
    return feature_is_valid_phone(phone)

def is_valid_email(email):
    return feature_is_valid_email(email)

def is_valid_password(pwd):
    return feature_is_valid_password(pwd)

def safe_int(value):
    return feature_safe_int(value)

# =========================
# THEME
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

HDV_STATUSES = ["Sẵn sàng", "Đã phân công", "Đang dẫn tour", "Tạm nghỉ"]
TOUR_FINISHED_STATUSES = ["Đã kết thúc", "Đã hủy"]
BOOKING_CANCEL_STATUSES = ["Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]

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
            "maHDV": "HDV01",
            "tenHDV": "Nguyễn Văn Anh",
            "sdt": "0901234567",
            "email": "anh@travel.com",
            "kn": "5",
            "gioiTinh": "Nam",
            "khuVuc": "Miền Bắc",
            "trangThai": "Sẵn sàng",
            "password": "123",
            "total_reviews": 0,
            "avg_rating": 0,
            "skill_score": 0,
            "attitude_score": 0,
            "problem_solving_score": 0,
        }
    ],
    "tours": [],
    "bookings": [],
    "users": [],
    "admin": {"username": "admin", "password": "123"},
}


# =========================
# DATA STORE
# =========================
def normalize_review_item(r, datastore=None):
    normalized = core_normalize_review_item(
        r,
        fullname_keys=("fullname", "tenKhach", "hoTen", "tenNguoiDanhGia"),
        content_keys=("content", "comment", "noiDung", "danhGia"),
        include_rating=True,
        include_ma_hdv=True,
    )

    ma_tour = str(normalized.get("maTour", "")).strip()
    ten_tour = str((r or {}).get("tenTour", "")).strip()
    if not ten_tour and datastore is not None and ma_tour:
        tour = datastore.find_tour(ma_tour)
        ten_tour = str((tour or {}).get("ten", "")).strip()
    normalized["tenTour"] = ten_tour

    ma_hdv = str(normalized.get("maHDV", "")).strip()
    ten_hdv = str(normalized.get("tenHDV", "")).strip()
    if not ma_hdv and ma_tour and datastore is not None:
        tour = datastore.find_tour(ma_tour)
        if tour:
            ma_hdv = str(tour.get("hdvPhuTrach", "")).strip()
            normalized["maHDV"] = ma_hdv
            
    if not ma_hdv and datastore is not None and normalized.get("maBooking"):
        bookings_list = getattr(datastore, "list_bookings", getattr(datastore, "data", {}).get("bookings", []))
        booking = next((b for b in bookings_list if str(b.get("maBooking", b.get("ma", ""))).strip().upper() == str(normalized.get("maBooking", "")).strip().upper()), None)
        if booking:
            b_tour = datastore.find_tour(booking.get("maTour"))
            if b_tour:
                ma_hdv = str(b_tour.get("hdvPhuTrach", "")).strip()
                normalized["maHDV"] = ma_hdv
                
    if ma_hdv and not ten_hdv and datastore is not None:
        hdv = datastore.find_hdv(ma_hdv)
        if hdv:
            ten_hdv = str(hdv.get("tenHDV", "")).strip()
            normalized["tenHDV"] = ten_hdv

    return normalized


def normalize_notification_item(n, datastore=None):
    return core_normalize_notification_item(
        n,
        datastore=datastore,
        content_keys=("content", "noiDung", "message", "thongBao"),
    )

def auto_fit_treeview_columns(tree, columns, min_widths=None, max_widths=None, padding=24):
    def estimate_width(text):
        text = "" if text is None else str(text)
        return max(40, len(text) * 8 + padding)

    for col in columns:
        header_text = tree.heading(col)["text"]
        width = estimate_width(header_text)

        for item in tree.get_children():
            cell_value = tree.set(item, col)
            width = max(width, estimate_width(cell_value))

        if min_widths and col in min_widths:
            width = max(width, min_widths[col])
        if max_widths and col in max_widths:
            width = min(width, max_widths[col])

        tree.column(col, width=width)

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
    for idx, item in enumerate(tree.get_children()):
        tree.item(item, tags=(("even" if idx % 2 == 0 else "odd"),))

def style_button(parent, text, bg, command, fg="white"):
    return RoundedButton(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        activebackground=bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Times New Roman", 11, "bold"),
        padx=14,
        pady=9,
        highlightthickness=1,
        highlightbackground=bg,
        highlightcolor=bg,
        command=command,
    )

def configure_ui_fonts(root):
    default_font = ("Times New Roman", 12)
    heading_font = ("Times New Roman", 12, "bold")
    root.option_add("*Font", default_font)
    root.option_add("*Label.Font", default_font)
    root.option_add("*Button.Font", default_font)
    root.option_add("*Entry.Font", default_font)
    root.option_add("*Text.Font", default_font)
    root.option_add("*Spinbox.Font", default_font)
    root.option_add("*TCombobox*Listbox*Font", default_font)

    style = ttk.Style(root)
    style.configure("TLabel", font=default_font)
    style.configure("TButton", font=heading_font)
    style.configure("TEntry", font=default_font)
    style.configure("TCombobox", font=default_font)

def bind_autohide_scrollbar(widget, scrollbar, orient="vertical"):
    """Tự động ẩn/hiện scrollbar khi nội dung có hoặc không tràn khung."""
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
            start = float(first)
            end = float(last)
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

def create_scrollable_frame(parent, bg):
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    content = tk.Frame(canvas, bg=bg)

    content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
    bind_autohide_scrollbar(canvas, scrollbar, "vertical")

    def resize_content(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", resize_content)
    canvas.pack(side="left", fill="both", expand=True)
    return outer, content

def responsive_wraplength(widget, offset=80, min_width=260, fallback=760):
    width = widget.winfo_width()
    if width <= 1:
        return fallback
    return max(min_width, width - offset)


# =========================
# GUIDE UI
# =========================
def khoi_tao_hdv(root, user_data=None):
    if not user_data:
        user_data = {"maHDV": "HDV01", "tenHDV": "Hướng Dẫn Viên"}

    app = {
        "root": root,
        "ql": DataStore(),
        "user": user_data,
        "container": None,
        "content_canvas": None,
        "tv_tours": None,
        "detail_frame": None,
        "active_menu_btn": None,
        "page_title_var": tk.StringVar(value="Lịch trình tour"),
        "page_subtitle_var": tk.StringVar(value="Theo dõi các tour được phân công, danh sách khách và trạng thái vận hành."),
        "status_var": tk.StringVar(value="Sẵn sàng làm việc"),
        "status_label": None,
        "status_badge": None,
        "login_time": datetime.now(),
        "login_time_var": tk.StringVar(),
        "current_tab": "tour",
        "sidebar_collapsed": False,
    }

    app["login_time_var"].set(
        "Đăng nhập lúc: " + app["login_time"].strftime("%d/%m/%Y - %H:%M:%S")
    )

    for widget in root.winfo_children():
        widget.destroy()

    root.title("VIETNAM TRAVEL - HƯỚNG DẪN VIÊN")
    root.geometry("1320x780")
    root.minsize(1120, 700)
    root.configure(bg=THEME["bg"])
    configure_ui_fonts(root)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        font=("Times New Roman", 12),
        rowheight=38,
        background=THEME["surface"],
        fieldbackground=THEME["surface"],
        foreground=THEME["text"],
        bordercolor=THEME["border"],
        relief="flat",
    )
    style.configure(
        "Treeview.Heading",
        font=("Times New Roman", 12, "bold"),
        background=THEME["heading_bg"],
        foreground=THEME["text"],
        relief="flat",
        padding=(8, 10),
    )
    style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", THEME["text"])])
    style.configure(
        "TScrollbar",
        bordercolor="#1e293b",
        troughcolor="#1e293b",
        background="#475569",
        darkcolor="#475569",
        lightcolor="#475569",
        arrowcolor="#1e293b",
        arrowsize=10,
        relief="flat",
        gripcount=0,
    )
    style.layout(
        "Vertical.TScrollbar",
        [
            (
                "Vertical.Scrollbar.trough",
                {
                    "children": [
                        ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
                    ],
                    "sticky": "nswe",
                },
            )
        ],
    )
    style.configure(
        "Vertical.TScrollbar",
        troughcolor="#1e293b",
        background="#475569",
        darkcolor="#475569",
        lightcolor="#475569",
        bordercolor="#1e293b",
        arrowcolor="#1e293b",
        relief="flat",
        arrowsize=11,
        gripcount=0,
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", "#64748b"), ("pressed", "#64748b")],
        darkcolor=[("active", "#64748b"), ("pressed", "#64748b")],
        lightcolor=[("active", "#64748b"), ("pressed", "#64748b")],
    )
    style.layout(
        "Horizontal.TScrollbar",
        [
            (
                "Horizontal.Scrollbar.trough",
                {
                    "children": [
                        ("Horizontal.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
                    ],
                    "sticky": "nswe",
                },
            )
        ],
    )
    style.configure(
        "Horizontal.TScrollbar",
        troughcolor="#1e293b",
        background="#475569",
        darkcolor="#475569",
        lightcolor="#475569",
        bordercolor="#1e293b",
        arrowcolor="#1e293b",
        relief="flat",
        arrowsize=11,
        gripcount=0,
    )
    style.map(
        "Horizontal.TScrollbar",
        background=[("active", "#64748b"), ("pressed", "#64748b")],
        darkcolor=[("active", "#64748b"), ("pressed", "#64748b")],
        lightcolor=[("active", "#64748b"), ("pressed", "#64748b")],
    )

    SIDEBAR_EXPANDED_WIDTH = 300
    SIDEBAR_COLLAPSED_WIDTH = 92
    SIDEBAR_BG = "#020f2a"
    SIDEBAR_CARD_BG = "#0f1e3d"
    SIDEBAR_BORDER = "#2a3e66"
    SIDEBAR_BTN_HOVER = "#102547"
    SIDEBAR_BTN_ACTIVE = "#2563eb"

    sidebar = tk.Frame(root, bg=SIDEBAR_BG, width=SIDEBAR_EXPANDED_WIDTH)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    brand = tk.Frame(sidebar, bg=SIDEBAR_BG)
    brand.pack(fill="x", padx=18, pady=(18, 10))
    brand_top = tk.Frame(brand, bg=SIDEBAR_BG)
    brand_top.pack(fill="x")
    brand_title = tk.Label(
        brand_top,
        text="VIETNAM TRAVEL",
        justify="left",
        anchor="w",
        bg=SIDEBAR_BG,
        fg="#34d399",
        font=("Times New Roman", 21, "bold"),
    )
    brand_title.pack(side="left", fill="x", expand=True)
    collapse_btn = RoundedButton(
        brand_top,
        text="\u2630",
        bg=SIDEBAR_BG,
        fg="#dbeafe",
        activebackground=SIDEBAR_BTN_ACTIVE,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Times New Roman", 12, "bold"),
        padx=8,
        pady=3,
    )
    collapse_btn.pack(side="right")
    collapse_btn.bind("<Enter>", lambda _e: collapse_btn.configure(bg=SIDEBAR_BG))
    collapse_btn.bind("<Leave>", lambda _e: collapse_btn.configure(bg=SIDEBAR_BG))
    brand_subtitle = tk.Label(
        brand,
        text="Guide Control Center",
        justify="left",
        anchor="w",
        bg=SIDEBAR_BG,
        fg="#93c5fd",
        font=("Times New Roman", 11, "italic"),
    )
    brand_subtitle.pack(fill="x", pady=(2, 0))

    ten_hdv = user_data.get("tenHDV", "Hướng Dẫn Viên")
    ma_hdv = user_data.get("maHDV", "HDV01")
    account_card = tk.Frame(sidebar, bg=SIDEBAR_CARD_BG, highlightbackground=SIDEBAR_BORDER, highlightthickness=1)
    account_card.pack(fill="x", padx=16, pady=(0, 8))

    tk.Label(
        account_card,
        text="TÀI KHOẢN HƯỚNG DẪN VIÊN",
        bg=SIDEBAR_CARD_BG,
        fg="#dbeafe",
        font=("Times New Roman", 11, "bold"),
    ).pack(fill="x")

    tk.Label(
        account_card,
        text=f"{ten_hdv}",
        bg=SIDEBAR_CARD_BG,
        fg="white",
        font=("Times New Roman", 13, "bold"),
        pady=6,
    ).pack(fill="x")

    tk.Label(
        account_card,
        text=f"Mã HDV: {user_data.get('maHDV', '')}",
        bg=SIDEBAR_CARD_BG,
        fg="#93c5fd",
        font=("Times New Roman", 10, "italic"),
    ).pack(fill="x")

    tk.Label(
        account_card,
        text=f"Đang hoạt động",
        bg=SIDEBAR_CARD_BG,
        fg="#22c55e",
        font=("Times New Roman", 10, "bold"),
    ).pack(pady=(4, 0))

    menu = tk.Frame(sidebar, bg=SIDEBAR_BG)
    menu.pack(fill="x", padx=12, pady=(2, 0))

    def reload_current_page():
        app["ql"].load()
        current_tab = app.get("current_tab", "tour")

        if current_tab == "tour":
            tab_danh_sach_tour()
            set_status("Đã tải lại dữ liệu lịch trình tour", THEME["success"])
        elif current_tab == "stats":
            tab_thong_ke()
            set_status("Đã tải lại dữ liệu hiệu suất", THEME["success"])
        elif current_tab == "notify":
            tab_thong_bao()
            set_status("Đã tải lại dữ liệu thông báo", THEME["success"])
        elif current_tab == "settings":
            tab_cai_dat()
            set_status("Đã tải lại dữ liệu tài khoản", THEME["success"])
        else:
            tab_danh_sach_tour()
            set_status("Đã tải lại dữ liệu", THEME["success"])

    def set_status(text, color=THEME["primary"]):
        app["status_var"].set(text)
        if app.get("status_label"):
            app["status_label"].config(fg=color)

    def set_badge(text, bg="#123a5a", fg="#d1fae5"):
        if app.get("status_badge"):
            app["status_badge"].config(text=text, bg=bg, fg=fg)

    def set_active_menu(button):
        prev = app.get("active_menu_btn")
        if prev and prev.winfo_exists() and prev is not button:
            prev.configure(bg=SIDEBAR_BG, fg="#dbe4f5")
        app["active_menu_btn"] = button
        button.configure(bg=SIDEBAR_BTN_ACTIVE, fg="white")

    def menu_btn(text, cmd, icon=""):
        label = f"  {icon}  {text}" if icon else f"  {text}"
        btn = RoundedButton(
            menu,
            text=label,
            bg=SIDEBAR_BG,
            fg="#dbe4f5",
            activebackground=SIDEBAR_BTN_ACTIVE,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            anchor="w",
            justify="left",
            wraplength=210,
            font=("Times New Roman", 13, "bold"),
            padx=14,
            pady=13,
            command=cmd,
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

    right_panel = tk.Frame(root, bg=THEME["bg"])
    right_panel.pack(side="left", fill="both", expand=True)

    header = tk.Frame(
        right_panel,
        bg=THEME["header_bg"],
        height=96,
        highlightbackground=THEME["border"],
        highlightthickness=1,
    )
    header.pack(side="top", fill="x", padx=18, pady=(18, 12))
    header.pack_propagate(False)

    head_left = tk.Frame(header, bg=THEME["header_bg"])
    head_left.pack(side="left", fill="both", expand=True, padx=18, pady=12)
    tk.Label(
        head_left,
        textvariable=app["page_title_var"],
        bg=THEME["header_bg"],
        fg=THEME["text"],
        font=("Times New Roman", 24, "bold"),
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        head_left,
        textvariable=app["page_subtitle_var"],
        bg=THEME["header_bg"],
        fg=THEME["muted"],
        font=("Times New Roman", 12, "italic"),
        anchor="w",
        wraplength=760,
        justify="left",
    ).pack(anchor="w", pady=(3, 0))

    head_right = tk.Frame(header, bg=THEME["header_bg"])
    head_right.pack(side="right", padx=18, pady=16)
    tk.Label(
        head_right,
        text="Trạng thái hôm nay",
        bg=THEME["header_bg"],
        fg=THEME["muted"],
        font=("Times New Roman", 10, "bold"),
    ).pack(anchor="e")
    header_badge = tk.Label(
        head_right,
        text="SẴN SÀNG DẪN TOUR",
        bg="#dbeafe",
        fg="#1d4ed8",
        font=("Times New Roman", 11, "bold"),
        padx=14,
        pady=7,
    )
    header_badge.pack(anchor="e", pady=(6, 0))

    style_button(
        head_right,
        "↻ Tải lại",
        THEME["primary"],
        reload_current_page
    ).pack(anchor="e")

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

    status_bar = tk.Frame(
        right_panel,
        bg=THEME["status_bg"],
        height=36,
        highlightbackground=THEME["border"],
        highlightthickness=1,
    )
    status_bar.pack(side="bottom", fill="x", padx=18, pady=(0, 16))
    status_bar.pack_propagate(False)
    app["status_label"] = tk.Label(
        status_bar,
        textvariable=app["status_var"],
        bg=THEME["status_bg"],
        fg=THEME["primary"],
        anchor="w",
        padx=14,
        font=("Times New Roman", 11, "italic"),
    )
    app["status_label"].pack(fill="both", expand=True)

    def clear_container():
        for widget in content_area.winfo_children():
            widget.destroy()
        if app.get("content_canvas"):
            app["content_canvas"].yview_moveto(0)

    def get_my_tours():
        rows = []
        for t in app["ql"].list_tours:
            if t.get("hdvPhuTrach") != ma_hdv:
                continue
            if normalize_tour_status(t.get("trangThai", "")) == TOUR_STATUS_CANCELLED:
                continue
            rows.append(t)
        return rows

    def get_active_tours():
        return [t for t in get_my_tours() if normalize_tour_status(t.get("trangThai", "")) == TOUR_STATUS_STARTED]

    def format_currency(value):
        return f"{safe_int(value):,} đ".replace(",", ".")

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

    def info_pair(parent, left_items, right_items, bg):
        left = tk.Frame(parent, bg=bg)
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))
        right = tk.Frame(parent, bg=bg)
        right.pack(side="left", fill="both", expand=True)

        for label_text, value in left_items:
            row = tk.Frame(left, bg=bg)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{label_text}:", width=16, anchor="w", bg=bg, fg=THEME["text"], font=("Times New Roman", 12, "bold")).pack(side="left")
            tk.Label(row, text=str(value), anchor="w", bg=bg, fg=THEME["text"], font=("Times New Roman", 12)).pack(side="left", fill="x", expand=True)

        for label_text, value in right_items:
            row = tk.Frame(right, bg=bg)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{label_text}:", width=16, anchor="w", bg=bg, fg=THEME["text"], font=("Times New Roman", 12, "bold")).pack(side="left")
            tk.Label(row, text=str(value), anchor="w", bg=bg, fg=THEME["text"], font=("Times New Roman", 12), wraplength=360, justify="left").pack(side="left", fill="x", expand=True)

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

    def hien_thi_chi_tiet(event=None):
        sel = app["tv_tours"].selection()
        if not sel:
            return

        ma_tour = app["tv_tours"].item(sel[0])["values"][0]
        tour = app["ql"].find_tour(ma_tour)
        bookings = app["ql"].get_bookings_by_tour(ma_tour)

        for w in app["detail_frame"].winfo_children():
            w.destroy()

        if not tour:
            tk.Label(app["detail_frame"], text="Không tìm thấy dữ liệu tour.", font=("Times New Roman", 13), bg=THEME["bg"], fg=THEME["danger"]).pack(pady=20)
            return

        occupied = app["ql"].get_occupied_seats(ma_tour)
        paid_total = sum(safe_int(b.get("daThanhToan", 0)) for b in bookings)
        remaining_total = sum(safe_int(b.get("conNo", 0)) for b in bookings)

        _, overview_body = make_section(
            app["detail_frame"],
            f"Chi tiết tour {tour.get('ma', '')}",
            "Toàn bộ thông tin điều hành, lịch trình và trạng thái khách theo tour đang chọn.",
            accent="#2563eb",
        )

        info_pair(
            overview_body,
            [
                ("Tên tour", tour.get("ten", "")),
                ("Khởi hành", tour.get("ngay", "")),
                ("Kết thúc", tour.get("ngayKetThuc", "")),
                ("Số ngày", tour.get("soNgay", "")),
                ("Điểm đi", tour.get("diemDi", "")),
            ],
            [
                ("Điểm đến", tour.get("diemDen", "")),
                ("Trạng thái", normalize_tour_status(tour.get("trangThai", ""))),
                ("Sức chứa", tour.get("khach", "")),
                ("Đã đặt", occupied),
                ("Ghi chú", tour.get("ghiChuDieuHanh", "Không có") or "Không có"),
            ],
            THEME["surface"],
        )

        lich_trinh = tour.get("lichTrinh", [])
        if isinstance(lich_trinh, list) and lich_trinh:
            itinerary_lines = []
            for item in lich_trinh:
                if not isinstance(item, dict):
                    continue
                ngay = str(item.get("ngay", "")).strip()
                tieu_de = str(item.get("tieuDe", "")).strip()
                dia_diem = item.get("diaDiem", [])
                if isinstance(dia_diem, str):
                    dia_diem = [p.strip() for p in dia_diem.split(",") if p.strip()]
                mo_ta = str(item.get("moTa", "")).strip()
                itinerary_lines.append(f"- {ngay} {tieu_de}".strip())
                if dia_diem:
                    itinerary_lines.append(f"  Điểm đến: {', '.join(dia_diem)}")
                if mo_ta:
                    itinerary_lines.append(f"  {mo_ta}")
            if itinerary_lines:
                _, itinerary_body = make_section(app["detail_frame"], "Lịch trình tour", "Chi tiết các điểm tham quan theo từng ngày.", accent="#7c3aed")
                
                itinerary_wrapper = tk.Frame(itinerary_body, bg=THEME["surface"])
                itinerary_wrapper.pack(fill="x", pady=(0, 8))
                
                itinerary_text = tk.Text(
                    itinerary_wrapper,
                    height=9,
                    font=("Times New Roman", 12),
                    wrap="word",
                    relief="flat",
                    bg=THEME["surface"],
                    fg=THEME["text"]
                )
                itinerary_sb = ttk.Scrollbar(itinerary_wrapper, orient="vertical", command=itinerary_text.yview)
                itinerary_text.configure(yscrollcommand=itinerary_sb.set)
                
                bind_autohide_scrollbar(itinerary_text, itinerary_sb, "vertical")
                
                itinerary_text.pack(side="left", fill="both", expand=True)
                itinerary_text.insert("1.0", "\n".join(itinerary_lines))
                itinerary_text.configure(state="disabled")

        stats_wrap = tk.Frame(app["detail_frame"], bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))
        build_stat_card(stats_wrap, "Booking hiệu lực", str(len([b for b in bookings if b.get("trangThai") not in BOOKING_CANCEL_STATUSES])), "Số booking còn hiệu lực trên tour này.", THEME["primary"])
        build_stat_card(stats_wrap, "Doanh thu đã thu", format_currency(paid_total), "Tổng tiền khách đã thanh toán cho tour.", THEME["success"])
        build_stat_card(stats_wrap, "Công nợ còn lại", format_currency(remaining_total), "Khoản cần tiếp tục theo dõi trước ngày khởi hành.", THEME["warning"])

        _, booking_body = make_section(
            app["detail_frame"],
            "👥 Danh sách booking / khách hàng",
            "Theo dõi khách theo từng booking để chủ động chuẩn bị danh sách đoàn và hỗ trợ khi cần.",
            accent="#059669",
        )

        wrapper = tk.Frame(booking_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        wrapper.pack(fill="both", expand=True)
        wrapper.pack_propagate(False)
        wrapper.configure(height=250)

        cols = ("stt", "ten", "sdt", "sl", "tt", "thanhtoan")
        tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=7)

        headings = {
            "stt": "STT",
            "ten": "Tên khách hàng",
            "sdt": "Số điện thoại",
            "sl": "Số người",
            "tt": "Trạng thái",
            "thanhtoan": "Đã thanh toán",
        }
        for col, title in headings.items():
            tv.heading(col, text=title)

        tv.column("stt", width=60, minwidth=48, anchor="center", stretch=True)
        tv.column("ten", width=260, minwidth=170, anchor="w", stretch=True)
        tv.column("sdt", width=130, minwidth=100, anchor="center", stretch=True)
        tv.column("sl", width=90, minwidth=76, anchor="center", stretch=True)
        tv.column("tt", width=170, minwidth=120, anchor="center", stretch=True)
        tv.column("thanhtoan", width=150, minwidth=110, anchor="center", stretch=True)

        active_bookings = [b for b in bookings if b.get("trangThai") not in BOOKING_CANCEL_STATUSES]
        rows = active_bookings if active_bookings else bookings

        for i, b in enumerate(rows, 1):
            tv.insert(
                "",
                "end",
                values=(
                    i,
                    b.get("tenKhach", ""),
                    b.get("sdt", ""),
                    b.get("soNguoi", ""),
                    b.get("trangThai", ""),
                    format_currency(b.get("daThanhToan", 0)),
                ),
            )

        if not rows:
            tv.insert("", "end", values=("", "Chưa có booking nào cho tour này", "", "", "", ""))

        apply_zebra(tv)
        sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
        bind_autohide_scrollbar(tv, sy, "vertical")
        tv.pack(side="left", fill="both", expand=True)

        def fit_booking_columns(event=None):
            width = max(520, wrapper.winfo_width() - 20)
            ratios = {"stt": 0.08, "ten": 0.32, "sdt": 0.16, "sl": 0.10, "tt": 0.19, "thanhtoan": 0.15}
            mins = {"stt": 48, "ten": 170, "sdt": 100, "sl": 76, "tt": 120, "thanhtoan": 110}
            for col in cols:
                tv.column(col, width=max(mins[col], int(width * ratios[col])))

        wrapper.bind("<Configure>", fit_booking_columns)
        fit_booking_columns()

        set_status(f"Đang xem chi tiết tour {ma_tour}", THEME["primary"])

    def tab_danh_sach_tour():
        clear_container()

        my_tours = get_my_tours()
        active_tours = get_active_tours()
        total_guests = sum(app["ql"].get_occupied_seats(t["ma"]) for t in my_tours)
        total_notifications = len([n for n in app["ql"].list_notifications if n.get("maHDV") == ma_hdv])

        stats_wrap = tk.Frame(content_area, bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))
        build_stat_card(stats_wrap, "Tour được phân công", str(len(my_tours)), "Tổng số tour HDV đang phụ trách trong hệ thống.", THEME["primary"])
        build_stat_card(stats_wrap, "Tour đang hoạt động", str(len(active_tours)), "Tour chưa kết thúc hoặc chưa bị hủy.", THEME["success"])
        build_stat_card(stats_wrap, "Tổng khách đang theo", str(total_guests), "Số khách hiện đang nằm trong các tour được phân công.", THEME["warning"])
        build_stat_card(stats_wrap, "Thông báo đã gửi", str(total_notifications), "Thông báo đã gửi cho các đoàn trong kỳ hiện tại.", "#7c3aed")

        _, table_body = make_section(
            content_area,
            "Danh sách tour được phân công",
            "Chọn một tour để xem nhanh lịch trình, trạng thái đoàn và danh sách khách hàng theo booking.",
            accent="#1d4ed8",
        )

        wrapper = tk.Frame(table_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        wrapper.pack(fill="x")

        cols = ("ma", "ten", "ngay", "khach", "tt")
        tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=8)
        app["tv_tours"] = tv

        tv.heading("ma", text="Mã tour")
        tv.heading("ten", text="Tên tour")
        tv.heading("ngay", text="Ngày khởi hành")
        tv.heading("khach", text="Đã đặt / Tổng")
        tv.heading("tt", text="Trạng thái")

        tv.column("ma", width=90, minwidth=78, anchor="center", stretch=True)
        tv.column("ten", width=380, minwidth=240, anchor="w", stretch=True)
        tv.column("ngay", width=150, minwidth=110, anchor="center", stretch=True)
        tv.column("khach", width=140, minwidth=100, anchor="center", stretch=True)
        tv.column("tt", width=150, minwidth=110, anchor="center", stretch=True)

        for t in my_tours:
            occupied = app["ql"].get_occupied_seats(t["ma"])
            tv.insert("", "end", values=(t["ma"], t["ten"], t["ngay"], f"{occupied}/{t['khach']}", normalize_tour_status(t.get("trangThai", ""))))

        apply_zebra(tv)
        sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
        bind_autohide_scrollbar(tv, sy, "vertical")
        tv.pack(side="left", fill="both", expand=True)

        def fit_tour_columns(event=None):
            width = max(560, wrapper.winfo_width() - 20)
            ratios = {"ma": 0.10, "ten": 0.44, "ngay": 0.18, "khach": 0.14, "tt": 0.14}
            mins = {"ma": 78, "ten": 240, "ngay": 110, "khach": 100, "tt": 110}
            for col in cols:
                tv.column(col, width=max(mins[col], int(width * ratios[col])))

        wrapper.bind("<Configure>", fit_tour_columns)
        fit_tour_columns()

        tv.bind("<<TreeviewSelect>>", hien_thi_chi_tiet)
        
        def on_tour_double_click(event):
            """Double-click vào tour để xem thời tiết."""
            sel = tv.selection()
            if not sel:
                return
            ma = tv.item(sel[0])["values"][0]
            tour = app["ql"].find_tour(ma)
            if tour:
                open_tour_weather_popup(app["root"], tour, app["ql"])
        
        tv.bind("<Double-1>", on_tour_double_click)

        app["detail_frame"] = tk.Frame(content_area, bg=THEME["bg"])
        app["detail_frame"].pack(fill="both", expand=True, pady=(2, 0))
        app["current_tab"] = "settings"

        if my_tours:
            first = tv.get_children()
            if first:
                tv.selection_set(first[0])
                tv.focus(first[0])
                hien_thi_chi_tiet()
        else:
            _, empty_body = make_section(
                app["detail_frame"],
                "Chưa có tour được phân công",
                "Khi admin gán tour cho bạn, danh sách tour và khách hàng sẽ hiển thị tại đây.",
                accent="#dc2626",
            )
            tk.Label(empty_body, text="Hiện tại bạn chưa có tour nào được phân công.", font=("Times New Roman", 13), bg=THEME["surface"], fg=THEME["muted"]).pack(anchor="w")

    def tab_thong_ke():
        clear_container()
        app["current_tab"] = "stats"
        app["ql"].load()

        # 1. Lọc đánh giá đúng HDV đang đăng nhập
        my_reviews = []
        for r in app["ql"].list_reviews:
            review_status = str(r.get("trangThai", "")).strip().lower()
            if bool(r.get("hidden")) or review_status in {"hidden", "deleted", "archived", "đã ẩn", "da an", "đã xóa", "da xoa"}:
                continue
            target = str(r.get("target", "")).strip().lower()
            if target not in {"hdv", "guide"}:
                continue
            ma_hdv_r = str(r.get("maHDV", "")).strip().upper()
            target_id_r = str(r.get("target_id", "")).strip().upper()
            if ma_hdv_r == ma_hdv.upper() or target_id_r == ma_hdv.upper():
                my_reviews.append(r)

        # Đánh số REVxxx tự động nếu thiếu
        for idx, r in enumerate(my_reviews, 1):
            if not r.get("maReview"):
                r["maReview"] = f"REV{idx:03d}"

        # Tính toán thống kê chi tiết từ review thực tế
        valid_ratings = []
        for r in my_reviews:
            val = r.get("rating")
            if val == "":
                skill = safe_int(r.get("skill", 0))
                attitude = safe_int(r.get("attitude", 0))
                problem = safe_int(r.get("problem", r.get("problem_solving", 0)))
                scores_temp = [x for x in [skill, attitude, problem] if x > 0]
                rating_num = round(sum(scores_temp) / len(scores_temp) / 20, 1) if scores_temp else 5.0
            else:
                try:
                    rating_num = float(val)
                except (TypeError, ValueError):
                    rating_num = 5.0
            if 1 <= rating_num <= 5:
                valid_ratings.append(rating_num)

        total_reviews = len(my_reviews)
        avg_rating = round(sum(valid_ratings) / len(valid_ratings), 1) if valid_ratings else 0.0

        # Đồng bộ thống kê HDV và lưu file
        h = app["ql"].find_hdv(ma_hdv)
        if h:
            h["total_reviews"] = total_reviews
            h["avg_rating"] = avg_rating
            app["ql"].save()
        else:
            h = {
                "avg_rating": avg_rating,
                "total_reviews": total_reviews,
                "skill_score": 0.0,
                "attitude_score": 0.0,
                "problem_solving_score": 0.0,
                "tenHDV": ten_hdv,
                "maHDV": ma_hdv
            }

        # 2. Tiêu đề & Thống kê nhanh - Phiên bản cải tiến
        _, top_body = make_section(
            content_area,
            "Hiệu suất & đánh giá của khách hàng",
            f"Theo dõi phản hồi, mức độ hài lòng và năng lực chuyên môn của hướng dẫn viên {ten_hdv} ({ma_hdv}).",
            accent="#7c3aed",
        )

        stats_container = tk.Frame(top_body, bg=THEME["surface"])
        stats_container.pack(fill="x", pady=(0, 15))
        
        my_tours = get_my_tours()
        total_assigned_tours = len(my_tours)
        completed_tours_count = sum(1 for t in my_tours if t.get("trangThai") in {"Đã kết thúc", "Đã hoàn thành", "Completed"})
        satisfaction_rate = f"{avg_rating * 20:.0f}%" if total_reviews > 0 else "0%"
        
        stats_data = [
            ("Tổng tour đã dẫn", f"{total_assigned_tours} tour", "Tổng số tour được phân công phụ trách", THEME["primary"], 0, 0),
            ("Tour đã hoàn thành", f"{completed_tours_count} tour", "Tour đã kết thúc tốt đẹp", THEME["success"], 0, 1),
            ("Tổng số đánh giá", f"{total_reviews} lượt", "Số phản hồi thực tế nhận được", "#7c3aed", 0, 2),
            ("Điểm trung bình", f"{avg_rating:.1f} / 5.0 ⭐", "Đánh giá chất lượng trung bình", THEME["warning"], 1, 0),
            ("Tỷ lệ hài lòng", satisfaction_rate, "Mức độ hài lòng của khách hàng", "#0ea5e9", 1, 1),
            ("Cập nhật mới nhất", datetime.now().strftime("%d/%m/%Y %H:%M"), "Thời gian thống kê tự động", THEME["muted"], 1, 2),
        ]
        
        for c in range(3):
            stats_container.grid_columnconfigure(c, weight=1)
            
        for title, value, subtitle, color, row, col in stats_data:
            card = tk.Frame(stats_container, bg="#ffffff", highlightbackground="#cbd5e1", highlightthickness=1)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            
            accent = tk.Frame(card, bg=color, width=4)
            accent.pack(side="left", fill="y")
            
            info_frame = tk.Frame(card, bg="#ffffff", padx=12, pady=10)
            info_frame.pack(side="left", fill="both", expand=True)
            
            tk.Label(info_frame, text=title, font=("Times New Roman", 10, "bold"), bg="#ffffff", fg=THEME["muted"], anchor="w").pack(fill="x")
            
            val_lbl = tk.Label(info_frame, text=value, font=("Times New Roman", 14, "bold"), bg="#ffffff", fg=color, anchor="w")
            val_lbl.pack(fill="x", pady=(2, 2))
            
            tk.Label(info_frame, text=subtitle, font=("Times New Roman", 9, "italic"), bg="#ffffff", fg=THEME["muted"], anchor="w").pack(fill="x")

        _, chart_body = make_section(
            content_area,
            "Chỉ số đánh giá chuyên môn (%)",
            "Ba tiêu chí quan trọng phản ánh chất lượng dẫn đoàn và xử lý tình huống thực tế.",
            accent="#059669",
        )

        progress_container = tk.Frame(chart_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1, padx=20, pady=15)
        progress_container.pack(fill="x", pady=(0, 10))

        criteria = [
            ("Kiến thức chuyên môn", h.get("skill_score", 0), THEME["primary"], "💡"),
            ("Thái độ phục vụ", h.get("attitude_score", 0), THEME["success"], "😊"),
            ("Xử lý tình huống", h.get("problem_solving_score", 0), THEME["warning"], "🔧"),
        ]

        for icon, name, val, color in [(c[3], c[0], c[1], c[2]) for c in criteria]:
            criteria_frame = tk.Frame(progress_container, bg=THEME["surface"])
            criteria_frame.pack(fill="x", pady=8)
            
            header_frame = tk.Frame(criteria_frame, bg=THEME["surface"])
            header_frame.pack(fill="x", pady=(0, 6))
            
            tk.Label(
                header_frame, 
                text=f"{icon} {name}", 
                font=("Times New Roman", 12, "bold"), 
                anchor="w", 
                bg=THEME["surface"], 
                fg=THEME["text"]
            ).pack(side="left")
            
            tk.Label(
                header_frame,
                text=f"{float(val):.1f}%",
                font=("Times New Roman", 12, "bold"),
                bg=THEME["surface"],
                fg=color
            ).pack(side="right")
            
            progress_bg = tk.Frame(criteria_frame, bg="#e2e8f0", height=24, relief="flat", bd=0)
            progress_bg.pack(fill="x")
            progress_bg.pack_propagate(False)
            
            fill_percent = max(0, min(100, float(val)))
            if fill_percent > 0:
                fill_frame = tk.Frame(progress_bg, bg=color, height=24)
                fill_frame.place(x=0, y=0, relwidth=fill_percent/100, relheight=1)
                
                if fill_percent > 15:
                    tk.Label(
                        fill_frame,
                        text=f"{fill_percent:.1f}%",
                        font=("Times New Roman", 10, "bold"),
                        bg=color,
                        fg="white"
                    ).place(relx=0.95, rely=0.5, anchor="e")
        
        note_frame = tk.Frame(chart_body, bg="#fffbeb", highlightbackground="#fcd34d", highlightthickness=1, padx=12, pady=10)
        note_frame.pack(fill="x", pady=(5, 10))
        
        tk.Label(
            note_frame,
            text="💡 Lưu ý: Các chỉ số này được tính toán tự động dựa trên đánh giá chi tiết từ khách hàng.",
            font=("Times New Roman", 10, "italic"),
            bg="#fffbeb",
            fg="#92400e",
            justify="left"
        ).pack(anchor="w")

        # 3. Giao diện danh sách đánh giá
        _, review_body = make_section(
            content_area,
            "Đánh giá từ khách hàng",
            "Danh sách phản hồi khách hàng dành cho hướng dẫn viên trong các tour đã hoàn tất.",
            accent="#7c3aed",
        )

        if not my_reviews:
            tk.Label(review_body, text="Chưa có đánh giá nào.", font=("Times New Roman", 13, "italic"), bg=THEME["surface"], fg=THEME["muted"]).pack(pady=40)
            set_status("Đang ở Đánh giá khách hàng - Hiển thị 0 đánh giá", THEME["primary"])
            return

        review_canvas_frame = tk.Frame(review_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        review_canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(review_canvas_frame, bg=THEME["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(review_canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollable_frame = tk.Frame(canvas, bg=THEME["bg"])
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Hỗ trợ cuộn chuột
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        review_canvas_frame.bind("<Destroy>", _unbind_mousewheel)

        def show_review_detail(r):
            fullname_d = str(r.get("fullname") or r.get("tenKhach") or r.get("hoTen") or r.get("tenNguoiDanhGia") or "").strip()
            username_d = str(r.get("username") or r.get("user") or "").strip()
            ma_booking_d = str(r.get("maBooking") or r.get("soBooking") or "").strip()
            ma_tour_d = str(r.get("maTour") or "").strip()
            tour_d = app["ql"].find_tour(ma_tour_d)
            ten_tour_d = str(tour_d.get("ten", "")).strip() if tour_d else ""
            
            rating_val_d = r.get("rating", "")
            if rating_val_d == "":
                skill = safe_int(r.get("skill", 0))
                attitude = safe_int(r.get("attitude", 0))
                problem = safe_int(r.get("problem", r.get("problem_solving", 0)))
                scores_temp = [x for x in [skill, attitude, problem] if x > 0]
                rating_val_d = round(sum(scores_temp) / len(scores_temp) / 20, 1) if scores_temp else 5.0
            else:
                try:
                    rating_val_d = float(rating_val_d)
                except ValueError:
                    rating_val_d = 5.0

            review_content_d = str(r.get("content") or r.get("comment") or r.get("noiDung") or r.get("danhGia") or "").strip()
            review_date_d = str(r.get("date") or r.get("ngayGui") or r.get("thoiGian") or r.get("ngay") or "").strip()

            popup = tk.Toplevel(root)
            popup.title("Chi tiết đánh giá khách hàng")
            popup.geometry("900x600")
            popup.minsize(800, 500)
            popup.configure(bg=THEME["bg"])
            popup.grab_set()

            popup.update_idletasks()
            x = (popup.winfo_screenwidth() - popup.winfo_reqwidth()) // 2
            y = (popup.winfo_screenheight() - popup.winfo_reqheight()) // 2
            popup.geometry(f"+{x-100}+{y-100}")

            pop_sect, pop_body = make_section(
                popup,
                "Chi tiết đánh giá khách hàng",
                f"Đánh giá mã: {r.get('maReview', '-')}",
                accent="#7c3aed"
            )
            pop_sect.pack(fill="both", expand=True, padx=20, pady=20)

            grid_fr = tk.Frame(pop_body, bg=THEME["surface"])
            grid_fr.pack(fill="x", pady=(0, 15))

            details = [
                ("Mã đánh giá", r.get("maReview", "-")),
                ("Khách hàng", f"{fullname_d} ({username_d})" if username_d else fullname_d),
                ("Mã booking", ma_booking_d),
                ("Mã tour", ma_tour_d),
                ("Tên tour", ten_tour_d or "Không tìm thấy"),
                ("Mã HDV", ma_hdv),
                ("Tên HDV", ten_hdv),
                ("Điểm đánh giá", f"{rating_val_d:.1f} / 5.0"),
                ("Ngày gửi", review_date_d),
            ]

            for idx, (lbl, val) in enumerate(details):
                row_idx = idx // 2
                col_idx = (idx % 2) * 2
                tk.Label(grid_fr, text=f"{lbl}:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg=THEME["muted"]).grid(row=row_idx, column=col_idx, sticky="w", padx=(10, 5), pady=6)
                tk.Label(grid_fr, text=val, font=("Times New Roman", 12), bg=THEME["surface"], fg=THEME["text"]).grid(row=row_idx, column=col_idx+1, sticky="w", padx=(0, 20), pady=6)

            tk.Label(pop_body, text="Nội dung đánh giá đầy đủ:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg=THEME["primary"]).pack(anchor="w", pady=(10, 5))
            
            txt_fr = tk.Frame(pop_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
            txt_fr.pack(fill="both", expand=True, pady=(0, 20))
            
            txt_area = tk.Text(txt_fr, font=("Times New Roman", 12), bg="#f8fafc", wrap="word", bd=0)
            txt_area.insert("1.0", review_content_d)
            txt_area.config(state="disabled")
            
            pop_sy = ttk.Scrollbar(txt_fr, orient="vertical", command=txt_area.yview)
            txt_area.configure(yscrollcommand=pop_sy.set)
            pop_sy.pack(side="right", fill="y")
            txt_area.pack(side="left", fill="both", expand=True, padx=10, pady=10)

            style_button(pop_body, "Đóng cửa sổ", THEME["primary"], popup.destroy).pack(anchor="center")

        def bind_double_click(widget, callback):
            widget.bind("<Double-1>", callback)
            for child in widget.winfo_children():
                bind_double_click(child, callback)

        for r in my_reviews:
            fullname = str(r.get("fullname") or r.get("tenKhach") or r.get("hoTen") or r.get("tenNguoiDanhGia") or "").strip()
            username = str(r.get("username") or r.get("user") or "").strip()
            if fullname and username:
                customer_text = f"{fullname} ({username})"
            elif fullname:
                customer_text = fullname
            elif username:
                customer_text = username
            else:
                customer_text = "Ẩn danh"

            ma_tour = str(r.get("maTour") or "").strip()
            tour = app["ql"].find_tour(ma_tour)
            ten_tour = str(tour.get("ten", "")).strip() if tour else ""
            tour_text = f"{ma_tour} - {ten_tour}" if ten_tour else ma_tour
            if not tour_text:
                tour_text = "Không xác định"

            rating_value = r.get("rating", "")
            if rating_value == "":
                skill = safe_int(r.get("skill", 0))
                attitude = safe_int(r.get("attitude", 0))
                problem = safe_int(r.get("problem", r.get("problem_solving", 0)))
                scores_temp = [x for x in [skill, attitude, problem] if x > 0]
                rating_value = round(sum(scores_temp) / len(scores_temp) / 20, 1) if scores_temp else 5.0
            else:
                try:
                    rating_value = float(rating_value)
                except ValueError:
                    rating_value = 5.0

            stars = "⭐" * int(round(rating_value))
            rating_text = f"{stars}  {rating_value:.1f} / 5.0"
            review_date = str(r.get("date") or r.get("ngayGui") or r.get("thoiGian") or r.get("ngay") or "Chưa rõ").strip()
            review_content = str(r.get("content") or r.get("comment") or r.get("noiDung") or r.get("danhGia") or "").strip()

            # Card
            card = tk.Frame(scrollable_frame, bg="#ffffff", highlightbackground="#e2e8f0", highlightthickness=1, padx=14, pady=12)
            card.pack(fill="x", padx=10, pady=6)

            # Hàng 1: Tên khách hàng & Rating
            row1 = tk.Frame(card, bg="#ffffff")
            row1.pack(fill="x", pady=(0, 4))
            tk.Label(row1, text=customer_text, font=("Times New Roman", 11, "bold"), fg=THEME["text"], bg="#ffffff").pack(side="left")
            tk.Label(row1, text=rating_text, font=("Times New Roman", 11, "bold"), fg="#eab308", bg="#ffffff").pack(side="right")

            # Hàng 2: Tên tour & Ngày
            row2 = tk.Frame(card, bg="#ffffff")
            row2.pack(fill="x", pady=(0, 8))
            tour_lbl_text = f"Tour: {tour_text}   |   Ngày gửi: {review_date}"
            tk.Label(row2, text=tour_lbl_text, font=("Times New Roman", 9.5, "italic"), fg=THEME["muted"], bg="#ffffff").pack(side="left")

            # Hàng 3: Nội dung đánh giá
            content_lbl = tk.Label(card, text=review_content, font=("Times New Roman", 11), fg=THEME["text"], bg="#ffffff", justify="left", anchor="w", wraplength=700)
            content_lbl.pack(fill="x", pady=(0, 6))

            # Hàng 4: Phản hồi từ Admin (nếu có)
            admin_reply = r.get("adminReply", "").strip()
            if admin_reply:
                reply_frame = tk.Frame(card, bg="#f8fafc", highlightbackground="#e2e8f0", highlightthickness=1, padx=12, pady=10)
                reply_frame.pack(fill="x", pady=(6, 0))

                accent_bar = tk.Frame(reply_frame, bg="#0ea5e9", width=3)
                accent_bar.pack(side="left", fill="y")

                reply_text_frame = tk.Frame(reply_frame, bg="#f8fafc")
                reply_text_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))

                reply_title = f"Phản hồi từ Admin ({r.get('adminReplyBy', 'Quản trị viên')} - {r.get('adminReplyDate', '')}):"
                tk.Label(reply_text_frame, text=reply_title, font=("Times New Roman", 9.5, "bold"), fg="#0ea5e9", bg="#f8fafc", anchor="w").pack(fill="x")
                tk.Label(reply_text_frame, text=admin_reply, font=("Times New Roman", 10.5, "italic"), fg=THEME["text"], bg="#f8fafc", justify="left", anchor="w", wraplength=650).pack(fill="x", pady=(2, 0))

            bind_double_click(card, lambda event, r_item=r: show_review_detail(r_item))

        # Thêm nút làm mới
        style_button(review_body, "↻ LÀM MỚI ĐÁNH GIÁ", THEME["primary"], tab_thong_ke).pack(anchor="w", pady=(10, 0))

        # 4. Popup chi tiết khi double click
        # Được xử lý bằng bind_double_click trên các card đánh giá phía trên
        set_status(f"Đang ở Đánh giá khách hàng - Hiển thị {total_reviews} đánh giá", THEME["primary"])

    def tab_thong_bao():
        clear_container()
        app["current_tab"] = "notify"

        split_fr = tk.Frame(content_area, bg=THEME["bg"])
        split_fr.pack(fill="both", expand=True)
        split_fr.grid_columnconfigure(0, weight=1, uniform="col")
        split_fr.grid_columnconfigure(1, weight=1, uniform="col")

        left_col = tk.Frame(split_fr, bg=THEME["bg"])
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right_col = tk.Frame(split_fr, bg=THEME["bg"])
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # --- LEFT SIDE: SEND NOTIFICATION ---
        _, body = make_section(
            left_col,
            "Gửi thông báo khẩn cấp",
            "Chủ động gửi thông báo quan trọng cho từng đoàn khách đang hoạt động để cập nhật lịch trình hoặc thay đổi phát sinh.",
            accent="#dc2626",
        )

        tk.Label(body, text="Chọn tour cần gửi thông báo", font=("Times New Roman", 13, "bold"), bg=THEME["surface"], fg=THEME["text"]).pack(anchor="w", pady=(0, 6))

        my_tours = get_my_tours()
        active_tours = [t for t in my_tours if t.get("trangThai") not in TOUR_FINISHED_STATUSES]
        tour_options = [f"{t['ma']} - {t['ten']}" for t in active_tours]

        tour_var = tk.StringVar()
        tour_cb = ttk.Combobox(body, textvariable=tour_var, values=tour_options, state="readonly", font=("Times New Roman", 12))
        tour_cb.pack(anchor="w", fill="x", pady=(0, 18))
        if tour_options:
            tour_cb.current(0)

        tk.Label(body, text="Nội dung thông báo", font=("Times New Roman", 13, "bold"), bg=THEME["surface"], fg=THEME["text"]).pack(anchor="w", pady=(0, 8))
        txt = tk.Text(body, height=11, font=("Times New Roman", 13), relief="solid", bd=1, wrap="word")
        txt.pack(fill="both", expand=True, pady=(0, 18))

        def gui_thong_bao():
            content = txt.get("1.0", "end").strip()
            if not tour_var.get():
                return messagebox.showwarning("Lỗi", "Vui lòng chọn đoàn khách muốn gửi thông báo!")
            if not content:
                return messagebox.showwarning("Lỗi", "Vui lòng nhập nội dung thông báo!")

            selected = tour_var.get().split(" - ", 1)
            selected_tour_ma = selected[0]
            selected_tour_ten = selected[1] if len(selected) > 1 else ""

            new_notif = {
                "maHDV": ma_hdv,
                "tenHDV": ten_hdv,
                "maTour": selected_tour_ma,
                "tenTour": selected_tour_ten,
                "content": content,
                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
            app["ql"].notifications.append(new_notif)
            app["ql"].save()
            messagebox.showinfo("Thành công", f"Đã gửi thông báo đến đoàn '{selected_tour_ten}'!")
            tab_danh_sach_tour()

        style_button(body, "XÁC NHẬN GỬI THÔNG BÁO", THEME["danger"], gui_thong_bao).pack(anchor="w")

        # --- RIGHT SIDE: RECEIVED NOTIFICATIONS ---
        right_section, right_body = make_section(
            right_col,
            "Thông báo nhận được",
            "Danh sách các chỉ thị điều hành, cảnh báo khởi hành và cập nhật từ hệ thống gửi riêng cho bạn.",
            accent=THEME["primary"],
        )

        my_ma_hdv = str(ma_hdv).strip().upper()
        relevant_notifs = []
        seen_notifs = set()

        for n in app["ql"].list_notifications:
            normalized_notif = normalize_notification_item(n, datastore=app["ql"])
            notif_hdv = str(normalized_notif.get("maHDV", "")).strip().upper()
            notif_user = str(normalized_notif.get("username", "")).strip().upper()
            target_ids = {my_ma_hdv, str(user_data.get("email", "")).strip().upper(), str(user_data.get("sdt", "")).strip().upper()}
            evt_type = str(normalized_notif.get("eventType", "")).strip()

            if (notif_hdv and notif_hdv == my_ma_hdv) or (notif_user and notif_user in target_ids) or evt_type in {"broadcast", "guide_broadcast"}:
                content_val = str(normalized_notif.get("content", "")).strip()
                date_val = str(normalized_notif.get("date", "")).strip()
                m_tour = str(normalized_notif.get("maTour", "")).strip()
                sig = (evt_type, m_tour, content_val, date_val)
                if sig not in seen_notifs:
                    seen_notifs.add(sig)
                    relevant_notifs.append(normalized_notif)

        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            except Exception:
                return datetime.min

        relevant_notifs.sort(key=lambda x: parse_date(x.get("date", "")), reverse=True)

        event_type_translations = {
            "TOUR_DEPARTURE_WARNING": "Cảnh báo khởi hành",
            "Account Update": "Cập nhật tài khoản",
            "booking_created": "Đã đặt tour",
            "payment_success": "Thanh toán thành công",
            "tour_completed": "Tour hoàn thành",
            "refund_request": "Yêu cầu hoàn tiền",
            "refund_approved": "Hoàn tiền được duyệt",
            "refund_rejected": "Hoàn tiền bị từ chối"
        }

        if not relevant_notifs:
            tk.Label(
                right_body,
                text="Bạn chưa nhận được thông báo nào.",
                bg=THEME["surface"],
                fg=THEME["muted"],
                font=("Times New Roman", 13, "italic")
            ).pack(anchor="center", pady=40)
        else:
            tree_frame = tk.Frame(right_body, bg=THEME["surface"])
            tree_frame.pack(fill="both", expand=True)

            style = ttk.Style()
            style.configure(
                "Notif.Treeview",
                font=("Times New Roman", 12),
                rowheight=45,
                background=THEME["surface"],
                fieldbackground=THEME["surface"],
                foreground=THEME["text"],
                bordercolor=THEME["border"],
                relief="flat",
            )
            style.map("Notif.Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", THEME["text"])])
            style.configure(
                "Notif.Treeview.Heading",
                font=("Times New Roman", 12, "bold"),
                background=THEME["heading_bg"],
                foreground=THEME["text"],
                relief="flat",
                padding=(8, 10),
            )

            cols = ("date", "eventType", "maTour", "maBooking", "content")
            notif_tree = ttk.Treeview(
                tree_frame,
                columns=cols,
                show="headings",
                style="Notif.Treeview",
                height=15
            )

            notif_tree.heading("date", text="Ngày nhận")
            notif_tree.heading("eventType", text="Loại sự kiện")
            notif_tree.heading("maTour", text="Mã Tour")
            notif_tree.heading("maBooking", text="Mã Booking")
            notif_tree.heading("content", text="Nội dung")

            notif_tree.column("date", width=125, anchor="w", stretch=False)
            notif_tree.column("eventType", width=140, anchor="w", stretch=False)
            notif_tree.column("maTour", width=80, anchor="center", stretch=False)
            notif_tree.column("maBooking", width=100, anchor="center", stretch=False)
            notif_tree.column("content", anchor="w", width=300)

            v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=notif_tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=notif_tree.xview)
            bind_autohide_scrollbar(notif_tree, v_scrollbar, "vertical")
            bind_autohide_scrollbar(notif_tree, h_scrollbar, "horizontal")

            notif_tree.pack(side="left", fill="both", expand=True)

            notif_mapping = {}
            for idx, item in enumerate(relevant_notifs):
                raw_evt = item.get("eventType", "")
                evt_display = event_type_translations.get(raw_evt, raw_evt or "Thông báo")
                m_tour = item.get("maTour", "") or "N/A"
                m_booking = item.get("maBooking", "") or "N/A"
                date_display = item.get("date", "")
                content_display = item.get("content", "").replace("\n", " ")

                tree_id = notif_tree.insert(
                    "",
                    "end",
                    values=(date_display, evt_display, m_tour, m_booking, content_display),
                )
                tag = "even" if idx % 2 == 0 else "odd"
                notif_tree.item(tree_id, tags=(tag,))
                notif_mapping[tree_id] = item

            apply_zebra(notif_tree)

            def on_notif_double_click(event):
                sel = notif_tree.selection()
                if not sel:
                    return
                notif = notif_mapping.get(sel[0])
                if not notif:
                    return

                popup = tk.Toplevel(root)
                popup.title("Chi tiết thông báo")
                popup.geometry("700x500")
                popup.minsize(600, 400)
                popup.configure(bg=THEME["bg"])
                popup.grab_set()

                popup.update_idletasks()
                x = (popup.winfo_screenwidth() - popup.winfo_reqwidth()) // 2
                y = (popup.winfo_screenheight() - popup.winfo_reqheight()) // 2
                popup.geometry(f"+{x-50}+{y-50}")

                pop_sect, pop_body = make_section(
                    popup,
                    "Chi tiết thông báo",
                    f"Sự kiện: {event_type_translations.get(notif.get('eventType', ''), notif.get('eventType', '') or 'Thông báo')}",
                    accent=THEME["primary"]
                )
                pop_sect.pack(fill="both", expand=True, padx=20, pady=20)

                grid_fr = tk.Frame(pop_body, bg=THEME["surface"])
                grid_fr.pack(fill="x", pady=(0, 15))

                details = [
                    ("Thời gian nhận", notif.get("date", "-")),
                    ("Mã Tour liên quan", notif.get("maTour", "-") or "N/A"),
                    ("Tên Tour", notif.get("tenTour", "-") or "N/A"),
                    ("Mã Booking", notif.get("maBooking", "-") or "N/A"),
                ]

                for idx_d, (lbl, val) in enumerate(details):
                    row_idx = idx_d // 2
                    col_idx = (idx_d % 2) * 2
                    tk.Label(grid_fr, text=f"{lbl}:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg=THEME["muted"]).grid(row=row_idx, column=col_idx, sticky="w", padx=(10, 5), pady=6)
                    tk.Label(grid_fr, text=val, font=("Times New Roman", 12), bg=THEME["surface"], fg=THEME["text"]).grid(row=row_idx, column=col_idx+1, sticky="w", padx=(0, 20), pady=6)

                tk.Label(pop_body, text="Nội dung chi tiết:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg=THEME["primary"]).pack(anchor="w", pady=(10, 5))

                txt_fr = tk.Frame(pop_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
                txt_fr.pack(fill="both", expand=True, pady=(0, 20))

                txt_area = tk.Text(txt_fr, font=("Times New Roman", 12), bg="#f8fafc", wrap="word", bd=0)
                txt_area.insert("1.0", notif.get("content", ""))
                txt_area.config(state="disabled")

                pop_sy = ttk.Scrollbar(txt_fr, orient="vertical", command=txt_area.yview)
                txt_area.configure(yscrollcommand=pop_sy.set)
                pop_sy.pack(side="right", fill="y")
                txt_area.pack(side="left", fill="both", expand=True, padx=10, pady=10)

                style_button(pop_body, "Đóng", THEME["primary"], popup.destroy).pack(anchor="center")

            notif_tree.bind("<Double-1>", on_notif_double_click)

    def tab_cai_dat():
        clear_container()
        app["current_tab"] = "settings"

        hdv_data = app["ql"].find_hdv(ma_hdv)
        if not hdv_data:
            tk.Label(content_area, text="Lỗi: Không tìm thấy thông tin tài khoản!", fg=THEME["danger"], bg=THEME["bg"], font=("Times New Roman", 13, "bold")).pack(anchor="w", pady=20, padx=20)
            return

        # Vùng chứa chính: Gắn trực tiếp vào content_area (Đã bỏ Canvas lồng dư thừa)
        main_container = tk.Frame(content_area, bg=THEME["bg"])
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        widgets = {}

        # ==========================================
        # HELPER: TẠO KHỐI FORM (CARD-STYLE)
        # ==========================================
        def create_form_card(parent, title, accent_color, fields, readonly=False):
            # Tạo viền Card
            card = tk.Frame(parent, bg="#ffffff", highlightbackground=THEME["border"], highlightthickness=1)
            card.pack(fill="x", pady=(0, 20))
            
            # Vạch màu trên cùng (Top accent bar)
            tk.Frame(card, bg=accent_color, height=3).pack(fill="x")
            
            # Header
            header = tk.Frame(card, bg="#ffffff")
            header.pack(fill="x", padx=25, pady=(15, 5))
            tk.Label(
                header, text=title, bg="#ffffff", fg=accent_color, font=("Times New Roman", 13, "bold")
            ).pack(side="left")
            
            # Lưới chứa nội dung
            grid_frame = tk.Frame(card, bg="#ffffff", padx=25, pady=10)
            grid_frame.pack(fill="x")
            
            # Thiết lập lưới cột (2 cột chính chia đôi màn hình)
            grid_frame.grid_columnconfigure(0, weight=0, minsize=140)
            grid_frame.grid_columnconfigure(1, weight=1)
            grid_frame.grid_columnconfigure(2, weight=0, minsize=40) 
            grid_frame.grid_columnconfigure(3, weight=0, minsize=140)
            grid_frame.grid_columnconfigure(4, weight=1)
            
            for idx, item in enumerate(fields):
                # Unpack dữ liệu tùy theo readonly hay editable
                if readonly:
                    label_text, value = item
                else:
                    label_text, key, kind = item

                row_idx = idx // 2
                col_offset = (idx % 2) * 3  # Trả về 0 (bên trái) hoặc 3 (bên phải)
                
                # Label
                tk.Label(
                    grid_frame,
                    text=f"{label_text}:" if readonly else label_text,
                    anchor="w",
                    bg="#ffffff",
                    font=("Times New Roman", 12, "bold" if not readonly else "normal"),
                    fg=THEME["muted"] if readonly else THEME["text"]
                ).grid(row=row_idx, column=col_offset, sticky="w", pady=10)
                
                # Input / Value
                if readonly:
                    tk.Label(
                        grid_frame, text=str(value), anchor="w", bg="#ffffff", font=("Times New Roman", 12), fg=THEME["text"]
                    ).grid(row=row_idx, column=col_offset + 1, sticky="w", pady=10)
                else:
                    if kind == "gender":
                        gender_val = str(hdv_data.get(key, "") or "Nam")
                        if gender_val not in ["Nam", "Nữ"]:
                            gender_val = "Nam"
                        widget = ttk.Combobox(grid_frame, values=["Nam", "Nữ"], state="readonly", font=("Times New Roman", 12))
                        widget.set(gender_val)
                    else:
                        show_char = "*" if kind == "password" else ""
                        widget = tk.Entry(grid_frame, font=("Times New Roman", 12), relief="solid", bd=1, show=show_char)
                        if kind != "password":
                            widget.insert(0, str(hdv_data.get(key, "") or ""))
                    
                    widget.grid(row=row_idx, column=col_offset + 1, sticky="ew", pady=10, ipady=5)
                    widgets[key] = widget

        # === PHẦN 1: THÔNG TIN HỆ THỐNG (READ-ONLY) ===
        readonly_items = [
            ("Mã HDV", hdv_data.get("maHDV", "-")),
            ("Username", hdv_data.get("username", "-")),
            ("Trạng thái phân công", hdv_data.get("trangThai", "-")),
            ("Trạng thái tài khoản", hdv_data.get("trangThaiTaiKhoan", "-")),
            ("Số tour đã dẫn", str(hdv_data.get("soTourDaDan", "0"))),
            ("Điểm đánh giá trung bình", f"{hdv_data.get('avg_rating', 0):.1f} / 5.0"),
        ]
        create_form_card(main_container, "THÔNG TIN HỆ THỐNG", THEME["primary"], readonly_items, readonly=True)

        # === PHẦN 2: THÔNG TIN CHỈNH SỬA ĐƯỢC ===
        create_form_card(main_container, "THÔNG TIN CÁ NHÂN", "#2563eb", [
            ("Họ và tên", "tenHDV", "text"),
            ("Ngày sinh", "ngaySinh", "text"),
            ("Giới tính", "gioiTinh", "gender"),
            ("Địa chỉ", "diaChi", "text"),
        ])
        
        create_form_card(main_container, "THÔNG TIN LIÊN HỆ", "#059669", [
            ("Số điện thoại", "sdt", "text"),
            ("Email", "email", "text"),
        ])
        
        create_form_card(main_container, "NGHIỆP VỤ CHUYÊN MÔN", "#7c3aed", [
            ("Khu vực hoạt động", "khuVuc", "text"),
            ("Ngoại ngữ", "ngoaiNgu", "text"),
            ("Chuyên môn", "chuyenMon", "text"),
            ("Chứng chỉ", "chungChi", "text"),
        ])

        # === PHẦN 3: BẢO MẬT (Custom Layout) ===
        sec_card = tk.Frame(main_container, bg="#ffffff", highlightbackground=THEME["border"], highlightthickness=1)
        sec_card.pack(fill="x", pady=(0, 20))
        tk.Frame(sec_card, bg="#fb923c", height=3).pack(fill="x")
        
        sec_head = tk.Frame(sec_card, bg="#ffffff")
        sec_head.pack(fill="x", padx=25, pady=(15, 0))
        tk.Label(sec_head, text="BẢO MẬT TÀI KHOẢN", bg="#ffffff", fg="#c2410c", font=("Times New Roman", 13, "bold")).pack(anchor="w")
        tk.Label(sec_head, text="* Lưu ý: Để trống ô mật khẩu nếu bạn không muốn thay đổi mật khẩu hiện tại.", bg="#ffffff", fg="#9a3412", font=("Times New Roman", 11, "italic")).pack(anchor="w", pady=(2, 0))
        
        sec_grid = tk.Frame(sec_card, bg="#ffffff", padx=25, pady=10)
        sec_grid.pack(fill="x")
        sec_grid.grid_columnconfigure(0, weight=0, minsize=140)
        sec_grid.grid_columnconfigure(1, weight=1)
        sec_grid.grid_columnconfigure(2, weight=1) # Cột trống cân bằng không gian
        
        tk.Label(sec_grid, text="Mật khẩu mới", anchor="w", bg="#ffffff", font=("Times New Roman", 12, "bold"), fg=THEME["text"]).grid(row=0, column=0, sticky="w", pady=10)
        pass_widget = tk.Entry(sec_grid, font=("Times New Roman", 12), relief="solid", bd=1, show="*")
        pass_widget.grid(row=0, column=1, sticky="ew", pady=10, ipady=5)
        widgets["password"] = pass_widget

        # === PHẦN 4: NÚT HÀNH ĐỘNG ===
        actions_wrapper = tk.Frame(main_container, bg=THEME["bg"])
        actions_wrapper.pack(fill="x", pady=(10, 40))

        actions_container = tk.Frame(actions_wrapper, bg=THEME["bg"])
        actions_container.pack(anchor="center") # Giữ nút căn giữa thanh lịch

        def save_profile():
            allowed_fields = ["tenHDV", "sdt", "email", "ngaySinh", "gioiTinh", "diaChi", "khuVuc", "ngoaiNgu", "chuyenMon", "chungChi"]
            values = {key: widgets[key].get().strip() for key in allowed_fields}
            new_name = values["tenHDV"]
            new_phone = values["sdt"]
            new_email = values["email"]
            new_pass = widgets["password"].get().strip()

            if len(new_name) < 3:
                return messagebox.showwarning("Lỗi", "Họ tên quá ngắn (tối thiểu 3 ký tự).")
            if not is_valid_phone(new_phone):
                return messagebox.showwarning("Lỗi", "Số điện thoại không hợp lệ.")
            if not is_valid_email(new_email):
                return messagebox.showwarning("Lỗi", "Định dạng email không hợp lệ.")
            if values["ngaySinh"]:
                try:
                    datetime.strptime(values["ngaySinh"], "%d/%m/%Y")
                except ValueError:
                    return messagebox.showwarning("Lỗi", "Ngày sinh phải đúng định dạng dd/mm/yyyy.")
            if new_pass and not is_valid_password(new_pass):
                return messagebox.showwarning("Lỗi", "Mật khẩu quá ngắn (tối thiểu 3 ký tự).")
            if values["gioiTinh"] not in ["Nam", "Nữ"]:
                return messagebox.showwarning("Lỗi", "Giới tính chỉ được chọn Nam hoặc Nữ.")

            for h in app["ql"].list_hdv:
                if h.get("maHDV") == ma_hdv:
                    continue
                if h.get("sdt") == new_phone:
                    return messagebox.showwarning("Lỗi", "Số điện thoại đã tồn tại ở HDV khác.")
                if str(h.get("email", "")).lower() == new_email.lower():
                    return messagebox.showwarning("Lỗi", "Email đã tồn tại ở HDV khác.")

            for key, value in values.items():
                hdv_data[key] = value
            if new_pass:
                hdv_data["password"] = prepare_password_for_storage(new_pass)

            user_data["tenHDV"] = new_name
            for key in allowed_fields:
                user_data[key] = hdv_data.get(key, "")
            now_text = datetime.now().strftime("%d/%m/%Y %H:%M")
            app["ql"].notifications.append({
                "eventType": "guide_profile_updated",
                "maHDV": ma_hdv,
                "tenHDV": new_name,
                "content": f"HDV đã cập nhật thông tin cá nhân. Mã HDV: {ma_hdv}, Tên HDV: {new_name}, Thời gian: {now_text}.",
                "date": now_text,
                "internalOnly": True,
                "phamVi": "internal",
            })
            app["ql"].save()
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin cá nhân thành công!")
            tab_cai_dat()

        style_button(actions_container, "LƯU THAY ĐỔI", THEME["success"], save_profile).pack(side="left", padx=10)
        style_button(actions_container, "HỦY/LÀM MỚI", THEME["muted"], tab_cai_dat).pack(side="left", padx=10)

    def open_view(title, subtitle, view_fn, button):
        set_active_menu(button)
        app["page_title_var"].set(title)
        app["page_subtitle_var"].set(subtitle)
        view_fn()
        set_status(f"Đang ở mục: {title}", THEME["primary"])
        if title == "Lịch trình tour":
            set_badge("ĐANG THEO DÕI TOUR", "#123a5a", "#d1fae5")
            header_badge.config(text="LỊCH TRÌNH TOUR", bg="#dbeafe", fg="#1d4ed8")
        elif title == "Hiệu suất & đánh giá":
            set_badge("ĐANG XEM HIỆU SUẤT", "#3b0764", "#ede9fe")
            header_badge.config(text="BÁO CÁO CÁ NHÂN", bg="#ede9fe", fg="#7c3aed")
        elif title == "Gửi thông báo":
            set_badge("CHẾ ĐỘ THÔNG BÁO", "#7f1d1d", "#fee2e2")
            header_badge.config(text="THÔNG BÁO KHẨN", bg="#fee2e2", fg="#dc2626")
        else:
            set_badge("CẬP NHẬT TÀI KHOẢN", "#78350f", "#fef3c7")
            header_badge.config(text="CÀI ĐẶT CÁ NHÂN", bg="#fef3c7", fg="#d97706")

    nav_items = [
        ("Lịch trình tour", "Theo dõi các tour được phân công, danh sách khách và trạng thái vận hành.", tab_danh_sach_tour, "🗺"),
        ("Hiệu suất & đánh giá", "Tổng hợp điểm số, tỷ lệ hài lòng và năng lực chuyên môn của HDV.", tab_thong_ke, "⭐"),
        ("Gửi thông báo", "Gửi thông báo khẩn cấp đến các đoàn khách đang hoạt động.", tab_thong_bao, "🔔"),
        ("Cài đặt tài khoản", "Quản lý thông tin cá nhân và cập nhật mật khẩu bảo mật.", tab_cai_dat, "👤"),
    ]

    nav_buttons = []
    for idx, (title, subtitle, view_fn, icon) in enumerate(nav_items):
        btn = menu_btn(
            title,
            lambda t=title, s=subtitle, f=view_fn, b_idx=idx: open_view(t, s, f, nav_buttons[b_idx]),
            icon=icon,
        )
        btn.pack(fill="x", pady=4)
        nav_buttons.append(btn)

    def _refresh_menu_button_layout(button):
        full_text = getattr(button, "_full_text", "")
        icon = getattr(button, "_icon", "")
        if app.get("sidebar_collapsed"):
            compact_text = icon if icon else (full_text[:1].upper() if full_text else "•")
            button.configure(
                text=compact_text,
                anchor="center",
                justify="center",
                padx=4,
                pady=12,
                wraplength=40,
            )
        else:
            label = f"  {icon}  {full_text}" if icon else f"  {full_text}"
            button.configure(
                text=label,
                anchor="w",
                justify="left",
                padx=14,
                pady=13,
                wraplength=210,
            )

    util = tk.Frame(sidebar, bg=SIDEBAR_BG)
    util.pack(side="bottom", fill="x", padx=12, pady=14)
    tk.Frame(util, bg="#22365b", height=1).pack(fill="x", pady=(0, 12))
    logout_btn = RoundedButton(
        util,
        text="  🚪  Đăng xuất",
        bg="#b91c1c",
        fg="white",
        activebackground="#dc2626",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        anchor="w",
        font=("Times New Roman", 13, "bold"),
        padx=14,
        pady=12,
        command=lambda: logout_system(root),
    )
    logout_btn.pack(fill="x")

    def apply_sidebar_mode():
        collapsed = app.get("sidebar_collapsed", False)
        sidebar.configure(width=SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_EXPANDED_WIDTH)

        if collapsed:
            brand_title.configure(text="VNT", font=("Times New Roman", 12, "bold"))
            if brand_subtitle.winfo_manager():
                brand_subtitle.pack_forget()
            if account_card.winfo_manager():
                account_card.pack_forget()
            collapse_btn.configure(text="\u2630")
            util.pack_configure(padx=8, pady=10)
            menu.pack_configure(padx=8)
            logout_btn.configure(text="🚪", anchor="center", padx=8)
        else:
            brand_title.configure(text="VIETNAM TRAVEL", font=("Times New Roman", 16, "bold"))
            if not brand_subtitle.winfo_manager():
                brand_subtitle.pack(fill="x", pady=(2, 0))
            if not account_card.winfo_manager():
                account_card.pack(fill="x", padx=16, pady=(0, 8), before=menu)
            collapse_btn.configure(text="\u2630")
            util.pack_configure(padx=12, pady=14)
            menu.pack_configure(padx=12)
            logout_btn.configure(text="🚪  Đăng xuất", anchor="w", padx=14)

        for nav_btn in nav_buttons:
            _refresh_menu_button_layout(nav_btn)

    def toggle_sidebar():
        app["sidebar_collapsed"] = not app.get("sidebar_collapsed", False)
        apply_sidebar_mode()

    collapse_btn.configure(command=toggle_sidebar)
    apply_sidebar_mode()

    open_view(
        "Lịch trình tour",
        "Theo dõi các tour được phân công, danh sách khách và trạng thái vận hành.",
        tab_danh_sach_tour,
        nav_buttons[0],
    )

def logout_system(root):
    if messagebox.askyesno("Xác nhận", "Bạn có muốn đăng xuất khỏi hệ thống?"):
        for widget in root.winfo_children():
            widget.destroy()
        try:
            from main import TravelSystem

            root.configure(bg=THEME["bg"])
            TravelSystem(root)
        except (ImportError, RuntimeError, tk.TclError) as e:
            messagebox.showerror("Lỗi", f"Không thể quay lại màn hình đăng nhập.\n{e}")
