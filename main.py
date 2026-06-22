




from GUI.Admin.Admin import DataStore, main as hien_thi_admin
from GUI.HuongDV.Guide import khoi_tao_hdv as hien_thi_guide
from GUI.Khach.user import khoi_tao_khach as hien_thi_khach
from GUI.common.rounded_button import RoundedButton
from PIL import Image, ImageTk
from core.app import AuthService, enable_tk_text_autofix
from tkinter import messagebox
from tkinter import ttk
import os
import tkinter as tk

LOGIN_WINDOW_SIZE = "1200x700"
WORKSPACE_WINDOW_SIZE = "1080x1920"

PASTEL = {
    "bg": "#F6F8FA",
    "surface": "#FFFFFF",

    "primary": "#6B8FEF",
    "primary_hover": "#5D7FDB",

    "warning": "#D9A441",
    "warning_hover": "#C7922F",

    "danger": "#E57373",
    "danger_hover": "#D65F5F",

    "success": "#6FBF8A",
    "success_hover": "#5AAA78",

    "text": "#334155",
    "muted": "#64748B",

    "border": "#DDE3EA",
    "input_bg": "#FFFFFF",
}


class TravelSystem:
    """
    Lớp quản lý luồng đăng nhập, đăng ký và chuyển hướng màn hình chính của hệ thống.
    """
    def __init__(self, root):
        """
        Khởi tạo hệ thống, thiết lập giao diện gốc, tải dữ liệu nền và mở màn hình chọn vai trò.
        """
        self.root = root
        self.configure_ui_fonts()
        self.root.title("Hệ thống Quản lý Du lịch 2026")
        self.root.configure(bg=PASTEL["bg"])
        self.root.state("zoomed")

        self.ds = DataStore()
        self.auth_service = AuthService(self.ds)

        self.main_frame = tk.Frame(self.root, bg=PASTEL["bg"])
        self.main_frame.pack(fill="both", expand=True)

        self.bg_label = None
        self.bg_image = None
        self.current_role = None
        self.ent_user = None
        self.ent_pass = None
        self.reg_widgets = {}

        self.show_role_selection()

    def configure_ui_fonts(self):
        """
        Cấu hình font chữ mặc định chuẩn (Times New Roman) cho toàn bộ widget hệ thống.
        """
        default_font = ("Times New Roman", 12)
        heading_font = ("Times New Roman", 12, "bold")

        self.root.option_add("*Font", default_font)
        self.root.option_add("*Label.Font", default_font)
        self.root.option_add("*Button.Font", default_font)
        self.root.option_add("*Entry.Font", default_font)
        self.root.option_add("*Text.Font", default_font)
        self.root.option_add("*Spinbox.Font", default_font)
        self.root.option_add("*TCombobox*Listbox*Font", default_font)

        style = ttk.Style(self.root)
        style.configure("TLabel", font=default_font)
        style.configure("TButton", font=heading_font)
        style.configure("TEntry", font=default_font)
        style.configure("TCombobox", font=default_font)

    def clear_screen(self):
        """
        Dọn dẹp tất cả các widget hiện tại trong frame chính để vẽ màn hình mới.
        """
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.bg_label = None

    def get_bg_path(self):
        """
        Lấy đường dẫn tệp ảnh nền giao diện đăng nhập.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "background.jpg")

    def set_background(self):
        """
        Tải và hiển thị ảnh nền tràn màn hình chính.
        """
        try:
            image_path = self.get_bg_path()
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()

            img = Image.open(image_path)
            img = img.resize((width, height), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)

            self.bg_label = tk.Label(self.main_frame, image=self.bg_image, bd=0)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except (OSError, ValueError, tk.TclError) as exc:
            print("Lỗi load background:", exc)
            self.bg_label = tk.Frame(self.main_frame, bg=PASTEL["bg"])
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    def make_soft_button(self, parent, text, bg, hover_bg, command, width=24, height=2):
        """
        Hàm tiện ích tạo nhanh nút giao diện bo tròn RoundedButton.
        """
        btn = RoundedButton(
            parent,
            text=text,
            bg=bg,
            fg="white",
            font=("Times New Roman", 12, "bold"),
            activebackground=hover_bg,
            activeforeground="white",
            radius=16,
            padx=max(14, int(width) * 4),
            pady=max(8, int(height) * 5),
            command=command,
        )

        btn.configure(width=max(220, int(width) * 12), height=max(42, int(height) * 22))
        return btn

    def make_entry(self, parent, show=None):
        """
        Tạo ô nhập liệu văn bản với kiểu dáng đồng bộ.
        """
        return tk.Entry(
            parent,
            font=("Times New Roman", 12),
            bd=1,
            relief="solid",
            bg=PASTEL["input_bg"],
            fg=PASTEL["text"],
            insertbackground=PASTEL["text"],
            show=show or "",
        )

    def make_center_card(self, width=430, height=None):
        """
        Tạo thẻ card nằm ở chính giữa màn hình làm nền cho form đăng ký/đăng nhập.
        """
        parent = self.bg_label if self.bg_label else self.main_frame
        card = tk.Frame(
            parent,
            bg=PASTEL["surface"],
            bd=0,
            highlightbackground=PASTEL["border"],
            highlightthickness=1,
            padx=36,
            pady=32,
        )

        if height:
            card.place(relx=0.5, rely=0.5, anchor="center", width=width, height=height)
        else:
            card.place(relx=0.5, rely=0.5, anchor="center", width=width)

        return card

    def show_role_selection(self):
        """
        Màn hình đầu tiên cho phép chọn vai trò đăng nhập (Admin, Hướng dẫn viên, Khách hàng).
        """
        self.clear_screen()
        self.root.geometry(LOGIN_WINDOW_SIZE)
        self.set_background()

        card = self.make_center_card(width=430)

        tk.Label(
            card,
            text="VIETNAM TRAVEL",
            font=("Times New Roman", 28, "bold"),
            bg=PASTEL["surface"],
            fg=PASTEL["primary"],
        ).pack(pady=(4, 10))

        tk.Label(
            card,
            text="Bạn muốn đăng nhập với vai trò nào?",
            font=("Times New Roman", 13, "italic"),
            bg=PASTEL["surface"],
            fg=PASTEL["muted"],
        ).pack(pady=(0, 26))

        roles = [
            ("ADMIN (Quản trị)", PASTEL["danger"], PASTEL["danger_hover"], "admin"),
            ("GUIDE (Hướng dẫn viên)", PASTEL["warning"], PASTEL["warning_hover"], "guide"),
            ("USER (Khách du lịch)", PASTEL["success"], PASTEL["success_hover"], "user"),
        ]

        for text, color, hover, role_type in roles:
            self.make_soft_button(
                card,
                text=text,
                bg=color,
                hover_bg=hover,
                command=lambda r=role_type: self.show_login_screen(r),
                width=24,
            ).pack(pady=9)

        tk.Label(
            card,
            text="© 2026 Travel Management | Developed by TNY",
            font=("Times New Roman", 11),
            bg=PASTEL["surface"],
            fg=PASTEL["muted"],
        ).pack(pady=(24, 4))

    def show_login_screen(self, role):
        """
        Hiển thị form nhập tài khoản và mật khẩu tương ứng với vai trò đã chọn.
        """
        self.clear_screen()
        self.root.geometry(LOGIN_WINDOW_SIZE)
        self.current_role = role
        self.set_background()

        role_name = {
            "admin": "QUẢN TRỊ VIÊN",
            "guide": "HƯỚNG DẪN VIÊN",
            "user": "KHÁCH DU LỊCH",
        }
        role_color = {
            "admin": PASTEL["danger"],
            "guide": PASTEL["warning"],
            "user": PASTEL["success"],
        }
        role_hover = {
            "admin": PASTEL["danger_hover"],
            "guide": PASTEL["warning_hover"],
            "user": PASTEL["success_hover"],
        }

        card = self.make_center_card(width=390)

        tk.Label(
            card,
            text="ĐĂNG NHẬP",
            font=("Times New Roman", 24, "bold"),
            bg=PASTEL["surface"],
            fg=PASTEL["text"],
        ).pack(pady=(0, 8))

        tk.Label(
            card,
            text=role_name[role],
            font=("Times New Roman", 12, "bold"),
            bg=PASTEL["surface"],
            fg=role_color[role],
        ).pack(pady=(0, 22))

        tk.Label(
            card,
            text="Tài khoản",
            font=("Times New Roman", 11, "bold"),
            bg=PASTEL["surface"],
            fg=PASTEL["text"],
        ).pack(anchor="w")
        self.ent_user = self.make_entry(card)
        self.ent_user.pack(fill="x", pady=(5, 14), ipady=6)

        tk.Label(
            card,
            text="Mật khẩu",
            font=("Times New Roman", 11, "bold"),
            bg=PASTEL["surface"],
            fg=PASTEL["text"],
        ).pack(anchor="w")
        self.ent_pass = self.make_entry(card, show="*")
        self.ent_pass.pack(fill="x", pady=(5, 20), ipady=6)

        self.make_soft_button(
            card,
            text="ĐĂNG NHẬP",
            bg=role_color[role],
            hover_bg=role_hover[role],
            command=self.handle_login,
            width=22,
        ).pack(pady=(6, 10))

        if role == "user":
            tk.Button(
                card,
                text="Chưa có tài khoản Đăng ký ngay",
                font=("Times New Roman", 11, "underline"),
                fg=PASTEL["primary"],
                bg=PASTEL["surface"],
                bd=0,
                cursor="hand2",
                activebackground=PASTEL["surface"],
                activeforeground=PASTEL["primary"],
                command=self.show_register_screen,
            ).pack(pady=(4, 6))

        tk.Button(
            card,
            text="← Quay lại",
            font=("Times New Roman", 11),
            fg=PASTEL["muted"],
            bg=PASTEL["surface"],
            bd=0,
            cursor="hand2",
            activebackground=PASTEL["surface"],
            activeforeground=PASTEL["text"],
            command=self.show_role_selection,
        ).pack()

        self.ent_pass.bind("<Return>", lambda e: self.handle_login())

    def handle_login(self):
        """
        Xử lý xác thực thông tin đăng nhập từ dịch vụ AuthService và chuyển màn hình nếu thành công.
        """
        result = self.auth_service.authenticate(
            self.current_role,
            self.ent_user.get().strip(),
            self.ent_pass.get().strip(),
        )

        if result.success:
            messagebox.showinfo("Thành công", result.message)
            self.redirect_to_interface(result.username)
            return

        notifier = messagebox.showwarning if result.level == "warning" else messagebox.showerror
        notifier("Lỗi", result.message)

    def redirect_to_interface(self, username):
        """
        Khởi tạo giao diện làm việc chính tương ứng với quyền của người dùng vừa đăng nhập thành công.
        """
        self.main_frame.destroy()
        self.root.geometry(WORKSPACE_WINDOW_SIZE)
        self.root.resizable(True, True)

        if self.current_role == "admin":
            admin_info = self.ds.find_admin(username)
            if admin_info:
                fullname = admin_info["fullname"]
            else:
                fullname = username
            admin_data = {
                "username": username,
                "name": fullname,
                "id": f"KH_{username}",
            }
            _ = admin_data
            hien_thi_admin(self.root)

        elif self.current_role == "guide":
            hdv_info = self.ds.find_hdv(username)
            user_data = {
                "maHDV": username,
                "tenHDV": hdv_info["tenHDV"] if hdv_info else "Hướng Dẫn Viên",
            }
            hien_thi_guide(self.root, user_data)

        elif self.current_role == "user":
            user_info = self.ds.find_user(username)
            user_data = {
                "username": username,
                "name": user_info["fullname"] if user_info else username,
                "id": f"KH_{username}",
            }
            hien_thi_khach(self.root, user_data)

    def show_register_screen(self):
        """
        Hiển thị form đăng ký tài khoản mới cho Khách hàng.
        """
        self.clear_screen()
        self.root.geometry(LOGIN_WINDOW_SIZE)
        self.set_background()

        card = self.make_center_card(width=420)

        tk.Label(
            card,
            text="ĐĂNG KÝ TÀI KHOẢN",
            font=("Times New Roman", 22, "bold"),
            bg=PASTEL["surface"],
            fg=PASTEL["success"],
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            card,
            text="Tạo tài khoản khách hàng mới",
            font=("Times New Roman", 11, "italic"),
            bg=PASTEL["surface"],
            fg=PASTEL["muted"],
        ).pack(anchor="w", pady=(0, 18))

        fields = [
            ("Tên đăng nhập", "user", None),
            ("Mật khẩu", "pass", "*"),
            ("Họ và tên", "name", None),
            ("Số điện thoại", "phone", None),
        ]

        self.reg_widgets = {}
        phone_validator = self.root.register(lambda value: (value.isdigit() and len(value) <= 10) or value == "")
        for label_text, key, show_char in fields:
            row = tk.Frame(card, bg=PASTEL["surface"])
            row.pack(fill="x", pady=(0, 10))

            tk.Label(
                row,
                text=label_text,
                font=("Times New Roman", 11, "bold"),
                bg=PASTEL["surface"],
                fg=PASTEL["text"],
            ).pack(anchor="w")

            entry = self.make_entry(row, show=show_char)
            entry.pack(fill="x", pady=(5, 0), ipady=6)
            if key == "phone":
                entry.configure(validate="key", validatecommand=(phone_validator, "%P"))
            self.reg_widgets[key] = entry

        tk.Label(
            card,
            text="SĐT phải có 10 số, bắt đầu bằng 0 và dùng đầu số di động Việt Nam hợp lệ.",
            font=("Times New Roman", 10, "italic"),
            bg=PASTEL["surface"],
            fg=PASTEL["muted"],
            justify="left",
            wraplength=320,
        ).pack(anchor="w", pady=(0, 12))

        def perform_register():
            result = self.auth_service.register_user(
                self.reg_widgets["user"].get().strip(),
                self.reg_widgets["pass"].get().strip(),
                self.reg_widgets["name"].get().strip(),
                self.reg_widgets["phone"].get().strip(),
            )

            if result.success:
                messagebox.showinfo("Thành công", result.message)
                self.show_login_screen("user")
                return

            notifier = messagebox.showwarning if result.level == "warning" else messagebox.showerror
            notifier("Lỗi", result.message)

        self.make_soft_button(
            card,
            text="ĐĂNG KÝ NGAY",
            bg=PASTEL["success"],
            hover_bg=PASTEL["success_hover"],
            command=perform_register,
            width=22,
        ).pack(pady=(14, 10))

        tk.Button(
            card,
            text="← Quay lại",
            font=("Times New Roman", 11),
            fg=PASTEL["muted"],
            bg=PASTEL["surface"],
            bd=0,
            cursor="hand2",
            activebackground=PASTEL["surface"],
            activeforeground=PASTEL["text"],
            command=lambda: self.show_login_screen("user"),
        ).pack()

        self.reg_widgets["phone"].bind("<Return>", lambda e: perform_register())
        self.reg_widgets["user"].focus_set()


def main():
    """
    Hàm khởi tạo ứng dụng và chạy vòng lặp giao diện chính mainloop.
    """
    enable_tk_text_autofix()
    root = tk.Tk()
    TravelSystem(root)
    root.mainloop()


if __name__ == "__main__":
    main()

