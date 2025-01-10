import argparse
import cv2
import os
import pymupdf
import sys
import traceback

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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
from ocr import process_image, process_pdf, save_analysis, write_analysis_to_stream


class OCRThread(QThread):
    error = Signal(str)
    finished = Signal()

    def __init__(
        self,
        infile_path,
        output_path,
        page_range,
        model_path,
        classes_path,
        splitLeftRight,
    ):
        super().__init__()
        self.infile_path = infile_path
        self.output_path = output_path
        self.page_range = page_range
        self.model_path = model_path
        self.classes_path = classes_path
        self.splitLeftRight = splitLeftRight

    def run(self):
        try:
            classes = load_metadata(self.classes_path)
            model = load_onnx_model(self.model_path)

            if self.infile_path.endswith(".pdf"):
                analysis = process_pdf(
                    self.infile_path,
                    self.page_range,
                    model,
                    classes,
                    split_lr=self.splitLeftRight,
                )
            else:
                image = cv2.imread(self.infile_path, cv2.IMREAD_GRAYSCALE)
                analysis = process_image(
                    image, model, classes, split_lr=self.splitLeftRight
                )

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

        self.chkTwoPageSpread = QCheckBox("Two-Page Spread", self)

        self.btnGo = QPushButton("Go!", self)
        self.btnGo.setEnabled(False)
        # self.btnGo.setGeometry(150, 100, 100, 30)
        self.btnGo.clicked.connect(self.go)

        self.layout = QVBoxLayout(self)
        # self.layout.addWidget(self.text)
        self.layout.addLayout(self.layoutSelectInput)
        self.layout.addLayout(self.layoutPages)
        self.layout.addWidget(self.chkTwoPageSpread)
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
        page_range = []

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
            self.chkTwoPageSpread.isChecked(),
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
        if self.infile_path.endswith(".pdf"):
            self.txtPages.setEnabled(enabled)
        self.chkTwoPageSpread.setEnabled(enabled)

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


def launch_normal():
    app = QApplication([])

    widget = MyWidget()
    widget.setWindowTitle("Byzantine Chant OCR")
    # widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())


def launch_headless(args):
    if args.input is None:
        print("Please specify an input file with -i or --input.")
        sys.exit(1)

    metadata = load_metadata(args.meta)
    model = load_onnx_model(args.model)

    if args.input.endswith(".pdf"):
        if args.start_page == -1:
            print("Please provide a page number with --start-page.")
            sys.exit(1)

        start = args.start_page - 1
        end = args.end_page - 1 if args.end_page != -1 else start

        page_range = range(start, end + 1)

        results = process_pdf(args.input, page_range, model, metadata, args.split_lr)
    else:
        image = cv2.imread(args.input, cv2.IMREAD_GRAYSCALE)
        results = process_image(image, model, metadata, args.split_lr)

    if args.stdout:
        print(
            write_analysis_to_stream(results),
            flush=True,
        )
    else:
        save_analysis(results, args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Performs OCR on an image or PDF")

    parser.add_argument(
        "--headless",
        help="Launch the app without a window",
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--start-page",
        help="The first page to process. Required for PDFs.",
        type=int,
        default=-1,
    )
    parser.add_argument(
        "-e",
        "--end-page",
        help="The last page to process. If omitted, only the start page will be processed.",
        type=int,
        default=-1,
    )

    parser.add_argument("-i", "--input", help="Relative path to the input file")

    parser.add_argument(
        "-o",
        "--output",
        help="Relative path to the output file",
        default="output.yaml",
    )

    parser.add_argument(
        "--model",
        help="Relative path to the model",
        default="current_model.onnx",
    )

    parser.add_argument(
        "--meta",
        help="Relative path to model metadata",
        default="metadata.json",
    )

    parser.add_argument(
        "--stdout",
        help="Print to stdout instead of to a file",
        action="store_true",
    )

    parser.add_argument(
        "--split-lr",
        help="Use this flag if each PDF page contains two side-by-side pages",
        action="store_true",
    )

    args = parser.parse_args()

    if args.headless:
        launch_headless(args)
    else:
        launch_normal()
