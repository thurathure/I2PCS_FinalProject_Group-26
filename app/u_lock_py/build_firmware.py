import argparse
import logging
import os
import shutil
import subprocess
import sys

from pathlib import Path
from typing import Optional


# ============================================================
# U-LOCK FIRMWARE BUILD MANAGER
# ============================================================
#
# Responsibilities:
#   1. Validate the Arduino development environment.
#   2. Locate the ESP32 firmware source.
#   3. Compile firmware using Arduino CLI.
#   4. Upload compiled firmware to ESP32-C3.
#   5. Monitor ESP32 serial output.
#   6. Manage generated firmware build files.
#   7. Provide useful build diagnostics.
#
# Python manages the development workflow.
# Arduino CLI performs the actual compilation and flashing.
#
# ============================================================


# ---------------- PROJECT CONFIGURATION ----------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FIRMWARE_DIRECTORY = PROJECT_ROOT / "sketch_nov19a"

FIRMWARE_FILE = FIRMWARE_DIRECTORY / "sketch_nov19a.ino"

BUILD_DIRECTORY = Path(__file__).resolve().parent / "firmware_build"

BOARD_FQBN = "esp32:esp32:nologo_esp32c3_super_mini"

SERIAL_BAUD_RATE = 115200

DEFAULT_UPLOAD_SPEED = 115200


ARDUINO_CLI_RELATIVE_PATH = (
    Path("Programs")
    / "Arduino IDE"
    / "resources"
    / "app"
    / "lib"
    / "backend"
    / "resources"
    / "arduino-cli.exe"
)



# ---------------- LOGGING CONFIGURATION ----------------

def configure_logging():
    """
    Configure readable console logging for firmware operations.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    return logging.getLogger("ULockFirmware")


logger = configure_logging()


# ---------------- ENVIRONMENT MANAGEMENT ----------------

class FirmwareEnvironment:
    """
    Detect and validate the local Arduino development environment.

    This class centralizes environment configuration so that
    other parts of the build manager do not need to locate
    Arduino CLI independently.
    """

    def __init__(self):

        self.project_root = PROJECT_ROOT

        self.firmware_directory = FIRMWARE_DIRECTORY

        self.firmware_file = FIRMWARE_FILE

        self.build_directory = BUILD_DIRECTORY

        self.board_fqbn = BOARD_FQBN

        self.cli_path = self._locate_arduino_cli()

    def _locate_arduino_cli(self) -> Path:
        """
        Locate Arduino CLI inside the Arduino IDE installation.
        """

        local_app_data = os.environ.get("LOCALAPPDATA")

        if not local_app_data:
            raise EnvironmentError(
                "Windows LOCALAPPDATA environment variable was not found."
            )

        cli_path = (
            Path(local_app_data)
            / ARDUINO_CLI_RELATIVE_PATH
        )

        if not cli_path.is_file():
            raise FileNotFoundError(
                f"Arduino CLI executable not found: {cli_path}"
            )

        return cli_path

    def validate_project(self):
        """
        Verify that all required project paths exist.
        """

        if not self.project_root.is_dir():
            raise FileNotFoundError(
                f"Project root not found: {self.project_root}"
            )

        if not self.firmware_directory.is_dir():
            raise FileNotFoundError(
                f"Firmware directory not found: "
                f"{self.firmware_directory}"
            )

        if not self.firmware_file.is_file():
            raise FileNotFoundError(
                f"Firmware source not found: {self.firmware_file}"
            )

        if not self.cli_path.is_file():
            raise FileNotFoundError(
                f"Arduino CLI not found: {self.cli_path}"
            )

        logger.info("Project structure validated.")

    def display_configuration(self):
        """
        Display the active firmware configuration.
        """

        print("\n========== U-LOCK BUILD CONFIGURATION ==========")

        print(f"Project root : {self.project_root}")
        print(f"Firmware     : {self.firmware_file}")
        print(f"Board        : {self.board_fqbn}")
        print(f"Arduino CLI  : {self.cli_path}")
        print(f"Build output : {self.build_directory}")

        print("================================================\n")


# ---------------- COMMAND EXECUTION ----------------

class CommandRunner:
    """
    Execute external development tools through Python.

    All Arduino CLI commands pass through this class.

    This provides:
      - Consistent command execution.
      - Centralized error handling.
      - Command logging.
      - Optional live terminal output.
    """

    def __init__(self, cli_path: Path):

        self.cli_path = cli_path

    def execute(
        self,
        arguments: list[str],
        description: str,
        allow_failure: bool = False,
    ) -> subprocess.CompletedProcess:

        command = [
            str(self.cli_path),
            *arguments,
        ]

        logger.info(description)

        logger.debug("Command: %s", command)

        try:

            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

        except FileNotFoundError as error:

            raise RuntimeError(
                "Arduino CLI could not be executed."
            ) from error

        except OSError as error:

            raise RuntimeError(
                f"Failed to execute Arduino CLI: {error}"
            ) from error

        if result.returncode != 0 and not allow_failure:

            raise RuntimeError(
                f"{description} failed with exit code "
                f"{result.returncode}."
            )

        return result


# ---------------- FIRMWARE VALIDATION ----------------

class FirmwareValidator:
    """
    Validate firmware source and build prerequisites.

    This class performs basic checks before compilation.
    It does not modify the original firmware.
    """

    REQUIRED_FILES = (
        "sketch_nov19a.ino",
    )

    REQUIRED_SOURCE_MARKERS = (
        "#include <Arduino.h>",
        "#include <ESP32Servo.h>",
        "#include <BLEDevice.h>",
        "#include <BLEServer.h>",
    )

    def __init__(self, environment: FirmwareEnvironment):

        self.environment = environment

    def validate_files(self):

        logger.info("Checking firmware source files...")

        for filename in self.REQUIRED_FILES:

            path = self.environment.firmware_directory / filename

            if not path.is_file():

                raise FileNotFoundError(
                    f"Required firmware file is missing: {filename}"
                )

        logger.info("Required firmware files found.")

    def validate_source(self):

        logger.info("Checking firmware dependencies...")

        source = self.environment.firmware_file.read_text(
            encoding="utf-8"
        )

        missing_markers = [
            marker
            for marker in self.REQUIRED_SOURCE_MARKERS
            if marker not in source
        ]

        if missing_markers:

            raise ValueError(
                "Firmware source is missing required includes: "
                + ", ".join(missing_markers)
            )

        logger.info("Firmware dependency declarations verified.")

    def validate(self):

        self.environment.validate_project()

        self.validate_files()

        self.validate_source()

        logger.info("Firmware validation completed.")


# ---------------- FIRMWARE BUILDER ----------------

class FirmwareBuilder:
    """
    Manage ESP32 firmware compilation.

    The builder uses the exact board definition detected
    during project configuration.
    """

    def __init__(
        self,
        environment: FirmwareEnvironment,
        runner: CommandRunner,
        validator: FirmwareValidator,
    ):

        self.environment = environment

        self.runner = runner

        self.validator = validator

    def prepare_build_directory(self):

        self.environment.build_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def compile(self):

        print("\n========== U-LOCK FIRMWARE BUILD ==========")

        self.validator.validate()

        self.environment.display_configuration()

        self.prepare_build_directory()

        arguments = [
            "compile",
            "--fqbn",
            self.environment.board_fqbn,
            "--build-path",
            str(self.environment.build_directory),
            str(self.environment.firmware_directory),
        ]

        result = self.runner.execute(
            arguments,
            "Compiling ESP32-C3 firmware...",
        )

        print("\n========== BUILD SUCCESSFUL ==========")

        logger.info("ESP32 firmware compiled successfully.")

        return result


# ---------------- FIRMWARE UPLOADER ----------------

class FirmwareUploader:
    """
    Upload compiled firmware to the ESP32-C3.

    The serial port is supplied by the user to avoid
    accidentally flashing another connected device.
    """

    def __init__(
        self,
        environment: FirmwareEnvironment,
        runner: CommandRunner,
        builder: FirmwareBuilder,
    ):

        self.environment = environment

        self.runner = runner

        self.builder = builder

    @staticmethod
    def validate_port(port: str):

        normalized = port.strip().upper()

        if not normalized.startswith("COM"):

            raise ValueError(
                "Invalid Windows serial port. "
                "Example: COM5"
            )

        if not normalized[3:].isdigit():

            raise ValueError(
                "Serial port must have a numeric COM identifier."
            )

        return normalized

    def upload(self, port: str):

        port = self.validate_port(port)

        # Always compile before uploading.
        self.builder.compile()

        print("\n========== U-LOCK FIRMWARE UPLOAD ==========")

        arguments = [
            "upload",
            "--fqbn",
            self.environment.board_fqbn,
            "--port",
            port,
            "--input-dir",
            str(self.environment.build_directory),
        ]

        self.runner.execute(
            arguments,
            f"Uploading firmware to ESP32 through {port}...",
        )

        print("\n========== UPLOAD SUCCESSFUL ==========")

        logger.info("Firmware uploaded successfully.")


# ---------------- SERIAL MONITOR ----------------

class FirmwareMonitor:
    """
    Open Arduino CLI serial monitoring.

    Serial output is useful for observing:
      - BLE connection events.
      - Servo initialization.
      - LOCK commands.
      - UNLOCK commands.
      - Notification events.
      - Firmware debugging information.
    """

    def __init__(
        self,
        environment: FirmwareEnvironment,
        runner: CommandRunner,
    ):

        self.environment = environment

        self.runner = runner

    def start(
        self,
        port: str,
        baud_rate: int = SERIAL_BAUD_RATE,
    ):

        port = FirmwareUploader.validate_port(port)

        if baud_rate <= 0:

            raise ValueError(
                "Baud rate must be greater than zero."
            )

        print("\n========== U-LOCK SERIAL MONITOR ==========")

        print(f"Port      : {port}")
        print(f"Baud rate : {baud_rate}")

        print("Press Ctrl+C to stop monitoring.\n")

        arguments = [
            "monitor",
            "--port",
            port,
            "--config",
            f"baudrate={baud_rate}",
        ]

        self.runner.execute(
            arguments,
            "Starting ESP32 serial monitor...",
        )


# ---------------- BUILD CLEANER ----------------

class FirmwareCleaner:
    """
    Remove generated firmware build artifacts.

    The original .ino source is never deleted.
    """

    def __init__(self, environment: FirmwareEnvironment):

        self.environment = environment

    def clean(self):

        directory = self.environment.build_directory

        if not directory.exists():

            logger.info("No firmware build directory to clean.")

            return

        logger.info("Removing generated firmware build files...")

        shutil.rmtree(directory)

        logger.info("Firmware build directory cleaned.")


# ---------------- APPLICATION CONTROLLER ----------------

class FirmwareManager:
    """
    Main orchestration class for the U-LOCK firmware workflow.

    All firmware operations are exposed through this class.
    """

    def __init__(self):

        self.environment = FirmwareEnvironment()

        self.runner = CommandRunner(
            self.environment.cli_path
        )

        self.validator = FirmwareValidator(
            self.environment
        )

        self.builder = FirmwareBuilder(
            self.environment,
            self.runner,
            self.validator,
        )

        self.uploader = FirmwareUploader(
            self.environment,
            self.runner,
            self.builder,
        )

        self.monitor = FirmwareMonitor(
            self.environment,
            self.runner,
        )

        self.cleaner = FirmwareCleaner(
            self.environment
        )

    def build(self):

        self.builder.compile()

    def upload(self, port: str):

        self.uploader.upload(port)

    def monitor_serial(
        self,
        port: str,
        baud_rate: int,
    ):

        self.monitor.start(port, baud_rate)

    def clean(self):

        self.cleaner.clean()


# ---------------- COMMAND-LINE INTERFACE ----------------

def create_argument_parser():

    parser = argparse.ArgumentParser(
        prog="build_firmware.py",
        description=(
            "Python-powered U-LOCK ESP32-C3 firmware manager."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="action",
        required=True,
    )

    subparsers.add_parser(
        "build",
        help="Compile ESP32-C3 firmware.",
    )

    upload_parser = subparsers.add_parser(
        "upload",
        help="Compile and upload firmware.",
    )

    upload_parser.add_argument(
        "--port",
        required=True,
        help="ESP32 serial port, for example COM5.",
    )

    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Open ESP32 serial monitor.",
    )

    monitor_parser.add_argument(
        "--port",
        required=True,
        help="ESP32 serial port, for example COM5.",
    )

    monitor_parser.add_argument(
        "--baud",
        type=int,
        default=SERIAL_BAUD_RATE,
        help="Serial baud rate.",
    )

    subparsers.add_parser(
        "clean",
        help="Remove generated firmware build files.",
    )

    return parser


# ---------------- MAIN ENTRY POINT ----------------

def main(
    arguments: Optional[list[str]] = None,
):

    parser = create_argument_parser()

    options = parser.parse_args(arguments)

    try:

        manager = FirmwareManager()

        if options.action == "build":

            manager.build()

        elif options.action == "upload":

            manager.upload(options.port)

        elif options.action == "monitor":

            manager.monitor_serial(
                options.port,
                options.baud,
            )

        elif options.action == "clean":

            manager.clean()

        return 0

    except KeyboardInterrupt:

        logger.warning("Operation interrupted by user.")

        return 130

    except (
        EnvironmentError,
        FileNotFoundError,
        ValueError,
        RuntimeError,
        OSError,
    ) as error:

        logger.error("%s", error)

        return 1


if __name__ == "__main__":

    sys.exit(main())