import pygame
import socket
import threading
import os
import sys

# 初始化 Pygame
pygame.init()
os.environ["SDL_IME_SHOW_UI"] = "1"

# ==================== 配置常量 ====================

# 窗口配置
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700
FPS = 60


# 字体配置
def get_font(size, bold=False):
    """获取中文字体"""
    # 优先使用常见中文字体
    fonts = ["simsun", "simhei", "microsoftyahei", "notosanscjk", "wenquanyimicrohei", "arial"]
    for font_name in fonts:
        try:
            if bold:
                return pygame.font.SysFont(font_name, size, bold=True)
            return pygame.font.SysFont(font_name, size)
        except:
            continue
    return pygame.font.SysFont("arial", size)


FONT_MAIN = lambda: get_font(16)  # 相当于宋体11pt
FONT_STATUS = lambda: get_font(14)  # 状态栏
FONT_TAB_TITLE = lambda: get_font(14)  # 标签标题
FONT_RULE_CONTENT = lambda: get_font(14)  # 玩法说明
FONT_RULE_TITLE = lambda: get_font(16, bold=True)  # 玩法小标题
FONT_BUTTON = lambda: get_font(16)  # 按钮字体
FONT_LIST = lambda: get_font(14)  # 列表字体

# 配色常量（完全匹配原HTML配色）
COLOR_ROOT_BG = (237, 252, 243)  # #EDFCF3
COLOR_FRAME_ALL_BG = (237, 252, 243)  # #EDFCF3
COLOR_MSG_PANEL_BG = (237, 252, 243)  # #EDFCF3
COLOR_MSG_PANEL_FG = (184, 144, 212)  # #B890D4

COLOR_TEXT_STATUS_DISCONNECT = (231, 133, 166)  # #E785A6
COLOR_TEXT_STATUS_CONNECT = (139, 200, 232)  # #8BC8E8
COLOR_TEXT_LABEL_TITLE = (92, 164, 216)  # #5CA4D8
COLOR_TEXT_TAB_TITLE = (184, 144, 212)  # #B890D4
COLOR_TEXT_BUTTON_NORMAL = (51, 51, 51)  # #333333
COLOR_TEXT_BUTTON_HOVER = (255, 255, 255)  # #FFFFFF

COLOR_MSG_SELF = (92, 164, 216)  # #5CA4D8
COLOR_MSG_SYSTEM = (156, 108, 211)  # #9C6CD3
COLOR_MSG_SUCCESS = (100, 184, 156)  # #64B89C
COLOR_MSG_ERROR = (231, 100, 116)  # #E76474
COLOR_MSG_TIP = (232, 181, 105)  # #E8B569
COLOR_MSG_DEFAULT = (85, 85, 85)  # #555555

COLOR_BTN_NORMAL_BG = (217, 241, 252)  # #D9F1FC
COLOR_BTN_HOVER_BG = (139, 200, 232)  # #8BC8E8
COLOR_BTN_ACTIVE_BG = (92, 164, 216)  # #5CA4D8
COLOR_ENTRY_BG = (255, 255, 255)  # #FFFFFF
COLOR_ENTRY_FG = (51, 51, 51)  # #333333
COLOR_ENTRY_SELECT_BG = (200, 226, 240)  # #C8E2F0
COLOR_FRAME_BORDER = (139, 200, 232)  # #8BC8E8
COLOR_SCROLL_BAR_BG = (230, 244, 239)  # #E6F4EF
COLOR_SCROLL_BAR_ACTIVE = (92, 164, 216)  # #5CA4D8
COLOR_TAB_SELECT_BG = (200, 226, 240)  # #C8E2F0
COLOR_TAB_NORMAL_BG = (230, 244, 239)  # #E6F4EF
COLOR_SCROLL_BG = (217, 241, 252)  # 滚动条背景

# 列表组件颜色
COLOR_LIST_BG = (255, 255, 255)  # 列表背景
COLOR_LIST_ITEM_NORMAL = (240, 248, 255)  # 列表项正常
COLOR_LIST_ITEM_HOVER = (220, 240, 255)  # 列表项悬停
COLOR_LIST_ITEM_SELECTED = (180, 220, 255)  # 列表项选中
COLOR_LIST_BORDER = (200, 220, 240)  # 列表边框

# 服务器配置
HOST = "127.0.0.1"
PORT = 9999
BUFFER_SIZE = 4096  # 增大缓冲区
ENCODING = "utf-8"

# 地图配置
MAP_PATHS = {
    "一层地图": "img/map_floor1.png",
    "二层地图": "img/map_floor2.png",
    "地下一层地图": "img/map_floorF1.png"
}


# ==================== UI组件类 ====================

class DropdownList:
    """下拉列表组件 - 支持滚动"""

    def __init__(self, items, width=200, max_visible_items=5, font=None):
        self.items = items  # 列表选项
        self.width = width
        self.max_visible_items = max_visible_items  # 最大可见项数
        self.font = font or FONT_LIST()
        self.item_height = 30

        # 状态
        self.expanded = False
        self.selected_index = 0
        self.hovered_index = -1
        self.scroll_offset = 0  # 滚动偏移

        # 计算尺寸
        self.height = self.item_height  # 收起时高度
        self.expanded_height = min(len(items), max_visible_items) * self.item_height  # 展开时高度

        # 创建表面
        self.rect = pygame.Rect(0, 0, width, self.height)

        # 滚动条
        self.scrollbar_width = 10
        self.scrollbar_dragging = False
        self.scrollbar_hover = False
        self.max_scroll = max(0, len(items) - max_visible_items)

        # 滚动条矩形区域
        self.scrollbar_rect = None
        self.thumb_rect = None

    def set_position(self, x, y):
        """设置列表位置"""
        self.rect.x = x
        self.rect.y = y

    def draw(self, surface):
        """绘制下拉列表"""
        # 绘制主框
        current_height = self.expanded_height if self.expanded else self.height
        list_rect = pygame.Rect(self.rect.x, self.rect.y, self.width, current_height)

        # 背景
        pygame.draw.rect(surface, COLOR_LIST_BG, list_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_LIST_BORDER, list_rect, width=1, border_radius=4)

        if not self.expanded:
            # 收起状态：只显示选中的项
            if self.items and 0 <= self.selected_index < len(self.items):
                item_text = self.items[self.selected_index]
                text_surf = self.font.render(item_text, True, COLOR_ENTRY_FG)
                text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
                surface.blit(text_surf, text_rect)

                # 绘制下拉箭头
                arrow_points = [
                    (self.rect.right - 15, self.rect.centery - 3),
                    (self.rect.right - 10, self.rect.centery + 2),
                    (self.rect.right - 5, self.rect.centery - 3)
                ]
                pygame.draw.polygon(surface, COLOR_ENTRY_FG, arrow_points)
        else:
            # 展开状态：显示可见项
            visible_count = min(len(self.items), self.max_visible_items)

            for i in range(visible_count):
                item_idx = i + self.scroll_offset
                if item_idx >= len(self.items):
                    break

                item = self.items[item_idx]
                item_rect = pygame.Rect(self.rect.x, self.rect.y + i * self.item_height,
                                        self.width, self.item_height)

                # 背景色
                if item_idx == self.selected_index:
                    bg_color = COLOR_LIST_ITEM_SELECTED
                elif item_idx == self.hovered_index:
                    bg_color = COLOR_LIST_ITEM_HOVER
                else:
                    bg_color = COLOR_LIST_ITEM_NORMAL

                pygame.draw.rect(surface, bg_color, item_rect)

                # 分隔线
                if i > 0:
                    pygame.draw.line(surface, COLOR_LIST_BORDER,
                                     (item_rect.left, item_rect.top),
                                     (item_rect.right, item_rect.top), 1)

                # 文字
                text_surf = self.font.render(item, True, COLOR_ENTRY_FG)
                text_rect = text_surf.get_rect(midleft=(item_rect.x + 10, item_rect.centery))
                surface.blit(text_surf, text_rect)

            # 如果需要，绘制滚动条
            if self.max_scroll > 0:
                self._draw_scrollbar(surface, visible_count)

    def _draw_scrollbar(self, surface, visible_count):
        """绘制滚动条"""
        scrollbar_x = self.rect.right - self.scrollbar_width
        scrollbar_rect = pygame.Rect(scrollbar_x, self.rect.y,
                                     self.scrollbar_width, self.expanded_height)

        # 滚动条背景
        pygame.draw.rect(surface, COLOR_SCROLL_BAR_BG, scrollbar_rect)

        # 计算滑块
        total_items = len(self.items)
        ratio = visible_count / total_items
        thumb_height = max(20, int(scrollbar_rect.height * ratio))
        thumb_y = scrollbar_rect.y + (self.scroll_offset / self.max_scroll) * (scrollbar_rect.height - thumb_height)

        thumb_rect = pygame.Rect(scrollbar_x, thumb_y,
                                 self.scrollbar_width, thumb_height)

        # 滑块颜色
        thumb_color = COLOR_SCROLL_BAR_ACTIVE if self.scrollbar_hover else COLOR_FRAME_BORDER
        pygame.draw.rect(surface, thumb_color, thumb_rect, border_radius=3)

        self.scrollbar_rect = scrollbar_rect
        self.thumb_rect = thumb_rect

    def handle_event(self, event, mouse_pos=None):
        """处理事件"""
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.expanded:
                # 收起状态：检查是否点击主框
                if self.rect.collidepoint(mouse_pos):
                    self.expanded = True
                    self.hovered_index = -1
                    return True
            else:
                # 展开状态
                expanded_rect = pygame.Rect(self.rect.x, self.rect.y,
                                            self.width, self.expanded_height)

                # 检查是否点击在展开区域
                if expanded_rect.collidepoint(mouse_pos):
                    # 检查是否点击滚动条
                    if self.thumb_rect and self.thumb_rect.collidepoint(mouse_pos):
                        self.scrollbar_dragging = True
                        return True

                    # 检查是否点击选项
                    for i in range(min(len(self.items), self.max_visible_items)):
                        item_idx = i + self.scroll_offset
                        if item_idx >= len(self.items):
                            break

                        item_rect = pygame.Rect(self.rect.x, self.rect.y + i * self.item_height,
                                                self.width, self.item_height)
                        if item_rect.collidepoint(mouse_pos):
                            self.selected_index = item_idx
                            self.expanded = False
                            return True

                    # 点击其他区域（但不是外部），不收起
                    return True
                else:
                    # 点击外部，收起列表
                    self.expanded = False
                    return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.scrollbar_dragging:
                self.scrollbar_dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.expanded:
                # 更新悬停项
                self.hovered_index = -1
                visible_count = min(len(self.items), self.max_visible_items)

                for i in range(visible_count):
                    item_idx = i + self.scroll_offset
                    if item_idx >= len(self.items):
                        break

                    item_rect = pygame.Rect(self.rect.x, self.rect.y + i * self.item_height,
                                            self.width, self.item_height)
                    if item_rect.collidepoint(mouse_pos):
                        self.hovered_index = item_idx
                        break

                # 处理滚动条悬停
                if self.thumb_rect:
                    self.scrollbar_hover = self.thumb_rect.collidepoint(mouse_pos)

                # 处理滚动条拖动
                if self.scrollbar_dragging and self.scrollbar_rect:
                    relative_y = mouse_pos[1] - self.scrollbar_rect.y
                    ratio = relative_y / self.scrollbar_rect.height
                    new_offset = int(ratio * len(self.items))
                    self.scroll_offset = max(0, min(self.max_scroll, new_offset))

        elif event.type == pygame.MOUSEWHEEL:
            if self.expanded and self.rect.collidepoint(mouse_pos):
                self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - event.y))
                return True

        return False

    def get_selected(self):
        """获取选中的选项"""
        if self.items and 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return ""

    def get_selected_index(self):
        """获取选中的索引"""
        return self.selected_index


class Button:
    """自定义按钮组件"""

    def __init__(self, rect, text, callback, font=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = font or FONT_BUTTON()
        self.hovered = False
        self.pressed = False

    def draw(self, surface):
        # 确定背景色
        if self.pressed:
            bg_color = COLOR_BTN_ACTIVE_BG
            text_color = COLOR_TEXT_BUTTON_HOVER
        elif self.hovered:
            bg_color = COLOR_BTN_HOVER_BG
            text_color = COLOR_TEXT_BUTTON_HOVER
        else:
            bg_color = COLOR_BTN_NORMAL_BG
            text_color = COLOR_TEXT_BUTTON_NORMAL

        # 绘制背景
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=4)
        # 绘制边框
        pygame.draw.rect(surface, COLOR_FRAME_BORDER, self.rect, width=1, border_radius=4)

        # 绘制文字
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.pressed and self.hovered and event.button == 1:
                self.callback()
            self.pressed = False
        return False


class ButtonMessage:
    """消息中的可点击按钮"""

    def __init__(self, text, callback, font=None):
        self.text = text
        self.callback = callback
        self.font = font or FONT_BUTTON()
        self.hovered = False
        self.pressed = False

        # 计算按钮尺寸
        padding_x, padding_y = 10, 5
        text_size = self.font.size(text)
        self.width = text_size[0] + padding_x * 2
        self.height = text_size[1] + padding_y * 2
        self.rect = pygame.Rect(0, 0, self.width, self.height)

    def set_position(self, x, y):
        """设置按钮位置"""
        self.rect.x = x
        self.rect.y = y

    def draw(self, surface):
        # 确定背景色
        if self.pressed:
            bg_color = COLOR_BTN_ACTIVE_BG
            text_color = COLOR_TEXT_BUTTON_HOVER
        elif self.hovered:
            bg_color = COLOR_BTN_HOVER_BG
            text_color = COLOR_TEXT_BUTTON_HOVER
        else:
            bg_color = COLOR_BTN_NORMAL_BG
            text_color = COLOR_TEXT_BUTTON_NORMAL

        # 绘制背景
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=4)
        # 绘制边框
        pygame.draw.rect(surface, COLOR_FRAME_BORDER, self.rect, width=1, border_radius=4)

        # 绘制文字
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        """简化：只在 ScrollText 中直接处理逻辑，这里仅作备用"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        return False  # 事件由 ScrollText 统一处理


class MessageLine:
    """单行消息，可能包含文字和多个按钮 - 支持多行文本"""

    def __init__(self, content, color=COLOR_MSG_DEFAULT, font=None, max_width=None):
        self.font = font or FONT_MAIN()
        self.color = color
        self.buttons = []  # 按钮列表
        self.dropdown = None  # 下拉列表
        self.submit_button = None  # 提交按钮
        self.text_lines = []  # 多行文本
        self.height = self.font.get_height() + 4
        self.max_width = max_width  # 最大宽度（用于自动换行）

        # 解析内容
        self._parse_content(content)

    def _parse_content(self, content):
        """解析内容，提取按钮和普通文字 - 支持多行文本"""
        if isinstance(content, str):
            content = content.strip()  # 去除首尾空白
            if content.startswith("button:"):
                # 按钮消息格式: button:文字1$文字2$文字3
                buttons_text = content[7:].split("$")  # 去掉"button:"
                for btn_text in buttons_text:
                    if btn_text.strip():
                        # 创建按钮，回调函数稍后设置
                        btn = ButtonMessage(btn_text.strip(), None, self.font)
                        self.buttons.append(btn)
                        self.height = max(self.height, btn.height + 4)

            elif content.startswith("list:"):
                # 列表消息格式: list:选项1$选项2$选项3
                list_items = content[5:].split("$")  # 去掉"list:"
                list_items = [item.strip() for item in list_items if item.strip()]

                if list_items:
                    # 创建下拉列表（支持滚动）
                    self.dropdown = DropdownList(list_items, width=200, max_visible_items=5, font=self.font)
                    # 创建提交按钮
                    self.submit_button = ButtonMessage("确认提交", None, self.font)

                    # 计算行高度
                    list_height = self.dropdown.expanded_height + 10
                    btn_height = self.submit_button.height + 10
                    self.height = max(self.height, list_height + btn_height + 10)
            else:
                # 普通文本，处理自动换行
                if self.max_width and self.max_width > 0:
                    self.text_lines = self._wrap_text(content, self.max_width)
                    self.height = len(self.text_lines) * (self.font.get_height() + 4)
                else:
                    self.text_lines = [content]
        else:
            self.text_lines = [str(content)]

    def _wrap_text(self, text, max_width):
        """将文本自动换行到指定宽度"""
        lines = []
        words = text.split()
        current_line = []

        for word in words:
            # 测试添加单词后是否会超出宽度
            test_line = ' '.join(current_line + [word])
            test_width = self.font.size(test_line)[0]

            if test_width > max_width and current_line:
                # 当前行已满，添加当前行
                lines.append(' '.join(current_line))
                current_line = [word]  # 开始新行
            else:
                # 继续添加单词到当前行
                current_line.append(word)

        # 添加最后一行
        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def set_button_callback(self, callback):
        """为所有按钮设置回调"""
        for btn in self.buttons:
            btn.callback = lambda btn_text=btn.text: callback(btn_text)

        if self.submit_button:
            self.submit_button.callback = lambda: callback(self.dropdown.get_selected() if self.dropdown else "")

    def draw(self, surface, x, y, max_width):
        """绘制这一行内容"""
        current_x = x
        current_y = y

        # 首先绘制文本行（可能有多行）
        for text_line in self.text_lines:
            text_surf = self.font.render(text_line, True, self.color)
            surface.blit(text_surf, (current_x, current_y))
            current_y += self.font.get_height() + 4

        # 调整current_y位置，确保按钮在文本下方
        if self.text_lines:
            current_y -= self.font.get_height() + 4  # 回到最后一行文本的位置
            current_y += 5  # 添加一些间距

        if self.buttons:
            # 绘制多个按钮
            spacing = 10  # 按钮间距
            for btn in self.buttons:
                # 检查是否超出边界，如果超出则换行
                if current_x + btn.width > x + max_width:
                    current_x = x
                    current_y += btn.height + 5

                btn.set_position(current_x, current_y + (self.height - btn.height) // 2)
                btn.draw(surface)
                current_x += btn.width + spacing

        elif self.dropdown and self.submit_button:
            # 绘制下拉列表和提交按钮
            list_x = current_x
            list_y = current_y + 5

            # 绘制下拉列表
            self.dropdown.set_position(list_x, list_y)
            self.dropdown.draw(surface)

            # 绘制提交按钮（在下拉列表下方）
            btn_x = list_x
            btn_y = list_y + (self.dropdown.expanded_height if self.dropdown.expanded else self.dropdown.height) + 10
            self.submit_button.set_position(btn_x, btn_y)
            self.submit_button.draw(surface)

    def handle_event(self, event, relative_x, relative_y):
        """处理按钮事件 - 修复坐标计算"""
        if self.buttons:
            for btn in self.buttons:
                # 检查是否点击在这个按钮上
                if (relative_x >= btn.rect.x and relative_x <= btn.rect.x + btn.width and
                        relative_y >= btn.rect.y and relative_y <= btn.rect.y + btn.height):

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn.pressed = True
                        return True
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if btn.pressed and btn.callback:
                            btn.pressed = False
                            btn.callback()
                            return True
                    elif event.type == pygame.MOUSEMOTION:
                        btn.hovered = True
                        return True
                    else:
                        btn.hovered = False
        return False

    def get_buttons(self):
        return self.buttons


class TextInput:
    """文本输入框组件 - 支持中文输入"""

    def __init__(self, rect, font=None):
        self.rect = pygame.Rect(rect)
        self.font = font or FONT_MAIN()
        self.text = ""
        self.active = False
        self.cursor_pos = 0
        self.cursor_timer = 0
        self.show_cursor = True
        self.scroll_x = 0

    def draw(self, surface):
        # 绘制背景
        pygame.draw.rect(surface, COLOR_ENTRY_BG, self.rect, border_radius=3)
        # 绘制边框（激活时高亮）
        border_color = COLOR_FRAME_BORDER if self.active else (200, 200, 200)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=3)

        # 裁剪区域
        clip_rect = pygame.Rect(self.rect.x + 5, self.rect.y, self.rect.width - 10, self.rect.height)
        surface.set_clip(clip_rect)

        # 计算文字位置
        text_x = self.rect.x + 8 - self.scroll_x
        text_y = self.rect.centery - self.font.get_height() // 2

        # 绘制文字
        text_surf = self.font.render(self.text, True, COLOR_ENTRY_FG)
        surface.blit(text_surf, (text_x, text_y))

        # 绘制光标
        if self.active and self.show_cursor:
            cursor_x = text_x + self.font.size(self.text[:self.cursor_pos])[0]
            pygame.draw.line(surface, COLOR_ENTRY_FG,
                             (cursor_x, self.rect.y + 5),
                             (cursor_x, self.rect.y + self.rect.height - 5), 2)

        surface.set_clip(None)

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer > 500:  # 光标闪烁
            self.show_cursor = not self.show_cursor
            self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos)
            # 如果刚激活，启动文本输入
            if self.active and not was_active:
                pygame.key.start_text_input()
                pygame.key.set_text_input_rect(self.rect)
            elif not self.active and was_active:
                pygame.key.stop_text_input()
            return self.active

        if not self.active:
            return False

        # 处理文本输入事件（支持中文）
        if event.type == pygame.TEXTINPUT:
            # 插入文本
            self.text = self.text[:self.cursor_pos] + event.text + self.text[self.cursor_pos:]
            self.cursor_pos += len(event.text)
            self._update_scroll()
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "submit"
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    # 处理UTF-8字符，避免删除半个中文
                    text_before = self.text[:self.cursor_pos]
                    if text_before:
                        # 检查是否是UTF-8多字节字符
                        text_before = text_before[:-1]
                        self.text = text_before + self.text[self.cursor_pos:]
                        self.cursor_pos -= 1
                        self._update_scroll()
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
                    self._update_scroll()
            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
                self._update_scroll()
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                self._update_scroll()
            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0
                self._update_scroll()
            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.text)
                self._update_scroll()
            # 处理Ctrl+A全选（可选）
            elif event.key == pygame.K_a and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.cursor_pos = len(self.text)

        return False

    def _update_scroll(self):
        """更新滚动位置"""
        text_width = self.font.size(self.text[:self.cursor_pos])[0]
        if text_width - self.scroll_x > self.rect.width - 20:
            self.scroll_x = text_width - self.rect.width + 20
        elif text_width < self.scroll_x:
            self.scroll_x = max(0, text_width - 20)

    def get_text(self):
        return self.text

    def clear(self):
        self.text = ""
        self.cursor_pos = 0
        self.scroll_x = 0


class ScrollText:
    """带滚动条的文本显示区域（支持按钮消息和下拉列表）- 支持多行文本"""

    def __init__(self, rect, font=None):
        self.rect = pygame.Rect(rect)
        self.font = font or FONT_MAIN()
        self.lines = []  # [MessageLine, ...]
        self.scroll_y = 0
        self.line_height = self.font.get_height() + 4
        self.max_lines = 1000  # 最大行数限制

        # 滚动条
        self.scrollbar_width = 12
        self.scrollbar_dragging = False
        self.scrollbar_hover = False

        # 内容区域（用于坐标转换）
        self.content_rect = None
        self._last_mouse_pos = (0, 0)

        # 存储活动的下拉列表
        self.active_dropdown = None

    def add_line(self, content, color=COLOR_MSG_DEFAULT, button_callback=None):
        """添加一行内容（可能是文字或按钮组或下拉列表）"""
        # 计算可用宽度（减去滚动条和边距）
        max_width = self.rect.width - self.scrollbar_width - 20

        line = MessageLine(content, color, self.font, max_width)

        # 如果是按钮行或下拉列表行，设置回调
        if button_callback and (line.buttons or line.submit_button):
            line.set_button_callback(button_callback)

        self.lines.append(line)
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)

        # 自动滚动到底部
        total_height = sum(line.height for line in self.lines)
        visible_height = self.rect.height - 10
        if total_height > visible_height:
            self.scroll_y = total_height - visible_height

    def draw(self, surface):
        """修复后的绘制方法，正确显示多行文本"""
        # 绘制背景
        pygame.draw.rect(surface, COLOR_MSG_PANEL_BG, self.rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_FRAME_BORDER, self.rect, width=1, border_radius=4)

        # 裁剪区域
        self.content_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 5,
                                        self.rect.width - self.scrollbar_width - 10,
                                        self.rect.height - 10)
        surface.set_clip(self.content_rect)

        # 绘制内容
        y_offset = self.rect.y + 5 - self.scroll_y

        for line in self.lines:
            # 只绘制可见区域内的内容
            if y_offset + line.height < self.rect.y:
                y_offset += line.height
                continue
            if y_offset > self.rect.bottom:
                break

            # 绘制多行文本
            current_text_y = y_offset
            for text_line in line.text_lines:
                text_surf = self.font.render(text_line, True, line.color)
                surface.blit(text_surf, (self.rect.x + 8, current_text_y))
                current_text_y += self.font.get_height() + 4

            # 绘制按钮（如果有）
            if line.buttons:
                current_x = self.rect.x + 8
                current_btn_y = current_text_y  # 从文本下方开始
                spacing = 10

                for btn in line.buttons:
                    # 检查是否需要换行
                    if current_x + btn.width > self.rect.x + 8 + self.rect.width - self.scrollbar_width - 15:
                        current_x = self.rect.x + 8
                        current_btn_y += btn.height + 5

                    btn.set_position(current_x, current_btn_y)
                    btn.draw(surface)
                    current_x += btn.width + spacing

            # 绘制下拉列表和提交按钮（如果有）
            if line.dropdown and line.submit_button:
                list_x = self.rect.x + 8
                list_y = current_text_y + 5
                line.dropdown.set_position(list_x, list_y)
                line.dropdown.draw(surface)

                # 提交按钮位置
                btn_x = list_x
                btn_y = list_y + (
                    line.dropdown.expanded_height if line.dropdown.expanded else line.dropdown.height) + 10
                line.submit_button.set_position(btn_x, btn_y)
                line.submit_button.draw(surface)

            y_offset += line.height

        surface.set_clip(None)

        # 绘制滚动条
        self._draw_scrollbar(surface)

    def _draw_scrollbar(self, surface):
        total_height = sum(line.height for line in self.lines)
        visible_height = self.rect.height - 10

        if total_height <= visible_height:
            return  # 不需要滚动条

        scrollbar_x = self.rect.right - self.scrollbar_width - 2
        scrollbar_rect = pygame.Rect(scrollbar_x, self.rect.y + 5,
                                     self.scrollbar_width, self.rect.height - 10)

        # 滚动条背景
        pygame.draw.rect(surface, COLOR_SCROLL_BAR_BG, scrollbar_rect, border_radius=6)

        # 计算滑块位置
        ratio = visible_height / total_height
        thumb_height = max(30, int(scrollbar_rect.height * ratio))
        max_scroll = total_height - visible_height
        if max_scroll > 0:
            thumb_pos = scrollbar_rect.y + (self.scroll_y / max_scroll) * (scrollbar_rect.height - thumb_height)
        else:
            thumb_pos = scrollbar_rect.y

        thumb_rect = pygame.Rect(scrollbar_x + 2, thumb_pos,
                                 self.scrollbar_width - 4, thumb_height)

        # 滑块颜色
        thumb_color = COLOR_SCROLL_BAR_ACTIVE if self.scrollbar_hover else COLOR_FRAME_BORDER
        pygame.draw.rect(surface, thumb_color, thumb_rect, border_radius=6)

        self.scrollbar_rect = scrollbar_rect
        self.thumb_rect = thumb_rect

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        self._last_mouse_pos = mouse_pos

        # 首先处理活动的下拉列表（如果存在）
        if self.active_dropdown:
            if self.active_dropdown.handle_event(event, mouse_pos):
                if not self.active_dropdown.expanded:
                    self.active_dropdown = None
                return True

        # 处理鼠标滚轮
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(mouse_pos):
                total_height = sum(line.height for line in self.lines)
                visible_height = self.rect.height - 10
                if total_height > visible_height:
                    self.scroll_y = max(0, min(total_height - visible_height,
                                               self.scroll_y - event.y * 30))
                return True

        elif event.type == pygame.MOUSEMOTION:
            # 更新滚动条悬停状态
            if hasattr(self, 'thumb_rect') and self.thumb_rect.collidepoint(mouse_pos):
                self.scrollbar_hover = True
            else:
                self.scrollbar_hover = False

            if self.scrollbar_dragging:
                total_height = sum(line.height for line in self.lines)
                visible_height = self.rect.height - 10
                max_scroll = total_height - visible_height

                relative_y = mouse_pos[1] - self.scrollbar_rect.y
                ratio = relative_y / self.scrollbar_rect.height
                self.scroll_y = max(0, min(max_scroll, int(ratio * max_scroll)))
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 检查滚动条点击
            if hasattr(self, 'thumb_rect') and self.thumb_rect.collidepoint(mouse_pos):
                self.scrollbar_dragging = True
                return True

            # 检查是否在内容区域内
            if not self.content_rect or not self.content_rect.collidepoint(mouse_pos):
                return False

            # 计算相对于内容区域的坐标
            relative_x = mouse_pos[0] - self.content_rect.x
            relative_y = mouse_pos[1] - self.content_rect.y + self.scroll_y

            # 遍历所有行，检查点击
            current_y = 0
            for line in self.lines:
                if current_y <= relative_y < current_y + line.height:
                    # 检查是否点击在下拉列表上
                    if line.dropdown:
                        dropdown_rect = pygame.Rect(
                            line.dropdown.rect.x,
                            line.dropdown.rect.y,
                            line.dropdown.width,
                            line.dropdown.expanded_height if line.dropdown.expanded else line.dropdown.height
                        )

                        if dropdown_rect.collidepoint(mouse_pos):
                            # 激活这个下拉列表
                            self.active_dropdown = line.dropdown
                            line.dropdown.handle_event(event, mouse_pos)
                            return True

                    # 检查是否点击在按钮上
                    elif line.buttons:
                        for btn in line.buttons:
                            if btn.rect.collidepoint(mouse_pos):
                                btn.pressed = True
                                return True

                    # 检查是否点击在提交按钮上
                    if line.submit_button and line.submit_button.rect.collidepoint(mouse_pos):
                        line.submit_button.pressed = True
                        return True

                current_y += line.height

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.scrollbar_dragging:
                self.scrollbar_dragging = False
                return True

            # 检查是否在内容区域内
            if not self.content_rect or not self.content_rect.collidepoint(mouse_pos):
                return False

            # 处理按钮释放
            relative_x = mouse_pos[0] - self.content_rect.x
            relative_y = mouse_pos[1] - self.content_rect.y + self.scroll_y

            current_y = 0
            for line in self.lines:
                if current_y <= relative_y < current_y + line.height:
                    # 检查按钮释放
                    if line.buttons:
                        for btn in line.buttons:
                            if btn.rect.collidepoint(mouse_pos) and btn.pressed:
                                btn.pressed = False
                                if btn.callback:
                                    btn.callback()
                                return True

                    # 检查提交按钮释放
                    if line.submit_button and line.submit_button.rect.collidepoint(mouse_pos):
                        if hasattr(line.submit_button, 'pressed') and line.submit_button.pressed:
                            line.submit_button.pressed = False
                            if line.submit_button.callback:
                                line.submit_button.callback()
                            return True

                current_y += line.height

        return False


class TabView:
    """标签页组件"""

    def __init__(self, rect, tabs, font=None):
        self.rect = pygame.Rect(rect)
        self.tabs = tabs  # [(name, content_surface), ...]
        self.active_tab = 0
        self.font = font or FONT_TAB_TITLE()
        self.tab_height = 30

    def draw(self, surface):
        # 绘制标签栏背景
        tab_bar_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.tab_height)
        pygame.draw.rect(surface, COLOR_TAB_NORMAL_BG, tab_bar_rect)

        # 绘制标签
        tab_width = self.rect.width // len(self.tabs)
        for i, (name, _) in enumerate(self.tabs):
            tab_rect = pygame.Rect(self.rect.x + i * tab_width, self.rect.y,
                                   tab_width, self.tab_height)

            # 背景色
            bg_color = COLOR_TAB_SELECT_BG if i == self.active_tab else COLOR_TAB_NORMAL_BG
            pygame.draw.rect(surface, bg_color, tab_rect)

            # 分隔线
            if i > 0:
                pygame.draw.line(surface, COLOR_FRAME_BORDER,
                                 (tab_rect.x, tab_rect.y),
                                 (tab_rect.x, tab_rect.y + self.tab_height))

            # 文字
            text_surf = self.font.render(name, True, COLOR_TEXT_TAB_TITLE)
            text_rect = text_surf.get_rect(center=tab_rect.center)
            surface.blit(text_surf, text_rect)

        # 绘制内容区域
        content_rect = pygame.Rect(self.rect.x, self.rect.y + self.tab_height,
                                   self.rect.width, self.rect.height - self.tab_height)
        pygame.draw.rect(surface, COLOR_FRAME_ALL_BG, content_rect)
        pygame.draw.rect(surface, COLOR_FRAME_BORDER, content_rect, width=1)

        # 绘制当前标签内容
        if self.tabs:
            _, content = self.tabs[self.active_tab]
            if content:
                # 居中显示内容
                content_rect_inner = pygame.Rect(content_rect.x + 5, content_rect.y + 5,
                                                 content_rect.width - 10, content_rect.height - 10)
                # 等比缩放内容
                scaled = self._fit_content(content, content_rect_inner.width, content_rect_inner.height)
                if scaled:
                    scaled_rect = scaled.get_rect(center=content_rect.center)
                    surface.blit(scaled, scaled_rect)

    def _fit_content(self, surface, max_w, max_h):
        """等比缩放内容"""
        if surface is None:
            return None
        w, h = surface.get_size()
        scale = min(max_w / w, max_h / h, 1.0)
        if scale >= 1.0:
            return surface
        new_w, new_h = int(w * scale), int(h * scale)
        return pygame.transform.smoothscale(surface, (new_w, new_h))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # 检查是否点击标签
                tab_width = self.rect.width // len(self.tabs)
                for i in range(len(self.tabs)):
                    tab_rect = pygame.Rect(self.rect.x + i * tab_width, self.rect.y,
                                           tab_width, self.tab_height)
                    if tab_rect.collidepoint(event.pos):
                        self.active_tab = i
                        return True
        return False

    def set_tab_content(self, index, content_surface):
        if 0 <= index < len(self.tabs):
            name, _ = self.tabs[index]
            self.tabs[index] = (name, content_surface)


class Dialog:
    """模态对话框"""

    def __init__(self, title, width=320, height=190):
        self.title = title
        self.width = width
        self.height = height
        self.active = False
        self.result = None
        self.elements = []

        # 计算居中位置
        screen_w, screen_h = pygame.display.get_surface().get_size()
        self.rect = pygame.Rect((screen_w - width) // 2, (screen_h - height) // 2, width, height)

    def show(self):
        self.active = True

    def close(self):
        self.active = False

    def draw(self, surface):
        if not self.active:
            return

        # 半透明遮罩
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))

        # 对话框背景
        pygame.draw.rect(surface, COLOR_ROOT_BG, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_FRAME_BORDER, self.rect, width=2, border_radius=8)

        # 标题
        title_surf = FONT_RULE_TITLE().render(self.title, True, COLOR_TEXT_LABEL_TITLE)
        title_rect = title_surf.get_rect(centerx=self.rect.centerx, top=self.rect.y + 20)
        surface.blit(title_surf, title_rect)

        # 绘制子元素
        for elem in self.elements:
            if hasattr(elem, 'draw'):
                elem.draw(surface)

    def handle_event(self, event):
        """修复：正确处理对话框内的事件，优先传递给子元素"""
        if not self.active:
            return False

        handled = False

        # 优先处理子元素（输入框、按钮等）
        # 倒序遍历，让后添加的元素（通常在上层）先处理
        for elem in reversed(self.elements):
            if hasattr(elem, 'handle_event'):
                if elem.handle_event(event):
                    handled = True
                    break  # 如果子元素处理了事件，就不再继续传递

        # 如果子元素没有处理，检查是否点击对话框外部（可选：点击外部关闭）
        if not handled and event.type == pygame.MOUSEBUTTONDOWN:
            if not self.rect.collidepoint(event.pos):
                # 点击外部不自动关闭，保持模态特性
                pass

        # ESC关闭对话框
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True

        return True  # 对话框激活时，消费所有事件（模态特性）


# ==================== 主游戏类 ====================

class GameClient:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("推理游戏 - Pygame版")
        self.clock = pygame.time.Clock()
        self.running = True

        # 游戏状态
        self.client_socket = None
        self.is_connected = False
        self.recv_thread = None
        self.current_host = HOST
        self.current_port = PORT

        # 地图图片缓存
        self.map_surfaces = {}

        # 创建UI
        self._create_ui()

        # 加载地图
        self._load_maps()

    def _create_ui(self):
        """创建所有UI组件"""
        # 顶部状态栏 (y: 0-40)
        self.status_label_pos = (20, 15)
        self.config_btn = Button((WINDOW_WIDTH - 120, 10, 100, 30), "设置服务器", self.show_config_dialog)

        # 主内容区域
        # 左侧面板 - 消息面板 (x: 12, y: 50, w: ~594, h: ~590)
        left_width = int(WINDOW_WIDTH * 0.6) - 24
        self.msg_panel = ScrollText((12, 50, left_width, WINDOW_HEIGHT - 120))

        # 右侧容器 - 地图 + 玩法说明
        right_x = left_width + 24
        right_width = WINDOW_WIDTH - right_x - 12

        # 地图区域 - 严格16:9比例 (高度 = 宽度 * 0.5625)
        map_height = int(right_width * 0.5625)
        self.map_tabs = []
        for name in MAP_PATHS.keys():
            self.map_tabs.append((name, None))
        self.map_view = TabView((right_x, 50, right_width, map_height), self.map_tabs)

        # 玩法说明区域
        rule_y = 50 + map_height + 12
        rule_height = WINDOW_HEIGHT - rule_y - 70
        self.rule_panel = ScrollText((right_x, rule_y, right_width, rule_height), font=FONT_RULE_CONTENT())

        # 初始化玩法说明内容（支持自动换行）
        self._init_rule_content()

        # 底部输入区
        input_y = WINDOW_HEIGHT - 60
        self.input_label_pos = (20, input_y + 10)
        self.input_entry = TextInput((100, input_y, left_width - 80, 40))
        self.send_btn = Button((left_width + 40, input_y, 80, 40), "发送", self.send_message)

        # 对话框
        self.config_dialog = None

    def _init_rule_content(self):
        """初始化玩法说明内容 - 优化自动换行"""
        # 定义规则文本（原始内容）
        rules_raw = [
            ("游戏背景设定", COLOR_TEXT_LABEL_TITLE),
            ("在世界上，存在名为“魔女”的种族。在人类发现他们后，出于对不可控力量的恐惧，人类发动了战争将这个种族从世界上抹去。而在最后一名魔女死亡之前，为了报复人类，她将名为‘魔女因子’的物质散播至世界",
             COLOR_MSG_DEFAULT),
            ("一些受过心理创伤的少女被魔女因子感染后，便会成为‘预备魔女’，而一旦再次经历心理创伤，这些预备魔女便会‘魔女化’，成为拥有强大力量，同时拥有强烈杀戮欲望的‘魔女’",
             COLOR_MSG_DEFAULT),
            ("为了防止最坏的情况发生，国家找到了检测‘魔女因子’的方法，并将所有的‘预备魔女’囚禁于一座监牢中，一旦监牢内发生杀人案，典狱长将会举行‘魔女审判’，将预备魔女们票选出的‘魔女’处刑",
             COLOR_MSG_DEFAULT),
            ("在游戏中，部分玩家需要扮演‘预备魔女’的角色，找出并票选出所有的‘魔女’将其处刑。而另一部分玩家会成为‘魔女’，她们希望杀死所有人",
             COLOR_MSG_DEFAULT),
            ("", COLOR_MSG_DEFAULT),
            ("基础操作规则", COLOR_TEXT_LABEL_TITLE),
            ("1. 连接服务器后，可以开始输入昵称", COLOR_MSG_DEFAULT),
            ("2. 在选择人物时，请完整且区分大小写地输入列出的人物昵称，如果输入后程序无反应，请稍等或检查输入是否有误",
             COLOR_MSG_DEFAULT),
            ("3. 地图面板可切换不同楼层，查看当前场景布局，每间房间有门的墙上均有窗户，且由于年久失修，窗户玻璃均已碎裂",
             COLOR_MSG_DEFAULT),
            ("4. 输入框与游戏过程中弹出的下拉列表或按钮等价，可以使用输入框输入按钮上的内容进行选择", COLOR_MSG_DEFAULT),
            ("5. 在消息界面弹出下拉列表或按钮时，使用下拉列表或按钮进行选择，尽量避免使用输入框输入", COLOR_MSG_DEFAULT),
            ("", COLOR_MSG_DEFAULT),
            ("游戏核心玩法", COLOR_TEXT_LABEL_TITLE),
            ("1. 本游戏为多人对抗推理类游戏，通过探索场景收集线索", COLOR_MSG_DEFAULT),
            ("2. 参与游戏的玩家中，有一名玩家在游戏开始时会成为魔女，随着游戏进行，可能会有更多玩家成为魔女",
             COLOR_MSG_DEFAULT),
            ("3. 魔女可以攻击其他玩家，玩家被击杀后会留下尸体，当尸体被其他玩家发现时游戏进入搜证阶段，魔女杀人后玩家可能会获取到有关凶手与杀人手法的其他证据",
             COLOR_MSG_DEFAULT),
            ("4. 搜证结束后进入发言阶段，玩家可以通过提交已有证据进行发言，当所有玩家发言结束后将进行一轮总结，随后进行投票，得票最高的玩家将被处刑",
             COLOR_MSG_DEFAULT),
            ("5. 魔女需要杀死所有非魔女玩家，非魔女玩家需要在投票时票选出魔女，直到所有魔女均被处刑", COLOR_MSG_DEFAULT),
            ("6. 收集到的线索可以在手机中查看，玩家需整合线索完成推理并找出魔女，魔女则需隐藏自己", COLOR_MSG_DEFAULT),
            ("7. 同时，每名玩家都拥有不同的‘魔法’，在适当时机发动来为自己争取优势吧", COLOR_MSG_DEFAULT),
        ]

        # 清空现有内容
        self.rule_panel.lines = []

        # 添加规则文本，确保自动换行生效
        for text, color in rules_raw:
            # 直接使用add_line方法，它会自动处理换行
            self.rule_panel.add_line(text, color)

    def _load_maps(self):
        """加载地图图片（强制16:9显示）"""
        for i, (name, path) in enumerate(MAP_PATHS.items()):
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path).convert()
                    self.map_surfaces[name] = img
                    self.map_view.set_tab_content(i, img)
                    self.add_message(f"加载地图: {name}", COLOR_MSG_SUCCESS)
                else:
                    # 创建错误提示表面
                    surf = pygame.Surface((400, 225))
                    surf.fill(COLOR_FRAME_ALL_BG)
                    text = FONT_MAIN().render(f"地图文件不存在: {path}", True, COLOR_MSG_ERROR)
                    surf.blit(text, (20, 100))
                    self.map_view.set_tab_content(i, surf)
                    self.add_message(f"{name} 文件不存在: {path}", COLOR_MSG_ERROR)
            except Exception as e:
                self.add_message(f"加载{name}失败: {str(e)}", COLOR_MSG_ERROR)

    def show_config_dialog(self):
        """显示服务器配置对话框"""
        if self.is_connected:
            self.disconnect_server()
            return

        self.config_dialog = Dialog("服务器配置", 320, 200)
        self.config_dialog.show()

        # 添加输入框和按钮到对话框
        dialog = self.config_dialog

        # IP输入
        ip_y = dialog.rect.y + 50
        self.dialog_ip = TextInput((dialog.rect.x + 20, ip_y, dialog.rect.width - 40, 30))
        self.dialog_ip.text = self.current_host

        # 端口输入
        port_y = ip_y + 50
        self.dialog_port = TextInput((dialog.rect.x + 20, port_y, dialog.rect.width - 40, 30))
        self.dialog_port.text = str(self.current_port)

        # 确认按钮
        def on_confirm():
            try:
                self.current_host = self.dialog_ip.get_text().strip()
                self.current_port = int(self.dialog_port.get_text().strip())
                if not (1 <= self.current_port <= 65535):
                    raise ValueError("端口范围错误")
                dialog.close()
                self.add_message(f"✅ 服务器配置完成: {self.current_host}:{self.current_port}", COLOR_MSG_SUCCESS)
                self.connect_server()
            except ValueError as e:
                self.add_message(f"❌ 配置错误: {str(e)}", COLOR_MSG_ERROR)

        self.dialog_confirm = Button((dialog.rect.centerx - 50, dialog.rect.y + 150, 100, 35),
                                     "确认配置", on_confirm)

        dialog.elements = [self.dialog_ip, self.dialog_port, self.dialog_confirm]

    def add_message(self, text, color=COLOR_MSG_DEFAULT):
        """添加消息到面板"""
        # 检查是否是按钮消息或列表消息
        if isinstance(text, str):
            text = text.strip()  # 确保去除首尾空白
            if text.startswith("button:") or text.startswith("list:"):
                # 按钮或列表消息，传入回调函数
                self.msg_panel.add_line(text, color, self.on_button_or_list_click)
            else:
                self.msg_panel.add_line(text, color)
        else:
            self.msg_panel.add_line(text, color)

    def on_button_or_list_click(self, button_text):
        """消息中按钮或列表提交的点击回调"""
        # 自动发送按钮文字或选中的列表项作为指令
        if self.is_connected and self.client_socket:
            try:
                # 发送按钮文字或列表选中的内容
                self.client_socket.send(button_text.encode(ENCODING))

                # 显示发送的消息
                if "list:" in button_text:  # 这是列表提交
                    self.add_message(f"你(选择提交): {button_text}", COLOR_MSG_SELF)
                else:  # 普通按钮
                    self.add_message(f"你(点击): {button_text}", COLOR_MSG_SELF)
            except Exception as e:
                self.add_message(f"❌ 发送失败: {str(e)}", COLOR_MSG_ERROR)
        else:
            self.add_message("⚠️ 未连接服务器，无法执行操作", COLOR_MSG_TIP)

    def connect_server(self):
        """连接服务器"""
        if self.is_connected:
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 不设置超时，使用阻塞模式
            self.client_socket.setblocking(True)
            self.client_socket.connect((self.current_host, self.current_port))
            self.is_connected = True
            self.config_btn.text = "断开连接"

            self.add_message(f"✅ 成功连接到游戏服务器 {self.current_host}:{self.current_port}！", COLOR_MSG_SUCCESS)

            # 启动接收线程
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()

        except Exception as e:
            self.add_message(f"❌ 连接服务器失败: {str(e)}", COLOR_MSG_ERROR)

    def disconnect_server(self):
        """断开服务器"""
        if self.is_connected and self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.is_connected = False
        self.config_btn.text = "设置服务器"
        self.add_message("❌ 已断开与服务器的连接", COLOR_MSG_ERROR)

    def _recv_loop(self):
        """接收消息循环 - 修复TCP粘包问题"""
        while self.is_connected:
            try:
                # 阻塞式接收数据
                data = self.client_socket.recv(BUFFER_SIZE).decode(ENCODING)
                if not data:
                    # 对方关闭连接
                    if not hasattr(self, 'pending_messages'):
                        self.pending_messages = []
                    self.pending_messages.append(("❌ 服务器已关闭连接", COLOR_MSG_ERROR))
                    self.is_connected = False
                    break

                # 按换行符分割多条消息
                messages = data.split('\n')

                for msg in messages:
                    msg = msg.strip()
                    if not msg:  # 跳过空行
                        continue

                    # 根据内容判断颜色
                    color = COLOR_MSG_DEFAULT

                    # 按钮消息或列表消息特殊处理（不判断颜色）
                    if msg.startswith("button:") or msg.startswith("list:"):
                        color = COLOR_MSG_SYSTEM  # 按钮或列表消息使用系统色
                    elif "系统公告" in msg or "游戏结束" in msg:
                        color = COLOR_MSG_SYSTEM
                    elif "失败" in msg or "死亡" in msg or "不可" in msg:
                        color = COLOR_MSG_ERROR
                    elif "成功" in msg or "获得" in msg or "已到达" in msg:
                        color = COLOR_MSG_SUCCESS
                    elif "请" in msg or "输入" in msg or "可选" in msg:
                        color = COLOR_MSG_TIP
                    else:
                        color = COLOR_MSG_DEFAULT

                    # 使用线程安全的方式添加消息
                    if not hasattr(self, 'pending_messages'):
                        self.pending_messages = []
                    self.pending_messages.append((msg, color))

            except Exception as e:
                # 只有在明确断开连接时才退出
                if self.is_connected:
                    if not hasattr(self, 'pending_messages'):
                        self.pending_messages = []
                    self.pending_messages.append((f"❌ 与服务器断开连接: {str(e)}", COLOR_MSG_ERROR))
                    self.is_connected = False
                break

    def send_message(self):
        """发送消息"""
        msg = self.input_entry.get_text().strip()
        if not msg:
            return

        if not self.is_connected:
            self.add_message("⚠️ 请先配置并连接服务器再发送指令！", COLOR_MSG_TIP)
            return

        try:
            # 发送消息并添加换行符，帮助服务器识别消息边界
            self.client_socket.send((msg + '\n').encode(ENCODING))
            self.add_message(f"你: {msg}", COLOR_MSG_SELF)
            self.input_entry.clear()
        except Exception as e:
            self.add_message(f"❌ 发送指令失败: {str(e)}", COLOR_MSG_ERROR)

    def run(self):
        """主循环 - 修复事件处理"""
        # 启动文本输入系统（支持中文）
        pygame.key.start_text_input()

        while self.running:
            dt = self.clock.tick(FPS)

            # 处理待处理的消息（从接收线程）
            if hasattr(self, 'pending_messages'):
                for text, color in self.pending_messages:
                    self.add_message(text, color)
                self.pending_messages.clear()

            # 处理断开状态
            if not self.is_connected and self.config_btn.text == "断开连接":
                self.config_btn.text = "设置服务器"

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    # 处理窗口大小变化（保持最小尺寸）
                    new_w = max(event.w, WINDOW_MIN_WIDTH)
                    new_h = max(event.h, WINDOW_MIN_HEIGHT)
                    self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                    self._on_resize(new_w, new_h)

                # 更新输入框的位置（用于文本输入候选框跟随）
                if event.type == pygame.MOUSEBUTTONDOWN and self.input_entry.active:
                    pygame.key.set_text_input_rect(self.input_entry.rect)

                # 先处理对话框（模态）
                if self.config_dialog and self.config_dialog.active:
                    handled = self.config_dialog.handle_event(event)
                    if handled:
                        continue  # 对话框处理了事件，跳过后续处理
                    # 即使对话框没有处理特定事件，也继续处理（保持模态）

                # 再处理其他UI - 优先级：输入框 > 消息面板(含按钮和下拉列表) > 其他
                handled = False

                if not handled:
                    handled = self.input_entry.handle_event(event)
                    if handled == "submit":
                        self.send_message()
                        handled = True

                if not handled:
                    handled = self.msg_panel.handle_event(event)

                if not handled:
                    handled = self.map_view.handle_event(event)

                if not handled:
                    handled = self.rule_panel.handle_event(event)

                if not handled:
                    handled = self.config_btn.handle_event(event)

                if not handled:
                    handled = self.send_btn.handle_event(event)

            # 更新
            self.input_entry.update(dt)

            # 绘制
            self.screen.fill(COLOR_ROOT_BG)

            # 绘制状态栏
            status_text = f"已连接服务器 {self.current_host}:{self.current_port} | 游戏中" if self.is_connected else f"未设置服务器 | 等待配置..." if self.config_btn.text == "设置服务器" else f"已配置服务器 {self.current_host}:{self.current_port} | 未连接"
            status_color = COLOR_TEXT_STATUS_CONNECT if self.is_connected else COLOR_TEXT_STATUS_DISCONNECT
            status_surf = FONT_STATUS().render(status_text, True, status_color)
            self.screen.blit(status_surf, self.status_label_pos)

            # 绘制组件
            self.config_btn.draw(self.screen)
            self.msg_panel.draw(self.screen)
            self.map_view.draw(self.screen)
            self.rule_panel.draw(self.screen)

            # 绘制底部
            label_surf = FONT_MAIN().render("输入指令:", True, COLOR_TEXT_LABEL_TITLE)
            self.screen.blit(label_surf, self.input_label_pos)
            self.input_entry.draw(self.screen)
            self.send_btn.draw(self.screen)

            # 绘制对话框
            if self.config_dialog:
                self.config_dialog.draw(self.screen)

            pygame.display.flip()

        # 清理
        pygame.key.stop_text_input()
        if self.is_connected:
            self.disconnect_server()
        pygame.quit()
        sys.exit()

    def _on_resize(self, w, h):
        """窗口大小变化时重新布局"""
        # 更新组件位置和大小
        left_width = int(w * 0.6) - 24
        self.msg_panel.rect = pygame.Rect(12, 50, left_width, h - 120)

        right_x = left_width + 24
        right_width = w - right_x - 12

        # 地图保持16:9
        map_height = int(right_width * 0.5625)
        self.map_view.rect = pygame.Rect(right_x, 50, right_width, map_height)

        # 玩法说明填充剩余空间
        rule_y = 50 + map_height + 12
        rule_height = h - rule_y - 70
        self.rule_panel.rect = pygame.Rect(right_x, rule_y, right_width, max(rule_height, 100))

        # 底部输入区
        input_y = h - 60
        self.input_label_pos = (20, input_y + 10)
        self.input_entry.rect = pygame.Rect(100, input_y, left_width - 80, 40)
        self.send_btn.rect = pygame.Rect(left_width + 40, input_y, 80, 40)
        self.config_btn.rect = pygame.Rect(w - 120, 10, 100, 30)

        # 更新文本输入框位置
        if self.input_entry.active:
            pygame.key.set_text_input_rect(self.input_entry.rect)

        # 重新初始化玩法说明内容，以便根据新宽度重新换行
        self._init_rule_content()


def main():
    game = GameClient()
    game.run()


if __name__ == "__main__":
    main()