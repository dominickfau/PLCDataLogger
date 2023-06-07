import os
import json
from typing import List, Dict
from dataclasses import dataclass
from datatypes import Tag, Condition



COMPANY_NAME = "DF-Software"
PROGRAM_NAME = "PLC Data Logger"
PROGRAM_VERSION = "1.1.0"
CONFIG_FILE_NAME = "config.json"


USER_HOME_FOLDER = os.path.expanduser("~")
COMPANY_FOLDER = os.path.join(USER_HOME_FOLDER, "Documents", COMPANY_NAME)
PROGRAM_FOLDER = os.path.join(COMPANY_FOLDER, PROGRAM_NAME)
LOG_FOLDER = os.path.join(PROGRAM_FOLDER, "Logs")
DATA_FOLDER = os.path.join(PROGRAM_FOLDER, 'Data')

DATETIME_FORMAT_FILE_SAFE = "%m_%d_%Y - %I-%M %p"
DATETIME_FORMAT_MYSQL = "%Y-%m_%d %I:%M:%S"
DATETIME_FORMAT = "%m/%d/%Y - %H:%M:%S.%f"


if not os.path.exists(COMPANY_FOLDER):
    os.mkdir(COMPANY_FOLDER)

if not os.path.exists(PROGRAM_FOLDER):
    os.mkdir(PROGRAM_FOLDER)

if not os.path.exists(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)


CONFIG_FILE_PATH = os.path.join(USER_HOME_FOLDER, PROGRAM_FOLDER, CONFIG_FILE_NAME)


def convert_key_name(key: str) -> str:
    return key.lower().replace(" ", "_")


def convert_dict_keys(data: dict) -> Dict:
    data_ = {}
    for key in data:
        x = data[key]
        data_[convert_key_name(key)] = x
    return data_


@dataclass
class DataLoggerConfig:
    sampling_interval: float
    plc_ip_address: str
    tags: List[Tag]
    start_conditions: List[Condition] = None
    stop_conditions: List[Condition] = None

    def __post_init__(self) -> None:
        if not self.start_conditions:
            return
    
        for condition in self.start_conditions:
            if not self._validate_condition(condition):
                raise Exception(f"Start condition tag '{condition.tag.name}' does not exist in tags.")
        
        if not self.stop_conditions:
            return
        
        for condition in self.stop_conditions:
            if not self._validate_condition(condition):
                raise Exception(f"Stop condition tag '{condition.tag.name}' does not exist in tags.")

    def _validate_condition(self, condition: Condition) -> bool:
        if condition.tag not in self.tags:
            return False
        return True

    @staticmethod
    def from_path(file_path: str) -> 'DataLoggerConfig':
        if not file_path or file_path and not os.path.exists(file_path):
            raise FileNotFoundError(f"Could not find config file '{file_path}', or path does not exist.")
        
        with open(file_path, "r") as file:
            config = json.load(file) # type: dict
        
        data = config.pop("Data Logger Config", None) # type: dict
        if not data:
            raise KeyError("Config file missing section 'Data Logger Config'.")
        
        sampling_interval = data.pop("Sampling Interval", None) # type: float
        plc_ip_address = data.pop("PLC IP Address", None) # type: str

        if not sampling_interval:
            raise KeyError("Config file missing section 'Data Logger Config'.'Sampling Interval'.")
        
        if not plc_ip_address:
            raise KeyError("Config file missing section 'Data Logger Config'.'PLC IP Address'.")

        tag_data = data.pop("Tags", None) # type: List[Dict[str, str]]
        if not tag_data:
            raise KeyError("Config file missing section 'Data Logger Config'.'Tags'.")

        tags = [] # type: List[Tag]

        for tag_dict in tag_data:
            tags.append(
                Tag.from_dict(tag_dict)
            )

        # start_condition_data = data.pop("Start Condition", None) # type: List[Dict]
        # start_conditions = [] # type: List[Condition]
        # if start_condition_data:
        #     for data in start_condition_data:
        #         tag_name = data["Tag Name"]
        #         tag = None
        #         edge_transition = EdgeTransitionType.Rising if data["Edge Transition"] == "Rising" else EdgeTransitionType.Falling
        #         for tag_ in tags:
        #             if tag_name == tag_.name:
        #                 tag = tag_
        #                 break
        #         else:
        #             raise Exception(f"Start condition could not find tag '{tag_name}'")
        #         start_condition = Condition(tag, edge_transition)
        #         start_conditions.append(start_condition)
        
        # stop_condition_data = data.pop("Stop Condition", None) # type: Dict
        # stop_condition = None
        # if stop_condition_data:
        #     tag_name = start_condition_data["Tag Name"]
        #     tag = None
        #     edge_transition = EdgeTransitionType.Rising if start_condition_data["Edge Transition"] == "Rising" else EdgeTransitionType.Falling
        #     for tag_ in tags:
        #         if tag_name == tag_.name:
        #             tag = tag_
        #             break
        #     else:
        #         raise Exception(f"Stop condition could not find tag '{tag_name}'")
        #     stop_condition = Condition(tag, edge_transition)
        
        return DataLoggerConfig(
            sampling_interval = sampling_interval,
            plc_ip_address = plc_ip_address,
            tags = tags
        )