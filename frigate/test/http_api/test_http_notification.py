from fastapi.testclient import TestClient

from frigate.models import User
from frigate.test.http_api.base_http_test import BaseTestHttp


class TestHttpNotification(BaseTestHttp):
    def setUp(self):
        super().setUp([User])
        self.app = super().create_app()

    def _get_users_in_db(self, usernames: list[str]):
        return list(User.select().where(User.username.in_(usernames)).execute())

    ####################################################################################################################
    #####################################  GET /notifications/pubkey Endpoint   ########################################
    ####################################################################################################################
    def test_get_notifications_pubkey_notifications_disabled(self):
        with TestClient(self.app) as client:
            response = client.get("/notifications/pubkey")
            assert response.status_code == 400
            response_json = response.json()
            self.assertDictEqual(
                {"success": False, "message": "Notifications are not enabled."},
                response_json,
            )

    def test_get_notifications_pubkey_success(self):
        with TestClient(self.app) as client:
            self.app.frigate_config.notifications.enabled = True
            response = client.get("/notifications/pubkey")
            assert response.status_code == 200
            response_json = response.json()
            self.assertIsInstance(response_json, str)
            self.assertEqual(
                response_json,
                "BCt98BGdXLaUcp4FZDsjXDFL8-W_ho1A4YLI6nwE6zfLRb5ACSV8OQOhkdrs2YAm1d3uC12LlXvKro1-J_dSz6Y",
            )

    ####################################################################################################################
    #####################################  POST /notifications/register Endpoint   #####################################
    ####################################################################################################################
    def test_post_register_notifications_no_sub_provided(self):
        with TestClient(self.app) as client:
            body = {"sub": ""}
            response = client.post("/notifications/register", json=body)
            assert response.status_code == 400
            response_json = response.json()
            self.assertDictEqual(
                {"success": False, "message": "Subscription must be provided."},
                response_json,
            )

    def test_post_register_notifications_user_not_found(self):
        with TestClient(self.app) as client:
            body = {"sub": "some_subscription"}
            headers = {"remote-user": "nonExistentUser"}
            response = client.post(
                "/notifications/register", json=body, headers=headers
            )
            assert response.status_code == 200
            response_json = response.json()
            # Even thought the user does not exist it will still
            # SEE: https://github.com/blakeblackshear/frigate/discussions/16584#discussioncomment-12517081
            self.assertDictEqual(
                {"success": True, "message": "Successfully saved token."},
                response_json,
            )

    def test_post_register_notifications_success(self):
        with TestClient(self.app) as client:
            self.insert_mock_user("admin")
            body = {"sub": "some_subscription"}
            response = client.post("/notifications/register", json=body)
            assert response.status_code == 200
            response_json = response.json()
            self.assertDictEqual(
                {"success": True, "message": "Successfully saved token."},
                response_json,
            )
            users = self._get_users_in_db(["admin"])
            self.assertEqual(users[0].username, "admin")
            self.assertListEqual(users[0].notification_tokens, ["some_subscription"])
