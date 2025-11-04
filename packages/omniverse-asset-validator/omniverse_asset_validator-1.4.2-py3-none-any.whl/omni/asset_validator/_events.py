# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import RLock
from uuid import UUID, uuid4
from weakref import WeakSet

__all__ = [
    "EventListener",
    "EventStream",
    "create_event_stream",
]


@dataclass(frozen=True)
class EventListener:
    """
    An event listener.
    """

    stream: EventStream
    callback: Callable[[], None]

    def unsubscribe(self) -> None:
        """
        Unsubscribe the listener from the event stream.

        Example:
        .. code-block:: python

            event_stream = create_event_stream()
            listener = event_stream.create_event_listener(lambda: print("Event triggered"))
            listener.unsubscribe()
        """
        self.stream.remove_event_listener(self)

    def __call__(self) -> None:
        self.callback()


@dataclass(frozen=True)
class EventStream:
    """
    An event stream.
    """

    id: UUID = field(init=False, default_factory=uuid4)
    listeners: WeakSet[EventListener] = field(init=False, default_factory=WeakSet)
    lock: RLock = field(init=False, default_factory=RLock)

    def create_event_listener(self, callback: Callable[[], None]) -> EventListener:
        """
        Create a new event listener.

        Example:
        .. code-block:: python

            event_stream = create_event_stream()
            listener = event_stream.create_event_listener(lambda: print("Event triggered"))
        """
        listener = EventListener(self, callback)
        with self.lock:
            self.listeners.add(listener)
        return listener

    def remove_event_listener(self, listener: EventListener) -> None:
        with self.lock:
            self.listeners.remove(listener)

    def notify(self) -> None:
        """
        Notify all listeners.

        Example:
        .. code-block:: python

            event_stream = create_event_stream()
            event_stream.notify()
        """
        with self.lock:
            listeners = list(self.listeners)
        for listener in listeners:
            listener()

    def __len__(self) -> int:
        with self.lock:
            return len(self.listeners)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventStream):
            return False
        return self.id == other.id


def create_event_stream() -> EventStream:
    """
    Create a new event stream.

    Example:
    .. code-block:: python

        event_stream = create_event_stream()
        listener = event_stream.create_event_listener(lambda: print("Event triggered"))
        event_stream.notify()
    """
    return EventStream()
