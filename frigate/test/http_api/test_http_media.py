from fastapi.testclient import TestClient

from frigate.config.config import FrigateConfig
from frigate.models import Event, Recordings, ReviewSegment
from frigate.ptz.onvif import OnvifController
from frigate.test.http_api.base_http_test import BaseTestHttp


class TestHttpMedia(BaseTestHttp):
    def setUp(self):
        super().setUp([Event, Recordings, ReviewSegment])
        self.app = super().create_app()

    ####################################################################################################################
    #####################################  GET /{camera_name}/ptz/info Endpoint   ######################################
    ####################################################################################################################
    def test_get_camera_ptz_info_camera_not_found(self):
        with TestClient(self.app) as client:
            camera_name = "non_existent_camera"
            response = client.get(f"/{camera_name}/ptz/info")
            assert response.status_code == 404
            response_json = response.json()
            self.assertDictEqual(
                {"success": False, "message": "Camera not found"},
                response_json,
            )

    def test_get_camera_ptz_info_camera_without_onvif_config_success(self):
        onvif_controller = OnvifController(FrigateConfig(**self.minimal_config), {})
        self.app = super().create_app(onvif=onvif_controller)
        with TestClient(self.app) as client:
            camera_name = "front_door"
            response = client.get(f"/{camera_name}/ptz/info")
            assert response.status_code == 200
            response_json = response.json()
            self.assertDictEqual(
                {},
                response_json,
            )
