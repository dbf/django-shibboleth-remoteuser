import re
from typing import List
from urllib.parse import unquote

from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.models import Group
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured

from shibboleth import settings


class ShibbolethRemoteUserMiddleware(RemoteUserMiddleware):
    """
    Authentication Middleware for use with Shibboleth.  Uses the recommended pattern
    for remote authentication from: http://code.djangoproject.com/svn/django/tags/releases/1.3/django/contrib/auth/middleware.py
    --> site not available anymore
    """

    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class."
            )

        # Locate the remote user header.
        try:
            username = request.META[self.header]
            if settings.UNQUOTE_ATTRIBUTES:
                username = unquote(username)
        except KeyError:
            # If specified header doesn't exist then return (leaving
            # request.user set to AnonymousUser by the
            # AuthenticationMiddleware).
            return
        # If we got an empty value for request.META[self.header], treat it like
        #   self.header wasn't in self.META at all - it's still an anonymous user.
        if not username:
            return
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        is_authenticated = request.user.is_authenticated
        if is_authenticated:
            if request.user.username == self.clean_username(username, request):
                return

        # Make sure we have all required Shiboleth elements before proceeding.
        shib_meta, error = self.parse_attributes(request)
        # Add parsed attributes to the session.
        request.session["shib"] = shib_meta
        if error:
            raise ShibbolethValidationError(
                "All required Shibboleth elements" " not found.  %s" % shib_meta
            )

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(request, remote_user=username, shib_meta=shib_meta)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)

            # Upgrade user groups if configured in the settings.py
            # If activated, the user will be associated with those groups.
            if settings.GROUP_ATTRIBUTES:
                self.update_user_groups(request, user)
            # call make profile.
            self.make_profile(user, shib_meta)
            # setup session.
            self.setup_session(request)

    def make_profile(self, user, shib_meta):
        """
        This is here as a stub to allow subclassing of ShibbolethRemoteUserMiddleware
        to include a make_profile method that will create a Django user profile
        from the Shib provided attributes.  By default it does nothing.
        """
        return

    def setup_session(self, request):
        """
        If you want to add custom code to setup user sessions, you
        can extend this.
        """
        return

    def update_user_groups(self, request, user):
        groups = self.parse_group_attributes(request)
        # Remove the user from all groups that are not specified in the shibboleth metadata
        for group in user.groups.all():
            if group.name not in groups:
                group.user_set.remove(user)
        # Add the user to all groups in the shibboleth metadata
        for g in groups:
            group, created = Group.objects.get_or_create(name=g)
            group.user_set.add(user)

    @staticmethod
    def parse_attributes(request):
        """
        Parse the incoming Shibboleth attributes and convert them to the internal data structure.
        From: https://github.com/russell/django-shibboleth/blob/master/django_shibboleth/utils.py
        Pull the mapped attributes from the apache headers.
        """
        shib_attrs = {}
        error = False
        meta = request.META
        for header, attr in list(settings.ATTRIBUTE_MAP.items()):
            if len(attr) == 3:
                required, name, attr_processor = attr
            else:
                required, name = attr
                attr_processor = lambda x: x  # noqa: E731
            value = meta.get(header, None)
            if value:
                if settings.UNQUOTE_ATTRIBUTES:
                    value = unquote(value)
                shib_attrs[name] = attr_processor(value)
            elif required:
                error = True
        return shib_attrs, error

    @staticmethod
    def parse_group_attributes(request):
        """
        Parse the Shibboleth attributes for the GROUP_ATTRIBUTES and generate a list of them.
        """
        groups: List[str] = []
        for attr in settings.GROUP_ATTRIBUTES:
            value = request.META.get(attr, "")
            if settings.UNQUOTE_ATTRIBUTES:
                value = unquote(value)
            parsed_groups = re.split("|".join(settings.GROUP_DELIMITERS), value)
            groups += filter(bool, parsed_groups)
        return groups


class ShibbolethValidationError(Exception):
    pass
