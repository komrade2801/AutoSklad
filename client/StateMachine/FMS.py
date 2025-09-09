import traceback

from transitions import Machine, MachineError

from StateMachine.Triggers import Triggers
from StateMachine.state_map import *
from transitions.extensions import GraphMachine
from transitions import Machine


# На этт объект будем вешать состояния
class Map(object):
    pass


class Maps(object):
    def __init__(self, initial_system):
        self.lump = Map()
        # Инициализация машины
        self.machine = Machine(self.lump, states=states, transitions=transitions, initial=initial_system)

    def trigger(self, name):
        return self.lump.trigger(name)


    def state(self):
        return self.lump.state
