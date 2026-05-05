"""

"""
import dotenv
import httpx
import json
import os
from tests.shared import APIBase # noqa
from tests.shared.utils import run_host_script
import textwrap

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


# ===================================== Plugin Actions =====================================
class TestPluginActions(APIBase):

    @classmethod
    def setUpClass(cls):
        pass

    @staticmethod
    def _execute_action(action_id: str, props: dict = None, wait: bool = True, msg_id: str = "test-plugin-action") -> bool | httpx.Response:
        """Post a plugin.executeAction command to the Indigo Web Server API.

        Args:
            action_id (str): The Indigo action ID to execute.
            props (dict): Optional action props to include in the payload.
            wait (bool): Whether to wait for the action to complete before returning.
            msg_id (str): Value for the message ``id`` field, used to identify the call in logs.

        Returns:
            bool | httpx.Response: The HTTP response, or False if the request failed.
        """
        try:
            message: dict = {
                "id":            msg_id,
                "message":       "plugin.executeAction",
                "pluginId":      os.getenv("PLUGIN_ID"),
                "actionId":      action_id,
                "waitUntilDone": wait,
            }
            if props is not None:
                message["props"] = props
            url = f"{os.getenv('URL_PREFIX')}/v2/api/command/?api-key={os.getenv('GOOD_API_KEY')}"
            return httpx.post(url, json=message, verify=False)
        except Exception:
            return False

    def _assert_response(self, result: bool | httpx.Response, msg: str) -> httpx.Response:
        """Assert that the result is a valid HTTP response, not a failed request.

        Args:
            result (bool | httpx.Response): The result from _execute_action.
            msg (str): Assertion failure message.

        Returns:
            httpx.Response: The validated response object.
        """
        self.assertIsInstance(result, httpx.Response, f"Request failed with exception: {msg}")
        return result

    def test_refresh_sensors_now(self):
        """Verify refreshSensorsNow executes successfully via the Indigo Web Server API."""
        result = self._assert_response(
            self._execute_action("refreshSensorsNow",
                                 wait=True,
                                 msg_id="test_refresh_sensors_now"),
            "refreshSensorsNow",
        )
        self.assertEqual(result.status_code, 200, "refreshSensorsNow action call was not successful.")

    def test_send_to_server_action(self):
        """Verify sendToServerAction executes successfully via the Indigo Web Server API."""
        props  = {
            "server":   os.getenv("OWSERVER_IP"),
            "romId":    os.getenv("OWSERVER_DEVICE_ROM_ID"),
            "variable": os.getenv("VARIABLE_NAME"),
            "value":    os.getenv("VARIABLE_VALUE"),
        }
        result = self._assert_response(
            self._execute_action("sendToServerAction",
                                 props=props,
                                 wait=True,
                                 msg_id="test_send_to_server_action"),
            "sendToServerAction",
        )
        self.assertEqual(result.status_code, 200, "sendToServerAction action call was not successful.")
