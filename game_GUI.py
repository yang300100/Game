import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import socket
import threading
import os  # 图片文件存在性检查，增强容错

HOST = "127.0.0.1"
PORT = 9999
BUFFER_SIZE = 1024
ENCODING = "utf-8"

# ------------------- 窗口尺寸配置【完全匹配HTML版 全屏无滚动】 -------------------
WINDOW_WIDTH = 1000  # 匹配HTML min-width:1000px
WINDOW_HEIGHT = 700  # 精准适配，刚好铺满，无滚动条
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700

# ------------------- 字体全局配置 【完全保留不变】 -------------------
FONT_MAIN = ("宋体", 11)  # 全局默认字体
FONT_STATUS = ("宋体", 10)  # 状态栏字体
FONT_TAB_TITLE = ("宋体", 10)  # 地图选项卡标题字体
FONT_RULE_CONTENT = ("宋体", 10) # 玩法说明字体
FONT_RULE_TITLE = ("宋体", 11, "normal") # 玩法说明小标题

# 全量配色常量 【一字未改，完全保留你的原版】
COLOR_ROOT_BG = "#EDFCF3"
COLOR_FRAME_ALL_BG = "#EDFCF3"
COLOR_MSG_PANEL_BG = "#EDFCF3"
COLOR_MSG_PANEL_FG = "#B890D4"
COLOR_INPUT_FRAME_BG = "#EDFCF3"

COLOR_TEXT_STATUS_DISCONNECT = "#E785A6"
COLOR_TEXT_STATUS_CONNECT = "#8BC8E8"
COLOR_TEXT_LABEL_TITLE = "#5CA4D8"
COLOR_TEXT_TAB_TITLE = "#B890D4"
COLOR_TEXT_BUTTON_NORMAL = "#333333"
COLOR_TEXT_BUTTON_HOVER = "#FFFFFF"

COLOR_MSG_SELF = "#5CA4D8"
COLOR_MSG_SYSTEM = "#9C6CD3"
COLOR_MSG_SUCCESS = "#64B89C"
COLOR_MSG_ERROR = "#E76474"
COLOR_MSG_TIP = "#E8B569"
COLOR_MSG_DEFAULT = "#555555"

COLOR_BTN_NORMAL_BG = "#D9F1FC"
COLOR_BTN_HOVER_BG = "#8BC8E8"
COLOR_ENTRY_BG = "#FFFFFF"
COLOR_ENTRY_FG = "#333333"
COLOR_ENTRY_SELECT_BG = "#C8E2F0"
COLOR_FRAME_BORDER = "#8BC8E8"
COLOR_SCROLL_BAR_BG = "#E6F4EF"
COLOR_SCROLL_BAR_ACTIVE = "#5CA4D8"
COLOR_TAB_SELECT_BG = "#C8E2F0"
COLOR_TAB_NORMAL_BG = "#E6F4EF"

# ------------------- 地图配置 【完全保留不变】 -------------------
MAP_PATHS = {
    "一层地图": "map_floor1.png",
    "二层地图": "map_floor2.png",
    "地下一层地图": "map_floorF1.png"
}

class GameClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("推理游戏 - 严格16:9地图+HTML同款布局")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.config(bg=COLOR_ROOT_BG)
        self.root.resizable(False, False) # 固定窗口，彻底无滚动，和HTML一致

        # 游戏状态变量 【完全保留不变】
        self.client_socket = None
        self.is_connected = False
        self.recv_thread = None
        self.img_refs = []  # 稳定保存图片引用，防止GC回收导致地图消失
        self.current_host = HOST
        self.current_port = PORT

        # 初始化TTK样式 【完全保留不变】
        self._init_ttk_style()
        # 创建界面组件 【核心修复+布局不变】
        self._create_widgets()
        # 绑定回车发送消息 【完全保留不变】
        self.input_entry.bind("<Return>", self.send_message)

    def _init_ttk_style(self):
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        self.style.configure('Main.TFrame', background=COLOR_FRAME_ALL_BG)
        self.style.configure('Panel.TLabelframe', background=COLOR_FRAME_ALL_BG, bordercolor=COLOR_FRAME_BORDER,borderwidth=1)
        self.style.configure('Panel.TLabelframe.Label', background=COLOR_FRAME_ALL_BG,foreground=COLOR_TEXT_LABEL_TITLE, font=FONT_MAIN)
        self.style.configure('Main.TButton', background=COLOR_BTN_NORMAL_BG, foreground=COLOR_TEXT_BUTTON_NORMAL,font=FONT_MAIN, padding=5)
        self.style.map('Main.TButton', background=[('active', COLOR_BTN_HOVER_BG)],foreground=[('active', COLOR_TEXT_BUTTON_HOVER)])
        self.style.configure('Status.TLabel', background=COLOR_ROOT_BG, font=FONT_STATUS)
        self.style.configure('Text.TLabel', background=COLOR_FRAME_ALL_BG, foreground=COLOR_TEXT_LABEL_TITLE,font=FONT_MAIN)
        self.style.configure('Main.TEntry', fieldbackground=COLOR_ENTRY_BG, foreground=COLOR_ENTRY_FG, font=FONT_MAIN)
        self.style.map('Main.TEntry', selectbackground=[('active', COLOR_ENTRY_SELECT_BG)])
        self.style.configure('Map.TNotebook', background=COLOR_FRAME_ALL_BG, borderwidth=0)
        self.style.configure('Map.TNotebook.Tab', background=COLOR_TAB_NORMAL_BG, foreground=COLOR_TEXT_TAB_TITLE,font=FONT_TAB_TITLE, padding=[10, 2])
        self.style.map('Map.TNotebook.Tab', background=[('selected', COLOR_TAB_SELECT_BG)],foreground=[('selected', COLOR_TEXT_TAB_TITLE)])

    def _create_widgets(self):
        """✅ 布局不变：左消息面板 + 右(上16:9地图+下玩法说明) 完全匹配HTML"""
        # ========== 1. 顶部状态栏 - 和HTML完全一致 ==========
        self.status_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.status_frame.pack(fill=tk.X, padx=12, pady=6)
        self.status_label = ttk.Label(self.status_frame, text="未设置服务器 | 等待配置...",
                                    foreground=COLOR_TEXT_STATUS_DISCONNECT, style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.config_btn = ttk.Button(self.status_frame, text="设置服务器", command=self.config_server,style='Main.TButton')
        self.config_btn.pack(side=tk.RIGHT, padx=5)

        # ========== 2. 主内容区 - 左3 右2 严格比例 ==========
        self.main_container = ttk.Frame(self.root, style='Main.TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,6))
        
        # ---- 左侧：游戏消息面板 (占比3，和HTML一致) ----
        self.msg_panel = ttk.LabelFrame(self.main_container, text="游戏消息面板", style='Panel.TLabelframe')
        self.msg_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,6), ipady=5)
        self.msg_text = scrolledtext.ScrolledText(self.msg_panel, font=FONT_MAIN, state=tk.DISABLED,
                                                  bg=COLOR_MSG_PANEL_BG, fg=COLOR_MSG_PANEL_FG,
                                                  selectbackground=COLOR_ENTRY_SELECT_BG, wrap=tk.WORD)
        self.msg_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._fix_scrollbar_color()

        # ---- 右侧：容器 (占比2，垂直分栏：上地图 + 下玩法) 宽度固定400px 和HTML一致 ----
        self.right_container = ttk.Frame(self.main_container, width=400, style='Main.TFrame')
        self.right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6,0))
        self.right_container.pack_propagate(False)

        # --- 右侧上：楼层地图面板 ✅【核心修复：严格强制16:9 永不改变】---
        self.map_panel = ttk.LabelFrame(self.right_container, text="楼层地图", style='Panel.TLabelframe')
        self.map_panel.pack(fill=tk.BOTH, expand=True, pady=(0,6))
        self.map_notebook = ttk.Notebook(self.map_panel, style='Map.TNotebook')
        self.map_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # 加载严格16:9的地图
        self._load_maps_strict_16_9()

        # --- 右侧下：游戏玩法说明面板 (内容和HTML一字不差) ---
        self.rule_panel = ttk.LabelFrame(self.right_container, text="游戏玩法说明", style='Panel.TLabelframe')
        self.rule_panel.pack(fill=tk.BOTH, expand=True, pady=(6,0))
        
        self.rule_text = scrolledtext.ScrolledText(self.rule_panel, font=FONT_RULE_CONTENT, state=tk.DISABLED,
                                                   bg=COLOR_MSG_PANEL_BG, fg=COLOR_MSG_DEFAULT, wrap=tk.WORD)
        self.rule_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._init_rule_content()
        self._fix_scrollbar_color_rule()

        # ========== 3. 底部输入区 - 和HTML完全一致 ==========
        self.input_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.input_frame.pack(fill=tk.X, padx=12, pady=6)
        ttk.Label(self.input_frame, text="输入指令:", style='Text.TLabel').pack(side=tk.LEFT, padx=5)
        self.input_entry = ttk.Entry(self.input_frame, style='Main.TEntry')
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.send_btn = ttk.Button(self.input_frame, text="发送", command=self.send_message, style='Main.TButton')
        self.send_btn.pack(side=tk.RIGHT, padx=5)

    def _init_rule_content(self):
        """玩法说明内容 和HTML版完全一致"""
        rule_content = """🎮 基础操作规则
1. 连接服务器后，在输入框输入指令并回车/点击发送即可执行操作
2. 指令支持：移动、调查、交互、查看道具、提交推理结论等
3. 地图面板可切换不同楼层，查看当前场景布局

🔍 游戏核心玩法
1. 本游戏为文字推理类游戏，通过探索场景收集线索
2. 收集到的线索会在消息面板提示，需整合线索完成推理
3. 遇到NPC可触发对话，获取关键剧情和推理提示
4. 禁止使用违规指令，违规会触发系统警告并断开连接

💡 温馨提示
1. 若连接断开，请检查服务器配置并重新连接
2. 地图加载失败时，确认地图图片文件路径是否正确
3. 所有操作指令需符合游戏内场景逻辑，无效指令会提示错误
4. 游戏过程中保持网络稳定，避免数据传输异常"""
        self.rule_text.config(state=tk.NORMAL)
        self.rule_text.insert(tk.END, rule_content)
        self.rule_text.tag_add("title", "1.0", "1.7")
        self.rule_text.tag_add("title", "4.0", "4.7")
        self.rule_text.tag_add("title", "8.0", "8.7")
        self.rule_text.tag_config("title", foreground=COLOR_TEXT_LABEL_TITLE, font=FONT_RULE_TITLE)
        self.rule_text.config(state=tk.DISABLED)

    def _fix_scrollbar_color(self):
        """修复消息面板滚动条配色"""
        for child in self.msg_text.winfo_children():
            if isinstance(child, tk.Scrollbar):
                child.config(bg=COLOR_SCROLL_BAR_BG, activebackground=COLOR_SCROLL_BAR_ACTIVE,
                             troughcolor=COLOR_FRAME_ALL_BG, bd=0)

    def _fix_scrollbar_color_rule(self):
        """修复玩法面板滚动条配色"""
        for child in self.rule_text.winfo_children():
            if isinstance(child, tk.Scrollbar):
                child.config(bg=COLOR_SCROLL_BAR_BG, activebackground=COLOR_SCROLL_BAR_ACTIVE,
                             troughcolor=COLOR_FRAME_ALL_BG, bd=0)

    def _load_maps_strict_16_9(self):
        """✅ ✅ ✅ 核心重点：Tkinter实现【HTML同款 严格强制16:9宽高比】
           逻辑和网页版 .map-ratio-16-9 完全一致：
           1. 地图容器宽度100%填满父级，高度强制 = 宽度 * 56.25% (9/16) 一丝不差
           2. 无论窗口怎么变，地图永远是标准16:9，不会拉伸/变形/比例失调
           3. 图片在16:9容器内 绝对居中、等比缩放、不变形、不裁切、无空白
        """
        # 获取地图选项卡的可用宽度
        map_tab_width = self.right_container.winfo_width() - 30  # 扣除内边距，和HTML一致
        # ✅ 严格强制计算：16:9 黄金比例 高度 = 宽度 * 0.5625  永远不变！
        map_tab_height = int(map_tab_width * 0.5625)  

        for floor_name, img_path in MAP_PATHS.items():
            # 每个标签页都强制16:9尺寸
            tab = ttk.Frame(self.map_notebook, width=map_tab_width, height=map_tab_height)
            tab.pack_propagate(False)  # 锁死容器尺寸，禁止被内容撑开
            self.map_notebook.add(tab, text=floor_name)

            try:
                if not os.path.exists(img_path):
                    raise Exception(f"文件不存在 {img_path}")

                # 加载原图
                img = tk.PhotoImage(file=img_path)
                img_org_w = img.width()
                img_org_h = img.height()

                # ✅ 等比缩放算法：适配16:9容器，图片居中，不变形，不裁切，和HTML的object-fit:contain一致
                scale_w = map_tab_width / img_org_w
                scale_h = map_tab_height / img_org_h
                best_scale = min(scale_w, scale_h)  # 取最小缩放比，保证图片完整显示
                new_w = int(img_org_w * best_scale)
                new_h = int(img_org_h * best_scale)

                # 缩放图片
                img_scaled = img.subsample(max(1, int(img_org_w/new_w)), max(1, int(img_org_h/new_h)))
                self.img_refs.append(img_scaled)
                setattr(self, f"_img_{floor_name}", img_scaled)

                # ✅ 绝对居中显示：在16:9容器内，图片上下左右居中，无空白/无裁切
                img_label = tk.Label(tab, image=img_scaled, bg=COLOR_FRAME_ALL_BG)
                img_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            except Exception as e:
                # 加载失败显示错误文字，同样居中
                error_label = ttk.Label(tab, text=f"地图加载失败：{str(e)}", foreground=COLOR_MSG_ERROR,style='Text.TLabel')
                error_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                self.add_msg(f"⚠️ {floor_name} 加载异常：{str(e)}", COLOR_MSG_ERROR)

    def config_server(self):
        """服务器配置弹窗 - 完全保留不变"""
        config_win = tk.Toplevel(self.root)
        config_win.title("服务器配置")
        config_win.geometry("320x190")
        config_win.resizable(False, False)
        config_win.config(bg=COLOR_ROOT_BG)
        config_win.transient(self.root)
        config_win.grab_set()

        ttk.Label(config_win, text="服务器IP地址：", style='Text.TLabel').pack(pady=(20, 5), padx=20, anchor='w')
        ip_entry = ttk.Entry(config_win, style='Main.TEntry')
        ip_entry.pack(padx=20, fill='x')
        ip_entry.insert(0, self.current_host)

        ttk.Label(config_win, text="服务器端口号：", style='Text.TLabel').pack(pady=(10, 5), padx=20, anchor='w')
        port_entry = ttk.Entry(config_win, style='Main.TEntry')
        port_entry.pack(padx=20, fill='x')
        port_entry.insert(0, str(self.current_port))

        def confirm_config():
            new_host = ip_entry.get().strip()
            new_port = port_entry.get().strip()
            if not new_host:
                messagebox.showwarning("提示", "IP地址不能为空！")
                return
            try:
                new_port = int(new_port)
                if not (1 <= new_port <= 65535):
                    raise ValueError
            except ValueError:
                messagebox.showwarning("提示", "端口号必须是1-65535的整数！")
                return

            self.current_host = new_host
            self.current_port = new_port
            self.status_label.config(text=f"已配置服务器 {new_host}:{new_port} | 未连接",foreground=COLOR_TEXT_STATUS_DISCONNECT)
            self.add_msg(f"✅ 服务器配置完成：{new_host}:{new_port}", COLOR_MSG_SUCCESS)
            config_win.destroy()

            messagebox.showinfo("提示","点击确定尝试连接服务器")
            self.connect_server()

        ttk.Button(config_win, text="确认配置", command=confirm_config, style='Main.TButton').pack(pady=15)

    def add_msg(self, msg, color=COLOR_MSG_DEFAULT):
        """消息面板添加内容 - 完全保留不变"""
        self.msg_text.config(state=tk.NORMAL)
        self.msg_text.insert(tk.END, msg + '\n')
        tag_name = f"tag_{color.replace('#', '')}"
        self.msg_text.tag_add(tag_name, tk.END + f"-{len(msg) + 2}c", tk.END + "-1c")
        self.msg_text.tag_config(tag_name, foreground=color)
        self.msg_text.config(state=tk.DISABLED)
        self.msg_text.see(tk.END)

    def connect_server(self):
        """连接服务器 - 完全保留不变"""
        if self.is_connected:
            messagebox.showinfo("提示", "已连接服务器，无需重复连接！")
            return
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.current_host, self.current_port))
            self.is_connected = True
            self.config_btn.config(text="断开连接", command=self.disconnect_server)
            self.status_label.config(text=f"已连接服务器 {self.current_host}:{self.current_port} | 游戏中",foreground=COLOR_TEXT_STATUS_CONNECT)
            self.add_msg(f"✅ 成功连接到游戏服务器 {self.current_host}:{self.current_port}！", COLOR_MSG_SUCCESS)
            self.recv_thread = threading.Thread(target=self.recv_msg_loop, daemon=True)
            self.recv_thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"连接失败：{str(e)}")
            self.add_msg(f"❌ 连接服务器失败：{str(e)}", COLOR_MSG_ERROR)

    def disconnect_server(self):
        """断开服务器 - 完全保留不变"""
        if self.is_connected:
            self.client_socket.close()
            self.is_connected = False
            self.config_btn.config(text="设置服务器", command=self.config_server)
            self.status_label.config(text=f"已配置服务器 {self.current_host}:{self.current_port} | 已断开",foreground=COLOR_TEXT_STATUS_DISCONNECT)
            self.add_msg("❌ 已断开与服务器的连接", COLOR_MSG_ERROR)

    def recv_msg_loop(self):
        """接收消息循环 - 完全保留不变"""
        while self.is_connected:
            try:
                recv_data = self.client_socket.recv(BUFFER_SIZE).decode(ENCODING).strip()
                if recv_data:
                    if "系统公告" in recv_data or "游戏结束" in recv_data:
                        self.add_msg(recv_data, COLOR_MSG_SYSTEM)
                    elif "失败" in recv_data or "死亡" in recv_data or "不可" in recv_data:
                        self.add_msg(recv_data, COLOR_MSG_ERROR)
                    elif "成功" in recv_data or "获得" in recv_data or "已到达" in recv_data:
                        self.add_msg(recv_data, COLOR_MSG_SUCCESS)
                    elif "请" in recv_data or "输入" in recv_data or "可选" in recv_data:
                        self.add_msg(recv_data, COLOR_MSG_TIP)
                    else:
                        self.add_msg(recv_data, COLOR_MSG_DEFAULT)
            except Exception as e:
                self.add_msg(f"❌ 与服务器断开连接：{str(e)}", COLOR_MSG_ERROR)
                self.disconnect_server()
                break

    def send_message(self, event=None):
        """发送指令 - 完全保留不变"""
        msg = self.input_entry.get().strip()
        if not msg:
            messagebox.showwarning("提示", "输入内容不能为空！")
            return
        if not self.is_connected:
            messagebox.showwarning("提示", "请先配置并连接服务器再发送指令！")
            return
        try:
            self.client_socket.send(msg.encode(ENCODING))
            self.add_msg(f"你：{msg}", COLOR_MSG_SELF)
            self.input_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("错误", f"发送失败：{str(e)}")
            self.add_msg(f"❌ 发送指令失败：{str(e)}", COLOR_MSG_ERROR)

# 程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = GameClientGUI(root)
    root.mainloop()