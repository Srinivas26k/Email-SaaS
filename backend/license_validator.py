"""License validation using Google Sheets. Supports DB settings (no .env required)."""
import requests
import pandas as pd
from datetime import datetime

from backend.config import config as env_config


class LicenseValidationError(Exception):
    pass


def _get_license_config():
    """Get license_sheet_url and license_key from DB first, then env."""
    try:
        from backend.settings_service import get_app_settings
        settings = get_app_settings()
        url = (settings.get("license_sheet_url") or "").strip()
        key = (settings.get("license_key") or "").strip()
        if url or key:
            return url, key
    except Exception:
        pass
    return (getattr(env_config, "LICENSE_SHEET_URL", None) or "").strip(), (
        getattr(env_config, "LICENSE_KEY", None) or ""
    ).strip()


def validate_license(license_key: str = None, license_sheet_url: str = None) -> bool:
    """
    Validate license by fetching Google Sheet CSV.
    Uses DB settings then env for URL and key if not passed.
    """
    sheet_url = license_sheet_url
    key = license_key
    if sheet_url is None or key is None:
        url_from_config, key_from_config = _get_license_config()
        if sheet_url is None:
            sheet_url = url_from_config
        if key is None:
            key = key_from_config

    if not key:
        raise LicenseValidationError("No license key provided")
    if not sheet_url:
        raise LicenseValidationError("License sheet URL not configured")

    try:
        response = requests.get(sheet_url, timeout=10)
        response.raise_for_status()
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        required_columns = ["license_key", "status", "expiry_date"]
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            raise LicenseValidationError(
                f"License sheet missing columns: {', '.join(missing)}"
            )
        license_row = df[df["license_key"] == key]
        if license_row.empty:
            raise LicenseValidationError(f"License key not found")
        license_data = license_row.iloc[0]
        status = str(license_data["status"]).strip().upper()
        if status != "ACTIVE":
            raise LicenseValidationError(f"License status is '{status}', must be ACTIVE")
        expiry_str = str(license_data["expiry_date"]).strip()
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                expiry_date = datetime.strptime(expiry_str, fmt)
                break
            except ValueError:
                continue
        else:
            raise LicenseValidationError(f"Invalid expiry date: {expiry_str}")
        if expiry_date < datetime.now():
            raise LicenseValidationError(f"License expired on {expiry_date.strftime('%Y-%m-%d')}")
        return True
    except requests.RequestException as e:
        raise LicenseValidationError(f"Failed to fetch license sheet: {str(e)}")
    except Exception as e:
        if isinstance(e, LicenseValidationError):
            raise
        raise LicenseValidationError(f"License validation failed: {str(e)}")


def validate_on_startup():
    """Validate license on startup. If no license configured (DB or env), allow startup."""
    url, key = _get_license_config()
    if not url or not key:
        print("License not configured. Configure in Settings to enable campaigns.")
        return True
    try:
        validate_license(license_key=key, license_sheet_url=url)
        print("License validated successfully")
        return True
    except LicenseValidationError as e:
        print(f"License validation failed: {e}. Configure in Settings.")
        return True  # Allow startup; user can fix in UI