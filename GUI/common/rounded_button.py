import math
import tkinter as tk
from tkinter import font as tkfont


class RoundedButton(tk.Canvas):
    """
    Điều chỉnh các nút buttton mặc định của Tkinter để có hình dạng tròn hơn
    và hỗ trợ nhiều tùy chọn hơn như màu nền, màu chữ, font chữ, padding, v.v.
    Nút này cũng hỗ trợ trạng thái "disabled" và hiệu ứng khi nhấn hoặc hover chuột.
    """

    def __init__(self, master=None, cnf=None, **kw):
        """
        Khởi tạo nút bo tròn với các thuộc tính màu sắc, font, viền, bo góc và sự kiện nhấn chuột.
        """
        options = {}
        if cnf:
            options.update(cnf)
        options.update(kw)

        self._command = options.pop("command", None)
        self._text = str(options.pop("text", ""))
        self._bg = options.pop("bg", options.pop("background", "#2563eb"))
        self._fg = options.pop("fg", options.pop("foreground", "white"))
        self._active_bg = options.pop("activebackground", self._bg)
        self._active_fg = options.pop("activeforeground", self._fg)
        self._font = options.pop("font", ("Times New Roman", 11, "bold"))
        self._padx = int(options.pop("padx", 14))
        self._pady = int(options.pop("pady", 9))
        self._wraplength = int(options.pop("wraplength", 0) or 0)
        self._anchor = options.pop("anchor", "center")
        self._justify = options.pop("justify", "center")
        self._state = options.pop("state", "normal")
        self._radius = int(options.pop("radius", 14))
        self._cursor = options.pop("cursor", "hand2")

        relief = options.pop("relief", "flat")
        borderwidth = options.pop("bd", options.pop("borderwidth", 0))
        options.pop("highlightthickness", None)
        options.pop("highlightbackground", None)
        options.pop("highlightcolor", None)

        parent_bg = options.pop("canvas_bg", None)
        if parent_bg is None:
            try:
                parent_bg = master.cget("bg")
            except Exception:
                parent_bg = self._bg

        super().__init__(
            master,
            relief=relief,
            bd=borderwidth,
            highlightthickness=0,
            bg=parent_bg,
            cursor=self._cursor,
            **options,
        )

        self._shape_id = self.create_polygon(0, 0, 0, 0, smooth=True, splinesteps=24, outline=self._bg, fill=self._bg)
        self._text_id = self.create_text(0, 0, text=self._text, fill=self._fg, font=self._font)
        self._pressed = False
        self._hover = False

        self.bind("<Configure>", self._on_resize)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Destroy>", self._on_destroy)

        self._alive = True
        self._update_requested_size()
        self.after_idle(self._redraw)

    def _on_destroy(self, _event):
        """
        Xử lý dọn dẹp biến khi đối tượng nút bị hủy.
        """
        self._alive = False

    def _rounded_points(self, x1, y1, x2, y2, r):
        """
        Tạo danh sách tọa độ đa giác để vẽ hình bo tròn.
        """
        return [
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1 + r,
            x1,
            y1,
        ]

    def _text_layout(self, width, height):
        """
        Tính toán tọa độ hiển thị văn bản trên nút dựa trên neo (anchor).
        """
        anchor = str(self._anchor or "center").strip().lower()



        if anchor in {"w", "nw", "sw"}:
            x = self._padx
            h = "w"
        elif anchor in {"e", "ne", "se"}:
            x = width - self._padx
            h = "e"
        else:
            x = width / 2
            h = ""

        if anchor in {"n", "ne", "nw"}:
            y = self._pady
            v = "n"
        elif anchor in {"s", "se", "sw"}:
            y = height - self._pady
            v = "s"
        else:
            y = height / 2
            v = ""

        text_anchor = f"{v}{h}" if (v or h) else "center"
        return x, y, text_anchor

    def _get_font(self):
        """
        Lấy font chữ từ Tkinter một cách an toàn.
        """
        try:
            return tkfont.nametofont(self._font)
        except Exception:
            try:
                return tkfont.Font(font=self._font)
            except Exception:
                return tkfont.nametofont("TkDefaultFont")

    def _estimate_text_lines(self, fnt, wraplength):
        """
        Ước lượng số dòng và độ rộng tối đa của văn bản khi xuống dòng tự động.
        """
        lines = self._text.splitlines() or [""]
        if wraplength <= 0:
            return len(lines), max((fnt.measure(line) for line in lines), default=0)

        visual_lines = 0
        max_line_width = 0
        for line in lines:
            width = max(1, fnt.measure(line))
            max_line_width = max(max_line_width, min(width, wraplength))
            visual_lines += max(1, int(math.ceil(width / max(1, wraplength))))
        return max(1, visual_lines), max_line_width

    def _update_requested_size(self):
        """
        Cập nhật kích thước mong muốn của nút dựa trên độ dài văn bản và padding.
        """
        fnt = self._get_font()
        wrap = max(0, int(self._wraplength))
        line_count, text_width = self._estimate_text_lines(fnt, wrap)
        line_height = max(12, int(fnt.metrics("linespace")))

        req_w = max(40, int(text_width + self._padx * 2 + 8))
        req_h = max(28, int(line_count * line_height + self._pady * 2 + 6))
        self.configure(width=req_w, height=req_h)

    def _current_fill(self):
        """
        Lấy màu nền hiện tại của nút tùy theo trạng thái (bình thường, hover, nhấn, hoặc disable).
        """
        if self._state == "disabled":
            return "#94a3b8"
        if self._pressed or self._hover:
            return self._active_bg
        return self._bg

    def _current_text_color(self):
        """
        Lấy màu chữ hiện tại của nút tùy theo trạng thái.
        """
        if self._state == "disabled":
            return "#e2e8f0"
        if self._pressed or self._hover:
            return self._active_fg
        return self._fg

    def _redraw(self):
        """
        Vẽ lại hình dáng và văn bản trên Canvas khi thay đổi kích thước hoặc trạng thái.
        """
        if not self._alive:
            return

        width = max(2, int(self.winfo_width()))
        height = max(2, int(self.winfo_height()))
        radius = min(self._radius, max(2, int(min(width, height) / 2)))
        pts = self._rounded_points(1, 1, width - 1, height - 1, radius)

        self.coords(self._shape_id, *pts)
        fill = self._current_fill()
        self.itemconfigure(self._shape_id, fill=fill, outline=fill)

        tx, ty, text_anchor = self._text_layout(width, height)
        self.coords(self._text_id, tx, ty)
        available_width = max(0, width - (self._padx * 2))
        text_width = max(0, min(self._wraplength, available_width)) if self._wraplength > 0 else 0
        self.itemconfigure(
            self._text_id,
            text=self._text,
            fill=self._current_text_color(),
            font=self._font,
            anchor=text_anchor,
            justify=self._justify,
            width=text_width,
        )

    def _on_resize(self, _event):
        """
        Xử lý vẽ lại khi nút thay đổi kích thước.
        """
        self._redraw()

    def _on_enter(self, _event):
        """
        Hiệu ứng khi di chuột vào nút (hover).
        """
        if self._state == "disabled":
            return
        self._hover = True
        self._redraw()

    def _on_leave(self, _event):
        """
        Hiệu ứng khi di chuột ra khỏi nút.
        """
        if self._state == "disabled":
            return
        self._hover = False
        self._pressed = False
        self._redraw()

    def _on_press(self, _event):
        """
        Hiệu ứng khi nhấn chuột trái lên nút.
        """
        if self._state == "disabled":
            return
        self._pressed = True
        self._redraw()

    def _on_release(self, event):
        """
        Kích hoạt lệnh callback (command) khi thả chuột trái trong vùng của nút.
        """
        if self._state == "disabled":
            return
        was_pressed = self._pressed
        self._pressed = False
        self._redraw()
        if was_pressed and self._command and 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self._command()

    def invoke(self):
        """
        Kích hoạt nút lập trình bằng mã lệnh.
        """
        if self._state != "disabled" and self._command:
            return self._command()
        return None

    def configure(self, cnf=None, **kw):
        """
        Cấu hình lại các tham số của nút (text, bg, fg, command, radius...).
        """
        cfg = {}
        if cnf:
            cfg.update(cnf)
        cfg.update(kw)

        style_changed = False
        passthrough = {}
        for key, value in cfg.items():
            if key in {"text"}:
                self._text = str(value)
                style_changed = True
            elif key in {"bg", "background"}:
                self._bg = value
                style_changed = True
            elif key in {"fg", "foreground"}:
                self._fg = value
                style_changed = True
            elif key == "activebackground":
                self._active_bg = value
                style_changed = True
            elif key == "activeforeground":
                self._active_fg = value
                style_changed = True
            elif key == "font":
                self._font = value
                style_changed = True
            elif key == "padx":
                self._padx = int(value)
                style_changed = True
            elif key == "pady":
                self._pady = int(value)
                style_changed = True
            elif key == "wraplength":
                self._wraplength = int(value or 0)
                style_changed = True
            elif key == "anchor":
                self._anchor = value
                style_changed = True
            elif key == "justify":
                self._justify = value
                style_changed = True
            elif key == "command":
                self._command = value
            elif key == "state":
                self._state = value
                style_changed = True
            elif key == "cursor":
                self._cursor = value
                passthrough[key] = value
            elif key == "radius":
                self._radius = max(2, int(value))
                style_changed = True
            elif key in {"highlightthickness", "highlightbackground", "highlightcolor"}:
                continue
            else:
                passthrough[key] = value

        if passthrough:
            super().configure(**passthrough)

        if style_changed:
            self._update_requested_size()
            self._redraw()

    config = configure

    def cget(self, key):
        """
        Truy vấn giá trị thuộc tính cấu hình hiện tại của nút.
        """
        lookup = str(key).lower()
        if lookup in {"text"}:
            return self._text
        if lookup in {"bg", "background"}:
            return self._bg
        if lookup in {"fg", "foreground"}:
            return self._fg
        if lookup == "activebackground":
            return self._active_bg
        if lookup == "activeforeground":
            return self._active_fg
        if lookup == "font":
            return self._font
        if lookup == "padx":
            return self._padx
        if lookup == "pady":
            return self._pady
        if lookup == "wraplength":
            return self._wraplength
        if lookup == "anchor":
            return self._anchor
        if lookup == "justify":
            return self._justify
        if lookup == "state":
            return self._state
        if lookup == "command":
            return self._command
        if lookup == "radius":
            return self._radius
        return super().cget(key)
