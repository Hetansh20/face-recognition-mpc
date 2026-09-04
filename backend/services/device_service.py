from datetime import datetime
from backend.models.database import db_session, DeviceModel
from backend.services.logging_service import logging_service

class DeviceService:
    def register_or_update_device(self, device_id: str, user_id: int = None, device_name: str = None, platform: str = "Android", app_version: str = None):
        device = db_session.query(DeviceModel).filter(DeviceModel.device_id == device_id).first()
        if not device:
            device = DeviceModel(
                device_id=device_id,
                user_id=user_id,
                device_name=device_name or "Mobile Device",
                platform=platform,
                app_version=app_version,
                status="ACTIVE",
                last_seen=datetime.utcnow()
            )
            db_session.add(device)
        else:
            if user_id: device.user_id = user_id
            if device_name: device.device_name = device_name
            if app_version: device.app_version = app_version
            device.last_seen = datetime.utcnow()

        db_session.commit()
        return self._format_device(device)

    def get_all_devices(self):
        devices = db_session.query(DeviceModel).order_by(DeviceModel.last_seen.desc()).all()
        return [self._format_device(d) for d in devices]

    def update_device_status(self, device_id: str, status: str):
        device = db_session.query(DeviceModel).filter(DeviceModel.device_id == device_id).first()
        if not device: return None
        device.status = status.upper()
        db_session.commit()
        logging_service.log_audit("DEVICE_STATUS_CHANGE", "device", device_id, f"Device status set to {status}")
        return self._format_device(device)

    def _format_device(self, d: DeviceModel) -> dict:
        if not d: return None
        return {
            "id": d.id,
            "device_id": d.device_id,
            "user_id": d.user_id,
            "device_name": d.device_name,
            "platform": d.platform,
            "app_version": d.app_version,
            "status": d.status,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None
        }

device_service = DeviceService()
