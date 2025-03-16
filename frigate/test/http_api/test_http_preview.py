from datetime import datetime
from unittest import mock

import pytz
from fastapi.testclient import TestClient

from frigate.const import PREVIEW_FRAME_TYPE
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
    def test_get_previews_time_period_no_matches(self):
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

    def test_get_previews_time_period_with_matches(self):
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

    def test_get_previews_time_period_multiple_matches(self):
        now = int(datetime.now().timestamp())

        with TestClient(self.app) as client:
            previews_to_insert = [
                [now - 500, now],  # id_0
                [now, now + 500],  # id_1
                [now - 500, now - 2],  # id_2 (outside range)
                [now + 2, now + 500],  # id_3 (outside range)
                [now - 1000, now + 1000],  # id_4
            ]
            for index, (start_ts, end_ts) in enumerate(previews_to_insert):
                id = f"id_{index}"
                self.insert_mock_preview(
                    id, start_ts, end_ts, f"/media/frigate/dir/{id}"
                )

            start_ts = now - 1
            end_ts = now + 1
            camera_name = "front_door"
            response = client.get(
                f"/preview/{camera_name}/start/{start_ts}/end/{end_ts}"
            )
            assert response.status_code == 200
            response_json = response.json()
            assert len(response_json) == 3

            # id_4 comes first since it has the smallest start_time
            expected_event_order = ["/dir/id_4", "/dir/id_0", "/dir/id_1"]
            actual_event_order = [obj["src"] for obj in response_json]
            self.assertEqual(actual_event_order, expected_event_order)

    ####################################################################################################################
    ####################  GET /preview/{year_month}/{day}/{hour}/{camera_name}/{tz_name} Endpoint   ####################
    ####################################################################################################################
    def test_get_previews_hour_with_timezone_no_matches(self):
        with TestClient(self.app) as client:
            start_time = datetime(2025, 2, 1, 0, 0, 0, tzinfo=pytz.utc).timestamp()
            time_end = datetime(2025, 2, 1, 6, 59, 59, tzinfo=pytz.utc).timestamp()
            super().insert_mock_preview(
                "123456.random", start_time, time_end, f"/media/frigate/dir/{id}"
            )

            year_month = "2025-02"
            day = 1
            hour = 0
            tz_name = "America,Phoenix"
            camera_name = "front_door"
            # Looks for Previews at 01 February 2025 00:00:00 America/Phoenix timezone
            # This means it will look for Previews starting at 01 February 2025 07:00:00 UTC
            response = client.get(
                f"/preview/{year_month}/{day}/{hour}/{camera_name}/{tz_name}"
            )
            assert response.status_code == 404
            response_json = response.json()
            self.assertDictEqual(
                {"success": False, "message": "No previews found."},
                response_json,
            )

    def test_get_previews_hour_with_timezone_matches(self):
        with TestClient(self.app) as client:
            start_time = datetime(2025, 2, 1, 0, 0, 0, tzinfo=pytz.utc).timestamp()
            time_end = datetime(2025, 2, 1, 9, 0, 0, tzinfo=pytz.utc).timestamp()
            super().insert_mock_preview(
                "123456.random", start_time, time_end, f"/media/frigate/dir/{id}"
            )

            year_month = "2025-02"
            day = 1
            hour = 0
            tz_name = "America,Phoenix"
            camera_name = "front_door"
            # Looks for Previews at 01 February 2025 00:00:00 America/Phoenix timezone
            # This means it will look for Previews starting at 01 February 2025 07:00:00 UTC
            response = client.get(
                f"/preview/{year_month}/{day}/{hour}/{camera_name}/{tz_name}"
            )
            assert response.status_code == 200
            response_json = response.json()
            assert len(response_json) == 1

    ####################################################################################################################
    ####################  GET /preview/{camera_name}/start/{start_ts}/end/{end_ts}/frames Endpoint   ###################
    ####################################################################################################################
    def test_get_preview_frames_time_period_no_matches(self):
        now = int(datetime.now().timestamp())

        with TestClient(self.app) as client:
            with mock.patch("os.listdir") as mocked_listdir:
                start_ts = now
                end_ts = start_ts + 2

                mocked_listdir.return_value = [
                    f"preview_front_door-{start_ts}",
                ]

                id = "123456.random"
                camera_name = "front_door"
                # Insert Preview with start/end outside of the time period to search
                super().insert_mock_preview(id, end_ts + 1, end_ts + 2)
                response = client.get(
                    f"/preview/{camera_name}/start/{start_ts}/end/{end_ts}/frames"
                )
                assert response.status_code == 200
                response_json = response.json()
                assert len(response_json) == 0

    def test_get_preview_frames_time_period_matches(self):
        now = int(datetime.now().timestamp())

        with TestClient(self.app) as client:
            with mock.patch("os.listdir") as mocked_listdir:
                start_ts = now
                end_ts = start_ts + 2

                mocked_listdir.return_value = [
                    f"preview_front_door-{start_ts}.0.{PREVIEW_FRAME_TYPE}",
                    f"preview_front_door-{end_ts}.0.{PREVIEW_FRAME_TYPE}",
                ]

                id = "123456.random"
                camera_name = "front_door"
                # Insert Preview with start/end outside of the time period to search
                super().insert_mock_preview(id, end_ts + 1, end_ts + 2)
                response = client.get(
                    f"/preview/{camera_name}/start/{start_ts}/end/{end_ts}/frames"
                )
                assert response.status_code == 200
                response_json = response.json()
                assert len(response_json) == 2
                self.assertListEqual(
                    response_json,
                    [
                        f"preview_front_door-{start_ts}.0.{PREVIEW_FRAME_TYPE}",
                        f"preview_front_door-{end_ts}.0.{PREVIEW_FRAME_TYPE}",
                    ],
                )
