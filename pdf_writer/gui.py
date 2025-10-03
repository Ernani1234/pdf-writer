from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QToolBar,
    QInputDialog,
    QColorDialog,
    QSpinBox,
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
)

from .editor import write_text, add_image, sign_pdf, rotate_pages, extract_text, merge_pdfs, split_pdf, fill_form, flatten_form


@dataclass
class TextOverlay:
    page_index: int
    text: str
    x: float
    y: float
    font_name: str = "Helvetica"
    font_size: int = 12
    color: str = "black"


@dataclass
class ImageOverlay:
    page_index: int
    image_path: str
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None


class PdfEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Writer - Editor Avançado")
        self.resize(1200, 800)

        self.document = QPdfDocument(self)
        self.view = QPdfView(self)
        self.view.setDocument(self.document)
        self.view.setPageMode(QPdfView.PageMode.MultiPage)
        self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

        # Estado
        self.current_pdf_path: Optional[str] = None
        self._pending_open_path: Optional[str] = None
        self.pending_text: Optional[Tuple[str, int, str]] = None  # (text, size, color)
        self.pending_image: Optional[Tuple[str, Optional[float], Optional[float]]] = None  # (path, w, h)
        self.text_overlays: List[TextOverlay] = []
        self.image_overlays: List[ImageOverlay] = []

        # UI básica com barra inferior de página e zoom
        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.addWidget(self.view, stretch=1)
        self.setCentralWidget(central)

        self._init_toolbar()

        # Capturar cliques para posicionar overlays
        self.view.mousePressEvent = self._on_view_click  # type: ignore

        # Reagir a mudanças de status do documento (carregamento assíncrono)
        self.document.statusChanged.connect(self._on_status_changed)

    def _init_toolbar(self):
        tb = QToolBar("Ferramentas", self)
        tb.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, tb)

        act_open = QAction("Abrir", self)
        act_open.triggered.connect(self.open_pdf)
        tb.addAction(act_open)

        act_save = QAction("Salvar como…", self)
        act_save.triggered.connect(self.save_as)
        tb.addAction(act_save)

        tb.addSeparator()

        act_add_text = QAction("Adicionar Texto", self)
        act_add_text.triggered.connect(self.prepare_add_text)
        tb.addAction(act_add_text)

        act_add_img = QAction("Adicionar Imagem", self)
        act_add_img.triggered.connect(self.prepare_add_image)
        tb.addAction(act_add_img)

        act_sign = QAction("Assinar Rápido", self)
        act_sign.triggered.connect(self.quick_sign)
        tb.addAction(act_sign)

        tb.addSeparator()

        act_rotate = QAction("Girar", self)
        act_rotate.triggered.connect(self.rotate_dialog)
        tb.addAction(act_rotate)

        act_extract = QAction("Extrair Texto", self)
        act_extract.triggered.connect(self.extract_dialog)
        tb.addAction(act_extract)

        act_flatten = QAction("Flatten Form", self)
        act_flatten.triggered.connect(self.flatten_dialog)
        tb.addAction(act_flatten)

        tb.addSeparator()

        act_zoom_in = QAction("+", self)
        act_zoom_in.triggered.connect(lambda: self.view.setZoomFactor(self.view.zoomFactor() * 1.2))
        tb.addAction(act_zoom_in)

        act_zoom_out = QAction("-", self)
        act_zoom_out.triggered.connect(lambda: self.view.setZoomFactor(self.view.zoomFactor() / 1.2))
        tb.addAction(act_zoom_out)

        mode_box = QComboBox(self)
        mode_box.addItems(["Fit Width", "Fit Page", "Custom Zoom"])
        mode_box.currentIndexChanged.connect(self._change_zoom_mode)
        tb.addWidget(QLabel(" Zoom:"))
        tb.addWidget(mode_box)

    def _change_zoom_mode(self, idx: int):
        if idx == 0:
            self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        elif idx == 1:
            self.view.setZoomMode(QPdfView.ZoomMode.FitInView)
        else:
            self.view.setZoomMode(QPdfView.ZoomMode.Custom)

    def open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", os.getcwd(), "PDF Files (*.pdf)")
        if not path:
            return
        self._pending_open_path = path
        st = self.document.load(path)
        if st == QPdfDocument.Status.Error:
            self._pending_open_path = None
            QMessageBox.critical(self, "Erro", "Não foi possível carregar o PDF.")
            return
        if st == QPdfDocument.Status.Ready:
            # Carregado imediatamente
            self._finalize_open(path)

    def save_as(self):
        if not self.current_pdf_path:
            QMessageBox.warning(self, "Aviso", "Abra um PDF primeiro.")
            return
        out, _ = QFileDialog.getSaveFileName(self, "Salvar como", os.getcwd(), "PDF Files (*.pdf)")
        if not out:
            return

        # Aplicar overlays acumulados utilizando funções do editor
        tmp_in = self.current_pdf_path
        tmp_work = tmp_in

        # Aplicar textos
        for t in self.text_overlays:
            # Salvar iterativamente em arquivo temporário
            tmp_next = tempfile.mktemp(suffix=".pdf")
            try:
                write_text(tmp_work, tmp_next, t.text, t.x, t.y, page=t.page_index + 1, font_name=t.font_name, font_size=t.font_size, color=t.color)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao escrever texto: {e}")
                return
            tmp_work = tmp_next

        # Aplicar imagens
        for im in self.image_overlays:
            tmp_next = tempfile.mktemp(suffix=".pdf")
            try:
                add_image(tmp_work, tmp_next, im.image_path, im.x, im.y, width=im.width, height=im.height, page=im.page_index + 1)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao inserir imagem: {e}")
                return
            tmp_work = tmp_next

        # No fim, copiar para o destino final
        try:
            import shutil
            shutil.copyfile(tmp_work, out)
            self.statusBar().showMessage(f"Salvo em {out}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar: {e}")
            return

        # Recarregar o PDF salvo
        self.document.load(out)
        self.current_pdf_path = out
        self.text_overlays.clear()
        self.image_overlays.clear()

    def _on_status_changed(self, status):
        # Finaliza abertura quando o documento ficar pronto
        if status == QPdfDocument.Status.Ready and self._pending_open_path:
            self._finalize_open(self._pending_open_path)
            self._pending_open_path = None
        elif status == QPdfDocument.Status.Error and self._pending_open_path:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar o PDF.")
            self._pending_open_path = None

    def _finalize_open(self, path: str):
        self.current_pdf_path = path
        self.text_overlays.clear()
        self.image_overlays.clear()
        self.statusBar().showMessage(
            f"Aberto: {os.path.basename(path)} | Páginas: {self.document.pageCount()}"
        )

    def _page_at_pos(self, pos) -> Optional[int]:
        # Aproximação: usar página atual da view (top) quando em multipage
        if self.document.pageCount() == 0:
            return None
        # QPdfView não dá mapeamento simples de coordenadas. Usaremos a página central atual.
        # Para operações mais precisas, poderíamos alternar para SinglePage.
        self.view.setPageMode(QPdfView.PageMode.SinglePage)
        # Qt6 API: use pageNavigator()
        try:
            page_index = self.view.pageNavigator().currentPage()
        except Exception:
            page_index = 0
        return page_index

    def _map_view_to_pdf_coords(self, widget_pos: QPointF) -> Tuple[float, float]:
        # Conversão aproximada: usar fator de zoom e posição dentro do widget para estimar
        # Para precisão, o ideal é usar transformações do QPdfView (não expostas diretamente).
        # Estratégia: colocar texto relativo à borda inferior esquerda com base no clique vertical invertido.
        try:
            page_index = self.view.pageNavigator().currentPage()
        except Exception:
            page_index = 0
        if page_index is None:
            return 72.0, 72.0
        from pypdf import PdfReader
        if not self.current_pdf_path:
            return 72.0, 72.0
        r = PdfReader(self.current_pdf_path)
        page = r.pages[page_index]
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        # Normalizar coordenadas do clique para a área do widget
        wx = widget_pos.x() / max(1.0, self.view.width())
        wy = widget_pos.y() / max(1.0, self.view.height())
        x = wx * w
        y = (1.0 - wy) * h  # origem inferior
        return x, y

    def _on_view_click(self, event):
        if event.button() != Qt.LeftButton:
            return QPdfView.mousePressEvent(self.view, event)
        if not self.current_pdf_path:
            return QPdfView.mousePressEvent(self.view, event)

        page_index = self._page_at_pos(event.position())
        if page_index is None:
            return QPdfView.mousePressEvent(self.view, event)

        x, y = self._map_view_to_pdf_coords(event.position())

        if self.pending_text:
            text, size, color = self.pending_text
            self.text_overlays.append(TextOverlay(page_index, text, x, y, font_size=size, color=color))
            self.pending_text = None
            self.statusBar().showMessage(f"Texto posicionado na página {page_index+1} em ({int(x)}, {int(y)})")
            return

        if self.pending_image:
            img_path, w, h = self.pending_image
            self.image_overlays.append(ImageOverlay(page_index, img_path, x, y, width=w, height=h))
            self.pending_image = None
            self.statusBar().showMessage(f"Imagem posicionada na página {page_index+1} em ({int(x)}, {int(y)})")
            return

        return QPdfView.mousePressEvent(self.view, event)

    def prepare_add_text(self):
        if not self.current_pdf_path:
            QMessageBox.information(self, "Info", "Abra um PDF primeiro.")
            return
        text, ok = QInputDialog.getText(self, "Adicionar Texto", "Texto:")
        if not ok or not text:
            return
        size, ok = QInputDialog.getInt(self, "Tamanho da Fonte", "Tamanho:", 12, 6, 96, 1)
        if not ok:
            return
        color = QColorDialog.getColor(QColor("black"), self, "Cor do Texto")
        color_name = color.name() if color.isValid() else "black"
        self.pending_text = (text, size, color_name)
        QMessageBox.information(self, "Posicionar", "Clique na página para posicionar o texto.")

    def prepare_add_image(self):
        if not self.current_pdf_path:
            QMessageBox.information(self, "Info", "Abra um PDF primeiro.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Escolher Imagem", os.getcwd(), "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        width, ok = QInputDialog.getInt(self, "Largura (pt)", "Largura (pt):", 180, 10, 1440, 10)
        if not ok:
            return
        self.pending_image = (path, float(width), None)
        QMessageBox.information(self, "Posicionar", "Clique na página para posicionar a imagem.")

    def quick_sign(self):
        if not self.current_pdf_path:
            QMessageBox.information(self, "Info", "Abra um PDF primeiro.")
            return
        img, _ = QFileDialog.getOpenFileName(self, "Imagem da Assinatura", os.getcwd(), "Images (*.png *.jpg *.jpeg *.bmp)")
        if not img:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Salvar assinado como", os.getcwd(), "PDF Files (*.pdf)")
        if not out:
            return
        try:
            sign_pdf(self.current_pdf_path, out, img)
            self.document.load(out)
            self.current_pdf_path = out
            self.statusBar().showMessage(f"Assinado e salvo em {out}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao assinar: {e}")

    def rotate_dialog(self):
        if not self.current_pdf_path:
            QMessageBox.information(self, "Info", "Abra um PDF primeiro.")
            return
        deg, ok = QInputDialog.getInt(self, "Girar", "Graus (90/180/270):", 90, 0, 360, 90)
        if not ok:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Salvar como", os.getcwd(), "PDF Files (*.pdf)")
        if not out:
            return
        try:
            # Todas as páginas
            rotate_pages(self.current_pdf_path, out, deg, None)
            self.document.load(out)
            self.current_pdf_path = out
            self.statusBar().showMessage(f"Giro aplicado e salvo em {out}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao girar: {e}")

    def extract_dialog(self):
        if not self.current_pdf_path:
            QMessageBox.information(self, "Info", "Abra um PDF primeiro.")
            return
        txt = extract_text(self.current_pdf_path, None)
        out, _ = QFileDialog.getSaveFileName(self, "Salvar texto", os.getcwd(), "Text Files (*.txt)")
        if not out:
            return
        try:
            with open(out, "w", encoding="utf-8") as f:
                f.write(txt)
            self.statusBar().showMessage(f"Texto extraído em {out}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar texto: {e}")

    def flatten_dialog(self):
        if not self.current_pdf_path:
            QMessageBox.information(self, "Info", "Abra um PDF primeiro.")
            return
        out, _ = QFileDialog.getSaveFileName(self, "Salvar como", os.getcwd(), "PDF Files (*.pdf)")
        if not out:
            return
        try:
            flatten_form(self.current_pdf_path, out)
            self.document.load(out)
            self.current_pdf_path = out
            self.statusBar().showMessage(f"Formulário achatado em {out}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao achatar: {e}")


def run_gui():
    app = QApplication.instance() or QApplication([])
    win = PdfEditorWindow()
    win.show()
    app.exec()
