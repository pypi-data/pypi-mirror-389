from datasette import hookimpl
from datasette.permissions import PermissionSQL


@hookimpl
def permission_resources_sql(action):
    if action == "permissions-debug":
        return PermissionSQL.allow(reason="datasette-allow-permissions-debug")
