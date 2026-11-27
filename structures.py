"""Estructuras de datos propias: Pila (LIFO) y Cola (FIFO)."""
from collections import deque


class Pila:
    """Stack LIFO: historial de operaciones + Deshacer."""
    def __init__(self):
        self._items = []

    def push(self, x):
        self._items.append(x)

    def pop(self):
        return self._items.pop() if self._items else None

    def peek(self):
        return self._items[-1] if self._items else None

    def __len__(self):
        return len(self._items)

    def to_list(self):  # más reciente primero
        return list(reversed(self._items))


class Cola:
    """Queue FIFO: turnos de atención / solicitudes de recolección."""
    def __init__(self):
        self._items = deque()

    def enqueue(self, x):
        self._items.append(x)

    def dequeue(self):
        return self._items.popleft() if self._items else None

    def __len__(self):
        return len(self._items)

    def to_list(self):
        return list(self._items)
