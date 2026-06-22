
"""
Module popup hiển thị thời tiết và vị trí địa điểm du lịch.
Tích hợp với Open-Meteo API để lấy thông tin thời tiết thực tế.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import math
from datetime import datetime
from io import BytesIO
from urllib.request import Request, urlopen

from PIL import Image, ImageTk, ImageDraw
from GUI.common.rounded_button import RoundedButton


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from core.travel_api import (
    get_location_weather,
    build_weather_location_query,
    normalize_vietnam_location_name,
    geocode_location,
    fetch_weather_by_coordinates,
    build_google_maps_url
)


THEME = {
    "bg": "#f1f5f9",
    "surface": "#ffffff",
    "primary": "#2563eb",
    "success": "#059669",
    "danger": "#dc2626",
    "warning": "#d97706",
    "text": "#0f172a",
    "muted": "#64748b",
    "border": "#d2dae6",
    "heading_bg": "#e2e8f0",
}


def format_currency(value):
    """Định dạng số tiền."""
    try:
        return f"{int(value):,}đ".replace(",", ".")
    except (ValueError, TypeError):
        return "0đ"


def safe_get(data, key, default=""):
    """Lấy giá trị an toàn từ dict."""
    value = data.get(key, default)
    return str(value).strip() if value else default


class TourWeatherPopup:
    """
    Popup hiển thị thông tin thời tiết và vị trí cho tour du lịch.
    """

    def __init__(self, parent, tour_data, datastore=None):
        """
        Khởi tạo popup.

        Args:
            parent: Widget cha (root window)
            tour_data: Dict chứa thông tin tour
            datastore: DataStore instance (optional)
        """
        self.parent = parent
        self.tour = tour_data or {}
        self.datastore = datastore
        self.current_weather_data = None
        self.selected_location = None
        self.weather_request_id = 0
        self.map_request_id = 0
        self.current_map_url = None
        self.map_preview_image = None
        self.weather_state = {
            "current_place": None,
            "current_query": None,
            "latitude": None,
            "longitude": None,
            "last_result": None,
        }


        self.window = tk.Toplevel(parent)
        self.window.title("Thời tiết & Vị trí điểm du lịch")
        self.window.geometry("1000x680")
        self.window.minsize(800, 500)
        self.window.configure(bg=THEME["bg"])
        self.window.resizable(True, True)


        self.window.update_idletasks()
        width, height = 1000, 680
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")


        self._build_ui()


        main_destination = safe_get(self.tour, "diemDen", "")
        if main_destination:

            self.window.after(100, lambda: self._load_weather_for_destination(main_destination))

    def _build_ui(self):
        """Xây dựng giao diện popup."""
        self.window.grid_rowconfigure(0, weight=0)
        self.window.grid_rowconfigure(1, weight=0)
        self.window.grid_rowconfigure(2, weight=1)
        self.window.grid_rowconfigure(3, weight=0)
        self.window.grid_columnconfigure(0, weight=1)


        header = tk.Frame(self.window, bg=THEME["primary"])
        header.grid(row=0, column=0, sticky="ew")

        tk.Label(
            header,
            text="THỜI TIẾT & VỊ TRÍ ĐIỂM DU LỊCH",
            bg=THEME["primary"],
            fg="white",
            font=("Times New Roman", 18, "bold")
        ).pack(pady=(12, 2))

        tk.Label(
            header,
            text="Xem thời tiết thực tế, vị trí chi tiết và bản đồ trực quan",
            bg=THEME["primary"],
            fg="#dbeafe",
            font=("Times New Roman", 11, "italic")
        ).pack(pady=(0, 12))


        self._build_tour_info_section(self.window)

        body_frame = tk.Frame(self.window, bg=THEME["bg"])
        body_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=10)
        body_frame.grid_rowconfigure(0, weight=1)
        body_frame.grid_columnconfigure(0, weight=11)
        body_frame.grid_columnconfigure(1, weight=9)


        self._build_itinerary_section(body_frame)


        self._build_weather_section(body_frame)


        footer = tk.Frame(self.window, bg=THEME["bg"])
        footer.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))
        self._build_action_buttons(footer)

    def _build_tour_info_section(self, parent):
        """Xây dựng phần thông tin tour."""
        frame = tk.LabelFrame(
            parent,
            text="Thông tin tour",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=("Times New Roman", 12, "bold"),
            relief="solid",
            bd=1
        )
        frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 0))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        info_grid = tk.Frame(frame, bg=THEME["surface"])
        info_grid.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=10)
        info_grid.grid_columnconfigure(0, weight=1)
        info_grid.grid_columnconfigure(1, weight=1)

        items = [
            ("Mã tour", safe_get(self.tour, "ma")),
            ("Tên tour", safe_get(self.tour, "ten")),
            ("Điểm đi", safe_get(self.tour, "diemDi")),
            ("Điểm đến", safe_get(self.tour, "diemDen")),
            ("Ngày khởi hành", safe_get(self.tour, "ngay")),
            ("Thời gian", safe_get(self.tour, "soNgay")),
        ]

        for idx, (label_text, value) in enumerate(items):
            row = idx // 2
            col = idx % 2
            item_frame = tk.Frame(info_grid, bg=THEME["surface"])
            item_frame.grid(row=row, column=col, sticky="ew", padx=(0, 18) if col == 0 else (18, 0), pady=4)
            tk.Label(
                item_frame,
                text=f"{label_text}:",
                bg=THEME["surface"],
                fg=THEME["muted"],
                font=("Times New Roman", 10, "bold"),
                anchor="w",
                width=14,
            ).pack(side="left")
            tk.Label(
                item_frame,
                text=value,
                bg=THEME["surface"],
                fg=THEME["primary"] if label_text == "Điểm đến" else THEME["text"],
                font=("Times New Roman", 11, "bold" if label_text in ("Tên tour", "Điểm đến") else "normal"),
                anchor="w",
                wraplength=390,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

    def _build_itinerary_section(self, parent):
        """Xây dựng phần danh sách địa điểm lịch trình."""
        frame = tk.LabelFrame(
            parent,
            text="Danh sách địa điểm lịch trình",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=("Times New Roman", 12, "bold"),
            relief="solid",
            bd=1
        )
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)


        lich_trinh = self.tour.get("lichTrinh", [])

        if not lich_trinh:
            tk.Label(
                frame,
                text="Tour chưa có lịch trình chi tiết. Sẽ tra cứu thời tiết cho điểm đến chính.",
                bg=THEME["surface"],
                fg=THEME["muted"],
                font=("Times New Roman", 11, "italic"),
                wraplength=700,
                justify="left"
            ).pack(padx=15, pady=15)
            return


        tree_frame = tk.Frame(frame, bg=THEME["surface"])
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("ngay", "dia_diem", "mo_ta")
        self.itinerary_tree = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="headings",
            height=14,
            selectmode="browse"
        )

        self.itinerary_tree.heading("ngay", text="Ngày")
        self.itinerary_tree.heading("dia_diem", text="Địa điểm")
        self.itinerary_tree.heading("mo_ta", text="Mô tả")

        self.itinerary_tree.column("ngay", width=80, anchor="center")
        self.itinerary_tree.column("dia_diem", width=250, anchor="w")
        self.itinerary_tree.column("mo_ta", width=400, anchor="w")


        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.itinerary_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.itinerary_tree.xview)
        self.itinerary_tree.configure(yscrollcommand=scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.itinerary_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(1, weight=0)
        tree_frame.grid_columnconfigure(0, weight=1)


        for item in lich_trinh:
            ngay = safe_get(item, "ngay", "")
            dia_diem_list = item.get("diaDiem", [])
            mo_ta = safe_get(item, "moTa", "")

            places = []
            if isinstance(dia_diem_list, list):
                for place_raw in dia_diem_list:
                    split_places = [x.strip() for x in str(place_raw).split(",") if x.strip()]
                    places.extend(split_places)
            else:
                places = [x.strip() for x in str(dia_diem_list).split(",") if x.strip()]

            if not places:
                places = [""]

            for idx, place in enumerate(places):
                row_day = ngay if idx == 0 else ""
                row_desc = mo_ta if idx == 0 else ""
                if len(row_desc) > 60:
                    row_desc = row_desc[:57] + "..."
                self.itinerary_tree.insert("", "end", values=(row_day, place, row_desc))


        self.itinerary_tree.bind("<Double-1>", self._on_itinerary_double_click)

    def _build_weather_section(self, parent):
        """Xây dựng phần hiển thị kết quả thời tiết."""
        frame = tk.LabelFrame(
            parent,
            text="Thông tin thời tiết & vị trí",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=("Times New Roman", 12, "bold"),
            relief="solid",
            bd=1
        )
        frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)


        self.status_label = tk.Label(
            frame,
            text="Đang tải dữ liệu thời tiết...",
            bg=THEME["surface"],
            fg=THEME["warning"],
            font=("Times New Roman", 11, "italic"),
            wraplength=700,
            justify="left"
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        scroll_holder = tk.Frame(frame, bg=THEME["surface"])
        scroll_holder.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 10))
        scroll_holder.grid_rowconfigure(0, weight=1)
        scroll_holder.grid_rowconfigure(1, weight=0)
        scroll_holder.grid_columnconfigure(0, weight=1)

        self.weather_canvas = tk.Canvas(scroll_holder, bg=THEME["surface"], highlightthickness=0, bd=0)
        weather_scroll = ttk.Scrollbar(scroll_holder, orient="vertical", command=self.weather_canvas.yview)
        weather_hscroll = ttk.Scrollbar(scroll_holder, orient="horizontal", command=self.weather_canvas.xview)
        self.weather_canvas.configure(yscrollcommand=weather_scroll.set, xscrollcommand=weather_hscroll.set)
        self.weather_canvas.grid(row=0, column=0, sticky="nsew")
        weather_scroll.grid(row=0, column=1, sticky="ns")
        weather_hscroll.grid(row=1, column=0, sticky="ew")

        self.weather_content = tk.Frame(self.weather_canvas, bg=THEME["surface"])
        self.weather_canvas_window = self.weather_canvas.create_window(
            (0, 0),
            window=self.weather_content,
            anchor="nw",
        )

        def _on_content_configure(_event):
            self.weather_canvas.configure(scrollregion=self.weather_canvas.bbox("all"))

        def _on_canvas_configure(event):
            content_width = self.weather_content.winfo_reqwidth()
            if content_width < event.width:
                self.weather_canvas.itemconfigure(self.weather_canvas_window, width=event.width)
            else:
                self.weather_canvas.itemconfigure(self.weather_canvas_window, width=content_width)

        self.weather_content.bind("<Configure>", _on_content_configure)
        self.weather_canvas.bind("<Configure>", _on_canvas_configure)


        def _on_mousewheel(event):
            try:
                self.weather_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        def _bind_wheel(event):
            self.weather_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(event):
            self.weather_canvas.unbind_all("<MouseWheel>")

        self.weather_canvas.bind("<Enter>", _bind_wheel)
        self.weather_canvas.bind("<Leave>", _unbind_wheel)

        self.weather_value_labels = {}
        self.location_card = self._create_info_card(self.weather_content, "VỊ TRÍ HIỆN TẠI")
        self._add_info_row(self.location_card, "Địa điểm tra cứu", "query")
        self._add_info_row(self.location_card, "Query API khớp", "matched_query")
        self._add_info_row(self.location_card, "Nhà cung cấp vị trí", "provider")
        self._add_info_row(self.location_card, "Tên vị trí", "resolved_name")
        self._add_info_row(self.location_card, "Khu vực", "area")
        self._add_info_row(self.location_card, "Quốc gia", "country")
        self._add_info_row(self.location_card, "Vĩ độ", "latitude")
        self._add_info_row(self.location_card, "Kinh độ", "longitude")
        self._add_info_row(self.location_card, "Vị trí hiện tại", "current_address")

        self.weather_card = self._create_info_card(self.weather_content, "THỜI TIẾT HIỆN TẠI")
        self._add_info_row(self.weather_card, "Nhiệt độ hiện tại", "temperature")
        self._add_info_row(self.weather_card, "Thời tiết", "weather_text")
        self._add_info_row(self.weather_card, "Mã thời tiết", "weather_code")
        self._add_info_row(self.weather_card, "Tốc độ gió", "wind_speed")
        self._add_info_row(self.weather_card, "Cập nhật lúc", "time")
        self._add_info_row(self.weather_card, "Nguồn dữ liệu", "source")

        self.map_card = self._create_info_card(self.weather_content, "BẢN ĐỒ VỊ TRÍ")
        self.map_preview_label = tk.Label(
            self.map_card,
            text="Bản đồ sẽ hiển thị sau khi có tọa độ.",
            bg="#eef6ff",
            fg=THEME["muted"],
            font=("Times New Roman", 11, "italic"),
            width=52,
            height=12,
            relief="solid",
            bd=1,
            justify="center",
        )
        self.map_preview_label.pack(fill="x", padx=12, pady=(10, 6))
        self.map_caption_label = tk.Label(
            self.map_card,
            text="Vị trí hiện tại trên bản đồ",
            bg=THEME["surface"],
            fg=THEME["muted"],
            font=("Times New Roman", 10, "italic"),
        )
        self.map_caption_label.pack(anchor="center", pady=(0, 10))
        self._clear_weather_values()

    def _create_info_card(self, parent, title):
        """Tạo card thông tin trong panel thời tiết."""
        card = tk.Frame(
            parent,
            bg=THEME["surface"],
            highlightbackground=THEME["border"],
            highlightthickness=1,
        )
        card.pack(fill="x", padx=2, pady=(0, 10))
        tk.Label(
            card,
            text=title,
            bg="#dbeafe",
            fg=THEME["primary"],
            font=("Times New Roman", 11, "bold"),
            anchor="w",
            padx=10,
            pady=6,
        ).pack(fill="x")
        return card

    def _add_info_row(self, parent, label_text, key):
        """Thêm một dòng key-value vào card."""
        row = tk.Frame(parent, bg=THEME["surface"])
        row.pack(fill="x", padx=12, pady=3)
        tk.Label(
            row,
            text=f"{label_text}:",
            bg=THEME["surface"],
            fg=THEME["muted"],
            font=("Times New Roman", 10, "bold"),
            anchor="w",
            width=18,
        ).pack(side="left")
        value_label = tk.Label(
            row,
            text="--",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=("Times New Roman", 11),
            anchor="w",
            justify="left",
            wraplength=800,
        )
        value_label.pack(side="left", fill="x", expand=True)
        self.weather_value_labels[key] = value_label

    def _clear_weather_values(self):
        """Đặt panel thời tiết về trạng thái rỗng thân thiện."""
        for label in self.weather_value_labels.values():
            label.config(text="--")

    def _format_current_address(self, result, area):
        """Tạo chuỗi vị trí hiện tại dễ đọc từ dữ liệu geocoding."""
        display_name = result.get("display_name")
        if display_name:
            return str(display_name)

        address = result.get("address")
        if isinstance(address, dict):
            preferred_keys = [
                "tourism",
                "historic",
                "amenity",
                "road",
                "suburb",
                "city",
                "town",
                "village",
                "county",
                "state",
                "country",
            ]
            parts = []
            for key in preferred_keys:
                value = address.get(key)
                if value and value not in parts:
                    parts.append(str(value))
            if parts:
                return ", ".join(parts)
        if address:
            return str(address)

        return ", ".join([x for x in [result.get("resolved_name", ""), area, result.get("country", "")] if x])

    def _build_action_buttons(self, parent):
        """Xây dựng các nút hành động."""
        button_frame = tk.Frame(parent, bg=THEME["bg"])
        button_frame.pack(side="right")


        self.reload_btn = RoundedButton(
            button_frame,
            text="Tải lại",
            bg=THEME["warning"],
            fg="white",
            font=("Times New Roman", 11, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._reload_weather
        )
        self.reload_btn.pack(side="left", padx=(0, 10))


        self.map_btn = RoundedButton(
            button_frame,
            text="Mở trên Google Maps",
            bg=THEME["success"],
            fg="white",
            font=("Times New Roman", 11, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            state="disabled",
            command=self._open_map
        )
        self.map_btn.pack(side="left", padx=(0, 10))


        self.close_btn = RoundedButton(
            button_frame,
            text="Đóng",
            bg=THEME["danger"],
            fg="white",
            font=("Times New Roman", 11, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.window.destroy
        )
        self.close_btn.pack(side="right")

    def _set_weather_text(self, content):
        """Ghi nội dung vào khung thời tiết và luôn cuộn về đầu."""
        if not hasattr(self, "weather_text"):
            return
        self.weather_text.config(state="normal")
        self.weather_text.delete("1.0", "end")
        self.weather_text.insert("1.0", content)
        self.weather_text.config(state="disabled")
        self.weather_text.yview_moveto(0)

    def set_loading_state(self, location_name):
        """Hiển thị trạng thái đang tải mà không làm mất footer."""
        self.status_label.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        self.status_label.config(
            text=f"⏳ Đang tải dữ liệu thời tiết cho '{location_name}'...\n(Vui lòng đợi 5-20 giây, tùy tốc độ mạng)",
            fg=THEME["warning"],
        )
        self._clear_weather_values()
        self.map_preview_label.config(
            image="",
            text="Đang chờ tọa độ để tải bản đồ...",
            bg="#eef6ff",
            fg=THEME["muted"],
            width=52,
            height=12,
        )
        self.map_preview_image = None
        self.weather_canvas.yview_moveto(0)

    def set_error_state(self, message, query=""):
        """Hiển thị lỗi rõ ràng trong panel phải."""
        self.status_label.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        self.status_label.config(
            text=f"❌ Không lấy được dữ liệu thời tiết & vị trí.\nChi tiết lỗi: {message}",
            fg=THEME["danger"],
        )
        self._clear_weather_values()
        self.weather_value_labels["query"].config(text=query or self.selected_location or "--")
        self.map_preview_label.config(
            image="",
            text="Không tải được xem trước bản đồ.",
            bg="#fff7ed",
            fg=THEME["warning"],
            width=52,
            height=12,
        )
        self.map_preview_image = None

    def build_map_preview_url(self, lat, lon):
        """Tạo URL tile OpenStreetMap trung tâm để debug khi cần."""
        zoom = 14
        tile_x, tile_y = self._lat_lon_to_tile(lat, lon, zoom)
        return f"https://tile.openstreetmap.org/{zoom}/{int(tile_x)}/{int(tile_y)}.png"

    def _lat_lon_to_tile(self, lat, lon, zoom):
        """Đổi lat/lon sang tọa độ tile dạng số thực."""
        lat_rad = math.radians(float(lat))
        n = 2 ** zoom
        x = (float(lon) + 180.0) / 360.0 * n
        y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
        return x, y

    def render_map_preview(self, lat, lon):
        """Tải và hiển thị bản đồ thu nhỏ trong popup."""
        if lat is None or lon is None:
            self.map_preview_label.config(
                image="",
                text="Không có tọa độ để hiển thị bản đồ.",
                bg="#fff7ed",
                fg=THEME["warning"],
                width=52,
                height=12,
            )
            self.map_preview_image = None
            return

        self.map_request_id += 1
        request_id = self.map_request_id
        self.map_preview_label.config(
            image="",
            text="Đang tải bản đồ vị trí...",
            bg="#eef6ff",
            fg=THEME["muted"],
            width=52,
            height=12,
        )

        thread = threading.Thread(
            target=self._fetch_map_preview,
            args=(lat, lon, request_id),
            daemon=True,
        )
        thread.start()

    def _fetch_map_preview(self, lat, lon, request_id):
        """Tải ảnh bản đồ ở thread phụ, cập nhật UI qua after."""
        try:
            image = self._build_osm_tile_preview(lat, lon)
            self.window.after(0, lambda: self._update_map_preview(request_id, image, None))
        except Exception as exc:
            self.window.after(0, lambda: self._update_map_preview(request_id, None, str(exc)))

    def _build_osm_tile_preview(self, lat, lon):
        """Ghép tile OpenStreetMap thành ảnh preview và vẽ marker ở giữa."""
        zoom = 14
        tile_size = 256
        width, height = 640, 320
        tile_x, tile_y = self._lat_lon_to_tile(lat, lon, zoom)
        center_px = tile_x * tile_size
        center_py = tile_y * tile_size
        start_px = int(center_px - width / 2)
        start_py = int(center_py - height / 2)
        start_tile_x = start_px // tile_size
        start_tile_y = start_py // tile_size
        end_tile_x = int((start_px + width) // tile_size)
        end_tile_y = int((start_py + height) // tile_size)

        preview = Image.new("RGB", (width, height), "#e5edf5")
        loaded_count = 0
        max_tile = (2 ** zoom) - 1

        for tx in range(start_tile_x, end_tile_x + 1):
            for ty in range(start_tile_y, end_tile_y + 1):
                if ty < 0 or ty > max_tile:
                    continue
                wrapped_tx = tx % (2 ** zoom)
                tile_url = f"https://tile.openstreetmap.org/{zoom}/{wrapped_tx}/{ty}.png"
                try:
                    request = Request(tile_url, headers={"User-Agent": "TourManagementTkinter/1.0"})
                    with urlopen(request, timeout=10) as response:
                        tile_raw = response.read()
                    tile = Image.open(BytesIO(tile_raw)).convert("RGB")
                    paste_x = tx * tile_size - start_px
                    paste_y = ty * tile_size - start_py
                    preview.paste(tile, (paste_x, paste_y))
                    loaded_count += 1
                except Exception:
                    continue

        if loaded_count == 0:
            raise RuntimeError("Không tải được tile bản đồ.")

        draw = ImageDraw.Draw(preview)
        cx, cy = width // 2, height // 2
        draw.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill="#dc2626", outline="white", width=3)
        draw.polygon([(cx, cy + 18), (cx - 7, cy + 5), (cx + 7, cy + 5)], fill="#dc2626")
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill="white")
        return preview

    def _update_map_preview(self, request_id, image, error):
        """Gắn ảnh bản đồ vào Label nếu request vẫn là request mới nhất."""
        if request_id != self.map_request_id:
            return
        if error or image is None:
            self.map_preview_label.config(
                image="",
                text="Không tải được xem trước bản đồ.",
                bg="#fff7ed",
                fg=THEME["warning"],
                width=52,
                height=12,
            )
            self.map_preview_image = None
            return
        self.map_preview_image = ImageTk.PhotoImage(image)
        self.map_preview_label.config(
            image=self.map_preview_image,
            text="",
            bg=THEME["surface"],
            width=image.width,
            height=image.height,
        )

    def _on_itinerary_double_click(self, event):
        """Xử lý double-click vào địa điểm trong lịch trình."""
        selection = self.itinerary_tree.selection()
        if not selection:
            return

        item = self.itinerary_tree.item(selection[0])
        values = item.get("values", [])
        if len(values) < 2:
            return

        dia_diem_str = str(values[1]).strip()
        if not dia_diem_str:
            return


        dia_diem_list = [d.strip() for d in dia_diem_str.split(",") if d.strip()]
        if dia_diem_list:
            location = dia_diem_list[0]
            self.weather_state["current_place"] = location
            query = build_weather_location_query(self.tour, location)
            self.weather_state["current_query"] = query
            self._load_weather_async(query)

    def _reload_weather(self):
        """Tải lại thời tiết cho địa điểm hiện tại."""
        if self.selected_location:
            self._load_weather_async(self.selected_location)
        else:
            main_destination = safe_get(self.tour, "diemDen", "")
            if main_destination:
                self._load_weather_for_destination(main_destination)

    def _load_weather_for_destination(self, destination):
        """Tải thời tiết cho điểm đến chính (không cần ghép thêm)."""
        self._load_weather_async(destination)

    def _load_weather_async(self, location_name):
        """Tải thời tiết bất đồng bộ."""
        self.selected_location = location_name
        self.weather_state["current_query"] = location_name
        if not self.weather_state.get("current_place"):
            self.weather_state["current_place"] = location_name
        self.weather_request_id += 1
        request_id = self.weather_request_id

        self.set_loading_state(location_name)
        self.map_btn.config(state="disabled")
        self.reload_btn.config(state="disabled")


        thread = threading.Thread(
            target=self._fetch_weather_data,
            args=(location_name, request_id),
            daemon=True
        )
        thread.start()

    def _fetch_weather_data(self, location_name, request_id):
        """Gọi API lấy dữ liệu thời tiết (chạy trong thread)."""
        try:
            def update_loading():
                try:
                    if self.window and self.window.winfo_exists():
                        self.status_label.config(
                            text=f"⏳ Đang tải dữ liệu thời tiết và vị trí cho '{location_name}'...\n(Vui lòng đợi 5-20 giây, tùy tốc độ mạng)",
                            fg=THEME["warning"]
                        )
                except (tk.TclError, AttributeError):
                    pass
            self.window.after(0, update_loading)


            lat = self.tour.get("lat") or self.tour.get("latitude")
            lon = self.tour.get("lon") or self.tour.get("longitude")
            main_destination = safe_get(self.tour, "diemDen", "")

            result = None

            if location_name.strip().lower() == main_destination.strip().lower() and lat is not None and lon is not None:
                try:
                    lat_val = float(lat)
                    lon_val = float(lon)
                    weather_res = fetch_weather_by_coordinates(lat_val, lon_val)
                    if weather_res.get("ok"):
                        result = {
                            "ok": True,
                            "query": location_name,
                            "resolved_name": main_destination,
                            "latitude": lat_val,
                            "longitude": lon_val,
                            "temperature": weather_res.get("temperature"),
                            "weather_code": weather_res.get("weather_code"),
                            "weather_text": weather_res.get("weather_text"),
                            "wind_speed": weather_res.get("wind_speed"),
                            "time": weather_res.get("time"),
                            "source": "Tour Coordinates + Open-Meteo Forecast",
                            "provider": "Tour Data"
                        }
                    else:
                        result = {
                            "ok": False,
                            "query": location_name,
                            "error": weather_res.get("error", "Không thể tải dữ liệu thời tiết hiện tại. Vui lòng kiểm tra kết nối mạng hoặc thử lại sau.")
                        }
                except (ValueError, TypeError):
                    pass

            if result is None:

                result = get_location_weather(
                    location_name,
                    expected_destination=main_destination,
                    timeout=20
                )


            def post_result():
                try:
                    if self.window and self.window.winfo_exists():
                        self._render_if_latest(request_id, result)
                except (tk.TclError, AttributeError):
                    pass
            self.window.after(0, post_result)

        except Exception as e:
            error_result = {
                "ok": False,
                "query": location_name,
                "error": f"Lỗi không xác định: {str(e)}"
            }
            def post_error():
                try:
                    if self.window and self.window.winfo_exists():
                        self._render_if_latest(request_id, error_result)
                except (tk.TclError, AttributeError):
                    pass
            try:
                self.window.after(0, post_error)
            except (tk.TclError, AttributeError):
                pass

    def _render_if_latest(self, request_id, result):
        try:
            if not self.window or not self.window.winfo_exists():
                return
        except (tk.TclError, AttributeError):
            return

        if request_id != self.weather_request_id:
            return
        self._update_weather_ui(result)

    def _update_weather_ui(self, result):
        """Cập nhật UI với dữ liệu thời tiết."""
        try:
            if not self.window or not self.window.winfo_exists():
                return
        except (tk.TclError, AttributeError):
            return

        try:
            self.current_weather_data = result
            self.weather_state["last_result"] = result
            self.reload_btn.config(state="normal")

            if not result.get("ok"):
                error_msg = result.get("error", "Không thể lấy dữ liệu thời tiết")
                self.set_error_state(error_msg, result.get("query", self.selected_location or ""))
                self.map_btn.config(state="disabled")
                self.current_map_url = None
                self.weather_state["latitude"] = None
                self.weather_state["longitude"] = None
                return

            self.status_label.grid_remove()

            admin1 = result.get("admin1", "")
            admin2 = result.get("admin2", "")
            admin3 = result.get("admin3", "")
            area = ", ".join([x for x in [admin1, admin2, admin3] if x])

            lat = result.get("latitude")
            lon = result.get("longitude")
            lat_display = f"{lat:.4f}" if lat is not None else "N/A"
            lon_display = f"{lon:.4f}" if lon is not None else "N/A"

            temp = result.get("temperature")
            temp_display = f"{temp} °C" if temp is not None else "N/A"

            wind = result.get("wind_speed")
            wind_display = f"{wind} km/h" if wind is not None else "N/A"

            time_str = result.get("time", "")
            if time_str:
                try:
                    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    time_display = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    time_display = time_str
            else:
                time_display = "N/A"

            self.current_map_url = build_google_maps_url(lat, lon, result.get("query", "")) if lat is not None and lon is not None else None
            self.weather_state["latitude"] = lat
            self.weather_state["longitude"] = lon
            current_address = self._format_current_address(result, area)

            values = {
                "query": result.get("query", ""),
                "matched_query": result.get("matched_query", ""),
                "provider": result.get("provider", ""),
                "resolved_name": result.get("resolved_name", ""),
                "area": area or "N/A",
                "country": result.get("country", "N/A"),
                "latitude": lat_display,
                "longitude": lon_display,
                "current_address": current_address or "N/A",
                "temperature": temp_display,
                "weather_text": result.get("weather_text", "N/A"),
                "weather_code": str(result.get("weather_code", "N/A")),
                "wind_speed": wind_display,
                "time": time_display,
                "source": result.get("source", "Open-Meteo"),
            }
            for key, value in values.items():
                if key in self.weather_value_labels:
                    self.weather_value_labels[key].config(text=value)

            self.weather_canvas.yview_moveto(0)
            self.render_map_preview(lat, lon)

            if lat is not None and lon is not None:
                self.map_btn.config(state="normal")
            else:
                self.map_btn.config(state="disabled")
                self.current_map_url = None
        except (tk.TclError, AttributeError):
            pass

    def _open_map(self):
        """Mở vị trí trên Google Maps."""
        try:
            if not self.window or not self.window.winfo_exists():
                return
        except (tk.TclError, AttributeError):
            return

        lat = self.weather_state.get("latitude")
        lon = self.weather_state.get("longitude")
        if (lat is None or lon is None) and self.current_weather_data:
            lat = self.current_weather_data.get("latitude")
            lon = self.current_weather_data.get("longitude")

        country_code = ""
        if self.current_weather_data:
            country_code = str(self.current_weather_data.get("country_code", "")).upper()

        if lat is None or lon is None:
            messagebox.showwarning(
                "Chưa có tọa độ",
                "Chưa có tọa độ hợp lệ để mở bản đồ.",
                parent=self.window
            )
            return
        if not self.current_map_url:
            messagebox.showwarning(
                "Chưa có tọa độ",
                "Chưa có tọa độ để mở bản đồ.",
                parent=self.window
            )
            return
        if country_code and country_code != "VN":
            messagebox.showwarning(
                "Không mở bản đồ",
                "Tọa độ hiện tại không thuộc Việt Nam.",
                parent=self.window
            )
            return


        map_url = build_google_maps_url(lat, lon, self.selected_location)
        if not map_url:
            messagebox.showwarning("Thông báo", "Không tạo được URL bản đồ.", parent=self.window)
            return

        try:
            webbrowser.open(map_url)
        except Exception as e:
            messagebox.showerror(
                "Lỗi",
                f"Không thể mở trình duyệt: {str(e)}",
                parent=self.window
            )


def open_tour_weather_popup(parent, tour_data, datastore=None):
    """
    Hàm tiện ích để mở popup thời tiết cho tour.

    Args:
        parent: Widget cha
        tour_data: Dict chứa thông tin tour
        datastore: DataStore instance (optional)
    """
    try:
        TourWeatherPopup(parent, tour_data, datastore)
    except Exception as e:
        messagebox.showerror(
            "Lỗi",
            f"Không thể mở popup thời tiết: {str(e)}",
            parent=parent
        )


def open_weather_map_popup(parent, tour, datastore=None):
    """
    Wrapper helper cho STEP 6.
    """
    return open_tour_weather_popup(parent, tour, datastore)
