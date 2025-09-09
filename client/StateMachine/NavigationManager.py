class NavigationManager:
    def __init__(self):
        # Стек истории: каждый элемент – словарь с именем экрана и состоянием (value)
        self.history = []

    def push(self, screen_name: str, value: any):
        self.history.append({'screen': screen_name, 'value': value})

    def pop(self):
        if self.history:
            return self.history.pop()
        return None

    def peek(self):
        if self.history:
            return self.history[-1]
        return None

    def clear(self):
        self.history.clear()
