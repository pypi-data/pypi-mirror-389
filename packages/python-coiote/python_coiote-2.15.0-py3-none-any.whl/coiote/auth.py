from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Union

from requests import Session
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_not_result
from urllib.parse import quote as sanitize_param


@dataclass
class Credentials:
    username: str
    password: str


@dataclass
class ServiceAccount:
    realm: str
    client_id: str
    client_secret: str

    def make_token_url(self, coiote_url: str):
        return f"{coiote_url}/iam/realms/{self.realm}/protocol/openid-connect/token"

    def sanitized_id(self):
        return sanitize_param(self.client_id, safe='')

    def sanitized_secret(self):
        return sanitize_param(self.client_secret, safe='')

    def to_token_request_data(self):
        return f"grant_type=client_credentials&client_id={self.sanitized_id()}&client_secret={self.sanitized_secret()}"

    def get_token_request_headers():
        return {"content-type": "application/x-www-form-urlencoded"}


CoioteCredentials = Union[str, Credentials, ServiceAccount]


class AuthType(Enum):
    CREDENTIALS = 1
    RAW_TOKEN = 2
    SERVICE_ACCOUNT = 3


class Authenticator:
    def __init__(
            self,
            url: str,
            session: Session,
            auth: CoioteCredentials
    ):
        self.url = url
        self.session = session
        self.oauth_url = f"{url}/api/auth/oauth_password"
        self.token = None
        self.token_expiration_time = None

        if isinstance(auth, str):
            self.auth_type = AuthType.RAW_TOKEN
            self.token = auth
            self.token_expiration_time = datetime.now() + timedelta(minutes=30)
            self.creds = None
        elif isinstance(auth, Credentials):
            self.auth_type = AuthType.CREDENTIALS
            self.creds = auth
        elif isinstance(auth, ServiceAccount):
            self.auth_type = AuthType.SERVICE_ACCOUNT
            self.creds = auth
        else:
            raise ValueError(
                "You must provide one of the following auth methods: raw token, service account or credentials")

    def _set_headers(self, bearer_token: str):
        self.session.headers.update(
            {"Authorization": f"Bearer {bearer_token}", "API-Client": "coiote-python", "API-Auth": self.auth_type.name})

    def authenticate(self):
        if self.auth_type == AuthType.RAW_TOKEN:
            self._set_headers(self.token)
        elif self.auth_type == AuthType.CREDENTIALS and self.should_acquire_token():
            self.acquire_token()
        elif self.auth_type == AuthType.SERVICE_ACCOUNT and self.should_acquire_token():
            self.acquire_token_for_sa()

    def should_acquire_token(self) -> bool:
        if self.token_expiration_time is None:
            return True
        else:
            return datetime.now() + timedelta(seconds=60) > self.token_expiration_time


    def _extract_token(self, auth_response, allowed_response_code: int = 200):
        if auth_response.status_code == allowed_response_code:
            json = auth_response.json()
            self.token = json['access_token']
            self.token_expiration_time = datetime.now(
            ) + timedelta(seconds=int(json['expires_in']))
            self._set_headers(self.token)
            return True
        elif auth_response.status_code > 500:
            return False
        else:
            raise ValueError(f"Failed to acquire auth token: {auth_response}")
        
    @retry(retry=retry_if_not_result(lambda x: x), wait=wait_exponential(multiplier=1, min=4, max=10),
           stop=stop_after_attempt(5))
    def acquire_token_for_sa(self):
        auth_response = self.session.post(
            url=self.creds.make_token_url(self.url),
            headers=ServiceAccount.get_token_request_headers(),
            data=self.creds.to_token_request_data()
        )
        return self._extract_token(auth_response, allowed_response_code=200)

    @retry(retry=retry_if_not_result(lambda x: x), wait=wait_exponential(multiplier=1, min=4, max=10),
           stop=stop_after_attempt(5))
    def acquire_token(self):
        auth_response = self.session.post(
            url=self.oauth_url, data=asdict(self.creds))
        return self._extract_token(auth_response, allowed_response_code=201)
