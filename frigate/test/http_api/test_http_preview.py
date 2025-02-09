from datetime import datetime

from fastapi.testclient import TestClient

from frigate.models import Previews
from frigate.test.http_api.base_http_test import BaseTestHttp


class TestHttpPReview(BaseTestHttp):
    def setUp(self):
        super().setUp([Previews])
        self.app = super().create_app()

    def _get_previews_in_db(self, ids: list[str]):
        return list(Previews.select(Previews.id).where(Previews.id.in_(ids)).execute())

    ####################################################################################################################
    #######################  GET /preview/{camera_name}/start/{start_ts}/end/{end_ts} Endpoint   #######################
    ####################################################################################################################
    def test_get_preview_within_ts_no_matches(self):
        now = int(datetime.now().timestamp())

        with TestClient(self.app) as client:
            id = "123456.random"
            start_ts = now
            end_ts = start_ts + 2
            camera_name = "front_door"
            # Insert Preview with start/end outside of the time period to search
            super().insert_mock_preview(id, end_ts + 1, end_ts + 2)
            response = client.get(
                f"/preview/{camera_name}/start/{start_ts}/end/{end_ts}"
            )
            assert response.status_code == 404
            response_json = response.json()
            self.assertDictEqual(
                {"success": False, "message": "No previews found."},
                response_json,
            )

    def test_get_preview_within_ts_with_matches(self):
        now = int(datetime.now().timestamp())

        with TestClient(self.app) as client:
            id = "123456.random"
            start_ts = now
            end_ts = start_ts + 2
            camera_name = "front_door"
            super().insert_mock_preview(
                id, start_ts, end_ts, f"/media/frigate/dir/{id}"
            )
            response = client.get(
                f"/preview/{camera_name}/start/{start_ts}/end/{end_ts}"
            )
            assert response.status_code == 200
            response_json = response.json()
            assert len(response_json) == 1
            expected_response = {
                "camera": camera_name,
                "start": start_ts,
                "end": end_ts,
                "type": "video/mp4",
                "src": f"/dir/{id}",
            }
            self.assertEqual(response_json[0], expected_response)

    def test_get_preview_within_ts_with_multiple_matches(self):
        now = int(datetime.now().timestamp())

        with TestClient(self.app) as client:
            # between now - 500 <-> now
            id1 = "1.random"
            super().insert_mock_preview(
                id1, now - 500, now, f"/media/frigate/dir/{id1}"
            )
            # between now <-> now + 500
            id2 = "2.random"
            super().insert_mock_preview(
                id2, now, now + 500, f"/media/frigate/dir/{id2}"
            )
            # between now - 1000 <-> now <-> now + 1000
            id3 = "3.random"
            super().insert_mock_preview(
                id3, now - 1000, now + 1000, f"/media/frigate/dir/{id3}"
            )
            # between now + 1 <-> now + 500 (should not be found in the response)
            id4 = "4.random"
            super().insert_mock_preview(
                id4, now + 1, now + 500, f"/media/frigate/dir/{id4}"
            )
            # between now - 500 <-> now - 1 (should not be found in the response)
            id5 = "5.random"
            super().insert_mock_preview(
                id5, now + 1, now + 500, f"/media/frigate/dir/{id5}"
            )

            start_ts = now
            end_ts = now
            camera_name = "front_door"
            response = client.get(
                f"/preview/{camera_name}/start/{start_ts}/end/{end_ts}"
            )
            assert response.status_code == 200
            response_json = response.json()
            assert len(response_json) == 3

            # id3 comes first since it has the smallest start_time
            # There's actually no guarantee that id1 and id2 come in any order
            expected_event_order = [f"/dir/{id3}", f"/dir/{id1}", f"/dir/{id2}"]
            actual_event_order = [obj["src"] for obj in response_json]
            self.assertEqual(actual_event_order, expected_event_order)

    ####################################################################################################################
    ####################  GET /preview/{year_month}/{day}/{hour}/{camera_name}/{tz_name} Endpoint   ####################
    ####################################################################################################################

    ####################################################################################################################
    ####################  GET /preview/{camera_name}/start/{start_ts}/end/{end_ts}/frames Endpoint   ###################
    ####################################################################################################################
