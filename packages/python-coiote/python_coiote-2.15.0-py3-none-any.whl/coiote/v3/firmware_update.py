from dataclasses import asdict
from typing import Optional

from requests import Response

from coiote.utils import ApiEndpoint, StringResult, api_call, domain_header, sanitize_request_param, api_call_raw
from coiote.v3.model.firmware_update import FirmwareConfigId, FirmwareUpdateConfig, FirmwareUpdateConfigCreateRequest, FirmwareUpdateConfigCreated, ScheduledBasicFirmwareInfo


class FirmwareUpdate(ApiEndpoint):
    def __init__(
            self, *args, **kwargs
    ):
        super().__init__(*args, **kwargs, api_url="firmwareUpdate")

    @api_call(FirmwareUpdateConfigCreated)
    def create_update_configuration(self, domain: str, createRequest: FirmwareUpdateConfigCreateRequest) -> Response:
        return self.session.post(self.get_url("/configurations"), json=asdict(createRequest), headers=domain_header(domain))

    @api_call_raw
    def delete_update_configuration(self, id: FirmwareConfigId) -> Response:
        return self.session.delete(self.get_url(f"/configurations/{id}"))

    @api_call(FirmwareUpdateConfig)
    def get_update_configuration(self, id: FirmwareConfigId) -> Response:
        return self.session.get(self.get_url(f"/configurations/{id}"))

    @api_call(ScheduledBasicFirmwareInfo)
    def schedule_basic_firmware_upgrade(self, device_id: str, id: FirmwareConfigId, upgrade_name: str) -> Response:
        payload = {
            "fotaName": upgrade_name,
            "fotaConfigId": id,
        }
        return self.session.post(self.get_url(f"/basic/{device_id}"), json=payload)
