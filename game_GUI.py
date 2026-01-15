import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import socket
import threading
import os  # 图片文件存在性检查，增强容错

# =====================================================
# ================= 【全局配色/尺寸配置区 - 只改这里即可】 =================
# =====================================================
# ------------------- 网络配置项（默认值，可通过设置服务器弹窗修改） -------------------
HOST = "127.0.0.1"
PORT = 9999
BUFFER_SIZE = 1024
ENCODING = "utf-8"

# ------------------- 窗口尺寸配置 -------------------
WINDOW_WIDTH = 823  # 窗口总宽度
WINDOW_HEIGHT = 600  # 窗口总高度
MAP_AREA_WIDTH = 820  # 侧边地图区域的宽度【改这个值自定义地图大小】
MAP_AREA_HEIGHT = WINDOW_HEIGHT - 80  # 地图高度适配窗口，无需修改

# ------------------- 字体全局配置 -------------------
FONT_MAIN = ("宋体", 11)  # 全局默认字体（输入框、消息面板、按钮、标签）
FONT_STATUS = ("宋体", 10)  # 状态栏字体
FONT_TAB_TITLE = ("宋体", 10)  # 地图选项卡标题字体

# 1. 基础背景色系列
# 1. 基础背景色系列 (主色调：图片清新浅薄荷柔绿，柔和护眼，全局统一无割裂感)
COLOR_ROOT_BG = "#EDFCF3"  # 软件主窗口背景色
COLOR_FRAME_ALL_BG = "#EDFCF3"  # 所有框架/面板统一背景色
COLOR_MSG_PANEL_BG = "#EDFCF3"  # 游戏消息面板背景色
COLOR_MSG_PANEL_FG = "#B890D4"  # 消息面板默认字体颜色（柔和紫，不刺眼+高可读性）
COLOR_INPUT_FRAME_BG = "#EDFCF3"  # 输入框区域背景色

# 2. 文字颜色系列 (区分度清晰，状态一眼识别，深浅配比符合阅读习惯)
COLOR_TEXT_STATUS_DISCONNECT = "#E785A6"  # 状态栏-未连接/断开 文字色（柔粉，醒目不刺眼）
COLOR_TEXT_STATUS_CONNECT = "#8BC8E8"  # 状态栏-已连接 文字色（清浅蓝，舒适柔和）
COLOR_TEXT_LABEL_TITLE = "#5CA4D8"  # 输入指令/面板标题 文字色（深一点的清蓝，标题突出）
COLOR_TEXT_TAB_TITLE = "#B890D4"  # 地图选项卡标题文字色（柔紫，和面板呼应）
COLOR_TEXT_BUTTON_NORMAL = "#333333"  # 按钮默认文字颜色（深灰黑，比纯黑柔和，可读性拉满）
COLOR_TEXT_BUTTON_HOVER = "#FFFFFF"  # 按钮鼠标悬浮文字颜色（纯白，深色按钮上绝对清晰）

# 3. 消息面板-分级消息配色 (重中之重，✅最高优先级可读性+辨识度)
# 5类消息色彩区分明显，一眼能分辨类型，饱和度适中不刺眼，长时间阅读不累眼
COLOR_MSG_SELF = "#5CA4D8"  # 自己发送的指令-清透蓝 (突出自己消息，柔和不跳脱)
COLOR_MSG_SYSTEM = "#9C6CD3"  # 系统公告/游戏结束-柔紫 (系统类特殊消息，醒目区分)
COLOR_MSG_SUCCESS = "#64B89C"  # 成功/获得/到达-柔绿 (积极反馈色，温和舒适)
COLOR_MSG_ERROR = "#E76474"  # 失败/死亡/错误/警告-柔红 (警示色，醒目不刺眼)
COLOR_MSG_TIP = "#E8B569"  # 操作提示/可选指令-柔橙 (提示色，友好引导，辨识度高)
COLOR_MSG_DEFAULT = "#555555"  # 普通消息-中灰色 (比深灰浅，浅背景上阅读0压力)

# 4. 控件主题配色 (控件交互清晰，悬浮/选中状态一眼识别，同色系协调不突兀)
COLOR_BTN_NORMAL_BG = "#D9F1FC"  # 按钮默认背景色（清浅冰蓝，和主背景区分明显）
COLOR_BTN_HOVER_BG = "#8BC8E8"  # 按钮鼠标悬浮背景色（加深清蓝，悬浮状态清晰，无断层）
COLOR_ENTRY_BG = "#EDFCF3"  # 输入框背景色（纯白，输入文字最清晰，和主背景柔和过渡）
COLOR_ENTRY_FG = "#333333"  # 输入框文字色（深灰黑，纯白框上阅读极致舒适）
COLOR_ENTRY_SELECT_BG = "#C8E2F0"  # 输入框选中文本背景色（浅蓝底，选中文本无遮挡，清晰可见）
COLOR_FRAME_BORDER = "#8BC8E8"  # 所有面板边框色（清蓝边，边框柔和不抢视觉焦点）
COLOR_SCROLL_BAR_BG = "#E6F4EF"  # 滚动条背景色（浅薄荷灰，和主背景统一）
COLOR_SCROLL_BAR_ACTIVE = "#5CA4D8"  # 滚动条拖动/选中色（清透蓝，拖动状态清晰）
COLOR_TAB_SELECT_BG = "#C8E2F0"  # 地图选项卡选中背景色（浅蓝底，选中状态一目了然）
COLOR_TAB_NORMAL_BG = "#E6F4EF"  # 地图选项卡未选中背景色（浅薄荷灰，和选中态区分明显）

# ------------------- 地图配置 -------------------
MAP_PATHS = {
    "一层地图": "map_floor1.png",
    "二层地图": "map_floor2.png",
    "地下一层地图": "map_floorF1.png"
}


# =====================================================
# ================= 业务代码开始（修改处均有标注，其余无需修改） =================
# =====================================================
class GameClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("推理游戏")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.config(bg=COLOR_ROOT_BG)

        # 游戏状态变量
        self.client_socket = None
        self.is_connected = False
        self.recv_thread = None
        self.map_visible = False
        self.img_refs = []  # 新增：稳定保存图片引用，防止GC回收导致地图消失

        # ========== 新增变量：缓存当前的IP和端口（核心修改1） ==========
        self.current_host = HOST
        self.current_port = PORT

        # 布局关键变量
        self.main_area_width = WINDOW_WIDTH - 20
        self.msg_frame_original_width = self.main_area_width

        # 初始化TTK样式 (核心修复：不影响原生tk组件，只美化ttk控件)
        self._init_ttk_style()
        # 创建界面组件
        self._create_widgets()
        # 绑定回车发送消息
        self.input_entry.bind("<Return>", self.send_message)

    def _init_ttk_style(self):
        """✅ 修复TTK样式 - 只美化ttk控件，完全不干扰原生tk组件(地图/消息面板)"""
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')  # 兼容所有颜色修改的主题

        # 1. 所有ttk框架样式
        self.style.configure('Main.TFrame', background=COLOR_FRAME_ALL_BG)
        # 2. 带标题的面板 (消息/地图)
        self.style.configure('Panel.TLabelframe', background=COLOR_FRAME_ALL_BG, bordercolor=COLOR_FRAME_BORDER,
                             borderwidth=2)
        self.style.configure('Panel.TLabelframe.Label', background=COLOR_FRAME_ALL_BG,
                             foreground=COLOR_TEXT_LABEL_TITLE, font=FONT_MAIN)
        # 3. 按钮样式 - 悬浮变色
        self.style.configure('Main.TButton', background=COLOR_BTN_NORMAL_BG, foreground=COLOR_TEXT_BUTTON_NORMAL,
                             font=FONT_MAIN, padding=5)
        self.style.map('Main.TButton', background=[('active', COLOR_BTN_HOVER_BG)],
                       foreground=[('active', COLOR_TEXT_BUTTON_HOVER)])
        # 4. 状态栏标签样式
        self.style.configure('Status.TLabel', background=COLOR_ROOT_BG, font=FONT_STATUS)
        # 5. 普通文字标签样式
        self.style.configure('Text.TLabel', background=COLOR_FRAME_ALL_BG, foreground=COLOR_TEXT_LABEL_TITLE,
                             font=FONT_MAIN)
        # 6. 输入框样式
        self.style.configure('Main.TEntry', fieldbackground=COLOR_ENTRY_BG, foreground=COLOR_ENTRY_FG, font=FONT_MAIN)
        self.style.map('Main.TEntry', selectbackground=[('active', COLOR_ENTRY_SELECT_BG)])
        # 7. 地图选项卡样式
        self.style.configure('Map.TNotebook', background=COLOR_FRAME_ALL_BG, borderwidth=0)
        self.style.configure('Map.TNotebook.Tab', background=COLOR_TAB_NORMAL_BG, foreground=COLOR_TEXT_TAB_TITLE,
                             font=FONT_TAB_TITLE, padding=[10, 2])
        self.style.map('Map.TNotebook.Tab', background=[('selected', COLOR_TAB_SELECT_BG)],
                       foreground=[('selected', COLOR_TEXT_TAB_TITLE)])

    def _create_widgets(self):
        """✅ 修复所有组件渲染 - 消息面板恢复+地图恢复"""
        # 顶部状态栏
        self.status_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        self.status_label = ttk.Label(self.status_frame, text="未设置服务器 | 等待配置...",
                                      foreground=COLOR_TEXT_STATUS_DISCONNECT, style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT)

        # ========== 修改按钮：连接服务器 → 设置服务器（核心修改2） ==========
        self.config_btn = ttk.Button(self.status_frame, text="设置服务器", command=self.config_server,
                                     style='Main.TButton')
        self.config_btn.pack(side=tk.RIGHT, padx=5)
        self.map_btn = ttk.Button(self.status_frame, text="显示地图", command=self.toggle_map, style='Main.TButton')
        self.map_btn.pack(side=tk.RIGHT)

        # 主内容区
        self.main_frame = ttk.Frame(self.root, width=self.main_area_width, height=WINDOW_HEIGHT - 110,
                                    style='Main.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.main_frame.pack_propagate(False)

        # ✅ 核心修复：消息面板 完全恢复显示+配色+字体
        self.msg_frame = ttk.LabelFrame(self.main_frame, text="游戏消息面板", width=self.msg_frame_original_width,
                                        height=self.main_frame["height"], style='Panel.TLabelframe')
        self.msg_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        self.msg_frame.pack_propagate(False)
        # 原生tk的ScrolledText，不被ttk样式污染，字体/颜色/背景全生效
        self.msg_text = scrolledtext.ScrolledText(self.msg_frame, font=FONT_MAIN, state=tk.DISABLED,
                                                  bg=COLOR_MSG_PANEL_BG, fg=COLOR_MSG_PANEL_FG,
                                                  selectbackground=COLOR_ENTRY_SELECT_BG, wrap=tk.WORD)
        self.msg_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # 修复滚动条配色
        self._fix_scrollbar_color()

        # ✅ 核心修复：地图面板 保证图片渲染正常
        self.map_frame = ttk.LabelFrame(self.main_frame, text="楼层地图", width=MAP_AREA_WIDTH,
                                        height=MAP_AREA_HEIGHT, style='Panel.TLabelframe')
        self.map_frame.pack_propagate(False)
        self.map_notebook = ttk.Notebook(self.map_frame, style='Map.TNotebook')
        self.map_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 加载地图
        self._load_maps()

        # 输入区
        self.input_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(self.input_frame, text="输入指令:", style='Text.TLabel').pack(side=tk.LEFT)
        self.input_entry = ttk.Entry(self.input_frame, style='Main.TEntry')
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.send_btn = ttk.Button(self.input_frame, text="发送", command=self.send_message, style='Main.TButton')
        self.send_btn.pack(side=tk.RIGHT)

    # ========== 新增核心方法：设置服务器弹窗（核心修改3） ==========
    def config_server(self):
        """弹窗配置服务器IP和端口，带数据校验，配置后可选择立即连接"""
        # 创建顶级弹窗，模态窗口（不关闭弹窗无法操作主界面）
        config_win = tk.Toplevel(self.root)
        config_win.title("服务器配置")
        config_win.geometry("320x190")
        config_win.resizable(False, False)
        config_win.config(bg=COLOR_ROOT_BG)
        config_win.transient(self.root)  # 置顶主窗口
        config_win.grab_set()  # 锁定焦点

        # 弹窗布局
        ttk.Label(config_win, text="服务器IP地址：", style='Text.TLabel').pack(pady=(20, 5), padx=20, anchor='w')
        ip_entry = ttk.Entry(config_win, style='Main.TEntry')
        ip_entry.pack(padx=20, fill='x')
        ip_entry.insert(0, self.current_host)  # 默认填充当前IP

        ttk.Label(config_win, text="服务器端口号：", style='Text.TLabel').pack(pady=(10, 5), padx=20, anchor='w')
        port_entry = ttk.Entry(config_win, style='Main.TEntry')
        port_entry.pack(padx=20, fill='x')
        port_entry.insert(0, str(self.current_port))  # 默认填充当前端口

        # 确认配置按钮事件
        def confirm_config():
            new_host = ip_entry.get().strip()
            new_port = port_entry.get().strip()
            # 数据校验
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

            # 保存配置
            self.current_host = new_host
            self.current_port = new_port
            self.status_label.config(text=f"已配置服务器 {new_host}:{new_port} | 未连接",
                                     foreground=COLOR_TEXT_STATUS_DISCONNECT)
            self.add_msg(f"✅ 服务器配置完成：{new_host}:{new_port}", COLOR_MSG_SUCCESS)
            config_win.destroy()

            messagebox.showinfo("提示","点击确定尝试连接服务器")
            self.connect_server()

        ttk.Button(config_win, text="确认配置", command=confirm_config, style='Main.TButton').pack(pady=15)

    def _fix_scrollbar_color(self):
        """修复滚动条配色 - 不影响消息面板功能"""
        for child in self.msg_text.winfo_children():
            if isinstance(child, tk.Scrollbar):
                child.config(bg=COLOR_SCROLL_BAR_BG, activebackground=COLOR_SCROLL_BAR_ACTIVE,
                             troughcolor=COLOR_FRAME_ALL_BG, bd=0)

    def _load_maps(self):
        """✅ 彻底修复地图显示：100%正常加载+等比例缩放+防GC回收+文件容错"""
        usable_map_w = MAP_AREA_WIDTH - 20
        usable_map_h = MAP_AREA_HEIGHT - 20

        for floor_name, img_path in MAP_PATHS.items():
            tab = ttk.Frame(self.map_notebook, width=usable_map_w, height=usable_map_h, style='Main.TFrame')
            tab.pack_propagate(False)
            self.map_notebook.add(tab, text=floor_name)

            try:
                # 检查图片文件是否存在，增强容错
                if not os.path.exists(img_path):
                    raise Exception(f"文件不存在 {img_path}")

                # 加载图片 - 用原生tk.PhotoImage，不被ttk干扰
                img = tk.PhotoImage(file=img_path)
                img_org_w = img.width()
                img_org_h = img.height()

                # 等比例缩放算法 (原版保留，不变形不裁切)
                scale_ratio_w = usable_map_w / img_org_w
                scale_ratio_h = usable_map_h / img_org_h
                best_scale = min(scale_ratio_w, scale_ratio_h)
                new_w = int(img_org_w * best_scale)
                new_h = int(img_org_h * best_scale)
                scale_x = max(1, int(img_org_w / new_w))
                scale_y = max(1, int(img_org_h / new_h))
                img_scaled = img.subsample(scale_x, scale_y)

                # ✅ 双重防回收：列表保存+实例属性保存，地图永久显示
                self.img_refs.append(img_scaled)
                setattr(self, f"_img_{floor_name}", img_scaled)

                # ✅ 核心修复：用【原生tk.Label】显示图片，ttk.Label会屏蔽图片！！！
                img_label = tk.Label(tab, image=img_scaled, bg=COLOR_FRAME_ALL_BG)
                img_label.pack(fill=tk.BOTH, expand=True)

            except Exception as e:
                # 加载失败显示提示文字
                error_label = ttk.Label(tab, text=f"地图加载失败：{str(e)}", foreground=COLOR_MSG_ERROR,
                                        style='Text.TLabel')
                error_label.pack(fill=tk.BOTH, expand=True)
                self.add_msg(f"⚠️ {floor_name} 加载异常：{str(e)}", COLOR_MSG_ERROR)

    def toggle_map(self):
        """地图显示/隐藏 - 原版布局逻辑，完全保留"""
        if not self.map_visible:
            new_msg_width = self.main_area_width - MAP_AREA_WIDTH - 5
            self.msg_frame.config(width=new_msg_width)
            self.map_frame.pack(side=tk.LEFT, fill=tk.BOTH)
            self.map_btn.config(text="隐藏地图")
            self.map_visible = True
        else:
            self.msg_frame.config(width=self.msg_frame_original_width)
            self.map_frame.pack_forget()
            self.map_btn.config(text="显示地图")
            self.map_visible = False
        self.main_frame.update()

    def add_msg(self, msg, color=COLOR_MSG_DEFAULT):
        """✅ 彻底修复：消息面板字体+颜色全显示，标签100%生效无错位"""
        self.msg_text.config(state=tk.NORMAL)
        # 插入消息内容
        self.msg_text.insert(tk.END, msg + '\n')
        # 配置颜色标签 - 简化写法，百分百兼容生效
        tag_name = f"tag_{color.replace('#', '')}"
        self.msg_text.tag_add(tag_name, tk.END + f"-{len(msg) + 2}c", tk.END + "-1c")
        self.msg_text.tag_config(tag_name, foreground=color)
        # 锁定消息面板+滚动到底部
        self.msg_text.config(state=tk.DISABLED)
        self.msg_text.see(tk.END)

    def connect_server(self):
        """连接服务器 - 原版逻辑修改：使用配置后的IP和端口"""
        if self.is_connected:
            messagebox.showinfo("提示", "已连接服务器，无需重复连接！")
            return
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # ========== 修改：使用缓存的IP和端口连接（核心修改4） ==========
            self.client_socket.connect((self.current_host, self.current_port))
            self.is_connected = True
            # ========== 修改：按钮文本和绑定事件 ==========
            self.config_btn.config(text="断开连接", command=self.disconnect_server)
            self.status_label.config(text=f"已连接服务器 {self.current_host}:{self.current_port} | 游戏中",
                                     foreground=COLOR_TEXT_STATUS_CONNECT)
            self.add_msg(f"✅ 成功连接到游戏服务器 {self.current_host}:{self.current_port}！", COLOR_MSG_SUCCESS)
            self.recv_thread = threading.Thread(target=self.recv_msg_loop, daemon=True)
            self.recv_thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"连接失败：{str(e)}")
            self.add_msg(f"❌ 连接服务器失败：{str(e)}", COLOR_MSG_ERROR)

    def disconnect_server(self):
        """断开连接 - 原版逻辑修改：恢复按钮文本"""
        if self.is_connected:
            self.client_socket.close()
            self.is_connected = False
            # ========== 修改：恢复设置服务器按钮 ==========
            self.config_btn.config(text="设置服务器", command=self.config_server)
            self.status_label.config(text=f"已配置服务器 {self.current_host}:{self.current_port} | 已断开",
                                     foreground=COLOR_TEXT_STATUS_DISCONNECT)
            self.add_msg("❌ 已断开与服务器的连接", COLOR_MSG_ERROR)

    def recv_msg_loop(self):
        """接收服务器消息 - 原版逻辑，无修改"""
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
        """发送指令 - 原版逻辑，无修改"""
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