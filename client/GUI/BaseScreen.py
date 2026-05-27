from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractScrollArea,
    QAbstractItemView,
    QScroller,
    QScrollerProperties,
)
from abc import ABC, ABCMeta, abstractmethod


# Создаём комбинированный метакласс
class CombinedMeta(QtWidgets.QWidget.__class__, ABCMeta):
    pass


# Создаём базовый класс с этим метаклассом
class BaseScreen(QtWidgets.QWidget, ABC, metaclass=CombinedMeta):
    SCREEN_WIDTH = 480
    SCREEN_HEIGHT = 800

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__is_read = False
        self.__is_write = False
        # Флаг: включать ли тач-скролл для данного экрана
        # По умолчанию отключён и явно включается в нужных подклассах.
        self.enable_touch_scroll = False
        self._touch_scroll_initialized = False
        # self.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1, stop:0 rgba(47, 70, 105, 255), stop:1 rgba(131, 149, 174, 255));\n""")
        self.setStyleSheet("background-color: #2e4461;")
        self.event_timeout_back = None
        self.event_edit_psw = None
        self.event_edit_login = None
        self.event_input_name_code = None
        self.event_select_group = None
        self.event_select_tool = None
        self.event_select_plan = None
        self.on_serial_data_received = None
        self.event_enter_barcode = None
        self.event_select_management_group = None

    # ------------------------------------------------------------------
    # Тач-скролл: кинетическая прокрутка одним пальцем для всех
    # QAbstractScrollArea (QListWidget, QScrollArea, QTableWidget и т.д.)
    # Инициализируется один раз при первом показе экрана, когда все
    # дочерние виджеты уже созданы через setupUi.
    # ------------------------------------------------------------------
    def normalize_screen_geometry(self) -> None:
        """Фиксированный размер экрана как у .ui (480×800)."""
        self.setMinimumSize(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.setMaximumSize(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.resize(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

    def showEvent(self, event):
        super().showEvent(event)
        if self.enable_touch_scroll and not self._touch_scroll_initialized:
            self._touch_scroll_initialized = True
            self._enable_touch_scroll()

    def _enable_touch_scroll(self):
        """Плавный скролл по пикселям + кинетический свайп (QScroller) для тач-экрана."""
        all_scroll_areas = self.findChildren(QAbstractScrollArea)
        # Только области без вложенных QAbstractScrollArea, чтобы не было двойного скролла и скачков
        for scroll_area in all_scroll_areas:
            has_nested = any(
                scroll_area.isAncestorOf(other) and other != scroll_area
                for other in all_scroll_areas
            )
            if has_nested:
                continue

            # Плавный скролл по пикселям (а не по целым карточкам/элементам) для списков и таблиц
            if isinstance(scroll_area, QAbstractItemView):
                scroll_area.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
                scroll_area.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
                scroll_area.verticalScrollBar().setSingleStep(20)

            viewport = scroll_area.viewport()
            viewport.setAttribute(Qt.WA_AcceptTouchEvents, True)
            QScroller.grabGesture(viewport, QScroller.TouchGesture)
            QScroller.grabGesture(viewport, QScroller.LeftMouseButtonGesture)
            scroller = QScroller.scroller(viewport)
            props = scroller.scrollerProperties()
            props.setScrollMetric(
                QScrollerProperties.DecelerationFactor, 0.12
            )
            props.setScrollMetric(
                QScrollerProperties.MaximumVelocity, 1.2
            )
            scroller.setScrollerProperties(props)

    @staticmethod
    def format_fio_short(user):
        """
        Форматирует ФИО в вид «Фамилия И.О.».
        Если отчество пустое или состоит только из не-букв — выводится «Фамилия И.».
        """
        family = (getattr(user, 'family', None) or '').strip()
        first = (getattr(user, 'first_name', None) or '').strip()
        second = (getattr(user, 'second_name', None) or '').strip()
        first_initial = f"{first[0]}." if first and first[0].isalpha() else ""
        # Отчество: только если есть и первая буква — буква (не пустая строка и не символы)
        second_initial = f"{second[0]}." if second and second[0].isalpha() else ""
        parts = [family, first_initial, second_initial]
        return " ".join(p for p in parts if p).strip()

    def is_read(self):
        return self.__is_read

    def is_write(self):
        return self.__is_write

    @abstractmethod
    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        raise NotImplementedError("Метод set_data должен быть реализован в подклассе")

    @abstractmethod
    def get_data(self):
        pass

    def on_focus_out(self, object_name):
        pass

    def on_focus_in(self, object_name):
        pass

    def handle_callback_executor(self, *args, **kwargs):
        pass
