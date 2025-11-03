"""Models for Hinen Open API."""

from typing import Any

from pydantic import BaseModel, Field


class HinenDeviceInfo(BaseModel):
    """hinen device info."""

    id: str = Field(...)
    device_name: str = Field(..., alias="deviceName")
    serial_number: str = Field(..., alias="serialNumber")

    @property
    def get_device_name(self) -> str:
        """Return device_name."""
        return self.device_name

    @property
    def get_id(self) -> str:
        """Return id."""
        return self.id

    @property
    def get_serial_number(self) -> str:
        """Return serial_number."""
        return self.serial_number

class HinenDeviceProperty(BaseModel):
    """hinen device property."""

    identifier: str = Field(..., description="property key")
    name: str = Field(..., description="name")
    value: Any = Field(..., description="value")


class HinenDeviceDetail(BaseModel):
    """hinen device detail."""

    id: str = Field(...)
    device_name: str = Field(..., alias="deviceName")
    serial_number: str = Field(..., alias="serialNumber")
    status: int = Field(...)
    alert_status: int = Field(..., alias="alertStatus")
    properties: list[HinenDeviceProperty] = Field(..., alias="properties")


class HinenDeviceControl(BaseModel):
    """hinen device control."""

    device_id: str = Field(..., alias="deviceId", description="设备ID")
    map: dict[str, Any] = Field(..., description="控制参数映射")

    class Config:
        """配置信息."""

        allow_population_by_field_name = True

