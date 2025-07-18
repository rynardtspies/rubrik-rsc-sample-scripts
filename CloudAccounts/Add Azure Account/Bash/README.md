# Rubrik RSC Azure Subscription Integration Script (Bash - Without OAuth)

This Bash script provides a command-line utility to integrate an Azure subscription with Rubrik Security Cloud (RSC) for cloud-native protection, specifically using the non-OAuth method. It orchestrates the necessary GraphQL API calls using `curl` and `jq`.

## Features

* **Bash-based Automation**: Fully executable from the command line using standard tools (`curl`, `jq`).
* **Azure AD Application Credential Management**: Sets Azure AD application details in RSC.
* **Dynamic Permission Retrieval**: Fetches the required Azure permissions for specific cloud-native protection features.
* **Cloud-Native Protection Setup**: Configures the subscription for selected features.
* **Interactive Pause**: Pauses for manual Azure role creation and assignment.

-----

## Prerequisites

Before using this script, ensure you have the following:

* **Bash**: A Unix-like environment (Linux, macOS, WSL on Windows).
* **`curl`**: For making HTTP requests (usually pre-installed).
* **`jq`**: A lightweight and flexible command-line JSON processor.
  * **Installation:**
    * **macOS (Homebrew):** `brew install jq`
    * **Debian/Ubuntu:** `sudo apt-get install jq`
    * **CentOS/RHEL:** `sudo yum install jq`
    * **Windows (WSL):** Install `jq` within your WSL distribution.
* **Rubrik Security Cloud (RSC) API Access**:
  * An active RSC account.
  * **RSC API Client Credentials**: A Client ID and Client Secret generated within your RSC environment (Settings -\> API Access/Client Credentials).
* **Azure Subscription**:
  * Access to an Azure subscription.
  * **Azure Active Directory Application**: An existing Azure AD Application (Client ID) with a Client Secret (Value) and the Tenant Domain Name. This application will be used by RSC to access your Azure resources.
  * Sufficient permissions in Azure to create custom roles and assign roles at the subscription level.

-----

## Installation

1. **Save the script:** Save the provided Bash script content into a file (e.g., `add_azure_account_rsc.sh`).
2. **Make it executable:**

```bash
chmod +x add_azure_account_rsc.sh
```

-----

## Usage

This script guides you through the Azure subscription integration in several steps, including a necessary manual intervention in the Azure portal.

### Step 1: Obtain Azure AD Application Details

Before running the script, ensure you have your Azure AD Application details:

1. Go to the [Azure Portal](https://portal.azure.com/).
2. Navigate to **Azure Active Directory** -\> **App registrations**.
3. Either use an existing application or register a new one.
4. For your application, note down:
     * **Application (client) ID**
     * **Directory (tenant) ID** (This is your Tenant Domain Name, e.g., `yourcompany.onmicrosoft.com` or the Tenant ID itself).
5. Under the app, go to **Certificates & secrets** and create a new client secret. **Copy the `Value` of the secret immediately** as it will not be shown again.

### Step 2: Run the Bash Script

Execute the script with your RSC and Azure AD application details.

```bash
./add_azure_account_rsc.sh \
  --env_name "your_rsc_env_name" \
  --client_id "your_rsc_client_id" \
  --client_secret "your_rsc_client_secret" \
  --azure_app_id "your_azure_app_client_id" \
  --azure_app_name "rubrik-rsc-app" \
  --azure_app_secret_key "your_azure_app_secret_value" \
  --azure_tenant_domain_name "yourcompany.onmicrosoft.com" \
  --azure_cloud_type "AZUREPUBLICCLOUD" \
  --azure_subscription_id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --azure_subscription_name "My Pay-As-You-Go Subscription" \
  --azure_regions "UKSOUTH EASTUS" \
  --azure_feature_type "CLOUD_NATIVE_BLOB_PROTECTION" \
  --azure_rg_name "rubrik-resources" \
  --azure_rg_region "UKSOUTH"
```

**Parameters:**

* `--env_name`: **(Required)** Your Rubrik Security Cloud environment name (e.g., `rscetf`).
* `--client_id`: **(Optional)** Your RSC API Client ID. Defaults to `RUBRIK_CLIENT_ID` environment variable.
* `--client_secret`: **(Optional)** Your RSC API Client Secret. Defaults to `RUBRIK_CLIENT_SECRET` environment variable.
* `--azure_app_id`: **(Required)** The Application (client) ID of your Azure AD Application.
* `--azure_app_name`: **(Optional)** A name for your Azure AD Application in RSC context (default: `rubrik-rsc-app`).
* `--azure_app_secret_key`: **(Required)** The secret `Value` generated for your Azure AD Application.
* `--azure_tenant_domain_name`: **(Required)** Your Azure AD Tenant Domain Name (e.g., `yourcompany.onmicrosoft.com`).
* `--azure_cloud_type`: **(Optional)** Your Azure cloud type (default: `AZUREPUBLICCLOUD`). Other options: `AZUREGOVERNMENTCLOUD`.
* `--should_replace_app_creds`: **(Optional, Flag)** Add this flag to replace existing app credentials in RSC.
* `--azure_subscription_id`: **(Required)** The ID of the Azure subscription to integrate.
* `--azure_subscription_name`: **(Required)** A descriptive name for the Azure subscription in RSC.
* `--azure_regions`: **(Required)** Space-separated list of Azure regions to protect (e.g., `"UKSOUTH EASTUS"`). **Enclose multiple regions in quotes.**
* `--azure_feature_type`: **(Required)** The specific cloud-native protection feature to enable (e.g., `CLOUD_NATIVE_BLOB_PROTECTION`, `AZURE_SQL_DB_PROTECTION`).
* `--azure_rg_name`: **(Optional)** The name of a resource group relevant to your feature (e.g., for Blob protection, if you have a specific resource group for Rubrik objects).
* `--azure_rg_region`: **(Optional)** The region of the resource group specified by `--azure_rg_name`.

**Script Execution Flow:**

1. **Authentication**: The script will first authenticate with your RSC environment.
2. **Set App Credentials**: It will then send the `AzureSetCustomerAppCredentialsMutation` to configure your Azure AD application details in RSC.
3. **Get Required Permissions**: The script will query RSC for the **exact JSON permissions** required for the specified `azure_feature_type`. This output is crucial for the next manual step.
4. **Pause for Manual Step**: The script will then **pause**, prompting you to press `Enter` to continue after performing the manual Azure role setup.

### Step 3: Manually Create and Assign Custom Role in Azure

This is a **CRUCIAL MANUAL STEP** you must perform in the Azure portal based on the script's output. **Do not close the terminal running the script.**

1. **Parse Permissions**: From the `Required Azure permissions JSON:` output by the script, identify the `included_actions` array.
2. **Create Custom Role**:
      * Go to the [Azure Portal](https://portal.azure.com/).
      * Navigate to **Subscriptions** -\> Select the Azure subscription you are integrating.
      * Go to **Access control (IAM)** -\> **Roles**.
      * Click "+ Create" -\> "Custom role".
      * Provide a **name** for your custom role (e.g., `RubrikCloudNativeRole`).
      * On the **Permissions** tab, add the `included_actions` from the script's JSON output. This can often be done by importing a JSON file or adding permissions manually.
      * Review and create the role.
3. **Assign Custom Role**:
      * Still under **Access control (IAM)** for your subscription, go to **Add role assignment**.
      * Select your newly created custom role (e.g., `RubrikCloudNativeRole`).
      * Assign it to your **Azure AD Application** (the one identified by `--azure_app_id` and `--azure_app_name`).
      * Ensure the scope is your subscription.

After completing these steps in Azure, return to your terminal where the Bash script is paused and press `Enter`.

### Automatic Continuation: Add Cloud Account

Once you press `Enter`, the script will automatically proceed to execute the final GraphQL mutation (`AzureCloudAccountAddWithoutOAuthMutation`) to add your Azure subscription to Rubrik Security Cloud.

**Expected Final Output:**

The script will confirm the successful addition of the Azure subscription and provide its details, including the Rubrik internal ID.

-----

## Authentication

The script authenticates with Rubrik Security Cloud using OAuth 2.0 Client Credentials Flow. You can provide your `client_id` and `client_secret` via:

1. **Environment Variables (Recommended)**:

```bash
export RUBRIK_CLIENT_ID="your_client_id"
export RUBRIK_CLIENT_SECRET="your_client_secret"
```

1. **Command-line Arguments**

    `--client_id your_client_id --client_secret your_client_secret`

Command-line arguments will take precedence over environment variables if both are provided.

-----

## Error Handling

The script includes basic error handling for `curl` and `jq` commands, as well as checking for `errors` in GraphQL responses. If an API call fails or an error is detected, the script will exit with an error message.

-----

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
