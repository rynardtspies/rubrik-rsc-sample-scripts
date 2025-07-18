# Rubrik RSC Azure Subscription Integration Script (Without OAuth)

This Python script automates the integration of an Azure subscription with Rubrik Security Cloud (RSC) for cloud-native protection, specifically using the non-OAuth method. This process involves setting Azure AD application credentials, retrieving required permissions, and finally adding the Azure subscription to RSC.

## Features

* **Programmatic Azure Subscription Integration**: Automates the process of adding an Azure subscription to Rubrik Security Cloud without OAuth.
* **Azure AD Application Credential Management**: Sets the necessary Azure AD application details within RSC.
* **Dynamic Permission Retrieval**: Queries RSC for the exact permissions required for specific Azure cloud-native protection features.
* **Cloud-Native Protection Setup**: Configures the subscription for selected cloud-native protection features (e.g., Blob, SQL DB).
* **GraphQL API Interaction**: Demonstrates how to interact with the Rubrik Security Cloud GraphQL API.
* **Interactive Pause for Manual Step**: The script pauses for the user to perform the manual Azure custom role creation and assignment.

-----

## Prerequisites

Before using this script, ensure you have the following:

* **Python 3.x**: Installed on your system.
* **`requests` library**: Can be installed via `pip`.
  
  ```bash
  pip install requests
  ```

* **Rubrik Security Cloud (RSC) API Access**:
  * An active RSC account.
  * **RSC API Client Credentials**: A Client ID and Client Secret generated within your RSC environment (Settings -\> API Access/Client Credentials).
* **Azure Subscription**:
  * Access to an Azure subscription.
  * **Azure Active Directory Application**: An existing Azure AD Application (Client ID) with a Client Secret (Value) and the Tenant Domain Name. This application will be used by RSC to access your Azure resources.
  * Sufficient permissions in Azure to create custom roles and assign roles at the subscription level.

-----

## Usage

This script guides you through the Azure subscription integration in several steps, including a necessary manual intervention in the Azure portal.

### Step 1: Obtain Azure AD Application Details

Before running the script, you need to have an Azure AD Application. If you don't have one:

1. Go to the Azure Portal.
2. Navigate to **Azure Active Directory**.
3. Go to **App registrations**.
4. Register a new application:
      * Give it a name (e.g., `rubrik-rsc-integration`).
      * Select "Accounts in this organizational directory only".
      * Leave Redirect URI blank.
5. Once created, note down the **Application (client) ID** and **Directory (tenant) ID**.
6. Go to **Certificates & secrets** for your application.
7. Create a new client secret. **Copy the `Value` of the secret immediately**, as it will not be shown again.
8. The **Tenant Domain Name** is typically found in Azure Active Directory Overview (e.g., `yourcompany.onmicrosoft.com`).

-----

### Step 2: Run the Script for Initial Setup and Permission Retrieval

Execute the script with your RSC and Azure AD application details.

```bash
python add_azure_account_rsc.py \
  --env_name <YOUR_RSC_ENVIRONMENT_NAME> \
  --client_id <YOUR_RSC_CLIENT_ID> \
  --client_secret <YOUR_RSC_CLIENT_SECRET> \
  --azure_app_id <YOUR_AZURE_APP_CLIENT_ID> \
  --azure_app_name "rubrik-rsc-app" \
  --azure_app_secret_key <YOUR_AZURE_APP_SECRET_VALUE> \
  --azure_tenant_domain_name <YOUR_AZURE_TENANT_DOMAIN_NAME> \
  --azure_cloud_type AZUREPUBLICCLOUD \
  --azure_subscription_id <YOUR_AZURE_SUBSCRIPTION_ID> \
  --azure_subscription_name "My Pay-As-You-Go Subscription" \
  --azure_regions UKSOUTH EASTUS \
  --azure_feature_type CLOUD_NATIVE_BLOB_PROTECTION \
  --azure_rg_name "rubrik-resources" \
  --azure_rg_region "UKSOUTH"
```

**Parameters:**

* `--env_name`: **(Required)** Your Rubrik Security Cloud environment name (e.g., `rscetf`).
* `--client_id`: **(Optional)** Your RSC API Client ID. Defaults to `RUBRIK_CLIENT_ID` env var.
* `--client_secret`: **(Optional)** Your RSC API Client Secret. Defaults to `RUBRIK_CLIENT_SECRET` env var.
* `--azure_app_id`: **(Required)** The Application (client) ID of your Azure AD Application.
* `--azure_app_name`: **(Optional)** A name for your Azure AD Application in RSC context (default: `rubrik-rsc-app`).
* `--azure_app_secret_key`: **(Required)** The secret `Value` generated for your Azure AD Application.
* `--azure_tenant_domain_name`: **(Required)** Your Azure AD Tenant Domain Name (e.g., `yourcompany.onmicrosoft.com`).
* `--azure_cloud_type`: **(Optional)** Your Azure cloud type (default: `AZUREPUBLICCLOUD`). Other options: `AZUREGOVERNMENTCLOUD`.
* `--should_replace_app_creds`: **(Optional, Flag)** Add this flag if you want to replace existing app credentials in RSC.
* `--azure_subscription_id`: **(Required)** The ID of the Azure subscription to integrate (e.g., `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).
* `--azure_subscription_name`: **(Required)** A descriptive name for the Azure subscription in RSC.
* `--azure_regions`: **(Required)** Space-separated list of Azure regions to protect (e.g., `UKSOUTH EASTUS`).
* `--azure_feature_type`: **(Required)** The specific cloud-native protection feature to enable (e.g., `CLOUD_NATIVE_BLOB_PROTECTION`, `AZURE_SQL_DB_PROTECTION`).
* `--azure_rg_name`: **(Optional)** The name of a resource group relevant to your feature (e.g., for Blob protection, if you have a specific resource group for Rubrik objects).
* `--azure_rg_region`: **(Optional)** The region of the resource group specified by `--azure_rg_name`.

**Output from Script:**

The script will first set the Azure app credentials. Then, it will query RSC for the **exact JSON permissions** required for the specified `azure_feature_type`. This JSON output is critical for the next manual step. The script will then **pause**, prompting you to press Enter to continue.

-----

### Step 3: Manually Create and Assign Custom Role in Azure

This is a **CRUCIAL MANUAL STEP** you must perform in the Azure portal based on the script's output:

1. **Parse Permissions**: Take the `permissionJson` output from the script (e.g., `[{"included_actions":["Microsoft.Sql/..."]}]`). This is a JSON string containing the required `actions`.
2. **Create Custom Role**:
      * Go to the Azure Portal.
      * Navigate to **Subscriptions** -\> Select your subscription.
      * Go to **Access control (IAM)** -\> **Roles**.
      * Click "+ Create" -\> "Custom role".
      * Provide a **name** for your custom role (e.g., `RubrikCloudNativeRole`).
      * On the **Permissions** tab, add the `included_actions` from the `permissionJson` output. You'll typically do this by importing a JSON file or adding them manually.
      * Review and create the role.
3. **Assign Custom Role**:
      * Still under **Access control (IAM)** for your subscription, go to **Add role assignment**.
      * Select your newly created custom role (`RubrikCloudNativeRole`).
      * Assign it to your **Azure AD Application** (the one identified by `--azure_app_id` and `--azure_app_name`).
      * Ensure the scope is your subscription.

After completing these steps in Azure, return to your terminal where the Python script is paused.

-----

### Step 4: The Script will automatically proceed to Add Cloud Account

Once you've finished the manual Azure steps, press `Enter` in the terminal where the script is paused. The script will then execute the final GraphQL mutation to add your Azure subscription to Rubrik Security Cloud.

**Expected Final Output:**

The script will confirm the successful addition of the Azure subscription and provide its Rubrik internal ID.

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

The script includes basic error handling for API calls and authentication failures. If an API call fails, it will print the error message from the Rubrik API response.

-----

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
