"""License validation system using Google Sheets."""
import requests
import pandas as pd
from datetime import datetime
from backend.config import config


class LicenseValidationError(Exception):
    """Raised when license validation fails."""
    pass


def validate_license(license_key: str = None) -> bool:
    """
    Validate license by fetching Google Sheet CSV.
    
    Args:
        license_key: License key to validate. If None, uses config.LICENSE_KEY
        
    Returns:
        True if license is valid
        
    Raises:
        LicenseValidationError: If license is invalid or validation fails
    """
    key = license_key or config.LICENSE_KEY
    
    if not key:
        raise LicenseValidationError("No license key provided")
    
    if not config.LICENSE_SHEET_URL:
        raise LicenseValidationError("License sheet URL not configured")
    
    try:
        # Fetch Google Sheet CSV
        response = requests.get(config.LICENSE_SHEET_URL, timeout=10)
        response.raise_for_status()
        
        # Parse CSV
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        # Validate required columns
        required_columns = ["license_key", "status", "expiry_date"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise LicenseValidationError(
                f"License sheet missing required columns: {', '.join(missing_columns)}"
            )
        
        # Find license key
        license_row = df[df["license_key"] == key]
        
        if license_row.empty:
            raise LicenseValidationError(f"License key '{key}' not found")
        
        # Get first matching row
        license_data = license_row.iloc[0]
        
        # Check status
        status = str(license_data["status"]).strip().upper()
        if status != "ACTIVE":
            raise LicenseValidationError(f"License status is '{status}', must be 'ACTIVE'")
        
        # Check expiry date
        expiry_str = str(license_data["expiry_date"]).strip()
        try:
            # Try multiple date formats
            for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    expiry_date = datetime.strptime(expiry_str, date_format)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("No valid date format found")
            
            if expiry_date < datetime.now():
                raise LicenseValidationError(
                    f"License expired on {expiry_date.strftime('%Y-%m-%d')}"
                )
                
        except ValueError:
            raise LicenseValidationError(f"Invalid expiry date format: '{expiry_str}'")
        
        return True
        
    except requests.RequestException as e:
        raise LicenseValidationError(f"Failed to fetch license sheet: {str(e)}")
    except Exception as e:
        if isinstance(e, LicenseValidationError):
            raise
        raise LicenseValidationError(f"License validation failed: {str(e)}")


def validate_on_startup():
    """Validate license on application startup."""
    try:
        validate_license()
        print("✅ License validated successfully")
        return True
    except LicenseValidationError as e:
        print(f"❌ LICENSE VALIDATION FAILED: {str(e)}")
        print("Application cannot start without valid license")
        raise
