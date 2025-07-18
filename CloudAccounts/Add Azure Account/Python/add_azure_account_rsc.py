import requests
import os
import argparse
import json
from typing import List

# A class to define the GraphQL queries and mutations with their variables
class QueriesAndMutations():
    @staticmethod
    def azure_set_customer_app_credentials_payload(app_id: str, 
                                                   app_name: str, 
                                                   app_secret_key: str, 
                                                   tenant_domain_name: str, 
                                                   azure_cloud_type: str = "AZUREPUBLICCLOUD", 
                                                   should_replace: bool = False):
        """
        GraphQL mutation to set Azure Active Directory application credentials.
        """
        mutation = """
            mutation AzureSetCustomerAppCredentialsMutation($input: SetAzureCloudAccountCustomerAppCredentialsInput!) {
              setAzureCloudAccountCustomerAppCredentials(input: $input)
            }
        """
        variables = {
            "input": {
                "appId": app_id,
                "appName": app_name,
                "appSecretKey": app_secret_key,
                "tenantDomainName": tenant_domain_name,
                "azureCloudType": azure_cloud_type,
                "shouldReplace": should_replace
            }
        }
        return dict(
            query=mutation,
            variables=variables
        )

    @staticmethod
    def all_current_feature_permissions_for_cloud_accounts_payload(permissions_group_filters: List[dict], 
                                                                   cloud_vendor: str = "AZURE",
                                                                   cloud_account_ids: List[str] = None):
        """
        GraphQL query to get required permissions for Azure role based on features.
        """
        query = """
            query AllCurrentFeaturePermissionsForCloudAccountsQuery($cloudVendor: CloudVendor!, $cloudAccountIds: [UUID!], $permissionsGroupFilters: [FeatureWithPermissionsGroups!]) {
              allCurrentFeaturePermissionsForCloudAccounts(
                cloudVendor: $cloudVendor
                cloudAccountIds: $cloudAccountIds
                permissionsGroupFilters: $permissionsGroupFilters
              ) {
                featurePermissions {
                  feature
                  permissionsGroupVersions {
                    version
                    permissionsGroup
                    __typename
                  }
                  permissionJson
                  __typename
                }
                __typename
              }
            }
        """
        variables = {
            "cloudVendor": cloud_vendor,
            "cloudAccountIds": cloud_account_ids,
            "permissionsGroupFilters": permissions_group_filters
        }
        return dict(
            query=query,
            variables=variables
        )

    @staticmethod
    def azure_cloud_account_add_without_oauth_payload(tenant_domain_name: str, 
                                                      subscriptions: List[dict], 
                                                      regions: List[str], 
                                                      azure_cloud_type: str = "AZUREPUBLICCLOUD", 
                                                      is_asynchronous: bool = False):
        """
        GraphQL mutation to add an Azure subscription without OAuth.
        """
        mutation = """
            mutation AzureCloudAccountAddWithoutOAuthMutation($input: AddAzureCloudAccountWithoutOauthInput!) {
              addAzureCloudAccountWithoutOauth(input: $input) {
                tenantId
                status {
                  error
                  azureSubscriptionRubrikId
                  azureSubscriptionNativeId
                  __typename
                }
                __typename
              }
            }
        """
        variables = {
            "input": {
                "tenantDomainName": tenant_domain_name,
                "azureCloudType": azure_cloud_type,
                "subscriptions": subscriptions,
                "regions": regions,
                "isAsynchronous": is_asynchronous
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
                print("Disconnected from RSC.")
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

    def set_azure_customer_app_credentials(self, app_id: str, 
                                           app_name: str, 
                                           app_secret_key: str, 
                                           tenant_domain_name: str, 
                                           azure_cloud_type: str = "AZUREPUBLICCLOUD", 
                                           should_replace: bool = False):
        """
        Step 1: Set Azure Active Directory application credentials in RSC.
        """
        print(f"Setting Azure customer app credentials for tenant: {tenant_domain_name}...")
        payload = QueriesAndMutations.azure_set_customer_app_credentials_payload(
            app_id=app_id,
            app_name=app_name,
            app_secret_key=app_secret_key,
            tenant_domain_name=tenant_domain_name,
            azure_cloud_type=azure_cloud_type,
            should_replace=should_replace
        )
        response = self._send_graphql_call(payload=payload)
        return response.get("data", {}).get("setAzureCloudAccountCustomerAppCredentials")

    def get_azure_required_permissions(self, feature_type: str, permissions_groups: List[str]):
        """
        Step 2: Get required permissions for Azure role for a specific feature.
        """
        print(f"Retrieving required Azure permissions for feature: {feature_type} with groups: {', '.join(permissions_groups)}...")
        permissions_group_filters = [
            {
                "featureType": feature_type,
                "permissionsGroups": permissions_groups
            }
        ]
        payload = QueriesAndMutations.all_current_feature_permissions_for_cloud_accounts_payload(
            permissions_group_filters=permissions_group_filters
        )
        response = self._send_graphql_call(payload=payload)
        feature_permissions = response.get("data", {}).get("allCurrentFeaturePermissionsForCloudAccounts", [])
        if feature_permissions:
            # Assuming we're interested in the first feature permission block
            return feature_permissions[0].get("featurePermissions", [])
        return []

    def add_azure_cloud_account_without_oauth(self, 
                                              tenant_domain_name: str, 
                                              subscription_id: str, 
                                              subscription_name: str, 
                                              azure_regions: List[str], 
                                              feature_type: str, 
                                              resource_group_name: str = None, 
                                              resource_group_region: str = None):
        """
        Step 3: Add Azure subscription to Rubrik RSC without OAuth.
        """
        print(f"Adding Azure subscription '{subscription_name}' ({subscription_id}) for tenant '{tenant_domain_name}'...")

        # Constructing the features list based on the example
        features_input = [
            {
                "featureType": feature_type,
                "policyVersion": 0, # Or appropriate version
                "permissionsGroups": [
                    {"permissionsGroup": "BASIC", "version": 2},
                    {"permissionsGroup": "RECOVERY", "version": 3}
                ]
            }
        ]

        if resource_group_name and resource_group_region:
            # If resource group details are provided, add them to the feature
            # Note: The provided GQL example had resourceGroup nested within a specific feature,
            # so this logic assumes that structure. Adjust if other features have different structures.
            for feature_config in features_input:
                if feature_config["featureType"] == feature_type: # Match the feature type for resource group
                    feature_config["resourceGroup"] = {
                        "name": resource_group_name,
                        "region": resource_group_region
                    }


        subscriptions_input = [
            {
                "features": features_input,
                "subscription": {
                    "name": subscription_name,
                    "nativeId": subscription_id
                }
            }
        ]

        payload = QueriesAndMutations.azure_cloud_account_add_without_oauth_payload(
            tenant_domain_name=tenant_domain_name,
            subscriptions=subscriptions_input,
            regions=azure_regions,
            is_asynchronous=False
        )
        response = self._send_graphql_call(payload=payload)
        return response.get("data", {}).get("addAzureCloudAccountWithoutOauth")


# MAIN SCRIPT
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add an Azure Subscription for Cloud-Native Protection in Rubrik RSC (Without OAuth).")
    parser.add_argument("--client_id", help="Client ID for Rubrik API authentication. Defaults to RUBRIK_CLIENT_ID environment variable if not provided.", default=None)
    parser.add_argument("--client_secret", help="Client Secret for Rubrik API authentication. Defaults to RUBRIK_CLIENT_SECRET environment variable if not provided.", default=None)
    parser.add_argument("--env_name", help="Environment name for the Rubrik Security Cloud instance. Example: 'mycompany' for 'mycompany.my.rubrik.com'. Do not include the domain names.", required=True)

    # Azure App Credentials
    parser.add_argument("--azure_app_id", help="Azure AD Application (client) ID.", required=True)
    parser.add_argument("--azure_app_name", help="Azure AD Application name.", default="rubrik-rsc-app")
    parser.add_argument("--azure_app_secret_key", help="Azure AD Application secret key (value).", required=True)
    parser.add_argument("--azure_tenant_domain_name", help="Azure AD Tenant Domain Name (e.g., yourcompany.onmicrosoft.com).", required=True)
    parser.add_argument("--azure_cloud_type", help="Azure Cloud Type (e.g., AZUREPUBLICCLOUD, AZUREGOVERNMENTCLOUD).", default="AZUREPUBLICCLOUD")
    parser.add_argument("--should_replace_app_creds", help="Set to true to replace existing app credentials if they already exist.", default=False, type=bool)

    # Azure Subscription Details
    parser.add_argument("--azure_subscription_id", help="The Azure Subscription ID to add.", required=True)
    parser.add_argument("--azure_subscription_name", help="A descriptive name for the Azure subscription.", required=True)
    parser.add_argument("--azure_regions", nargs='+', help="Space-separated list of Azure regions to protect (e.g., 'UKSOUTH EASTUS').", required=True)
    parser.add_argument("--azure_feature_type", help="The Azure feature type to enable (e.g., CLOUD_NATIVE_BLOB_PROTECTION, AZURE_SQL_DB_PROTECTION).", required=True)
    parser.add_argument("--azure_rg_name", help="Optional: Azure Resource Group Name for the feature (e.g., 'rubrik-rg'). Required for some features.", default=None)
    parser.add_argument("--azure_rg_region", help="Optional: Azure Resource Group Region for the feature (e.g., 'UKSOUTH'). Required for some features.", default=None)

    args = parser.parse_args()

    client = RubrikClient(client_id=args.client_id, client_secret=args.client_secret, env_name=args.env_name)

    try:
        # --- Step 1: Set Azure Customer App Credentials ---
        print("\n--- Step 1: Setting Azure Customer App Credentials ---")
        set_creds_success = client.set_azure_customer_app_credentials(
            app_id=args.azure_app_id,
            app_name=args.azure_app_name,
            app_secret_key=args.azure_app_secret_key,
            tenant_domain_name=args.azure_tenant_domain_name,
            azure_cloud_type=args.azure_cloud_type,
            should_replace=args.should_replace_app_creds
        )

        if set_creds_success:
            print("Azure customer app credentials set successfully.")
        else:
            print("Failed to set Azure customer app credentials. Check inputs or existing credentials.")
            client._delete_session()
            exit(1)

        # --- Step 2: Get Required Permissions for Azure Role ---
        # Note: The example uses AZURE_SQL_DB_PROTECTION for getting permissions,
        # but the Add Cloud Account mutation uses CLOUD_NATIVE_BLOB_PROTECTION.
        # Adjust feature_type and permissions_groups below to match what you actually need permissions for.
        print("\n--- Step 2: Getting Required Permissions for Azure Role ---")
        required_permissions = client.get_azure_required_permissions(
            feature_type=args.azure_feature_type, # Use the feature type provided in args
            permissions_groups=["BASIC", "RECOVERY"] # Example groups, adjust as needed based on feature
        )

        if required_permissions:
            print("Required Azure permissions JSON:")
            for perm in required_permissions:
                # Assuming permissionJson is a string that needs to be parsed
                if perm.get("permissionJson"):
                    try:
                        parsed_permission_json = json.loads(perm["permissionJson"])
                        print(json.dumps(parsed_permission_json, indent=2))
                    except json.JSONDecodeError:
                        print(f"  Raw permissionJson (not valid JSON): {perm['permissionJson']}")
                else:
                    print(f"  No permissionJson for feature {perm.get('feature')}")
            print("\n!!! IMPORTANT: Manually create a custom Azure role with these permissions and assign it to your Azure AD Application at the subscription level. !!!")
            print("!!! The script will pause here to allow you to perform this manual step. !!!")
            input("Press Enter to continue after creating and assigning the Azure custom role...") # Pause for user

        else:
            print("Failed to retrieve required Azure permissions. This might indicate an issue with the feature type or an API error.")
            client._delete_session()
            exit(1)

        # --- Step 3: Add Cloud Account without OAuth ---
        print("\n--- Step 3: Adding Azure Cloud Account without OAuth ---")
        add_account_response = client.add_azure_cloud_account_without_oauth(
            tenant_domain_name=args.azure_tenant_domain_name,
            subscription_id=args.azure_subscription_id,
            subscription_name=args.azure_subscription_name,
            azure_regions=args.azure_regions,
            feature_type=args.azure_feature_type, # Pass feature type for subscription features
            resource_group_name=args.azure_rg_name,
            resource_group_region=args.azure_rg_region
        )

        if add_account_response and add_account_response.get("status"):
            for status_entry in add_account_response["status"]:
                if status_entry.get("error"):
                    print(f"Failed to add subscription {status_entry.get('azureSubscriptionNativeId')}: {status_entry['error']}")
                else:
                    print(f"Successfully added Azure Subscription: {status_entry.get('azureSubscriptionName')} (ID: {status_entry.get('azureSubscriptionNativeId')})")
                    print(f"Rubrik Internal ID: {status_entry.get('azureSubscriptionRubrikId')}")
            print("Azure Cloud Account integration process initiated successfully. Check RSC UI for final status.")
        else:
            print("Failed to add Azure Cloud Account. No status returned or unexpected response structure.")
            client._delete_session()
            exit(1)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        client._delete_session()
        print("\nScript execution finished.")