from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

CREATE_UNKNOWN_USER = getattr(settings, "CREATE_UNKNOWN_USER", True)

ATTRIBUTE_MAP = getattr(
    settings, "SHIBBOLETH_ATTRIBUTE_MAP", {"REMOTE_USER": (True, "username")}
)

# This list of attributes will map to Django permission groups
GROUP_ATTRIBUTES = getattr(settings, "SHIBBOLETH_GROUP_ATTRIBUTES", [])

# If a group attribute is actually a list of groups, define the
# delimiters used to split the list
GROUP_DELIMITERS = getattr(settings, "SHIBBOLETH_GROUP_DELIMITERS", [";"])

LOGIN_URL = getattr(
    settings, "SHIBBOLETH_LOGIN_URL", "/Shibboleth.sso/Login"
)  # revert default to None
if not LOGIN_URL:
    raise ImproperlyConfigured("SHIBBOLETH_LOGIN_URL setting required.")

LOGIN_REDIRECT_URL = getattr(settings, "SHIBBOLETH_LOGIN_REDIRECT_URL", None)
# Optional logout parameters
# This should look like: https://sso.school.edu/idp/logout.jsp?return=%s
# The return url variable will be replaced in the LogoutView.
LOGOUT_URL = getattr(
    settings, "SHIBBOLETH_LOGOUT_URL", "/Shibboleth.sso/Logout"
)  # revert default to None
# LOGOUT_REDIRECT_URL specifies a default logout page that will always be used when
# users logout from Shibboleth.
LOGOUT_REDIRECT_URL = getattr(settings, "SHIBBOLETH_LOGOUT_REDIRECT_URL", None)
# Set to true if you are testing and want to insert sample headers.
MOCK_HEADERS = getattr(settings, "SHIBBOLETH_MOCK_HEADERS", False)
