import argparse
from pathlib import Path
from .client import GCSClient
from .permissions_checker import print_detailed_report

def main():
    p = argparse.ArgumentParser(prog="gcs-easy", description="Simple CLI for GCS")
    sub = p.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("upload")
    up.add_argument("--bucket", required=True)
    up.add_argument("--src", required=True)
    up.add_argument("--dst", required=True)
    up.add_argument("--public", action="store_true")

    down = sub.add_parser("download")
    down.add_argument("--bucket", required=True)
    down.add_argument("--src", required=True)
    down.add_argument("--dst", required=True)

    ls = sub.add_parser("list")
    ls.add_argument("--bucket", required=True)
    ls.add_argument("--prefix", default="")

    url = sub.add_parser("sign")
    url.add_argument("--bucket", required=True)
    url.add_argument("--path", required=True)
    url.add_argument("--minutes", type=int, default=15)

    perm = sub.add_parser("permissions", description="Check GCS permissions and configuration")
    perm.add_argument("--bucket", help="Bucket name to check (optional, uses default from config)")

    args = p.parse_args()
    client = GCSClient(default_bucket=args.bucket)

    if args.cmd == "upload":
        client.upload_file(args.src, args.dst, make_public=args.public)
        print("OK")
    elif args.cmd == "download":
        client.download_file(args.src, args.dst)
        print("OK")
    elif args.cmd == "list":
        for name in client.list(prefix=args.prefix):
            print(name)
    elif args.cmd == "sign":
        from datetime import timedelta
        url = client.signed_url(args.path, expires=timedelta(minutes=args.minutes))
        print(url)
    elif args.cmd == "permissions":
        # Permissions command doesn't need a client, just print the report
        print_detailed_report()

if __name__ == "__main__":
    main()