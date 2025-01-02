import cv2
import os
import pymupdf
import sys
import traceback

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from model_metadata import load_metadata
from model import load_onnx_model
from ocr import process_image, process_pdf, save_analysis


class OCRThread(QThread):
    error = Signal(str)
    finished = Signal()

    def __init__(self, infile_path, output_path, page_range, model_path, classes_path):
        super().__init__()
        self.infile_path = infile_path
        self.output_path = output_path
        self.page_range = page_range
        self.model_path = model_path
        self.classes_path = classes_path

    def run(self):
        # Simulate OCR processing
        try:
            classes = load_metadata(self.classes_path)
            model = load_onnx_model(self.model_path)

            if self.infile_path.endswith(".pdf"):
                analysis = process_pdf(
                    self.infile_path, self.page_range, model, classes
                )
            else:
                image = cv2.imread(self.infile_path, cv2.IMREAD_GRAYSCALE)
                analysis = process_image(image, model, classes)

            save_analysis(analysis, self.output_path)
            self.finished.emit()
        except:
            self.error.emit(traceback.format_exc())


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.btnSelectInput = QPushButton("Select Input")
        self.btnSelectInput.clicked.connect(self.choose_input_file)
        self.lblSelectInput = QLabel("No file selected")
        self.layoutSelectInput = QHBoxLayout()
        self.layoutSelectInput.addWidget(self.btnSelectInput)
        self.layoutSelectInput.addWidget(self.lblSelectInput)

        self.btnSelectModel = QPushButton("Select Model")
        self.btnSelectModel.clicked.connect(self.choose_model)
        self.txtSelectModel = QLineEdit("current_model.onnx")
        self.txtSelectModel.setEnabled(False)
        self.layoutSelectModel = QHBoxLayout()
        self.layoutSelectModel.addWidget(self.btnSelectModel)
        self.layoutSelectModel.addWidget(self.txtSelectModel)

        self.btnSelectMetadata = QPushButton("Select Metadata")
        self.btnSelectMetadata.clicked.connect(self.choose_metadata)
        self.txtSelectMetadata = QLineEdit("metadata.json")
        self.txtSelectMetadata.setEnabled(False)
        self.layoutSelectMetadata = QHBoxLayout()
        self.layoutSelectMetadata.addWidget(self.btnSelectMetadata)
        self.layoutSelectMetadata.addWidget(self.txtSelectMetadata)

        self.lblPages = QLabel("Pages")
        self.txtPages = QLineEdit()
        self.txtPages.setText("N/A")
        self.txtPages.setEnabled(False)
        self.layoutPages = QHBoxLayout()
        self.layoutPages.addWidget(self.lblPages)
        self.layoutPages.addWidget(self.txtPages)

        self.btnGo = QPushButton("Go!", self)
        self.btnGo.setEnabled(False)
        # self.btnGo.setGeometry(150, 100, 100, 30)
        self.btnGo.clicked.connect(self.go)

        self.layout = QVBoxLayout(self)
        # self.layout.addWidget(self.text)
        self.layout.addLayout(self.layoutSelectInput)
        self.layout.addLayout(self.layoutPages)
        self.layout.addLayout(self.layoutSelectModel)
        self.layout.addLayout(self.layoutSelectMetadata)
        self.layout.addWidget(self.btnGo)

    def choose_input_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open File")

        if len(filepath) > 0:
            self.lblSelectInput.setText(os.path.basename(filepath))
            self.infile_path = filepath
            self.btnGo.setEnabled(True)

            if filepath.endswith(".pdf"):
                doc = pymupdf.open(filepath)
                self.page_count = len(doc)
                self.txtPages.setText(f"1-{self.page_count}")
                self.txtPages.setEnabled(True)
            else:
                self.txtPages.setEnabled(False)
                self.txtPages.setText(f"N/A")

    def choose_metadata(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open File", filter="JSON (*.json)"
        )

        if len(filepath) > 0:
            self.txtSelectMetadata.setText(filepath)

    def choose_model(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open File", filter="ONNX Model (*.onnx)"
        )

        if len(filepath) > 0:
            self.txtSelectModel.setText(filepath)

    def go(self):
        if self.infile_path.endswith(".pdf"):
            try:
                page_range = self.parse_page_range(self.txtPages.text())
            except:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Could not parse the page range.",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )
                return

            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save File", dir="output.yaml"
            )

            if len(output_path) == 0:
                return

            self.enable_ui(False)

            # Start OCR in a separate thread
            self.thread = OCRThread(
                self.infile_path,
                output_path,
                page_range,
                self.txtSelectModel.text(),
                self.txtSelectMetadata.text(),
            )
            self.thread.error.connect(self.display_error)
            self.thread.finished.connect(lambda: self.enable_ui(True))
            self.thread.start()

    def display_error(self, msg):
        QMessageBox.critical(
            self,
            "Error",
            msg,
            buttons=QMessageBox.Ok,
            defaultButton=QMessageBox.Ok,
        )

    def enable_ui(self, enabled):
        self.btnGo.setEnabled(enabled)
        self.btnSelectInput.setEnabled(enabled)
        self.btnSelectMetadata.setEnabled(enabled)
        self.btnSelectModel.setEnabled(enabled)
        self.txtPages.setEnabled(enabled)

    def parse_page_range(self, page_range):
        """
        Parses a page range string (e.g., "1-5,7,9") into a list of zero-based integer indexes.

        Args:
            page_range (str): The range string, where ranges are specified as "start-end" and individual pages as numbers.

        Returns:
            list: A list of zero-based integer indexes.
        """
        indexes = []
        # Split the input string by commas to handle multiple ranges/numbers
        parts = page_range.split(",")

        for part in parts:
            # Check if the part specifies a range (e.g., "1-5")
            if "-" in part:
                start, end = map(int, part.split("-"))
                indexes.extend(range(start - 1, end))  # Convert to zero-based indexes
            else:
                # Handle single page numbers
                indexes.append(int(part) - 1)  # Convert to zero-based index

        return sorted(indexes)  # Sort the final list


if __name__ == "__main__":
    app = QApplication([])

    widget = MyWidget()
    widget.setWindowTitle("Byzantine Chant OCR")
    # widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
