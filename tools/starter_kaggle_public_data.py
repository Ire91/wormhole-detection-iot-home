import argparse
import os
from kaggle.api.kaggle_api_extended import KaggleApi


def download_unsw_nb15(dataset_slug: str, dest_dir: str = "data/public/unsw_nb15") -> str:
    """Download the UNSW-NB15 dataset using the official Kaggle API.

    This returns the path to the downloaded (and unzipped) data directory.
    """
    os.makedirs(dest_dir, exist_ok=True)
    api = KaggleApi()
    api.authenticate()
    # The API will download and unzip files into dest_dir
    api.dataset_download_files(dataset=dataset_slug, path=dest_dir, unzip=True, quiet=False)
    # Return the path we targeted; users can inspect contents
    return os.path.abspath(dest_dir)


def main():
    parser = argparse.ArgumentParser(description="Starter Kaggle public data download for UNSW-NB15")
    parser.add_argument("slug", help="Dataset slug on Kaggle (e.g., UNSW-NB15) or full slug 'owner/dataset' if needed")
    parser.add_argument("dest", nargs="?", default="data/public/unsw_nb15", help="Destination directory for dataset")
    args = parser.parse_args()
    path = download_unsw_nb15(args.slug, args.dest)
    print("Downloaded dataset to:", path)


if __name__ == "__main__":
    main()
