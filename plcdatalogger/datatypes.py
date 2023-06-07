from typing import List, Dict, Any
from dataclasses import dataclass
from pycomm3 import LogixDriver
from edgetrigger import EdgeTransitionType


@dataclass
class Tag:
    name: str
    description: str
    value: Any = None
    valid: bool = False

    def update(self, plc: LogixDriver) -> None:
        """Updates the tag value from the plc.

        Args:
            plc (LogixDriver): ControlLogix or CompactLogix PLC to communicate with.
        """
        self.value = plc.read(self.name).value
        self.valid = True
        if self.value == None:
            self.valid = False

    @staticmethod
    def from_dict(data: dict) -> 'Tag':
        # data = convert_dict_keys(data)
        return Tag(**data)


@dataclass
class Condition:
    tag: Tag
    edge_transition: EdgeTransitionType