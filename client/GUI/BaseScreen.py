from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QScroller, QAbstractScrollArea, QScrollerProperties
from abc import ABC, ABCMeta, abstractmethod


# Создаём комбинированный метакласс
class CombinedMeta(QtWidgets.QWidget.__class__, ABCMeta):
    pass


# Создаём базовый класс с этим метаклассом
class BaseScreen(QtWidgets.QWidget, ABC, metaclass=CombinedMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__is_read = False
        self.__is_write = False
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
    def showEvent(self, event):
        super().showEvent(event)
        if not self._touch_scroll_initialized:
            self._touch_scroll_initialized = True
            self._enable_touch_scroll()

    def _enable_touch_scroll(self):
        """Включает кинетический свайп-скролл для всех прокручиваемых областей."""
        for scroll_area in self.findChildren(QAbstractScrollArea):
            viewport = scroll_area.viewport()
            QScroller.grabGesture(viewport, QScroller.LeftMouseButtonGesture)

            # Тонкая настройка параметров скролла для тачскрина
            scroller = QScroller.scroller(viewport)
            props = scroller.scrollerProperties()

            # Минимальная дистанция для распознавания свайпа (метры, ~5мм)
            props.setScrollMetric(QScrollerProperties.DragStartDistance, 0.005)
            # Сглаживание скорости при свайпе
            props.setScrollMetric(QScrollerProperties.DragVelocitySmoothingFactor, 0.6)
            # Замедление кинетического скролла (меньше = быстрее остановка)
            props.setScrollMetric(QScrollerProperties.DecelerationFactor, 0.15)
            # Максимальная скорость (м/с)
            props.setScrollMetric(QScrollerProperties.MaximumVelocity, 0.5)
            # Отключаем пружинящий эффект за границами списка
            props.setScrollMetric(QScrollerProperties.OvershootDragResistanceFactor, 0.0)
            props.setScrollMetric(QScrollerProperties.OvershootScrollDistanceFactor, 0.0)

            scroller.setScrollerProperties(props)

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
