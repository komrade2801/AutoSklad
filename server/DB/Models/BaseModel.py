from sqlalchemy import inspect


class Model:
    def to_dict(self):
        """
        Возвращает полный словарь из всех колонок данной модели.
        """
        return {
            attr.key: getattr(self, attr.key)
            for attr in inspect(self).mapper.column_attrs
        }