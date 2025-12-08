# import cairosvg
from PyQt5 import QtSvg, QtCore, QtGui
import subprocess
from io import BytesIO
#from svglib.svglib import svg2rlg
#from reportlab.graphics import renderPM
#from PIL import Image


class SvgToPng:

    def __init__(self):
        self.src = ""

    def get_pixmap(self, width=None, height=None):
        return self.get_pixmap_QtSvg(width, height)

    def get_pixmap_QtSvg(self, width=None, height=None) -> QtGui.QPixmap:
        """
        Рендерит SVG в QPixmap с указанными размерами.
        
        :param width: Ширина pixmap. Если None, определяется из SVG.
        :param height: Высота pixmap. Если None, определяется из SVG.
        :return: QPixmap с отрендеренным SVG
        """
        # Загрузка SVG-кода
        renderer = QtSvg.QSvgRenderer()
        if not renderer.load(QtCore.QByteArray(self.src.encode())):
            # Если не удалось загрузить, возвращаем пустой pixmap
            return QtGui.QPixmap(51, 51)
        
        # Определяем размеры из SVG или используем переданные
        if width is None or height is None:
            view_box = renderer.viewBox()
            if view_box.isValid() and view_box.width() > 0 and view_box.height() > 0:
                # Используем размеры из viewBox
                width = int(view_box.width())
                height = int(view_box.height())
            else:
                # Пытаемся получить размеры из атрибутов SVG
                # Размеры по умолчанию для иконок кнопок
                width = 51
                height = 51

        # Создание пиксмапа из SVG-кода
        pixmap = QtGui.QPixmap(width, height)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap

 #   def svg_to_png_QtSvg(self) -> QtGui.QPixmap:
 #        # Загрузка SVG-кода
 #        renderer = QtSvg.QSvgRenderer()
 #        renderer.load(QtCore.QByteArray(self.src.encode()))
 #
 #        # Создание пиксмапа из SVG-кода
 #        pixmap = QtGui.QPixmap(464, 371)
 #        pixmap.fill(QtCore.Qt.transparent)
 #        painter = QtGui.QPainter(pixmap)
 #        renderer.render(painter)
 #        painter.end()
 #        return pixmap
 #
 #    def get_pixmap_svglib(self):
 #        # Загрузка SVG-кода
 #        drawing = svg2rlg(BytesIO(self.src.encode()))
 #
 #        # Создание пиксмапа из SVG-кода
 #        png_data = renderPM.drawToString(drawing, fmt='PNG')
 #        img = QtGui.QImage.fromData(png_data)
 #        pixmap = QtGui.QPixmap.fromImage(img)
 #        return pixmap
 #
 #    def get_pixmap_inkscape(self):
 #        # Загрузка SVG-кода
 #        svg_bytes = self.src.encode()
 #
 #        # Создание пиксмапа из SVG-кода
 #        with subprocess.Popen(['inkscape', '-z', '-e', '-', '-w', '464', '-h', '371', '-'], stdin=subprocess.PIPE,
 #                              stdout=subprocess.PIPE) as p:
 #            png_data = p.communicate(input=svg_bytes)[0]
 #        img = Image.open(BytesIO(png_data))
 #        pixmap = QtGui.QPixmap.fromImage(
 #            QtGui.QImage(img.tobytes(), img.width, img.height, QtGui.QImage.Format_RGBA8888))
 #        return pixmap
 #
 #    def get_pixmap_rsvg(self):
 #        # Загрузка SVG-кода
 #        svg_bytes = self.src.encode()
 #
 #        # Создание пиксмапа из SVG-кода
 #        with subprocess.Popen(['rsvg-convert', '-w', '464', '-h', '371', '-'], stdin=subprocess.PIPE,
 #                              stdout=subprocess.PIPE) as p:
 #            png_data = p.communicate(input=svg_bytes)[0]
 #        img = QtGui.QImage.fromData(png_data)
 #        pixmap = QtGui.QPixmap.fromImage(img)
 #        return pixmap


if __name__ == "__main__":
    # Пример SVG-кода
    svg_data = """
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="40" fill="#0077b6" />
    </svg>
    """
    svgToPng = SvgToPng()
    svgToPng.src = svg_data
    svgToPng.svg_to_png_QtSvg()
    # Конвертируем SVG в PNG
    # png_data = cairosvg.svg2png(svg_data)
    #
    # # Теперь вы можете сохранить или обработать PNG-изображение
    # with open("output.png", "wb") as f:
    #     f.write(png_data)
