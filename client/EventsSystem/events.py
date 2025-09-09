from Helpers.Singleton import singleton


@singleton
class Hendlers:
    def __init__(self):
        self.events_hendlers = {}
        self.function = []

    def clear(self):
        self.events_hendlers = {}
        self.function = []

    def handler(self, event: str, func: callable):
        function = self.events_hendlers.get(event)

        if function is None:
            self.events_hendlers[event] = [func]
        else:
            function.append(func)

    def dispatch(self, event: str, data):
        function = self.events_hendlers.get(event)

        if function is None:
            raise ValueError(f'Unknown event {event}')

        for func in function:
            func(data)
