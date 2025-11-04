from daaskit.sdk import util

class CONFIG:
    backend_host: str = util.get_env('ENV_BACKEND_HOST', 'http://ssms-backend:8080')
    extend_api_host: str = util.get_env('ENV_EXT_API_HOST', 'http://light-extendapi:8080')

    admin_name: str = util.get_env('ENV_ADMIN_NAME', 'admin')
    admin_pwd: str = util.get_env('ENV_ADMIN_PWD', 'Admin@123')
    org_domain: str = util.get_env('ENV_ORG_DOMAIN', 'cvxa3663')
