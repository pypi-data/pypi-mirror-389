"""Custom exceptions for CNVRT SDK"""


class CNVRTError(Exception):
    """Base exception for CNVRT SDK"""
    pass


class PaymentError(CNVRTError):
    """Payment-related errors"""
    pass


class ConversionError(CNVRTError):
    """Conversion-related errors"""
    pass


class ValidationError(CNVRTError):
    """Validation-related errors"""
    pass


class NetworkError(CNVRTError):
    """Network-related errors"""
    pass

