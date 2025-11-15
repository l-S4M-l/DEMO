import sys
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image
import imageio.v2 as imageio
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFrame,
)


SUPPORTED_FORMATS = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
    "TIFF": ".tiff",
    "BMP": ".bmp",
    "TGA": ".tga",
    "DDS": ".dds",
    "GIF": ".gif",
    "ICO": ".ico",
}
SUPPORTED_SUFFIXES = {ext.lower() for ext in SUPPORTED_FORMATS.values()}
REGISTERED_SUFFIXES = {ext.lower() for ext in Image.registered_extensions().keys()}


class DropImageFrame(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropFrame")
        self.setMinimumSize(360, 240)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_label = QLabel("Drag an image here")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

        self._current_path: Optional[Path] = None

    @property
    def current_path(self) -> Optional[Path]:
        return self._current_path

    def load_image(self, path: Path) -> None:
        self._load_image(path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 (Qt override)
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and self._is_supported(Path(url.toLocalFile())):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 (Qt override)
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if self._is_supported(path):
                    self._load_image(path)
                    event.acceptProposedAction()
                    return
        QMessageBox.warning(self, "Unsupported file", "The dropped file is not a supported image format.")

    def _load_image(self, path: Path) -> None:
        try:
            with Image.open(path) as pil_image:
                preview = pil_image.copy()
            preview.thumbnail((640, 480))
            qt_image = self._pil_to_qpixmap(preview)
        except Exception as exc:  # pragma: no cover - visual feedback only
            QMessageBox.critical(self, "Error", f"Could not load image:\n{exc}")
            return

        self.preview_label.setText("")
        self.preview_label.setPixmap(qt_image)
        self.preview_label.setScaledContents(True)
        self._current_path = path

    @staticmethod
    def _pil_to_qpixmap(image: Image.Image) -> QPixmap:
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")
        width, height = image.size
        data = image.tobytes("raw", "RGBA")
        qimage = QImage(data, width, height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimage)

    @staticmethod
    def _is_supported(path: Path) -> bool:
        suffix = path.suffix.lower()
        return suffix in REGISTERED_SUFFIXES or suffix in SUPPORTED_SUFFIXES


class ImageConverterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Image Format Converter")
        self.resize(720, 520)

        self._create_actions()
        self._apply_styling()

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        title_label = QLabel("Universal Image Converter")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        self.drop_frame = DropImageFrame()
        main_layout.addWidget(self.drop_frame)

        controls = QHBoxLayout()
        controls.setSpacing(16)

        self.format_box = QComboBox()
        for name in SUPPORTED_FORMATS:
            self.format_box.addItem(name)
        self.format_box.setObjectName("formatBox")
        self.format_box.setEditable(False)
        controls.addWidget(self.format_box)

        self.convert_button = QPushButton("Convert & Save")
        self.convert_button.clicked.connect(self.convert_image)  # type: ignore[arg-type]
        controls.addWidget(self.convert_button)

        controls.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addLayout(controls)

        hint = QLabel("Drag & drop an image, choose a format, then convert. Supports modern formats including DDS & TGA.")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setObjectName("hintLabel")
        main_layout.addWidget(hint)

    def _create_actions(self) -> None:
        open_action = QAction("Open Image", self)
        open_action.triggered.connect(self._open_via_dialog)  # type: ignore[arg-type]
        self.menuBar().addAction(open_action)

    def _apply_styling(self) -> None:
        palette_color = "#202123"
        accent_color = "#343541"
        secondary = "#444654"
        text_color = "#E8E9EB"
        button_color = "#565869"

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {palette_color};
            }}
            QWidget#dropFrame {{
                background-color: {accent_color};
                border-radius: 16px;
                border: 2px dashed {button_color};
                color: {text_color};
            }}
            QLabel#previewLabel {{
                font-size: 16px;
                padding: 16px;
            }}
            QLabel#titleLabel {{
                font-size: 28px;
                font-weight: 600;
                color: {text_color};
            }}
            QLabel#hintLabel {{
                color: {text_color};
                background-color: {accent_color};
                border-radius: 12px;
                padding: 12px 18px;
            }}
            QComboBox#formatBox {{
                background-color: {secondary};
                color: {text_color};
                border-radius: 12px;
                padding: 8px 12px;
            }}
            QPushButton {{
                background-color: {button_color};
                color: {text_color};
                border-radius: 12px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{
                background-color: {secondary};
            }}
        """
        )

    def _open_via_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an image")
        if file_path:
            self.drop_frame.load_image(Path(file_path))

    def convert_image(self) -> None:
        source_path = self.drop_frame.current_path
        if not source_path:
            QMessageBox.information(self, "No image", "Please load an image before converting.")
            return

        target_format = self.format_box.currentText()
        extension = SUPPORTED_FORMATS[target_format]

        default_name = source_path.stem + extension
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save converted image",
            str(source_path.with_name(default_name)),
            f"{target_format} (*{extension})"
        )
        if not save_path:
            return

        try:
            self._perform_conversion(source_path, Path(save_path), target_format)
        except Exception as exc:  # pragma: no cover - user feedback only
            QMessageBox.critical(self, "Conversion error", f"Failed to convert image:\n{exc}")
            return

        QMessageBox.information(self, "Success", f"Image saved to {save_path}")

    @staticmethod
    def _perform_conversion(source: Path, destination: Path, target_format: str) -> None:
        destination = destination.with_suffix(SUPPORTED_FORMATS[target_format])

        if target_format == "DDS":
            with Image.open(source) as img:
                rgba_image = img.convert("RGBA")
                array = np.array(rgba_image)
                imageio.imwrite(destination, array, format="DDS")
        else:
            with Image.open(source) as img:
                if target_format in {"JPEG", "ICO"}:
                    img = img.convert("RGB")
                img.save(destination)


def main() -> None:
    app = QApplication(sys.argv)
    window = ImageConverterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
