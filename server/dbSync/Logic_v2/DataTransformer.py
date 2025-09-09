import threading
import traceback
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional, TypedDict
from .DiagnosticLogger import DiagnosticLogger
import logging

logger = logging.getLogger(__name__)


class TransformRules(TypedDict, total=False):
    """
    Правила трансформации для одной таблицы.

    Incoming: Список функций пред обработки "сырых" данных.
    Outgoing: Список функций постобработки перед отправкой.
    Validate: Функция валидации данных.
    """
    incoming: List[Callable[[Dict[str, Any]], Dict[str, Any]]]
    outgoing: List[Callable[[Dict[str, Any]], Dict[str, Any]]]
    validate: Callable[[Dict[str, Any]], bool]


class DataTransformer:
    """
    Выполняет пред обработку, валидацию и постобработку данных в процессе синхронизации.

    Место в архитектуре:
        • Используется в SyncProcessor перед и после DataMapper.
        • Гарантирует соответствие данных бизнес-правилам.

    Зависимости:
        :param rules: Dict[table_name, TransformRules] — набор функций:
            - incoming: List[fn(raw_dict)->dict]
            - validate: fn(cleaned_dict)->bool
            - outgoing: List[fn(mapped_dict)->dict]
        :param _logger: DiagnosticLogger для логирования ошибок и предупреждений.
        :param strict: bool — если True, при падении валидации или обработчиков возбуждать исключение.

    Основные методы:
        preprocess(table, raw)   — последовательный вызов incoming rules
        validate(table, clean)   — проверка через validator
        postprocess(table, mapped)— последовательный вызов outgoing rules
        register_rule(table, stage, fn) — динамическая регистрация функций

    Протокол вызовов (Sequence Diagram):
        SyncProcessor.process_push:
            raw = cmd.data
            clean = transformer.preprocess(table, raw)
            if not transformer.validate(table, clean): skip
            mapped = data_mapper.map_incoming(table, clean)
            final = transformer.postprocess(table, mapped)
            sync_manager.process_command(data=final)

        SyncProcessor.prepare_pull:
            record = crud.fetch()
            remote = data_mapper.map_outgoing(table, record)
            enriched = transformer.postprocess(table, remote)
            send(enriched)
    """

    def __init__(
            self,
            rules: Optional[Dict[str, TransformRules]] = None,
            _logger: Optional[DiagnosticLogger] = None,
            strict: bool = False
    ) -> None:
        self.rules: Dict[str, TransformRules] = rules or {}
        self.logger = _logger
        self.strict = strict

    def register_rule(
            self,
            table: str,
            stage: str,
            fn: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Регистрирует функцию трансформации для таблицы и этапа.

        :param table: Имя таблицы.
        :param stage: 'Incoming', 'outgoing' или 'validate'.
        :param fn:    Функция обработки.
        """
        print(f'[ПОТОК][{threading.current_thread().name}][DataTransformer][register_rule] - table: {table}, stage: {stage}, fn: {fn}. [{datetime.now()}]')
        if table not in self.rules:
            self.rules[table] = {}
        if stage == 'validate':
            self.rules[table]['validate'] = fn  # type: ignore
        else:
            self.rules[table].setdefault(stage, [])  # type: ignore
            self.rules[table][stage].append(fn)  # type: ignore
        if self.logger:
            self.logger.log_info(f"Registered transformer rule for {table}.{stage}")

    def preprocess(self, table: str, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Последовательно применяет incoming правила к "сырым" данным.
        """
        rules = self.rules.get(table, {})
        data = raw.copy()
        print(f'[ПОТОК][{threading.current_thread().name}][DataTransformer][preprocess] начали обработку - table: {table}, data: {data}. [{datetime.now()}]')

        for fn in rules.get('incoming', []):
            try:
                data = fn(data)
            except Exception as e:
                print(f'[ПОТОК][{threading.current_thread().name}][DataTransformer][preprocess][ERROR] закончили обработку - error: {e}, Ошибка предварительной обработки {table} подробности: - {traceback.format_exc()}. [{datetime.now()}]')
                if self.logger:
                    self.logger.log_error(f"Preprocess error {table}: {e}")
                if self.strict:
                    raise
        print(f'[ПОТОК][{threading.current_thread().name}][DataTransformer][preprocess] - table: {table}, data: {data}. [{datetime.now()}]')
        return data

    def validate(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Проверяет данные через валидатор для таблицы.
        """
        fn = self.rules.get(table, {}).get('validate')
        if not fn:
            return True
        try:
            valid = fn(data)
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][DataTransformer][validate][ERROR] - error: {e}, Ошибка проверки {table} подробности: - {traceback.format_exc()}. [{datetime.now()}]')

            if self.logger:
                self.logger.log_error(f"Validation error {table}: {e}")
            if self.strict:
                raise
            return False
        if not valid and self.logger:
            self.logger.log_warning(f"Validation failed for {table}: {data}")
        print(f'[ПОТОК][{threading.current_thread().name}][DataTransformer][validate] - table: {table}, valid: {valid}. [{datetime.now()}]')
        return valid

    def postprocess(self, table: str, mapped: Dict[str, Any]) -> Dict[str, Any]:
        """
        Последовательно применяет outgoing правила к заммапленным данным.
        """
        rules = self.rules.get(table, {})
        data = mapped.copy()
        for fn in rules.get('outgoing', []):
            try:
                data = fn(data)
            except Exception as e:
                print(f'[ПОТОК][{threading.current_thread().name}][DataTransformer][postprocess][ERROR] - error: {e}, Ошибка постобработки {table} подробности: - {traceback.format_exc()}. [{datetime.now()}]')
                if self.logger:
                    self.logger.log_error(f"Postprocess error {table}: {e}")
                if self.strict:
                    raise
        print(f'[ПОТОК][{threading.current_thread().name}][DataTransformer][postprocess] - table: {table}, data: {data}. [{datetime.now()}]')
        return data
