# test_debug.py

from PyQt5.QtWidgets import QMessageBox


def handle_test_button(ui):
    """
    这是“测试”按钮的响应逻辑占位函数。
    所有临时测试功能写在这里，便于未来替换或拓展。

    参数:
        ui: 主窗口对象（MainWindow）
    """
    # 示例占位：弹出提示框
    QMessageBox.information(ui, "测试按钮", "你点击了『测试』按钮！\n该函数位于 test_debug.py 中。")

    # 👉 你可以在这里调用其他测试功能，例如：
    # test_export_slice(ui)
    # test_segmentation_preview(ui)
    # test_measurement_ui(ui)
