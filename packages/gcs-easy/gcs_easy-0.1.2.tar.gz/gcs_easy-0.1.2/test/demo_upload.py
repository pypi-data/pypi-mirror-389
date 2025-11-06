#!/usr/bin/env python3
"""
Demo script to upload a file to GCS that stays in the bucket.
This creates a visible file for testing purposes.
"""

import tempfile
from pathlib import Path
from gcs_easy.client import GCSClient


def main():
    print("🚀 GCS Demo Upload")
    print("=" * 50)

    try:
        # Initialize GCS client
        client = GCSClient()
        print(f"✅ Connected to bucket: {client.default_bucket}")

        # Create a demo file
        demo_content = """This is a demo file uploaded to GCS.
Created on: November 5, 2025
This file will remain in the bucket for you to see.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(demo_content)
            temp_file_path = f.name

        try:
            # Upload the file (without cleanup)
            blob_name = "demo/demo_file.txt"
            print(f"📤 Uploading to: {client.default_bucket}/{blob_name}")

            result = client.upload_file(temp_file_path, blob_name)

            print("✅ Upload successful!")
            print(f"   📁 Bucket: {result.bucket}")
            print(f"   📄 Blob: {result.blob}")
            print(f"   📏 Size: {result.size} bytes")
            print(f"   🆔 Generation: {result.generation}")

            # Generate a signed URL so they can view it
            signed_url = client.signed_url(blob_name)
            print(f"\n🔗 View file at: {signed_url}")

            print("\n🎉 File uploaded successfully! You can now see it in your GCS bucket.")
            print("   📍 Location: demo/demo_file.txt")

        finally:
            # Clean up local temp file
            Path(temp_file_path).unlink()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()