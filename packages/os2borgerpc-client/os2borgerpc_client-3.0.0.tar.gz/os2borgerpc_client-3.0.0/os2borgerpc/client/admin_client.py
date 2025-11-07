"""Module for the admin client."""

import requests
import urllib


def get_default_admin():
    """Return the default OS2borgerPCAdmin object."""
    from os2borgerpc.client.config import OS2borgerPCConfig

    conf_data = OS2borgerPCConfig().get_data()
    admin_url = conf_data.get("admin_url", "https://os2borgerpc-admin.magenta.dk")
    client_api_url = "/client-api/"
    return OS2borgerPCAdmin(urllib.parse.urljoin(admin_url, client_api_url))


class OS2borgerPCAdmin(object):
    """API client class for communicating with admin system."""

    def __init__(self, url):
        """According to D107 docstrings are required."""
        # The replacement is there to handle login integrations that explicitly point at
        # admin-xml in their files
        self.url = url.replace("admin-xml", "client-api")

    def client_api_request(self, endpoint, data):
        """Make a request to the client-api."""
        endpoint_url = urllib.parse.urljoin(self.url, endpoint)
        response = requests.post(endpoint_url, json=data)
        if response.ok:
            return response.json()
        else:
            raise Exception(response.text)

    def register_new_computer(self, mac, name, site, configuration):
        """register_new_computer from the admin site rpc module."""
        endpoint = "register_new_computer"
        data = {"mac": mac, "name": name, "site": site, "configuration": configuration}
        return self.client_api_request(endpoint, data)

    def send_status_info(self, pc_uid, job_data):
        """send_status_info from the admin site rpc module."""
        endpoint = "send_status_info"
        data = {"pc_uid": pc_uid, "job_data": job_data}
        return self.client_api_request(endpoint, data)

    def get_instructions(self, pc_uid):
        """get_instructions from the admin site rpc module."""
        endpoint = "get_instructions"
        data = {"pc_uid": pc_uid}
        return self.client_api_request(endpoint, data)

    def push_config_keys(self, pc_uid, config_dict, read_only=False):
        """push_config_keys from the admin site rpc module."""
        endpoint = "push_config_keys"
        data = {"pc_uid": pc_uid, "config_dict": config_dict, "read_only": read_only}
        return self.client_api_request(endpoint, data)

    def push_security_events(self, pc_uid, events_csv):
        """push_security_events from the admin site rpc module."""
        endpoint = "push_security_events"
        data = {"pc_uid": pc_uid, "events_csv": events_csv}
        return self.client_api_request(endpoint, data)

    def citizen_login(self, username, password, pc_uid, prevent_dual_login=False):
        """citizen_login from the admin site rpc module."""
        endpoint = "citizen_login"
        data = {
            "username": username,
            "password": password,
            "pc_uid": pc_uid,
            "prevent_dual_login": prevent_dual_login,
        }
        return self.client_api_request(endpoint, data)

    def citizen_logout(self, citizen_hash):
        """citizen_logout from the admin site rpc module."""
        endpoint = "citizen_logout"
        data = {"citizen_hash": citizen_hash}
        return self.client_api_request(endpoint, data)

    def general_citizen_login(self, pc_uid, integration, value_dict):
        """general_citizen_login from the admin site rpc module."""
        endpoint = "general_citizen_login"
        data = {"pc_uid": pc_uid, "integration": integration, "value_dict": value_dict}
        return self.client_api_request(endpoint, data)

    def general_citizen_logout(self, citizen_hash, log_id):
        """general_citizen_logout from the admin site rpc module."""
        endpoint = "general_citizen_logout"
        data = {"citizen_hash": citizen_hash, "log_id": log_id}
        return self.client_api_request(endpoint, data)

    def sms_login(
        self,
        phone_number,
        message,
        pc_uid,
        require_booking,
        pc_name,
        allow_idle_login=False,
        login_duration=None,
        quarantine_duration=None,
        unlimited_access=False,
    ):
        """sms_login from the admin site rpc module."""
        endpoint = "sms_login"
        data = {
            "phone_number": phone_number,
            "message": message,
            "pc_uid": pc_uid,
            "require_booking": require_booking,
            "pc_name": pc_name,
            "allow_idle_login": allow_idle_login,
            "login_duration": login_duration,
            "quarantine_duration": quarantine_duration,
            "unlimited_access": unlimited_access,
        }
        return self.client_api_request(endpoint, data)

    def sms_login_finalize(
        self,
        phone_number,
        pc_uid,
        require_booking,
        save_log,
        allow_idle_login=False,
        login_duration=None,
        quarantine_duration=None,
    ):
        """sms_login_finalize from the admin site rpc module."""
        endpoint = "sms_login_finalize"
        data = {
            "phone_number": phone_number,
            "pc_uid": pc_uid,
            "require_booking": require_booking,
            "save_log": save_log,
            "allow_idle_login": allow_idle_login,
            "login_duration": login_duration,
            "quarantine_duration": quarantine_duration,
        }
        return self.client_api_request(endpoint, data)

    def sms_logout(self, citizen_hash, log_id):
        """sms_logout from the admin site rpc module."""
        endpoint = "sms_logout"
        data = {"citizen_hash": citizen_hash, "log_id": log_id}
        return self.client_api_request(endpoint, data)
