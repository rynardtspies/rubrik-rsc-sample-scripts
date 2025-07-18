# Add Azure Subscription Operations to Rubrik RSC (Without OAuth)

This document outlines the GraphQL operations used to integrate an Azure subscription with Rubrik Security Cloud (RSC) for cloud-native protection without relying on OAuth. The process involves three distinct GraphQL calls that must be executed in sequence.

-----

## 1\. AzureSetCustomerAppCredentialsMutation

This mutation sets the Azure Active Directory (AAD) application credentials in Rubrik Security Cloud. These credentials allow RSC to authenticate with your Azure environment.

**Operation:**

```graphql
mutation AzureSetCustomerAppCredentialsMutation($input: SetAzureCloudAccountCustomerAppCredentialsInput!) {
  setAzureCloudAccountCustomerAppCredentials(input: $input)
}
```

**Variables:**

The `input` variable contains the details of the Azure AD application, including its ID, name, secret key, tenant domain name, and Azure cloud type.

```json
{
    "input": {
        "appId": "43b072c7-e6ce-43dc-bca3-00ed907d9a84",
        "appName": "rubrik-pso-rsc",
        "appSecretKey": "Z2e8Q~xxxxxxxxxxxxxxxxxx-~8fV8SzgK-hNqQdjc",
        "tenantDomainName": "mydomain.onmicrosoft.com",
        "azureCloudType": "AZUREPUBLICCLOUD",
        "shouldReplace": false
    }
}
```

**Response:**

A successful response will return `true`, indicating that the credentials have been set.

```json
{
  "data": {
    "setAzureCloudAccountCustomerAppCredentials": true
  }
}
```

-----

## 2\. AllCurrentFeaturePermissionsForCloudAccountsQuery

This query retrieves the required Azure permissions for the specific features you intend to enable (e.g., Azure SQL DB Protection). This information is crucial for creating the custom role in Azure later.

**Operation:**

```graphql
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
```

**Variables:**

The `cloudVendor` is set to "AZURE", and `permissionsGroupFilters` specify the feature type and permission groups for which you need permissions.

```json
{
    "cloudVendor": "AZURE",
    "permissionsGroupFilters": [
        {
            "featureType": "AZURE_SQL_DB_PROTECTION",
            "permissionsGroups": [
                "BACKUP_V2"
            ]
        }
    ]
}
```

**Response:**

The response contains a `permissionJson` string, which is a JSON array of required permissions for the specified feature. This string will need to be parsed to extract the permissions.

```json
{
  "data": {
    "allCurrentFeaturePermissionsForCloudAccounts": [
      {
        "featurePermissions": [
          {
            "feature": "AZURE_SQL_DB_PROTECTION",
            "permissionsGroupVersions": [
              {
                "version": 6,
                "permissionsGroup": "BACKUP_V2",
                "__typename": "PermissionsGroupWithVersion"
              }
            ],
            "permissionJson": "[{\"included_actions\":[\"Microsoft.Sql/servers/databases/delete\",\"Microsoft.Sql/servers/databases/transparentDataEncryption/read\",\"Microsoft.Sql/servers/databases/write\",\"Microsoft.Sql/servers/delete\",\"Microsoft.Sql/servers/firewallRules/read\",\"Microsoft.Sql/servers/firewallRules/write\",\"Microsoft.Sql/servers/privateEndpointConnectionsApproval/action\",\"Microsoft.Sql/servers/write\"]}]",
            "__typename": "FeaturePermission"
          }
        ],
        "__typename": "CloudAccountFeaturePermission"
      }
    ]
  }
}
```

**Action Required:** Parse the `permissionJson` from the response. You will need to create a custom Azure role with these permissions and assign it to the Azure AD application (created in step 1's context) at the subscription level.

-----

## 3\. AzureCloudAccountAddWithoutOAuthMutation

This mutation adds the Azure subscription to Rubrik Security Cloud, associating it with the previously configured application credentials and specifying the regions and protection features.

**Operation:**

```graphql
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
```

**Variables:**

The `input` specifies the tenant domain, Azure cloud type, the subscriptions to add (including their native ID and name), the features to enable (e.g., `CLOUD_NATIVE_BLOB_PROTECTION`), and the regions for protection.

Below is a list of the avaiable cloud account feaure types as found in the `CloudAccountFeature` ENUM in the GQL API. Please not that not all these types are related to Azure.

```text
ALL
All cloud account features.

APP_FLOWS
Cloud account feature is App Flows.

ARCHIVAL
Cloud account feature is Archival.

AZURE_SQL_DB_PROTECTION
Cloud account feature is Azure SQL DB Protection.

AZURE_SQL_MI_PROTECTION
Cloud account feature is Azure SQL MI Protection.

CLOUD_DISCOVERY
Cloud account feature is Cloud Discovery.

CLOUD_NATIVE_ARCHIVAL
Cloud account feature is Cloud Native Archival.

CLOUD_NATIVE_ARCHIVAL_ENCRYPTION
Cloud account feature is Cloud Native Archival Encryption.

CLOUD_NATIVE_BLOB_PROTECTION
Cloud account feature is Cloud Native Blob Protection.

CLOUD_NATIVE_DYNAMODB_PROTECTION
Cloud account feature is Cloud Native DynamoDB Protection.

CLOUD_NATIVE_PROTECTION
Cloud account feature is Cloud Native Protection.

CLOUD_NATIVE_S3_PROTECTION
Cloud account feature is Cloud Native S3 Protection.

CLOUD_SQL_PROTECTION
Cloud account feature is Cloud SQL Protection.

CLOUDACCOUNTS
Cloud account feature is Cloud Accounts.

CYBERRECOVERY_DATA_CLASSIFICATION_DATA
Cloud account feature is Cyber Recovery Data Classification Data.

CYBERRECOVERY_DATA_CLASSIFICATION_METADATA
Cloud account feature is Cyber Recovery Data Classification Metadata.

DATA_CENTER_ROLE_BASED_ARCHIVAL
Cloud account feature is Data Center Role Based Archival.

DSPM_DATA
Cloud account feature is DSPM Data.

DSPM_METADATA
Cloud account feature is DSPM Metadata.

EXOCOMPUTE
Cloud account feature is Exocompute.

FEATURE_UNSPECIFIED
Feature is not specified.

GCP_SHARED_VPC_HOST
Cloud account feature is GCP Shared VPC Host.

KUBERNETES_PROTECTION
Cloud account feature is Kubernetes Protection.

LAMINAR_CROSS_ACCOUNT
Cloud account feature is Laminar Cross Account.

LAMINAR_INTERNAL
Cloud account feature is Laminar Internal.

LAMINAR_OUTPOST_APPLICATION
Cloud account feature is Azure Laminar Outpost Application.

LAMINAR_OUTPOST_MANAGED_IDENTITY
Cloud account feature is Azure Laminar Outpost Managed Identity.

LAMINAR_TARGET_APPLICATION
Cloud account feature is Azure Laminar Target Application.

LAMINAR_TARGET_MANAGED_IDENTITY
Cloud account feature is Azure Laminar Target Managed Identity.

OUTPOST
Cloud account feature is Rubrik Outpost.

RDS_PROTECTION
Cloud account feature is RDS Protection.

ROLE_CHAINING
Cloud account feature is Role Chaining.

SERVERS_AND_APPS
Cloud account feature is Servers and Apps.
```

```json
{
    "input": {
        "tenantDomainName": "mydomain.onmicrosoft.com",
        "azureCloudType": "AZUREPUBLICCLOUD",
        "subscriptions": [
            {
                "features": [
                    {
                        "featureType": "CLOUD_NATIVE_BLOB_PROTECTION",
                        "policyVersion": 0,
                        "resourceGroup": {
                            "name": "rubrik-devel",
                            "region": "UKSOUTH"
                        },
                        "permissionsGroups": [
                            {
                                "permissionsGroup": "BASIC",
                                "version": 2
                            },
                            {
                                "permissionsGroup": "RECOVERY",
                                "version": 3
                            }
                        ]
                    }
                ],
                "subscription": {
                    "name": "My-Azure-Subscription",
                    "nativeId": "947c6838-bca7-476b-b1ca-f76e7e9d5b1b"
                }
            }
        ],
        "regions": [
            "UKSOUTH"
        ],
        "isAsynchronous": false
    }
}
```

**Response:**

A successful response will provide the `tenantId` and a `status` array for each added subscription, indicating success or any errors, along with the Rubrik and native IDs of the subscription.

```json
{
  "data": {
    "addAzureCloudAccountWithoutOauth": {
      "tenantId": "d2a22a8c-b006-4a9b-aa2e-77bba532dcbc",
      "status": [
        {
          "error": "",
          "azureSubscriptionRubrikId": "017ac9b9-148e-4c7d-853f-0bb7aad83783",
          "azureSubscriptionNativeId": "947c6838-bca7-476b-b1ca-f76e7e9d5b1b",
          "__typename": "AddAzureCloudAccountStatus"
        }
      ],
      "__typename": "AddAzureCloudAccountWithoutOauthReply"
    }
  }
}
```