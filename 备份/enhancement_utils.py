import cv2
import numpy as np
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from visualization import numpy_to_vtk_image2d, render_image2d, get_slice_image

def apply_image_enhancement(ui):
    if not hasattr(ui, "_preprocessed_array"):
        QMessageBox.warning(ui, "错误", "请先加载 DICOM 数据！")
        return

    view_type, ok = QInputDialog.getItem(
        ui, "选择视图", "请选择要滤波的视图：", ["axial", "sagittal", "coronal"], 0, False
    )
    if not ok:
        return

    if view_type == "axial":
        original_slice = get_slice_image(ui._preprocessed_array, "axial", ui.axialBar.value())
    elif view_type == "coronal":
        original_slice = get_slice_image(ui._preprocessed_array, "coronal", ui.coronalBar.value())
    else:
        original_slice = get_slice_image(ui._preprocessed_array, "sagittal", ui.sagittalBar.value())

    filter_type, ok = QInputDialog.getItem(
        ui, "选择滤波类型", "请选择滤波算法：", ["Sobel (边缘检测)", "Laplace (二阶微分)"], 0, False
    )
    if not ok:
        return

    if filter_type.startswith("Sobel"):
        direction, ok = QInputDialog.getItem(
            ui, "Sobel 方向", "选择方向：", ["水平 (x)", "垂直 (y)", "双向 (x+y)"], 0, False
        )
        if not ok:
            return
        direction_map = {"水平 (x)": "x", "垂直 (y)": "y", "双向 (x+y)": "both"}
        filtered_slice = cv2_Sobel_filter(original_slice, direction_map[direction])
    else:
        filtered_slice = cv2_Laplace_filter(original_slice)

    blended = cv2.addWeighted(original_slice, 0.5, filtered_slice, 0.5, 0)
    vtk_img = numpy_to_vtk_image2d(blended)

    if view_type == "axial":
        render_image2d(vtk_img, ui.axialWidget, reset_camera=False)
    elif view_type == "coronal":
        render_image2d(vtk_img, ui.coronalWidget, reset_camera=False)
    else:
        render_image2d(vtk_img, ui.sagittalWidget, reset_camera=False)

def cv2_Sobel_filter(image, direction='both'):
    if direction == 'x':
        return cv2.Sobel(image, cv2.CV_8U, 1, 0, ksize=3)
    elif direction == 'y':
        return cv2.Sobel(image, cv2.CV_8U, 0, 1, ksize=3)
    else:
        sobelx = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
        return cv2.magnitude(sobelx, sobely).astype(np.uint8)

def cv2_Laplace_filter(image):
    return cv2.Laplacian(image, cv2.CV_8U)
