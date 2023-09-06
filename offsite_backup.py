from datetime import datetime
import logging
import fnmatch
import os
import sys
import argparse
import hashlib
import json
import b2sdk.v1 as b2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


directory_to_backup = './backup/'
def read_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)

def setup_logging(log_output_file, log_output_level, to_console=False):
    numeric_level = getattr(logging, log_output_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_output_level}")

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Clear any existing handlers on the root logger
    logging.getLogger().handlers = []

    if not to_console:
        # Create a file handler for logging
        file_handler = logging.FileHandler(log_output_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
    else:
        # Create a console handler for logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

    logging.getLogger().setLevel(numeric_level)



def list_bucket_contents():
    logger.info("Current contents of the bucket:")
    for file_info, _ in bucket.ls(recursive=True):
        # Convert the timestamp from milliseconds to seconds
        timestamp_seconds = file_info.upload_timestamp / 1000
        # Convert the Unix timestamp to a datetime object
        upload_date = datetime.utcfromtimestamp(timestamp_seconds)
        # Format the datetime object as a string
        formatted_date = upload_date.strftime('%Y-%m-%d %H:%M:%S UTC')
        logger.info(f"{file_info.file_name}, uploaded at {formatted_date}, SHA1: {file_info.content_sha1}")


def compute_sha1(file_path):
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)  # read in 64k chunks
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

file_versions_cache = {}

def file_exists_in_bucket(file_name, sha1_hash):
    if file_name not in file_versions_cache:
        file_versions_cache[file_name] = [file_version for file_version in bucket.list_file_versions(file_name)]

    for existing_file_version in file_versions_cache[file_name]:
        if existing_file_version.content_sha1 == sha1_hash:
            return True
    return False

def upload_to_backblaze(directory, folders_to_ignore):
    for root, _, files in os.walk(directory):
        # Check if the directory or any of its parent directories should be ignored
        if any(root.startswith(ignore_pattern.rstrip('/')) for ignore_pattern in folders_to_ignore):
            logger.info(f"Ignoring directory: {root}")
            continue

        for file in files:
            file_path = os.path.join(root, file)
            # Check if the file should be ignored
            if any(fnmatch.fnmatch(file_path, ignore_pattern.rstrip('/')) for ignore_pattern in folders_to_ignore):
                logger.info(f"Ignoring file: {file_path}")
                continue

            try:
                upload_file(file_path, directory)
            except Exception as e:
                logger.error(f"Error occurred while processing file {file_path}: {e}")


def upload_file(file_path, base_directory):
    try:
        # Adjust the start point for the relative path
        relative_path = os.path.relpath(file_path, start="/")  # Get the relative path of the file from the root
        sha1_hash = compute_sha1(file_path)

        if file_exists_in_bucket(relative_path, sha1_hash):
            logger.info(f"File {relative_path} already exists in the bucket. Skipping...")
            return

        logger.info(f"Uploading {file_path}...")
        with open(file_path, 'rb') as file:
            bucket.upload_bytes(file.read(), relative_path)  # Use the relative path as the file name
        logger.info(f"Uploaded {relative_path} successfully!")
    except Exception as e:
        logger.exception(f"Error uploading {relative_path}")




def load_configuration(config_path):
    config = read_config(config_path)
    setup_logging(config["log_output_file"], config["log_output_level"])

    # Set the credentials from the configuration
    KEY_ID = config["credentials"]["keyID"]
    APPLICATION_KEY = config["credentials"]["applicationKey"]
    BUCKET_NAME = config["credentials"]["bucketName"]

    # Initialize B2 SDK after setting the credentials
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    try:
        b2_api.authorize_account("production", KEY_ID, APPLICATION_KEY)
        bucket = b2_api.get_bucket_by_name(BUCKET_NAME)
        return config, b2_api, bucket
    except b2.exception.InvalidAuthToken as e:
        logger.error(f"Failed to authorize account: {e}")
        return None, None, None
    except Exception as e:
        logger.exception(f"Unexpected error occurred during authorization: {e}")
        return None, None, None

def main():
    global KEY_ID, APPLICATION_KEY, BUCKET_NAME  # Declare these as global variables

    parser = argparse.ArgumentParser(description="Offsite backup tool for Backblaze.")
    parser.add_argument('-p', '--print', action='store_true', help="Print the contents of the bucket.")
    parser.add_argument('-s', '--show', action='store_true', help="Show logs in the console instead of writing to a file.")
    parser.add_argument('-c', '--config', metavar='CONFIG_PATH', required=True, help="Path to the configuration file.")

    args = parser.parse_args()

    # Load configuration
    config = read_config(args.config)

    # Setup logging
    if args.show:
        setup_logging(None, config["log_output_level"], to_console=True)
    else:
        setup_logging(config["log_output_file"], config["log_output_level"])

    # Set the credentials from the configuration
    KEY_ID = config["credentials"]["keyID"]
    APPLICATION_KEY = config["credentials"]["applicationKey"]
    BUCKET_NAME = config["credentials"]["bucketName"]

    # Initialize B2 SDK after setting the credentials
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    try:
        b2_api.authorize_account("production", KEY_ID, APPLICATION_KEY)
        global bucket
        bucket = b2_api.get_bucket_by_name(BUCKET_NAME)
    except Exception as e:
        logger.error(f"Error authorizing account: {e}")
        return

    # If the print flag is set, just list the bucket contents and return
    if args.print:
        list_bucket_contents()
        return

    # Process backup
    for folder in config["folders_to_backup"]:
        upload_to_backblaze(folder, config["folders_to_ignore"])

if __name__ == "__main__":
    main()
