from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, Set, List, Optional, Union
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

class HtmlTitleParser:
    """
    Класс для извлечения текста из <title>...</title> в HTML-файле.
    """

    def __init__(self, path: str | Path):
        """
        :param path: Путь к HTML-файлу на диске.
        """
        self.path = Path(path)

    def get_title(self) -> str | None:
        """
        Читает файл, парсит HTML и возвращает содержимое тега <title>.
        :return: Строка с заголовком или None, если тег отсутствует.
        """
        html = self.path.read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')
        return title_tag.string if title_tag else None


class HtmlTitleParserXML:
    """
    Парсер <title> для валидного XHTML/HTML при помощи xml.etree.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def get_title(self) -> str | None:
        text = self.path.read_text(encoding='utf-8')
        # Подставляем корневой namespace, чтобы ElementTree не жаловался
        wrapper = f"<?xml version='1.0'?><root>{text}</root>"
        root = ET.fromstring(wrapper)
        title_elem = root.find('.//title')
        return title_elem.text if title_elem is not None else None




class NavigationService:
    """
    Сервис для работы со страницами:
      - извлечение заголовков
      - построение навигационного графа
      - определение вложенных страниц
      - получение списка корневых страниц
    """
    _nested_cache: Optional[Set[str]] = None

    def __init__(self, pages_dir: Union[str, Path]):
        self.pages_dir = Path(pages_dir)

    def list_pages(self) -> List[str]:
        return [p.name for p in self.pages_dir.glob('screen_*.html')]

    def get_title(self, page_name: str) -> Optional[str]:
        parser = HtmlTitleParser(self.pages_dir / page_name)
        return parser.get_title()

    def build_navigation_graph(self) -> Dict[str, Set[str]]:
        graph: Dict[str, Set[str]] = {}
        for html_file in self.pages_dir.glob('screen_*.html'):
            name = html_file.name
            html = html_file.read_text(encoding='utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            targets: Set[str] = set()
            # navigateWithToken
            for btn in soup.select('[onclick*="navigateWithToken"]'):
                js = btn['onclick']
                found = re.findall(r"navigateWithToken\(['\"]\.\./([^'\"]+)['\"]\)", js)
                targets.update(found)
            # window.location.href
            for btn in soup.select('[onclick*="window.location.href"]'):
                js = btn['onclick']
                found = re.findall(r"window\.location\.href=['\"]\./([^?'\" ]+)", js)
                targets.update(found)
            graph[name] = targets
        return graph

    def compute_nested(self) -> Set[str]:
        if NavigationService._nested_cache is None:
            graph = self.build_navigation_graph()
            nested = set()
            for targets in graph.values():
                nested |= targets
            NavigationService._nested_cache = nested
        return NavigationService._nested_cache

    def is_nested(self, page_name: str) -> bool:
        # по имени
        parts = page_name.rstrip('.html').split('_')
        if len(parts) >= 3 and (parts[2].isdigit() or parts[2] == 'append'):
            return True
        # по графу ссылок
        return page_name in self.compute_nested()

    def get_root_pages(self) -> List[str]:
        return [p for p in self.list_pages() if not self.is_nested(p)]

if __name__ == '__main__':
    import logging
    _log = logging.getLogger(__name__)
    svc = NavigationService('../frontend/page')
    _log.info('Корневые страницы: %s', svc.get_root_pages())
    for page in svc.get_root_pages():
        _log.info('%s -> %s', page, svc.get_title(page))
