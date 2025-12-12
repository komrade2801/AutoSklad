# Интеграция с ActionMapper
from typing import Any

from Cnf.Actions import CnfActions


class ActionMapper:
    def __init__(self, executor):
        self._executor = executor
        self._cnf_actions = CnfActions()
        self._setup_actions()

    def _setup_actions(self) -> None:
        self._actions = {
            'read_cnf': self._cnf_actions.read_cnf,
            'write_cnf_unlock_load': lambda: self._cnf_actions.write_cnf_unlock_load(),
            'write_cnf_unlock_drop': lambda: self._cnf_actions.write_cnf_unlock_drop(),
            'read_cnf_serial': self._cnf_actions.read_cnf_serial,
            'read_cnf_IP': self._cnf_actions.read_cnf_IP,
            'write_cnf_serial': lambda *a: self._cnf_actions.write_cnf_serial(*a),
            'write_cnf_IP': lambda ip: self._cnf_actions.write_cnf_IP(ip),
            'write_cnf_network': lambda *args: self._cnf_actions.write_cnf_network(*args),
            'write_cnf_lock_load': lambda index: self._cnf_actions.write_cnf_lock_load(index),
            'read_cnf_lock_load': self._cnf_actions.read_cnf_lock_load,
            'read_cnf_lock_drop': self._cnf_actions.read_cnf_lock_drop,
            'write_cnf_lock_drop': lambda index: self._cnf_actions.write_cnf_lock_drop(index),
            'write_log_critical_err': lambda err: self._cnf_actions.write_log_critical_err(err),
            'read_cnf_signature':  lambda index: self._cnf_actions.read_cnf_signature(index),
            'read_cnf_barcode': lambda index: self._cnf_actions.read_cnf_barcode(index),
            'write_cnf_barcode': lambda port, baudrate: self._cnf_actions.write_cnf_barcode(port, baudrate),
        }

    def execute(self, act: str, *args, **kwargs) -> Any:
        if action := self._actions.get(act):
            return action(*args, **kwargs)
        raise ValueError(f"Action '{act}' not found in CnfModule.")