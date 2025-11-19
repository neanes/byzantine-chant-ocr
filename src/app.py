import argparse
from pathlib import Path
import cv2
import os
import pymupdf
import sys
import traceback

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from model_downloader import download_latest_model
from model_metadata import load_metadata
from model import load_onnx_model
from ocr import (
    PreprocessOptions,
    process_image,
    process_pdf,
    save_analysis,
    write_analysis_to_stream,
)
from version import __version__


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
        preprocess_options,
        split_lr,
        use_latest_model,
    ):
        super().__init__()
        self.infile_path = infile_path
        self.output_path = output_path
        self.page_range = page_range
        self.model_path = model_path
        self.classes_path = classes_path
        self.preprocess_options = preprocess_options
        self.split_lr = split_lr
        self.use_latest_model = use_latest_model

    def run(self):
        try:
            if self.use_latest_model:
                model_dir = get_model_dir()
                self.classes_path = str(model_dir / "latest" / "metadata.json")
                self.model_path = str(model_dir / "latest" / "current_model.onnx")

                if not os.path.exists(self.classes_path) or not os.path.exists(
                    self.model_path
                ):
                    download_latest_model(model_dir / "latest")

            classes = load_metadata(self.classes_path)
            model = load_onnx_model(self.model_path)

            if self.infile_path.endswith(".pdf"):
                analysis = process_pdf(
                    self.infile_path,
                    self.page_range,
                    model,
                    classes,
                    preprocess_options=self.preprocess_options,
                    split_lr=self.split_lr,
                )
            else:
                image = cv2.imread(self.infile_path, cv2.IMREAD_GRAYSCALE)
                analysis = process_image(
                    image,
                    model,
                    classes,
                    preprocess_options=self.preprocess_options,
                    split_lr=self.split_lr,
                )

            analysis.additional_metadata["app_name"] = "Byzantine Chant OCR"
            analysis.additional_metadata["app_version"] = __version__

            save_analysis(analysis, self.output_path)
            self.finished.emit()
        except:
            self.error.emit(traceback.format_exc())


class UpdateModelThread(QThread):
    error = Signal(str)
    finished = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            tag = download_latest_model(self.path)
            self.finished.emit(tag)
        except:
            self.error.emit(traceback.format_exc())


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.infile_path = ""

        self.btnSelectInput = QPushButton("Select Input")
        self.btnSelectInput.clicked.connect(self.choose_input_file)
        self.lblSelectInput = QLabel("No file selected")
        self.layoutSelectInput = QHBoxLayout()
        self.layoutSelectInput.addWidget(self.btnSelectInput)
        self.layoutSelectInput.addWidget(self.lblSelectInput)

        self.chkUseLatestModel = QCheckBox("Use Latest Model", self)
        self.chkUseLatestModel.setChecked(True)
        self.chkUseLatestModel.stateChanged.connect(self.toggle_use_latest_model)
        self.btnUpdateModel = QPushButton("Check for Model Updates")
        self.btnUpdateModel.clicked.connect(self.update_model)

        self.btnSelectModel = QPushButton("Select Model")
        self.btnSelectModel.clicked.connect(self.choose_model)
        self.txtSelectModel = QLineEdit("current_model.onnx")
        self.txtSelectModel.setEnabled(False)
        self.layoutSelectModel = QHBoxLayout()
        self.layoutSelectModel.addWidget(self.btnSelectModel)
        self.layoutSelectModel.addWidget(self.txtSelectModel)
        self.widgetSelectModel = QWidget()
        self.widgetSelectModel.setLayout(self.layoutSelectModel)
        self.widgetSelectModel.setVisible(False)

        self.btnSelectMetadata = QPushButton("Select Metadata")
        self.btnSelectMetadata.clicked.connect(self.choose_metadata)
        self.txtSelectMetadata = QLineEdit("metadata.json")
        self.txtSelectMetadata.setEnabled(False)
        self.layoutSelectMetadata = QHBoxLayout()
        self.layoutSelectMetadata.addWidget(self.btnSelectMetadata)
        self.layoutSelectMetadata.addWidget(self.txtSelectMetadata)
        self.widgetSelectMetadata = QWidget()
        self.widgetSelectMetadata.setLayout(self.layoutSelectMetadata)
        self.widgetSelectMetadata.setVisible(False)

        self.lblPages = QLabel("Pages")
        self.txtPages = QLineEdit()
        self.txtPages.setText("N/A")
        self.txtPages.setEnabled(False)
        self.layoutPages = QHBoxLayout()
        self.layoutPages.addWidget(self.lblPages)
        self.layoutPages.addWidget(self.txtPages)

        self.chkTwoPageSpread = QCheckBox("Two-Page Spread", self)

        self.layoutDeskew = QHBoxLayout()
        self.chkDeskew = QCheckBox("Deskew", self)
        self.lblDeskew = QLabel("max deg")
        self.spnDeskew = QSpinBox(self)
        self.spnDeskew.setMinimumWidth(50)
        self.spnDeskew.setValue(5)
        self.spnDeskew.setMinimum(1)
        self.spnDeskew.setMaximum(90)
        self.layoutDeskew.addWidget(self.chkDeskew)
        self.layoutDeskew.addStretch()
        self.layoutDeskew.addWidget(self.lblDeskew)
        self.layoutDeskew.addWidget(self.spnDeskew)

        self.layoutDespeckle = QHBoxLayout()
        self.chkDespeckle = QCheckBox("Despeckle", self)
        self.lblDespeckle = QLabel("k-size")
        self.cmbDespeckle = QComboBox(self)
        self.cmbDespeckle.setMinimumWidth(50)
        self.cmbDespeckle.addItems(["3", "5", "7", "9"])
        self.cmbDespeckle.setCurrentText("3")
        self.layoutDespeckle.addWidget(self.chkDespeckle)
        self.layoutDespeckle.addStretch()
        self.layoutDespeckle.addWidget(self.lblDespeckle)
        self.layoutDespeckle.addWidget(self.cmbDespeckle)

        self.layoutClose = QHBoxLayout()
        self.chkClose = QCheckBox("Close Holes", self)
        self.lblClose = QLabel("k-size")
        self.spnClose = QSpinBox(self)
        self.spnClose.setMinimumWidth(50)
        self.spnClose.setValue(2)
        self.spnClose.setMinimum(2)
        self.layoutClose.addWidget(self.chkClose)
        self.layoutClose.addStretch()
        self.layoutClose.addWidget(self.lblClose)
        self.layoutClose.addWidget(self.spnClose)

        self.btnGo = QPushButton("Go!", self)
        self.btnGo.setEnabled(False)
        # self.btnGo.setGeometry(150, 100, 100, 30)
        self.btnGo.clicked.connect(self.go)

        self.layout = QVBoxLayout(self)
        # self.layout.addWidget(self.text)
        self.layout.addLayout(self.layoutSelectInput)
        self.layout.addLayout(self.layoutPages)
        self.layout.addWidget(self.chkTwoPageSpread)
        self.layout.addLayout(self.layoutDeskew)
        self.layout.addLayout(self.layoutDespeckle)
        self.layout.addLayout(self.layoutClose)
        self.layout.addWidget(self.chkUseLatestModel)
        self.layout.addWidget(self.btnUpdateModel)
        self.layout.addWidget(self.widgetSelectModel)
        self.layout.addWidget(self.widgetSelectMetadata)
        self.layout.addWidget(self.btnGo)

    def choose_input_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            dir=str(Path.home()),
            filter=(
                "PDF and Images (*.pdf "
                "*.bmp *.dib *.gif *.jpeg *.jpg *.jpe *.jp2 *.png *.webp *.avif "
                "*.pbm *.pgm *.ppm *.pxm *.pnm *.pfm *.sr *.ras *.tiff *.tif *.exr *.hdr *.pic)"
            ),
        )

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
            self, "Open File", dir=str(Path.home()), filter="JSON (*.json)"
        )

        if len(filepath) > 0:
            self.txtSelectMetadata.setText(filepath)

    def choose_model(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open File", dir=str(Path.home()), filter="ONNX Model (*.onnx)"
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

        default_file_name = Path(self.infile_path).with_suffix(".byzocr")

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            dir=str(default_file_name),
            filter="BYZOCR (*.byzocr)",
        )

        if len(output_path) == 0:
            return

        self.enable_ui(False)

        preprocess_options = PreprocessOptions()

        preprocess_options.deskew = self.chkDeskew.isChecked()
        preprocess_options.despeckle = self.chkDespeckle.isChecked()
        preprocess_options.close = self.chkClose.isChecked()
        preprocess_options.despeckle_kernel_size = int(self.cmbDespeckle.currentText())
        preprocess_options.close_kernel_size = self.spnClose.value()
        preprocess_options.deskew_max_angle = self.spnDeskew.value()

        # Start OCR in a separate thread
        self.thread = OCRThread(
            self.infile_path,
            output_path,
            page_range,
            self.txtSelectModel.text(),
            self.txtSelectMetadata.text(),
            preprocess_options,
            self.chkTwoPageSpread.isChecked(),
            self.chkUseLatestModel.isChecked(),
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
        self.chkDeskew.setEnabled(enabled)
        self.chkDespeckle.setEnabled(enabled)
        self.chkClose.setEnabled(enabled)
        self.spnDeskew.setEnabled(enabled)
        self.cmbDespeckle.setEnabled(enabled)
        self.spnClose.setEnabled(enabled)
        self.chkUseLatestModel.setEnabled(enabled)
        self.btnUpdateModel.setEnabled(enabled)

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

    def update_model(self):
        try:
            self.enable_ui(False)

            # Start Model Update in a separate thread
            self.thread = UpdateModelThread(get_model_dir() / "latest")

            def on_finished(tag):
                QMessageBox.information(
                    self,
                    "Model Update",
                    f"The latest model ({tag}) has been downloaded successfully.",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )

                self.enable_ui(True)

            def on_error(msg):
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred while updating the model:\n{msg}",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )

                self.enable_ui(True)

            self.thread.error.connect(on_error)
            self.thread.finished.connect(on_finished)
            self.thread.start()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while updating the model:\n{str(e)}",
                buttons=QMessageBox.Ok,
                defaultButton=QMessageBox.Ok,
            )

            self.enable_ui(True)

    def toggle_use_latest_model(self, state):
        if not state:
            self.widgetSelectMetadata.show()
            self.widgetSelectModel.show()
            self.adjustSize()
        else:
            self.widgetSelectMetadata.hide()
            self.widgetSelectModel.hide()
            self.adjustSize()


def launch_normal():
    app = QApplication([])

    widget = MyWidget()
    widget.setWindowTitle(f"Byzantine Chant OCR v{__version__}")
    # widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())


def launch_headless(args):
    if args.input is None:
        print("Please specify an input file with -i or --input.")
        sys.exit(1)

    if args.use_latest_model:
        model_dir = get_model_dir()
        args.model = str(model_dir / "latest" / "current_model.onnx")
        args.meta = str(model_dir / "latest" / "metadata.json")

        if not os.path.exists(args.meta) or not os.path.exists(args.model):
            download_latest_model(model_dir / "latest")

    metadata = load_metadata(args.meta)
    model = load_onnx_model(args.model)

    preprocess_options = PreprocessOptions()

    preprocess_options.deskew = args.deskew
    preprocess_options.despeckle = args.despeckle
    preprocess_options.close = args.close

    if args.despeckle_ksize:
        preprocess_options.despeckle_kernel_size = args.despeckle_ksize

    if args.close_ksize:
        preprocess_options.close_kernel_size = args.close_ksize

    if args.deskew_max_angle:
        preprocess_options.deskew_max_angle = args.deskew_max_angle

    if args.input.endswith(".pdf"):
        if args.start_page == -1:
            print("Please provide a page number with --start-page.")
            sys.exit(1)

        start = args.start_page - 1
        end = args.end_page - 1 if args.end_page != -1 else start

        page_range = range(start, end + 1)

        results = process_pdf(
            args.input,
            page_range,
            model,
            metadata,
            preprocess_options=preprocess_options,
            split_lr=args.split_lr,
        )
    else:
        image = cv2.imread(args.input, cv2.IMREAD_GRAYSCALE)
        results = process_image(
            image,
            model,
            metadata,
            preprocess_options=preprocess_options,
            split_lr=args.split_lr,
        )

    if args.stdout:
        print(
            write_analysis_to_stream(results),
            flush=True,
        )
    else:
        save_analysis(results, args.output)


def get_datadir() -> Path:
    """
    Returns a parent directory path
    where persistent application data can be stored.
    """

    home = Path.home()

    if sys.platform == "win32":
        return home / "AppData/Local" / "ByzantineChantOCR"
    elif sys.platform == "linux":
        return home / ".local/share" / "ByzantineChantOCR"
    elif sys.platform == "darwin":
        return home / "Library/Application Support" / "ByzantineChantOCR"


def get_model_dir() -> Path:
    """
    Returns the directory path
    where models are stored.
    """

    return get_datadir() / "models"


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
        default="output.byzocr",
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
        "--use-latest-model",
        help="Use the latest available model from GitHub. Downloads the model if not already present.",
        action="store_true",
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

    parser.add_argument(
        "--deskew",
        help="Use this flag if the image is significantly skewed",
        action="store_true",
    )

    parser.add_argument(
        "--deskew-max-angle",
        help="The maximum tilt angle to consider when attempting to deskew. The larger this angle, the slower the deskewing process will be.",
        type=int,
    )

    parser.add_argument(
        "--despeckle",
        help="Use this flag if the image contains a lot of salt-and-pepper noise. Performs a median blur.",
        action="store_true",
    )

    parser.add_argument(
        "--despeckle-ksize",
        help="The kernel size for despeckling. E.g. 3 indicates a 3x3 kernel.",
        type=int,
    )

    parser.add_argument(
        "--close",
        help="Use this flag if the neumes contain a lot of small gaps. Performs a morphological closing transformation.",
        action="store_true",
    )

    parser.add_argument(
        "--close-ksize",
        help="The kernel size for morphological closing. E.g. 3 indicates a 3x3 kernel.",
        type=int,
    )

    args = parser.parse_args()

    if args.headless:
        launch_headless(args)
    else:
        launch_normal()
