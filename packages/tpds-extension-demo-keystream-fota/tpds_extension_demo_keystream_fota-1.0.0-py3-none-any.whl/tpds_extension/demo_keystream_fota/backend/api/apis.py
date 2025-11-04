# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.
import os
import shutil
from tpds.settings import TrustPlatformSettings
from fastapi.routing import APIRouter
from ..FOTA.api import fota_demo_api

# Create a new router for the FOTA demo
fota_demo = APIRouter(tags=["FOTA_DEMO_APIs"])
fota_demo.include_router(fota_demo_api)

demo_dir = os.path.join(TrustPlatformSettings().get_base_folder(), "keystream_fota_demo")
os.makedirs(demo_dir, exist_ok=True)
resources_path = os.path.join(os.path.dirname(__file__), "..", "resources")
for file in os.listdir(resources_path):
    shutil.copy2(os.path.join(resources_path, file), demo_dir)
