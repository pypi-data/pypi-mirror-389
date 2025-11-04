# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.
import os
import yaml
import re
import serial
import asyncio
# import subprocess
from pathlib import Path
from pykitinfo import pykitinfo
from fastapi import WebSocket, WebSocketDisconnect
from .helper import remove_line_formating, ResponseModel

from tpds_extension.keystream_connect.backend.key_stream import KeyStream
from tpds.devices import TpdsBoards
from tpds.settings import TrustPlatformSettings


class FOTA_DEMO:
    def __init__(self) -> None:
        self.board_data = {"version": "0.0.0", "app_type": "Light Sensor"}
        self.serial = serial.Serial(
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )
        self.board = "EV89U05A"
        self.board_details = TpdsBoards().get_board_info(self.board)
        self.demo_dir = os.path.join(TrustPlatformSettings().get_base_folder(), "keystream_fota_demo")
        self.ks_creds_file = os.path.join(self.demo_dir, "..", "keystream_config.yaml")
        self.creds = {
            "title": "Wifi credentials, Public Profile UID and keySTREAM Authentication token."
        }
        self.set_board_data_to_default()

    def setup_demo(self):
        response = ResponseModel()
        current_dir = os.getcwd()
        os.makedirs(self.demo_dir, exist_ok=True)
        os.chdir(self.demo_dir)
        try:
            self.get_board_com_port()
            self.connect_to_board()
            self.get_ks_creds_from_file()
            response.status = True
        except Exception as e:
            response.status = False
            response.message = f"Demo Setup failed with error: {e}"
        finally:
            os.chdir(current_dir)
        return response

    def get_board_com_port(self) -> None:
        com_port = None
        kits = pykitinfo.detect_all_kits()
        for kit in kits:
            if kit.get("debugger", {}).get("kitname", "") == self.board_details.kit_name:
                com_port = kit.get("debugger").get("serial_port")
                break

        assert com_port, "Can't Connect to CyrptoAuth PRO Trust Platform Board Please check your connections"
        self.serial.port = com_port

    def connect_to_board(self):
        try:
            # mplab_path = TrustPlatformSettings(log_enable=False).settings.mplab_path
            # assert mplab_path, "MPLAB X path is not set, Please set it in File -> Preferences"
            # assert os.path.exists(mplab_path), "MPLAB X path doesnt exits"
            # mdb_path = get_mdb_path(mplab_path)
            self.serial.open()

            # process = subprocess.Popen(
            #     [mdb_path, os.path.abspath("reset.txt")],
            #     stdout=subprocess.PIPE,
            #     stderr=subprocess.PIPE,
            #     encoding='utf-8',
            #     universal_newlines=True,
            #     shell=True,
            # )
            # for reset_line in process.stdout:
            #     if "halt" in reset_line:
            #         self.serial.reset_input_buffer()
        except Exception as e:
            assert False, f"Serial Port Connection failed with Error: {e}"

    def disconnect_from_board(self) -> None:
        self.serial.close()

    async def update_board_data(self, websocket: WebSocket) -> bool:
        is_ws_closed = False
        response = ResponseModel(data=self.board_data)

        try:
            if not self.serial.is_open:
                self.connect_to_board()
            while True:
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass
                line = self.serial.readline().decode('utf-8', errors="ignore").strip()
                line = remove_line_formating(line)
                if not line:
                    continue

                if line and "[TPDS_DEMO]" in line:
                    self.parse_line(line)
                    response.status = True
                    response.terminal_data = None
                    response.data = self.board_data
                else:
                    response.status = True
                    response.data = None
                    response.terminal_data = line
                await websocket.send_json(response.dict())

        except WebSocketDisconnect:
            is_ws_closed = True
        except Exception as e:
            response.status = False
            response.message = f"Failed to Read Data from Board with error: {e}"
            response.data, response.terminal_data = None, None
            await websocket.send_json(response.dict())
        finally:
            self.disconnect_from_board()
        return is_ws_closed

    def parse_line(self, line: str):
        if "Bootloader Starting" in line:
            self.set_board_data_to_default()
        elif "Signature Verification Success" in line:
            self.board_data |= {"verification": True, "wifi": False}
        elif "Signature Verification Failed" in line:
            self.board_data |= {"verification": False, "wifi": False}
        elif "WiFi Connected" in line:
            self.board_data |= {"wifi": True}
        elif "WiFi Disconnected" in line:
            self.board_data |= {"wifi": False}
        elif "Erased block" in line:
            self.board_data |= {"progress": 0}
        else:
            if version_match := re.search(r'Application Version:\s*(\d+\.\d+\.\d+)', line):
                self.board_data |= {"version": version_match.group(1)}
                patch_version = int(version_match.group(1).split(".")[2])
                self.board_data |= {"app_type": "Light Sensor" if patch_version % 2 == 0 else "Temperature Sensor"}
            if light_match := re.search(r'Light:\s*(-?\d+(?:\.\d+)?)\s*lux', line):
                self.board_data |= {"light": float(light_match.group(1))}
            if temp_match := re.search(r'Temperature:\s*(-?\d+(?:\.\d+)?)\s*C', line):
                self.board_data |= {"temperature": float(temp_match.group(1))}
            if progress_match := re.search(r'Downloaded \d+ bytes - ([\d.]+) %', line):
                self.board_data |= {"progress": float(progress_match.group(1))}

    def get_ks_creds_from_file(self):
        assert os.path.exists(self.ks_creds_file), "KeySTREAM Credentials are not Available"
        self.creds = yaml.safe_load(Path(self.ks_creds_file).read_text(encoding="utf-8"))

    def deploy_firmware(self, firmware_name: str) -> ResponseModel:
        response = ResponseModel()
        current_dir = os.getcwd()
        os.makedirs(self.demo_dir, exist_ok=True)
        os.chdir(self.demo_dir)
        try:
            assert self.board_data.get("app_type") != firmware_name, f"Already {firmware_name} is runnning."
            campaign_name = "DEPLOY_LIGHT" if "light" in firmware_name.lower() else "DEPLOY_TEMPERATURE"
            campaign_update_data = {"percentage": 100, "state": "active"}
            key_stream = KeyStream(self.creds.get("keystream_auth_token"), self.creds.get("pub_uid"))
            key_stream.update_campaign(campaign_name, campaign_update_data)
            response.status = True
            response.message = "Deployment Success!! Download will start soon..."
        except Exception as e:
            response.status = False
            response.message = f"Deployment failed with error: {e}"
        finally:
            os.chdir(current_dir)
        return response

    def set_board_data_to_default(self):
        self.board_data |= {
            "verification": False,
            "wifi": False,
            "progress": 100,
            "light": 0,
            "temprature": 0,
        }
