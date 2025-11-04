"""
    Trust Platform core package - cloud_connect module
"""
from .cloud_connect import CloudConnect

__all__ = ["CloudConnect"]

try:
    from .aws_connect import AWSConnect, AWSZTKitError

    __all__ += ["AWSZTKitError", "AWSConnect"]

except ModuleNotFoundError:
    pass

try:
    from .azure_connect import AzureConnect, AzureConnectBase
    from .azure_sdk import AzureSDK, AzureSDK_IotAuthentication, AzureSDK_RTOS
    from .azureRTOS_connect import AzurertosConnect, make_valid_filename

    __all__ += ["AzureConnect", "AzurertosConnect", "make_valid_filename", "AzureSDK", "AzureSDK_IotAuthentication", "AzureSDK_RTOS", "AzureConnectBase"]
except ModuleNotFoundError:
    pass

try:
    from .gcp_connect import GCPConnect

    __all__ += ["GCPConnect"]
except ModuleNotFoundError:
    pass
