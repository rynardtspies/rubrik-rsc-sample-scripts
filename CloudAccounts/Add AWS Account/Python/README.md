# Rubrik RSC AWS Cloud Account Integration Script

This Python script facilitates the integration of an AWS cloud account with Rubrik Security Cloud (RSC) for cloud-native protection using the RSC GraphQL API. The process involves three main steps: initiating the account creation, finalizing protection by specifying regions, and registering the necessary AWS Cross-Account Role ARN.

## Features

* **Programmatic AWS Account Integration**: Automates the initial steps of adding an AWS account to Rubrik Security Cloud.
* **Cloud-Native Protection Setup**: Configures the account for cloud-native protection features.
* **GraphQL API Interaction**: Demonstrates how to interact with the Rubrik Security Cloud GraphQL API for complex workflows.
* **Multi-Region Support**: Allows specifying multiple AWS regions for protection.
* **Phased Execution**: Supports a two-phase execution to accommodate the manual AWS CloudFormation deployment step.

-----

## Prerequisites

Before using this script, ensure you have the following:

* **Python 3.x**: Installed on your system.
* **`requests` library**: Can be installed via `pip`.
* **Rubrik Security Cloud (RSC) API Access**:
  * An active RSC account.
  * **RSC API Client Credentials**: A Client ID and Client Secret generated within your RSC environment (Settings -\> API Access/Client Credentials).
* **AWS Account**:
  * The AWS Account ID you wish to integrate.
  * Sufficient permissions in your AWS account to deploy CloudFormation stacks and create IAM roles.

-----

## Installation

1. **Install dependencies:**

    ```bash
    pip install requests
    ```

-----

## Usage

The script is designed to be run in two logical phases, accommodating the necessary manual step of deploying a CloudFormation template in AWS.

### Phase 1: Initiate Account Creation and Get CloudFormation Details

This initial run will send the first GraphQL mutation to RSC, which validates the AWS account and provides the URL for the AWS CloudFormation template. You will need this template to set up permissions in your AWS environment.

```bash
python add_aws_account_rsc.py \
  --env_name <YOUR_RSC_ENVIRONMENT_NAME> \
  --aws_account_id <YOUR_AWS_ACCOUNT_ID> \
  --aws_account_name "My AWS Account for RSC" \
  --aws_regions US_EAST_1 EU_WEST_2 \
  --client_id <YOUR_RSC_CLIENT_ID> \
  --client_secret <YOUR_RSC_CLIENT_SECRET>
```

**Parameters:**

* `--env_name`: **(Required)** Your Rubrik Security Cloud environment name (e.g., `mycompany` if your URL is `mycompany.my.rubrik.com`).
* `--aws_account_id`: **(Required)** The 12-digit AWS Account ID you want to integrate (e.g., `123456789012`).
* `--aws_account_name`: **(Required)** A friendly name for this AWS account within Rubrik Security Cloud.
* `--aws_regions`: **(Required)** A space-separated list of AWS regions where you want to enable cloud-native protection (e.g., `US_EAST_1 EU_WEST_2`).
* `--client_id`: **(Optional)** Your RSC API Client ID. If not provided, the script attempts to read from the `RUBRIK_CLIENT_ID` environment variable.
* `--client_secret`: **(Optional)** Your RSC API Client Secret. If not provided, the script attempts to read from the `RUBRIK_CLIENT_SECRET` environment variable.

**Expected Output (Phase 1):**

The script will print details about the CloudFormation template, including:

* `CloudFormation Console URL`
* `CloudFormation Template URL`
* `Suggested Stack Name`

**Action Required After Phase 1:**

You must manually perform the following steps in your AWS environment:

1. **Download the CloudFormation Template**: Use the `CloudFormation Template URL` provided by the script to download the JSON template file.
2. **Deploy the Template in AWS**:
      * Log in to your AWS Management Console.
      * Navigate to the **CloudFormation** service.
      * Click "Create stack" and upload the downloaded template file.
      * Follow the on-screen instructions. Use the `Suggested Stack Name` from the script's output.
      * Ensure you deploy the stack in a region where you intend to protect resources.
      * Once the CloudFormation stack's status is `CREATE_COMPLETE`, go to its **Outputs** tab.
      * **Copy the value of the `CrossAccountRoleARN`.** This ARN is critical for the next phase.

-----

### Phase 2: Deploy CloudFormation in AWS and Get Role ARN

(This is the manual step described above, performed in your AWS console.)

-----

### Phase 3: Register the Cross-Account Role ARN with RSC

After successfully deploying the CloudFormation stack in AWS and obtaining the `CrossAccountRoleARN`, run the script again. This time, include the `--cross_account_role_arn` argument.

```bash
python add_aws_account_rsc.py \
  --env_name <YOUR_RSC_ENVIRONMENT_NAME> \
  --aws_account_id <YOUR_AWS_ACCOUNT_ID> \
  --aws_account_name "My AWS Account for RSC" \
  --aws_regions US_EAST_1 EU_WEST_2 \
  --cross_account_role_arn "arn:aws:iam::123456789012:role/RSC-CloudNativeProtectionSetup-CrossAccountRole-xxxxxxxxxxxxxxxx" \
  --client_id <YOUR_RSC_CLIENT_ID> \
  --client_secret <YOUR_RSC_CLIENT_SECRET>
```

**New Parameter for Phase 3:**

  `--cross_account_role_arn`: **(Required for Phase 3)** The full ARN of the IAM role created by the CloudFormation stack in your AWS account.

**Expected Output (Phase 3):**

The script will confirm the successful registration of the ARN and indicate that the AWS Cloud Account integration is complete.

-----

## Authentication

The script authenticates with Rubrik Security Cloud using OAuth 2.0 Client Credentials Flow. You can provide your `client_id` and `client_secret` via:

1. **Environment Variables (Recommended)**:
      * `export RUBRIK_CLIENT_ID="your_client_id"`
      * `export RUBRIK_CLIENT_SECRET="your_client_secret"`
2. **Command-line Arguments**:
      * `--client_id your_client_id --client_secret your_client_secret`

Command-line arguments will take precedence over environment variables if both are provided.

-----

## Error Handling

The script includes basic error handling for API calls and authentication failures. If an API call fails, it will print the error message from the Rubrik API response.

-----

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
