from typing import TypedDict

__all__ = ['AuthenticatedUser', 'AuthorizedUser']

class AuthenticatedUser(TypedDict):
    username: str
    email: str
    fullname: str
    description: str

class AuthorizedUser(TypedDict):
    connection_mode_cloud_active: bool
    connection_mode_direct_active: bool
    connection_mode_direct_sso_active: bool
