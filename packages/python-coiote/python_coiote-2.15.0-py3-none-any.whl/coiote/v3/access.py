from dataclasses import asdict

from requests import Response

from coiote.utils import ApiEndpoint, api_call, api_call_raw
from coiote.v3.model.access import AccessGetResponse, DefaultAccessPatchRequest, UserAccessPutModel, AccessPutRequest


class Access(ApiEndpoint):
    def __init__(
            self, *args, **kwargs
    ):
        super().__init__(*args, **kwargs, api_url="access")

    @api_call(AccessGetResponse)
    def get_for_user(self, userId: str) -> Response:
        return self.session.get(self.get_url(), params={"userId": userId})

    @api_call(AccessGetResponse)
    def get_for_domain(self, domainId: str) -> Response:
        return self.session.get(self.get_url(), params={"domain": domainId})

    @api_call(AccessGetResponse)
    def get_for_domain_and_user(self, domainId: str, userId: str) -> Response:
        return self.session.get(self.get_url(), params={"domain": domainId, "userId": userId})

    @api_call_raw
    def patch_default_for_user(self, userId: str, request: DefaultAccessPatchRequest) -> Response:
        return self.session.patch(self.get_url(f"/defaults/{userId}"), json=asdict(request))

    @api_call_raw
    def change_in_domain(self, domainId: str, request: AccessPutRequest) -> Response:
        return self.session.put(self.get_url(f"/{domainId}"), json=asdict(request))

    @api_call_raw
    def delete_for_domain(self, domainId: str) -> Response:
        return self.session.delete(self.get_url(f"/{domainId}"))

    @api_call_raw
    def delete_for_domain_and_user(self, domainId: str, userId) -> Response:
        return self.session.delete(self.get_url(f"/{domainId}"), params={"userId": userId})