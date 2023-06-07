import csv
import logging
import argparse
from time import sleep, perf_counter
from os import path
from datetime import datetime
from pycomm3 import LogixDriver
from plcdatalogger.config import DATA_FOLDER, LOG_FOLDER, PROGRAM_VERSION, DATETIME_FORMAT_MYSQL
from plcdatalogger.config import DataLoggerConfig


logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(asctime)s [%(levelname)s] in %(module)s: %(message)s",
    handlers=[logging.FileHandler(filename=path.join(LOG_FOLDER, "Log.log")), logging.StreamHandler()]
)

global_logger = logging.getLogger(f"{__name__}")



def log_data(writer: csv.DictWriter, logger_config: DataLoggerConfig) -> None:
    data = {}
    data["Timestamp"] = datetime.now().strftime(DATETIME_FORMAT_MYSQL)
    for tag in logger_config.tags:
        data[tag.description] = tag.value
    # global_logger.info(f"{data}")
    writer.writerow(data)


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PLC data logger."
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version = f"{parser.prog} version {PROGRAM_VERSION}"
    )

    parser.add_argument(
        "-c", "--config", required=True,
        help="Path to configuration file to load.",
        type=str
    )
    return parser


class DataLogger:

    _logger = logging.getLogger(f"{__module__}.{__qualname__}")
    DATETIME_FORMAT_FILE_SAFE = "%m_%d_%Y - %I-%M %p"
    DATETIME_FORMAT_MYSQL = "%Y-%m_%d %I:%M:%S"

    def __init__(self, plc: LogixDriver, data_save_folder: str, config: DataLoggerConfig):
        """Creates a data logger.

        Args:
            plc (LogixDriver): ControlLogix or CompactLogix PLC to communicate with.
            data_save_folder (str): Folder path used for saving log data to.
            config (DataLoggerConfig): Configuration of data to log.
        """
        self._logger.info("Initalizing data logger.")
        self.plc = plc
        self.data_save_folder = data_save_folder
        self.start_date = datetime.now()
        self.config = config
        self.running = True
    
    def validate_tags(self) -> bool:
        self._logger.info(f"Validating {len(self.config.tags)} tags.")
        all_tags_valid = True

        for tag in self.config.tags:
            try:
                tag.update(self.plc)
                if tag.valid:
                    continue
                all_tags_valid = False
                self._logger.warning(f"Tag '{tag.name}' could not be found in the controller.")
            except Exception:
                all_tags_valid = False
                self._logger.warning(f"Tag '{tag.name}' could not be found in the controller.")
        if all_tags_valid:
            self._logger.info("All tags valid.")
        return all_tags_valid
    
    def update_tags(self) -> None:
        for tag in self.config.tags:
            tag.update(self.plc)

    def log_data(self, writer: csv.DictWriter) -> dict:
        data = {}
        data["Timestamp"] = datetime.now().strftime(self.DATETIME_FORMAT_MYSQL)
        for tag in self.config.tags:
            data[tag.description] = tag.value
        writer.writerow(data)
        return data
    
    def log(self) -> None:
        loops = 0

        if not self.validate_tags():
            self._logger.error("Not all tags are valid for the selected controller. Closing logger.")
            exit()
        
        fieldnames = []
        fieldnames.append("Timestamp")
        fieldnames.extend([tag.description for tag in self.config.tags])
        current_date_file_safe = self.start_date.strftime(self.DATETIME_FORMAT_FILE_SAFE)
        file_path = path.join(self.data_save_folder, f"{current_date_file_safe}.csv")
        self._logger.info("Initalizing log file.")
        with open(file_path, "a") as file:
            writer = csv.DictWriter(file, delimiter=',', quotechar='"', lineterminator="\r", quoting=csv.QUOTE_ALL, fieldnames=fieldnames)
            self._logger.info(f"Creating headers.")
            writer.writeheader()

            self._logger.info("Starting data logger.")
            while self.running:
                loops += 1
                try:
                    start_time = perf_counter()
                    self.update_tags()
                    data = self.log_data(writer)
                    end_time = perf_counter()
                    run_time = end_time - start_time

                    if run_time < self.config.sampling_interval:
                        delay_time = self.config.sampling_interval - run_time
                        sleep(delay_time)
                    
                    end_time = perf_counter()
                    run_time = end_time - start_time
                    percentage = ((run_time / self.config.sampling_interval) * 100)

                    # Log data after 10 seconds.
                    if (run_time * loops) >= 10:
                        self._logger.info(f"Data: {data}")
                        self._logger.info(f"[EXECUTION TIME] {run_time:.4f} seconds. Precentage of sample interval {percentage:.4f}%")
                        loops = 0

                except KeyboardInterrupt:
                    self._logger.info("Closing.")
                    self.running = False
                except Exception as error:
                    self._logger.info("Closing.")
                    self._logger.exception(f"Error: {error}.")
                    self.running = False
        

def main(config_file_path: str) -> None:
    data_logger_config = DataLoggerConfig.from_path(config_file_path)

    global_logger.info(f"=" * 80)
    global_logger.info(f"Starting v{PROGRAM_VERSION}")
    global_logger.info("Connecting to PLC.")
    with LogixDriver(data_logger_config.plc_ip_address) as plc:
        global_logger.info(f"Connected to PLC: '{plc.name}'")
        global_logger.info(f"Sampling interval: {data_logger_config.sampling_interval} seconds.")

        data_logger = DataLogger(plc, DATA_FOLDER, data_logger_config)
        data_logger.log()


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()

    config_file_path = args.config
    main(config_file_path)