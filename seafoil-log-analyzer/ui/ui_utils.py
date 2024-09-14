
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QDialog, QLabel, \
    QLineEdit, QHBoxLayout, QPushButton
class TwoFieldInputDialog(QDialog):
    def __init__(self, windows_title,
                 first_label_text,
                 second_label_text,
                 first_input_text="",
                 second_input_text=""):
        super().__init__()

        self.setWindowTitle(windows_title)

        # Layouts
        layout = QVBoxLayout()

        # First input field
        self.first_label = QLabel(first_label_text, self)
        self.first_input = QLineEdit(self)
        self.first_input.setText(first_input_text)

        # Second input field
        self.second_label = QLabel(second_label_text, self)
        self.second_input = QLineEdit(self)
        self.second_input.setText(second_input_text)

        # Ok and Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        # Add widgets to the layout
        layout.addWidget(self.first_label)
        layout.addWidget(self.first_input)
        layout.addWidget(self.second_label)
        layout.addWidget(self.second_input)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect signals to slots
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Connect "enter" key to accept
        self.second_input.returnPressed.connect(self.accept)

    def get_inputs(self):
        """Return the input values from the dialog."""
        return self.first_input.text(), self.second_input.text()