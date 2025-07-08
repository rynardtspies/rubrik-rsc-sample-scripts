# Rubrik RSC API Sample - Python

Getting SLA Domain Details

This Python script connects to the Rubrik Security Cloud (RSC) API to retrieve a list of all configured SLA domains and their associated snapshot schedules (hourly, daily, weekly, monthly, and yearly).

## Features

  * **Authentication:** Authenticates with the Rubrik API using Client ID and Client Secret.
  * **Pagination Support:** Handles pagination to retrieve all SLA domains, regardless of the number.
  * **Detailed SLA Information:** Fetches and displays the name, ID, and detailed snapshot schedules (frequency and retention) for each SLA domain.
  * **Session Management:** Securely connects and disconnects from the Rubrik API.

## Prerequisites

Before running the script, ensure you have the following:

  * **Python 3.x:** Installed on your system.
  * **Rubrik Security Cloud Service Account:** With API client credentials (Client ID and Client Secret) that have permissions to read SLA domains.
  * **Required Python Libraries:** Install them using `pip` and the provided `requirements.txt` file.

## Installation

1.  **Clone this repository** (or download the `rubrik_get_sla_details.py` and `requirements.txt` files).

2.  **Install the required Python packages** by running the following command in your terminal in the same directory as `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

The script can be run from the command line. You can provide your Rubrik Client ID, Client Secret, and environment name as command-line arguments or set them as environment variables.

### Command-line Arguments

```bash
python rubrik_get_sla_details.py --client_id YOUR_CLIENT_ID --client_secret YOUR_CLIENT_SECRET --env_name YOUR_RUBRIK_ENV_NAME
```

  * `--client_id`: Your Rubrik API Client ID. If not provided, the script will attempt to read from the `RUBRIK_CLIENT_ID` environment variable.
  * `--client_secret`: Your Rubrik API Client Secret. If not provided, the script will attempt to read from the `RUBRIK_CLIENT_SECRET` environment variable.
  * `--env_name`: The environment name for your Rubrik Security Cloud instance (e.g., `rscetf` for `rscetf.my.rubrik.com`). Do not include the domain names like `.my.rubrik.com`.

### Environment Variables

Alternatively, you can set the `RUBRIK_CLIENT_ID`, `RUBRIK_CLIENT_SECRET`, and `RUBRIK_ENV_NAME` environment variables before running the script:

**Linux/macOS:**

```bash
export RUBRIK_CLIENT_ID="YOUR_CLIENT_ID"
export RUBRIK_CLIENT_SECRET="YOUR_CLIENT_SECRET"
export RUBRIK_ENV_NAME="YOUR_RUBRIK_ENV_NAME"
python rubrik_get_sla_details.py
```

**Windows (Command Prompt):**

```bash
set RUBRIK_CLIENT_ID="YOUR_CLIENT_ID"
set RUBRIK_CLIENT_SECRET="YOUR_CLIENT_SECRET"
set RUBRIK_ENV_NAME="YOUR_RUBRIK_ENV_NAME"
python rubrik_get_sla_details.py
```

**Windows (PowerShell):**

```powershell
$env:RUBRIK_CLIENT_ID="YOUR_CLIENT_ID"
$env:RUBRIK_CLIENT_SECRET="YOUR_CLIENT_SECRET"
$env:RUBRIK_ENV_NAME="YOUR_RUBRIK_ENV_NAME"
python rubrik_get_sla_details.py
```

## Example Output

```
Connected to RSC...
Retrieving SLA domains...
    SLA domains retrieved so far: 1. end_cursor: None
Total SLA domains retrieved: 1
SLA Domain Name: Gold, ID: 12345
Hourly Schedule: Frequency: 1, Retention: 24 Hours
Daily Schedule: Frequency: 1, Retention: 7 Days
Weekly Schedule: Frequency: 1, Retention: 4 Weeks
Monthly Schedule: Frequency: 1, Retention: 6 Months
Yearly Schedule: Not configured


Session deleted successfully.
Disconnected from RSC.
Cleaning up...
```

## License

This project is open-source and available under the [MIT License](https://opensource.org/licenses/MIT).