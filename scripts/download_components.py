import argparse
from pathlib import Path

import requests


def download_components(ref: str):
    # Create components directory
    components_dir = Path("components")
    components_dir.mkdir(exist_ok=True)

    # GitHub API URL for the components directory
    api_url = "https://api.github.com/repos/atlanhq/application-sdk/contents/components"
    params = {"ref": ref}

    # Get list of files
    response = requests.get(api_url, params=params)
    response.raise_for_status()

    # Download each file
    for file_info in response.json():
        if file_info["type"] == "file" and file_info["name"].endswith(".yaml"):
            # Get raw content URL
            raw_url = file_info["download_url"]

            # Download and save file
            file_response = requests.get(raw_url)
            file_response.raise_for_status()

            file_path = components_dir / file_info["name"]
            file_path.write_text(file_response.text)
            print(f"Downloaded: {file_info['name']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download components from Atlan Application SDK"
    )
    parser.add_argument(
        "--ref",
        default="v0.1.1rc5",
        help="Git reference (tag, branch, or commit) to download from",
    )
    args = parser.parse_args()

    download_components(args.ref)
