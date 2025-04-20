from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QPushButton, QLabel, QSlider,
    QVBoxLayout, QHBoxLayout, QMenuBar, QStatusBar, QGroupBox, QAction,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from controller import Controller

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CBCT图像处理软件")
        self.resize(1600, 1000)

        # ========== 中央布局 ==========
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # ========== 左侧三块结构 ==========
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_panel.setMinimumWidth(280)
        self.main_layout.addWidget(self.left_panel)

        # ➤ 上：快捷工具按钮区
        self.tool_group = QGroupBox("快捷工具")
        self.tool_layout = QGridLayout(self.tool_group)#网格布局
        self.tool_buttons = {}

        tool_names = ["加载DICOM", "平移", "旋转", "一键复位", "图像增强", "分割", "保存", "距离测量"]
        for idx, name in enumerate(tool_names):
            btn = QPushButton(name)
            btn.setMinimumHeight(24)
            row, col = divmod(idx, 2)
            self.tool_layout.addWidget(btn, row, col)
            self.tool_buttons[name] = btn

        self.left_layout.addWidget(self.tool_group, 1)

        # ➤ 中：直方图区域（替代“当前模式”）
        self.hist_group = QGroupBox("直方图")
        self.hist_layout = QVBoxLayout(self.hist_group)

        self.hist_source_box = QComboBox()
        self.hist_source_box.addItems(["Axial", "Sagittal", "Coronal", "Whole"])
        self.hist_layout.addWidget(self.hist_source_box)

        self.hist_canvas = FigureCanvas(Figure(figsize=(3, 2)))
        self.hist_ax = self.hist_canvas.figure.subplots()
        self.hist_layout.addWidget(self.hist_canvas)

        self.left_layout.addWidget(self.hist_group, 1)

        # ➤ 下：DICOM信息展示表格
        self.info_group = QGroupBox("图像信息")
        self.info_layout = QVBoxLayout(self.info_group)

        self.info_table = QTableWidget()
        self.info_table.setColumnCount(2)
        self.info_table.setHorizontalHeaderLabels(["标签", "值"])
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.horizontalHeader().setStretchLastSection(True)
        self.info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.info_table.setShowGrid(True)
        self.info_table.setAlternatingRowColors(True)
        self.info_table.setWordWrap(True)
        self.info_table.setColumnWidth(0, 120)
        self.info_layout.addWidget(self.info_table)

        self.left_layout.addWidget(self.info_group, 1)

        # ========== 中部视图区 ==========
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)

        self.axialWidget = QVTKRenderWindowInteractor()
        self.axialBar = QSlider(Qt.Vertical)
        self.axialBar.setEnabled(True)

        self.sagittalWidget = QVTKRenderWindowInteractor()
        self.sagittalBar = QSlider(Qt.Vertical)
        self.sagittalBar.setEnabled(True)

        self.coronalWidget = QVTKRenderWindowInteractor()
        self.coronalBar = QSlider(Qt.Vertical)
        self.coronalBar.setEnabled(True)


        self.grid_layout.addWidget(self.axialWidget,    0, 0)
        self.grid_layout.addWidget(self.axialBar,       0, 1)
        self.grid_layout.addWidget(self.sagittalWidget, 0, 2)
        self.grid_layout.addWidget(self.sagittalBar,    0, 3)

        self.threeDWidget = QVTKRenderWindowInteractor()

        self.grid_layout.addWidget(self.coronalWidget, 1, 0)
        self.grid_layout.addWidget(self.coronalBar, 1, 1)
        self.grid_layout.addWidget(self.threeDWidget, 1, 2)

        self.main_layout.addWidget(self.grid_widget, 10)

        # ========== 顶部菜单栏 ==========
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("文件")
        edit_menu = menu_bar.addMenu("编辑")
        ortho_menu = menu_bar.addMenu("正畸")
        fusion_menu = menu_bar.addMenu("融合")
        segment_menu = menu_bar.addMenu("分割")
        help_menu = menu_bar.addMenu("帮助")
        self.openOrthoAction = QAction("打开", self)
        self.ortho_help_action = QAction("帮助", self)
        ortho_menu.addAction(self.openOrthoAction)
        ortho_menu.addAction(self.ortho_help_action)

        self.openFileAction = QAction("打开文件", self)
        file_menu.addAction(self.openFileAction)

        # ========== 状态栏 ==========
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # ========== 控制器绑定 ==========
        self.controller = Controller(self)
