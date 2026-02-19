from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QScroller,
    QAbstractScrollArea,
    QScrollerProperties,
    QAbstractItemView,
)
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
        """Включает кинетический свайп-скролл для прокручиваемых областей (только «листовые», без вложенных)."""
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
                # Плавный скролл колесиком мыши: шаг в пикселях (20 ≈ как при тач-свайпе)
                scroll_area.verticalScrollBar().setSingleStep(20)

            viewport = scroll_area.viewport()
            QScroller.grabGesture(viewport, QScroller.LeftMouseButtonGesture)

            scroller = QScroller.scroller(viewport)
            props = scroller.scrollerProperties()

            # Порог старта жеста: ~20 мм — чтобы 4 px не запускали скролл (Qt переводит в пиксели по DPI)
            props.setScrollMetric(QScrollerProperties.DragStartDistance, 0.02)
            # Минимальная скорость отпускания для старта кинетики (м/с) — мелкие «подёргивания» не дают полёт
            props.setScrollMetric(QScrollerProperties.MinimumVelocity, 0.02)
            # Блокировка оси: 0.9 — почти только вертикальный скролл при свайпе
            props.setScrollMetric(QScrollerProperties.AxisLockThreshold, 0.9)
            # Сглаживание скорости при свайпе
            props.setScrollMetric(QScrollerProperties.DragVelocitySmoothingFactor, 0.05)
            props.setScrollMetric(QScrollerProperties.DecelerationFactor, 0.08)
            props.setScrollMetric(QScrollerProperties.MaximumVelocity, 0.0005)
            # Без пружинящего эффекта за границами
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
