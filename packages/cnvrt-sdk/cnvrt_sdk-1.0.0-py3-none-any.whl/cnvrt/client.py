"""
CNVRT Python SDK Client

Provides a Python interface to the CNVRT media conversion API with x402 payment support.
"""

import requests
from typing import Optional, Dict, Any, List, BinaryIO
from pathlib import Path

from .exceptions import CNVRTError, PaymentError, ConversionError, ValidationError, NetworkError


class CNVRT:
    """
    CNVRT API Client
    
    Args:
        base_url: Base URL of the CNVRT service (default: https://cnvrt.ing)
        network: Blockchain network to use (default: "base")
        wallet: Optional wallet configuration for automatic payments
        timeout: Request timeout in seconds (default: 120)
    
    Example:
        >>> client = CNVRT()
        >>> result = client.convert(
        ...     url="https://youtube.com/watch?v=example",
        ...     format="mp3",
        ...     quality="best"
        ... )
        >>> print(result["download_url"])
    """
    
    def __init__(
        self,
        base_url: str = "https://cnvrt.ing",
        network: str = "base",
        wallet: Optional[Dict[str, str]] = None,
        timeout: int = 120
    ):
        self.base_url = base_url.rstrip("/")
        self.network = network
        self.wallet = wallet
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "cnvrt-python-sdk/1.0.0"
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request to the CNVRT API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle x402 payment required
            if response.status_code == 402:
                payment_info = response.json()
                raise PaymentError(
                    f"Payment required: {payment_info.get('amount')} USDC on {payment_info.get('network')}"
                )
            
            # Handle other errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text)
                    error_code = error_data.get("code", "UNKNOWN")
                except:
                    error_msg = response.text
                    error_code = "UNKNOWN"
                
                if response.status_code >= 500:
                    raise NetworkError(f"[{error_code}] {error_msg}")
                else:
                    raise CNVRTError(f"[{error_code}] {error_msg}")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection error")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {str(e)}")
    
    def convert(
        self,
        url: Optional[str] = None,
        file: Optional[BinaryIO] = None,
        format: str = "mp4",
        quality: str = "best",
        dry_run: bool = False,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert media from URL or file
        
        Args:
            url: URL of media to convert (YouTube, TikTok, Instagram, etc.)
            file: File-like object to convert
            format: Output format (mp3, mp4, wav, webp, pdf, etc.)
            quality: Quality setting (best, 1080p, 720p, 480p, 360p, audio)
            dry_run: Test without actually converting (no cost)
            idempotency_key: Optional key to prevent duplicate processing
        
        Returns:
            Dict containing download_url, file_size, duration, etc.
        
        Raises:
            PaymentError: If payment is required
            ConversionError: If conversion fails
            ValidationError: If parameters are invalid
        """
        endpoint = "/api/convert"
        
        if dry_run:
            endpoint += "?dryRun=true"
        
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        if url:
            data = {
                "url": url,
                "format": format,
                "quality": quality
            }
            return self._request("POST", endpoint, json=data, headers=headers)
        
        elif file:
            files = {"file": file}
            data = {"format": format}
            return self._request("POST", endpoint, data=data, files=files, headers=headers)
        
        else:
            raise ValidationError("Either url or file must be provided")
    
    def transcribe(
        self,
        url: Optional[str] = None,
        file: Optional[BinaryIO] = None,
        language: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio/video using AI
        
        Args:
            url: URL of media to transcribe
            file: File-like object to transcribe
            language: Optional language code (e.g., "en", "es", "fr")
            idempotency_key: Optional key to prevent duplicate processing
        
        Returns:
            Dict containing transcription text, timestamps, etc.
        """
        endpoint = "/api/transcribe"
        
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        if url:
            data = {"url": url}
            if language:
                data["language"] = language
            return self._request("POST", endpoint, json=data, headers=headers)
        
        elif file:
            files = {"file": file}
            data = {}
            if language:
                data["language"] = language
            return self._request("POST", endpoint, data=data, files=files, headers=headers)
        
        else:
            raise ValidationError("Either url or file must be provided")
    
    def validate(
        self,
        url: Optional[str] = None,
        file_path: Optional[str] = None,
        format: str = "mp4",
        quality: str = "best"
    ) -> Dict[str, Any]:
        """
        Validate request parameters before payment
        
        Args:
            url: URL to validate
            file_path: File path to validate
            format: Output format
            quality: Quality setting
        
        Returns:
            Dict with validation result and any issues
        """
        data = {
            "format": format,
            "quality": quality
        }
        
        if url:
            data["url"] = url
        elif file_path:
            data["file_path"] = file_path
        
        return self._request("POST", "/api/validate", json=data)
    
    def estimate_cost(
        self,
        url: Optional[str] = None,
        file_size: Optional[int] = None,
        operation: str = "convert",
        format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate cost before processing
        
        Args:
            url: URL to estimate cost for
            file_size: File size in bytes
            operation: Operation type (convert, transcribe, etc.)
            format: Output format
        
        Returns:
            Dict with estimated cost breakdown
        """
        data = {"operation": operation}
        
        if url:
            data["url"] = url
        if file_size:
            data["file_size"] = file_size
        if format:
            data["format"] = format
        
        return self._request("POST", "/api/estimate-cost", json=data)
    
    def detect_format(
        self,
        url: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Auto-detect optimal output format
        
        Args:
            url: URL to detect format for
            file_path: File path to detect format for
        
        Returns:
            Dict with suggested formats
        """
        data = {}
        
        if url:
            data["url"] = url
        elif file_path:
            data["file_path"] = file_path
        
        return self._request("POST", "/api/detect-format", json=data)
    
    def get_usage(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
        
        Returns:
            Dict with usage statistics
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return self._request("GET", "/api/usage", params=params)
    
    def get_x402_info(self) -> Dict[str, Any]:
        """
        Get x402 protocol information
        
        Returns:
            Dict with x402 protocol details, networks, and facilitator info
        """
        return self._request("GET", "/supported")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check service health
        
        Returns:
            Dict with health status
        """
        return self._request("GET", "/health")

