"""DayBetter API client."""

import aiohttp
import logging
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import DayBetterError, AuthenticationError, APIError

_LOGGER = logging.getLogger(__name__)


class DayBetterClient:
    """DayBetter API client."""
    
    # 测试环境URL
    TEST_BASE_URL = "https://cloud.v2.dbiot.link/daybetter/hass/api/v1.0/"
    # 正式环境URL
    PROD_BASE_URL = "https://a.dbiot.org/daybetter/hass/api/v1.0/"
    
    def __init__(
        self, 
        token: str, 
        base_url: Optional[str] = None,
        hass_code: Optional[str] = None
    ):
        """Initialize the client.
        
        Args:
            token: Authentication token
            base_url: Base URL for the API (optional, will be determined by hass_code if not provided)
            hass_code: Home Assistant integration code (optional, if provided and starts with "db-", 
                      will use production environment)
        """
        self.token = token
        
        # 根据 hass_code 或 base_url 确定使用的环境
        if base_url is not None:
            # 如果明确指定了 base_url，使用指定的 URL
            self.base_url = base_url
        elif hass_code is not None and hass_code.startswith("db-"):
            # 如果 hass_code 以 "db-" 开头，使用正式环境
            self.base_url = self.PROD_BASE_URL
            _LOGGER.debug("Using production environment based on hass_code")
        else:
            # 默认使用测试环境
            self.base_url = self.TEST_BASE_URL
            _LOGGER.debug("Using test environment")
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_valid = True
        self._devices: List[Dict[str, Any]] = []
        self._pids: Dict[str, Any] = {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {"Authorization": f"Bearer {self.token}"}
    
    async def fetch_devices(self) -> List[Dict[str, Any]]:
        """Fetch devices from API.
        
        Returns:
            List of device dictionaries
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        try:
            session = self._get_session()
            url = f"{self.base_url}hass/devices"
            headers = self._get_headers()
            
            async with session.post(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    devices = data.get("data", [])
                    _LOGGER.debug("Fetched %d devices", len(devices))
                    self._auth_valid = True
                    return devices
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Failed to fetch devices: %s", error_text)
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception("Client error while fetching devices: %s", e)
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception("Exception while fetching devices: %s", e)
            raise DayBetterError(f"Unexpected error: {e}")
    
    async def fetch_pids(self) -> Dict[str, Any]:
        """Fetch device type PIDs.
        
        Returns:
            Dictionary of device type PIDs
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        try:
            session = self._get_session()
            url = f"{self.base_url}hass/pids"
            headers = self._get_headers()
            
            async with session.post(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._auth_valid = True
                    return data.get("data", {})
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Failed to fetch PIDs: %s", error_text)
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception("Client error while fetching PIDs: %s", e)
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception("Exception while fetching PIDs: %s", e)
            raise DayBetterError(f"Unexpected error: {e}")
    
    async def control_device(
        self,
        device_name: str,
        action: bool,
        brightness: Optional[int] = None,
        hs_color: Optional[Tuple[float, float]] = None,
        color_temp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Control a device.
        
        Args:
            device_name: Name of the device to control
            action: Switch action (True/False)
            brightness: Brightness value (0-255)
            hs_color: Hue and saturation tuple (hue, saturation)
            color_temp: Color temperature in mireds
            
        Returns:
            Control result dictionary
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        session = self._get_session()
        url = f"{self.base_url}hass/control"
        headers = self._get_headers()
        
        # Priority: color temperature > color > brightness > switch
        if color_temp is not None:
            # Convert mireds to Kelvin
            kelvin = int(1000000 / color_temp)
            payload = {
                "deviceName": device_name,
                "type": 4,  # Type 4 is color temperature control
                "kelvin": kelvin,
            }
        elif hs_color is not None:
            h, s = hs_color
            v = (brightness / 255) if brightness is not None else 1.0
            payload = {
                "deviceName": device_name,
                "type": 3,
                "hue": h,
                "saturation": s / 100,
                "brightness": v,
            }
        elif brightness is not None:
            payload = {
                "deviceName": device_name, 
                "type": 2, 
                "brightness": brightness
            }
        else:
            # Type 1 control switch is used by default
            payload = {
                "deviceName": device_name, 
                "type": 1, 
                "on": action
            }
        
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    self._auth_valid = True
                    return await resp.json()
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error(
                        "Failed to control device %s: HTTP %d - %s", 
                        device_name, resp.status, error_text
                    )
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception(
                "Client error while controlling device %s: %s", device_name, e
            )
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception(
                "Exception while controlling device %s: %s", device_name, e
            )
            raise DayBetterError(f"Unexpected error: {e}")
    
    async def fetch_mqtt_config(self) -> Dict[str, Any]:
        """Fetch MQTT connection configuration.
        
        Returns:
            MQTT configuration dictionary
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        session = self._get_session()
        url = f"{self.base_url}hass/cert"
        headers = self._get_headers()
        _LOGGER.debug("Requesting MQTT configuration URL: %s", url)
        
        try:
            async with session.post(url, headers=headers) as resp:
                _LOGGER.debug("MQTT configuration API response status: %d", resp.status)
                
                if resp.status == 200:
                    data = await resp.json()
                    _LOGGER.debug("MQTT configuration API raw response: %s", data)
                    self._auth_valid = True
                    return data.get("data", {})
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Failed to fetch MQTT config: %s", error_text)
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception("Client error while fetching MQTT config: %s", e)
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception("Exception while fetching MQTT config: %s", e)
            raise DayBetterError(f"Unexpected error: {e}")
    
    async def fetch_device_statuses(self) -> List[Dict[str, Any]]:
        """Fetch statuses for all devices.
        
        Returns:
            List of device status dictionaries. Example item:
            {
                "deviceName": str,
                "type": int,
                "online": bool,
                "temp": int,
                "humi": int,
                "bettery": int
            }
        
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        try:
            session = self._get_session()
            url = f"{self.base_url}hass/status"
            headers = self._get_headers()
            
            async with session.post(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._auth_valid = True
                    # API expected to return { "data": [...] }
                    return data.get("data", [])
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Failed to fetch device statuses: %s", error_text)
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception("Client error while fetching device statuses: %s", e)
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception("Exception while fetching device statuses: %s", e)
            raise DayBetterError(f"Unexpected error: {e}")
    
    async def integrate(self, hass_code: str) -> Dict[str, Any]:
        """Integrate with Home Assistant using hassCode.
        
        Args:
            hass_code: Home Assistant integration code from APP
            
        Returns:
            Integration result dictionary
            
        Raises:
            APIError: If API request fails
        """
        # 根据 hass_code 动态更新 base_url（如果之前没有明确指定）
        # 如果 hass_code 以 "db-" 开头，切换到正式环境
        if hass_code.startswith("db-") and self.base_url != self.PROD_BASE_URL:
            old_url = self.base_url
            self.base_url = self.PROD_BASE_URL
            _LOGGER.info(
                "Switching to production environment based on hass_code. "
                "URL changed from %s to %s", old_url, self.base_url
            )
        elif not hass_code.startswith("db-") and self.base_url != self.TEST_BASE_URL:
            # 如果 hass_code 不以 "db-" 开头，且当前不是测试环境，切换到测试环境
            old_url = self.base_url
            self.base_url = self.TEST_BASE_URL
            _LOGGER.info(
                "Switching to test environment based on hass_code. "
                "URL changed from %s to %s", old_url, self.base_url
            )
        
        try:
            session = self._get_session()
            url = f"{self.base_url}hass/integrate"
            payload = {"hassCode": hass_code}
            
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    _LOGGER.debug("Integration successful: %s", data)
                    return data
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Failed to integrate: %s", error_text)
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception("Client error while integrating: %s", e)
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception("Exception while integrating: %s", e)
            raise DayBetterError(f"Unexpected error: {e}")
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the API client is authenticated."""
        return self._auth_valid
    
    def filter_sensor_devices(
        self,
        devices: List[Dict[str, Any]],
        pids: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Filter devices to only include sensors based on PID.
        
        Args:
            devices: List of all devices
            pids: Dictionary containing device type PIDs
            
        Returns:
            List of sensor devices only
        """
        sensor_pids_str = pids.get("sensor", "")
        if not sensor_pids_str:
            return []

        sensor_pids = {pid.strip() for pid in sensor_pids_str.split(",")}

        return [
            device
            for device in devices
            if device.get("deviceMoldPid", "") in sensor_pids
        ]
    
    def merge_device_status(
        self,
        devices: List[Dict[str, Any]],
        statuses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge device info with status info.
        
        Args:
            devices: List of device info dictionaries
            statuses: List of device status dictionaries
            
        Returns:
            List of merged device dictionaries
        """
        status_dict = {status.get("deviceName"): status for status in statuses}

        merged = []
        for device in devices:
            device_name = device.get("deviceName")
            merged_device = device.copy()

            if device_name in status_dict:
                merged_device.update(status_dict[device_name])

            merged.append(merged_device)

        return merged
    
    async def fetch_sensor_data(self) -> List[Dict[str, Any]]:
        """Fetch and process sensor data in one call.
        
        This method fetches device statuses, devices list, and PIDs,
        filters for sensor devices, and merges the data.
        
        Returns:
            List of sensor devices with merged status data
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        # Fetch current statuses
        statuses = await self.fetch_device_statuses()
        
        # Fetch devices and PIDs if not cached
        if not self._devices or not self._pids:
            self._devices = await self.fetch_devices()
            self._pids = await self.fetch_pids()
        
        # Filter to sensor devices only
        sensor_devices = self.filter_sensor_devices(self._devices, self._pids)
        
        # Merge with current status
        merged = self.merge_device_status(sensor_devices, statuses)
        _LOGGER.debug("Fetched %d sensor devices", len(merged))
        return merged
    
    async def close(self):
        """Close the client session."""
        if self._session:
            await self._session.close()
            self._session = None
