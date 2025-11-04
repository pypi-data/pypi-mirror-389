# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
from .FOTA import FOTA_DEMO
from .helper import ResponseModel

fota_demo_api = APIRouter(prefix="/fota_demo")

demo_ins: FOTA_DEMO | None = None


@fota_demo_api.post("/setup")
def fota_setup() -> ResponseModel:
    try:
        global demo_ins
        if not demo_ins:
            demo_ins = FOTA_DEMO()
        return demo_ins.setup_demo()
    except Exception as e:
        return ResponseModel(status=False, message=str(e))


@fota_demo_api.websocket("/ws/")
async def fota_websocket(websocket: WebSocket):
    global demo_ins
    await websocket.accept()
    try:
        assert demo_ins, "DEMO is not initialized. Please setup DEMO!"
        is_ws_closed = await demo_ins.update_board_data(websocket)
        if not is_ws_closed:
            await websocket.close()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json(ResponseModel(status=False, message=str(e)).dict())
        await websocket.close()
    finally:
        demo_ins = None


@fota_demo_api.post("/deploy/{firmware_name}")
def deploy_firmware(firmware_name: str):
    try:
        assert demo_ins, "DEMO is not initialized. Please setup DEMO!"
        return demo_ins.deploy_firmware(firmware_name)
    except Exception as e:
        return ResponseModel(status=False, message=str(e))
