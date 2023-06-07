from typing import Callable
from enum import Enum
from datetime import datetime


class EdgeTransitionType(Enum):
    Falling = "Falling"
    Rising = "Rising"
    Both = "Both"


class EdgeTrigger:
    def __init__(self, callback: Callable, transition_type: EdgeTransitionType = EdgeTransitionType.Both):
        self.test = None
        self.transition_type = transition_type
        self.callback = callback
        self.date_triggered = datetime.now()

        if self.transition_type not in EdgeTransitionType:
            raise ValueError(f"Unknown transition_type '{self.transition_type}'.")

    def __call__(self, *args, **kwargs):
        test = kwargs.pop("test", None) # type: bool
        if test == None:
            raise ValueError("Missing required keyword argument 'test'.")
        
        if self.transition_type == EdgeTransitionType.Both:
            if test != self.test:
                self.date_triggered = datetime.now()
                self.callback(*args, **kwargs)
            self.test = test
        
        elif self.transition_type == EdgeTransitionType.Falling:
            if self.test and not test:
                self.date_triggered = datetime.now()
                self.callback(*args, **kwargs)
            self.test = test

        elif self.transition_type == EdgeTransitionType.Rising:
            if not self.test and test:
                self.date_triggered = datetime.now()
                self.callback(*args, **kwargs)
            self.test = test


class RisingEdgeTrigger(EdgeTrigger):
    def __init__(self, callback: Callable):
        super().__init__(callback, transition_type = EdgeTransitionType.Rising)


class FallingEdgeTrigger(EdgeTrigger):
    def __init__(self, callback: Callable):
        super().__init__(callback, transition_type = EdgeTransitionType.Falling)


class EdgeRetrigger:
    def __init__(self, edge_trigger: EdgeTrigger, retrigger_seconds: int) -> None:
        self.edge_trigger = edge_trigger
        self.retrigger_seconds = retrigger_seconds
    
    def update(self) -> None:
        if self.edge_trigger.transition_type == EdgeTransitionType.Both:
            return
            
        time_diff = datetime.now() - self.edge_trigger.date_triggered
        if time_diff.total_seconds() < self.retrigger_seconds:
            return
        
        if self.edge_trigger.transition_type == EdgeTransitionType.Rising:
            self.edge_trigger.test = False
        elif self.edge_trigger.transition_type == EdgeTransitionType.Falling:
            self.edge_trigger.test = True