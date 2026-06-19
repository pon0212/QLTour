import os
import re
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
from dataclasses import dataclass
import copy
import threading
import urllib.parse
import urllib.request
from GUI.common.rounded_button import RoundedButton
from GUI.common.weather_popup import open_tour_weather_popup

from core.app import (
    ACTIVE_TOUR_STATUSES_FOR_GUIDE,
    JSONDataStore,
    TERMINAL_TOUR_STATUSES,
    TOUR_STATUS_CANCELLED,
    TOUR_STATUS_CHOICES,
    TOUR_STATUS_COMPLETED,
    TOUR_STATUS_FULL,
    TOUR_STATUS_HIDDEN,
    TOUR_STATUS_INACTIVE,
    TOUR_STATUS_NOT_OPEN,
    TOUR_STATUS_OPEN,
    TOUR_STATUS_STARTED,
    approve_refund as service_approve_refund,
    can_hard_delete_booking as service_can_hard_delete_booking,
    build_revenue_report,
    calculate_booking_total,
    calculate_paid_amount,
    calculate_remaining_amount,
    create_review_notification,
    show_wrapped_message,
    show_detailed_notification_popup,
    cleanup_deleted_tour_references,
    build_voucher_scope_label,
    calculate_age_discount,
    cancel_booking as service_cancel_booking,
    collect_changed_fields,
    compute_duration_days,
    compute_end_date,
    derive_tour_status,
    enable_tk_text_autofix,
    fix_mojibake,
    find_review_by_id,
    format_ddmmyyyy,
    is_booking_allowed,
    is_upcoming_or_ongoing,
    is_valid_email as core_is_valid_email,
    is_valid_phone as core_is_valid_phone,
    mask_password,
    normalize_review_for_display,
    normalize_code,
    normalize_email,
    normalize_notification_item as core_normalize_notification_item,
    normalize_passenger_breakdown,
    normalize_review_item as core_normalize_review_item,
    normalize_spaces,
    normalize_tour_name,
    normalize_title_case,
    normalize_tour_scope,
    normalize_tour_status,
    parse_ddmmyyyy as parse_tour_ddmmyyyy,
    parse_duration_days,
    prepare_password_for_storage,
    recalculate_hdv_review_stats,
    reject_refund as service_reject_refund,
    refresh_all_tour_statuses,
    sync_ghi_chu_dieu_hanh,
    summarize_bookings_by_tour,
    validate_voucher_payload,
    save_reviews,
    write_crud_log,
)


@dataclass(frozen=True)
class AdminTabDef:
    key: str
    title: str
    subtitle: str
    icon: str
    handler_name: str


TAB_DEFINITIONS: tuple[AdminTabDef, ...] = (
    AdminTabDef(
        key="dashboard",
        title="Tổng quan Dashboard",
        subtitle="Theo dõi nhanh doanh thu, số tour, HDV và booking trong hệ thống.",
        icon="🏠",
        handler_name="dashboard_tab",
    ),
    AdminTabDef(
        key="hdv",
        title="Quản lý hướng dẫn viên",
        subtitle="Quản trị hồ sơ nhân sự, trạng thái và thông tin điều phối HDV.",
        icon="🧭",
        handler_name="admin_hdv_tab",
    ),
    AdminTabDef(
        key="users",
        title="Quản lý khách hàng",
        subtitle="Theo dõi tài khoản khách, lịch sử đặt chỗ và thông tin liên hệ.",
        icon="👥",
        handler_name="admin_user_tab",
    ),
    AdminTabDef(
        key="tours",
        title="Quản lý tour",
        subtitle="Điều phối lịch trình, trạng thái tour và hướng dẫn viên phụ trách.",
        icon="🗺",
        handler_name="admin_tour_tab",
    ),
    AdminTabDef(
        key="bookings",
        title="Quản lý booking",
        subtitle="Kiểm soát booking, thanh toán và danh sách khách theo tour.",
        icon="🧾",
        handler_name="admin_booking_tab",
    ),
    AdminTabDef(
        key="vouchers",
        title="Mã giảm giá",
        subtitle="Quản lý voucher, chương trình ưu đãi và điều kiện áp dụng.",
        icon="🎟",
        handler_name="admin_voucher_tab",
    ),
    AdminTabDef(
        key="report",
        title="Báo cáo tổng hợp",
        subtitle="Xem nhanh báo cáo doanh thu và tổng hợp booking theo tour.",
        icon="📊",
        handler_name="report",
    ),
    
    AdminTabDef(
        key="reviews",
        title="Đánh giá khách hàng",
        subtitle="Theo dõi phản hồi, điểm chấm và nội dung đánh giá từ khách hàng.",
        icon="⭐",
        handler_name="admin_reviews_tab",
    ),
    AdminTabDef(
        key="notifications",
        title="Thông báo HDV",
        subtitle="Tổng hợp các thông báo điều hành đã gửi tới hướng dẫn viên.",
        icon="🔔",
        handler_name="admin_notifications_tab",
    ),
)


def get_admin_tab_definitions() -> tuple[AdminTabDef, ...]:
    return TAB_DEFINITIONS


def get_admin_tab_handler(tab_key: str):
    normalized_key = str(tab_key or "").strip().lower()
    tab_def = next((item for item in TAB_DEFINITIONS if item.key == normalized_key), TAB_DEFINITIONS[0])
    if tab_def.handler_name == "report":
        return _render_report_tab
    return globals()[tab_def.handler_name]


def _render_matplotlib_charts(parent, report):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    fig = Figure(figsize=(10, 4.5), dpi=100)
    fig.patch.set_facecolor(THEME["surface"])

    # Biểu đồ tròn: Doanh thu thực nhận theo tour
    ax_pie = fig.add_subplot(121)
    tours_data = report.get("by_tour", [])
    pie_labels = []
    pie_values = []
    for r in tours_data:
        val = safe_int(r.get("doanhThuThuan", 0))
        if val > 0:
            pie_labels.append(r.get("maTour", ""))
            pie_values.append(val)

    if pie_values:
        colors = ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed", "#10b981", "#f43f5e", "#0ea5e9"]
        wedges, texts, autotexts = ax_pie.pie(
            pie_values,
            labels=pie_labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors[:len(pie_values)],
            textprops=dict(fontname="Times New Roman", color=THEME["text"])
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')
        ax_pie.set_title("Tỷ lệ doanh thu thực nhận theo tour", fontname="Times New Roman", fontsize=12, fontweight="bold", color=THEME["text"])
    else:
        ax_pie.text(0.5, 0.5, "Không có dữ liệu doanh thu thực nhận", ha="center", va="center", fontname="Times New Roman", color=THEME["muted"])
        ax_pie.set_title("Tỷ lệ doanh thu theo tour", fontname="Times New Roman", fontsize=12, fontweight="bold", color=THEME["text"])
        ax_pie.axis('off')

    # Biểu đồ cột: Doanh thu thực nhận theo tour
    ax_bar = fig.add_subplot(122)
    bar_labels = []
    bar_values = []
    for r in sorted(report.get("by_tour", []), key=lambda item: safe_int(item.get("doanhThuThuan", 0)), reverse=True)[:10]:
        bar_labels.append(r.get("maTour", ""))
        bar_values.append(safe_int(r.get("doanhThuThuan", 0)))

    if bar_values and any(v > 0 for v in bar_values):
        ax_bar.bar(bar_labels, bar_values, color="#2563eb", width=0.55, label="Doanh thu thực nhận")
        ax_bar.set_title("Doanh thu thực nhận theo tour", fontname="Times New Roman", fontsize=12, fontweight="bold", color=THEME["text"])
        ax_bar.set_ylabel("Doanh thu (VND)", fontname="Times New Roman", fontsize=10, color=THEME["text"])
        ax_bar.set_xticks(range(len(bar_labels)))
        ax_bar.set_xticklabels(bar_labels, fontname="Times New Roman", fontsize=9, color=THEME["text"], rotation=15)
        ax_bar.tick_params(axis='y', labelcolor=THEME["text"])
        ax_bar.grid(axis='y', linestyle='--', alpha=0.5)
        ax_bar.set_axisbelow(True)
        ax_bar.legend(prop={"family": "Times New Roman", "size": 9})
    else:
        ax_bar.text(0.5, 0.5, "Không có dữ liệu doanh thu thực nhận", ha="center", va="center", fontname="Times New Roman", color=THEME["muted"])
        ax_bar.set_title("Doanh thu theo tour", fontname="Times New Roman", fontsize=12, fontweight="bold", color=THEME["text"])
        ax_bar.set_axis_off()

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


def _render_report_tab(app):
    clear_container(app)

    # Tạo Canvas và Scrollbar để report có thể scroll khi nội dung dài
    canvas_wrapper = tk.Frame(app["container"], bg=THEME["bg"])
    canvas_wrapper.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(canvas_wrapper, bg=THEME["bg"], highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_wrapper, orient="vertical", command=canvas.yview)
    
    report_body = tk.Frame(canvas, bg=THEME["bg"])
    
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Sử dụng auto-hide scrollbar
    bind_autohide_scrollbar(canvas, scrollbar, "vertical")
    
    canvas.pack(side="left", fill="both", expand=True)
    
    canvas_window = canvas.create_window((0, 0), window=report_body, anchor="nw")
    
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)
    
    report_body.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)
    
    # Hỗ trợ scroll bằng chuột
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    # Cleanup mousewheel binding khi report bị destroy
    def cleanup_mousewheel():
        try:
            canvas.unbind_all("<MouseWheel>")
        except:
            pass
    
    canvas_wrapper.bind("<Destroy>", lambda e: cleanup_mousewheel())
    
    # Thêm padding cho nội dung
    content_frame = tk.Frame(report_body, bg=THEME["bg"])
    content_frame.pack(fill="both", expand=True, padx=10, pady=10)

    report = build_revenue_report(app["ql"])
    overview = report.get("overview", {})
    stats_row = tk.Frame(content_frame, bg=THEME["bg"])
    stats_row.pack(fill="x", pady=(0, 10))
    stats = [
        ("Tổng phải thu", format_currency(overview.get("tongPhaiThu", overview.get("doanhThuDuKien", 0))), THEME["primary"]),
        ("Booking hiệu lực", str(overview.get("bookingHieuLuc", 0)), THEME["success"]),
        ("Số tiền đã thu", format_currency(overview.get("daThu", 0)), "#0ea5e9"),
        ("Số tiền còn nợ", format_currency(overview.get("conNo", 0)), THEME["danger"]),
        ("Đã hoàn/trừ", format_currency(overview.get("tongHoanTien", 0)), THEME["muted"]),
        ("Doanh thu thực nhận", format_currency(overview.get("doanhThuThuan", 0)), "#059669"),
    ]
    for idx, (title, value, color) in enumerate(stats):
        r_idx, c_idx = divmod(idx, 3)
        card = tk.Frame(stats_row, bg=THEME["surface"], bd=1, relief="solid")
        card.grid(row=r_idx, column=c_idx, sticky="nsew", padx=6, pady=6)
        stats_row.grid_columnconfigure(c_idx, weight=1)
        
        tk.Frame(card, bg=color, height=4).pack(fill="x")
        tk.Label(card, text=title, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 3))
        tk.Label(card, text=value, bg=THEME["surface"], fg=color, font=("Times New Roman", 16, "bold")).pack(anchor="w", padx=14, pady=(0, 12))

    actions = tk.Frame(content_frame, bg=THEME["bg"])
    actions.pack(fill="x", pady=(0, 10))
    style_button(actions, "Làm mới", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 8))
    style_button(actions, "Báo cáo doanh thu chi tiết", "#0f766e", lambda: open_revenue_report_window(app)).pack(side="left", padx=(0, 8))

    style = ttk.Style(app["root"])
    style.configure("Report.TNotebook", background=THEME["bg"], borderwidth=0)
    style.configure(
        "Report.TNotebook.Tab",
        padding=(16, 8),
        font=("Times New Roman", 11, "bold"),
        background=THEME["heading_bg"],
        foreground=THEME["text"],
    )
    style.map(
        "Report.TNotebook.Tab",
        background=[("selected", THEME["surface"])],
        foreground=[("selected", THEME["primary"])],
    )

    notebook = ttk.Notebook(content_frame, style="Report.TNotebook")
    notebook.pack(fill="both", expand=True)

    # Tab 1: Bảng dữ liệu
    table_tab = tk.Frame(notebook, bg=THEME["surface"])
    notebook.add(table_tab, text="Bảng dữ liệu")

    summary_wrap = tk.Frame(table_tab, bg=THEME["surface"], bd=1, relief="solid")
    summary_wrap.pack(fill="both", expand=True)
    tk.Label(summary_wrap, text="Tổng hợp booking và doanh thu theo tour", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 14, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

    cols = ("ma", "ten", "booking", "hieuluc", "phaithu", "dathu", "hoantien", "thucnhan", "conno")
    tv = ttk.Treeview(summary_wrap, columns=cols, show="headings", height=8)
    headers = [
        ("ma", "Mã tour", 80), 
        ("ten", "Tên tour", 230), 
        ("booking", "Tổng BK", 85), 
        ("hieuluc", "BK hiệu lực", 95), 
        ("phaithu", "Tổng phải thu", 125),
        ("dathu", "Đã thu", 115), 
        ("hoantien", "Hoàn/Trừ", 115), 
        ("thucnhan", "Thực nhận", 125), 
        ("conno", "Còn nợ", 115)
    ]
    for c, t, w in headers:
        tv.heading(c, text=t)
        anchor_val = "w" if c == "ten" else ("e" if c in ("booking", "hieuluc", "phaithu", "dathu", "hoantien", "thucnhan", "conno") else "center")
        tv.column(c, width=w, anchor=anchor_val, stretch=(c == "ten"))
    for row in report.get("by_tour", []):
        tv.insert(
            "", 
            "end", 
            values=(
                row.get("maTour", ""), 
                row.get("tenTour", ""), 
                row.get("tongBooking", 0), 
                row.get("bookingHieuLuc", 0), 
                format_currency(row.get("tongPhaiThu", row.get("doanhThuDuKien", 0))),
                format_currency(row.get("daThu", 0)), 
                format_currency(row.get("hoanTien", 0)), 
                format_currency(row.get("doanhThuThuan", 0)), 
                format_currency(row.get("conNo", 0))
            )
        )
    sy = ttk.Scrollbar(summary_wrap, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(summary_wrap, orient="horizontal", command=tv.xview)
    bind_autohide_scrollbar(tv, sy, "vertical")
    bind_autohide_scrollbar(tv, sx, "horizontal")
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
    sy.pack(side="right", fill="y", padx=(0, 12), pady=(0, 12))
    sx.pack(side="bottom", fill="x", padx=(12, 12), pady=(0, 12))
    apply_zebra(tv)

    # Tab 2: Biểu đồ trực quan
    chart_tab = tk.Frame(notebook, bg=THEME["surface"])
    notebook.add(chart_tab, text="Biểu đồ trực quan")

    chart_wrapper = tk.Frame(chart_tab, bg=THEME["surface"])
    chart_wrapper.pack(fill="both", expand=True, padx=15, pady=15)
    _render_matplotlib_charts(chart_wrapper, report)

    # Tạo status card ngoài canvas
    update_admin_status_card(app, "report", "Đang ở Báo cáo tổng hợp", THEME["primary"])

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
    "status_bg": "#e8eef8",
    "header_bg": "#ffffff",
    "heading_bg": "#e2e8f0",
    "note_bg": "#fff7ed",
    "note_fg": "#9a3412",
    "zebra_even": "#f8fbff",
    "zebra_odd": "#ffffff",
}

TOUR_STATUSES = list(TOUR_STATUS_CHOICES)
BOOKING_STATUSES = ["Mới tạo", "Đã cọc", "Đã thanh toán", "Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]


def refresh_tour_lifecycle_for_admin(app, show_popup=False):
    changes = refresh_all_tour_statuses(app["ql"])
    if changes:
        app["ql"].save()
        if show_popup:
            lines = ["Hệ thống đã tự động cập nhật trạng thái tour:"]
            for item in changes:
                lines.append(
                    f"- {item.get('maTour', '')} | {item.get('tenTour', '')}: "
                    f"{item.get('oldStatus', '')} -> {item.get('newStatus', '')} | "
                    f"Lý do: {item.get('reason', 'điều chỉnh theo nghiệp vụ')}"
                )
            messagebox.showinfo("Cập nhật trạng thái tour", "\n".join(lines))
    return changes
HDV_STATUSES = ["Sẵn sàng", "Đã phân công", "Đang dẫn tour", "Tạm nghỉ"]

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
    "admin": {"username": "admin", "password": "123"}
}

# =========================
# DATA STORE
# =========================
# -----------------------------------------------------------------------------
# Hàm bọc (wrapper) cho bộ chuẩn hóa dữ liệu đánh giá.
# Mục đích: đồng nhất cấu trúc review trước khi lưu/hiển thị trong hệ thống.
# Hàm này không tự xử lý logic mới mà ủy quyền sang core.normalizers.
# -----------------------------------------------------------------------------
def normalize_review_item(r, datastore=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_review_item` (normalize review item).
    Tham số:
        r: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = core_normalize_review_item(
        r,
        include_rating=True,
        include_ma_hdv=True,
    )

    ma_tour = str(normalized.get("maTour", "")).strip()
    ten_tour = str((r or {}).get("tenTour", "")).strip()
    if not ten_tour and datastore is not None and ma_tour:
        tour = datastore.find_tour(ma_tour)
        ten_tour = str((tour or {}).get("ten", "")).strip()
    normalized["tenTour"] = ten_tour

    # Tự động truy vết maHDV và tenHDV nếu bị thiếu
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


# -----------------------------------------------------------------------------
# Hàm bọc để chuẩn hóa một bản ghi thông báo.
# Có truyền kèm datastore khi cần đối chiếu dữ liệu liên quan trong quá trình chuẩn hóa.
# -----------------------------------------------------------------------------
def normalize_notification_item(n, datastore=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_notification_item` (normalize notification item).
    Tham số:
        n: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return core_normalize_notification_item(n, datastore=datastore)
# =============================================================================
# Lớp kho dữ liệu chính của màn hình Admin.
# Kế thừa JSONDataStore để đọc/ghi dữ liệu trực tiếp từ file JSON,
# đồng thời truyền vào các hàm chuẩn hóa review/thông báo đặc thù của module này.
# =============================================================================
class DataStore(JSONDataStore):
    def __init__(self, path=DATA_FILE, rev_path=REVIEWS_FILE, notif_path=NOTIF_FILE):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `__init__` (  init  ).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            rev_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            notif_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        super().__init__(
            path=path,
            rev_path=rev_path,
            notif_path=notif_path,
            default_data=DEFAULT_DATA,
            normalize_review_item=normalize_review_item,
            normalize_notification_item=normalize_notification_item,
        )


# =========================
# HELPERS
# =========================
# Xóa toàn bộ widget con trong vùng nội dung trung tâm để chuẩn bị render tab mới.
def clear_container(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `clear_container` (clear container).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    for widget in app["container"].winfo_children():
        widget.destroy()

# Cập nhật nội dung thanh trạng thái phía dưới giao diện.
# Nếu có truyền màu, đồng thời đổi màu chữ để nhấn mạnh trạng thái hiện tại.
def set_status(app, text, color=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `set_status` (set status).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    app["status_var"].set(text)
    if color:
        app["status_label"].config(fg=color)


# Tải lại dữ liệu từ datastore, sau đó render lại đúng tab admin đang mở.
# Dùng khi cần làm mới giao diện sau khi CRUD hoặc sau khi dữ liệu thay đổi từ nơi khác.
def reload_admin_current_tab(app, success_message="Đã tải lại dữ liệu"):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `reload_admin_current_tab` (reload admin current tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        success_message: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    app["ql"].load()
    current_tab = app.get("current_tab", "dashboard")
    handler = get_admin_tab_handler(current_tab)
    handler(app)
    set_status(app, success_message, THEME["success"])

# Tạo nhanh một nút theo bộ giao diện thống nhất của toàn module admin.
# Việc gom style vào một hàm giúp các nút đồng nhất màu sắc, font và hành vi.
def style_button(parent, text, bg, command, fg="white"):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `style_button` (style button).
    Tham số:
        parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        bg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        command: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
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


# Tạo status card thống nhất cho các tab Admin.
# Status card hiển thị trạng thái trang và số lượng dữ liệu đang hiển thị.
def create_admin_status_card(app, key, default_text):
    """
    Tạo một status card trong trang Admin với style thống nhất.
    
    Args:
        app: Dictionary chứa các thành phần giao diện của ứng dụng
        key: Khóa định danh cho status card (vd: "booking", "tour", "review")
        default_text: Nội dung text mặc định hiển thị trong status card
    
    Returns:
        StringVar: Biến chứa text của status card để cập nhật sau này
    """
    status_card = tk.Frame(
        app["container"],
        bg="#eef6ff",
        highlightbackground="#c9defa",
        highlightthickness=1,
    )
    status_card.pack(fill="x", pady=(8, 0))
    
    var_name = f"{key}_status_text_var"
    label_name = f"{key}_status_card_label"
    
    app[var_name] = tk.StringVar(value=default_text)
    app[label_name] = tk.Label(
        status_card,
        textvariable=app[var_name],
        bg="#eef6ff",
        fg="#2563eb",
        font=("Times New Roman", 13, "italic"),
        anchor="w",
        padx=20,
        pady=6,
    )
    app[label_name].pack(anchor="w")
    
    return app[var_name]


# Cập nhật nội dung status card và thanh trạng thái dưới cùng.
def update_admin_status_card(app, key, text, color=None):
    """
    Cập nhật nội dung của status card đã được tạo.
    
    Args:
        app: Dictionary chứa các thành phần giao diện của ứng dụng
        key: Khóa định danh của status card cần cập nhật
        text: Nội dung text mới
        color: Màu text cho thanh trạng thái dưới (tùy chọn)
    """
    var_name = f"{key}_status_text_var"
    if var_name in app:
        app[var_name].set(text)
    set_status(app, text, color or THEME["primary"])


FORM_COMBOBOX_STYLE = "AdminForm.TCombobox"
POPUP_FORM_SCROLLBAR_STYLE = "PopupForm.Vertical.TScrollbar"


def style_form_entry_widget(widget):
    """
    Làm mềm giao diện ô nhập liệu trong các form popup.
    """
    widget.configure(
        relief="flat",
        bd=0,
        bg="#f8fafc",
        fg=THEME["text"],
        insertbackground=THEME["text"],
        highlightthickness=1,
        highlightbackground="#cbd5e1",
        highlightcolor="#2563eb",
    )


def style_form_text_widget(widget):
    """
    Làm mềm giao diện ô text nhiều dòng trong các form popup.
    """
    widget.configure(
        relief="flat",
        bd=0,
        bg="#f8fafc",
        fg=THEME["text"],
        insertbackground=THEME["text"],
        highlightthickness=1,
        highlightbackground="#cbd5e1",
        highlightcolor="#2563eb",
        padx=8,
        pady=6,
    )


# Thiết lập font mặc định cho toàn bộ ứng dụng Tkinter và cho các widget ttk.
def configure_ui_fonts(root):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `configure_ui_fonts` (configure ui fonts).
    Tham số:
        root: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
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

# Tô màu xen kẽ từng dòng của Treeview để bảng dữ liệu dễ nhìn hơn.
def apply_zebra(tree):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `apply_zebra` (apply zebra).
    Tham số:
        tree: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree.tag_configure("odd", background=THEME["zebra_odd"])
    tree.tag_configure("even", background=THEME["zebra_even"])
    for i, item in enumerate(tree.get_children()):
        tree.item(item, tags=(("even" if i % 2 == 0 else "odd"),))

# Hàm chuyển tiếp sang validator lõi để kiểm tra số điện thoại hợp lệ.
def is_valid_phone(phone):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_phone` (is valid phone).
    Tham số:
        phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return core_is_valid_phone(phone)

# Hàm chuyển tiếp sang validator lõi để kiểm tra email hợp lệ.
def is_valid_email(email):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_email` (is valid email).
    Tham số:
        email: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return core_is_valid_email(email)


def register_phone_validate(entry_widget):
    validator = entry_widget.register(lambda value: (value.isdigit() and len(value) <= 10) or value == "")
    entry_widget.configure(validate="key", validatecommand=(validator, "%P"))


def normalize_itinerary_text(value):
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()


def parse_itinerary_text(raw_text):
    text = normalize_itinerary_text(raw_text)
    if not text:
        return []
    result = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for idx, line in enumerate(lines, 1):
        title = line
        places = []
        desc = line
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                title = parts[0] or f"Ngày {idx}"
                places = [p.strip() for p in parts[1].split(",") if p.strip()]
                desc = parts[2] if len(parts) >= 3 and parts[2].strip() else line
        result.append(
            {
                "ngay": f"Ngày {idx}",
                "tieuDe": title,
                "diaDiem": places,
                "moTa": desc,
            }
        )
    return result


def itinerary_to_text(lich_trinh):
    if isinstance(lich_trinh, str):
        return normalize_itinerary_text(lich_trinh)
    if not isinstance(lich_trinh, list):
        return ""
    lines = []
    for item in lich_trinh:
        if not isinstance(item, dict):
            continue
        title = str(item.get("tieuDe", "")).strip() or str(item.get("ngay", "")).strip() or "Lịch trình"
        places = item.get("diaDiem", [])
        if isinstance(places, str):
            places = [p.strip() for p in places.split(",") if p.strip()]
        place_text = ", ".join(str(p).strip() for p in places if str(p).strip())
        desc = str(item.get("moTa", "")).strip()
        lines.append(f"{title} | {place_text} | {desc}" if place_text else f"{title} | {desc}")
    return "\n".join(lines).strip()


# Chuyển chuỗi ngày theo định dạng dd/mm/yyyy sang đối tượng datetime; lỗi thì trả về None.
def parse_ddmmyyyy(date_text):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `parse_ddmmyyyy` (parse ddmmyyyy).
    Tham số:
        date_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return parse_tour_ddmmyyyy(date_text)

# Kiểm tra chuỗi ngày có đúng định dạng dd/mm/yyyy hay không.
def is_valid_date(date_text):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_date` (is valid date).
    Tham số:
        date_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return parse_ddmmyyyy(date_text) is not None

# Ép kiểu sang số nguyên an toàn; nếu lỗi thì trả về 0 để tránh làm hỏng luồng xử lý.
def safe_int(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `safe_int` (safe int).
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
        return int(value)
    except (ValueError, TypeError):
        return 0


# Đá»‹nh dạng số tiền theo kiểu hiển thị Việt Nam, ví dụ: 1000000 -> 1.000.000đ.
def format_currency(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `format_currency` (format currency).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return f"{safe_int(value):,}đ".replace(",", ".")


def shorten_text(value, max_len=35):
    if value is None:
        return ""
    text = str(value)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _to_readable_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _first_non_empty(data, keys, default=""):
    for key in keys:
        value = data.get(key, "")
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip():
                return value.strip()
        elif str(value).strip():
            return value
    return default


def _map_popup_fields(data, field_order, field_labels):
    mapped = {}
    used = set()
    source = data if isinstance(data, dict) else {}
    for key in field_order:
        if key in source:
            mapped[fix_mojibake(field_labels.get(key, key))] = fix_mojibake(source.get(key))
            used.add(key)
    for key, value in source.items():
        if key in used:
            continue
        mapped[fix_mojibake(field_labels.get(key, key))] = fix_mojibake(value)
    return mapped


def build_admin_review_popup_data(app, review_data, row_index=None):
    review = dict(review_data or {})
    target = _first_non_empty(review, ("target", "doiTuong"), "HDV")
    target_id = _first_non_empty(review, ("target_id", "maHDV", "maTour"))
    ma_review = _first_non_empty(review, ("maReview", "id"))
    if not ma_review and row_index is not None:
        ma_review = f"REV{row_index + 1:02d}"

    ma_hdv = _first_non_empty(review, ("maHDV",))
    ten_hdv = _first_non_empty(review, ("tenHDV", "ten_hdv"))
    ma_tour = _first_non_empty(review, ("maTour",))
    ten_tour = _first_non_empty(review, ("tenTour", "ten_tour"))

    if not ma_hdv:
        if ma_tour:
            tour = app["ql"].find_tour(ma_tour)
            if tour:
                ma_hdv = str(tour.get("hdvPhuTrach", "")).strip()
        if not ma_hdv and review.get("maBooking"):
            bookings_list = getattr(app["ql"], "list_bookings", getattr(app["ql"], "data", {}).get("bookings", []))
            booking = next((b for b in bookings_list if str(b.get("maBooking", b.get("ma", ""))).strip().upper() == str(review.get("maBooking", "")).strip().upper()), None)
            if booking:
                b_tour = app["ql"].find_tour(booking.get("maTour"))
                if b_tour:
                    ma_hdv = str(b_tour.get("hdvPhuTrach", "")).strip()

    if ma_hdv and not ten_hdv:
        hdv = app["ql"].find_hdv(ma_hdv)
        if hdv:
            ten_hdv = str(hdv.get("tenHDV", "")).strip()

    if ma_tour and not ten_tour:
        tour = app["ql"].find_tour(ma_tour)
        ten_tour = (tour or {}).get("ten", "")

    if target == "HDV":
        ma_hdv = ma_hdv or target_id
    elif target == "Tour":
        ma_tour = ma_tour or target_id

    normalized = dict(review)
    normalized["maReview"] = ma_review
    normalized["maHDV"] = ma_hdv
    normalized["tenHDV"] = ten_hdv
    normalized["maTour"] = ma_tour
    normalized["tenTour"] = ten_tour
    normalized["target"] = target
    normalized["target_id"] = target_id
    normalized["rating"] = _first_non_empty(normalized, ("rating",), "")
    normalized["date"] = _first_non_empty(normalized, ("date", "ngayGui", "ngay", "thoiGian"), "")
    normalized["content"] = _first_non_empty(normalized, ("content", "noiDung", "comment", "danhGia"), "")
    normalized["fullname"] = _first_non_empty(normalized, ("fullname", "tenKhach", "hoTen"), "")
    normalized["username"] = _first_non_empty(normalized, ("username", "user"), "")
    # Ẩn các key kỹ thuật cũ để popup không hiển thị target/target_id.
    normalized.pop("target", None)
    normalized.pop("target_id", None)

    field_order = [
        "maReview",
        "maBooking",
        "maHDV",
        "tenHDV",
        "maTour",
        "tenTour",
        "username",
        "fullname",
        "date",
        "rating",
        "content",
        "adminReply",
        "adminReplyDate",
        "adminReplyBy",
        "trangThai",
    ]
    field_labels = {
        "maReview": "Mã đánh giá",
        "maBooking": "Mã Booking",
        "maHDV": "Mã HDV",
        "tenHDV": "Tên HDV",
        "maTour": "Mã tour",
        "tenTour": "Tên tour",
        "username": "Username khách",
        "fullname": "Tên khách",
        "date": "Ngày gửi",
        "rating": "Điểm đánh giá",
        "content": "Nội dung đánh giá",
        "noiDung": "Nội dung đánh giá",
        "comment": "Nội dung đánh giá",
        "adminReply": "Phản hồi Admin",
        "adminReplyDate": "Ngày phản hồi",
        "adminReplyBy": "Người phản hồi",
        "trangThai": "Trạng thái",
    }
    return _map_popup_fields(normalized, field_order, field_labels)


def _notification_type_label(notification: dict) -> str:
    event_type = _first_non_empty(notification, ("eventType", "loai"), "")
    lookup = {
        "booking_created": "Booking mới",
        "payment_success": "Thanh toán thành công",
        "tour_cancelled": "Tour bị hủy",
        "tour_completed": "Tour đã kết thúc",
        "guide_assigned": "Phân công hướng dẫn viên",
        "guide_broadcast": "Thông báo từ hướng dẫn viên",
    }
    normalized = str(event_type).strip().lower()
    return lookup.get(normalized, "")


def build_admin_notification_popup_data(app, notification_data):
    notification = enrich_notification_hdv_info(app, notification_data)
    ma_hdv = _first_non_empty(notification, ("maHDV",))
    ten_hdv = _first_non_empty(notification, ("tenHDV",))
    ma_tour = _first_non_empty(notification, ("maTour",))
    ten_tour = _first_non_empty(notification, ("tenTour",))

    if ma_hdv and not ten_hdv:
        hdv = app["ql"].find_hdv(ma_hdv)
        ten_hdv = (hdv or {}).get("tenHDV", "")
    if ma_tour and not ten_tour:
        tour = app["ql"].find_tour(ma_tour)
        ten_tour = (tour or {}).get("ten", "")

    normalized = dict(notification)
    normalized["maHDV"] = ma_hdv
    normalized["tenHDV"] = ten_hdv
    normalized["maTour"] = ma_tour
    normalized["tenTour"] = ten_tour
    normalized["loaiThongBao"] = _notification_type_label(notification)
    normalized["date"] = _first_non_empty(notification, ("date", "ngayGui", "ngay", "thoiGian"), "")
    normalized["content"] = _first_non_empty(notification, ("content", "noiDung", "thongBao"), "")
    # Ẩn key kỹ thuật trong popup chi tiết, chỉ giữ thông tin hiển thị thân thiện.
    normalized.pop("eventType", None)
    normalized.pop("loai", None)

    field_order = ["maHDV", "tenHDV", "maTour", "tenTour", "loaiThongBao", "date", "content"]
    field_labels = {
        "maHDV": "Mã HDV",
        "tenHDV": "Tên HDV",
        "maTour": "Mã tour",
        "tenTour": "Tên tour",
        "loaiThongBao": "Loại thông báo",
        "date": "Ngày gửi",
        "content": "Nội dung thông báo",
        "noiDung": "Nội dung thông báo",
        "thongBao": "Nội dung thông báo",
    }
    return _map_popup_fields(normalized, field_order, field_labels)


def enrich_notification_hdv_info(app, notification):
    n = dict(notification or {})

    ma_hdv = str(n.get("maHDV", "")).strip()
    ten_hdv = str(n.get("tenHDV", "")).strip()
    ma_tour = str(n.get("maTour", "")).strip()

    if not ma_tour:
        ma_booking = str(n.get("maBooking", "")).strip()
        if ma_booking:
            booking = next(
                (
                    b for b in app["ql"].list_bookings
                    if str(b.get("maBooking", "")).strip() == ma_booking
                ),
                None,
            )
            if booking:
                ma_tour = str(booking.get("maTour", "")).strip()
                n["maTour"] = ma_tour

    if not ma_hdv and ma_tour:
        tour = app["ql"].find_tour(ma_tour)
        if tour:
            ma_hdv = str(tour.get("hdvPhuTrach", "")).strip()
            n["maHDV"] = ma_hdv
            if not n.get("tenTour"):
                n["tenTour"] = str(tour.get("ten", "")).strip()

    if ma_hdv and not ten_hdv:
        hdv = app["ql"].find_hdv(ma_hdv)
        if hdv:
            ten_hdv = str(hdv.get("tenHDV", "")).strip()
            n["tenHDV"] = ten_hdv

    return n


def show_detail_popup(root, title, data_dict, geometry="900x620", minsize=(760, 520), wraplength=650):
    top = tk.Toplevel(root)
    top.title(fix_mojibake(title))
    top.geometry(geometry)
    top.minsize(*minsize)
    top.configure(bg=THEME["bg"])
    top.transient(root)
    top.grab_set()

    shell = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    shell.pack(fill="both", expand=True, padx=16, pady=(16, 10))

    canvas = tk.Canvas(shell, bg=THEME["surface"], highlightthickness=0, bd=0)
    inner = tk.Frame(canvas, bg=THEME["surface"])
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    sy = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
    bind_autohide_scrollbar(canvas, sy, "vertical")
    canvas.pack(side="left", fill="both", expand=True)

    def _on_inner_configure(_event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        canvas.itemconfigure(window_id, width=max(event.width - 2, 1))

    inner.bind("<Configure>", _on_inner_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    tk.Label(
        inner,
        text=fix_mojibake(title),
        bg=THEME["surface"],
        fg=THEME["text"],
        font=("Times New Roman", 18, "bold"),
        anchor="w",
    ).pack(fill="x", padx=18, pady=(14, 10))

    value_labels = []
    hidden_keys = {"target", "target_id"}
    for key, raw_value in (data_dict or {}).items():
        if str(key).strip().lower() in hidden_keys:
            continue
        row = tk.Frame(inner, bg=THEME["surface"])
        row.pack(fill="x", padx=18, pady=5)
        tk.Label(
            row,
            text=f"{fix_mojibake(key)}:",
            width=22,
            anchor="nw",
            justify="left",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=("Times New Roman", 12, "bold"),
        ).pack(side="left", padx=(0, 8))
        value_label = tk.Label(
            row,
            text=_to_readable_text(fix_mojibake(raw_value)),
            wraplength=wraplength,
            justify="left",
            anchor="w",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=("Times New Roman", 12),
        )
        value_label.pack(side="left", fill="x", expand=True)
        value_labels.append(value_label)

    def _refresh_wraplength(_event=None):
        current = max(wraplength, top.winfo_width() - 320)
        for label in value_labels:
            label.configure(wraplength=current)

    top.bind("<Configure>", _refresh_wraplength)
    _refresh_wraplength()

    footer = tk.Frame(top, bg=THEME["bg"])
    footer.pack(fill="x", padx=16, pady=(0, 16))
    style_button(footer, "Đóng", THEME["danger"], top.destroy).pack(fill="x")


# Lấy username admin hiện tại để ghi log thao tác CRUD và các hành động nghiệp vụ.
def get_admin_actor(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `get_admin_actor` (get admin actor).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return str(app["ql"].data.get("admin", {}).get("username", "admin")).strip() or "admin"


# Chuẩn hóa họ tên: bỏ khoảng trắng thừa và viết hoa chữ cái đầu từng từ.
def normalize_name_case(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_name_case` (normalize name case).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return normalize_title_case(value)


BOOKING_CANCEL_STATUSES = {"Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}


def build_tour_display_label(datastore, ma_tour):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_tour_display_label` (build tour display label).
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
    code = normalize_code(ma_tour)
    if not code:
        return ""
    tour = datastore.find_tour(code) if datastore else None
    name = normalize_spaces(tour.get("ten", "")) if isinstance(tour, dict) else ""
    return f"{code} - {name}" if name else code


def build_hdv_display_label(datastore, ma_hdv):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_hdv_display_label` (build hdv display label).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    code = normalize_code(ma_hdv)
    if not code:
        return ""
    guide = datastore.find_hdv(code) if datastore else None
    name = normalize_spaces(guide.get("tenHDV", "")) if isinstance(guide, dict) else ""
    return f"{code} - {name}" if name else code


# Chuyển đối tượng được đánh giá (HDV/Tour/Công ty) sang chuỗi hiển thị thân thiện.
# Nếu có thể, hàm sẽ tra cứu thêm tên thật từ datastore để tránh chỉ hiện mã.
def format_review_target(datastore, review, include_code=False):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `format_review_target` (format review target).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        review: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        include_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    target = str(review.get("target", "") or review.get("doiTuong", "") or "Công ty").strip()
    target_id = str(review.get("target_id", "") or review.get("maHDV", "") or review.get("maTour", "")).strip()

    if target == "HDV":
        hdv = datastore.find_hdv(target_id) if target_id else None
        hdv_name = str(hdv.get("tenHDV", "")).strip() if hdv else ""
        if hdv_name and include_code and target_id:
            return f"HDV: {hdv_name} ({target_id})"
        if hdv_name:
            return f"HDV: {hdv_name}"
        return f"HDV: {target_id}" if target_id else "HDV"

    if target == "Tour":
        tour = datastore.find_tour(target_id) if target_id else None
        tour_name = str(tour.get("ten", "")).strip() if tour else ""
        if tour_name and include_code and target_id:
            return f"Tour: {tour_name} ({target_id})"
        if tour_name:
            return f"Tour: {tour_name}"
        return f"Tour: {target_id}" if target_id else "Tour"

    return target or "Công ty"

# Tự động ẩn thanh cuộn khi nội dung chưa tràn khung hiển thị.
def bind_autohide_scrollbar(widget, scrollbar, orient="vertical"):
    """
    Mục đích:
        Tự động ẩn/hiện scrollbar theo trạng thái tràn nội dung.
    """
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


# Tạo một form có thể cuộn theo trục dọc.
# Rất hữu ích cho các cửa sổ nhập liệu dài như HDV, tour, booking, voucher.
def create_scrollable_form(parent, bg):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_scrollable_form` (create scrollable form).
    Tham số:
        parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        bg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(
        outer,
        orient="vertical",
        command=canvas.yview,
        style=POPUP_FORM_SCROLLBAR_STYLE,
    )
    bind_autohide_scrollbar(canvas, v_scroll, "vertical")
    canvas.pack(side="left", fill="both", expand=True)

    content = tk.Frame(canvas, bg=bg)
    win = canvas.create_window((0, 0), window=content, anchor="nw")

    def on_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_configure` (on configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_canvas_configure` (on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfig(win, width=event.width)

    content.bind("<Configure>", on_configure)
    canvas.bind("<Configure>", on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    parent.after(200, lambda: content.bind_all("<MouseWheel>", _on_mousewheel))
    return outer, content


# =========================
# DASHBOARD
# =========================
# Render tab Dashboard của admin.
# Tab này tổng hợp số liệu nhanh, tác vụ nhanh và các ghi chú điều hành dựa trên dữ liệu hiện tại.
def dashboard_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `dashboard_tab` (dashboard tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)
    ql = app["ql"]
    root = app.get("root")
    current_height = root.winfo_height() if root else 820
    compact_mode = current_height < 820
    stats_gap = 12 if compact_mode else 18
    stat_title_pad = (12, 5) if compact_mode else (16, 6)
    stat_value_pad = (0, 12) if compact_mode else (0, 16)
    side_section_pad = 10 if compact_mode else 15
    side_gap = 6 if compact_mode else 8
    notes_limit = 5 if compact_mode else 7

    # tk.Label(
    #     app["container"],
    #     text="HỆ THỐNG VIETNAM TRAVEL",
    #     font=("Times New Roman", 22, "bold"),
    #     bg=THEME["bg"],
    #     fg=THEME["text"],
    # ).pack(anchor="w", pady=(0, 20))

    # Tạo Canvas và Scrollbar để dashboard có thể scroll khi nội dung dài
    canvas_wrapper = tk.Frame(app["container"], bg=THEME["bg"])
    canvas_wrapper.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(canvas_wrapper, bg=THEME["bg"], highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_wrapper, orient="vertical", command=canvas.yview)
    
    dashboard_body = tk.Frame(canvas, bg=THEME["bg"])
    
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Sử dụng auto-hide scrollbar
    bind_autohide_scrollbar(canvas, scrollbar, "vertical")
    
    canvas.pack(side="left", fill="both", expand=True)
    
    canvas_window = canvas.create_window((0, 0), window=dashboard_body, anchor="nw")
    
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)
    
    dashboard_body.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)
    
    # Hỗ trợ scroll bằng chuột
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    dashboard_body.grid_columnconfigure(0, weight=1)

    # Thêm padding cho nội dung
    content_frame = tk.Frame(dashboard_body, bg=THEME["bg"])
    content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    content_frame.grid_columnconfigure(0, weight=1)

    stats = tk.Frame(content_frame, bg=THEME["bg"])
    stats.grid(row=0, column=0, sticky="ew", pady=(0, stats_gap))

    revenue = sum(safe_int(t.get("gia", 0)) * ql.get_occupied_seats(t["ma"]) for t in ql.list_tours)
    stat_items = [
        ("Doanh thu tạm tính", f"{revenue:,}đ".replace(",", "."), THEME["primary"]),
        ("Tổng tour", str(len(ql.list_tours)), THEME["warning"]),
        ("Tổng HDV", str(len(ql.list_hdv)), THEME["success"]),
        ("Tổng booking", str(len(ql.list_bookings)), THEME["danger"]),
    ]

    for i in range(4):
        stats.grid_columnconfigure(i, weight=1, uniform="dashboard_stats")

    for idx, (title, value, color) in enumerate(stat_items):
        card = tk.Frame(stats, bg=THEME["surface"], bd=1, relief="solid")
        card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0 if idx == 3 else 8))
        tk.Label(card, text=title, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 13, "bold")).pack(anchor="w", padx=16, pady=stat_title_pad)
        tk.Label(card, text=value, bg=THEME["surface"], fg=color, font=("Times New Roman", 22, "bold")).pack(anchor="w", padx=16, pady=stat_value_pad)

    lower = tk.Frame(content_frame, bg=THEME["bg"])
    lower.grid(row=1, column=0, sticky="ew", pady=(0, 0), padx=0)
    lower.grid_rowconfigure(0, weight=1, minsize=235)
    lower.grid_rowconfigure(1, weight=0)
    lower.grid_columnconfigure(0, weight=1, uniform="dashboard_lower")
    lower.grid_columnconfigure(1, weight=1, uniform="dashboard_lower")

    left = tk.LabelFrame(lower, text="Tác vụ quản trị nhanh", font=("Times New Roman", 14, "bold"), bg=THEME["surface"], bd=1, relief="solid", padx=side_section_pad, pady=side_section_pad)
    style_button(left, "Thêm HDV mới", THEME["success"], lambda: open_hdv_form(app)).pack(fill="x", pady=4 if compact_mode else 5)
    style_button(left, "Tạo tour mới", THEME["warning"], lambda: open_tour_form(app)).pack(fill="x", pady=4 if compact_mode else 5)
    style_button(left, "Báo cáo doanh thu", "#0f766e", lambda: open_revenue_report_window(app)).pack(fill="x", pady=4 if compact_mode else 5)
    style_button(left, "Làm mới Dashboard", "#0ea5e9", lambda: dashboard_tab(app)).pack(fill="x", pady=4 if compact_mode else 5)

    right = tk.LabelFrame(lower, text="Ghi chú điều hành", font=("Times New Roman", 14, "bold"), bg=THEME["note_bg"], fg=THEME["note_fg"], bd=1, relief="solid", padx=side_section_pad, pady=side_section_pad)

    dynamic_notes = []

    for t in ql.list_tours:
        occupied = ql.get_occupied_seats(t["ma"])
        total = safe_int(t["khach"])
        tour_status = normalize_tour_status(t.get("trangThai", ""))

        if tour_status == TOUR_STATUS_FULL:
            dynamic_notes.append(f"• Tour {t['ten']} đã đủ chỗ đăng ký.")
        elif tour_status == TOUR_STATUS_STARTED:
            dynamic_notes.append(f"• Tour {t['ten']} đã khởi hành.")
        elif tour_status == TOUR_STATUS_COMPLETED:
            dynamic_notes.append(f"• Tour {t['ten']} đã hoàn thành.")
        elif tour_status == TOUR_STATUS_CANCELLED:
            dynamic_notes.append(f"• Tour {t['ten']} đã hủy.")
        else:
            dynamic_notes.append(f"• Tour {t['ten']} còn {max(total - occupied, 0)} chỗ trống.")
            if total > 0 and occupied < total / 2 and tour_status == TOUR_STATUS_OPEN:
                dynamic_notes.append(f"• Tour {t['ten']} có nguy cơ không đủ khách (mới có {occupied} khách).")

    for t in ql.list_tours:
        if t.get("hdvPhuTrach"):
            hdv = ql.find_hdv(t["hdvPhuTrach"])
            if hdv:
                dynamic_notes.append(f"• HDV {hdv['tenHDV']} phụ trách tour {t['ten']} từ {t['ngay']}.")
        else:
            dynamic_notes.append(f"• Cần phân công HDV cho tour {t['ten']} ({t['ngay']}).")

    for h in ql.list_hdv:
        if h["trangThai"] == "Tạm nghỉ":
            dynamic_notes.append(f"• HDV {h['tenHDV']} hiện đang tạm nghỉ.")

    note_text = "\n".join(dynamic_notes[:notes_limit]) if dynamic_notes else "• Hiện không có ghi chú điều hành mới."

    note_label = tk.Label(
        right,
        text=note_text,
        justify="left",
        anchor="nw",
        bg=THEME["note_bg"],
        fg=THEME["note_fg"],
        font=("Times New Roman", 13),
    )
    note_label.pack(anchor="nw", fill="both", expand=True)
    left.grid_propagate(True)
    right.grid_propagate(True)

    def arrange_dashboard_boxes(_event=None):
        try:
            width = content_frame.winfo_width()
            left.grid_forget()
            right.grid_forget()

            if width and width < 760:
                lower.grid_columnconfigure(0, weight=1, uniform="")
                lower.grid_columnconfigure(1, weight=0, uniform="")
                lower.grid_rowconfigure(0, weight=0, minsize=0)
                lower.grid_rowconfigure(1, weight=0, minsize=0)
                left.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, side_gap))
                right.grid(row=1, column=0, sticky="ew", padx=0, pady=(side_gap, 0))
            else:
                lower.grid_columnconfigure(0, weight=1, uniform="dashboard_lower")
                lower.grid_columnconfigure(1, weight=1, uniform="dashboard_lower")
                lower.grid_rowconfigure(0, weight=1, minsize=235)
                lower.grid_rowconfigure(1, weight=0, minsize=0)
                left.grid(row=0, column=0, sticky="nsew", padx=(0, side_gap), pady=0)
                right.grid(row=0, column=1, sticky="nsew", padx=(side_gap, 0), pady=0)
        except tk.TclError:
            return

    def sync_note_wrap(_event=None):
        try:
            note_label.configure(wraplength=max(260, right.winfo_width() - 40))
        except tk.TclError:
            return

    # Cleanup mousewheel binding khi dashboard bị destroy
    def cleanup_mousewheel():
        try:
            canvas.unbind_all("<MouseWheel>")
        except:
            pass
    
    canvas_wrapper.bind("<Destroy>", lambda e: cleanup_mousewheel())

    content_frame.bind("<Configure>", arrange_dashboard_boxes)
    lower.bind("<Configure>", arrange_dashboard_boxes)
    right.bind("<Configure>", sync_note_wrap)
    content_frame.after_idle(arrange_dashboard_boxes)
    note_label.after_idle(sync_note_wrap)

    set_status(app, f"Đang ở Dashboard - Hiển thị {len(stat_items)} chỉ số", THEME["primary"])


# =========================
# HDV MANAGEMENT
# =========================
# Kiểm tra dữ liệu đầu vào của hướng dẫn viên trước khi lưu.
# Bao gồm: bắt buộc trường, định dạng mã, độ dài tên/mật khẩu, trùng số điện thoại/email,
# phạm vi năm kinh nghiệm và ràng buộc giới tính.
def validate_hdv(app, form_data, old_ma=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_hdv` (validate hdv).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        form_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_ma: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    form_data["maHDV"] = normalize_code(form_data.get("maHDV", ""))
    form_data["tenHDV"] = normalize_name_case(form_data.get("tenHDV", ""))
    form_data["sdt"] = normalize_spaces(form_data.get("sdt", ""))
    form_data["email"] = normalize_email(form_data.get("email", ""))
    form_data["kn"] = normalize_spaces(form_data.get("kn", ""))
    form_data["gioiTinh"] = normalize_spaces(form_data.get("gioiTinh", ""))
    form_data["cccd"] = normalize_spaces(form_data.get("cccd", ""))
    form_data["khuVuc"] = normalize_name_case(form_data.get("khuVuc", ""))
    form_data["trangThai"] = normalize_spaces(form_data.get("trangThai", ""))
    form_data["password"] = normalize_spaces(form_data.get("password", ""))

    required = ["maHDV", "tenHDV", "sdt", "email", "kn", "gioiTinh", "khuVuc", "trangThai"]
    if old_ma is None:
        required.append("password")

    if not all(form_data.get(k, "").strip() for k in required):
        return False, "Vui lòng nhập đầy đủ thông tin HDV."

    if not re.fullmatch(r"HDV\d{2,}", form_data["maHDV"]):
        return False, "Mã HDV phải theo dạng HDV01, HDV02..."

    if len(form_data["tenHDV"].strip()) < 3:
        return False, "Tên HDV quá ngắn."
    if form_data.get("password") and len(form_data["password"].strip()) < 3:
        return False, "Mật khẩu quá ngắn."

    if not is_valid_phone(form_data["sdt"]):
        return False, "Số điện thoại không hợp lệ."
    if not is_valid_email(form_data["email"]):
        return False, "Email không hợp lệ."

    if not form_data["kn"].isdigit() or not (0 <= int(form_data["kn"]) <= 50):
        return False, "Kinh nghiệm phải là số từ 0 đến 50."

    if form_data.get("gioiTinh") not in {"Nam", "Nữ"}:
        return False, "Giới tính chỉ hỗ trợ Nam hoặc Nữ."
    if form_data["cccd"]:
        if not form_data["cccd"].isdigit():
            return False, "CCCD chỉ được chứa chữ số."
        if len(form_data["cccd"]) > 12:
            return False, "CCCD không được vượt quá 12 chữ số."

    for h in app["ql"].list_hdv:
        if normalize_code(h.get("maHDV", "")) == form_data["maHDV"] and form_data["maHDV"] != normalize_code(old_ma):
            return False, "Mã HDV đã tồn tại."
        if normalize_spaces(h.get("sdt", "")) == form_data["sdt"] and normalize_code(h.get("maHDV", "")) != normalize_code(old_ma):
            return False, "Số điện thoại đã tồn tại."
        if normalize_email(h.get("email", "")) == form_data["email"] and normalize_code(h.get("maHDV", "")) != normalize_code(old_ma):
            return False, "Email đã tồn tại."
        if form_data["cccd"] and normalize_spaces(h.get("cccd", "")) == form_data["cccd"] and normalize_code(h.get("maHDV", "")) != normalize_code(old_ma):
            return False, "CCCD đã tồn tại."

    return True, ""

def refresh_hdv(app, keyword=""):
    tree = app.get("tv_hdv")
    if not tree:
        return

    for item in tree.get_children():
        tree.delete(item)

    rows = app["ql"].list_hdv
    if keyword:
        kw = keyword.lower().strip()
        rows = [h for h in rows if kw in h["maHDV"].lower() or kw in h["tenHDV"].lower() or kw in h["khuVuc"].lower() or kw in h["trangThai"].lower()]

    for h in rows:
        tree.insert(
            "",
            "end",
            values=(
                shorten_text(h.get("maHDV", ""), 200),
                shorten_text(h.get("tenHDV", ""), 30),
                shorten_text(h.get("sdt", ""), 15),
                shorten_text(h.get("khuVuc", ""), 24),
                shorten_text(h.get("kn", ""), 10),
                shorten_text(h.get("trangThai", ""), 20),
            ),
        )
    apply_zebra(tree)
    update_admin_status_card(app, "hdv", f"Đang ở Quản lý hướng dẫn viên - Hiển thị {len(rows)} HDV", THEME["primary"])

def open_hdv_form(app, data=None):  
    top = tk.Toplevel(app["root"])
    top.title("Thông tin hướng dẫn viên")
    top.geometry("620x520")
    top.minsize(560, 420)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()
    top.resizable(True, True)

    card = tk.Frame(
        top,
        bg=THEME["surface"],
        bd=0,
        highlightbackground="#d8e2f0",
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(card, text="THÔNG TIN HƯỚNG DẪN VIÊN", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 18, "bold")).pack(pady=(14, 10))

    scroll_outer, form = create_scrollable_form(card, THEME["surface"])
    scroll_outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    password_label = "Mật khẩu mới" if data else "Mật khẩu"
    fields = [
        ("Mã HDV", "maHDV", "entry"),
        ("Tên HDV", "tenHDV", "entry"),
        (password_label, "password", "entry"),
        ("Số điện thoại", "sdt", "entry"),
        ("Email", "email", "entry"),
        ("Kinh nghiệm (năm)", "kn", "entry"),
        ("Giới tính", "gioiTinh", "combo", ["Nam", "Nữ"]),
        ("CCCD ", "cccd", "entry"),
        ("Khu vực", "khuVuc", "combo", ["Miền Bắc", "Miền Trung", "Miền Nam"]),
        ("Trạng thái", "trangThai", "combo", HDV_STATUSES),
    ]

    widgets = {}
    for label, key, kind, *extra in fields:
        row = tk.Frame(form, bg=THEME["surface"])
        row.pack(fill="x", pady=7)
        tk.Label(row, text=label, width=16, anchor="w", bg=THEME["surface"], font=("Times New Roman", 13, "bold")).pack(side="left")

        if kind == "entry":
            w = tk.Entry(row, font=("Times New Roman", 13), show="*" if key == "password" else "")
            w.pack(side="left", fill="x", expand=True, ipady=5)
            style_form_entry_widget(w)
        else:
            w = ttk.Combobox(
                row,
                font=("Times New Roman", 12),
                values=extra[0],
                state="readonly",
                style=FORM_COMBOBOX_STYLE,
            )
            w.pack(side="left", fill="x", expand=True, ipady=5)

        widgets[key] = w
        if key == "sdt" and kind == "entry":
            register_phone_validate(w)
        if data:
            if kind == "entry" and key != "password":
                widgets[key].insert(0, data.get(key, ""))
            elif kind != "entry":
                value = data.get(key, "")
                if key == "gioiTinh" and value not in {"Nam", "Nữ"}:
                    value = ""
                widgets[key].set(value)

    if data:
        widgets["maHDV"].config(state="disabled")

    def sync_hdv_name_case(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `sync_hdv_name_case` (sync hdv name case).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        name_widget = widgets.get("tenHDV")
        if not name_widget:
            return

        current_value = name_widget.get()
        normalized_value = normalize_name_case(current_value)
        if normalized_value == current_value:
            return

        cursor = name_widget.index(tk.INSERT)
        name_widget.delete(0, "end")
        name_widget.insert(0, normalized_value)
        name_widget.icursor(min(cursor, len(normalized_value)))

    widgets["tenHDV"].bind("<FocusOut>", sync_hdv_name_case)

    def save_hdv():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save_hdv` (save hdv).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        new_data = {}
        before_data = copy.deepcopy(data) if data else None
        for _, key, kind, *extra in fields:
            if data and key == "maHDV":
                new_data[key] = data["maHDV"]
            else:
                new_data[key] = widgets[key].get().strip()

        new_data["tenHDV"] = normalize_name_case(new_data.get("tenHDV", ""))

        raw_password = new_data.get("password", "")
        if data and not raw_password:
            new_data["password"] = data.get("password", "")

        ok, msg = validate_hdv(app, new_data, data["maHDV"] if data else None)
        if not ok:
            messagebox.showwarning("Thông báo", msg, parent=top)
            return

        if data and raw_password:
            new_data["password"] = prepare_password_for_storage(raw_password)
        if not data:
            new_data["password"] = prepare_password_for_storage(raw_password)

        if data:
            for field in ["total_reviews", "avg_rating", "skill_score", "attitude_score", "problem_solving_score"]:
                new_data[field] = data.get(field, 0)
            for i, h in enumerate(app["ql"].list_hdv):
                if h["maHDV"] == data["maHDV"]:
                    app["ql"].list_hdv[i] = new_data
                    break
        else:
            new_data.update({
                "total_reviews": 0,
                "avg_rating": 0,
                "skill_score": 0,
                "attitude_score": 0,
                "problem_solving_score": 0
            })
            app["ql"].list_hdv.append(new_data)

        app["ql"].save()
        if data:
            changed_fields = [field for field in collect_changed_fields(before_data, new_data) if field != "password"]
            if raw_password:
                changed_fields.append("password")

            field_names = {
                "tenHDV": "Tên HDV",
                "sdt": "Số điện thoại",
                "khuVuc": "Khu vực",
                "trangThai": "Trạng thái",
                "password": "Mật khẩu"
            }
            details = []
            for f in changed_fields:
                if f == "password":
                    details.append("Mật khẩu tài khoản đã được cập nhật")
                else:
                    pretty_name = field_names.get(f, f)
                    old_val = before_data.get(f, "N/A")
                    new_val = new_data.get(f, "N/A")
                    details.append(f"{pretty_name}: '{old_val}' -> '{new_val}'")

            if details:
                from core.app import emit_notification
                content_msg = f"Tài khoản của bạn đã được cập nhật vào lúc {datetime.now().strftime('%d/%m/%Y %H:%M')}. Chi tiết thay đổi:\n- " + "\n- ".join(details)
                emit_notification(
                    app["ql"],
                    event_type="Account Update",
                    content=content_msg,
                    ma_hdv=new_data["maHDV"],
                    persist=True
                )
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="hdv",
                operation="update",
                target=new_data["maHDV"],
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="hdv",
                operation="create",
                target=new_data["maHDV"],
                detail=f"Tạo HDV {new_data.get('tenHDV', '')} | Khu vực: {new_data.get('khuVuc', '')} | Trạng thái: {new_data.get('trangThai', '')}",
            )
        top.destroy()
        refresh_hdv(app, app["search_hdv_var"].get())
        set_status(app, "Đã lưu HDV thành công", THEME["success"])

    btns = tk.Frame(card, bg=THEME["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))
    style_button(btns, "Lưu thông tin", THEME["success"], save_hdv).pack(side="left", fill="x", expand=True, padx=(0, 8))
    style_button(btns, "Hủy bỏ", THEME["danger"], top.destroy).pack(side="left", fill="x", expand=True)


# Lấy dòng HDV đang chọn và mở form chỉnh sửa cho bản ghi đó.
def edit_hdv(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_hdv` (edit hdv).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_hdv"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn hướng dẫn viên cần sửa.")
        return
    ma = app["tv_hdv"].item(sel[0])["values"][0]
    hdv = app["ql"].find_hdv(ma)
    if hdv:
        open_hdv_form(app, hdv)


# Xóa HDV được chọn sau khi kiểm tra ràng buộc.
# Không cho xóa nếu HDV vẫn đang được phân công cho tour.
def delete_hdv(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_hdv` (delete hdv).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_hdv"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn hướng dẫn viên cần xóa.")
        return
    ma = app["tv_hdv"].item(sel[0])["values"][0]

    blocking_tours = []
    for tour in app["ql"].list_tours:
        if normalize_code(tour.get("hdvPhuTrach", "")) != normalize_code(ma):
            continue
        status = normalize_tour_status(tour.get("trangThai", ""))
        if status not in ACTIVE_TOUR_STATUSES_FOR_GUIDE:
            continue
        start_date = parse_ddmmyyyy(tour.get("ngay"))
        end_date = parse_ddmmyyyy(tour.get("ngayKetThuc")) or start_date
        if is_upcoming_or_ongoing(start_date, end_date):
            blocking_tours.append(build_tour_display_label(app["ql"], tour.get("ma", "")))

    if blocking_tours:
        preview = ", ".join(blocking_tours[:3])
        if len(blocking_tours) > 3:
            preview += ", ..."
        messagebox.showwarning(
            "Không thể xóa",
            "HDV đang phụ trách tour sắp diễn ra hoặc đang diễn ra.\n"
            f"Tour liên quan: {preview}",
        )
        return

    if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa HDV {ma}?"):
        app["ql"].data["hdv"] = [h for h in app["ql"].list_hdv if h["maHDV"] != ma]
        app["ql"].save()
        write_crud_log(
            datastore=app["ql"],
            actor=get_admin_actor(app),
            role="admin",
            entity="hdv",
            operation="delete",
            target=ma,
            detail="Xóa hồ sơ hướng dẫn viên",
        )
        refresh_hdv(app, app["search_hdv_var"].get())
        set_status(app, f"Đã xóa HDV {ma}", THEME["danger"])

# Mở cửa sổ xem chi tiết hướng dẫn viên theo kiểu chỉ đọc.
# Hiển thị cả hồ sơ, điểm đánh giá và các tour HDV đang/đã phụ trách.
def open_hdv_detail(app, ma_hdv):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_hdv_detail` (open hdv detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    hdv = app["ql"].find_hdv(ma_hdv)
    if not hdv:
        messagebox.showerror("Lỗi", "Không tìm thấy thông tin HDV.")
        return

    assigned_tours = [
        t for t in app["ql"].list_tours
        if t.get("hdvPhuTrach") == ma_hdv
    ]

    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }

    top = tk.Toplevel(app["root"])
    top.title(f"Chi tiết HDV - {ma_hdv}")
    top.geometry("860x620")
    top.minsize(860, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(
        content_shell,
        bg=PASTEL_DETAIL["bg"],
        highlightthickness=0,
        bd=0
    )
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    bind_autohide_scrollbar(canvas, v_scroll, "vertical")
    canvas.pack(side="left", fill="both", expand=True)

    outer = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=outer, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    outer.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    # ===== HEADER =====
    header = tk.Frame(outer, bg=PASTEL_DETAIL["surface"])
    header.pack(fill="x", padx=24, pady=(22, 14))

    tk.Label(
        header,
        text="CHI TIẾT HƯỚNG DẪN VIÊN",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 24, "bold")
    ).pack()

    tk.Label(
        header,
        text=hdv.get("tenHDV", ""),
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 20, "bold")
    ).pack(pady=(4, 6))

    tk.Label(
        header,
        text=f"Mã HDV: {hdv.get('maHDV', '')}",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack()

    def create_section(parent, title, bg_color):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `create_section` (create section).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        wrapper = tk.Frame(
            parent,
            bg=bg_color,
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        wrapper.pack(fill="x", padx=20, pady=(0, 14))

        tk.Label(
            wrapper,
            text=title,
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 15, "bold")
        ).pack(anchor="w", padx=16, pady=(12, 8))

        body = tk.Frame(wrapper, bg=bg_color)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return body

    def create_info_row(parent, label_text, value, bg_color, wraplength=320):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `create_info_row` (create info row).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            label_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            wraplength: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        row = tk.Frame(parent, bg=bg_color)
        row.pack(fill="x", pady=4)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=18,
            anchor="w",
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")

        tk.Label(
            row,
            text=value if str(value).strip() else "Chưa cập nhật",
            anchor="w",
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12),
            wraplength=wraplength,
            justify="left"
        ).pack(side="left", fill="x", expand=True)

    # ===== THÔNG TIN TỔNG QUAN =====
    info_body = create_section(outer, "Thông tin tổng quan", PASTEL_DETAIL["section_bg"])

    left = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
    left.pack(side="left", fill="both", expand=True, padx=(0, 18))

    right = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
    right.pack(side="left", fill="both", expand=True)

    avg_rating = float(hdv.get("avg_rating", 0) or 0)

    info_left = [
        ("Mã HDV", hdv.get("maHDV", "")),
        ("Tên HDV", hdv.get("tenHDV", "")),
        ("Giới tính", hdv.get("gioiTinh", "")),
        ("Ngày sinh", hdv.get("ngaySinh", "")),
        ("CCCD", hdv.get("cccd", "")),
        ("SĐT", hdv.get("sdt", "")),
        ("Email", hdv.get("email", "")),
        ("Đá»‹a chỉ", hdv.get("diaChi", "")),
    ]

    info_right = [
        ("Khu vực", hdv.get("khuVuc", "")),
        ("Ngoại ngữ", hdv.get("ngoaiNgu", "")),
        ("Chuyên môn", hdv.get("chuyenMon", "")),
        ("Chứng chỉ", hdv.get("chungChi", "")),
        ("Số tour đã dẫn", hdv.get("soTourDaDan", 0)),
        ("Trạng thái", hdv.get("trangThai", "")),
    ]

    for label_text, value in info_left:
        create_info_row(left, label_text, value, PASTEL_DETAIL["section_bg"], 300)

    for label_text, value in info_right:
        create_info_row(right, label_text, value, PASTEL_DETAIL["section_bg"], 320)

    # ===== ĐÁNH GIÁ & HIỆU SUẤT =====
    ops_body = create_section(outer, "Đánh giá & hiệu suất", PASTEL_DETAIL["section_bg_2"])

    ops_rows = [
        ("Kiến thức chuyên môn", f"{hdv.get('skill_score', 0)}%"),
        ("Thái độ phục vụ", f"{hdv.get('attitude_score', 0)}%"),
        ("Xử lý tình huống", f"{hdv.get('problem_solving_score', 0)}%"),
    ]

    for label_text, value in ops_rows:
        row = tk.Frame(ops_body, bg=PASTEL_DETAIL["section_bg_2"])
        row.pack(fill="x", pady=6)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=18,
            anchor="nw",
            bg=PASTEL_DETAIL["section_bg_2"],
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")

        tk.Label(
            row,
            text=value,
            anchor="w",
            bg=PASTEL_DETAIL["section_bg_2"],
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12),
            wraplength=760,
            justify="left"
        ).pack(side="left", fill="x", expand=True)

    # ===== CÁC TOUR ĐANG / ĐÃ PHỤ TRÁCH =====
    tours_body = create_section(outer, "Các tour hướng dẫn viên phụ trách", PASTEL_DETAIL["section_bg_3"])

    if assigned_tours:
        for idx, tour in enumerate(assigned_tours, 1):
            row = tk.Frame(tours_body, bg=PASTEL_DETAIL["section_bg_3"])
            row.pack(fill="x", pady=5)

            occupied = app["ql"].get_occupied_seats(tour["ma"])

            text = (
                f"{idx}. {tour.get('ten', '')} "
                f"({tour.get('ma', '')}) | "
                f"Khởi hành: {tour.get('ngay', '')} | "
                f"Trạng thái: {tour.get('trangThai', '')} | "
                f"Khách: {occupied}/{tour.get('khach', '')}"
            )

            tk.Label(
                row,
                text=text,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg_3"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12),
                wraplength=820,
                justify="left"
            ).pack(side="left", fill="x", expand=True)
    else:
        tk.Label(
            tours_body,
            text="Hiện tại HDV này chưa được phân công tour nào.",
            anchor="w",
            bg=PASTEL_DETAIL["section_bg_3"],
            fg=PASTEL_DETAIL["muted"],
            font=("Times New Roman", 12, "italic")
        ).pack(fill="x")

    tk.Frame(outer, bg=PASTEL_DETAIL["surface"], height=10).pack(fill="x")

    # ===== FOOTER =====
    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    footer_inner.pack(fill="x", padx=16, pady=10)

    style_button(
        footer_inner,
        "Cập nhật",
        THEME["primary"],
        lambda: [top.destroy(), open_hdv_form(app, hdv)]
    ).pack(side="left", padx=(0, 8))

    style_button(
        footer_inner,
        "Thoát",
        THEME["danger"],
        top.destroy
    ).pack(side="right")

    set_status(app, f"Đã mở chi tiết HDV {hdv['maHDV']}", THEME["primary"])

# Render tab quản lý hướng dẫn viên của admin.
def admin_hdv_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_hdv_tab` (admin hdv tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    # tk.Label(
    #     app["container"],
    #     text="QUẢN LÝ NHÂN SỰ HƯỚNG DẪN VIÊN",
    #     font=("Times New Roman", 20, "bold"),
    #     bg=THEME["bg"],
    #     fg=THEME["text"]
    # ).pack(anchor="w", pady=(0, 10))

    top = tk.Frame(app["container"], bg=THEME["bg"])
    top.pack(fill="x", pady=(0, 10))

    style_button(top, "Thêm HDV", THEME["success"], lambda: open_hdv_form(app)).pack(side="left", padx=(0, 8))
    style_button(top, "Cập nhật", THEME["primary"], lambda: edit_hdv(app)).pack(side="left", padx=(0, 8))
    style_button(
        top,
        "Xem chi tiết",
        THEME["warning"],
        lambda: open_hdv_detail(
            app,
            app["tv_hdv"].item(app["tv_hdv"].selection()[0])["values"][0]
        ) if app["tv_hdv"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn một dòng để xem chi tiết")
    ).pack(side="left", padx=(0, 8))
    style_button(top, "Xóa HDV", THEME["danger"], lambda: delete_hdv(app)).pack(side="left", padx=(0, 8))
    style_button(top, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 8))

    tk.Label(top, text="Tìm kiếm:", bg=THEME["bg"], font=("Times New Roman", 12, "bold")).pack(side="left")
    search_entry = tk.Entry(top, textvariable=app["search_hdv_var"], font=("Times New Roman", 12), relief="solid", bd=1)
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)
    search_entry.bind("<Return>", lambda e: refresh_hdv(app, app["search_hdv_var"].get()))
    style_button(top, "Lọc", THEME["primary"], lambda: refresh_hdv(app, app["search_hdv_var"].get())).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="x", expand=False, pady=(0, 6))
   

    cols = ("ma", "ten", "sdt", "kv", "kn", "tt")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=10)
    app["tv_hdv"] = tv

    config = [
        ("ma", "Mã HDV", 90),
        ("ten", "Họ tên", 180),
        ("sdt", "SĐT", 120),
        ("kv", "Khu vực", 170),
        ("kn", "Kinh nghiệm", 110),
        ("tt", "Trạng thái", 130),
    ]

    for c, t, w in config:
        header_anchor = "center" if c == "kv" else "w"
        tv.heading(c, text=t, anchor=header_anchor)
        tv.column(c, anchor=("w" if c == "ten" else "center"), width=w, minwidth=max(80, w - 20), stretch=(c in {"ten", "kv"}))

    def on_double_click(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click` (on double click).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sel = tv.selection()
        if not sel:
            return
        ma = tv.item(sel[0])["values"][0]
        open_hdv_detail(app, ma)

    tv.bind("<Double-1>", on_double_click)

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
    bind_autohide_scrollbar(tv, sy, "vertical")
    bind_autohide_scrollbar(tv, sx, "horizontal")
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")
    sx.pack(side="bottom", fill="x")

    

    refresh_hdv(app, app["search_hdv_var"].get())

# =========================
# USER MANAGEMENT
# =========================
# Nạp lại danh sách khách hàng lên bảng, có hỗ trợ lọc theo từ khóa.
def refresh_users(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_users` (refresh users).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree = app.get("tv_users")
    if not tree:
        return

    for item in tree.get_children():
        tree.delete(item)

    rows = app["ql"].list_users
    if keyword:
        kw = keyword.lower().strip()
        rows = [
            u for u in rows
            if kw in u["username"].lower()
            or kw in u["fullname"].lower()
            or kw in str(u.get("sdt", "")).lower()
            or kw in str(u.get("email", "")).lower()
            or kw in str(u.get("trangThai", "Hoạt động")).lower()
        ]

    for u in rows:
        tree.insert(
            "",
            "end",
            values=(
                shorten_text(u.get("username", ""), 200),
                shorten_text(u.get("fullname", ""), 30),
                shorten_text(u.get("sdt", ""), 15),
                shorten_text(u.get("email", ""), 32),
                shorten_text(u.get("trangThai", "Hoạt động"), 20),
            ),
        )
    apply_zebra(tree)
    update_admin_status_card(app, "user", f"Đang ở Quản lý khách hàng - Hiển thị {len(rows)} khách hàng", THEME["primary"])

# Hàm dựng cửa sổ chi tiết dùng chung theo phong cách pastel.
# Các tab khác chỉ cần truyền tiêu đề, phụ đề và danh sách section là có thể tái sử dụng.
def create_detail_window(app, title_text, subtitle_text, sections):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_detail_window` (create detail window).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        title_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        subtitle_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        sections: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }

    top = tk.Toplevel(app["root"])
    top.title(subtitle_text)
    top.geometry("860x620")
    top.minsize(860, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_shell, bg=PASTEL_DETAIL["bg"], highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    bind_autohide_scrollbar(canvas, v_scroll, "vertical")
    canvas.pack(side="left", fill="both", expand=True)

    outer = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=outer, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    outer.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    header = tk.Frame(outer, bg=PASTEL_DETAIL["surface"])
    header.pack(fill="x", padx=24, pady=(22, 14))

    tk.Label(
        header,
        text=title_text,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 24, "bold")
    ).pack()

    tk.Label(
        header,
        text=subtitle_text,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 20, "bold")
    ).pack(pady=(4, 6))

    def create_section(parent, title, bg_color):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `create_section` (create section).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        wrapper = tk.Frame(
            parent,
            bg=bg_color,
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        wrapper.pack(fill="x", padx=20, pady=(0, 14))

        tk.Label(
            wrapper,
            text=title,
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 15, "bold")
        ).pack(anchor="w", padx=16, pady=(12, 8))

        body = tk.Frame(wrapper, bg=bg_color)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return body

    section_colors = [
        PASTEL_DETAIL["section_bg"],
        PASTEL_DETAIL["section_bg_2"],
        PASTEL_DETAIL["section_bg_3"],
    ]

    for idx, section in enumerate(sections):
        body = create_section(
            outer,
            section["title"],
            section_colors[idx % len(section_colors)]
        )
        bg_color = section_colors[idx % len(section_colors)]

        for label_text, value in section["rows"]:
            row = tk.Frame(body, bg=bg_color)
            row.pack(fill="x", pady=5)

            tk.Label(
                row,
                text=f"{label_text}:",
                width=18,
                anchor="nw",
                bg=bg_color,
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=str(value) if value is not None else "",
                anchor="w",
                justify="left",
                wraplength=720,
                bg=bg_color,
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12)
            ).pack(side="left", fill="x", expand=True)

    tk.Frame(outer, bg=PASTEL_DETAIL["surface"], height=10).pack(fill="x")

    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    footer_inner.pack(fill="x", padx=16, pady=10)

    style_button(footer_inner, "Thoát", THEME["danger"], top.destroy).pack(side="right")

# Mở cửa sổ xem chi tiết khách hàng và thống kê booking liên quan.
def open_user_detail(app, username):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_user_detail` (open user detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    user = app["ql"].find_user(username)
    if not user:
        messagebox.showerror("Lỗi", "Không tìm thấy khách hàng.")
        return

    user_bookings = [b for b in app["ql"].list_bookings if b.get("usernameDat") == username]
    total_bookings = len(user_bookings)
    total_people = sum(safe_int(b.get("soNguoi", 0)) for b in user_bookings)
    total_paid = sum(safe_int(b.get("daThanhToan", 0)) for b in user_bookings)

    booking_lines = []
    for i, b in enumerate(user_bookings[:10], 1):
        tour_label = build_tour_display_label(app["ql"], b.get("maTour", ""))
        booking_lines.append(
            f"{i}. {b.get('maBooking', '')} | Tour: {tour_label or b.get('maTour', '')} | "
            f"SL: {b.get('soNguoi', '')} | TT: {b.get('trangThai', '')}"
        )

    if not booking_lines:
        booking_lines = ["Khách hàng này chưa có booking nào."]

    sections = [
        {
            "title": "Thông tin tổng quan",
            "rows": [
                ("Tên đăng nhập", user.get("username", "")),
                ("Họ và tên", user.get("fullname", "")),
                ("Số điện thoại", user.get("sdt", "")),
                ("Mật khẩu", mask_password(user.get("password", ""))),
            ],
        },
        {
            "title": "Thống kê booking",
            "rows": [
                ("Số booking", total_bookings),
                ("Tổng số người đã đặt", total_people),
                ("Tổng tiền đã thanh toán", f"{total_paid:,} đ".replace(",", ".")),
            ],
        },
        {
            "title": "Danh sách booking liên quan",
            "rows": [
                ("Booking", "\n".join(booking_lines)),
            ],
        },
    ]

    create_detail_window(
        app,
        "CHI TIẾT KHÁCH HÀNG",
        f"{user.get('fullname', '')} ({user.get('username', '')})",
        sections
    )

    set_status(app, f"Đã mở chi tiết khách hàng {username}", THEME["primary"])


# Mở form thêm mới / chỉnh sửa khách hàng.
# Khi sửa, username bị khóa để tránh làm hỏng khóa liên kết dữ liệu.
def open_user_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_user_form` (open user form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin Khách hàng")
    top.geometry("520x420")
    top.minsize(480, 360)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()
    top.resizable(True, True)

    card = tk.Frame(
        top,
        bg=THEME["surface"],
        bd=0,
        highlightbackground="#d8e2f0",
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(card, text="QUẢN LÝ KHÁCH HÀNG", bg=THEME["surface"], font=("Times New Roman", 16, "bold")).pack(pady=15)

    fields = [("Tên đăng nhập", "username"), ("Mật khẩu", "password"), ("Họ và tên", "fullname"), ("Số điện thoại", "sdt")]
    widgets = {}

    for label, key in fields:
        row = tk.Frame(card, bg=THEME["surface"])
        row.pack(fill="x", padx=20, pady=5)
        tk.Label(row, text=label, width=15, anchor="w", bg=THEME["surface"], font=("Times New Roman", 12)).pack(side="left")
        show_char = "*" if key == "password" else ""
        e = tk.Entry(row, font=("Times New Roman", 12), show=show_char)
        e.pack(side="left", fill="x", expand=True, ipady=3)
        style_form_entry_widget(e)
        if key == "sdt":
            register_phone_validate(e)
        if data and key != "password":
            e.insert(0, data.get(key, ""))
        widgets[key] = e

    if data:
        widgets["username"].config(state="disabled")

    tk.Label(card, text="SĐT phải có 10 số và dùng đầu số di động Việt Nam hợp lệ, ví dụ: 032, 038, 070, 081, 090...", bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 10, "italic")).pack(anchor="w", padx=20, pady=(5, 0))
    tk.Label(card, text="Để trống mật khẩu nếu không muốn thay đổi.", bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "italic")).pack(anchor="w", padx=20, pady=(3, 0))

    def save():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save` (save).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        before_user = copy.deepcopy(data) if data else None
        username = normalize_spaces(data["username"] if data else widgets["username"].get())
        password = widgets["password"].get().strip()
        fullname = normalize_name_case(widgets["fullname"].get())
        sdt = normalize_spaces(widgets["sdt"].get())

        if not username or not fullname:
            return messagebox.showwarning("Lỗi", "Vui lòng nhập đủ các trường bắt buộc!", parent=top)

        if not is_valid_phone(sdt):
            return messagebox.showwarning(
                "Lỗi",
                "Số điện thoại phải có 10 số, bắt đầu bằng 0 và dùng đầu số di động Việt Nam hợp lệ.",
                parent=top
            )

        if data:
            for u in app["ql"].list_users:
                if u["username"] != username and u.get("sdt") == sdt:
                    return messagebox.showwarning("Lỗi", "Số điện thoại đã tồn tại!", parent=top)
            for i, u in enumerate(app["ql"].list_users):
                if u["username"] == username:
                    app["ql"].list_users[i]["fullname"] = fullname
                    app["ql"].list_users[i]["sdt"] = sdt
                    if password:
                        if len(password) < 3:
                            return messagebox.showwarning("Lỗi", "Mật khẩu phải có ít nhất 3 ký tự.", parent=top)
                        app["ql"].list_users[i]["password"] = prepare_password_for_storage(password)
                    break
        else:
            if not password or len(password) < 3:
                return messagebox.showwarning("Lỗi", "Mật khẩu phải có ít nhất 3 ký tự.", parent=top)
            if app["ql"].find_user(username):
                return messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại!", parent=top)
            if any(u.get("sdt") == sdt for u in app["ql"].list_users):
                return messagebox.showwarning("Lỗi", "Số điện thoại đã tồn tại!", parent=top)

            app["ql"].list_users.append({
                "username": username,
                "password": prepare_password_for_storage(password),
                "fullname": fullname,
                "sdt": sdt
            })

        app["ql"].save()
        if data:
            updated_user = app["ql"].find_user(username)
            changed_fields = [field for field in collect_changed_fields(before_user, updated_user) if field != "password"]
            if password:
                changed_fields.append("password")

            field_names = {
                "fullname": "Họ và tên",
                "sdt": "Số điện thoại",
                "password": "Mật khẩu"
            }
            details = []
            for f in changed_fields:
                if f == "password":
                    details.append("Mật khẩu tài khoản đã được cập nhật")
                else:
                    pretty_name = field_names.get(f, f)
                    old_val = before_user.get(f, "N/A")
                    new_val = updated_user.get(f, "N/A")
                    details.append(f"{pretty_name}: '{old_val}' -> '{new_val}'")

            if details:
                from core.app import emit_notification
                content_msg = f"Tài khoản của bạn đã được cập nhật vào lúc {datetime.now().strftime('%d/%m/%Y %H:%M')}. Chi tiết thay đổi:\n- " + "\n- ".join(details)
                emit_notification(
                    app["ql"],
                    event_type="Account Update",
                    content=content_msg,
                    username=username,
                    persist=True
                )
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="user",
                operation="update",
                target=username,
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="user",
                operation="create",
                target=username,
                detail=f"Tạo khách hàng {fullname} | SĐT: {sdt}",
            )
        keyword = app["search_user_var"].get().strip() if app.get("search_user_var") else ""
        refresh_users(app, keyword)
        top.destroy()
        set_status(app, "Đã lưu khách hàng thành công", THEME["success"])

    style_button(card, "Lưu thông tin", THEME["success"], save).pack(pady=20)


# Mở form chỉnh sửa cho khách hàng đang được chọn trong bảng.
def edit_user(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_user` (edit user).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_users"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn khách hàng cần sửa.")
        return

    username = app["tv_users"].item(sel[0])["values"][0]
    user = app["ql"].find_user(username)
    if not user:
        messagebox.showerror("Lỗi", "Không tìm thấy thông tin khách hàng.")
        return

    open_user_form(app, user)


# Xóa khách hàng được chọn, sau đó lưu dữ liệu và ghi log thao tác.
def delete_user(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_user` (delete user).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_users"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn khách hàng cần xóa.")
        return
    username = app["tv_users"].item(sel[0])["values"][0]

    # Kiểm tra ràng buộc ngăn chặn xóa khách hàng đang hoạt động
    bookings_list = getattr(app["ql"], "list_bookings", getattr(app["ql"], "data", {}).get("bookings", []))
    user_bookings = [
        b for b in bookings_list
        if str(b.get("usernameDat", "")).strip().lower() == username.strip().lower()
    ]

    has_active = False
    for b in user_bookings:
        b_status = str(b.get("trangThai", "")).strip()
        if b_status in {"Mới tạo", "Đã cọc", "Đã thanh toán", "Chờ hoàn tiền"}:
            has_active = True
            break
        ma_tour = str(b.get("maTour", "")).strip()
        if ma_tour:
            tour = app["ql"].find_tour(ma_tour)
            if tour:
                t_status = normalize_tour_status(tour.get("trangThai", ""))
                if t_status not in {TOUR_STATUS_COMPLETED, TOUR_STATUS_CANCELLED}:
                    has_active = True
                    break

    if has_active:
        messagebox.showerror("Lỗi", "Không thể xóa khách hàng vì khách đang có tour/booking đang hoạt động")
        return

    if messagebox.askyesno("Xác nhận", f"Xóa khách hàng {username}?"):
        app["ql"].data["users"] = [u for u in app["ql"].list_users if u["username"] != username]
        app["ql"].save()
        write_crud_log(
            datastore=app["ql"],
            actor=get_admin_actor(app),
            role="admin",
            entity="user",
            operation="delete",
            target=username,
            detail="Xóa khách hàng khỏi hệ thống",
        )
        keyword = app["search_user_var"].get().strip() if app.get("search_user_var") else ""
        refresh_users(app, keyword)
        set_status(app, f"Đã xóa khách hàng {username}", THEME["danger"])


# Render tab quản lý khách hàng của admin.
def admin_user_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_user_tab` (admin user tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)
    # tk.Label(app["container"], text="QUẢN LÝ DANH SÁCH KHÁCH HÀNG", font=("Times New Roman", 20, "bold"), bg=THEME["bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))
    style_button(toolbar, "Thêm khách mới", THEME["success"], lambda: open_user_form(app)).pack(side="left", padx=5)
    style_button(toolbar, "Cập nhật khách", THEME["primary"], lambda: edit_user(app)).pack(side="left", padx=5)
    style_button(
        toolbar,
        "Xem chi tiết",
        THEME["warning"],
        lambda: open_user_detail(
            app,
            app["tv_users"].item(app["tv_users"].selection()[0])["values"][0]
        ) if app["tv_users"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn một dòng để xem chi tiết")
    ).pack(side="left", padx=5)
    style_button(toolbar, "Xóa khách", THEME["danger"], lambda: delete_user(app)).pack(side="left", padx=5)
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 16))

    tk.Label(toolbar, text="Tìm kiếm:", bg=THEME["bg"], font=("Times New Roman", 12, "bold")).pack(side="left", padx=(16, 4))
    search_entry = tk.Entry(toolbar, textvariable=app["search_user_var"], font=("Times New Roman", 12), relief="solid", bd=1)
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)
    search_entry.bind("<Return>", lambda e: refresh_users(app, app["search_user_var"].get()))
    style_button(toolbar, "Lọc", THEME["primary"], lambda: refresh_users(app, app["search_user_var"].get())).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="x", expand=False, pady=(0, 6))

    cols = ("user", "name", "sdt", "email", "status")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=11)
    app["tv_users"] = tv

    headers = [
        ("user", "Username", 170, "center", False),
        ("name", "Họ tên", 230, "w", True),
        ("sdt", "SĐT", 130, "center", False),
        ("email", "Email", 260, "w", True),
        ("status", "Trạng thái", 130, "center", False),
    ]
    for cid, txt, width, anchor, stretch in headers:
        tv.heading(cid, text=txt)
        tv.column(cid, anchor=anchor, width=width, minwidth=max(90, width - 40), stretch=stretch)

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
    bind_autohide_scrollbar(tv, sy, "vertical")
    bind_autohide_scrollbar(tv, sx, "horizontal")
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")
    sx.pack(side="bottom", fill="x")

    

    refresh_users(app, app["search_user_var"].get())

    def on_double_click_user(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click_user` (on double click user).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sel = tv.selection()
        if not sel:
            return
        username = tv.item(sel[0])["values"][0]
        open_user_detail(app, username)

    tv.bind("<Double-1>", on_double_click_user)

# =========================
# TOUR MANAGEMENT
# =========================
# Kiểm tra dữ liệu tour trước khi lưu.
# Bao gồm: định dạng mã tour, ngày đi/ngày về, sức chứa, giá, điểm đi/đến,
# chi phí, HDV tồn tại hay không và xung đột lịch HDV.
def validate_tour(app, form_data, old_ma=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_tour` (validate tour).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        form_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_ma: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    form_data["ma"] = normalize_code(form_data.get("ma", ""))
    form_data["ten"] = normalize_tour_name(form_data.get("ten", ""))
    form_data["diemDi"] = normalize_name_case(form_data.get("diemDi", ""))
    form_data["diemDen"] = normalize_name_case(form_data.get("diemDen", ""))
    form_data["hdvPhuTrach"] = normalize_code(form_data.get("hdvPhuTrach", ""))
    if "lichTrinh" in form_data:
        form_data["lichTrinh"] = form_data.get("lichTrinh", [])
    form_data["trangThai"] = normalize_tour_status(form_data.get("trangThai", ""))
    form_data["ghiChuDieuHanh"] = normalize_spaces(form_data.get("ghiChuDieuHanh", ""))
    form_data["khach"] = normalize_spaces(form_data.get("khach", ""))
    form_data["gia"] = normalize_spaces(form_data.get("gia", ""))

    start_date = parse_ddmmyyyy(form_data.get("ngay", ""))
    end_date = parse_ddmmyyyy(form_data.get("ngayKetThuc", ""))
    raw_start_date = start_date
    raw_end_date = end_date
    so_ngay = parse_duration_days(form_data.get("soNgay", 1), default=1)

    if raw_start_date and raw_end_date and raw_end_date < raw_start_date:
        return False, "Ngày kết thúc không được nhỏ hơn ngày khởi hành."

    if start_date and end_date:
        so_ngay = compute_duration_days(start_date, end_date, default=so_ngay)
        end_date = compute_end_date(start_date, so_ngay)
    elif start_date and not end_date:
        end_date = compute_end_date(start_date, so_ngay)
    elif end_date and not start_date:
        start_date = end_date
        so_ngay = 1

    if start_date:
        form_data["ngay"] = format_ddmmyyyy(start_date)
    if end_date:
        form_data["ngayKetThuc"] = format_ddmmyyyy(end_date)
    form_data["soNgay"] = str(max(1, so_ngay))

    required = ["ma", "ten", "ngay", "ngayKetThuc", "soNgay", "khach", "gia", "diemDi", "diemDen", "trangThai", "hdvPhuTrach"]
    if not all(form_data.get(k, "").strip() for k in required):
        return False, "Vui lòng nhập đầy đủ thông tin tour."

    if not re.fullmatch(r"T\d{2,}", form_data["ma"]):
        return False, "Mã tour phải theo dạng T01, T02..."

    if len(form_data["ten"].strip()) < 5:
        return False, "Tên tour quá ngắn."

    if not is_valid_date(form_data["ngay"]) or not is_valid_date(form_data["ngayKetThuc"]):
        return False, "Ngày khởi hành / kết thúc không đúng định dạng dd/mm/yyyy."

    ngay_di = parse_ddmmyyyy(form_data["ngay"])
    ngay_ve = parse_ddmmyyyy(form_data["ngayKetThuc"])
    if not ngay_di or not ngay_ve:
        return False, "Ngày tour không hợp lệ."
    if ngay_ve < ngay_di:
        return False, "Ngày kết thúc không được nhỏ hơn ngày khởi hành."
    form_data["soNgay"] = str(compute_duration_days(ngay_di, ngay_ve, default=1))

    if not form_data["khach"].isdigit() or not (1 <= int(form_data["khach"]) <= 500):
        return False, "Sức chứa tối đa phải từ 1 đến 500 khách."

    if not form_data["gia"].isdigit() or int(form_data["gia"]) <= 0:
        return False, "Giá tour phải là số dương."

    if form_data["diemDi"].strip().lower() == form_data["diemDen"].strip().lower():
        return False, "Điểm đi và điểm đến không được trùng nhau."

    hdv = app["ql"].find_hdv(form_data["hdvPhuTrach"])
    if not hdv:
        return False, "Hướng dẫn viên phụ trách không tồn tại."
    if hdv.get("trangThai") == "Tạm nghỉ":
        return False, "Không thể phân công HDV đang ở trạng thái tạm nghỉ."

    for t in app["ql"].list_tours:
        if normalize_code(t.get("ma", "")) == normalize_code(old_ma):
            continue
        if normalize_code(t.get("hdvPhuTrach", "")) != form_data["hdvPhuTrach"]:
            continue
        if normalize_tour_status(t.get("trangThai", "")) in TERMINAL_TOUR_STATUSES:
            continue

        other_start = parse_ddmmyyyy(t.get("ngay"))
        other_end = parse_ddmmyyyy(t.get("ngayKetThuc")) or other_start
        if not other_start or not other_end:
            continue

        if max(ngay_di, other_start) <= min(ngay_ve, other_end):
            hdv_label = build_hdv_display_label(app["ql"], form_data["hdvPhuTrach"]) or form_data["hdvPhuTrach"]
            return False, f"HDV {hdv_label} đã có tour {build_tour_display_label(app['ql'], t.get('ma', ''))} bị trùng lịch trong khoảng thời gian này."

    for t in app["ql"].list_tours:
        if normalize_code(t.get("ma", "")) == form_data["ma"] and normalize_code(t.get("ma", "")) != normalize_code(old_ma):
            return False, "Mã tour đã tồn tại."

    existing_booked = app["ql"].get_occupied_seats(normalize_code(old_ma) or form_data["ma"])
    if int(form_data["khach"]) < existing_booked:
        return False, f"Không thể giảm sức chứa vì đã có {existing_booked} chỗ được đặt."

    return True, ""


# Nạp lại bảng tour; đồng thời tính số chỗ đã đặt / tổng sức chứa để hiển thị.
def refresh_tours(app, keyword="", sync_status=False, show_status_popup=False):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_tours` (refresh tours).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if sync_status:
        refresh_tour_lifecycle_for_admin(app, show_popup=show_status_popup)

    tree = app.get("tv_tour")
    if not tree:
        return

    for item in tree.get_children():
        tree.delete(item)

    rows = app["ql"].list_tours
    if keyword:
        kw = keyword.lower().strip()
        rows = [t for t in rows if kw in t["ma"].lower() or kw in t["ten"].lower() or kw in t["diemDen"].lower() or kw in t["trangThai"].lower()]

    for t in rows:
        booked = app["ql"].get_occupied_seats(t["ma"])
        hdv_display = normalize_code(t.get("hdvPhuTrach", ""))
        display_status = normalize_tour_status(t.get("trangThai", ""))
        tree.insert(
            "",
            "end",
            values=(
                shorten_text(t.get("ma", ""), 200),
                shorten_text(t.get("ten", ""), 30),
                shorten_text(t.get("ngay", ""), 15),
                shorten_text(t.get("ngayKetThuc", ""), 15),
                shorten_text(t.get("khach", ""), 10),
                shorten_text(booked, 10),
                shorten_text(display_status, 20),
                shorten_text(hdv_display, 26),
            ),
        )
    apply_zebra(tree)
    update_admin_status_card(app, "tour", f"Đang ở Quản lý tour - Hiển thị {len(rows)} tour", THEME["primary"])


# Mở form thêm mới / chỉnh sửa tour.
# Khi lưu, hàm còn cập nhật trạng thái HDV phụ trách tương ứng với trạng thái tour.
def open_tour_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_tour_form` (open tour form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin tour du lịch")
    top.geometry("820x640")
    top.minsize(680, 460)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()
    top.resizable(True, True)

    card = tk.Frame(
        top,
        bg=THEME["surface"],
        bd=0,
        highlightbackground="#d8e2f0",
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(card, text="THÔNG TIN CHI TIẾT TOUR", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 18, "bold")).pack(pady=(14, 10))

    scroll_outer, form = create_scrollable_form(card, THEME["surface"])
    scroll_outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    hdv_options = []
    hdv_label_by_code = {}
    for guide in app["ql"].list_hdv:
        code = normalize_code(guide.get("maHDV", ""))
        name = normalize_name_case(guide.get("tenHDV", ""))
        label = f"{code} - {name}" if name else code
        hdv_options.append(label)
        hdv_label_by_code[code] = label

    fields = [
        ("Mã tour", "ma", "entry"),
        ("Tên tour", "ten", "entry"),
        ("Ngày khởi hành", "ngay", "entry"),
        ("Ngày kết thúc", "ngayKetThuc", "entry"),
        ("Số ngày", "soNgay", "entry"),
        ("Sức chứa tối đa", "khach", "entry"),
        ("Giá tour (VNĐ)", "gia", "entry"),
        ("Điểm xuất phát", "diemDi", "entry"),
        ("Điểm đến", "diemDen", "entry"),
        ("Ghi chú điều hành", "ghiChuDieuHanh", "entry"),
        ("Trạng thái", "trangThai", "combo", TOUR_STATUSES),
        ("HDV phụ trách", "hdvPhuTrach", "combo", hdv_options),
    ]

    widgets = {}
    for label, key, kind, *extra in fields:
        row = tk.Frame(form, bg=THEME["surface"])
        row.pack(fill="x", pady=7)
        tk.Label(row, text=label, width=16, anchor="w", bg=THEME["surface"], font=("Times New Roman", 13, "bold")).pack(side="left")

        if kind == "entry":
            w = tk.Entry(row, font=("Times New Roman", 13))
            w.pack(side="left", fill="x", expand=True, ipady=5)
            style_form_entry_widget(w)
        else:
            w = ttk.Combobox(
                row,
                font=("Times New Roman", 12),
                values=extra[0],
                state="readonly",
                style=FORM_COMBOBOX_STYLE,
            )
            w.pack(side="left", fill="x", expand=True, ipady=5)

        widgets[key] = w
        if key == "sdt" and kind == "entry":
            register_phone_validate(w)
        if data:
            val = data.get(key, "")
            if kind == "entry":
                w.insert(0, str(val))
            else:
                if key == "hdvPhuTrach":
                    hdv_code = normalize_code(val)
                    w.set(hdv_label_by_code.get(hdv_code, hdv_code))
                else:
                    w.set(val)

    itinerary_row = tk.Frame(form, bg=THEME["surface"])
    itinerary_row.pack(fill="both", expand=True, pady=7)
    tk.Label(itinerary_row, text="Lịch trình chi tiết", anchor="w", bg=THEME["surface"], font=("Times New Roman", 13, "bold")).pack(anchor="w")
    itinerary_text = tk.Text(itinerary_row, height=7, font=("Times New Roman", 12), relief="solid", bd=1, wrap="word")
    itinerary_text.pack(fill="x", expand=True, pady=(6, 0))
    if data:
        itinerary_text.insert("1.0", itinerary_to_text(data.get("lichTrinh", [])))

    if data:
        widgets["ma"].config(state="disabled")
    else:
        widgets["trangThai"].set(TOUR_STATUS_NOT_OPEN)

    sync_state = {"busy": False}

    def _set_entry_value(key, value):
        entry = widgets[key]
        entry.delete(0, "end")
        entry.insert(0, str(value))

    def _extract_hdv_code(raw_value):
        text = normalize_spaces(raw_value)
        if not text:
            return ""
        return normalize_code(text.split("-", 1)[0])

    def _sync_end_from_duration(_event=None):
        if sync_state["busy"]:
            return
        start_date = parse_ddmmyyyy(widgets["ngay"].get())
        if not start_date:
            return
        so_ngay = parse_duration_days(widgets["soNgay"].get(), default=1)
        end_date = compute_end_date(start_date, so_ngay)
        if not end_date:
            return
        sync_state["busy"] = True
        try:
            _set_entry_value("soNgay", so_ngay)
            _set_entry_value("ngayKetThuc", format_ddmmyyyy(end_date))
        finally:
            sync_state["busy"] = False

    def _sync_duration_from_end(_event=None):
        if sync_state["busy"]:
            return
        start_date = parse_ddmmyyyy(widgets["ngay"].get())
        end_date = parse_ddmmyyyy(widgets["ngayKetThuc"].get())
        if not start_date or not end_date:
            return
        so_ngay = compute_duration_days(start_date, end_date, default=1)
        normalized_end = compute_end_date(start_date, so_ngay)
        sync_state["busy"] = True
        try:
            _set_entry_value("soNgay", so_ngay)
            if normalized_end:
                _set_entry_value("ngayKetThuc", format_ddmmyyyy(normalized_end))
        finally:
            sync_state["busy"] = False

    for key in ("ngay", "soNgay"):
        widgets[key].bind("<FocusOut>", _sync_end_from_duration)
        widgets[key].bind("<KeyRelease>", _sync_end_from_duration)
    widgets["ngayKetThuc"].bind("<FocusOut>", _sync_duration_from_end)
    widgets["ngayKetThuc"].bind("<KeyRelease>", _sync_duration_from_end)
    _sync_end_from_duration()

    if data:
        current_ma = normalize_code(data.get("ma", ""))
        current_status = normalize_tour_status(data.get("trangThai", ""))
        occupied_now = app["ql"].get_occupied_seats(current_ma)
        has_any_booking = any(
            normalize_code(b.get("maTour", "")) == current_ma
            for b in app["ql"].list_bookings
        )

        available_statuses = list(TOUR_STATUS_CHOICES)
        if occupied_now > 0:
            available_statuses = [s for s in available_statuses if s != TOUR_STATUS_NOT_OPEN]

        lock_status = False
        if current_status == TOUR_STATUS_COMPLETED:
            available_statuses = [TOUR_STATUS_COMPLETED]
            lock_status = True
        elif current_status == TOUR_STATUS_CANCELLED and has_any_booking:
            available_statuses = [TOUR_STATUS_CANCELLED]
            lock_status = True

        widgets["trangThai"]["values"] = available_statuses
        widgets["trangThai"].set(current_status)
        if lock_status:
            widgets["trangThai"].configure(state="disabled")

    def save_tour():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save_tour` (save tour).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        before_tour = copy.deepcopy(data) if data else None
        form_data = {}
        for _, key, kind, *extra in fields:
            if data and key == "ma":
                form_data[key] = data["ma"]
            elif key == "hdvPhuTrach":
                form_data[key] = _extract_hdv_code(widgets[key].get())
            else:
                form_data[key] = widgets[key].get().strip()
        form_data["lichTrinh"] = parse_itinerary_text(itinerary_text.get("1.0", "end"))

        ma_tour = normalize_code(widgets["ma"].get())
        selected_status = normalize_tour_status(widgets["trangThai"].get())
        start_date = parse_ddmmyyyy(form_data.get("ngay", ""))
        end_date = parse_ddmmyyyy(form_data.get("ngayKetThuc", ""))
        occupied = app["ql"].get_occupied_seats(ma_tour)
        capacity = safe_int(form_data.get("khach", 0))
        today = datetime.now().date()
        current_status = normalize_tour_status((data or {}).get("trangThai", ""))
        has_any_booking = any(
            normalize_code(b.get("maTour", "")) == ma_tour
            for b in app["ql"].list_bookings
        )

        if capacity > 0 and capacity < occupied:
            messagebox.showwarning("Lỗi nghiệp vụ", "Số khách tối đa không được nhỏ hơn số khách đã đăng ký hiện tại.", parent=top)
            return

        if data and current_status == TOUR_STATUS_COMPLETED and selected_status != TOUR_STATUS_COMPLETED:
            messagebox.showwarning("Lỗi nghiệp vụ", "Tour đã kết thúc nên không thể thay đổi trạng thái nghiệp vụ.", parent=top)
            return

        if data and current_status == TOUR_STATUS_CANCELLED and selected_status != TOUR_STATUS_CANCELLED:
            messagebox.showwarning("Lỗi nghiệp vụ", "Tour đã hủy không được tự động mở lại. Vui lòng tạo tour mới nếu muốn kinh doanh lại lịch trình này.", parent=top)
            return

        if data and occupied > 0 and selected_status == TOUR_STATUS_NOT_OPEN:
            messagebox.showwarning(
                "Lỗi nghiệp vụ",
                "Tour đã có khách đăng ký nên không thể chuyển về 'Sắp mở bán'.",
                parent=top,
            )
            return

        if data and current_status == TOUR_STATUS_FULL and selected_status == TOUR_STATUS_OPEN and capacity <= occupied:
            messagebox.showwarning(
                "Lỗi nghiệp vụ",
                "Tour đã đủ khách. Muốn mở bán lại, vui lòng tăng số lượng khách tối đa lớn hơn số khách đã đăng ký.",
                parent=top,
            )
            return

        if selected_status == TOUR_STATUS_OPEN and start_date and start_date <= today:
            messagebox.showwarning("Lỗi nghiệp vụ", "Tour đã đến ngày khởi hành, không thể để trạng thái Đang mở bán.", parent=top)
            return

        if selected_status == TOUR_STATUS_OPEN and capacity > 0 and occupied >= capacity:
            messagebox.showwarning("Lỗi nghiệp vụ", "Tour đã đủ khách, không thể để trạng thái Đang mở bán.", parent=top)
            return

        if selected_status == TOUR_STATUS_FULL and capacity > 0 and occupied < capacity:
            if not messagebox.askyesno("Xác nhận", "Tour chưa đủ khách. Bạn có chắc muốn chốt trạng thái Đã đủ khách không?", parent=top):
                return

        if selected_status == TOUR_STATUS_STARTED and start_date and today < start_date.date():
            messagebox.showwarning("Lỗi nghiệp vụ", "Tour chưa đến ngày khởi hành, không thể chuyển sang Đang diễn ra.", parent=top)
            return

        if selected_status == TOUR_STATUS_COMPLETED and end_date and today <= end_date.date():
            messagebox.showwarning("Lỗi nghiệp vụ", "Tour chưa qua ngày kết thúc, không thể chuyển sang Đã kết thúc.", parent=top)
            return

        if data and current_status == TOUR_STATUS_STARTED and selected_status in {TOUR_STATUS_NOT_OPEN, TOUR_STATUS_OPEN, TOUR_STATUS_FULL}:
            messagebox.showwarning(
                "Lỗi nghiệp vụ",
                "Tour đang diễn ra nên không thể quay lại trạng thái trước khởi hành.",
                parent=top,
            )
            return

        if form_data["trangThai"] == TOUR_STATUS_CANCELLED and (not data or normalize_tour_status(data.get("trangThai", "")) != TOUR_STATUS_CANCELLED):
            booked = app["ql"].get_occupied_seats(form_data["ma"])
            if booked > 0:
                if not messagebox.askyesno("Xác nhận hủy", "Tour đã có khách đăng ký. Khi hủy tour, hệ thống sẽ chuyển tour sang 'Đã hủy' và các booking liên quan cần được xử lý hoàn tiền theo quy định. Bạn có chắc chắn không?"):
                    return
                existing_note = str(form_data.get("ghiChuDieuHanh", "")).strip()
                form_data["ghiChuDieuHanh"] = f"{existing_note} [ADMIN] Hủy tour khi đã có khách đăng ký.".strip()

        if not form_data.get("lichTrinh"):
            form_data["lichTrinh"] = [
                {
                    "ngay": "Ngày 1",
                    "tieuDe": f"{form_data.get('diemDi', '')} - {form_data.get('diemDen', '')}".strip(" -"),
                    "diaDiem": [form_data.get("diemDen", "")] if form_data.get("diemDen") else [],
                    "moTa": "Lịch trình đang được cập nhật chi tiết.",
                }
            ]

        ok, msg = validate_tour(app, form_data, data["ma"] if data else None)
        if not ok:
            messagebox.showwarning("Thông báo", msg, parent=top)
            return

        # Chuẩn hóa trạng thái sau khi validate theo quy tắc nghiệp vụ, nhưng vẫn tôn trọng
        # thao tác chốt đoàn thủ công khi admin chọn "Đã đủ khách".
        if selected_status == TOUR_STATUS_FULL and capacity > 0 and occupied < capacity:
            form_data["trangThai"] = TOUR_STATUS_FULL
        else:
            final_status = derive_tour_status(
                current_status=selected_status,
                start_date=parse_ddmmyyyy(form_data.get("ngay", "")),
                end_date=parse_ddmmyyyy(form_data.get("ngayKetThuc", "")),
                occupied=occupied,
                capacity=max(capacity, 0),
            )
            form_data["trangThai"] = normalize_tour_status(final_status)

        sync_ghi_chu_dieu_hanh(form_data)

        if data and current_status == TOUR_STATUS_COMPLETED:
            changed_core_fields = [
                key for key in ("ngay", "ngayKetThuc", "gia", "khach", "hdvPhuTrach")
                if str(form_data.get(key, "")).strip() != str((data or {}).get(key, "")).strip()
            ]
            if changed_core_fields:
                messagebox.showwarning(
                    "Lỗi nghiệp vụ",
                    "Tour đã kết thúc, chỉ được phép chỉnh sửa ghi chú điều hành.",
                    parent=top,
                )
                return

        if data:
            for i, t in enumerate(app["ql"].list_tours):
                if t["ma"] == data["ma"]:
                    app["ql"].list_tours[i] = form_data
                    break
        else:
            app["ql"].list_tours.append(form_data)

        hdv = app["ql"].find_hdv(form_data["hdvPhuTrach"])
        if hdv:
            normalized_tour_status = normalize_tour_status(form_data.get("trangThai", ""))
            if normalized_tour_status in ACTIVE_TOUR_STATUSES_FOR_GUIDE:
                hdv["trangThai"] = "Đang dẫn tour" if normalized_tour_status == TOUR_STATUS_STARTED else "Đã phân công"

        app["ql"].save()
        if data:
            changed_fields = collect_changed_fields(before_tour, form_data)
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="tour",
                operation="update",
                target=form_data["ma"],
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="tour",
                operation="create",
                target=form_data["ma"],
                detail=f"Tạo tour {form_data.get('ten', '')} | Ngày đi: {form_data.get('ngay', '')} | HDV: {form_data.get('hdvPhuTrach', '')}",
            )
        top.destroy()
        ma_upper = str(form_data["ma"]).strip().upper()
        if "open_tour_details" in app and ma_upper in app["open_tour_details"]:
            old_win = app["open_tour_details"][ma_upper]
            geom = None
            try:
                if old_win and old_win.winfo_exists():
                    geom = old_win.geometry()
                    old_win.grab_release()
                    old_win.destroy()
            except Exception:
                pass
            if "open_tour_detail_window_func" in app:
                app["open_tour_detail_window_func"](app, form_data["ma"])
                new_win = app["open_tour_details"].get(ma_upper)
                if new_win and geom:
                    try:
                        new_win.geometry(geom)
                    except Exception:
                        pass

        refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=True)
        
        # Tự động chọn lại dòng tour vừa chỉnh sửa trên Treeview
        tree = app.get("tv_tour")
        if tree:
            for item_id in tree.get_children():
                values = tree.item(item_id)["values"]
                if values and str(values[0]).strip().upper() == ma_upper:
                    tree.selection_set(item_id)
                    tree.focus(item_id)
                    tree.see(item_id)
                    break

        set_status(app, "Đã lưu thông tin tour thành công", THEME["success"])

    btns = tk.Frame(card, bg=THEME["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))
    style_button(btns, "Lưu tour", THEME["success"], save_tour).pack(side="left", fill="x", expand=True, padx=(0, 8))
    style_button(btns, "Hủy", THEME["danger"], top.destroy).pack(side="left", fill="x", expand=True)


# Mở form sửa tour đang chọn.
def edit_tour(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_tour` (edit tour).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_tour"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn tour cần sửa.")
        return
    ma = app["tv_tour"].item(sel[0])["values"][0]
    tour = app["ql"].find_tour(ma)
    if tour:
        open_tour_form(app, tour)


# Xóa tour nếu thỏa điều kiện nghiệp vụ.
# Không cho xóa tour đang chạy hoặc tour còn booking hiệu lực.
def delete_tour(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_tour` (delete tour).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_tour"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn tour cần xóa.")
        return
    ma = app["tv_tour"].item(sel[0])["values"][0]

    tour = app["ql"].find_tour(ma)
    if not tour:
        return

    normalized_status = normalize_tour_status(tour.get("trangThai", ""))
    if normalized_status == TOUR_STATUS_COMPLETED:
        messagebox.showwarning("Không thể xóa", "Tour đã hoàn thành nên không thể xóa.")
        return

    bookings = app["ql"].get_bookings_by_tour(ma)
    ma_upper = str(ma).strip().upper()

    if normalized_status == TOUR_STATUS_CANCELLED:
        # Kiểm tra xem có booking đang hoạt động không
        active_bookings = [b for b in bookings if b.get("trangThai") not in {"Đã hủy", "Hoàn tiền"}]
        if active_bookings:
            messagebox.showwarning("Không thể xóa", "Không thể xóa tour vì còn booking đang hoạt động.")
            return
        
        # Nếu không còn booking hoạt động, cho phép xóa cứng trực tiếp
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa tour {ma} khỏi hệ thống?"):
            app["ql"].data["tours"] = [t for t in app["ql"].list_tours if t["ma"] != ma]
            app["ql"].save()
            if "open_tour_details" in app and ma_upper in app["open_tour_details"]:
                old_win = app["open_tour_details"][ma_upper]
                try:
                    if old_win and old_win.winfo_exists():
                        old_win.grab_release()
                        old_win.destroy()
                except Exception:
                    pass
                app["open_tour_details"].pop(ma_upper, None)

            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="tour",
                operation="delete",
                target=ma,
                detail=f"Xóa tour đã hủy {tour.get('ten', '')}",
            )
            refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=True)
            set_status(app, f"Đã xóa tour {ma}", THEME["danger"])
        return

    has_registered_customers = any(safe_int(b.get("soNguoi", 0)) > 0 for b in bookings)
    start_date = parse_ddmmyyyy(tour.get("ngay"))
    has_started = normalized_status == TOUR_STATUS_STARTED or (
        start_date is not None and datetime.now().date() >= start_date
    )

    if has_registered_customers or has_started:
        if not messagebox.askyesno(
            "Xác nhận chuyển trạng thái",
            "Tour đã có khách đăng ký hoặc đã đến hạn khởi hành. Khi hủy tour, hệ thống sẽ chuyển tour sang 'Đã hủy' và các booking liên quan cần được xử lý hoàn tiền theo quy định. Bạn có chắc chắn không?",
        ):
            return

        before_tour = copy.deepcopy(tour)
        tour["trangThai"] = TOUR_STATUS_CANCELLED
        sync_ghi_chu_dieu_hanh(tour)
        soft_note = "[ADMIN] Đã hủy tour theo thao tác điều hành."
        old_note = normalize_spaces(tour.get("ghiChuDieuHanh", ""))
        if soft_note not in old_note:
            tour["ghiChuDieuHanh"] = f"{soft_note} {old_note}".strip()

        app["ql"].save()
        if "open_tour_details" in app and ma_upper in app["open_tour_details"]:
            old_win = app["open_tour_details"][ma_upper]
            geom = None
            try:
                if old_win and old_win.winfo_exists():
                    geom = old_win.geometry()
                    old_win.grab_release()
                    old_win.destroy()
            except Exception:
                pass
            if "open_tour_detail_window_func" in app:
                app["open_tour_detail_window_func"](app, ma)
                new_win = app["open_tour_details"].get(ma_upper)
                if new_win and geom:
                    try:
                        new_win.geometry(geom)
                    except Exception:
                        pass
        changed_fields = collect_changed_fields(before_tour, tour)
        write_crud_log(
            datastore=app["ql"],
            actor=get_admin_actor(app),
            role="admin",
            entity="tour",
            operation="update",
            target=ma,
            detail="Chuyển trạng thái xóa mềm: "
            + (", ".join(changed_fields) if changed_fields else "trạng thái/nghi chú"),
        )
        refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=True)
        set_status(app, f"Đã chuyển tour {ma} sang '{TOUR_STATUS_CANCELLED}'", THEME["warning"])
        return

    if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa tour {ma}?"):
        app["ql"].data["tours"] = [t for t in app["ql"].list_tours if t["ma"] != ma]
        app["ql"].save()
        if "open_tour_details" in app and ma_upper in app["open_tour_details"]:
            old_win = app["open_tour_details"][ma_upper]
            try:
                if old_win and old_win.winfo_exists():
                    old_win.grab_release()
                    old_win.destroy()
            except Exception:
                pass
            app["open_tour_details"].pop(ma_upper, None)

        write_crud_log(
            datastore=app["ql"],
            actor=get_admin_actor(app),
            role="admin",
            entity="tour",
            operation="delete",
            target=ma,
            detail=f"Xóa tour {tour.get('ten', '')}",
        )
        refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=True)
        set_status(app, f"Đã xóa tour {ma}", THEME["danger"])


# =========================
# WEATHER & LOCATION
# =========================
def open_weather_for_selected_tour(app):
    """Mở popup thời tiết cho tour đang chọn."""
    if not app.get("tv_tour"):
        messagebox.showwarning("Thông báo", "Không tìm thấy bảng tour.")
        return
    
    selection = app["tv_tour"].selection()
    if not selection:
        messagebox.showwarning("Thông báo", "Vui lòng chọn một tour để xem thời tiết.")
        return
    
    ma_tour = app["tv_tour"].item(selection[0])["values"][0]
    tour = app["ql"].find_tour(ma_tour)
    
    if not tour:
        messagebox.showerror("Lỗi", f"Không tìm thấy tour {ma_tour}")
        return
    
    open_tour_weather_popup(app["root"], tour, app["ql"])


# =========================
# TOUR MANAGEMENT
# =========================
# Render tab quản lý tour và khai báo thêm cửa sổ xem chi tiết tour bên trong tab này.
def admin_tour_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_tour_tab` (admin tour tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    # tk.Label(app["container"], text="QUẢN LÝ DANH SÁCH TOUR DU LỊCH", font=("Times New Roman", 20, "bold"), bg=THEME["bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))
    style_button(toolbar, "Thêm tour mới", THEME["success"], lambda: open_tour_form(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Cập nhật", THEME["primary"], lambda: edit_tour(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Xem chi tiết",THEME["warning"],lambda: open_tour_detail_window(app, app["tv_tour"].item(app["tv_tour"].selection()[0])["values"][0]) if app["tv_tour"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn một dòng để xem chi tiết") ).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Thời tiết", "#0891b2", lambda: open_weather_for_selected_tour(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Xóa tour", THEME["danger"], lambda: delete_tour(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 8))

    tk.Label(toolbar, text="Tìm kiếm:", bg=THEME["bg"], font=("Times New Roman", 12, "bold")).pack(side="left")
    search_entry = tk.Entry(toolbar, textvariable=app["search_tour_var"], font=("Times New Roman", 12), relief="solid", bd=1)
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)
    search_entry.bind("<Return>", lambda e: refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=False))
    style_button(toolbar, "Lọc", THEME["primary"], lambda: refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=False)).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="x", expand=False, pady=(0, 6))

    cols = ("ma", "ten", "ngay", "ngaykt", "khach", "dadat", "tt", "hdv")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=11)
    app["tv_tour"] = tv

    cfg = [
        ("ma", "Mã Tour", 80),
        ("ten", "Tên tour du lịch", 240),
        ("ngay", "Ngày đi", 110),
        ("ngaykt", "Ngày kết thúc", 110),
        ("khach", "Số khách", 90),
        ("dadat", "Đã đặt", 90),
        ("tt", "Trạng thái", 130),
        ("hdv", "Mã HDV", 120),
    ]
    for c, t, w in cfg:
        tv.heading(c, text=t)
        tv.column(c, anchor=("w" if c == "ten" else "center"), width=w, minwidth=max(78, w - 24), stretch=(c == "ten"))

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
    bind_autohide_scrollbar(tv, sy, "vertical")
    bind_autohide_scrollbar(tv, sx, "horizontal")
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")
    sx.pack(side="bottom", fill="x")

   
    def open_tour_detail_window(app, ma_tour):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `open_tour_detail_window` (open tour detail window).
        Tham số:
            app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if "open_tour_details" not in app:
            app["open_tour_details"] = {}
        app["open_tour_detail_window_func"] = open_tour_detail_window

        tour = app["ql"].find_tour(ma_tour)
        if not tour:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin tour.")
            return

        hdv = app["ql"].find_hdv(tour.get("hdvPhuTrach", ""))
        guest_count = app["ql"].get_occupied_seats(ma_tour)

        PASTEL_DETAIL = {
            "bg": "#edf6f9",
            "surface": "#ffffff",
            "title": "#1d3557",
            "muted": "#6c7a89",
            "border": "#cbd5e1",
            "section_bg": "#fff1e6",
            "section_bg_2": "#e8f6f0",
            "section_bg_3": "#f3ecff",
            "text": "#1f2937",
        }

        dia_diem_tham_quan = tour.get("diaDiemThamQuan", [])
        if isinstance(dia_diem_tham_quan, str):
            dia_diem_tham_quan = [x.strip() for x in dia_diem_tham_quan.split(",") if x.strip()]
        if not dia_diem_tham_quan:
            dia_diem_tham_quan = [tour.get("diemDen", "Chưa cập nhật")]

        ma_tour_upper = str(ma_tour).strip().upper()
        top = tk.Toplevel(app["root"])
        app["open_tour_details"][ma_tour_upper] = top
        
        def on_close():
            try:
                if "open_tour_details" in app:
                    app["open_tour_details"].pop(ma_tour_upper, None)
            except Exception:
                pass
            top.destroy()
            
        top.protocol("WM_DELETE_WINDOW", on_close)

        top.title(f"Chi tiết tour - {tour['ma']}")
        top.geometry("860x620")
        top.minsize(860, 620)
        top.configure(bg=PASTEL_DETAIL["bg"])
        top.transient(app["root"])
        top.grab_set()

        outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
        outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

        content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
        content_shell.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            content_shell,
            bg=PASTEL_DETAIL["bg"],
            highlightthickness=0,
            bd=0
        )
        v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
        bind_autohide_scrollbar(canvas, v_scroll, "vertical")
        canvas.pack(side="left", fill="both", expand=True)

        outer = tk.Frame(
            canvas,
            bg=PASTEL_DETAIL["surface"],
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        canvas_window = canvas.create_window((0, 0), window=outer, anchor="nw")

        def _on_frame_configure(event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            canvas.itemconfigure(canvas_window, width=event.width)

        outer.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except (tk.TclError, ValueError, AttributeError):
                pass

        def _bind_mousewheel(_event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
            Tham số:
                _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(_event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
            Tham số:
                _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            canvas.unbind_all("<MouseWheel>")

        top.bind("<Enter>", _bind_mousewheel)
        top.bind("<Leave>", _unbind_mousewheel)

        # ===== HEADER =====
        header = tk.Frame(outer, bg=PASTEL_DETAIL["surface"])
        header.pack(fill="x", padx=24, pady=(22, 14))

        tk.Label(
            header,
            text="CHI TIẾT TOUR",
            bg=PASTEL_DETAIL["surface"],
            fg=PASTEL_DETAIL["title"],
            font=("Times New Roman", 24, "bold")
        ).pack()

        tk.Label(
            header,
            text=tour.get("ten", ""),
            bg=PASTEL_DETAIL["surface"],
            fg=PASTEL_DETAIL["title"],
            font=("Times New Roman", 20, "bold")
        ).pack(pady=(4, 6))

        tk.Label(
            header,
            text=f"Mã tour: {tour.get('ma', '')}",
            bg=PASTEL_DETAIL["surface"],
            fg=PASTEL_DETAIL["muted"],
            font=("Times New Roman", 11, "italic")
        ).pack()

        def create_section(parent, title, bg_color):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `create_section` (create section).
            Tham số:
                parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            wrapper = tk.Frame(
                parent,
                bg=bg_color,
                highlightbackground=PASTEL_DETAIL["border"],
                highlightthickness=1
            )
            wrapper.pack(fill="x", padx=20, pady=(0, 14))

            tk.Label(
                wrapper,
                text=title,
                bg=bg_color,
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 15, "bold")
            ).pack(anchor="w", padx=16, pady=(12, 8))

            body = tk.Frame(wrapper, bg=bg_color)
            body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
            return body

        # ===== THÔNG TIN TỔNG QUAN =====
        info_body = create_section(outer, "Thông tin tổng quan", PASTEL_DETAIL["section_bg"])

        left = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 18))

        right = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
        right.pack(side="left", fill="both", expand=True)

        info_left = [
            ("Tên tour", tour.get("ten", "")),
            ("Mã tour", tour.get("ma", "")),
            ("Ngày khởi hành", tour.get("ngay", "")),
            ("Ngày kết thúc", tour.get("ngayKetThuc", "")),
            ("Số ngày", tour.get("soNgay", "")),
            ("Trạng thái", tour.get("trangThai", "")),
        ]

        info_right = [
            ("Điểm đi", tour.get("diemDi", "")),
            ("Điểm đến", tour.get("diemDen", "")),
            ("Sức chứa", str(tour.get("khach", ""))),
            ("Đã đặt", str(guest_count)),
            ("Giá tour", f"{safe_int(tour.get('gia', 0)):,} đ".replace(",", ".")),
            ("HDV phụ trách", build_hdv_display_label(app["ql"], tour.get("hdvPhuTrach", "")) or "Chưa xác định"),
        ]

        for label_text, value in info_left:
            row = tk.Frame(left, bg=PASTEL_DETAIL["section_bg"])
            row.pack(fill="x", pady=4)

            tk.Label(
                row,
                text=f"{label_text}:",
                width=16,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12)
            ).pack(side="left", fill="x", expand=True)

        for label_text, value in info_right:
            row = tk.Frame(right, bg=PASTEL_DETAIL["section_bg"])
            row.pack(fill="x", pady=4)

            tk.Label(
                row,
                text=f"{label_text}:",
                width=16,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12),
                wraplength=320,
                justify="left"
            ).pack(side="left", fill="x", expand=True)

        # ===== ĐIỀU HÀNH =====
        ops_body = create_section(outer, "Điều hành", PASTEL_DETAIL["section_bg_2"])

        ops_rows = [
            ("Ghi chú điều hành", tour.get("ghiChuDieuHanh", "") or "Không có"),
        ]

        for label_text, value in ops_rows:
            row = tk.Frame(ops_body, bg=PASTEL_DETAIL["section_bg_2"])
            row.pack(fill="x", pady=6)

            tk.Label(
                row,
                text=f"{label_text}:",
                width=16,
                anchor="nw",
                bg=PASTEL_DETAIL["section_bg_2"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg_2"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12),
                wraplength=760,
                justify="left"
            ).pack(side="left", fill="x", expand=True)

        # ===== LỊCH TRÌNH CHI TIẾT =====
        itinerary_body = create_section(outer, "Lịch trình chi tiết", PASTEL_DETAIL["section_bg_3"])
        
        itinerary_wrapper = tk.Frame(itinerary_body, bg=PASTEL_DETAIL["section_bg_3"])
        itinerary_wrapper.pack(fill="x", pady=(0, 8))

        itinerary_text = tk.Text(itinerary_wrapper, height=9, font=("Times New Roman", 12), wrap="word", relief="flat", bg=PASTEL_DETAIL["section_bg_3"])
        itinerary_sb = ttk.Scrollbar(itinerary_wrapper, orient="vertical", command=itinerary_text.yview)
        itinerary_text.configure(yscrollcommand=itinerary_sb.set)
        bind_autohide_scrollbar(itinerary_text, itinerary_sb, "vertical")

        itinerary_text.pack(side="left", fill="both", expand=True)

        itinerary_places = []
        lich_trinh = tour.get("lichTrinh", [])
        if isinstance(lich_trinh, str):
            lich_trinh = parse_itinerary_text(lich_trinh)
        if not isinstance(lich_trinh, list) or not lich_trinh:
            lich_trinh = [{"ngay": "Ngày 1", "tieuDe": f"{tour.get('diemDi', '')} - {tour.get('diemDen', '')}".strip(" -"), "diaDiem": [tour.get("diemDen", "")], "moTa": "Lịch trình đang được cập nhật."}]
        for item in lich_trinh:
            if not isinstance(item, dict):
                continue
            ngay = str(item.get("ngay", "")).strip()
            title = str(item.get("tieuDe", "")).strip()
            mo_ta = str(item.get("moTa", "")).strip()
            itinerary_text.insert("end", f"{ngay} - {title}\n")
            places = item.get("diaDiem", [])
            if isinstance(places, str):
                places = [p.strip() for p in places.split(",") if p.strip()]
            for place in places:
                place_name = str(place).strip()
                if place_name:
                    itinerary_places.append(place_name)
                    itinerary_text.insert("end", f"  • {place_name}\n")
            if mo_ta:
                itinerary_text.insert("end", f"  {mo_ta}\n")
            itinerary_text.insert("end", "\n")
        itinerary_text.configure(state="disabled")

        tk.Frame(outer, bg=PASTEL_DETAIL["surface"], height=10).pack(fill="x")

        # ===== FOOTER =====
        footer = tk.Frame(
            top,
            bg=PASTEL_DETAIL["surface"],
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        footer.pack(side="bottom", fill="x", padx=14, pady=14)

        footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
        footer_inner.pack(fill="x", padx=16, pady=10)

        style_button(
            footer_inner,
            "Cập nhật",
            THEME["primary"],
            lambda: open_tour_form(app, tour)
        ).pack(side="left", padx=(0, 8))

        style_button(
            footer_inner,
            "Thoát",
            THEME["danger"],
            on_close
        ).pack(side="right")

        set_status(app, f"Đã mở chi tiết tour {tour['ma']}", THEME["primary"])


    def on_double_click(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click` (on double click).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sel = tv.selection()
        if not sel:
            return
        ma = tv.item(sel[0])["values"][0]
        open_tour_detail_window(app, ma)

    tv.bind("<Double-1>", on_double_click)

  

    refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=True)

# =========================
# BOOKING MANAGEMENT
# =========================
# Mở cửa sổ xem chi tiết booking.
# Hiển thị đầy đủ thông tin khách, tour, thanh toán, hoàn tiền và danh sách khách đi cùng.
def open_booking_detail(app, ma_booking):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_booking_detail` (open booking detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = next((b for b in app["ql"].list_bookings if b.get("maBooking") == ma_booking), None)
    if not booking:
        messagebox.showerror("Lỗi", "Không tìm thấy booking.")
        return

    tour = app["ql"].find_tour(booking.get("maTour", ""))
    user = app["ql"].find_user(booking.get("usernameDat", "")) if booking.get("usernameDat") else None

    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }

    guest_list = booking.get("danhSachKhach", [])
    guest_lines = []
    for guest in guest_list:
        guest_lines.append(
            f"{guest.get('hoTen', '')} | {guest.get('gioiTinh', '')} | {guest.get('namSinh', '')}"
        )
    if not guest_lines:
        guest_lines = ["Chưa có danh sách khách chi tiết"]

    top = tk.Toplevel(app["root"])
    top.title(f"Chi tiết booking - {booking.get('maBooking', '')}")
    top.geometry("860x620")
    top.minsize(860, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_shell, bg=PASTEL_DETAIL["bg"], highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    bind_autohide_scrollbar(canvas, v_scroll, "vertical")
    canvas.pack(side="left", fill="both", expand=True)

    outer = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=outer, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    outer.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    header = tk.Frame(outer, bg=PASTEL_DETAIL["surface"])
    header.pack(fill="x", padx=24, pady=(22, 14))

    tk.Label(
        header,
        text="CHI TIẾT BOOKING",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 24, "bold")
    ).pack()

    tk.Label(
        header,
        text=f"{booking.get('maBooking', '')} - {booking.get('tenKhach', '')}",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 20, "bold")
    ).pack(pady=(4, 6))

    tk.Label(
        header,
        text=f"Tour liên quan: {booking.get('maTour', '')}",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack()

    def create_section(parent, title, bg_color):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `create_section` (create section).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        wrapper = tk.Frame(
            parent,
            bg=bg_color,
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        wrapper.pack(fill="x", padx=20, pady=(0, 14))

        tk.Label(
            wrapper,
            text=title,
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 15, "bold")
        ).pack(anchor="w", padx=16, pady=(12, 8))

        body = tk.Frame(wrapper, bg=bg_color)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return body

    # ===== THÔNG TIN BOOKING =====
    info_body = create_section(outer, "Thông tin booking", PASTEL_DETAIL["section_bg"])

    left = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
    left.pack(side="left", fill="both", expand=True, padx=(0, 18))

    right = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
    right.pack(side="left", fill="both", expand=True)

    tour_label = build_tour_display_label(app["ql"], booking.get("maTour", ""))
    hdv_label = build_hdv_display_label(app["ql"], tour.get("hdvPhuTrach", "")) if tour else ""

    info_left = [
        ("Mã booking", booking.get("maBooking", "")),
        ("Tour", tour_label or booking.get("maTour", "")),
        ("Tên khách", booking.get("tenKhach", "")),
        ("Số điện thoại", booking.get("sdt", "")),
        ("Số người", booking.get("soNguoi", "")),
        ("Trạng thái", booking.get("trangThai", "")),
    ]

    info_right = [
        ("Ngày đặt", booking.get("ngayDat", "")),
        ("Username đặt", booking.get("usernameDat", "")),
        ("Khách hàng hệ thống", user.get("fullname", "") if user else "Không liên kết"),
        ("Mã tour", booking.get("maTour", "")),
        ("Điểm đến", tour.get("diemDen", "") if tour else ""),
        ("HDV phụ trách", hdv_label if hdv_label else "Chưa phân công"),
    ]

    for label_text, value in info_left:
        row = tk.Frame(left, bg=PASTEL_DETAIL["section_bg"])
        row.pack(fill="x", pady=4)
        tk.Label(
            row, text=f"{label_text}:", width=16, anchor="w",
            bg=PASTEL_DETAIL["section_bg"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")
        tk.Label(
            row, text=value, anchor="w",
            bg=PASTEL_DETAIL["section_bg"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True)

    for label_text, value in info_right:
        row = tk.Frame(right, bg=PASTEL_DETAIL["section_bg"])
        row.pack(fill="x", pady=4)
        tk.Label(
            row, text=f"{label_text}:", width=16, anchor="w",
            bg=PASTEL_DETAIL["section_bg"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")
        tk.Label(
            row, text=value, anchor="w",
            bg=PASTEL_DETAIL["section_bg"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12), wraplength=320, justify="left"
        ).pack(side="left", fill="x", expand=True)

    # ===== THANH TOÁN =====
    payment_body = create_section(outer, "Thanh toán & ghi chú", PASTEL_DETAIL["section_bg_2"])

    age_breakdown = booking.get("coCauDoTuoi", {}) if isinstance(booking.get("coCauDoTuoi"), dict) else {}
    age_breakdown_text = (
        f"Trẻ em: {safe_int(age_breakdown.get('treEm', 0))} | "
        f"Trung niên: {safe_int(age_breakdown.get('trungNien', 0))} | "
        f"Người cao tuổi: {safe_int(age_breakdown.get('nguoiCaoTuoi', 0))}"
    )
    payment_rows = [
        ("Tổng gốc", format_currency(booking.get("tongTienGoc", 0))),
        ("Giảm đối tượng", format_currency(booking.get("giamGiaDoiTuong", 0))),
        ("Cơ cấu độ tuổi", age_breakdown_text),
        ("Mã voucher", booking.get("maVoucher", "") or "Không có"),
        ("Tên voucher", booking.get("tenVoucher", "") or "Không có"),
        ("Giảm voucher", format_currency(booking.get("giamGiaVoucher", 0))),
        ("Tổng tiền", f"{safe_int(booking.get('tongTien', 0)):,} đ".replace(",", ".")),
        ("Tiền cọc", f"{safe_int(booking.get('tienCoc', 0)):,} đ".replace(",", ".")),
        ("Đã thanh toán", f"{safe_int(booking.get('daThanhToan', 0)):,} đ".replace(",", ".")),
        ("Còn nợ", f"{safe_int(booking.get('conNo', 0)):,} đ".replace(",", ".")),
        ("Trạng thái hoàn", booking.get("trangThaiHoanTien", "") or "Không có"),
        ("Số tiền hoàn", f"{safe_int(booking.get('soTienHoan', 0)):,} đ".replace(",", ".")),
        ("Ngày yêu cầu hoàn", booking.get("ngayYeuCauHoanTien", "") or "Không có"),
        ("Ngày xử lý hoàn", booking.get("ngayXuLyHoanTien", "") or "Không có"),
        ("Người xử lý", booking.get("nguoiXuLyHoanTien", "") or "Không có"),
        ("Ghi chú hoàn tiền", booking.get("ghiChuHoanTien", "") or "Không có"),
        ("Hình thức thanh toán", booking.get("hinhThucThanhToan", "")),
        ("Nguồn khách", booking.get("nguonKhach", "")),
        ("Ghi chú", booking.get("ghiChu", "") or "Không có"),
    ]

    for label_text, value in payment_rows:
        row = tk.Frame(payment_body, bg=PASTEL_DETAIL["section_bg_2"])
        row.pack(fill="x", pady=6)
        tk.Label(
            row, text=f"{label_text}:", width=18, anchor="nw",
            bg=PASTEL_DETAIL["section_bg_2"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")
        tk.Label(
            row, text=value, anchor="w",
            bg=PASTEL_DETAIL["section_bg_2"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12), wraplength=760, justify="left"
        ).pack(side="left", fill="x", expand=True)

    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    footer_inner.pack(fill="x", padx=16, pady=10)

    style_button(
        footer_inner,
        "Cập nhật",
        THEME["primary"],
        lambda: open_booking_form(app, booking)
    ).pack(side="left", padx=(0, 8))

    if booking.get("trangThai") == "Chờ hoàn tiền":
        style_button(
            footer_inner,
            "Duyệt hoàn",
            "#16a34a",
            lambda: [top.destroy(), handle_refund_decision(app, True, booking.get("maBooking", ""))]
        ).pack(side="left", padx=(0, 8))
        style_button(
            footer_inner,
            "Từ chối hoàn",
            "#dc2626",
            lambda: [top.destroy(), handle_refund_decision(app, False, booking.get("maBooking", ""))]
        ).pack(side="left", padx=(0, 8))

    style_button(
        footer_inner,
        "Thoát",
        THEME["danger"],
        top.destroy
    ).pack(side="right")

    set_status(app, f"Đã mở chi tiết booking {booking.get('maBooking', '')}", THEME["primary"])


# Trả về mã booking đang được chọn trong bảng; nếu chưa chọn thì trả về chuỗi rỗng.
def _selected_booking_code(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_selected_booking_code` ( selected booking code).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree = app.get("tv_booking")
    if not tree:
        return ""
    selection = tree.selection()
    if not selection:
        return ""
    return str(tree.item(selection[0])["values"][0]).strip()


# Mở cửa sổ tổng hợp booking theo từng tour để admin theo dõi sức chứa và doanh thu nhanh.
def open_booking_summary_window(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_booking_summary_window` (open booking summary window).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    rows = summarize_bookings_by_tour(app["ql"])

    top = tk.Toplevel(app["root"])
    top.title("Tổng hợp booking theo tour")
    top.geometry("1080x520")
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()

    header = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    header.pack(fill="x", padx=18, pady=(16, 10))
    tk.Label(
        header,
        text="TỔNG HỢP BOOKING THEO TOUR",
        bg=THEME["surface"],
        fg=THEME["text"],
        font=("Times New Roman", 18, "bold"),
    ).pack(anchor="w", padx=16, pady=(12, 2))
    tk.Label(
        header,
        text=f"Số dòng: {len(rows)} | Cập nhật lúc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}",
        bg=THEME["surface"],
        fg=THEME["muted"],
        font=("Times New Roman", 11, "italic"),
    ).pack(anchor="w", padx=16, pady=(0, 12))

    total_booking = sum(safe_int(r.get("tongBooking", 0)) for r in rows)
    total_active_guest = sum(safe_int(r.get("khachHieuLuc", 0)) for r in rows)
    total_pending_refund = sum(safe_int(r.get("choHoanTien", 0)) for r in rows)
    total_revenue = sum(safe_int(r.get("doanhThu", 0)) for r in rows)

    stats = tk.Frame(top, bg=THEME["bg"])
    stats.pack(fill="x", padx=18, pady=(0, 10))
    stat_items = [
        ("Tổng booking", str(total_booking), THEME["primary"]),
        ("Khách hiệu lực", str(total_active_guest), THEME["success"]),
        ("Chờ hoàn tiền", str(total_pending_refund), "#7c3aed"),
        ("Doanh thu dự kiến", format_currency(total_revenue), THEME["warning"]),
    ]
    for title, value, color in stat_items:
        card = tk.Frame(stats, bg=THEME["surface"], bd=1, relief="solid")
        card.pack(side="left", fill="both", expand=True, padx=6)
        tk.Frame(card, bg=color, height=3).pack(fill="x")
        tk.Label(card, text=title, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(card, text=value, bg=THEME["surface"], fg=color, font=("Times New Roman", 14, "bold")).pack(anchor="w", padx=12, pady=(0, 10))

    wrapper = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    cols = ("ma", "ten", "booking", "khachhang", "hieuluc", "trong", "refund", "doanhthu", "dathu")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=14)

    headers = [
        ("ma", "Mã tour", 90),
        ("ten", "Tên tour", 240),
        ("booking", "Số booking", 90),
        ("khachhang", "Khách hàng", 95),
        ("hieuluc", "Khách hiệu lực", 100),
        ("trong", "Chỗ còn", 90),
        ("refund", "Chờ hoàn", 90),
        ("doanhthu", "Doanh thu", 130),
        ("dathu", "Đã thu", 130),
    ]
    numeric_cols = {"booking", "khachhang", "hieuluc", "trong", "refund", "doanhthu", "dathu"}
    for column, title, width in headers:
        tv.heading(column, text=title)
        tv.column(column, anchor=("e" if column in numeric_cols else "center"), width=width)

    for row in rows:
        tv.insert(
            "",
            "end",
            values=(
                shorten_text(row["maTour"], 18),
                shorten_text(row["tenTour"], 32),
                shorten_text(row["tongBooking"], 10),
                shorten_text(row["tongKhachHang"], 10),
                shorten_text(row["khachHieuLuc"], 10),
                shorten_text(row["choConLai"], 10),
                shorten_text(row["choHoanTien"], 10),
                shorten_text(format_currency(row["doanhThu"]), 18),
                shorten_text(format_currency(row["daThu"]), 18),
            ),
        )

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
    bind_autohide_scrollbar(tv, sy, "vertical")
    bind_autohide_scrollbar(tv, sx, "horizontal")
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")
    sx.pack(side="bottom", fill="x")
    apply_zebra(tv)

# Mở báo cáo doanh thu đa góc nhìn: theo tour, theo tháng và theo quý.
def open_revenue_report_window(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_revenue_report_window` (open revenue report window).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    report = build_revenue_report(app["ql"])
    overview = report["overview"]

    top = tk.Toplevel(app["root"])
    top.title("Báo cáo doanh thu")
    screen_w = top.winfo_screenwidth()
    screen_h = top.winfo_screenheight()
    width = max(1050, min(1400, screen_w - 80))
    height = max(700, min(900, screen_h - 120))
    pos_x = max((screen_w - width) // 2, 0)
    pos_y = max((screen_h - height) // 2, 0)
    top.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
    top.minsize(1050, 700)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()

    header = tk.Frame(top, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1, bd=0)
    header.pack(fill="x", padx=18, pady=(16, 10))
    tk.Label(
        header,
        text="BÁO CÁO DOANH THU CHI TIẾT",
        bg=THEME["surface"],
        fg=THEME["text"],
        font=("Times New Roman", 18, "bold"),
    ).pack(anchor="w", padx=16, pady=(12, 2))
    tk.Label(
        header,
        text=f"Tóm tắt booking, doanh thu thực nhận và công nợ chi tiết | Cập nhật {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}",
        bg=THEME["surface"],
        fg=THEME["muted"],
        font=("Times New Roman", 11, "italic"),
    ).pack(anchor="w", padx=16, pady=(0, 12))

    stats = tk.Frame(top, bg=THEME["bg"])
    stats.pack(fill="x", padx=18, pady=(0, 10))
    stat_items = [
        ("Tổng phải thu", format_currency(overview.get("tongPhaiThu", overview.get("doanhThuDuKien", 0))), THEME["primary"]),
        ("Booking hiệu lực", str(overview["bookingHieuLuc"]), THEME["success"]),
        ("Số tiền đã thu", format_currency(overview["daThu"]), "#0ea5e9"),
        ("Đã hoàn/trừ tiền", format_currency(overview["tongHoanTien"]), THEME["muted"]),
        ("Doanh thu thực nhận", format_currency(overview["doanhThuThuan"]), "#059669"),
        ("Số tiền còn nợ", format_currency(overview["conNo"]), THEME["danger"]),
        ("Booking chờ hoàn", f"{overview['dangChoHoan']} booking", "#7c3aed"),
        ("Tiền chờ hoàn", format_currency(overview["soTienChoHoan"]), "#7c3aed"),
    ]

    column_count = 4
    for col in range(column_count):
        stats.grid_columnconfigure(col, weight=1)

    for idx, (title, value, color) in enumerate(stat_items):
        row, col = divmod(idx, column_count)
        card = tk.Frame(stats, bg=THEME["surface"], bd=1, relief="solid")
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        tk.Frame(card, bg=color, height=4).pack(fill="x")
        tk.Label(card, text=title, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(card, text=value, bg=THEME["surface"], fg=color, font=("Times New Roman", 15, "bold")).pack(anchor="w", padx=12, pady=(0, 10))

    actions = tk.Frame(top, bg=THEME["bg"])
    actions.pack(fill="x", padx=18, pady=(0, 10))

    def refresh_report_window():
        app["ql"].load()
        top.destroy()
        open_revenue_report_window(app)

    style_button(actions, "Làm mới", "#0ea5e9", refresh_report_window).pack(side="left")

    style = ttk.Style(top)
    style.configure("Report.TNotebook", background=THEME["bg"], borderwidth=0)
    style.configure(
        "Report.TNotebook.Tab",
        padding=(16, 8),
        font=("Times New Roman", 11, "bold"),
        background=THEME["heading_bg"],
        foreground=THEME["text"],
    )
    style.map(
        "Report.TNotebook.Tab",
        background=[("selected", THEME["surface"])],
        foreground=[("selected", THEME["primary"])],
    )

    notebook = ttk.Notebook(top, style="Report.TNotebook")
    notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def build_report_tab(title, rows, columns, detail_rows=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `build_report_tab` (build report tab).
        Tham số:
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            rows: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            columns: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        frame = tk.Frame(notebook, bg=THEME["surface"])
        notebook.add(frame, text=title)

        tab_head = tk.Frame(frame, bg=THEME["surface"])
        tab_head.pack(fill="x", padx=10, pady=(10, 6))
        tk.Label(
            tab_head,
            text=f"Dữ liệu {title.lower()}",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=("Times New Roman", 13, "bold"),
        ).pack(side="left")
        tk.Label(
            tab_head,
            text=f"{len(rows)} dòng",
            bg=THEME["surface"],
            fg=THEME["muted"],
            font=("Times New Roman", 11, "italic"),
        ).pack(side="right")

        wrapper = tk.Frame(frame, bg=THEME["surface"], bd=1, relief="solid")
        wrapper.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tree = ttk.Treeview(wrapper, columns=[column[0] for column in columns], show="headings", height=16)
        numeric_keywords = ("booking", "nguoi", "doanhthu", "dathu", "conno", "hoan", "thuan", "gop")
        for column, text, width in columns:
            tree.heading(column, text=text)
            anchor = "e" if any(key in column for key in numeric_keywords) else "center"
            is_stretch = (column in ("ten", "ky", "tenTour"))
            tree.column(column, anchor=anchor, width=width, minwidth=max(60, width - 20), stretch=is_stretch)

        for row in rows:
            tree.insert("", "end", values=tuple(shorten_text(v, 35) for v in row))

        if not rows:
            tree.insert("", "end", values=tuple("Không có dữ liệu" if i == 0 else "" for i in range(len(columns))))

        sy = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
        bind_autohide_scrollbar(tree, sy, "vertical")
        bind_autohide_scrollbar(tree, sx, "horizontal")
        tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        tree.pack(side="left", fill="both", expand=True)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        apply_zebra(tree)

        tree.bind("<Double-1>", lambda _event: None)

    build_report_tab(
        "Theo tour",
        [
            (
                row["maTour"],
                row["tenTour"],
                row["tongBooking"],
                row["bookingHieuLuc"],
                row["tongNguoi"],
                format_currency(row.get("tongPhaiThu", row.get("doanhThuDuKien", 0))),
                format_currency(row["daThu"]),
                format_currency(row["hoanTien"]),
                format_currency(row["doanhThuThuan"]),
                format_currency(row["conNo"]),
            )
            for row in report["by_tour"]
        ],
        [
            ("ma", "Mã tour", 80),
            ("ten", "Tên tour", 220),
            ("booking", "Tổng BK", 85),
            ("hieuluc", "BK hiệu lực", 95),
            ("nguoi", "Số người", 85),
            ("phaithu", "Tổng phải thu", 125),
            ("dathu", "Đã thu", 110),
            ("hoantien", "Hoàn tiền", 110),
            ("thucnhan", "Thực nhận", 120),
            ("conno", "Còn nợ", 110),
        ],
        detail_rows=[
            {
                "Mã tour": row["maTour"],
                "Tên tour": row["tenTour"],
                "Tổng booking": row["tongBooking"],
                "Tổng số người": row["tongNguoi"],
                "Tổng phải thu": format_currency(row.get("tongPhaiThu", row.get("doanhThuDuKien", 0))),
                "Đã thu": format_currency(row["daThu"]),
                "Hoàn tiền": format_currency(row["hoanTien"]),
                "Thực nhận": format_currency(row["doanhThuThuan"]),
                "Còn nợ": format_currency(row["conNo"]),
            }
            for row in report["by_tour"]
        ],
    )
    build_report_tab(
        "Theo tháng",
        [
            (
                row["ky"],
                row["tongBooking"],
                row["bookingHieuLuc"],
                row["tongNguoi"],
                format_currency(row["daThu"]),
                format_currency(row["hoanTien"]),
                format_currency(row["doanhThuThuan"]),
                format_currency(row["conNo"]),
            )
            for row in report["by_month"]
        ],
        [
            ("ky", "Tháng", 100),
            ("booking", "Tổng BK", 85),
            ("hieuluc", "BK hiệu lực", 95),
            ("nguoi", "Số người", 85),
            ("dathu", "Đã thu", 120),
            ("hoantien", "Hoàn tiền", 120),
            ("thucnhan", "Thực nhận", 130),
            ("conno", "Còn nợ", 120),
        ],
        detail_rows=[
            {
                "Kỳ báo cáo": row["ky"],
                "Tổng booking": row["tongBooking"],
                "Tổng số người": row["tongNguoi"],
                "Đã thu": format_currency(row["daThu"]),
                "Hoàn tiền": format_currency(row["hoanTien"]),
                "Thực nhận": format_currency(row["doanhThuThuan"]),
                "Còn nợ": format_currency(row["conNo"]),
            }
            for row in report["by_month"]
        ],
    )
    build_report_tab(
        "Theo quý",
        [
            (
                row["ky"],
                row["tongBooking"],
                row["bookingHieuLuc"],
                row["tongNguoi"],
                format_currency(row["daThu"]),
                format_currency(row["hoanTien"]),
                format_currency(row["doanhThuThuan"]),
                format_currency(row["conNo"]),
            )
            for row in report["by_quarter"]
        ],
        [
            ("ky", "Quý", 100),
            ("booking", "Tổng BK", 85),
            ("hieuluc", "BK hiệu lực", 95),
            ("nguoi", "Số người", 85),
            ("dathu", "Đã thu", 120),
            ("hoantien", "Hoàn tiền", 120),
            ("thucnhan", "Thực nhận", 130),
            ("conno", "Còn nợ", 120),
        ],
        detail_rows=[
            {
                "Kỳ báo cáo": row["ky"],
                "Tổng booking": row["tongBooking"],
                "Tổng số người": row["tongNguoi"],
                "Đã thu": format_currency(row["daThu"]),
                "Hoàn tiền": format_currency(row["hoanTien"]),
                "Thực nhận": format_currency(row["doanhThuThuan"]),
                "Còn nợ": format_currency(row["conNo"]),
            }
            for row in report["by_quarter"]
        ],
    )

    # Tab 4: Biểu đồ trực quan
    chart_tab = tk.Frame(notebook, bg=THEME["surface"])
    notebook.add(chart_tab, text="Biểu đồ trực quan")

    chart_wrapper = tk.Frame(chart_tab, bg=THEME["surface"])
    chart_wrapper.pack(fill="both", expand=True, padx=15, pady=15)
    _render_matplotlib_charts(chart_wrapper, report)

# Xử lý thao tác duyệt hoàn / từ chối hoàn tiền cho booking.
# Hàm này chỉ điều phối giao diện, còn nghiệp vụ chính được ủy quyền cho service ở core.services.
def handle_refund_decision(app, approve=True, ma_booking=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `handle_refund_decision` (handle refund decision).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        approve: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    ma_booking = ma_booking or _selected_booking_code(app)
    if not ma_booking:
        messagebox.showwarning("Thông báo", "Vui lòng chọn booking cần xử lý hoàn tiền.")
        return

    prompt = "Ghi chú xử lý hoàn tiền (có thể để trống):" if approve else "Lý do từ chối hoàn tiền:"
    note = simpledialog.askstring("Xử lý hoàn tiền", prompt, parent=app["root"])
    if note is None and not approve:
        return

    action_label = "duyệt" if approve else "từ chối"
    if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn {action_label} hoàn tiền cho booking {ma_booking}?"):
        return

    if approve:
        result = service_approve_refund(app["ql"], ma_booking, actor=get_admin_actor(app), note=note or "")
    else:
        result = service_reject_refund(app["ql"], ma_booking, actor=get_admin_actor(app), note=note or "")

    if not result.success:
        messagebox.showwarning("Không thể xử lý", result.message)
        return

    refresh_bookings(app, app["search_booking_var"].get())
    if app.get("tv_tour"):
        refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=True)
    set_status(app, result.message, THEME["success"] if approve else THEME["warning"])
    messagebox.showinfo("Thành công", result.message)

# Kiểm tra dữ liệu booking trước khi lưu.
# Ràng buộc chính: mã booking, tour tồn tại, username đặt hợp lệ, đủ chỗ trống,
# và không cho đặt vào tour đã hủy / tạm hoãn / hoàn tất.
def validate_booking(app, form_data, old_ma=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_booking` (validate booking).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        form_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_ma: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    form_data["maBooking"] = normalize_code(form_data.get("maBooking", ""))
    form_data["maTour"] = normalize_code(form_data.get("maTour", ""))
    form_data["tenKhach"] = normalize_name_case(form_data.get("tenKhach", ""))
    form_data["sdt"] = normalize_spaces(form_data.get("sdt", ""))
    form_data["soNguoi"] = normalize_spaces(form_data.get("soNguoi", ""))
    form_data["trangThai"] = normalize_spaces(form_data.get("trangThai", ""))
    form_data["usernameDat"] = normalize_spaces(form_data.get("usernameDat", ""))
    form_data["ghiChu"] = normalize_spaces(form_data.get("ghiChu", ""))

    required = ["maBooking", "maTour", "tenKhach", "sdt", "soNguoi", "trangThai"]

    if not all(str(form_data.get(k, "")).strip() for k in required):
        return False, "Vui lòng nhập đầy đủ thông tin booking."

    if not re.fullmatch(r"BK\d{2,}", str(form_data["maBooking"]).strip()):
        return False, "Mã booking phải theo dạng BK01, BK02..."
    if old_ma and normalize_code(form_data["maBooking"]) != normalize_code(old_ma):
        return False, "Mã booking là khóa chính, không được phép thay đổi."

    if len(str(form_data["tenKhach"]).strip()) < 3:
        return False, "Tên khách hàng quá ngắn."

    if not is_valid_phone(form_data["sdt"]):
        return False, "Số điện thoại khách hàng không hợp lệ."

    if not str(form_data["soNguoi"]).isdigit() or int(form_data["soNguoi"]) <= 0:
        return False, "Số người đi phải là số nguyên dương."

    tour = app["ql"].find_tour(form_data["maTour"])
    if not tour:
        return False, "Tour được chọn không tồn tại."

    username_dat = str(form_data.get("usernameDat", "")).strip()
    if username_dat:
        linked_user = app["ql"].find_user(username_dat) or next(
            (
                u for u in app["ql"].list_users
                if str(u.get("username", "")).strip().lower() == username_dat.lower()
            ),
            None,
        )
        if not linked_user:
            return False, "Username đặt không tồn tại trong hệ thống."

    for b in app["ql"].list_bookings:
        if b.get("maBooking") == form_data["maBooking"] and b.get("maBooking") != old_ma:
            return False, "Mã booking này đã tồn tại."

    occupied = app["ql"].get_occupied_seats(form_data["maTour"])
    old_people = 0

    if old_ma:
        old_booking = next(
            (b for b in app["ql"].list_bookings if b.get("maBooking") == old_ma),
            None
        )
        if (
            old_booking
            and normalize_code(old_booking.get("maTour", "")) == form_data["maTour"]
            and old_booking.get("trangThai") not in BOOKING_CANCEL_STATUSES
        ):
            old_people = safe_int(old_booking.get("soNguoi", 0))

    if form_data["trangThai"] not in BOOKING_CANCEL_STATUSES:
        if occupied - old_people + int(form_data["soNguoi"]) > int(tour["khach"]):
            return False, f"Tour này không đủ chỗ cho {form_data['soNguoi']} người."

    tour_status = normalize_tour_status(tour.get("trangThai", ""))
    start_date = parse_ddmmyyyy(tour.get("ngay"))
    capacity = max(1, safe_int(tour.get("khach", 1)))
    if (
        form_data["trangThai"] not in BOOKING_CANCEL_STATUSES
        and not is_booking_allowed(tour_status, start_date, occupied=occupied - old_people, capacity=capacity)
    ):
        return False, f"Không thể đặt chỗ cho tour đang ở trạng thái '{tour.get('trangThai')}'."

    return True, ""


def _next_booking_code_ui(app) -> str:
    """Sinh mã booking kế tiếp theo dạng BKxx."""
    max_seq = 0
    for booking in app["ql"].list_bookings:
        code = normalize_code(booking.get("maBooking", ""))
        matched = re.fullmatch(r"BK(\d+)", code)
        if not matched:
            continue
        try:
            max_seq = max(max_seq, int(matched.group(1)))
        except ValueError:
            continue
    return f"BK{max_seq + 1:02d}"


# Nạp lại danh sách booking lên Treeview, có hỗ trợ lọc theo mã/tên/trạng thái/hoàn tiền.
def refresh_bookings(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_bookings` (refresh bookings).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree = app.get("tv_booking")
    if not tree:
        return

    for item in tree.get_children():
        tree.delete(item)

    rows = app["ql"].list_bookings
    if keyword:
        kw = keyword.lower().strip()
        rows = [
            b for b in rows
            if kw in str(b.get("maBooking", "")).lower()
            or kw in str(b.get("tenKhach", "")).lower()
            or kw in str(b.get("maTour", "")).lower()
            or kw in str((app["ql"].find_tour(b.get("maTour", "")) or {}).get("ten", "")).lower()
            or kw in str(b.get("trangThai", "")).lower()
            or kw in str(b.get("trangThaiHoanTien", "")).lower()
        ]

    for b in rows:
        ngay_dat = (
            b.get("ngayDat")
            or b.get("ngayTao")
            or b.get("createdAt")
            or b.get("date")
            or ""
        )
        tree.insert(
            "",
            "end",
            values=(
                shorten_text(b.get("maBooking", ""), 200),
                shorten_text(b.get("maTour", ""), 18),
                shorten_text(b.get("tenKhach", ""), 30),
                shorten_text(b.get("sdt", ""), 15),
                shorten_text(b.get("soNguoi", ""), 10),
                shorten_text(format_currency(b.get("tongTien", 0)), 18),
                shorten_text(b.get("trangThai", ""), 20),
                shorten_text(ngay_dat, 16),
            )
        )

    apply_zebra(tree)
    status_text = f"Đang ở Quản lý booking - Hiển thị {len(rows)} booking"
    update_admin_status_card(app, "booking", status_text, THEME["primary"])

# Mở form thêm mới / chỉnh sửa booking.
# Đây là form có logic phụ trợ khá nhiều: tự tính tổng tiền, tiền cọc, còn nợ,
# chuẩn hóa cơ cấu độ tuổi và suy ra trạng thái thanh toán.
def open_booking_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_booking_form` (open booking form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin đặt chỗ (Booking)")
    top.geometry("760x680")
    top.minsize(680, 520)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()
    top.resizable(True, True)

    card = tk.Frame(
        top,
        bg=THEME["surface"],
        bd=0,
        highlightbackground="#d8e2f0",
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(
        card,
        text="THÔNG TIN ĐẶT CHỖ",
        bg=THEME["surface"],
        font=("Times New Roman", 18, "bold")
    ).pack(pady=(14, 10))

    scroll_outer, form = create_scrollable_form(card, THEME["surface"])
    scroll_outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    tour_options = []
    tour_label_by_code = {}
    for t in app["ql"].list_tours:
        code = normalize_code(t.get("ma", ""))
        label = build_tour_display_label(app["ql"], code)
        if not code:
            continue
        tour_label_by_code[code] = label
        tour_options.append(label)

    fields = [
        ("Mã booking", "maBooking", "entry"),
        ("Tour", "maTour", "combo", tour_options),
        ("Tên khách hàng", "tenKhach", "entry"),
        ("Số điện thoại", "sdt", "entry"),
        ("Số người đi", "soNguoi", "entry"),
        ("Trẻ em (<12)", "treEm", "entry"),
        ("Trung niên", "trungNien", "entry"),
        ("Người cao tuổi (>65)", "nguoiCaoTuoi", "entry"),
        ("Tổng tiền", "tongTien", "entry"),
        ("Tiền cọc", "tienCoc", "entry"),
        ("Đã thanh toán", "daThanhToan", "entry"),
        ("Còn nợ", "conNo", "entry"),
        ("Hình thức thanh toán", "hinhThucThanhToan", "combo", ["Chưa thanh toán", "Tiền mặt", "Chuyển khoản", "Thẻ", "Momo", "ZaloPay", "VNPay"]),
        ("Nguồn khách", "nguonKhach", "combo", ["Khách lẻ", "Khách đoàn", "Khách quen", "Facebook", "Fanpage", "Zalo", "Website", "Tiktok", "Đại lý"]),
        ("Username đặt", "usernameDat", "entry"),
        ("Ghi chú", "ghiChu", "entry"),
        ("Trạng thái", "trangThai", "combo", BOOKING_STATUSES),
    ]

    widgets = {}

    def _extract_tour_code(raw_value):
        text = normalize_spaces(raw_value)
        if not text:
            return ""
        return normalize_code(text.split("-", 1)[0])

    for label, key, kind, *extra in fields:
        row = tk.Frame(form, bg=THEME["surface"])
        row.pack(fill="x", pady=7)

        tk.Label(
            row,
            text=label,
            width=18,
            anchor="w",
            bg=THEME["surface"],
            font=("Times New Roman", 13, "bold")
        ).pack(side="left")

        if kind == "entry":
            w = tk.Entry(row, font=("Times New Roman", 13))
            w.pack(side="left", fill="x", expand=True, ipady=5)
            style_form_entry_widget(w)
        else:
            w = ttk.Combobox(
                row,
                font=("Times New Roman", 12),
                values=extra[0],
                state="readonly",
                style=FORM_COMBOBOX_STYLE,
            )
            w.pack(side="left", fill="x", expand=True, ipady=5)

        widgets[key] = w
        if data:
            if key in {"treEm", "trungNien", "nguoiCaoTuoi"}:
                age_cfg = data.get("coCauDoTuoi", {}) if isinstance(data.get("coCauDoTuoi"), dict) else {}
                val = age_cfg.get(key, 0)
            else:
                val = data.get(key, "")
            if kind == "entry":
                w.insert(0, str(val))
            else:
                if key == "maTour":
                    code = normalize_code(val)
                    w.set(tour_label_by_code.get(code, code))
                else:
                    w.set(val)

    if not data:
        widgets["maBooking"].insert(0, _next_booking_code_ui(app))
        widgets["soNguoi"].insert(0, "1")
        widgets["treEm"].insert(0, "0")
        widgets["trungNien"].insert(0, "1")
        widgets["nguoiCaoTuoi"].insert(0, "0")
        widgets["tongTien"].insert(0, "0")
        widgets["tienCoc"].insert(0, "0")
        widgets["daThanhToan"].insert(0, "0")
        widgets["conNo"].insert(0, "0")
        widgets["hinhThucThanhToan"].set("Chưa thanh toán")
        widgets["nguonKhach"].set("Khách lẻ")
        widgets["trangThai"].set("Mới tạo")

    widgets["maBooking"].config(state="readonly", readonlybackground="#f8fafc")

    tk.Label(
        form,
        text="Hệ thống sẽ tự tính lại tổng gốc, giảm theo độ tuổi, công nợ và trạng thái theo tour + thanh toán hiện có.",
        bg=THEME["surface"],
        fg=THEME["muted"],
        font=("Times New Roman", 11, "italic"),
        wraplength=520,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))

    calc_summary_var = tk.StringVar(value="")
    calc_summary_lbl = tk.Label(
        form,
        textvariable=calc_summary_var,
        bg=THEME["surface"],
        fg=THEME["success"],
        font=("Times New Roman", 11, "bold"),
        wraplength=540,
        justify="left",
    )
    calc_summary_lbl.pack(anchor="w", pady=(8, 0))

    readonly_fields = {"tongTien", "conNo"}

    def set_entry_value(key, value):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `set_entry_value` (set entry value).
        Tham số:
            key: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        widget = widgets[key]
        if key in readonly_fields:
            widget.config(state="normal")
        widget.delete(0, "end")
        widget.insert(0, str(value))
        if key in readonly_fields:
            widget.config(state="readonly", readonlybackground="#f8fafc")

    def build_payment_status(total_amount, paid_amount):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `build_payment_status` (build payment status).
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
        if paid_amount <= 0:
            return BOOKING_STATUSES[0]
        if total_amount > 0 and paid_amount < total_amount:
            return BOOKING_STATUSES[1]
        return BOOKING_STATUSES[2]

    def refresh_booking_quote():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `refresh_booking_quote` (refresh booking quote).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        people = max(1, safe_int(widgets["soNguoi"].get() or 1))
        age_breakdown = normalize_passenger_breakdown(
            {
                "treEm": widgets["treEm"].get(),
                "trungNien": widgets["trungNien"].get(),
                "nguoiCaoTuoi": widgets["nguoiCaoTuoi"].get(),
            },
            people,
        )
        if age_breakdown is None:
            calc_summary_var.set("Cơ cấu độ tuổi đang vượt quá số người đi.")
            calc_summary_lbl.config(fg=THEME["danger"])
            return None

        set_entry_value("soNguoi", people)
        set_entry_value("treEm", age_breakdown["treEm"])
        set_entry_value("trungNien", age_breakdown["trungNien"])
        set_entry_value("nguoiCaoTuoi", age_breakdown["nguoiCaoTuoi"])

        selected_tour_code = _extract_tour_code(widgets["maTour"].get())
        tour = app["ql"].find_tour(selected_tour_code)
        price_per_person = max(0, safe_int(tour.get("gia", 0))) if tour else 0
        gross_total = price_per_person * people
        age_discount = min(calculate_age_discount(price_per_person, age_breakdown), gross_total)
        voucher_discount = max(0, safe_int(data.get("giamGiaVoucher", 0) if data else 0))
        voucher_discount = min(voucher_discount, max(gross_total - age_discount, 0))
        total_amount = max(gross_total - age_discount - voucher_discount, 0)

        tien_coc = max(0, safe_int(widgets["tienCoc"].get()))
        da_thanh_toan = max(max(0, safe_int(widgets["daThanhToan"].get())), tien_coc)
        da_thanh_toan = min(da_thanh_toan, total_amount)
        tien_coc = min(tien_coc, da_thanh_toan)
        con_no = max(total_amount - da_thanh_toan, 0)

        set_entry_value("tienCoc", tien_coc)
        set_entry_value("daThanhToan", da_thanh_toan)
        set_entry_value("tongTien", total_amount)
        set_entry_value("conNo", con_no)

        current_method = widgets["hinhThucThanhToan"].get().strip()
        default_paid_method = "Tiền mặt"
        if data and str(data.get("hinhThucThanhToan", "")).strip() and str(data.get("hinhThucThanhToan", "")).strip() != "Chưa thanh toán":
            default_paid_method = str(data.get("hinhThucThanhToan")).strip()
        if da_thanh_toan <= 0:
            widgets["hinhThucThanhToan"].set("Chưa thanh toán")
        elif current_method == "Chưa thanh toán":
            widgets["hinhThucThanhToan"].set(default_paid_method)

        if widgets["trangThai"].get().strip() not in set(BOOKING_STATUSES[3:]):
            widgets["trangThai"].set(build_payment_status(total_amount, da_thanh_toan))

        if not tour:
            calc_summary_var.set("Chọn tour hợp lệ để hệ thống tính lại tổng tiền.")
            calc_summary_lbl.config(fg=THEME["warning"])
        else:
            calc_summary_var.set(
                f"Giá gốc: {format_currency(gross_total)} | "
                f"Giảm độ tuổi: {format_currency(age_discount)} | "
                f"Voucher giữ nguyên: {format_currency(voucher_discount)} | "
                f"Cần thu: {format_currency(total_amount)}"
            )
            calc_summary_lbl.config(fg=THEME["success"])

        return {
            "people": people,
            "age_breakdown": age_breakdown,
            "tour": tour,
            "price_per_person": price_per_person,
            "tong_tien_goc": gross_total,
            "giam_gia_doi_tuong": age_discount,
            "giam_gia_voucher": voucher_discount,
            "tong_tien": total_amount,
            "tien_coc": tien_coc,
            "da_thanh_toan": da_thanh_toan,
            "con_no": con_no,
        }

    refresh_booking_quote()
    for key in ["maTour", "trangThai"]:
        widgets[key].bind("<<ComboboxSelected>>", lambda _event: refresh_booking_quote())
    for key in ["soNguoi", "treEm", "trungNien", "nguoiCaoTuoi", "tienCoc", "daThanhToan"]:
        widgets[key].bind("<KeyRelease>", lambda _event: refresh_booking_quote())
        widgets[key].bind("<FocusOut>", lambda _event: refresh_booking_quote())

    def save_booking():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save_booking` (save booking).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        form_data = {}
        before_booking = copy.deepcopy(data) if data else None
        for _, key, kind, *extra in fields:
            if data and key == "maBooking":
                form_data[key] = data["maBooking"]
            elif not data and key == "maBooking":
                form_data[key] = _next_booking_code_ui(app)
            elif key == "maTour":
                form_data[key] = _extract_tour_code(widgets[key].get())
            else:
                form_data[key] = widgets[key].get().strip()

        if not form_data.get("trangThai"):
            form_data["trangThai"] = "Mới tạo"

        if safe_int(form_data.get("soNguoi", 0)) <= 0:
            messagebox.showwarning("Thông báo", "Số người đi phải là số nguyên dương.", parent=top)
            return

        snapshot = refresh_booking_quote()
        if snapshot is None:
            messagebox.showwarning("Thông báo", "Cơ cấu độ tuổi không hợp lệ so với số người đi.", parent=top)
            return

        people = snapshot["people"]
        age_breakdown = snapshot["age_breakdown"]
        giam_gia_voucher = snapshot["giam_gia_voucher"]

        form_data.pop("treEm", None)
        form_data.pop("trungNien", None)
        form_data.pop("nguoiCaoTuoi", None)
        form_data["soNguoi"] = str(people)
        form_data["tongTienGoc"] = snapshot["tong_tien_goc"]
        form_data["giamGiaDoiTuong"] = snapshot["giam_gia_doi_tuong"]
        form_data["coCauDoTuoi"] = age_breakdown
        form_data["tongTien"] = snapshot["tong_tien"]
        form_data["daThanhToan"] = snapshot["da_thanh_toan"]
        form_data["tienCoc"] = snapshot["tien_coc"]
        form_data["conNo"] = snapshot["con_no"]

        form_data["ngayDat"] = data.get("ngayDat", datetime.now().strftime("%d/%m/%Y")) if data else datetime.now().strftime("%d/%m/%Y")
        form_data["danhSachKhach"] = data.get("danhSachKhach", []) if data else []
        form_data["maVoucher"] = data.get("maVoucher", "") if data else ""
        form_data["tenVoucher"] = data.get("tenVoucher", "") if data else ""
        form_data["giamGiaVoucher"] = giam_gia_voucher
        form_data["trangThaiHoanTien"] = data.get("trangThaiHoanTien", "") if data else ""
        form_data["soTienHoan"] = data.get("soTienHoan", 0) if data else 0
        form_data["ngayYeuCauHoanTien"] = data.get("ngayYeuCauHoanTien", "") if data else ""
        form_data["ngayXuLyHoanTien"] = data.get("ngayXuLyHoanTien", "") if data else ""
        form_data["nguoiXuLyHoanTien"] = data.get("nguoiXuLyHoanTien", "") if data else ""
        form_data["ghiChuHoanTien"] = data.get("ghiChuHoanTien", "") if data else ""
        if form_data["trangThai"] not in set(BOOKING_STATUSES[3:]):
            form_data["trangThai"] = build_payment_status(form_data["tongTien"], form_data["daThanhToan"])
        if form_data["daThanhToan"] <= 0:
            form_data["hinhThucThanhToan"] = "Chưa thanh toán"
        elif form_data["hinhThucThanhToan"] == "Chưa thanh toán":
            form_data["hinhThucThanhToan"] = "Tiền mặt"

        ok, msg = validate_booking(app, form_data, data["maBooking"] if data else None)
        if not ok:
            messagebox.showwarning("Thông báo", msg, parent=top)
            return

        if data:
            for i, b in enumerate(app["ql"].list_bookings):
                if b["maBooking"] == data["maBooking"]:
                    app["ql"].list_bookings[i] = form_data
                    break
        else:
            app["ql"].list_bookings.append(form_data)

        app["ql"].save()
        if data:
            changed_fields = collect_changed_fields(before_booking, form_data)
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="booking",
                operation="update",
                target=form_data["maBooking"],
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="booking",
                operation="create",
                target=form_data["maBooking"],
                detail=f"Tạo booking cho tour {build_tour_display_label(app['ql'], form_data.get('maTour', ''))} | Khách: {form_data.get('tenKhach', '')}",
            )
        top.destroy()

        refresh_bookings(app, app["search_booking_var"].get())
        if app.get("tv_tour"):
            refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=True)

        set_status(app, "Đã lưu booking thành công", THEME["success"])

    btns = tk.Frame(card, bg=THEME["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))

    style_button(btns, "Lưu booking", THEME["success"], save_booking).pack(
        side="left", fill="x", expand=True, padx=(0, 8)
    )
    style_button(btns, "Hủy bỏ", THEME["danger"], top.destroy).pack(
        side="left", fill="x", expand=True
    )


# Mở form sửa booking đang chọn.
def edit_booking(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_booking` (edit booking).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_booking"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn booking cần sửa.")
        return

    ma = app["tv_booking"].item(sel[0])["values"][0]
    booking = next((b for b in app["ql"].list_bookings if b["maBooking"] == ma), None)
    if booking:
        open_booking_form(app, booking)


# Hủy booking theo nghiệp vụ, không xóa cứng dữ liệu khỏi JSON.
def delete_booking(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_booking` (delete booking).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_booking"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn booking cần hủy.")
        return

    ma = app["tv_booking"].item(sel[0])["values"][0]
    booking = next((b for b in app["ql"].list_bookings if b["maBooking"] == ma), None)
    if not booking:
        messagebox.showwarning("Thông báo", "Không tìm thấy booking cần xử lý.")
        return

    current_status = str(booking.get("trangThai", "")).strip()
    if current_status in {"Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}:
        messagebox.showwarning("Thông báo", f"Booking {ma} đang ở trạng thái '{current_status}', không thể hủy lại.")
        return

    if not messagebox.askyesno("Xác nhận hủy", f"Bạn có chắc muốn hủy booking {ma} không?"):
        return

    can_hard_delete, reason = service_can_hard_delete_booking(app["ql"], booking)
    cancel_note = f"[ADMIN-CANCEL] {reason or 'Hủy theo yêu cầu quản trị'}"
    result = service_cancel_booking(
        app["ql"],
        ma,
        actor=get_admin_actor(app),
        role="admin",
        note=cancel_note,
    )
    if not result.success:
        messagebox.showwarning("Không thể hủy booking", result.message)
        return

    refresh_bookings(app, app["search_booking_var"].get())
    if app.get("tv_tour"):
        refresh_tours(app, app["search_tour_var"].get(), sync_status=True, show_status_popup=True)
    set_status(app, f"Đã hủy booking {ma} với trạng thái '{result.booking.get('trangThai', '')}'.", THEME["warning"])


# Render tab quản lý booking, hoàn tiền và báo cáo liên quan.
def admin_booking_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_booking_tab` (admin booking tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    # tk.Label(
    #     app["container"],
    #     text="QUẢN LÝ ĐẶT CHỖ & KHÁCH HÀNG",
    #     font=("Times New Roman", 20, "bold"),
    #     bg=THEME["bg"],
    #     fg=THEME["text"]
    # ).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))

    style_button(toolbar, "Thêm booking", "#16a34a", lambda: open_booking_form(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Cập nhật", "#2563eb", lambda: edit_booking(app)).pack(side="left", padx=(0, 8))
    style_button(
        toolbar,
        "Xem chi tiết",
        "#f59e0b",
        lambda: open_booking_detail(
            app,
            app["tv_booking"].item(app["tv_booking"].selection()[0])["values"][0]
        ) if app["tv_booking"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn một dòng để xem chi tiết")
    ).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Duyệt hoàn", "#16a34a", lambda: handle_refund_decision(app, True)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Từ chối hoàn", "#dc2626", lambda: handle_refund_decision(app, False)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Hủy booking", "#991b1b", lambda: delete_booking(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, ))

    search_row = tk.Frame(app["container"], bg=THEME["bg"])
    search_row.pack(fill="x", pady=(0, 10))
    tk.Label(search_row, text="Tìm kiếm:", bg=THEME["bg"], font=("Times New Roman", 12, "bold")).pack(side="left")
    search_entry = tk.Entry(search_row, textvariable=app["search_booking_var"], font=("Times New Roman", 12), relief="solid", bd=1)
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)
    search_entry.bind("<Return>", lambda e: refresh_bookings(app, app["search_booking_var"].get()))
    style_button(search_row, "Lọc", THEME["primary"], lambda: refresh_bookings(app, app["search_booking_var"].get())).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="x", expand=False, pady=(0, 6))

    cols = ("ma", "matour", "ten", "sdt", "songuoi", "tongtien", "tt", "ngaydat")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=11)
    app["tv_booking"] = tv

    cfg = [
        ("ma", "Mã Booking", 100),
        ("matour", "Mã tour", 120),
        ("ten", "Tên khách hàng", 190),
        ("sdt", "Số điện thoại", 120),
        ("songuoi", "Số người", 90),
        ("tongtien", "Tổng tiền", 120),
        ("tt", "Trạng thái", 130),
        ("ngaydat", "Ngày đặt", 120),
    ]
    for c, t, w in cfg:
        tv.heading(c, text=t)
        tv.column(c, anchor=("w" if c in {"ten"} else "center"), width=w, minwidth=max(80, w - 25), stretch=(c == "ten"))

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
    bind_autohide_scrollbar(tv, sy, "vertical")
    bind_autohide_scrollbar(tv, sx, "horizontal")
    tv.pack(side="left", fill="both", expand=True)

    def on_double_click(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click` (on double click).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sel = tv.selection()
        if not sel:
            return
        ma = tv.item(sel[0])["values"][0]
        open_booking_detail(app, ma)

    tv.bind("<Double-1>", on_double_click)

   

    refresh_bookings(app, app["search_booking_var"].get())

# =========================
# FEEDBACK / NOTIFICATION
# =========================


# Mở popup xem nhanh chi tiết một phản hồi / thông báo.
def open_feedback_detail(app, mode, data):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_feedback_detail` (open feedback detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        mode: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }
    section_bg = PASTEL_DETAIL["section_bg_3"] if mode == "review" else PASTEL_DETAIL["section_bg_2"]

    top = tk.Toplevel(app["root"])
    top.title("Chi tiết")
    top.geometry("760x480")
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    card = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        bd=1,
        relief="solid",
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    title = "CHI TIẾT ĐÁNH GIÁ" if mode == "review" else "CHI TIẾT THÔNG BÁO"

    tk.Label(
        card,
        text=title,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 22, "bold")
    ).pack(pady=(14, 10))

    tk.Label(
        card,
        text="Đánh giá từ khách hàng" if mode == "review" else "Thông báo hướng dẫn viên",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack(pady=(0, 12))

    body = tk.Frame(
        card,
        bg=section_bg,
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    body.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    tk.Label(
        body,
        text="Thông tin chi tiết",
        bg=section_bg,
        fg=PASTEL_DETAIL["text"],
        font=("Times New Roman", 15, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    body_inner = tk.Frame(body, bg=section_bg)
    body_inner.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    if mode == "review":
        rows = [
            ("Khách hàng", f"{data.get('fullname', '')} ({data.get('username', '')})"),
            ("Đối tượng", format_review_target(app["ql"], data)),
            ("Điểm", data.get("rating", "")),
            ("Ngày gửi", data.get("date", "")),
            ("Nội dung", data.get("content", "")),
        ]
    else:
        rows = [
            ("Mã HDV", data.get("maHDV", "")),
            ("Tên HDV", data.get("tenHDV", "")),
            ("Tour", f"{data.get('maTour', '')} - {data.get('tenTour', '')}"),
            ("Ngày gửi", data.get("date", "")),
            ("Nội dung", data.get("content", "")),
        ]

    for label_text, value in rows:
        row = tk.Frame(body_inner, bg=section_bg, bd=0)
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=16,
            anchor="nw",
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            row,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=480,
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True, padx=(12, 12), pady=10)

    style_button(
        card,
        "Đóng",
        THEME["danger"],
        top.destroy,
        fg="white"
    ).pack(padx=20, pady=(8, 16), fill="x")

# Mở phiên bản chi tiết đầy đủ hơn cho phản hồi / thông báo.
def open_feedback_detail_full(app, mode, data):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_feedback_detail_full` (open feedback detail full).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        mode: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }
    section_bg = PASTEL_DETAIL["section_bg_3"] if mode == "review" else PASTEL_DETAIL["section_bg_2"]

    top = tk.Toplevel(app["root"])
    top.title("Chi tiết")
    top.geometry("860x620")
    top.minsize(840, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_shell, bg=PASTEL_DETAIL["bg"], highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    bind_autohide_scrollbar(canvas, v_scroll, "vertical")
    canvas.pack(side="left", fill="both", expand=True)

    card = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=card, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    card.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    title = "CHI TIẾT ĐÁNH GIÁ" if mode == "review" else "CHI TIẾT THÔNG BÁO"
    subtitle = "Đánh giá khách hàng" if mode == "review" else "Thông báo hướng dẫn viên"

    tk.Label(
        card,
        text=title,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 22, "bold")
    ).pack(pady=(16, 8))

    tk.Label(
        card,
        text=subtitle,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack(pady=(0, 12))

    body = tk.Frame(
        card,
        bg=section_bg,
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    body.pack(fill="both", expand=True, padx=20, pady=(0, 14))

    tk.Label(
        body,
        text="Thông tin chi tiết",
        bg=section_bg,
        fg=PASTEL_DETAIL["text"],
        font=("Times New Roman", 15, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    body_inner = tk.Frame(body, bg=section_bg)
    body_inner.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    if mode == "review":
        rows = [
            ("Khách hàng", f"{data.get('fullname', '')} ({data.get('username', '')})"),
            ("Username", data.get("username", "") or "Không có"),
            ("Mã Booking", data.get("maBooking", "") or "Không có"),
            ("Điểm đánh giá", data.get("rating", "") or "Không có"),
            ("Ngày gửi", data.get("date", "") or "Không có"),
            ("Nội dung", data.get("content", "") or "Không có"),
        ]
    else:
        rows = [
            ("Mã HDV", data.get("maHDV", "") or "Không có"),
            ("Tên HDV", data.get("tenHDV", "") or "Không có"),
            ("Mã tour", data.get("maTour", "") or "Không có"),
            ("Tên tour", data.get("tenTour", "") or "Không có"),
            ("Tour", f"{data.get('maTour', '')} - {data.get('tenTour', '')}".strip(" -") or "Không có"),
            ("Ngày gửi", data.get("date", "") or "Không có"),
            ("Nội dung", data.get("content", "") or "Không có"),
        ]

    for label_text, value in rows:
        row = tk.Frame(body_inner, bg=section_bg)
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=18,
            anchor="nw",
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            row,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=640,
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True, padx=(12, 12), pady=10)

    tk.Frame(card, bg=PASTEL_DETAIL["surface"], height=90).pack(fill="x")

    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    footer_inner.pack(fill="x", padx=16, pady=10)

    style_button(footer_inner, "Đóng", THEME["danger"], top.destroy).pack(fill="x")


def admin_reviews_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_reviews_tab` (admin reviews tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    """
    clear_container(app)

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))

    rev_tv = None

    def selected_review():
        if rev_tv is None:
            return None
        sel = rev_tv.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn một đánh giá.")
            return None
        ma_review = str(rev_tv.item(sel[0], "tags")[0] if rev_tv.item(sel[0], "tags") else rev_tv.set(sel[0], "ma")).strip()
        review = find_review_by_id(app["ql"], ma_review)
        if not review:
            messagebox.showerror("Lỗi", "Không tìm thấy đánh giá đã chọn.")
            return None
        return review

    def refresh_reviews(message="Đã tải lại dữ liệu đánh giá"):
        app["ql"].load()
        admin_reviews_tab(app)
        set_status(app, message, THEME["success"])

    def open_selected_review_detail():
        review = selected_review()
        if not review:
            return
        show_detail_popup(app["root"], "Chi tiết đánh giá", build_admin_review_popup_data(app, review))

    def save_review_changes(review, message):
        ma_hdv = str(review.get("maHDV", "") or review.get("target_id", "")).strip()
        if str(review.get("target", "")).strip().lower() in {"hdv", "guide"} and ma_hdv:
            recalculate_hdv_review_stats(app["ql"], ma_hdv)
        save_reviews(app["ql"])
        refresh_reviews(message)

    def open_reply_popup():
        review = selected_review()
        if not review:
            return

        top = tk.Toplevel(app["root"])
        top.title("Phản hồi đánh giá")
        top.geometry("680x430")
        top.minsize(620, 380)
        top.configure(bg=THEME["bg"])
        top.transient(app["root"])
        top.grab_set()

        card = tk.Frame(top, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1, padx=16, pady=14)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        tk.Label(card, text=f"Phản hồi đánh giá {review.get('maReview', '')}", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 16, "bold")).pack(anchor="w")
        tk.Label(card, text=shorten_text(str(review.get("content", "")), 110), bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "italic"), wraplength=610, justify="left").pack(anchor="w", pady=(4, 10))

        txt = tk.Text(card, height=9, wrap="word", font=("Times New Roman", 12), relief="solid", bd=1)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", str(review.get("adminReply", "")).strip())

        btns = tk.Frame(card, bg=THEME["surface"])
        btns.pack(fill="x", pady=(12, 0))

        def save_reply():
            content = txt.get("1.0", "end").strip()
            if not content:
                return messagebox.showwarning("Lỗi", "Không được lưu phản hồi rỗng.", parent=top)
            actor = get_admin_actor(app)
            review["adminReply"] = content
            review["adminReplyDate"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            review["adminReplyBy"] = actor
            create_review_notification(
                app["ql"],
                review.get("username", ""),
                f"Admin đã phản hồi đánh giá {review.get('maReview', '')}: {shorten_text(content, 120)}",
                ma_review=review.get("maReview", ""),
                ma_tour=review.get("maTour", ""),
                ten_tour=review.get("tenTour", ""),
                ma_booking=review.get("maBooking", ""),
            )
            save_reviews(app["ql"])
            top.destroy()
            refresh_reviews("Đã lưu phản hồi đánh giá")

        style_button(btns, "Lưu phản hồi", THEME["success"], save_reply).pack(side="left")
        style_button(btns, "Đóng", THEME["danger"], top.destroy).pack(side="left", padx=(8, 0))

    def set_review_visibility(hidden):
        review = selected_review()
        if not review:
            return
        review["trangThai"] = "Đã ẩn" if hidden else "Hiển thị"
        review["hidden"] = bool(hidden)
        save_review_changes(review, "Đã cập nhật trạng thái đánh giá")

    def delete_selected_review():
        review = selected_review()
        if not review:
            return
        ma_review = str(review.get("maReview", "")).strip()
        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa đánh giá {ma_review}?"):
            return
        ma_hdv = str(review.get("maHDV", "") or review.get("target_id", "")).strip()
        app["ql"].reviews = [r for r in app["ql"].list_reviews if str(r.get("maReview", "")).strip() != ma_review]
        if str(review.get("target", "")).strip().lower() in {"hdv", "guide"} and ma_hdv:
            recalculate_hdv_review_stats(app["ql"], ma_hdv)
        save_reviews(app["ql"])
        refresh_reviews("Đã xóa đánh giá")

    style_button(toolbar, "Làm mới", "#0ea5e9", lambda: refresh_reviews()).pack(side="left")
    style_button(toolbar, "Xem chi tiết", THEME["warning"], open_selected_review_detail).pack(side="left", padx=(8, 0))
    style_button(toolbar, "Phản hồi", THEME["success"], open_reply_popup).pack(side="left", padx=(8, 0))
    style_button(toolbar, "Ẩn đánh giá", "#7c3aed", lambda: set_review_visibility(True)).pack(side="left", padx=(8, 0))
    style_button(toolbar, "Hiện lại", "#059669", lambda: set_review_visibility(False)).pack(side="left", padx=(8, 0))
    style_button(toolbar, "Xóa", THEME["danger"], delete_selected_review).pack(side="left", padx=(8, 0))

    rev_wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    rev_wrapper.pack(fill="both", expand=True, pady=(0, 6))

    columns = ("ma", "ma_hdv", "ten_hdv", "ma_tour", "ten_tour", "ngay", "diem", "phanhoi", "trangthai")
    rev_tv = ttk.Treeview(rev_wrapper, columns=columns, show="headings", height=15)
    headings = {
        "ma": "Mã đánh giá",
        "ma_hdv": "Mã HDV",
        "ten_hdv": "Tên HDV",
        "ma_tour": "Mã tour",
        "ten_tour": "Tên tour",
        "ngay": "Ngày gửi",
        "diem": "Điểm",
        "phanhoi": "Phản hồi Admin",
        "trangthai": "Trạng thái",
    }
    widths = {
        "ma": 110,
        "ma_hdv": 90,
        "ten_hdv": 170,
        "ma_tour": 90,
        "ten_tour": 210,
        "ngay": 130,
        "diem": 70,
        "phanhoi": 260,
        "trangthai": 100,
    }
    for col in columns:
        rev_tv.heading(col, text=headings[col])
        rev_tv.column(col, width=widths[col], minwidth=70, anchor="center" if col not in {"ten_hdv", "ten_tour", "phanhoi"} else "w", stretch=col in {"ten_hdv", "ten_tour", "phanhoi"})

    rev_sy = ttk.Scrollbar(rev_wrapper, orient="vertical", command=rev_tv.yview)
    rev_sx = ttk.Scrollbar(rev_wrapper, orient="horizontal", command=rev_tv.xview)
    bind_autohide_scrollbar(rev_tv, rev_sy, "vertical")
    bind_autohide_scrollbar(rev_tv, rev_sx, "horizontal")
    rev_tv.configure(yscrollcommand=rev_sy.set, xscrollcommand=rev_sx.set)
    rev_tv.pack(side="left", fill="both", expand=True)
    rev_sy.pack(side="right", fill="y")
    rev_sx.pack(side="bottom", fill="x")

    for idx, r in enumerate(app["ql"].list_reviews, start=1):
        if not str(r.get("maReview", "")).strip():
            r["maReview"] = f"REV{idx:02d}"
        normalized = normalize_review_for_display(r, app["ql"])
        ma_review = normalized.get("maReview", "")
        reply = normalized.get("adminReply", "")
        status = normalized.get("trangThai", "") or ("Đã ẩn" if normalized.get("hidden") else "Hiển thị")
        rev_tv.insert("", "end", iid=ma_review, values=(
            shorten_text(ma_review, 20),
            shorten_text(normalized.get("maHDV", ""), 18),
            shorten_text(normalized.get("tenHDV", ""), 24),
            shorten_text(normalized.get("maTour", ""), 18),
            shorten_text(normalized.get("tenTour", ""), 28),
            shorten_text(normalized.get("date", ""), 16),
            shorten_text(normalized.get("rating", ""), 8),
            shorten_text(reply, 42) if reply else "Chưa phản hồi",
            shorten_text(status, 16),
        ), tags=(ma_review,))

    rev_tv.bind("<Double-1>", lambda _event: open_selected_review_detail())
    apply_zebra(rev_tv)

    review_count = len(app["ql"].list_reviews)
    status_text = f"Đang ở Đánh giá khách hàng - Hiển thị {review_count} đánh giá"
    update_admin_status_card(app, "review", status_text, THEME["primary"])


def admin_notifications_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_notifications_tab` (admin notifications tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    """
    clear_container(app)


    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left")
    
    notif_rows = []
    notif_tv = None
    
    def open_selected_notif_detail():
        if notif_tv is None:
            return
        sel = notif_tv.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn một dòng để xem chi tiết")
            return
        idx = notif_tv.index(sel[0])
        if 0 <= idx < len(notif_rows):
            show_detailed_notification_popup(app["root"], notif_rows[idx], app["ql"])
    
    style_button(
        toolbar,
        "Chi tiết",
        THEME["warning"],
        lambda: open_selected_notif_detail(),
    ).pack(side="left", padx=(8, 0))

    notif_wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    notif_wrapper.pack(fill="x", expand=False, pady=(0, 6))

    notif_tv = ttk.Treeview(notif_wrapper, columns=("ma", "ten", "matour", "tentour", "date"), show="headings", height=11)
    notif_tv.heading("ma", text="Mã HDV")
    notif_tv.heading("ten", text="Tên HDV")
    notif_tv.heading("matour", text="Mã tour")
    notif_tv.heading("tentour", text="Tên tour")
    notif_tv.heading("date", text="Ngày gửi")

    notif_tv.column("ma", width=90, minwidth=80, anchor="center", stretch=False)
    notif_tv.column("ten", width=190, minwidth=130, anchor="w", stretch=True)
    notif_tv.column("matour", width=100, minwidth=80, anchor="center", stretch=False)
    notif_tv.column("tentour", width=260, minwidth=160, anchor="w", stretch=True)
    notif_tv.column("date", width=160, minwidth=130, anchor="center", stretch=False)

    notif_sy = ttk.Scrollbar(notif_wrapper, orient="vertical", command=notif_tv.yview)
    notif_sx = ttk.Scrollbar(notif_wrapper, orient="horizontal", command=notif_tv.xview)
    bind_autohide_scrollbar(notif_tv, notif_sy, "vertical")
    bind_autohide_scrollbar(notif_tv, notif_sx, "horizontal")
    notif_tv.configure(yscrollcommand=notif_sy.set, xscrollcommand=notif_sx.set)
    notif_tv.pack(side="left", fill="both", expand=True)
    notif_sy.pack(side="right", fill="y")
    notif_sx.pack(side="bottom", fill="x")

    notif_rows.clear()
    for n in app["ql"].list_notifications:
        notif_popup = build_admin_notification_popup_data(app, n)
        notif_rows.append(notif_popup)
        notif_tv.insert("", "end", values=(
            shorten_text(notif_popup.get("Mã HDV", ""), 18),
            shorten_text(notif_popup.get("Tên HDV", ""), 24),
            shorten_text(notif_popup.get("Mã tour", ""), 18),
            shorten_text(notif_popup.get("Tên tour", ""), 28),
            shorten_text(notif_popup.get("Ngày gửi", ""), 16),
        ))

    def on_double_click_notif(_event):
        open_selected_notif_detail()

    notif_tv.bind("<Double-1>", on_double_click_notif)
    apply_zebra(notif_tv)

    # Cập nhật status card với số lượng thông báo thực tế
    notif_count = len(notif_rows)
    status_text = f"Đang ở Thông báo HDV - Hiển thị {notif_count} thông báo"
    update_admin_status_card(app, "notification", status_text, THEME["primary"])


def admin_feedback_tab(app):
    """Backward compatibility: chuyển về tab đánh giá."""
    admin_reviews_tab(app)
# =========================
# Voucher 
# =========================

# Kiểm tra tính hợp lệ của dữ liệu voucher trước khi lưu.
def validate_voucher(app, data, old_code=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_voucher` (validate voucher).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = copy.deepcopy(data)
    normalized["maVoucher"] = normalize_code(normalized.get("maVoucher", ""))
    normalized["tenVoucher"] = normalize_spaces(normalized.get("tenVoucher", ""))
    normalized["trangThai"] = normalize_spaces(normalized.get("trangThai", ""))
    normalized["moTa"] = normalize_spaces(normalized.get("moTa", ""))
    normalized["tourApDung"] = normalize_tour_scope(normalized.get("tourApDung", ""))
    return validate_voucher_payload(app["ql"], normalized, old_code=normalize_code(old_code or ""))


# Mở form thêm mới / chỉnh sửa voucher và kiểm tra dữ liệu trước khi lưu.
def open_voucher_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_voucher_form` (open voucher form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin mã giảm giá")
    top.geometry("720x620")
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()

    card = tk.Frame(
        top,
        bg=THEME["surface"],
        bd=0,
        highlightbackground="#d8e2f0",
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(
        card,
        text="THÔNG TIN MÃ GIẢM GIÁ",
        bg=THEME["surface"],
        fg=THEME["text"],
        font=("Times New Roman", 18, "bold")
    ).pack(pady=(14, 10))

    form_wrap, form = create_scrollable_form(card, THEME["surface"])
    form_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    tour_options = ["Tất cả tour"]
    for tour in app["ql"].list_tours:
        ma_tour = str(tour.get("ma", "")).strip()
        ten_tour = str(tour.get("ten", "")).strip()
        if not ma_tour:
            continue
        if normalize_tour_status(tour.get("trangThai", "")) == TOUR_STATUS_OPEN:
            tour_options.append(f"{ma_tour} - {ten_tour}" if ten_tour else ma_tour)

    fields = [
        ("Mã voucher", "maVoucher", "entry"),
        ("Tên voucher", "tenVoucher", "entry"),
        ("Loại giảm", "loaiGiam", "combo", ["Phần trăm", "Tiền mặt"]),
        ("Giảm giá", "giamGiaVoucher", "entry"),
        ("Đơn tối thiểu", "donToiThieu", "entry"),
        ("Số lượng", "soLuong", "entry"),
        ("Đã sử dụng", "daSuDung", "entry"),
        ("Giới hạn / user", "gioiHanMoiUser", "entry"),
        ("Tour áp dụng", "tourApDung", "combo_editable", tour_options),
        ("Ngày bắt đầu", "ngayBatDau", "entry"),
        ("Ngày kết thúc", "ngayKetThuc", "entry"),
        ("Trạng thái", "trangThai", "combo", ["Đang áp dụng", "Ngừng áp dụng", "Hết lượt"]),
        ("Mô tả", "moTa", "text"),
    ]

    widgets = {}

    for label, key, kind, *extra in fields:
        row = tk.Frame(form, bg=THEME["surface"])
        row.pack(fill="x", pady=7)

        tk.Label(
            row,
            text=label,
            width=16,
            anchor="w",
            bg=THEME["surface"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")

        if kind == "entry":
            w = tk.Entry(row, font=("Times New Roman", 12))
            w.pack(side="left", fill="x", expand=True, ipady=4)
            style_form_entry_widget(w)
        elif kind == "combo":
            w = ttk.Combobox(
                row,
                values=extra[0],
                state="readonly",
                font=("Times New Roman", 11),
                style=FORM_COMBOBOX_STYLE,
            )
            w.pack(side="left", fill="x", expand=True, ipady=4)
        elif kind == "combo_editable":
            w = ttk.Combobox(
                row,
                values=extra[0],
                state="normal",
                font=("Times New Roman", 11),
                style=FORM_COMBOBOX_STYLE,
            )
            w.pack(side="left", fill="x", expand=True, ipady=4)
        else:
            w = tk.Text(row, height=4, font=("Times New Roman", 12))
            w.pack(side="left", fill="both", expand=True)
            style_form_text_widget(w)

        widgets[key] = w

        if data:
            value = data.get(key, "")
            if kind == "text":
                w.insert("1.0", value)
            elif kind == "combo_editable":
                normalized_scope = normalize_tour_scope(value)
                w.set(normalized_scope if normalized_scope else "Tất cả tour")
            else:
                w.insert(0, value) if kind == "entry" else w.set(value)

    if data:
        widgets["maVoucher"].config(state="disabled")

    hint_var = tk.StringVar(
        value="Ví dụ: 10% hoặc 50000 | Giới hạn / user: 0 = không giới hạn | Tour áp dụng: chọn từ danh sách hoặc nhập T01, T02"
    )
    tk.Label(
        card,
        textvariable=hint_var,
        bg=THEME["surface"],
        fg=THEME["muted"],
        font=("Times New Roman", 10, "italic")
    ).pack(anchor="w", padx=20, pady=(0, 8))

    def on_discount_type_change(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_discount_type_change` (on discount type change).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        loai = widgets["loaiGiam"].get().strip()
        if loai == "Phần trăm":
            hint_var.set("Nhập giảm giá dạng phần trăm, ví dụ: 10%")
        else:
            hint_var.set("Nhập giảm giá dạng tiền mặt, ví dụ: 50000")

    if isinstance(widgets["loaiGiam"], ttk.Combobox):
        widgets["loaiGiam"].bind("<<ComboboxSelected>>", on_discount_type_change)

    def save_voucher():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save_voucher` (save voucher).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        new_data = {}
        before_voucher = copy.deepcopy(data) if data else None
        for _, key, kind, *extra in fields:
            if kind == "text":
                new_data[key] = widgets[key].get("1.0", "end").strip()
            elif data and key == "maVoucher":
                new_data[key] = data["maVoucher"]
            else:
                value = widgets[key].get().strip()
                if key == "tourApDung":
                    if value.lower() == "tất cả tour":
                        value = ""
                    elif " - " in value and "," not in value:
                        value = value.split(" - ", 1)[0].strip()
                new_data[key] = value

        new_data["maVoucher"] = normalize_code(new_data.get("maVoucher", ""))
        new_data["tenVoucher"] = normalize_spaces(new_data.get("tenVoucher", ""))
        new_data["trangThai"] = normalize_spaces(new_data.get("trangThai", ""))
        new_data["moTa"] = normalize_spaces(new_data.get("moTa", ""))
        new_data["tourApDung"] = normalize_tour_scope(new_data.get("tourApDung", ""))
        if not new_data.get("gioiHanMoiUser"):
            new_data["gioiHanMoiUser"] = "0"

        ok, msg = validate_voucher(app, new_data, data["maVoucher"] if data else None)
        if not ok:
            messagebox.showwarning("Thông báo", msg, parent=top)
            return

        if data:
            for i, v in enumerate(app["ql"].list_vouchers):
                if normalize_code(v.get("maVoucher", "")) == normalize_code(data.get("maVoucher", "")):
                    app["ql"].list_vouchers[i] = new_data
                    break
        else:
            app["ql"].list_vouchers.append(new_data)

        app["ql"].save()
        if data:
            changed_fields = collect_changed_fields(before_voucher, new_data)
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="voucher",
                operation="update",
                target=new_data["maVoucher"],
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="voucher",
                operation="create",
                target=new_data["maVoucher"],
                detail=f"Tạo voucher {new_data.get('tenVoucher', '')} | Phạm vi: {new_data.get('tourApDung', 'Tất cả tour') or 'Tất cả tour'}",
            )
        refresh_vouchers(app)
        top.destroy()
        set_status(app, "Đã lưu voucher thành công", THEME["success"])

    btns = tk.Frame(card, bg=THEME["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))

    style_button(btns, "Lưu voucher", THEME["success"], save_voucher).pack(side="left", fill="x", expand=True, padx=(0, 8))
    style_button(btns, "Hủy", THEME["danger"], top.destroy).pack(side="left", fill="x", expand=True)


# Mở form sửa voucher đang chọn.
def edit_voucher(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_voucher` (edit voucher).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tv = app.get("tv_voucher")
    if not tv:
        return

    sel = tv.selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn voucher cần sửa.")
        return

    code = tv.item(sel[0])["values"][0]
    voucher = next((v for v in app["ql"].list_vouchers if v.get("maVoucher") == code), None)
    if not voucher:
        messagebox.showerror("Lỗi", "Không tìm thấy voucher.")
        return

    open_voucher_form(app, voucher)


# Xóa voucher đang chọn sau khi xác nhận.
def delete_voucher(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_voucher` (delete voucher).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tv = app.get("tv_voucher")
    if not tv:
        return

    sel = tv.selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn voucher cần xóa.")
        return

    code = tv.item(sel[0])["values"][0]

    if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa voucher {code}?"):
        return

    app["ql"].data["maVoucher"] = [
        v for v in app["ql"].list_vouchers
        if str(v.get("maVoucher", "")).upper() != str(code).upper()
    ]
    app["ql"].save()
    write_crud_log(
        datastore=app["ql"],
        actor=get_admin_actor(app),
        role="admin",
        entity="voucher",
        operation="delete",
        target=code,
        detail="Xóa voucher khỏi hệ thống",
    )
    refresh_vouchers(app)
    set_status(app, f"Đã xóa voucher {code}", THEME["danger"])

# Mở cửa sổ xem nhanh chi tiết voucher.
def open_voucher_detail(app, code):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_voucher_detail` (open voucher detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    voucher = next((v for v in app["ql"].list_vouchers if v.get("maVoucher") == code), None)
    if not voucher:
        messagebox.showerror("Lỗi", "Không tìm thấy voucher.")
        return
    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }
    status = str(voucher.get("trangThai", "")).strip()
    section_bg = PASTEL_DETAIL["section_bg"]
    if "Đang áp dụng" in status:
        section_bg = PASTEL_DETAIL["section_bg_2"]
    elif "Hết" in status:
        section_bg = PASTEL_DETAIL["section_bg_3"]

    top = tk.Toplevel(app["root"])
    top.title(f"Chi tiết voucher - {code}")
    top.geometry("620x500")
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    card = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        bd=1,
        relief="solid",
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(
        card,
        text="CHI TIẾT MÃ GIẢM GIÁ",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 22, "bold")
    ).pack(pady=(14, 12))

    tk.Label(
        card,
        text=voucher.get("maVoucher", ""),
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack(pady=(0, 12))

    body = tk.Frame(
        card,
        bg=section_bg,
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    body.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    tk.Label(
        body,
        text="Thông tin voucher",
        bg=section_bg,
        fg=PASTEL_DETAIL["text"],
        font=("Times New Roman", 15, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    body_inner = tk.Frame(body, bg=section_bg)
    body_inner.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    rows = [
        ("Mã voucher", voucher.get("maVoucher", "")),
        ("Tên voucher", voucher.get("tenVoucher", "")),
        ("Loại giảm", voucher.get("loaiGiam", "")),
        ("Giảm giá", voucher.get("giamGiaVoucher", "")),
        ("Đơn tối thiểu", f"{safe_int(voucher.get('donToiThieu', 0)):,}đ".replace(",", ".")),
        ("Số lượng", voucher.get("soLuong", "")),
        ("Đã sử dụng", voucher.get("daSuDung", "")),
        ("Giới hạn / user", voucher.get("gioiHanMoiUser", "0") or "0"),
        ("Phạm vi tour", build_voucher_scope_label(voucher)),
        ("Ngày bắt đầu", voucher.get("ngayBatDau", "")),
        ("Ngày kết thúc", voucher.get("ngayKetThuc", "")),
        ("Trạng thái", voucher.get("trangThai", "")),
        ("Mô tả", voucher.get("moTa", "")),
    ]

    for label_text, value in rows:
        row = tk.Frame(body_inner, bg=section_bg, bd=0)
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=16,
            anchor="w",
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            row,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=360,
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True, padx=(12, 12), pady=10)

    btns = tk.Frame(card, bg=PASTEL_DETAIL["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))

    style_button(
        btns,
        "Sửa voucher",
        THEME["primary"],
        lambda: [top.destroy(), open_voucher_form(app, voucher)]
    ).pack(side="left", fill="x", expand=True, padx=(0, 8))

    style_button(
        btns,
        "Đóng",
        THEME["danger"],
        top.destroy
    ).pack(side="left", fill="x", expand=True)


# Mở cửa sổ chi tiết đầy đủ của voucher với thông tin mở rộng hơn.
def open_voucher_detail_full(app, code):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_voucher_detail_full` (open voucher detail full).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    voucher = next((v for v in app["ql"].list_vouchers if v.get("maVoucher") == code), None)
    if not voucher:
        messagebox.showerror("Lỗi", "Không tìm thấy voucher.")
        return

    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }

    status = str(voucher.get("trangThai", "")).strip()
    section_bg = PASTEL_DETAIL["section_bg"]
    if "Đang áp dụng" in status:
        section_bg = PASTEL_DETAIL["section_bg_2"]
    elif "Hết" in status:
        section_bg = PASTEL_DETAIL["section_bg_3"]

    top = tk.Toplevel(app["root"])
    top.title(f"Chi tiết voucher - {code}")
    top.geometry("820x620")
    top.minsize(820, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_shell, bg=PASTEL_DETAIL["bg"], highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    bind_autohide_scrollbar(canvas, v_scroll, "vertical")
    canvas.pack(side="left", fill="both", expand=True)

    card = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=card, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    card.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    tk.Label(
        card,
        text="CHI TIẾT MÃ GIẢM GIÁ",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 22, "bold")
    ).pack(pady=(16, 8))

    tk.Label(
        card,
        text=voucher.get("maVoucher", ""),
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack(pady=(0, 12))

    body = tk.Frame(
        card,
        bg=section_bg,
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    body.pack(fill="both", expand=True, padx=20, pady=(0, 14))

    tk.Label(
        body,
        text="Thông tin voucher",
        bg=section_bg,
        fg=PASTEL_DETAIL["text"],
        font=("Times New Roman", 15, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    body_inner = tk.Frame(body, bg=section_bg)
    body_inner.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    loai = str(voucher.get("loaiGiam", "")).strip()
    giam = str(voucher.get("giamGiaVoucher", "")).strip()
    if loai == "Tiền mặt" and giam.isdigit():
        giam_hien = f"{int(giam):,}đ".replace(",", ".")
    else:
        giam_hien = giam

    rows = [
        ("Mã voucher", voucher.get("maVoucher", "") or "Không có"),
        ("Tên voucher", voucher.get("tenVoucher", "") or "Không có"),
        ("Loại giảm", loai or "Không có"),
        ("Giảm giá", giam_hien or "Không có"),
        ("Đơn tối thiểu", f"{safe_int(voucher.get('donToiThieu', 0)):,}đ".replace(",", ".")),
        ("Số lượng", voucher.get("soLuong", "") or "0"),
        ("Đã sử dụng", voucher.get("daSuDung", "") or "0"),
        ("Còn lại", max(0, safe_int(voucher.get("soLuong", 0)) - safe_int(voucher.get("daSuDung", 0)))),
        ("Giới hạn / user", voucher.get("gioiHanMoiUser", "0") or "0"),
        ("Phạm vi tour", build_voucher_scope_label(voucher)),
        ("Ngày bắt đầu", voucher.get("ngayBatDau", "") or "Không có"),
        ("Ngày kết thúc", voucher.get("ngayKetThuc", "") or "Không có"),
        ("Trạng thái", voucher.get("trangThai", "") or "Không có"),
        ("Mô tả", voucher.get("moTa", "") or "Không có"),
    ]

    for label_text, value in rows:
        row = tk.Frame(body_inner, bg=section_bg)
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=18,
            anchor="nw",
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            row,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=620,
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True, padx=(12, 12), pady=10)

    tk.Frame(card, bg=PASTEL_DETAIL["surface"], height=90).pack(fill="x")

    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    btns = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    btns.pack(fill="x", padx=16, pady=10)

    style_button(
        btns,
        "Sửa voucher",
        THEME["primary"],
        lambda: [top.destroy(), open_voucher_form(app, voucher)]
    ).pack(side="left", fill="x", expand=True, padx=(0, 8))

    style_button(
        btns,
        "Đóng",
        THEME["danger"],
        top.destroy
    ).pack(side="left", fill="x", expand=True)


# Nạp lại bảng voucher để phản ánh dữ liệu mới nhất trên giao diện.
def refresh_vouchers(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_vouchers` (refresh vouchers).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tv = app.get("tv_voucher")
    if not tv:
        return

    for item in tv.get_children():
        tv.delete(item)

    rows = app["ql"].list_vouchers
    if keyword:
        kw = keyword.lower().strip()
        rows = [
            v for v in rows
            if kw in str(v.get("maVoucher", "")).lower()
            or kw in str(v.get("tenVoucher", "")).lower()
            or kw in str(v.get("trangThai", "")).lower()
            or kw in str(v.get("moTa", "")).lower()
            or kw in str(v.get("tourApDung", "")).lower()
        ]

    for v in rows:
        ma = str(v.get("maVoucher", "")).strip()
        ten = str(v.get("tenVoucher", "")).strip()
        tt = str(v.get("trangThai", "")).strip()
        loai = str(v.get("loaiGiam", "")).strip()
        giam = str(v.get("giamGiaVoucher", "")).strip()

        if loai == "Tiền mặt" and giam.isdigit():
            giam_hien = f"{int(giam):,}đ".replace(",", ".")
        else:
            giam_hien = giam

        so_luong = safe_int(v.get("soLuong", 0))
        da_dung = safe_int(v.get("daSuDung", 0))
        item = tv.insert(
            "",
            "end",
            values=(
                shorten_text(ma, 200),
                shorten_text(ten, 30),
                shorten_text(loai, 14),
                shorten_text(giam_hien, 20),
                shorten_text(so_luong, 10),
                shorten_text(da_dung, 10),
                shorten_text(tt, 20),
            ),
        )

        if "Đang áp dụng" in tt:
            tv.item(item, tags=("active",))
        elif "Ngừng" in tt:
            tv.item(item, tags=("inactive",))
        elif "Hết" in tt:
            tv.item(item, tags=("expired",))

    apply_zebra(tv)
    update_admin_status_card(app, "voucher", f"Đang ở Mã giảm giá - Hiển thị {len(rows)} voucher", THEME["primary"])


# Render tab quản lý voucher của admin.
def admin_voucher_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_voucher_tab` (admin voucher tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    # tk.Label(
    #     app["container"],
    #     text="QUẢN LÝ MÃ GIẢM GIÁ",
    #     font=("Times New Roman", 20, "bold"),
    #     bg=THEME["bg"],
    #     fg=THEME["text"]
    # ).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))

    style_button(toolbar, "Thêm mã", THEME["success"], lambda: open_voucher_form(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Sửa voucher", THEME["primary"], lambda: edit_voucher(app)).pack(side="left", padx=(0, 8))
    style_button(
        toolbar,
        "Chi tiết",
        THEME["warning"],
        lambda: open_voucher_detail_full(
            app,
            app["tv_voucher"].item(app["tv_voucher"].selection()[0])["values"][0],
        ) if app["tv_voucher"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn một dòng để xem chi tiết"),
    ).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Xóa mã", THEME["danger"], lambda: delete_voucher(app)).pack(side="left", padx=(0, 20))
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 20))

    tk.Label(
        toolbar,
        text="Tìm kiếm:",
        bg=THEME["bg"],
        font=("Times New Roman", 12, "bold")
    ).pack(side="left")

    if "search_voucher_var" not in app:
        app["search_voucher_var"] = tk.StringVar()

    ent_search = tk.Entry(
        toolbar,
        textvariable=app["search_voucher_var"],
        font=("Times New Roman", 12),
        relief="solid",
        bd=1
    )
    ent_search.pack(side="left", fill="x", expand=True, ipady=4)
    ent_search.bind("<Return>", lambda e: refresh_vouchers(app, app["search_voucher_var"].get()))

    style_button(
        toolbar,
        "Lọc",
        THEME["primary"],
        lambda: refresh_vouchers(app, app["search_voucher_var"].get())
    ).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="x", expand=False, pady=(0, 6))

    cols = ("ma", "ten", "loai", "giatri", "soluong", "dadung", "tt")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=11)
    app["tv_voucher"] = tv

    headers = [
        ("ma", "Mã voucher", 130),
        ("ten", "Tên voucher", 220),
        ("loai", "Loại giảm", 110),
        ("giatri", "Giá trị giảm", 130),
        ("soluong", "Số lượng", 90),
        ("dadung", "Đã dùng", 90),
        ("tt", "Trạng thái", 130),
    ]

    for c, t, w in headers:
        tv.heading(c, text=t)
        tv.column(c, anchor=("w" if c == "ten" else "center"), width=w, minwidth=max(80, w - 25), stretch=(c == "ten"))

    def on_double_click_voucher(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click_voucher` (on double click voucher).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sel = tv.selection()
        if not sel:
            return
        code = tv.item(sel[0])["values"][0]
        open_voucher_detail_full(app, code)

    tv.bind("<Double-1>", on_double_click_voucher)

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
    bind_autohide_scrollbar(tv, sy, "vertical")
    bind_autohide_scrollbar(tv, sx, "horizontal")
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")
    sx.pack(side="bottom", fill="x")



    refresh_vouchers(app, app["search_voucher_var"].get())

# =========================
# SYSTEM
# =========================

# Đăng xuất khỏi giao diện admin và quay về màn hình đăng nhập / chọn vai trò.
def logout(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `logout` (logout).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn thoát khỏi hệ thống quản trị?"):
        for widget in app["root"].winfo_children():
            widget.destroy()
        try:
            from main import TravelSystem

            app["root"].configure(bg=THEME["bg"])
            TravelSystem(app["root"])
        except (ImportError, RuntimeError, tk.TclError) as e:
            messagebox.showerror("Lỗi", f"Không thể quay lại màn hình đăng nhập.\n{e}")


# =========================
# MAIN
# =========================
# Hàm khởi tạo giao diện admin chính.
# Tạo root/window, datastore, sidebar, container nội dung, thanh trạng thái và gắn các tab chức năng.
def main(root=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `main` (main).
    Tham số:
        root: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    enable_tk_text_autofix()
    if root is None:
        root = tk.Tk()

    root.title("VIETNAM TRAVEL - QUẢN TRỊ HỆ THỐNG")
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    target_w = min(1420, max(1180, screen_w - 80))
    target_h = min(820, max(680, screen_h - 100))
    root.geometry(f"{target_w}x{target_h}")
    root.minsize(min(1220, target_w), min(740, target_h))
    root.configure(bg=THEME["bg"])
    configure_ui_fonts(root)

    for widget in root.winfo_children():
        widget.destroy()

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        font=("Times New Roman", 12),
        rowheight=34,
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
    style.configure(
        FORM_COMBOBOX_STYLE,
        font=("Times New Roman", 12),
        foreground=THEME["text"],
        fieldbackground="#f8fafc",
        background="#f8fafc",
        bordercolor="#cbd5e1",
        lightcolor="#e2e8f0",
        darkcolor="#e2e8f0",
        arrowsize=14,
        padding=6,
    )
    style.map(
        FORM_COMBOBOX_STYLE,
        fieldbackground=[("readonly", "#f8fafc"), ("focus", "#ffffff")],
        background=[("readonly", "#f8fafc"), ("active", "#f1f5f9")],
        foreground=[("readonly", THEME["text"])],
        selectbackground=[("readonly", "#e2e8f0")],
        selectforeground=[("readonly", THEME["text"])],
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
    # Đồng bộ toàn bộ scrollbar theo kiểu tối giản, không mÅ©i tên.
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
        POPUP_FORM_SCROLLBAR_STYLE,
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
        POPUP_FORM_SCROLLBAR_STYLE,
        troughcolor="#dbe3ee",
        background="#8fa3bd",
        darkcolor="#8fa3bd",
        lightcolor="#8fa3bd",
        bordercolor="#dbe3ee",
        arrowcolor="#dbe3ee",
        relief="flat",
        arrowsize=10,
        gripcount=0,
    )
    style.map(
        POPUP_FORM_SCROLLBAR_STYLE,
        background=[("active", "#7188a6"), ("pressed", "#5f7694")],
        darkcolor=[("active", "#7188a6"), ("pressed", "#5f7694")],
        lightcolor=[("active", "#7188a6"), ("pressed", "#5f7694")],
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

    app = {
        "root": root,
        "ql": DataStore(),
        "container": None,
        "content_canvas": None,
        "tv_hdv": None,
        "tv_tour": None,
        "tv_booking": None,
        "tv_users": None,
        "status_var": tk.StringVar(value="Hệ thống đã sẵn sàng"),
        "status_label": None,
        "search_hdv_var": tk.StringVar(),
        "search_user_var": tk.StringVar(),
        "search_tour_var": tk.StringVar(),
        "search_booking_var": tk.StringVar(),
        "search_voucher_var": tk.StringVar(),
        "search_feedback_var": tk.StringVar(),
        "page_title_var": tk.StringVar(value="Tổng quan Dashboard"),
        "page_subtitle_var": tk.StringVar(value="Theo dõi nhanh hoạt động tour, nhân sự và booking của hệ thống."),
        "active_menu_btn": None,
        "current_tab": "dashboard",
        "status_badge": None,
        "login_time": datetime.now(),
        "login_time_var": tk.StringVar(),
        "sidebar_collapsed": False,
    }

    app["login_time_var"].set(
        "Đăng nhập lúc: " + app["login_time"].strftime("%d/%m/%Y - %H:%M:%S")
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
        text="☰",
        bg="#020f2a",
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
    collapse_btn.bind("<Enter>", lambda _e: collapse_btn.configure(bg="#020f2a"))
    collapse_btn.bind("<Leave>", lambda _e: collapse_btn.configure(bg="#020f2a"))
    brand_subtitle = tk.Label(
        brand,
        text="Admin Control Center",
        justify="left",
        anchor="w",
        bg=SIDEBAR_BG,
        fg="#93c5fd",
        font=("Times New Roman", 11, "italic"),
    )
    brand_subtitle.pack(fill="x", pady=(2, 0))

    admin_info = app["ql"].data.get("admin", {})
    account_card = tk.Frame(sidebar, bg=SIDEBAR_CARD_BG, highlightbackground=SIDEBAR_BORDER, highlightthickness=1)
    account_card.pack(fill="x", padx=16, pady=(8, 12))
    tk.Label(
        account_card,
        text="TÀI KHOẢN QUẢN TRỊ",
        bg=SIDEBAR_CARD_BG,
        fg="#dbeafe",
        font=("Times New Roman", 11, "bold"),
    ).pack(fill="x", pady=(12, 2))
    tk.Label(
        account_card,
        text=f"{admin_info.get('fullname', 'Quản trị viên')}",
        bg=SIDEBAR_CARD_BG,
        fg="white",
        font=("Times New Roman", 13, "bold"),
        pady=4,
    ).pack(fill="x")
    tk.Label(
        account_card,
        text=f"Username: {admin_info.get('username', 'admin')}",
        bg=SIDEBAR_CARD_BG,
        fg="#93c5fd",
        font=("Times New Roman", 10, "italic"),
    ).pack(fill="x")
    tk.Label(
        account_card,
        textvariable=app["login_time_var"],
        bg=SIDEBAR_CARD_BG,
        fg="#93c5fd",
        font=("Times New Roman", 10, "italic"),
        pady=8,
        wraplength=220,
        justify="center",
    ).pack(fill="x")

# Khung menu có thể cuộn
    menu_shell = tk.Frame(sidebar, bg=SIDEBAR_BG)
    menu_shell.pack(fill="both", expand=True, padx=12, pady=(4, 0))

    menu_canvas = tk.Canvas(
        menu_shell,
        bg=SIDEBAR_BG,
        highlightthickness=0,
        bd=0
    )
    menu_scroll = ttk.Scrollbar(
        menu_shell,
        orient="vertical",
        command=menu_canvas.yview,
    )
    bind_autohide_scrollbar(menu_canvas, menu_scroll, "vertical")
    menu_canvas.pack(side="left", fill="both", expand=True)

    menu = tk.Frame(menu_canvas, bg=SIDEBAR_BG)
    menu_window = menu_canvas.create_window((0, 0), window=menu, anchor="nw")

    def _on_menu_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_menu_configure` ( on menu configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        menu_canvas.configure(scrollregion=menu_canvas.bbox("all"))

    def _on_menu_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_menu_canvas_configure` ( on menu canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        menu_canvas.itemconfigure(menu_window, width=event.width)

    menu.bind("<Configure>", _on_menu_configure)
    menu_canvas.bind("<Configure>", _on_menu_canvas_configure)

    def _on_sidebar_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_sidebar_mousewheel` ( on sidebar mousewheel).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        try:
            menu_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    menu_canvas.bind("<Enter>", lambda _e: menu_canvas.bind_all("<MouseWheel>", _on_sidebar_mousewheel))
    menu_canvas.bind("<Leave>", lambda _e: menu_canvas.unbind_all("<MouseWheel>"))

    def set_active_menu(button):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `set_active_menu` (set active menu).
        Tham số:
            button: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        prev = app.get("active_menu_btn")
        if prev and prev.winfo_exists() and prev is not button:
            prev.configure(bg=SIDEBAR_BG, fg="#dbe4f5")
        app["active_menu_btn"] = button
        button.configure(bg=SIDEBAR_BTN_ACTIVE, fg="white")

    def set_page(title, subtitle, current_tab):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `set_page` (set page).
        Tham số:
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            subtitle: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            current_tab: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        app["page_title_var"].set(title)
        app["page_subtitle_var"].set(subtitle)
        app["current_tab"] = current_tab

    def menu_btn(text, cmd, icon=""):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `menu_btn` (menu btn).
        Tham số:
            text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            cmd: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            icon: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
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
            font=("Times New Roman", 13, "bold"),
            padx=14,
            pady=13,
            wraplength=210,
            command=cmd,
        )
        btn._full_text = text
        btn._icon = icon

        def _sync_menu_wrap(_event=None, button=btn):
            if app.get("sidebar_collapsed"):
                button.configure(wraplength=40)
                return
            button.configure(wraplength=max(150, button.winfo_width() - 36))

        btn.bind("<Configure>", _sync_menu_wrap)
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
    head_left.pack(side="left", fill="x", expand=True, padx=18, pady=12)
    tk.Label(
        head_left,
        textvariable=app["page_title_var"],
        bg=THEME["header_bg"],
        fg=THEME["text"],
        font=("Times New Roman", 24, "bold"),
        anchor="w",
    ).pack(anchor="w")
    header_subtitle_label = tk.Label(
        head_left,
        textvariable=app["page_subtitle_var"],
        bg=THEME["header_bg"],
        fg=THEME["muted"],
        font=("Times New Roman", 12, "italic"),
        anchor="w",
        justify="left",
    )
    header_subtitle_label.pack(anchor="w", pady=(3, 0), fill="x")

    def _sync_header_subtitle_wrap(_event=None):
        try:
            header_subtitle_label.configure(wraplength=max(420, head_left.winfo_width() - 20))
        except tk.TclError:
            return

    head_left.bind("<Configure>", _sync_header_subtitle_wrap)
    header_subtitle_label.after_idle(_sync_header_subtitle_wrap)

    head_right = tk.Frame(header, bg=THEME["header_bg"])
    head_right.pack(side="right", padx=18, pady=16)
    tk.Label(
        head_right,
        text="Trạng thái hệ thống",
        bg=THEME["header_bg"],
        fg=THEME["muted"],
        font=("Times New Roman", 10, "bold"),
    ).pack(anchor="e")
    header_badge = tk.Label(
        head_right,
        text="ADMIN",
        bg="#dbeafe",
        fg="#1d4ed8",
        font=("Times New Roman", 11, "bold"),
        padx=14,
        pady=7,
    )
    header_badge.pack(anchor="e", pady=(6, 8))

    status_bar = tk.Frame(
        right_panel,
        bg=THEME["status_bg"],
        height=46,
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
        padx=18,
        pady=4,
        font=("Times New Roman", 13, "italic"),
    )
    app["status_label"].pack(fill="both", expand=True)

    content_shell = tk.Frame(
        right_panel,
        bg=THEME["bg"],
    )
    content_shell.pack(fill="both", expand=True, padx=18, anchor="n")

    content_area = tk.Frame(
        content_shell,
        bg=THEME["bg"],
        padx=4,
        pady=4,
    )
    content_area.pack(fill="both", expand=True)

    app["container"] = content_area
    app["content_canvas"] = None

    def open_view(title, subtitle, current_tab, view_fn, button):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `open_view` (open view).
        Tham số:
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            subtitle: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            current_tab: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            view_fn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            button: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        set_page(title, subtitle, current_tab)
        set_active_menu(button)
        view_fn()

    def reload_current_page():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `reload_current_page` (reload current page).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        reload_admin_current_tab(app)

    style_button(head_right, "Tải lại", THEME["primary"], reload_current_page).pack(anchor="e")

    tab_definitions = get_admin_tab_definitions()
    nav_specs = [
        (
            tab_def.title,
            tab_def.subtitle,
            tab_def.key,
            (lambda key=tab_def.key: get_admin_tab_handler(key)(app)),
            tab_def.icon,
        )
        for tab_def in tab_definitions
    ]

    nav_buttons = []
    for idx, (title, subtitle, current_tab, fn, icon) in enumerate(nav_specs):
        btn = menu_btn(
            title,
            lambda t=title, s=subtitle, c=current_tab, f=fn, i=idx: open_view(t, s, c, f, nav_buttons[i]),
            icon=icon,
        )
        btn.pack(fill="x", pady=2)
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
    logout_btn = style_button(util, "🚪  Đăng xuất hệ thống", "#7f1d1d", lambda: logout(app))
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
            collapse_btn.configure(text="☰")
            util.pack_configure(padx=8, pady=10)
            menu_shell.pack_configure(padx=8)
            logout_btn.configure(text="🚪", anchor="center", padx=8)
        else:
            brand_title.configure(text="VIETNAM TRAVEL", font=("Times New Roman", 16, "bold"))
            if not brand_subtitle.winfo_manager():
                brand_subtitle.pack(fill="x", pady=(2, 0))
            if not account_card.winfo_manager():
                account_card.pack(fill="x", padx=16, pady=(8, 12), before=menu_shell)
            collapse_btn.configure(text="☰")
            util.pack_configure(padx=12, pady=14)
            menu_shell.pack_configure(padx=12)
            logout_btn.configure(text="🚪  Đăng xuất hệ thống", anchor="w", padx=14)

        for nav_btn in nav_buttons:
            _refresh_menu_button_layout(nav_btn)
        menu_canvas.itemconfigure(menu_window, width=menu_canvas.winfo_width())
        root.update_idletasks()
        if app.get("current_tab") == "dashboard":
            root.after_idle(lambda: dashboard_tab(app))

    def toggle_sidebar():
        app["sidebar_collapsed"] = not app.get("sidebar_collapsed", False)
        apply_sidebar_mode()

    collapse_btn.configure(command=toggle_sidebar)
    apply_sidebar_mode()

    first_tab = tab_definitions[0]
    open_view(
        first_tab.title,
        first_tab.subtitle,
        first_tab.key,
        lambda: get_admin_tab_handler(first_tab.key)(app),
        nav_buttons[0],
    )

    if root is not None and not isinstance(root, tk.Tk):
        return
    root.mainloop()


if __name__ == "__main__":
    main()



