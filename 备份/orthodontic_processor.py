import numpy as np
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from image_io import read_dicom_series
from image_ops import translate_3d, rotate_3d
from visualization import show_views_with_slider

class OrthodonticProcessor:
    def __init__(self, ui):
        self.ui = ui
        self.second_image = None
        self.second_array = None
        self.overlay_visible = False
        self.current_translation = [0, 0, 0]
        self.current_rotation = [0, 0, 0]

    def load_second_image(self):
        if not hasattr(self.ui, '_preprocessed_array') or self.ui._preprocessed_array is None:
            QMessageBox.warning(self.ui, "错误", "请先加载第一个 DICOM 图像！")
            return False

        folder = QFileDialog.getExistingDirectory(self.ui, "选择第二个 DICOM 文件夹")
        if not folder:
            return False

        try:
            image, array, _ = read_dicom_series(folder, return_numpy=True)

            if array.shape != self.ui._preprocessed_array.shape:
                QMessageBox.warning(self.ui, "错误", "两个图像尺寸不一致，无法叠加！")
                return False

            self.second_image = image
            self.second_array = array
            self.current_translation = [0, 0, 0]
            self.current_rotation = [0, 0, 0]
            return True
        except Exception as e:
            QMessageBox.critical(self.ui, "错误", f"加载 DICOM 失败: {str(e)}")
            return False

    def apply_overlay(self):
        if self.second_array is None:
            return

        second = self.preprocess_array(self.second_array.copy())

        if any(self.current_translation):
            second = translate_3d(second, *self.current_translation)
        if any(self.current_rotation):
            second = rotate_3d(second, self.current_rotation[0], axes=(1, 2))  # 只实现一个方向旋转

        original = self.ui._preprocessed_array.copy()
        combined = np.clip(original + 0.5 * second, 0, 255).astype(np.uint8)

        show_views_with_slider(combined, self.ui, sitk_image=None)
        self.overlay_visible = True

    def preprocess_array(self, array):
        array = np.clip(array, np.percentile(array, 1), np.percentile(array, 99))
        array = (array - array.min()) / (array.max() - array.min()) * 255
        return array.astype(np.uint8)

    def remove_overlay(self):
        if hasattr(self.ui, '_preprocessed_array'):
            show_views_with_slider(self.ui._preprocessed_array, self.ui, self.ui.controller.image)
        self.overlay_visible = False

    def translate_second_image(self, dx, dy, dz):
        self.current_translation = [dx, dy, dz]
        if self.overlay_visible:
            self.apply_overlay()

    def rotate_second_image(self, angle):
        self.current_rotation = [angle, 0, 0]
        if self.overlay_visible:
            self.apply_overlay()
