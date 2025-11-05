#!/usr/bin/env python3
"""
GCS Permissions Checker

This module provides utilities to check and document the required Google Cloud Storage
permissions for different operations performed by the GCSClient.
"""

from typing import Dict, List, Set
import re
from pathlib import Path
import yaml


# GCS IAM Permissions mapping for common operations
GCS_PERMISSIONS = {
    "storage.objects.create": "Upload files to bucket",
    "storage.objects.get": "Download files from bucket",
    "storage.objects.list": "List files in bucket",
    "storage.objects.delete": "Delete files from bucket",
    "storage.objects.getIamPolicy": "Get IAM policy for objects",
    "storage.objects.setIamPolicy": "Set IAM policy for objects",
    "storage.buckets.get": "Get bucket metadata",
    "storage.buckets.create": "Create buckets",
    "storage.buckets.list": "List buckets",
    "storage.buckets.delete": "Delete buckets",
}

# Required permissions for each GCSClient method
METHOD_PERMISSIONS = {
    "upload_file": ["storage.objects.create"],
    "download_file": ["storage.objects.get"],
    "list": ["storage.objects.list"],
    "exists": ["storage.objects.get"],  # Actually needs list permission for the bucket
    "delete": ["storage.objects.delete"],
    "signed_url": ["storage.objects.get"],  # For generating signed URLs
    "__init__": ["storage.buckets.get"],  # To check bucket exists when create_bucket_if_missing=True
}


def get_method_permissions(method_name: str) -> List[str]:
    """Get the required permissions for a specific method."""
    return METHOD_PERMISSIONS.get(method_name, [])


def get_all_permissions() -> Set[str]:
    """Get all unique permissions required by the GCSClient."""
    all_perms = set()
    for perms in METHOD_PERMISSIONS.values():
        all_perms.update(perms)
    return all_perms


def check_service_account_permissions(service_account_email: str = None) -> Dict:
    """
    Check permissions for a service account.
    This is a placeholder - actual implementation would require GCP API calls.
    """
    if service_account_email is None:
        # Try to get from config
        config = load_config()
        creds_path = config.get('GOOGLE_APPLICATION_CREDENTIALS', '')
        if creds_path and Path(creds_path).exists():
            try:
                import json
                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
                    service_account_email = creds_data.get('client_email')
            except:
                pass

    return {
        "service_account": service_account_email,
        "permissions_checked": False,
        "note": "Actual permission checking requires GCP API access"
    }


def find_config_file() -> str:
    """Find the path to the config.yml file."""
    for possible_path in [
        Path(__file__).parent / "config.yml",
        Path(__file__).parent.parent / "config.yml",
        Path.cwd() / "config.yml"
    ]:
        if possible_path.exists():
            return str(possible_path)
    return "config.yml (not found)"


def load_config() -> Dict:
    """Load configuration from config.yml"""
    # Try multiple possible locations for config.yml
    possible_paths = [
        Path(__file__).parent / "config.yml",  # Same directory
        Path(__file__).parent.parent / "config.yml",  # Parent directory
        Path.cwd() / "config.yml",  # Current working directory
    ]

    for config_path in possible_paths:
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
    return {}


def analyze_client_permissions() -> Dict:
    """Analyze all permissions required by GCSClient methods."""
    config = load_config()
    bucket = config.get('default_bucket', 'unknown')

    analysis = {
        "bucket": bucket,
        "methods": {},
        "all_permissions": list(get_all_permissions()),
        "permission_descriptions": {}
    }

    for method, perms in METHOD_PERMISSIONS.items():
        analysis["methods"][method] = {
            "permissions": perms,
            "descriptions": [GCS_PERMISSIONS.get(p, f"Unknown permission: {p}") for p in perms]
        }

    for perm in get_all_permissions():
        analysis["permission_descriptions"][perm] = GCS_PERMISSIONS.get(perm, "Unknown permission")

    return analysis


def print_permissions_report():
    """Print a formatted permissions report."""
    print("GCS Client Permissions Report")
    print("=" * 50)

    analysis = analyze_client_permissions()
    config = load_config()

    print(f"Default Bucket: {analysis['bucket']}")
    print(f"Credentials File: {config.get('GOOGLE_APPLICATION_CREDENTIALS', 'Not configured')}")
    print()

    print("Required Permissions:")
    for perm in analysis['all_permissions']:
        desc = analysis['permission_descriptions'][perm]
        print(f"  - {perm}: {desc}")
    print()

    print("Method-specific Permissions:")
    for method, info in analysis['methods'].items():
        print(f"  {method}():")
        for perm, desc in zip(info['permissions'], info['descriptions']):
            print(f"    - {perm}: {desc}")
        print()

    # Check service account
    sa_check = check_service_account_permissions()
    if sa_check['service_account']:
        print(f"Service Account: {sa_check['service_account']}")
        print(f"Permissions Verified: {sa_check['permissions_checked']}")
        if sa_check.get('note'):
            print(f"Note: {sa_check['note']}")
    else:
        print("Service Account: Not detected")


def generate_iam_policy(permissions: List[str] = None) -> Dict:
    """Generate a sample IAM policy with the required permissions."""
    if permissions is None:
        permissions = list(get_all_permissions())

    return {
        "bindings": [
            {
                "role": "roles/storage.objectAdmin",  # Convenient role that includes most permissions
                "members": [
                    "serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com"
                ]
            }
        ],
        "note": "This is a sample policy. Adjust the role and members as needed.",
        "required_permissions": permissions
    }


def check_credentials_file() -> Dict:
    """Check if the credentials file exists and is readable."""
    config = load_config()
    creds_path = config.get('GOOGLE_APPLICATION_CREDENTIALS')

    if not creds_path:
        return {"status": "missing", "message": "GOOGLE_APPLICATION_CREDENTIALS not configured in config.yml"}

    # Find the config file location first
    config_path = None
    for possible_path in [
        Path(__file__).parent / "config.yml",
        Path(__file__).parent.parent / "config.yml",
        Path.cwd() / "config.yml"
    ]:
        if possible_path.exists():
            config_path = possible_path
            break

    if config_path:
        full_path = config_path.parent / creds_path
    else:
        full_path = Path(creds_path)

    if not full_path.exists():
        return {"status": "not_found", "message": f"Credentials file not found at {full_path}"}

    try:
        with open(full_path, 'r') as f:
            import json
            creds_data = json.load(f)
            service_account = creds_data.get('client_email', 'Unknown')
            project_id = creds_data.get('project_id', 'Unknown')

        return {
            "status": "valid",
            "path": str(full_path),
            "service_account": service_account,
            "project_id": project_id
        }
    except Exception as e:
        return {"status": "invalid", "message": f"Error reading credentials file: {e}"}


def print_detailed_report():
    """Print a detailed permissions and configuration report."""
    print("🔍 GCS Client Detailed Report")
    print("=" * 50)

    # Check credentials
    creds_check = check_credentials_file()
    status_emoji = {
        "valid": "✅",
        "missing": "❌",
        "not_found": "❌",
        "invalid": "⚠️"
    }.get(creds_check['status'], "❓")

    print(f"🔐 Credentials Status: {status_emoji} {creds_check['status'].upper()}")
    if creds_check['status'] == 'valid':
        print(f"   📁 File: {creds_check['path']}")
        print(f"   👤 Service Account: {creds_check['service_account']}")
        print(f"   🏢 Project ID: {creds_check['project_id']}")
    else:
        print(f"   ⚠️  Error: {creds_check.get('message', 'Unknown error')}")
    print()

    # Configuration
    config = load_config()
    print("⚙️  Configuration:")
    for key, value in config.items():
        if 'credentials' in key.lower():
            exists_status = "✅" if Path(value).exists() else "❌" if Path(value).is_absolute() else "⚠️"
            print(f"   {key}: {value} ({exists_status})")
        else:
            print(f"   {key}: {value}")
    print()

    # Permissions analysis
    analysis = analyze_client_permissions()
    
    # Choose emoji based on credential status
    if creds_check['status'] == 'valid':
        perm_emoji = "✅"
        perm_status = "Required GCS Permissions"
    else:
        perm_emoji = "❓"
        perm_status = "Required GCS Permissions (cannot verify without valid credentials)"
    
    print(f"🔑 {perm_status}:")
    for perm in analysis['all_permissions']:
        desc = analysis['permission_descriptions'][perm]
        print(f"   {perm_emoji} {perm}: {desc}")
    print()

    print("👥 Recommended IAM Roles:")
    print("   🛡️  roles/storage.objectAdmin (full object control)")
    print("   📤 roles/storage.objectCreator (upload only)")
    print("   👁️  roles/storage.objectViewer (read only)")
    print()

    # Generate sample gcloud command
    if creds_check.get('service_account'):
        print("🚀 Sample gcloud command to grant permissions:")
        print(f"   gcloud projects add-iam-policy-binding {creds_check.get('project_id', 'YOUR_PROJECT')} \\")
        print(f"     --member=\"serviceAccount:{creds_check['service_account']}\" \\")
        print("     --role=\"roles/storage.objectAdmin\"")


def main():
    """Main function to run the permissions checker."""
    print("🚀 GCS Permissions Checker")
    print("=" * 50)

    try:
        # Load configuration
        config = load_config()
        print("✅ Configuration loaded successfully")
        print(f"   📁 Config file: {find_config_file()}")
        print()

        # Check credentials
        creds_check = check_credentials_file()
        if creds_check['status'] == 'valid':
            print("✅ Credentials validation PASSED")
            print(f"   👤 Service Account: {creds_check['service_account']}")
            print(f"   🏢 Project ID: {creds_check['project_id']}")
        else:
            print(f"❌ Credentials validation FAILED: {creds_check.get('message', 'Unknown error')}")
            print("   ⚠️  Please check your config.yml and credentials file")
            return

        print()

        # Analyze permissions
        analysis = analyze_client_permissions()
        print("🔍 Permissions Analysis:")
        print(f"   📊 Total permissions required: {len(analysis['all_permissions'])}")
        print(f"   📋 Methods analyzed: {len(analysis['methods'])}")
        print()

        # Print detailed report
        print_detailed_report()

        print("\n" + "=" * 50)
        print("🎉 Permissions checker completed successfully!")
        print("   📝 Use the information above to configure your GCS permissions")

    except Exception as e:
        print(f"❌ Error running permissions checker: {e}")
        print("   ⚠️  Please check your configuration and try again")


if __name__ == "__main__":
    main()