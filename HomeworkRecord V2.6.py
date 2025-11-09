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
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.font_manager as fm
import threading
import queue
import time
from enum import Enum

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class TaskType(Enum):
    LOAD_DATA = "load_data"
    SAVE_DATA = "save_data" 
    ADD_HOMEWORK = "add_homework"
    REFRESH_LIST = "refresh_list"
    UPDATE_CHARTS = "update_charts"
    QUERY_HOMEWORK = "query_homework"
    DELETE_HOMEWORK = "delete_homework"
    CLEAR_ALL = "clear_all"
    MARK_COMPLETED = "mark_completed"

class HomeworkPlatform:
    def __init__(self, root):
        self.root = root
        self.root.title("学生自托管作业登记平台 v2.6")
        
        # 数据文件
        self.data_file = "homework_data.json"
        
        # 默认设置
        self.settings = {
            "main_font_size": 16,
            "table_font_size": 20,
            "theme_mode": "System",
            "color_theme": "blue",
            "window_mode": "percentage",
            "window_percentage": 80,
            "window_width": 1400,
            "window_height": 900,
            "remind_days": 3,
            "chart_days": 5
        }
        
        # 线程安全的数据结构
        self.homeworks = []
        self.data_loaded = False
        
        # 统一任务队列系统
        self.task_queue = queue.Queue()
        self.current_task = None
        self.task_in_progress = False
        
        # 加载数据
        self.submit_task(TaskType.LOAD_DATA)
        
        # 应用主题设置
        ctk.set_appearance_mode(self.settings["theme_mode"])
        ctk.set_default_color_theme(self.settings["color_theme"])
        
        # 设置窗口大小
        self.apply_window_size()
        
        # 创建界面
        self.create_widgets()
        
        # 启动任务处理器
        self.process_tasks()
    
    def submit_task(self, task_type, **kwargs):
        """提交任务到队列"""
        task = {
            "type": task_type,
            "kwargs": kwargs,
            "submit_time": time.time()
        }
        self.task_queue.put(task)
        self.update_queue_status()
    
    def process_tasks(self):
        """处理任务队列的主循环"""
        try:
            # 如果没有任务在执行，且队列不为空，执行下一个任务
            if not self.task_in_progress and not self.task_queue.empty():
                task = self.task_queue.get_nowait()
                self.execute_task(task)
        except queue.Empty:
            pass
        finally:
            # 每50ms检查一次任务队列
            self.root.after(50, self.process_tasks)
    
    def execute_task(self, task):
        """执行单个任务"""
        self.task_in_progress = True
        self.current_task = task
        self.update_queue_status()
        
        task_type = task["type"]
        kwargs = task["kwargs"]
        
        
        # 根据任务类型执行相应的操作
        if task_type == TaskType.LOAD_DATA:
            self.execute_load_data()
        elif task_type == TaskType.SAVE_DATA:
            self.execute_save_data()
        elif task_type == TaskType.ADD_HOMEWORK:
            self.execute_add_homework(**kwargs)
        elif task_type == TaskType.REFRESH_LIST:
            self.execute_refresh_list()
        elif task_type == TaskType.UPDATE_CHARTS:
            self.execute_update_charts()
        elif task_type == TaskType.QUERY_HOMEWORK:
            self.execute_query_homework(**kwargs)
        elif task_type == TaskType.DELETE_HOMEWORK:
            self.execute_delete_homework(**kwargs)
        elif task_type == TaskType.CLEAR_ALL:
            self.execute_clear_all()
        elif task_type == TaskType.MARK_COMPLETED:
            self.execute_mark_completed(**kwargs)
    
    def task_completed(self):
        """任务完成回调"""
        self.task_in_progress = False
        self.current_task = None
        self.update_queue_status()
    
    def update_queue_status(self):
        """更新队列状态显示"""
        if hasattr(self, 'queue_status_label'):
            queue_size = self.task_queue.qsize()
            # 修复这里：从字典中获取type而不是直接访问value
            current_task = self.current_task["type"].value if self.current_task else "无"
            status_text = f"队列: {queue_size} | 当前: {current_task}"
            self.queue_status_label.configure(text=status_text)

    def execute_load_data(self):
        """执行加载数据任务"""
        def load_task():
            try:
                homework_data = []
                settings_updated = False
                
                if os.path.exists(self.data_file):
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and "homeworks" in data and "settings" in data:
                        self.settings.update(data["settings"])
                        homework_data = data["homeworks"]
                        settings_updated = True
                    else:
                        homework_data = data
                    
                    for hw in homework_data:
                        if 'status' not in hw:
                            hw['status'] = 'pending'
                
                # 回到主线程完成
                self.root.after(0, lambda: self.on_load_data_complete(homework_data, settings_updated))
                
            except Exception as e:
                self.root.after(0, lambda: self.on_load_data_error(str(e)))
        
        threading.Thread(target=load_task, daemon=True).start()
    
    def on_load_data_complete(self, homework_data, settings_updated):
        """数据加载完成"""
        self.homeworks = homework_data
        self.data_loaded = True
        
        if settings_updated:
            ctk.set_appearance_mode(self.settings["theme_mode"])
            ctk.set_default_color_theme(self.settings["color_theme"])
            self.apply_window_size()
        
        self.update_stats()
        self.submit_task(TaskType.REFRESH_LIST)
        self.submit_task(TaskType.UPDATE_CHARTS)
        self.task_completed()
        
        if homework_data:
            self.show_temp_message(f"成功加载 {len(homework_data)} 条作业记录")
    
    def on_load_data_error(self, error_msg):
        """数据加载错误"""
        self.homeworks = []
        self.data_loaded = True
        messagebox.showerror("加载错误", f"加载数据时出错：{error_msg}")
        self.task_completed()
    
    def execute_save_data(self):
        """执行保存数据任务"""
        def save_task():
            try:
                data = {
                    "homeworks": self.homeworks,
                    "settings": self.settings
                }
                
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                self.root.after(0, self.on_save_data_complete)
                
            except Exception as e:
                self.root.after(0, lambda: self.on_save_data_error(str(e)))
        
        threading.Thread(target=save_task, daemon=True).start()
    
    def on_save_data_complete(self):
        """保存数据完成"""
        self.task_completed()
    
    def on_save_data_error(self, error_msg):
        """保存数据错误"""
        messagebox.showerror("保存错误", f"保存数据时出错：{error_msg}")
        self.task_completed()
    
    def execute_add_homework(self, code, subject, content, create_date, due_date):
        """执行添加作业任务"""
        # 验证数据
        if not all([code, subject, content, create_date, due_date]):
            messagebox.showerror("错误", "请填写所有字段！")
            self.task_completed()
            return
        
        # 验证日期格式
        create_date_obj = self.parse_date(create_date)
        due_date_obj = self.parse_date(due_date)
        
        if not create_date_obj or not due_date_obj:
            messagebox.showerror("错误", "日期格式不正确！请使用 DD/MM/YYYY 或 D/M/YYYY 格式")
            self.task_completed()
            return
        
        # 检查重复
        for hw in self.homeworks:
            if hw["code"] == code:
                messagebox.showerror("错误", f"作业代号 '{code}' 已存在！")
                self.task_completed()
                return
        
        # 添加作业
        homework = {
            "code": code,
            "subject": subject,
            "content": content,
            "create_date": self.format_date(create_date_obj),
            "due_date": self.format_date(due_date_obj),
            "status": "pending"
        }
        
        self.homeworks.append(homework)
        
        # 清空输入框（在主线程执行）
        self.root.after(0, lambda: self.clear_input_fields())
        
        # 触发后续任务
        self.submit_task(TaskType.SAVE_DATA)
        self.submit_task(TaskType.REFRESH_LIST)
        self.submit_task(TaskType.UPDATE_CHARTS)
        
        self.show_temp_message("作业添加成功！")
        self.task_completed()
    
    def clear_input_fields(self):
        """清空输入字段"""
        self.code_entry.delete(0, "end")
        self.subject_entry.delete(0, "end")
        self.content_entry.delete(0, "end")
        self.due_date_entry.delete(0, "end")
    
    def execute_refresh_list(self):
        """执行刷新列表任务"""
        def process_data():
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
            self.root.after(0, lambda: self.update_treeview(sorted_homeworks))
        
        threading.Thread(target=process_data, daemon=True).start()
    
    def update_treeview(self, sorted_homeworks):
        """更新树形视图"""
        # 清空当前显示
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        total_count = len(sorted_homeworks)
        
        # 根据数据量决定加载方式
        if total_count > 200:
            self.incremental_update_treeview(sorted_homeworks)
        else:
            self.batch_update_treeview(sorted_homeworks)
    
    def batch_update_treeview(self, sorted_homeworks):
        """批量更新树形视图"""
        for hw in sorted_homeworks:
            self.insert_homework_item(hw)
        
        total_count = len(sorted_homeworks)
        self.result_title.configure(text=f"所有作业 (共{total_count}项) - 今天截止的作业已标红")
        self.update_stats()
        self.task_completed()
    
    def incremental_update_treeview(self, sorted_homeworks):
        """增量更新树形视图"""
        total_count = len(sorted_homeworks)
        self.result_title.configure(text=f"正在加载作业... (0/{total_count})")
        
        # 显示进度框架
        self.progress_frame = ctk.CTkFrame(self.result_frame)
        self.progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text=f"正在加载作业... (0/{total_count})")
        self.progress_label.pack()
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        # 开始增量插入
        self.incremental_insert(sorted_homeworks, 0, 50)
    
    def incremental_insert(self, homeworks, start_idx, batch_size):
        """增量插入数据"""
        total_count = len(homeworks)
        end_idx = min(start_idx + batch_size, total_count)
        
        # 插入当前批次
        for i in range(start_idx, end_idx):
            self.insert_homework_item(homeworks[i])
        
        # 更新进度
        progress = end_idx / total_count
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"正在加载作业... ({end_idx}/{total_count})")
        
        if end_idx < total_count:
            # 继续下一批
            self.root.after(1, self.incremental_insert, homeworks, end_idx, batch_size)
        else:
            # 完成
            self.progress_frame.destroy()
            self.result_title.configure(text=f"所有作业 (共{total_count}项) - 今天截止的作业已标红")
            self.update_stats()
            self.task_completed()

    def execute_update_charts(self):
        """执行更新图表任务"""
        # 直接在主线程更新图表（matplotlib需要主线程）
        self.update_pie_chart()
        self.update_line_chart()
        self.task_completed()
    
    def execute_query_homework(self, query_date, query_type):
        """执行查询作业任务"""
        query_date_obj = self.parse_date(query_date)
        if not query_date_obj:
            messagebox.showerror("错误", "查询日期格式不正确！")
            self.task_completed()
            return
        
        normalized_query = self.format_date(query_date_obj)
        
        # 清空当前显示
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filtered_homeworks = []
        for hw in self.homeworks:
            normalized_hw_date = self.normalize_date(hw["due_date"] if query_type == "due" else hw["create_date"])
            if normalized_hw_date == normalized_query:
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
        
        for hw in sorted_homeworks:
            self.insert_homework_item(hw)
        
        query_type_text = "截止" if query_type == "due" else "创建"
        new_title = f"在 {normalized_query} {query_type_text}的作业 (共{len(filtered_homeworks)}项)"
        self.result_title.configure(text=new_title)
        self.task_completed()
    
    def execute_delete_homework(self, selected_codes):
        """执行删除作业任务"""
        self.homeworks = [hw for hw in self.homeworks if hw["code"] not in selected_codes]
        self.submit_task(TaskType.SAVE_DATA)
        self.submit_task(TaskType.REFRESH_LIST)
        self.submit_task(TaskType.UPDATE_CHARTS)
        self.show_temp_message(f"{len(selected_codes)} 个作业删除成功！")
        self.task_completed()
    
    def execute_clear_all(self):
        """执行清空所有作业任务"""
        self.homeworks = []
        self.submit_task(TaskType.SAVE_DATA)
        self.submit_task(TaskType.REFRESH_LIST)
        self.submit_task(TaskType.UPDATE_CHARTS)
        self.show_temp_message("所有作业已清空！")
        self.task_completed()
    
    def execute_mark_completed(self, code):
        """执行标记完成任务"""
        for hw in self.homeworks:
            if hw["code"] == code:
                hw["status"] = "completed"
                break
        
        self.submit_task(TaskType.SAVE_DATA)
        self.submit_task(TaskType.REFRESH_LIST)
        self.submit_task(TaskType.UPDATE_CHARTS)
        self.show_temp_message("作业已标记为已完成！")
        self.task_completed()

    # ========== 用户交互方法 ==========
    def add_homework(self):
        """添加新作业 - 用户交互方法"""
        code = self.code_entry.get().strip()
        subject = self.subject_entry.get().strip()
        content = self.content_entry.get().strip()
        create_date = self.create_date_entry.get().strip()
        due_date = self.due_date_entry.get().strip()
        
        self.submit_task(TaskType.ADD_HOMEWORK, 
                        code=code, subject=subject, content=content,
                        create_date=create_date, due_date=due_date)
    
    def refresh_list(self):
        """刷新列表 - 用户交互方法"""
        self.submit_task(TaskType.REFRESH_LIST)
    
    def query_homework(self):
        """查询作业 - 用户交互方法"""
        query_date = self.query_date_entry.get().strip()
        query_type = self.query_type.get()
        self.submit_task(TaskType.QUERY_HOMEWORK, 
                        query_date=query_date, query_type=query_type)
    
    def delete_homework(self):
        """删除作业 - 用户交互方法"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择要删除的作业！")
            return
        
        codes_to_delete = []
        for item in selected_item:
            item_values = self.tree.item(item, "values")
            if item_values:
                codes_to_delete.append(item_values[0])
        
        if not codes_to_delete:
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除 {len(codes_to_delete)} 个作业吗？"):
            self.submit_task(TaskType.DELETE_HOMEWORK, selected_codes=codes_to_delete)
    
    def mark_as_completed(self):
        """标记完成 - 用户交互方法"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择要标记为已完成的作业！")
            return
        
        item_values = self.tree.item(selected_item[0], "values")
        if not item_values:
            return
        
        code_to_update = item_values[0]
        self.submit_task(TaskType.MARK_COMPLETED, code=code_to_update)
    
    def clear_all_homework(self):
        """清空所有作业 - 用户交互方法"""
        if not self.homeworks:
            messagebox.showinfo("提示", "已经没有作业了！")
            return
        
        if messagebox.askyesno("确认", "确定要清空所有作业吗？此操作不可恢复！"):
            self.submit_task(TaskType.CLEAR_ALL)

    # ========== 界面构建方法 ==========
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 创建选项卡
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # 创建主要功能选项卡
        self.main_tab = self.tabview.add("作业管理")
        self.chart_tab = self.tabview.add("图表")
        self.settings_tab = self.tabview.add("设置")
        self.about_tab = self.tabview.add("关于")
        
        # 设置默认选中的选项卡
        self.tabview.set("作业管理")
        
        # 在主选项卡中构建原来的界面
        self.build_main_tab(self.main_tab)
        
        # 在图表选项卡中构建图表
        self.build_chart_tab(self.chart_tab)
        
        # 在设置选项卡中构建设置内容
        self.build_settings_tab(self.settings_tab)
        
        # 在关于选项卡中构建关于内容
        self.build_about_tab(self.about_tab)

    def build_main_tab(self, parent):
        """构建主选项卡内容"""
        # 创建顶部框架（标题和统计信息）
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))
        
        # 标题
        title_label = ctk.CTkLabel(top_frame, text="作业登记平台 v2.6", 
                                  font=ctk.CTkFont(size=32, weight="bold"))
        title_label.pack(pady=(0, 10))
        
        # 队列状态显示
        self.queue_status_label = ctk.CTkLabel(top_frame, text="队列: 0 | 当前: 无", 
                                             font=ctk.CTkFont(size=14),
                                             text_color="#6c757d")
        self.queue_status_label.pack()
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(top_frame, text="正在初始化...", 
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
        
        # 第一行：作业代号和科目
        row1_frame = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        row1_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(row1_frame, text="作业代号:", 
                    font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(side="left", padx=(0, 5))
        self.code_entry = ctk.CTkEntry(row1_frame, width=120, font=ctk.CTkFont(size=self.settings["main_font_size"]))
        self.code_entry.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(row1_frame, text="科目:", 
                    font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(side="left", padx=(0, 5))
        self.subject_entry = ctk.CTkEntry(row1_frame, width=120, font=ctk.CTkFont(size=self.settings["main_font_size"]))
        self.subject_entry.pack(side="left", padx=(0, 20))
        
        # 第二行：作业内容
        row2_frame = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        row2_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(row2_frame, text="作业内容:", 
                    font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(side="left", padx=(0, 5))
        self.content_entry = ctk.CTkEntry(row2_frame, font=ctk.CTkFont(size=self.settings["main_font_size"]))
        self.content_entry.pack(side="left", fill="x", expand=True, padx=(0, 0))
        
        # 第三行：日期和按钮
        row3_frame = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        row3_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(row3_frame, text="创建日期:", 
                    font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(side="left", padx=(0, 5))
        self.create_date_entry = ctk.CTkEntry(row3_frame, width=100, font=ctk.CTkFont(size=self.settings["main_font_size"]))
        self.create_date_entry.pack(side="left", padx=(0, 20))
        self.create_date_entry.insert(0, self.format_date(datetime.now()))
        
        ctk.CTkLabel(row3_frame, text="截止日期:", 
                    font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(side="left", padx=(0, 5))
        self.due_date_entry = ctk.CTkEntry(row3_frame, width=100, font=ctk.CTkFont(size=self.settings["main_font_size"]))
        self.due_date_entry.pack(side="left", padx=(0, 20))
        
        # 添加按钮
        ctk.CTkButton(self.add_frame, text="添加作业", command=self.add_homework,
                      height=35, font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(pady=(0, 15))
        
        # 查询部分
        self.query_frame = ctk.CTkFrame(left_frame)
        self.query_frame.pack(fill="x", pady=(0, 15))
        
        query_row1 = ctk.CTkFrame(self.query_frame, fg_color="transparent")
        query_row1.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(query_row1, text="查询日期:", 
                    font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(side="left", padx=(0, 5))
        self.query_date_entry = ctk.CTkEntry(query_row1, width=100, font=ctk.CTkFont(size=self.settings["main_font_size"]))
        self.query_date_entry.pack(side="left", padx=(0, 20))
        self.query_date_entry.insert(0, self.format_date(datetime.now()))
        
        # 查询类型
        self.query_type = ctk.StringVar(value="due")
        ctk.CTkRadioButton(query_row1, text="按截止日期查询", 
                          variable=self.query_type, value="due",
                          font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(side="left", padx=(20, 10))
        ctk.CTkRadioButton(query_row1, text="按创建日期查询", 
                          variable=self.query_type, value="create",
                          font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(side="left", padx=(10, 0))
        
        # 查询按钮
        ctk.CTkButton(self.query_frame, text="查询作业", command=self.query_homework,
                      height=35, font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(pady=(0, 15))
        
        # 操作按钮框架
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", pady=(0, 0))
        
        ctk.CTkButton(button_frame, text="删除选中作业", command=self.delete_homework,
                      height=35, font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(button_frame, text="标记为已完成", command=self.mark_as_completed,
                      height=35, font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(button_frame, text="清空所有作业", command=self.clear_all_homework,
                      height=35, font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(button_frame, text="刷新列表", command=self.refresh_list,
                      height=35, font=ctk.CTkFont(size=self.settings["main_font_size"])).pack(fill="x", padx=10, pady=5)
        
        # 右侧表格框架
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # 结果显示区域
        self.result_frame = ctk.CTkFrame(right_frame)
        self.result_frame.pack(fill="both", expand=True)
        
        # 结果标题
        self.result_title = ctk.CTkLabel(self.result_frame, text="正在初始化...", 
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
                        font=('Microsoft YaHei', self.settings["table_font_size"]),
                        rowheight=45)
        
        style.configure("Custom.Treeview.Heading",
                        background="#e9ecef",
                        foreground="black",
                        relief="raised",
                        font=('Microsoft YaHei', self.settings["table_font_size"]+2, 'bold'))
        
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
        
        # 初始显示加载状态
        self.update_stats()

    def build_settings_tab(self, parent):
        """构建设置选项卡内容"""
        # 标题
        title_label = ctk.CTkLabel(parent, text="应用设置", 
                                  font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(20, 30))
        
        # 创建滚动框架
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 字号设置框架
        font_frame = ctk.CTkFrame(scroll_frame)
        font_frame.pack(fill="x", pady=(0, 20))
        
        font_title = ctk.CTkLabel(font_frame, text="字号设置", 
                                 font=ctk.CTkFont(size=22, weight="bold"))
        font_title.pack(pady=(15, 20))
        
        # 主界面字号设置
        main_font_frame = ctk.CTkFrame(font_frame, fg_color="transparent")
        main_font_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(main_font_frame, text="主界面字号:", 
                    font=ctk.CTkFont(size=18)).pack(side="left")
        
        self.main_font_size_var = ctk.IntVar(value=self.settings["main_font_size"])
        main_font_slider = ctk.CTkSlider(main_font_frame, from_=12, to=24, number_of_steps=12,
                                        variable=self.main_font_size_var, command=self.on_main_font_slider_change)
        main_font_slider.pack(side="left", fill="x", expand=True, padx=20)
        
        self.main_font_size_label = ctk.CTkLabel(main_font_frame, text=str(self.settings["main_font_size"]),
                                               font=ctk.CTkFont(size=18, weight="bold"))
        self.main_font_size_label.pack(side="left", padx=(0, 10))
        
        # 表格字号设置
        table_font_frame = ctk.CTkFrame(font_frame, fg_color="transparent")
        table_font_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(table_font_frame, text="表格字号:", 
                    font=ctk.CTkFont(size=18)).pack(side="left")
        
        self.table_font_size_var = ctk.IntVar(value=self.settings["table_font_size"])
        table_font_slider = ctk.CTkSlider(table_font_frame, from_=16, to=28, number_of_steps=12,
                                         variable=self.table_font_size_var, command=self.on_table_font_slider_change)
        table_font_slider.pack(side="left", fill="x", expand=True, padx=20)
        
        self.table_font_size_label = ctk.CTkLabel(table_font_frame, text=str(self.settings["table_font_size"]),
                                                font=ctk.CTkFont(size=18, weight="bold"))
        self.table_font_size_label.pack(side="left", padx=(0, 10))
        
        # 主题设置框架
        theme_frame = ctk.CTkFrame(scroll_frame)
        theme_frame.pack(fill="x", pady=(0, 20))
        
        theme_title = ctk.CTkLabel(theme_frame, text="主题设置", 
                                  font=ctk.CTkFont(size=22, weight="bold"))
        theme_title.pack(pady=(15, 20))
        
        # 主题模式设置
        theme_mode_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_mode_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(theme_mode_frame, text="主题模式:", 
                    font=ctk.CTkFont(size=18)).pack(side="left")
        
        self.theme_mode_var = ctk.StringVar(value=self.settings["theme_mode"])
        theme_modes = ["Light", "Dark", "System"]
        theme_option = ctk.CTkOptionMenu(theme_mode_frame, values=theme_modes,
                                        variable=self.theme_mode_var,
                                        font=ctk.CTkFont(size=16))
        theme_option.pack(side="left", padx=20)
        
        # 颜色主题设置
        color_theme_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        color_theme_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(color_theme_frame, text="颜色主题:", 
                    font=ctk.CTkFont(size=18)).pack(side="left")
        
        self.color_theme_var = ctk.StringVar(value=self.settings["color_theme"])
        color_themes = ["blue", "green", "dark-blue"]
        color_option = ctk.CTkOptionMenu(color_theme_frame, values=color_themes,
                                        variable=self.color_theme_var,
                                        font=ctk.CTkFont(size=16))
        color_option.pack(side="left", padx=20)
        
        # 窗口大小设置框架
        window_frame = ctk.CTkFrame(scroll_frame)
        window_frame.pack(fill="x", pady=(0, 20))
        
        window_title = ctk.CTkLabel(window_frame, text="窗口大小设置", 
                                   font=ctk.CTkFont(size=22, weight="bold"))
        window_title.pack(pady=(15, 20))
        
        # 窗口模式设置
        window_mode_frame = ctk.CTkFrame(window_frame, fg_color="transparent")
        window_mode_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(window_mode_frame, text="窗口模式:", 
                    font=ctk.CTkFont(size=18)).pack(side="left")
        
        self.window_mode_var = ctk.StringVar(value=self.settings["window_mode"])
        window_modes = ["percentage", "pixel"]
        window_mode_option = ctk.CTkOptionMenu(window_mode_frame, values=window_modes,
                                              variable=self.window_mode_var,
                                              font=ctk.CTkFont(size=16),
                                              command=self.on_window_mode_change)
        window_mode_option.pack(side="left", padx=20)
        
        # 百分比模式设置
        self.percentage_frame = ctk.CTkFrame(window_frame, fg_color="transparent")
        self.percentage_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.percentage_frame, text="窗口大小百分比:", 
                    font=ctk.CTkFont(size=18)).pack(side="left")
        
        self.window_percentage_var = ctk.IntVar(value=self.settings["window_percentage"])
        percentage_slider = ctk.CTkSlider(self.percentage_frame, from_=50, to=95, number_of_steps=45,
                                         variable=self.window_percentage_var, command=self.on_percentage_slider_change)
        percentage_slider.pack(side="left", fill="x", expand=True, padx=20)
        
        self.percentage_label = ctk.CTkLabel(self.percentage_frame, text=f"{self.settings['window_percentage']}%",
                                           font=ctk.CTkFont(size=18, weight="bold"))
        self.percentage_label.pack(side="left", padx=(0, 10))
        
        # 像素模式设置
        self.pixel_frame = ctk.CTkFrame(window_frame, fg_color="transparent")
        if self.settings["window_mode"] != "pixel":
            self.pixel_frame.pack_forget()
        
        pixel_row1 = ctk.CTkFrame(self.pixel_frame, fg_color="transparent")
        pixel_row1.pack(fill="x", pady=5)
        
        ctk.CTkLabel(pixel_row1, text="窗口宽度:", 
                    font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        self.width_entry = ctk.CTkEntry(pixel_row1, width=80, font=ctk.CTkFont(size=16))
        self.width_entry.pack(side="left", padx=(0, 20))
        self.width_entry.insert(0, str(self.settings["window_width"]))
        ctk.CTkLabel(pixel_row1, text="px", 
                    font=ctk.CTkFont(size=16)).pack(side="left")
        
        pixel_row2 = ctk.CTkFrame(self.pixel_frame, fg_color="transparent")
        pixel_row2.pack(fill="x", pady=5)
        
        ctk.CTkLabel(pixel_row2, text="窗口高度:", 
                    font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        self.height_entry = ctk.CTkEntry(pixel_row2, width=80, font=ctk.CTkFont(size=16))
        self.height_entry.pack(side="left", padx=(0, 20))
        self.height_entry.insert(0, str(self.settings["window_height"]))
        ctk.CTkLabel(pixel_row2, text="px", 
                    font=ctk.CTkFont(size=16)).pack(side="left")
        
        # 功能设置框架
        function_frame = ctk.CTkFrame(scroll_frame)
        function_frame.pack(fill="x", pady=(0, 20))
        
        function_title = ctk.CTkLabel(function_frame, text="功能设置", 
                                     font=ctk.CTkFont(size=22, weight="bold"))
        function_title.pack(pady=(15, 20))
        
        # 提醒天数设置
        remind_frame = ctk.CTkFrame(function_frame, fg_color="transparent")
        remind_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(remind_frame, text="提前提醒天数:", 
                    font=ctk.CTkFont(size=18)).pack(side="left")
        
        self.remind_days_var = ctk.IntVar(value=self.settings["remind_days"])
        remind_slider = ctk.CTkSlider(remind_frame, from_=1, to=7, number_of_steps=6,
                                     variable=self.remind_days_var, command=self.on_remind_days_slider_change)
        remind_slider.pack(side="left", fill="x", expand=True, padx=20)
        
        self.remind_days_label = ctk.CTkLabel(remind_frame, text=str(self.settings["remind_days"]),
                                             font=ctk.CTkFont(size=18, weight="bold"))
        self.remind_days_label.pack(side="left", padx=(0, 10))
        
        # 图表天数设置
        chart_frame = ctk.CTkFrame(function_frame, fg_color="transparent")
        chart_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(chart_frame, text="图表显示天数:", 
                    font=ctk.CTkFont(size=18)).pack(side="left")
        
        self.chart_days_var = ctk.IntVar(value=self.settings["chart_days"])
        chart_slider = ctk.CTkSlider(chart_frame, from_=3, to=14, number_of_steps=11,
                                    variable=self.chart_days_var, command=self.on_chart_days_slider_change)
        chart_slider.pack(side="left", fill="x", expand=True, padx=20)
        
        self.chart_days_label = ctk.CTkLabel(chart_frame, text=str(self.settings["chart_days"]),
                                           font=ctk.CTkFont(size=18, weight="bold"))
        self.chart_days_label.pack(side="left", padx=(0, 10))
        
        # 应用设置按钮
        apply_button = ctk.CTkButton(scroll_frame, text="应用所有设置", command=self.apply_all_settings,
                                    height=40, font=ctk.CTkFont(size=18, weight="bold"))
        apply_button.pack(pady=30)
        
        # 提示信息
        hint_label = ctk.CTkLabel(scroll_frame, 
                                 text="注意：部分设置需要重启程序才能完全生效",
                                 font=ctk.CTkFont(size=14),
                                 text_color="#ff6b6b")
        hint_label.pack(pady=(0, 15))

    def build_chart_tab(self, parent):
        """构建图表选项卡内容"""
        # 标题
        title_label = ctk.CTkLabel(parent, text="作业统计图表", 
                                  font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # 刷新按钮
        refresh_button = ctk.CTkButton(parent, text="刷新图表", command=lambda: self.submit_task(TaskType.UPDATE_CHARTS),
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
        
        line_title = ctk.CTkLabel(line_frame, text=f"最近{self.settings['chart_days']}天作业量统计", 
                                 font=ctk.CTkFont(size=20, weight="bold"))
        line_title.pack(pady=10)
        
        # 折线图画布
        self.line_fig = Figure(figsize=(10, 6), dpi=100)
        self.line_canvas = FigureCanvasTkAgg(self.line_fig, line_frame)
        self.line_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # 初始显示空图表
        self.update_pie_chart()
        self.update_line_chart()

    def build_about_tab(self, parent):
        """构建关于选项卡内容"""
        # 标题
        title_label = ctk.CTkLabel(parent, text="作业登记平台 v2.6", 
                                  font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # 版本信息
        version_label = ctk.CTkLabel(parent, text="版本 2.6 - 高性能优化版", 
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
Deed:
https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en

版权所有 (c) 2025 杨锦程

本作品采用知识共享署名-非商业性使用-相同方式共享 4.0 国际许可协议进行许可。

注意：如中英文版本存在歧义，以英文版本为准！

要查看此许可证的副本，请访问：
https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans
摘要：
https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.zh-hans"""
        
        text_widget.insert("1.0", CC_license)
        text_widget.configure(state="disabled")

    # ========== 设置相关的回调方法 ==========
    def on_window_mode_change(self, value):
        if value == "percentage":
            self.pixel_frame.pack_forget()
            self.percentage_frame.pack(fill="x", padx=20, pady=10)
        else:
            self.percentage_frame.pack_forget()
            self.pixel_frame.pack(fill="x", padx=20, pady=10)

    def on_percentage_slider_change(self, value):
        self.percentage_label.configure(text=f"{int(value)}%")

    def on_main_font_slider_change(self, value):
        self.main_font_size_label.configure(text=str(int(value)))

    def on_table_font_slider_change(self, value):
        self.table_font_size_label.configure(text=str(int(value)))

    def on_remind_days_slider_change(self, value):
        self.remind_days_label.configure(text=str(int(value)))

    def on_chart_days_slider_change(self, value):
        self.chart_days_label.configure(text=str(int(value)))

    def apply_all_settings(self):
        """应用所有设置"""
        try:
            self.settings["main_font_size"] = self.main_font_size_var.get()
            self.settings["table_font_size"] = self.table_font_size_var.get()
            self.settings["theme_mode"] = self.theme_mode_var.get()
            self.settings["color_theme"] = self.color_theme_var.get()
            self.settings["window_mode"] = self.window_mode_var.get()
            self.settings["window_percentage"] = self.window_percentage_var.get()
            self.settings["remind_days"] = self.remind_days_var.get()
            self.settings["chart_days"] = self.chart_days_var.get()
            
            if self.settings["window_mode"] == "pixel":
                try:
                    self.settings["window_width"] = int(self.width_entry.get())
                    self.settings["window_height"] = int(self.height_entry.get())
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的宽度和高度数值！")
                    return
            
            self.submit_task(TaskType.SAVE_DATA)
            
            ctk.set_appearance_mode(self.settings["theme_mode"])
            ctk.set_default_color_theme(self.settings["color_theme"])
            self.apply_window_size()
            
            result = messagebox.askyesno(
                "设置已保存", 
                "设置已保存！\n\n部分设置需要重启程序才能完全生效。\n\n是否现在重启软件？",
                detail="点击'是'立即重启软件，点击'否'继续使用当前会话"
            )
            
            if result:
                self.root.destroy()
                os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            messagebox.showerror("错误", f"保存设置时出错：{str(e)}")

    # ========== 图表更新方法 ==========
    def update_pie_chart(self):
        """更新饼图"""
        self.pie_fig.clear()
        
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
        
        labels = []
        sizes = []
        colors = []
        
        if status_counts['completed'] > 0:
            labels.append('已完成')
            sizes.append(status_counts['completed'])
            colors.append('#28a745')
        
        if status_counts['overdue'] > 0:
            labels.append('逾期')
            sizes.append(status_counts['overdue'])
            colors.append('#dc3545')
        
        if status_counts['due_today'] > 0:
            labels.append('今天截止')
            sizes.append(status_counts['due_today'])
            colors.append('#fd7e14')
        
        if status_counts['due_soon'] > 0:
            labels.append('即将截止')
            sizes.append(status_counts['due_soon'])
            colors.append('#ffc107')
        
        if status_counts['pending'] > 0:
            labels.append('进行中')
            sizes.append(status_counts['pending'])
            colors.append('#007bff')
        
        if not sizes:
            ax = self.pie_fig.add_subplot(111)
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=16)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        else:
            ax = self.pie_fig.add_subplot(111)
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                            startangle=90, textprops={'fontsize': 12})
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title('作业状态分布', fontsize=16, fontweight='bold')
            ax.axis('equal')
        
        self.pie_canvas.draw()

    def update_line_chart(self):
        """更新折线图"""
        self.line_fig.clear()
        
        days = self.settings["chart_days"]
        today = datetime.now()
        dates = []
        for i in range(days-1, -1, -1):
            date_obj = today - timedelta(days=i)
            dates.append(self.format_date(date_obj))
        
        create_counts = [0] * days
        due_counts = [0] * days
        
        for hw in self.homeworks:
            normalized_create = self.normalize_date(hw['create_date'])
            normalized_due = self.normalize_date(hw['due_date'])
            
            for i, date in enumerate(dates):
                if normalized_create == date:
                    create_counts[i] += 1
            
            for i, date in enumerate(dates):
                if normalized_due == date:
                    due_counts[i] += 1
        
        ax = self.line_fig.add_subplot(111)
        line1, = ax.plot(range(days), create_counts, marker='o', linewidth=2, label='创建作业', color='#007bff')
        line2, = ax.plot(range(days), due_counts, marker='s', linewidth=2, label='截止作业', color='#dc3545')
        
        ax.set_title(f'最近{days}天作业量统计', fontsize=16, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('作业数量', fontsize=12)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        
        ax.set_xticks(range(days))
        ax.set_xticklabels(dates, rotation=45)
        
        for i, (create, due) in enumerate(zip(create_counts, due_counts)):
            if create > 0:
                ax.annotate(str(create), (i, create), textcoords="offset points", 
                           xytext=(0,10), ha='center', fontsize=10, fontweight='bold')
            if due > 0:
                ax.annotate(str(due), (i, due), textcoords="offset points", 
                           xytext=(0,-15), ha='center', fontsize=10, fontweight='bold')
        
        ax.set_ylim(bottom=0)
        self.line_fig.tight_layout()
        self.line_canvas.draw()

    # ========== 辅助方法 ==========
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0, font=('Microsoft YaHei', 20))
        self.context_menu.add_command(label="删除作业", command=self.delete_homework)
        self.context_menu.add_command(label="标记为已完成", command=self.mark_as_completed)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def show_temp_message(self, message, duration=2000):
        """显示临时消息"""
        if hasattr(self, 'temp_message_label'):
            self.temp_message_label.destroy()
        
        self.temp_message_label = ctk.CTkLabel(self.root, text=message, 
                                              font=ctk.CTkFont(size=14),
                                              fg_color="#d4edda", text_color="#155724",
                                              corner_radius=5)
        self.temp_message_label.place(relx=0.5, rely=0.1, anchor="center")
        self.root.after(duration, self.temp_message_label.destroy)

    def apply_window_size(self):
        """应用窗口大小设置"""
        if self.settings["window_mode"] == "percentage":
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            percentage = self.settings["window_percentage"] / 100.0
            width = int(screen_width * percentage)
            height = int(screen_height * percentage)
            self.settings["window_width"] = width
            self.settings["window_height"] = height
        else:
            width = self.settings["window_width"]
            height = self.settings["window_height"]
        
        self.root.geometry(f"{width}x{height}")

    def insert_homework_item(self, hw):
        """插入单个作业项到树形视图"""
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

    def update_stats(self):
        """更新统计信息"""
        if not self.data_loaded:
            self.stats_label.configure(text="数据加载中...")
            return
            
        display_homeworks = [hw for hw in self.homeworks if self.should_display_homework(hw)]
        total = len(display_homeworks)
        completed = len([hw for hw in display_homeworks if hw.get('status') == 'completed'])
        overdue = len([hw for hw in display_homeworks if self.get_homework_status(hw['due_date']) == 'overdue' and hw.get('status') != 'completed'])
        due_today = len([hw for hw in display_homeworks if self.get_homework_status(hw['due_date']) == 'due_today' and hw.get('status') != 'completed'])
        
        stats_text = f"总计: {total} | 已完成: {completed} | 逾期: {overdue} | 今天截止: {due_today}"
        self.stats_label.configure(text=stats_text)

    def parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str:
            return None
            
        date_str = date_str.strip()
        formats = ["%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        parts = date_str.replace('-', '/').split('/')
        if len(parts) == 3:
            try:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                if year < 100: year += 2000
                if 1 <= day <= 31 and 1 <= month <= 12:
                    return datetime(year, month, day)
            except (ValueError, IndexError):
                pass
        
        return None

    def format_date(self, date_obj):
        return date_obj.strftime("%d/%m/%Y")

    def normalize_date(self, date_str):
        date_obj = self.parse_date(date_str)
        return self.format_date(date_obj) if date_obj else date_str

    def get_homework_status(self, due_date):
        try:
            due = self.parse_date(due_date)
            if not due: return "pending"
                
            today = datetime.now()
            due_date_only, today_date_only = due.date(), today.date()
            
            if due_date_only < today_date_only: return "overdue"
            elif due_date_only == today_date_only: return "due_today"
            elif (due_date_only - today_date_only).days <= self.settings["remind_days"]: return "due_soon"
            else: return "pending"
        except: return "pending"

    def should_display_homework(self, hw):
        if hw.get('status') == 'completed':
            try:
                due_date = self.parse_date(hw['due_date'])
                return due_date.date() >= datetime.now().date()
            except: return True
        return True

def main():
    root = ctk.CTk()
    app = HomeworkPlatform(root)
    root.mainloop()

if __name__ == "__main__":
    main()
