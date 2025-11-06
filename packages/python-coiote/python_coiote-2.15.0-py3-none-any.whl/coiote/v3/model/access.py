from dataclasses import dataclass

@dataclass
class UserAccess:
    userId: str
    username: str
    isDefaultDomain: bool

@dataclass
class AccessModel:
    domain: str
    userAccesses: list[UserAccess]

@dataclass
class AccessGetResponse:
    accesses: list[AccessModel]

@dataclass
class DefaultAccessPatchRequest:
    defaultDomain: str

@dataclass
class UserAccessPutModel:
    userId: str

@dataclass
class AccessPutRequest:
    userAccesses: list[UserAccessPutModel]