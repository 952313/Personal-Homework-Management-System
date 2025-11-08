"""
Copyright (c) 2025 Yang Jincheng
Licensed under CC BY-NC-SA 4.0
"""
import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime, timedelta
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.font_manager as fm

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置CustomTkinter主题
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class HomeworkPlatform:
    def __init__(self, root):
        self.root = root
        self.root.title("学生自托管作业登记平台")
        self.root.geometry("1300x850")  # 进一步增大窗口
        
        # 数据文件
        self.data_file = "homework_data.json"
        self.homeworks = self.load_data()
        
        # 创建界面
        self.create_widgets()
        
    def load_data(self):
        """加载作业数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保所有作业都有status字段
                    for hw in data:
                        if 'status' not in hw:
                            hw['status'] = 'pending'
                    return data
            except:
                return []
        return []
    
    def save_data(self):
        """保存作业数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.homeworks, f, ensure_ascii=False, indent=2)
    
    def get_homework_status(self, due_date):
        """根据截止日期获取作业状态"""
        try:
            due = datetime.strptime(due_date, "%d/%m/%Y")
            today = datetime.now()
            
            if due.date() < today.date():
                return "overdue"  # 逾期
            elif due.date() == today.date():
                return "due_today"  # 今天截止
            elif (due.date() - today.date()).days <= 3:
                return "due_soon"  # 即将截止（3天内）
            else:
                return "pending"  # 进行中
        except:
            return "pending"
    
    def should_display_homework(self, hw):
        """判断是否应该显示这个作业"""
        if hw.get('status') == 'completed':
            # 只显示今天或今天之前已完成的作业
            try:
                due_date = datetime.strptime(hw['due_date'], "%d/%m/%Y")
                today = datetime.now()
                return due_date.date() >= today.date()
            except:
                return True
        return True
    
    def create_widgets(self, textsizeoftable=20):
        """创建界面组件"""
        # 创建主框架
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 创建选项卡
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # 创建主要功能选项卡
        self.main_tab = self.tabview.add("作业管理")
        self.chart_tab = self.tabview.add("图表")  # 新增图表选项卡
        self.about_tab = self.tabview.add("关于")
        
        # 设置默认选中的选项卡
        self.tabview.set("作业管理")
        
        # 在主选项卡中构建原来的界面
        self.build_main_tab(self.main_tab, textsizeoftable)
        
        # 在图表选项卡中构建图表
        self.build_chart_tab(self.chart_tab)
        
        # 在关于选项卡中构建关于内容
        self.build_about_tab(self.about_tab)

    def build_main_tab(self, parent, textsizeoftable):
        """构建主选项卡内容"""
        # 创建顶部框架（标题和统计信息）
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))
        
        # 标题
        title_label = ctk.CTkLabel(top_frame, text="作业登记平台", 
                                  font=ctk.CTkFont(size=32, weight="bold"))
        title_label.pack(pady=(0, 10))
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(top_frame, text="", 
                                       font=ctk.CTkFont(size=18))
        self.stats_label.pack()
        
        # 创建中间内容框架
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # 左侧功能框架
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # 添加作业部分
        self.add_frame = ctk.CTkFrame(left_frame)
        self.add_frame.pack(fill="x", pady=(0, 15))
        
        # ... 这里插入之前的所有主界面代码，但将 main_frame 改为 parent ...
        # 第一行：作业代号和科目
        row1_frame = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        row1_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(row1_frame, text="作业代号:", 
                    font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        self.code_entry = ctk.CTkEntry(row1_frame, width=120, font=ctk.CTkFont(size=16))
        self.code_entry.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(row1_frame, text="科目:", 
                    font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        self.subject_entry = ctk.CTkEntry(row1_frame, width=120, font=ctk.CTkFont(size=16))
        self.subject_entry.pack(side="left", padx=(0, 20))
        
        # 第二行：作业内容
        row2_frame = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        row2_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(row2_frame, text="作业内容:", 
                    font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        self.content_entry = ctk.CTkEntry(row2_frame, font=ctk.CTkFont(size=16))
        self.content_entry.pack(side="left", fill="x", expand=True, padx=(0, 0))
        
        # 第三行：日期和按钮
        row3_frame = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        row3_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(row3_frame, text="创建日期:", 
                    font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        self.create_date_entry = ctk.CTkEntry(row3_frame, width=100, font=ctk.CTkFont(size=16))
        self.create_date_entry.pack(side="left", padx=(0, 20))
        self.create_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        ctk.CTkLabel(row3_frame, text="截止日期:", 
                    font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        self.due_date_entry = ctk.CTkEntry(row3_frame, width=100, font=ctk.CTkFont(size=16))
        self.due_date_entry.pack(side="left", padx=(0, 20))
        
        # 添加按钮
        ctk.CTkButton(self.add_frame, text="添加作业", command=self.add_homework,
                      height=35, font=ctk.CTkFont(size=16)).pack(pady=(0, 15))
        
        # 查询部分
        self.query_frame = ctk.CTkFrame(left_frame)
        self.query_frame.pack(fill="x", pady=(0, 15))
        
        query_row1 = ctk.CTkFrame(self.query_frame, fg_color="transparent")
        query_row1.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(query_row1, text="查询日期:", 
                    font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        self.query_date_entry = ctk.CTkEntry(query_row1, width=100, font=ctk.CTkFont(size=16))
        self.query_date_entry.pack(side="left", padx=(0, 20))
        self.query_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        # 查询类型
        self.query_type = ctk.StringVar(value="due")
        ctk.CTkRadioButton(query_row1, text="按截止日期查询", 
                          variable=self.query_type, value="due",
                          font=ctk.CTkFont(size=16)).pack(side="left", padx=(20, 10))
        ctk.CTkRadioButton(query_row1, text="按创建日期查询", 
                          variable=self.query_type, value="create",
                          font=ctk.CTkFont(size=16)).pack(side="left", padx=(10, 0))
        
        # 查询按钮
        ctk.CTkButton(self.query_frame, text="查询作业", command=self.query_homework,
                      height=35, font=ctk.CTkFont(size=16)).pack(pady=(0, 15))
        
        # 操作按钮框架
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", pady=(0, 0))
        
        ctk.CTkButton(button_frame, text="删除选中作业", command=self.delete_homework,
                      height=35, font=ctk.CTkFont(size=16)).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(button_frame, text="标记为已完成", command=self.mark_as_completed,
                      height=35, font=ctk.CTkFont(size=16)).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(button_frame, text="清空所有作业", command=self.clear_all_homework,
                      height=35, font=ctk.CTkFont(size=16)).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(button_frame, text="刷新列表", command=self.refresh_list,
                      height=35, font=ctk.CTkFont(size=16)).pack(fill="x", padx=10, pady=5)
        
        # 右侧表格框架
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # 结果显示区域
        self.result_frame = ctk.CTkFrame(right_frame)
        self.result_frame.pack(fill="both", expand=True)
        
        # 结果标题
        self.result_title = ctk.CTkLabel(self.result_frame, text="所有作业", 
                                        font=ctk.CTkFont(size=20, weight="bold"))
        self.result_title.pack(pady=10)
        
        # 创建树形视图显示作业
        tree_frame = ctk.CTkFrame(self.result_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 配置Treeview样式
        style = ttk.Style()
        style.theme_use('default')
        
        style.configure("Custom.Treeview",
                        background="#f8f9fa",
                        foreground="black",
                        fieldbackground="#f8f9fa",
                        borderwidth=1,
                        relief="solid",
                        font=('Microsoft YaHei', textsizeoftable),
                        rowheight=45)
        
        style.configure("Custom.Treeview.Heading",
                        background="#e9ecef",
                        foreground="black",
                        relief="raised",
                        font=('Microsoft YaHei', textsizeoftable+2, 'bold'))
        
        style.map('Custom.Treeview',
                 background=[('selected', '#007bff')],
                 foreground=[('selected', 'white')])
        
        columns = ("代号", "科目", "内容", "创建日期", "截止日期", "状态")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                height=14, style="Custom.Treeview")
        
        # 设置列宽
        self.tree.column("代号", width=160, anchor="center", minwidth=140)
        self.tree.column("科目", width=200, anchor="center", minwidth=180)
        self.tree.column("内容", width=400, anchor="w", minwidth=300)
        self.tree.column("创建日期", width=180, anchor="center", minwidth=160)
        self.tree.column("截止日期", width=180, anchor="center", minwidth=160)
        self.tree.column("状态", width=180, anchor="center", minwidth=160)
        
        for col in columns:
            self.tree.heading(col, text=col)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y", padx=(5, 0))
        
        # 创建右键菜单
        self.create_context_menu()
        
        # 初始显示所有作业
        self.update_stats()
        self.refresh_list()

    def build_chart_tab(self, parent):
        """构建图表选项卡内容"""
        # 标题
        title_label = ctk.CTkLabel(parent, text="作业统计图表", 
                                  font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # 刷新按钮
        refresh_button = ctk.CTkButton(parent, text="刷新图表", command=self.update_charts,
                                      height=35, font=ctk.CTkFont(size=16))
        refresh_button.pack(pady=(0, 10))
        
        # 创建滚动框架以容纳图表
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 饼图框架
        pie_frame = ctk.CTkFrame(scroll_frame)
        pie_frame.pack(fill="x", pady=(0, 20))
        
        pie_title = ctk.CTkLabel(pie_frame, text="作业状态分布", 
                                font=ctk.CTkFont(size=20, weight="bold"))
        pie_title.pack(pady=10)
        
        # 饼图画布
        self.pie_fig = Figure(figsize=(8, 6), dpi=100)
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, pie_frame)
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # 折线图框架
        line_frame = ctk.CTkFrame(scroll_frame)
        line_frame.pack(fill="x", pady=(0, 20))
        
        line_title = ctk.CTkLabel(line_frame, text="最近5天作业量统计", 
                                 font=ctk.CTkFont(size=20, weight="bold"))
        line_title.pack(pady=10)
        
        # 折线图画布
        self.line_fig = Figure(figsize=(10, 6), dpi=100)
        self.line_canvas = FigureCanvasTkAgg(self.line_fig, line_frame)
        self.line_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # 初始更新图表
        self.update_charts()

    def update_charts(self):
        """更新图表"""
        self.update_pie_chart()
        self.update_line_chart()

    def update_pie_chart(self):
        """更新饼图"""
        # 清空图形
        self.pie_fig.clear()
        
        # 统计各状态作业数量
        status_counts = {
            'completed': 0,
            'overdue': 0,
            'due_today': 0,
            'due_soon': 0,
            'pending': 0
        }
        
        for hw in self.homeworks:
            if not self.should_display_homework(hw):
                continue
                
            if hw.get('status') == 'completed':
                status_counts['completed'] += 1
            else:
                status = self.get_homework_status(hw['due_date'])
                status_counts[status] += 1
        
        # 过滤掉数量为0的状态
        labels = []
        sizes = []
        colors = []
        
        if status_counts['completed'] > 0:
            labels.append('已完成')
            sizes.append(status_counts['completed'])
            colors.append('#28a745')  # 绿色
        
        if status_counts['overdue'] > 0:
            labels.append('逾期')
            sizes.append(status_counts['overdue'])
            colors.append('#dc3545')  # 红色
        
        if status_counts['due_today'] > 0:
            labels.append('今天截止')
            sizes.append(status_counts['due_today'])
            colors.append('#fd7e14')  # 橙色
        
        if status_counts['due_soon'] > 0:
            labels.append('即将截止')
            sizes.append(status_counts['due_soon'])
            colors.append('#ffc107')  # 黄色
        
        if status_counts['pending'] > 0:
            labels.append('进行中')
            sizes.append(status_counts['pending'])
            colors.append('#007bff')  # 蓝色
        
        # 如果没有数据，显示提示
        if not sizes:
            ax = self.pie_fig.add_subplot(111)
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=16)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        else:
            # 创建饼图
            ax = self.pie_fig.add_subplot(111)
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                            startangle=90, textprops={'fontsize': 12})
            
            # 设置百分比文本样式
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title('作业状态分布', fontsize=16, fontweight='bold')
            ax.axis('equal')  # 保证饼图是圆形
        
        self.pie_canvas.draw()

    def update_line_chart(self, days=5):
        """更新折线图 - 显示最近指定天数的作业量统计"""
        # 清空图形
        self.line_fig.clear()
        
        # 获取最近days天的日期
        today = datetime.now()
        dates = []
        for i in range(days-1, -1, -1):
            date_obj = today - timedelta(days=i)
            # 手动处理日期格式，移除前导零
            day_str = str(date_obj.day)
            month_str = str(date_obj.month)
            year_str = str(date_obj.year)
            date_str = f"{day_str}/{month_str}/{year_str}"
            dates.append(date_str)
        
        # 统计每天创建和截止的作业数量
        create_counts = [0] * days
        due_counts = [0] * days
        
        for hw in self.homeworks:
            # 统计创建日期
            for i, date in enumerate(dates):
                if self.normalize_date(hw['create_date']) == self.normalize_date(date):
                    create_counts[i] += 1
            
            # 统计截止日期
            for i, date in enumerate(dates):
                if self.normalize_date(hw['due_date']) == self.normalize_date(date):
                    due_counts[i] += 1
        
        # 创建折线图
        ax = self.line_fig.add_subplot(111)
        
        # 绘制两条折线
        line1, = ax.plot(range(days), create_counts, marker='o', linewidth=2, label='创建作业', color='#007bff')
        line2, = ax.plot(range(days), due_counts, marker='s', linewidth=2, label='截止作业', color='#dc3545')
        
        # 设置图表样式
        ax.set_title(f'最近{days}天作业量统计', fontsize=16, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('作业数量', fontsize=12)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # 设置x轴刻度
        ax.set_xticks(range(days))
        ax.set_xticklabels(dates, rotation=45)
        
        # 在数据点上显示数值
        for i, (create, due) in enumerate(zip(create_counts, due_counts)):
            if create > 0:
                ax.annotate(str(create), (i, create), textcoords="offset points", 
                           xytext=(0,10), ha='center', fontsize=10, fontweight='bold')
            if due > 0:
                ax.annotate(str(due), (i, due), textcoords="offset points", 
                           xytext=(0,-15), ha='center', fontsize=10, fontweight='bold')
        
        # 设置y轴从0开始，避免显示小数
        ax.set_ylim(bottom=0)
        """
        # 添加调试信息（可选，可以在控制台查看匹配情况）
        print(f"日期范围: {dates}")
        print(f"创建作业统计: {create_counts}")
        print(f"截止作业统计: {due_counts}")
        """
        
        self.line_fig.tight_layout()
        self.line_canvas.draw()

    def normalize_date(self, date_str):
        """标准化日期格式，移除前导零"""
        try:
            parts = date_str.split('/')
            if len(parts) == 3:
                day = str(int(parts[0]))  # 移除前导零
                month = str(int(parts[1]))  # 移除前导零
                year = parts[2]
                return f"{day}/{month}/{year}"
        except:
            pass
        return date_str
    
    def build_about_tab(self, parent):
        """构建关于选项卡内容"""
        # 标题
        title_label = ctk.CTkLabel(parent, text="作业登记平台", 
                                  font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # 版本信息
        version_label = ctk.CTkLabel(parent, text="版本 2.1", 
                                    font=ctk.CTkFont(size=18))
        version_label.pack(pady=(0, 30))
        
        # CC-BY-NC-SA 4.0 许可协议标题
        CC_title = ctk.CTkLabel(parent, text="CC-BY-NC-SA 4.0 许可协议", 
                                font=ctk.CTkFont(size=22, weight="bold"))
        CC_title.pack(pady=(0, 15))
        
        # 创建滚动文本框用于显示CC-BY-NC-SA 4.0协议
        text_frame = ctk.CTkFrame(parent)
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 文本框
        text_widget = ctk.CTkTextbox(text_frame, 
                                   font=ctk.CTkFont(size=14, family="Consolas"),
                                   wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # CC协议内容
        CC_license = """Copyright (c) 2025 Yang Jincheng

This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

To view a copy of this license, visit:
https://creativecommons.org/licenses/by-nc-sa/4.0/


版权所有 (c) 2025 杨锦程

本作品采用知识共享署名-非商业性使用-相同方式共享 4.0 国际许可协议进行许可。

注意：如中英文版本存在歧义，以英文版本为准！

要查看此许可证的副本，请访问：
https://creativecommons.org/licenses/by-nc-sa/4.0/"""
        
        text_widget.insert("1.0", CC_license)
        text_widget.configure(state="disabled")  # 设置为只读

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0, font=('Microsoft YaHei', 20))
        self.context_menu.add_command(label="删除作业", command=self.delete_selected_from_context)
        self.context_menu.add_command(label="标记为已完成", command=self.mark_selected_from_context)
        
        # 绑定右键事件
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def delete_selected_from_context(self):
        """从右键菜单删除选中的作业"""
        self.delete_homework()

    def mark_selected_from_context(self):
        """从右键菜单标记选中的作业为已完成"""
        self.mark_as_completed()

    def update_stats(self):
        """更新统计信息"""
        display_homeworks = [hw for hw in self.homeworks if self.should_display_homework(hw)]
        total = len(display_homeworks)
        completed = len([hw for hw in display_homeworks if hw.get('status') == 'completed'])
        overdue = len([hw for hw in display_homeworks if self.get_homework_status(hw['due_date']) == 'overdue' and hw.get('status') != 'completed'])
        due_today = len([hw for hw in display_homeworks if self.get_homework_status(hw['due_date']) == 'due_today' and hw.get('status') != 'completed'])
        
        stats_text = f"总计: {total} | 已完成: {completed} | 逾期: {overdue} | 今天截止: {due_today}"
        self.stats_label.configure(text=stats_text)
    
    def add_homework(self):
        """添加新作业"""
        code = self.code_entry.get().strip()
        subject = self.subject_entry.get().strip()
        content = self.content_entry.get().strip()
        create_date = self.create_date_entry.get().strip()
        due_date = self.due_date_entry.get().strip()
        
        if not all([code, subject, content, create_date, due_date]):
            messagebox.showerror("错误", "请填写所有字段！")
            return
        
        if not self.validate_date(create_date):
            messagebox.showerror("错误", "创建日期格式不正确！请使用 DD/MM/YYYY 格式")
            return
        
        if not self.validate_date(due_date):
            messagebox.showerror("错误", "截止日期格式不正确！请使用 DD/MM/YYYY 格式")
            return
        
        for hw in self.homeworks:
            if hw["code"] == code:
                messagebox.showerror("错误", f"作业代号 '{code}' 已存在！")
                return
        
        homework = {
            "code": code,
            "subject": subject,
            "content": content,
            "create_date": create_date,
            "due_date": due_date,
            "status": "pending"
        }
        
        self.homeworks.append(homework)
        self.save_data()
        
        self.code_entry.delete(0, "end")
        self.subject_entry.delete(0, "end")
        self.content_entry.delete(0, "end")
        self.due_date_entry.delete(0, "end")
        
        messagebox.showinfo("成功", "作业添加成功！")
        self.update_stats()
        self.refresh_list()
        self.update_charts()  # 更新图表
    
    def validate_date(self, date_str):
        """验证日期格式"""
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False
    
    def query_homework(self):
        """查询作业"""
        query_date = self.query_date_entry.get().strip()
        query_type = self.query_type.get()
        
        if not self.validate_date(query_date):
            messagebox.showerror("错误", "查询日期格式不正确！请使用 DD/MM/YYYY 格式")
            return
        
        # 清空当前显示
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 根据查询类型筛选作业
        filtered_homeworks = []
        for hw in self.homeworks:
            if query_type == "due" and hw["due_date"] == query_date:
                filtered_homeworks.append(hw)
            elif query_type == "create" and hw["create_date"] == query_date:
                filtered_homeworks.append(hw)
        
        # 排序
        def sort_key(hw):
            status = self.get_homework_status(hw['due_date'])
            if hw.get('status') == 'completed':
                return (4, hw['due_date'])
            elif status == "due_today":
                return (0, hw['due_date'])
            elif status == "overdue":
                return (1, hw['due_date'])
            elif status == "due_soon":
                return (2, hw['due_date'])
            else:
                return (3, hw['due_date'])
        
        sorted_homeworks = sorted(filtered_homeworks, key=sort_key)
        
        # 显示结果
        for hw in sorted_homeworks:
            status = self.get_homework_status(hw['due_date'])
            if hw.get('status') == 'completed':
                display_status = "✅ 已完成"
            else:
                display_status = "📝 进行中" if status == "pending" else "⏰ 即将截止" if status == "due_soon" else "🔥 今天截止" if status == "due_today" else "⚠️ 逾期"
            
            item = self.tree.insert("", "end", values=(
                hw["code"], hw["subject"], hw["content"], 
                hw["create_date"], hw["due_date"], display_status
            ))
            
            # 设置颜色
            if hw.get('status') == 'completed':
                self.tree.item(item, tags=("completed",))
            elif status == "overdue":
                self.tree.item(item, tags=("overdue",))
            elif status == "due_today":
                self.tree.item(item, tags=("due_today",))
            elif status == "due_soon":
                self.tree.item(item, tags=("due_soon",))
        
        # 配置标签
        self.tree.tag_configure("completed", background="#e9ecef", foreground="#6c757d")
        self.tree.tag_configure("overdue", background="#f8d7da", foreground="#721c24")
        self.tree.tag_configure("due_today", background="#dc3545", foreground="white")
        self.tree.tag_configure("due_soon", background="#fff3cd", foreground="#856404")
        
        query_type_text = "截止" if query_type == "due" else "创建"
        new_title = f"在 {query_date} {query_type_text}的作业 (共{len(filtered_homeworks)}项)"
        self.result_title.configure(text=new_title)
    
    def refresh_list(self):
        """刷新显示所有作业"""
        # 清空当前显示
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 过滤：不显示已完成且过了截止日期的作业
        display_homeworks = [hw for hw in self.homeworks if self.should_display_homework(hw)]
        
        # 排序
        def sort_key(hw):
            status = self.get_homework_status(hw['due_date'])
            if hw.get('status') == 'completed':
                return (4, hw['due_date'])
            elif status == "due_today":
                return (0, hw['due_date'])
            elif status == "overdue":
                return (1, hw['due_date'])
            elif status == "due_soon":
                return (2, hw['due_date'])
            else:
                return (3, hw['due_date'])
        
        sorted_homeworks = sorted(display_homeworks, key=sort_key)
        
        # 显示所有作业
        for hw in sorted_homeworks:
            status = self.get_homework_status(hw['due_date'])
            if hw.get('status') == 'completed':
                display_status = "✅ 已完成"
            else:
                display_status = "📝 进行中" if status == "pending" else "⏰ 即将截止" if status == "due_soon" else "🔥 今天截止" if status == "due_today" else "⚠️ 逾期"
            
            item = self.tree.insert("", "end", values=(
                hw["code"], hw["subject"], hw["content"], 
                hw["create_date"], hw["due_date"], display_status
            ))
            
            # 设置颜色
            if hw.get('status') == 'completed':
                self.tree.item(item, tags=("completed",))
            elif status == "overdue":
                self.tree.item(item, tags=("overdue",))
            elif status == "due_today":
                self.tree.item(item, tags=("due_today",))
            elif status == "due_soon":
                self.tree.item(item, tags=("due_soon",))
        
        # 配置标签
        self.tree.tag_configure("completed", background="#e9ecef", foreground="#6c757d")
        self.tree.tag_configure("overdue", background="#f8d7da", foreground="#721c24")
        self.tree.tag_configure("due_today", background="#dc3545", foreground="white")
        self.tree.tag_configure("due_soon", background="#fff3cd", foreground="#856404")
        
        new_title = f"所有作业 (共{len(display_homeworks)}项) - 今天截止的作业已标红"
        self.result_title.configure(text=new_title)
        self.update_stats()
    
    def mark_as_completed(self):
        """标记选中的作业为已完成"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择要标记为已完成的作业！")
            return
        
        # 获取选中作业的信息
        item_values = self.tree.item(selected_item[0], "values")
        if not item_values:
            return
        
        # 更新作业状态
        code_to_update = item_values[0]
        for hw in self.homeworks:
            if hw["code"] == code_to_update:
                hw["status"] = "completed"
                break
        
        self.save_data()
        messagebox.showinfo("成功", "作业已标记为已完成！")
        self.update_stats()
        self.refresh_list()
        self.update_charts()  # 更新图表
    
    def delete_homework(self):
        """删除选中的作业"""
        selected_item = self.tree.selection()
        if len(selected_item) == 1:
            # 获取选中作业的信息
            item_values = self.tree.item(selected_item[0], "values")
            if not item_values:
                return
            
            # 确认删除
            if messagebox.askyesno("确认删除", f"确定要删除作业 '{item_values[0]} - {item_values[1]}' 吗？"):
                # 从数据中删除
                code_to_delete = item_values[0]
                self.homeworks = [hw for hw in self.homeworks if hw["code"] != code_to_delete]
                self.save_data()
                
                messagebox.showinfo("成功", "作业删除成功！")
                self.update_stats()
                self.refresh_list()
                self.update_charts()  # 更新图表
        elif len(selected_item) > 1:
            # 确认删除
            if messagebox.askyesno("确认删除", f"确定要删除 {len(selected_item)} 个作业吗？"):
                # 获取所有选中作业的代号
                codes_to_delete = []
                for item in selected_item:
                    item_values = self.tree.item(item, "values")
                    if item_values:
                        codes_to_delete.append(item_values[0])
                
                # 从数据中删除所有选中的作业
                self.homeworks = [hw for hw in self.homeworks if hw["code"] not in codes_to_delete]
                self.save_data()
                
                messagebox.showinfo("成功", f"{len(codes_to_delete)} 个作业删除成功！")
                self.update_stats()
                self.refresh_list()
                self.update_charts()  # 更新图表
        else:
            messagebox.showwarning("警告", "请先选择要删除的作业！")
    
    def clear_all_homework(self):
        """清空所有作业"""
        if not self.homeworks:
            messagebox.showinfo("提示", "已经没有作业了！")
            return
        
        if messagebox.askyesno("确认", "确定要清空所有作业吗？此操作不可恢复！"):
            self.homeworks = []
            self.save_data()
            self.update_stats()
            self.refresh_list()
            self.update_charts()  # 更新图表
            messagebox.showinfo("成功", "所有作业已清空！")

def main():
    root = ctk.CTk()
    app = HomeworkPlatform(root)
    root.mainloop()

if __name__ == "__main__":
    main()
