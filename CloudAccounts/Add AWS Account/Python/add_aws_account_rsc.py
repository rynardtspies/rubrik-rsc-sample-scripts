import requests
import os
import argparse
import json
from typing import List

# A class to define the GraphQL queries and mutations with their variables
class QueriesAndMutations():
    @staticmethod
    def aws_cloud_account_validate_and_initiate_mutation_payload(aws_native_id: str, account_name: str):
        """
        GraphQL mutation to validate and initiate the creation of an AWS cloud account.
        This provides the CloudFormation template URL.
        """
        mutation = """
            mutation AwsCloudAccountValidateAndInitiateMutation($input: ValidateAndCreateAwsCloudAccountInput!) {
              validateAndCreateAwsCloudAccount(input: $input) {
                validateResponse {
                  invalidAwsAccounts {
                    nativeId
                    message
                    __typename
                  }
                  __typename
                }
                initiateResponse {
                  cloudFormationUrl
                  templateUrl
                  stackName
                  externalId
                  awsIamPairId
                  featureVersions {
                    feature
                    version
                    permissionsGroupVersions {
                      permissionsGroup
                      version
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                __typename
              }
            }
        """
        variables = {
            "input": {
                "action": "CREATE",
                "features": ["CLOUD_NATIVE_PROTECTION"],
                "awsChildAccounts": [
                    {
                        "nativeId": aws_native_id,
                        "accountName": account_name,
                        "cloudType": "STANDARD"
                    }
                ],
                "featuresWithPermissionsGroups": [
                    {
                        "featureType": "CLOUD_NATIVE_PROTECTION",
                        "permissionsGroups": ["BASIC"]
                    }
                ]
            }
        }
        return dict(
            query=mutation,
            variables=variables
        )

    @staticmethod
    def aws_cloud_account_process_mutation_payload(aws_native_id: str, account_name: str, aws_regions: List[str]):
        """
        GraphQL mutation to finalize the AWS cloud account protection,
        including specifying regions.
        """
        mutation = """
            mutation AwsCloudAccountProcessMutation($input: FinalizeAwsCloudAccountProtectionInput!) {
              finalizeAwsCloudAccountProtection(input: $input) {
                awsChildAccounts {
                  id
                  nativeId
                  __typename
                }
                __typename
              }
            }
        """
        variables = {
            "input": {
                "action": "CREATE",
                "awsChildAccounts": [
                    {
                        "nativeId": aws_native_id,
                        "accountName": account_name,
                        "cloudType": "STANDARD"
                    }
                ],
                "features": ["CLOUD_NATIVE_PROTECTION"],
                "awsRegions": aws_regions,
                "featuresWithPermissionsGroups": [
                    {
                        "featureType": "CLOUD_NATIVE_PROTECTION",
                        "permissionsGroups": ["BASIC"]
                    }
                ]
            }
        }
        return dict(
            query=mutation,
            variables=variables
        )

    @staticmethod
    def register_aws_feature_artifacts_mutation_payload(aws_native_id: str, cross_account_role_arn: str):
        """
        GraphQL mutation to register AWS feature artifacts, like the Cross-Account Role ARN.
        """
        mutation = """
            mutation RegisterAwsFeatureArtifactsMutation($input: RegisterAwsFeatureArtifactsInput!) {
              registerAwsFeatureArtifacts(input: $input) {
                allAwsNativeIdtoRscIdMappings {
                  awsCloudAccountId
                  awsNativeId
                  message
                  __typename
                }
                __typename
              }
            }
        """
        variables = {
            "input": {
                "awsArtifacts": [
                    {
                        "awsNativeId": aws_native_id,
                        "features": ["CLOUD_NATIVE_PROTECTION"],
                        "externalArtifacts": [
                            {
                                "externalArtifactKey": "CROSSACCOUNT_ROLE_ARN",
                                "externalArtifactValue": cross_account_role_arn
                            }
                        ]
                    }
                ],
                "cloudType": "STANDARD"
            }
        }
        return dict(
            query=mutation,
            variables=variables
        )

# A class to connect and send requests to the Rubrik API (RSC)
class RubrikClient:
    def __init__(self, client_id=None, client_secret=None, env_name=None):
        self.base_url = f"https://{env_name}.my.rubrik.com"
        self.token = None
        self.client_id = client_id if client_id else os.getenv('RUBRIK_CLIENT_ID')
        self.client_secret = client_secret if client_secret else os.getenv('RUBRIK_CLIENT_SECRET')
        self.headers = {'Content-Type': 'application/json'}
        self._authenticate()


    def _authenticate(self):
        """Authenticate with the Rubrik API using client credentials."""
        url = f"{self.base_url}/api/client_token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            self.token = response.json().get('access_token')
            self.headers['Authorization'] = f"Bearer {self.token}"
            print("Connected to RSC...")
        else:
            raise Exception(f"Authentication failed: {response.text}")


    def _delete_session(self):
        """Delete the current session."""
        if self.token:
            url = f"{self.base_url}/api/session"
            response = requests.delete(url, headers=self.headers)
            if response.status_code in [200, 204]:
                print("Session deleted successfully.")
                self.token = None
                print(f"Disconnected from RSC.")
            else:
                raise Exception(f"Failed to delete session: {response.text}")
        else:
            print("No active session to delete.")


    def _send_graphql_call(self, payload):
        """Send a GraphQL call to the Rubrik API and return the JSON response."""
        url = f"{self.base_url}/api/graphql"
        response = requests.post(url, json=payload, headers=self.headers)
        if response.ok:
            return response.json()
        else:
            raise Exception(f"GraphQL query failed: {response.text}")

    def validate_and_initiate_aws_account(self, aws_native_id: str, account_name: str):
        """
        Step 1: Validate and initiate the AWS cloud account creation.
        Returns the CloudFormation template URL and other initiate response details.
        """
        print(f"Initiating validation and creation for AWS Account: {aws_native_id}...")
        payload = QueriesAndMutations.aws_cloud_account_validate_and_initiate_mutation_payload(aws_native_id, account_name)
        response = self._send_graphql_call(payload=payload)
        return response.get("data", {}).get("validateAndCreateAwsCloudAccount", {}).get("initiateResponse")

    def finalize_aws_account_protection(self, aws_native_id: str, account_name: str, aws_regions: List[str]):
        """
        Step 2: Finalize the AWS cloud account protection by specifying regions.
        """
        print(f"Finalizing protection for AWS Account: {aws_native_id} in regions: {', '.join(aws_regions)}...")
        payload = QueriesAndMutations.aws_cloud_account_process_mutation_payload(aws_native_id, account_name, aws_regions)
        response = self._send_graphql_call(payload=payload)
        return response.get("data", {}).get("finalizeAwsCloudAccountProtection")

    def register_aws_feature_artifacts(self, aws_native_id: str, cross_account_role_arn: str):
        """
        Step 3: Register the AWS feature artifacts, specifically the Cross-Account Role ARN.
        """
        print(f"Registering Cross-Account Role ARN for AWS Account: {aws_native_id}...")
        payload = QueriesAndMutations.register_aws_feature_artifacts_mutation_payload(aws_native_id, cross_account_role_arn)
        response = self._send_graphql_call(payload=payload)
        return response.get("data", {}).get("registerAwsFeatureArtifacts")


# MAIN SCRIPT
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add an AWS Cloud Account for Cloud-Native Protection in Rubrik RSC.")
    parser.add_argument("--client_id", help="Client ID for Rubrik API authentication. Defaults to RUBRIK_CLIENT_ID environment variable if not provided.", default=None)
    parser.add_argument("--client_secret", help="Client Secret for Rubrik API authentication. Defaults to RUBRIK_CLIENT_SECRET environment variable if not provided.", default=None)
    parser.add_argument("--env_name", help="Environment name for the Rubrik Security Cloud instance. Example: 'mycompany' for 'mycompany.my.rubrik.com'. Do not include the domain names.", required=True)
    parser.add_argument("--aws_account_id", help="The AWS Native ID (Account ID) to add.", required=True)
    parser.add_argument("--aws_account_name", help="A descriptive name for the AWS account.", required=True)
    parser.add_argument("--aws_regions", nargs='+', help="Space-separated list of AWS regions to protect (e.g., 'EU_WEST_2 US_EAST_1').", required=True)
    parser.add_argument("--cross_account_role_arn", help="The AWS Cross-Account Role ARN obtained after deploying the CloudFormation template. This is required to complete the process.", default=None)


    args = parser.parse_args()

    # Initialize Rubrik Client
    client = RubrikClient(client_id=args.client_id, client_secret=args.client_secret, env_name=args.env_name)

    try:
        # --- Step 1: Validate and Initiate AWS Cloud Account ---
        print("\n--- Step 1: Validating and Initiating AWS Cloud Account Creation ---")
        initiate_response = client.validate_and_initiate_aws_account(
            aws_native_id=args.aws_account_id,
            account_name=args.aws_account_name
        )

        if initiate_response:
            cloud_formation_url = initiate_response.get("cloudFormationUrl")
            template_url = initiate_response.get("templateUrl")
            stack_name = initiate_response.get("stackName")
            print(f"Validation initiated successfully for AWS Account ID: {args.aws_account_id}")
            print(f"CloudFormation Console URL: {cloud_formation_url}")
            print(f"CloudFormation Template URL: {template_url}")
            print(f"Suggested Stack Name: {stack_name}")
            print("\n!!! IMPORTANT: Please download the template from the 'CloudFormation Template URL' above.")
            print("!!! Deploy this template in your AWS account via CloudFormation.")
            print("!!! Once deployed, copy the 'CrossAccountRoleARN' from the CloudFormation stack outputs.")
            print("!!! You will need this ARN to run the script again with the --cross_account_role_arn argument to complete the setup.")

            if not args.cross_account_role_arn:
                print("\nCross-Account Role ARN not provided. The script will pause here. Please obtain the ARN from AWS CloudFormation outputs and re-run with --cross_account_role_arn.")
                client._delete_session()
                exit(0)
            else:
                print("\nCross-Account Role ARN provided. Proceeding with the next steps...")
        else:
            print("Failed to initiate AWS cloud account validation. Check inputs.")
            client._delete_session()
            exit(1)

        # --- Step 2: Finalize AWS Cloud Account Protection (Specify Regions) ---
        print("\n--- Step 2: Finalizing AWS Cloud Account Protection (Specifying Regions) ---")
        finalize_response = client.finalize_aws_account_protection(
            aws_native_id=args.aws_account_id,
            account_name=args.aws_account_name,
            aws_regions=args.aws_regions
        )

        if finalize_response:
            print(f"Protection finalization initiated for regions: {', '.join(args.aws_regions)}")
        else:
            print("Failed to finalize AWS cloud account protection. Check regions or account details.")
            client._delete_session()
            exit(1)

        # --- Step 3: Register AWS Account Feature Artifacts (Cross-Account Role ARN) ---
        # This step is only executed if the Cross-Account Role ARN is provided
        print("\n--- Step 3: Registering AWS Account Feature Artifacts (Cross-Account Role ARN) ---")
        register_response = client.register_aws_feature_artifacts(
            aws_native_id=args.aws_account_id,
            cross_account_role_arn=args.cross_account_role_arn
        )

        if register_response:
            print("AWS Cross-Account Role ARN registered successfully.")
            print("AWS Cloud Account integration complete. RSC will now discover resources.")
        else:
            print("Failed to register AWS Cross-Account Role ARN. Check ARN or account status.")
            client._delete_session()
            exit(1)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # Clean up the session
        client._delete_session()
        print("\nScript execution finished.")