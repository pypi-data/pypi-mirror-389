import argparse
import pkg_resources
from pathlib import Path
import shutil

def list_docs():
    package_path = Path(pkg_resources.resource_filename("enterprise_docs", "templates"))
    for f in package_path.glob("*.md"):
        print(f.name)

def copy_docs(destination: str):
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    src = Path(pkg_resources.resource_filename("enterprise_docs", "templates"))
    for f in src.glob("*.md"):
        shutil.copy(f, dest / f.name)
    print(f"✅ Copied docs to {dest.resolve()}")

def main():
    parser = argparse.ArgumentParser(description="Enterprise Docs Manager")
    parser.add_argument("command", choices=["list", "sync"])
    parser.add_argument("--to", default="./docs")
    args = parser.parse_args()

    if args.command == "list":
        list_docs()
    elif args.command == "sync":
        copy_docs(args.to)

if __name__ == "__main__":
    main()