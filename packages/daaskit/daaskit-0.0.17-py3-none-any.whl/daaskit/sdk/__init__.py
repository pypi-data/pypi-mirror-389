import atexit
import daaskit.sdk.apis as DaasApis

atexit.register(DaasApis.cleanup)