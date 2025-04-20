from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout

class TransformDialog(QDialog):
    def __init__(self, mode="translate", parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入参数")

        layout = QFormLayout()

        if mode == "translate":
            self.dx_input = QLineEdit("0")
            self.dy_input = QLineEdit("0")
            self.dz_input = QLineEdit("0")
            layout.addRow("dx (像素):", self.dx_input)
            layout.addRow("dy (像素):", self.dy_input)
            layout.addRow("dz (像素):", self.dz_input)

        elif mode == "rotate":
            self.angle_input = QLineEdit("0")
            layout.addRow("角度（°）:", self.angle_input)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.setLayout(layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_translation(self):
        return (
            float(self.dx_input.text()),
            float(self.dy_input.text()),
            float(self.dz_input.text())
        )

    def get_rotation_angle(self):
        return float(self.angle_input.text())
