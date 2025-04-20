from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from image_io import read_dicom_series
from visualization import show_views_with_slider, update_slice, update_status_bar, enable_measurement
from test_debug import handle_test_button
from transform_dialog import TransformDialog
from image_ops import translate_3d, rotate_3d
from histogram_utils import draw_histogram
from enhancement_utils import apply_image_enhancement
from segmentation_utils import segment
from orthodontic_processor import OrthodonticProcessor
import vtk
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from image_ops import euler_angles_to_rotation_matrix, rotate_3d_image

class RotationWorker(QThread):
    finishing = pyqtSignal(np.ndarray)

    def __init__(self, array, angles):
        super().__init__()
        self.array = array
        self.angles = angles

    def running(self):
        try:
            R = euler_angles_to_rotation_matrix(self.angles)
            result = rotate_3d_image(self.array, R)
            self.finishing.emit(result)
        except Exception as e:
            print("[旋转线程] 错误:", str(e))

class Controller:
    def __init__(self, ui):
        self.ui = ui
        self.image = None
        self.array = None
        self.metadata = None
        self.measurement_enabled = False
        self.orthodontic = OrthodonticProcessor(self.ui)
        self.rotation_angle = 0.0  # 默认角度

        # 菜单栏“打开文件”
        self.ui.openFileAction.triggered.connect(self.load_dicom)
        self.ui.openOrthoAction.triggered.connect(self.load_orthodontic_dicom)

        # 滑块响应
        self.ui.axialBar.valueChanged.connect(lambda val: self.update_from_slider('axial', val))
        self.ui.sagittalBar.valueChanged.connect(lambda val: self.update_from_slider('sagittal', val))
        self.ui.coronalBar.valueChanged.connect(lambda val: self.update_from_slider('coronal', val))

        # 快捷按钮
        self.ui.tool_buttons["加载DICOM"].clicked.connect(self.load_dicom)
        self.ui.tool_buttons["平移"].clicked.connect(self.show_translation_dialog)
        self.ui.tool_buttons["旋转"].clicked.connect(self.show_rotation_dialog)
        self.ui.tool_buttons["距离测量"].clicked.connect(self.toggle_measurement_mode)
        self.ui.tool_buttons["分割"].clicked.connect(self.start_segmentation)
        self.ui.tool_buttons["一键复位"].clicked.connect(self.reset_view)
        self.ui.tool_buttons["图像增强"].clicked.connect(lambda: apply_image_enhancement(self.ui))

    def load_dicom(self):
        folder = QFileDialog.getExistingDirectory(None, "选择DICOM文件夹")
        if folder:
            try:
                self.image, self.array, self.metadata = read_dicom_series(folder, return_numpy=True)
                show_views_with_slider(self.array, self.ui, self.image)
                renderer = vtk.vtkRenderer()
                renderer.SetBackground(0.0, 0.0, 0.0)
                self.ui.threeDWidget.GetRenderWindow().AddRenderer(renderer)
                self.ui.threeDWidget.GetRenderWindow().Render()
                self.display_dicom_info()
                self.update_histogram()
            except Exception as e:
                QMessageBox.warning(self.ui, "错误", f"加载DICOM失败:\n{str(e)}")

    def load_orthodontic_dicom(self):
        print("[正畸] 加载正畸图像")
        success = self.orthodontic.load_second_image()
        if success:
            self.orthodontic.apply_overlay()
        else:
            print("[正畸] 加载失败或被用户取消")

    def display_dicom_info(self):
        if not self.metadata:
            return

        self.ui.info_table.clearContents()

        basic = self.metadata.get("基本信息", {})
        all_tags = self.metadata.get("全部DICOM标签", {})
        basic.pop("患者姓名", None)
        basic.pop("患者ID", None)

        rows = []
        rows.append(("【基本信息】", ""))
        for key, val in basic.items():
            rows.append((key, val))
        rows.append(("【详细DICOM标签】", ""))
        for tag, val in all_tags.items():
            if tag in basic:
                continue
            short_val = val if len(val) < 100 else val[:100] + "..."
            rows.append((tag, short_val))

        self.ui.info_table.setRowCount(len(rows))
        self.ui.info_table.setColumnCount(2)
        self.ui.info_table.setHorizontalHeaderLabels(["标签", "值"])
        for row_idx, (key, val) in enumerate(rows):
            self.ui.info_table.setItem(row_idx, 0, QTableWidgetItem(str(key)))
            self.ui.info_table.setItem(row_idx, 1, QTableWidgetItem(str(val)))
        self.ui.info_table.resizeRowsToContents()
        self.ui.info_table.resizeColumnsToContents()

    def update_from_slider(self, orientation, index):
        update_slice(self.array, self.ui, orientation, index, sitk_image=self.image)
        update_status_bar(self.ui)
    # def update_from_slider(self, orientation, index):
    #     if self.array is None:
    #         return
    #
    #     # 先更新当前方向
    #     update_slice(self.array, self.ui, orientation, index, sitk_image=self.image)
    #
    #     # 记录所有方向
    #     directions = ["axial", "sagittal", "coronal"]
    #     bars = {
    #         "axial": self.ui.axialBar,
    #         "sagittal": self.ui.sagittalBar,
    #         "coronal": self.ui.coronalBar
    #     }
    #
    #     # 联动更新所有方向（包括当前方向）以统一状态
    #     for dir_name in directions:
    #         bar = bars[dir_name]
    #         if dir_name != orientation:
    #             bar.blockSignals(True)
    #             bar.setValue(index)
    #             bar.blockSignals(False)
    #
    #         # 无论是否主滑动方向，都更新图像
    #         update_slice(self.array, self.ui, dir_name, index, sitk_image=self.image)
    #
    #     update_status_bar(self.ui)
    #     self.update_histogram(slider=orientation, index=index)

    def apply_translation(self, dx, dy, dz):
        if self.array is None:
            return
        print(f"[平移] dx={dx}, dy={dy}, dz={dz}")
        self.array = translate_3d(self.array, dx=dx, dy=dy, dz=dz)
        show_views_with_slider(self.array, self.ui, self.image)

    def apply_rotation(self, angle):
        if self.array is None:
            return
        print(f"[旋转] angle={angle}")
        self.array = rotate_3d(self.array, angle=angle, axes=(1, 2))
        show_views_with_slider(self.array, self.ui, self.image)

    # def on_rotation_finished(self, result_array):
    #     print("[旋转] 线程完成，刷新界面")
    #     self.array = result_array
    #     show_views_with_slider(self.array, self.ui, self.image)
    #     self.update_histogram()
    #
    # def apply_rotation(self, angle_xyz):
    #     if self.array is None:
    #         return
    #     print(f"[旋转] 启动线程, angles={angle_xyz}")
    #     self.rotation_thread = RotationWorker(self.array.copy(), angle_xyz)
    #     self.rotation_thread.finishing.connect(self.on_rotation_finished)
    #     self.rotation_thread.start()

    def show_translation_dialog(self):
        dlg = TransformDialog(mode="translate", parent=self.ui)
        if dlg.exec_():
            dx, dy, dz = dlg.get_translation()
            self.apply_translation(dx, dy, dz)

    def show_rotation_dialog(self):
        dlg = TransformDialog(mode="rotate", parent=self.ui)
        if dlg.exec_():
            angle = dlg.get_rotation_angle()
            self.apply_rotation(angle)


    def update_histogram(self, slider=None, index=None):
        if self.array is None:
            return
        choice = self.ui.hist_source_box.currentText().lower()
        z, y, x = self.array.shape

        if choice == "axial":
            idx = index if slider == "axial" and index is not None else self.ui.axialBar.value()
            data = self.array[idx, :, :]
        elif choice == "sagittal":
            idx = index if slider == "sagittal" and index is not None else self.ui.sagittalBar.value()
            data = self.array[:, :, idx]
        elif choice == "coronal":
            idx = index if slider == "coronal" and index is not None else self.ui.coronalBar.value()
            data = self.array[:, idx, :]
        else:
            data = self.array.flatten()

        self.ui.hist_ax.clear()
        draw_histogram(data, self.ui.hist_ax, mode=choice)
        self.ui.hist_canvas.draw()

    def toggle_measurement_mode(self):
        self.measurement_enabled = not self.measurement_enabled
        print(f"[测量模式] {'开启' if self.measurement_enabled else '关闭'}")
        enable_measurement(self.ui, self.measurement_enabled, self.image)

    def start_segmentation(self):
        if not hasattr(self.ui, "_preprocessed_array"):
            QMessageBox.warning(self.ui, "错误", "请先加载图像！")
            return
        window_width = 100
        window_level = 200
        for orientation in ["axial", "sagittal", "coronal"]:
            segment(self.ui, orientation, window_width, window_level)

    def reset_view(self):
        if self.image is None or self.array is None:
            return
        show_views_with_slider(self.array, self.ui, self.image)
        self.update_histogram()
