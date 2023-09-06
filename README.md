# Offsite Backup to Backblaze

This repository contains a Python script designed to facilitate offsite backups to the Backblaze cloud storage platform.
## Features

   - Configurable Backup: Define specific folders for backup and specify folders to ignore.
   - Logging: Detailed logging of backup operations with configurable output levels.
   - SHA1 Verification: Ensures the integrity of files by computing and comparing SHA1 hashes.
   - Bucket Listing: Option to list the current contents of the Backblaze bucket.
   - Command-Line Interface: Easily run backups and view bucket contents using command-line arguments.

## Configuration

The backup process is configured using a config.json file. Here's a sample configuration:


```json
{
    "credentials": {
        "keyID": "YOUR_KEY_ID",
        "bucketName": "YOUR_BUCKET_NAME",
        "applicationKey": "YOUR_APPLICATION_KEY"
    },
    "folders_to_backup": ["./backup/", "./data/"],
    "folders_to_ignore": ["./backup/temp/"],
    "log_output_file": "./backup_log.txt",
    "log_output_level": "info"
}
```
   - credentials: Contains the necessary credentials for accessing your Backblaze account.
   - folders_to_backup: List of directories you want to back up.
   - folders_to_ignore: List of directories you want to exclude from the backup.
   - log_output_file: Path to the file where logs will be written.
   - log_output_level: Logging level (e.g., "info", "error").

## Usage

To use the backup script, run the offsite_backup.py with the appropriate command-line arguments:

    -p, --print: Print the contents of the bucket.
    -s, --show: Show logs in the console instead of writing to a file.
    -c, --config CONFIG_PATH: Path to the configuration file.

Example:

```bash
python offsite_backup.py -c path_to_config.json
```

## Dependencies

   - b2sdk: The official Backblaze B2 SDK for Python.

**Note**: Ensure you replace placeholders in the config.json with your actual credentials and configurations before running the backup script.
