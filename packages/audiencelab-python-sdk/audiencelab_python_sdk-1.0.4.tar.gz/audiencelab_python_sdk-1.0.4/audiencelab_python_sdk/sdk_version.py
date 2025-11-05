"""
SDK Version and Metadata Module

This module provides centralized version tracking and SDK metadata
for the AudienceLab Python SDK.
"""

class SDKVersion:
    """
    Centralized SDK version and type information.
    
    This class provides constants and methods to retrieve SDK metadata
    that is included in all webhook requests for analytics and debugging.
    """
    
    VERSION = "1.0.4"
    SDK_TYPE = "S2S_python"
    
    @staticmethod
    def get_version():
        """
        Get the SDK version.
        
        Returns:
            str: The SDK version string
        """
        return SDKVersion.VERSION
    
    @staticmethod
    def get_sdk_type():
        """
        Get the SDK type identifier.
        
        Returns:
            str: The SDK type string
        """
        return SDKVersion.SDK_TYPE

