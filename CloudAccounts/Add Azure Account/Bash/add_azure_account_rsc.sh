#!/bin/bash

# Script to add an Azure Subscription to Rubrik Security Cloud (RSC) without OAuth
# This script uses curl to make GraphQL API calls.

# --- Configuration ---
# Set these environment variables or pass them as arguments
# export RUBRIK_CLIENT_ID="your_rsc_client_id"
# export RUBRIK_CLIENT_SECRET="your_rsc_client_secret"

# --- Argument Parsing ---
display_usage() {
    echo "Usage: $0 --env_name <RSC_ENV> --azure_app_id <AZURE_APP_ID> --azure_app_secret_key <AZURE_APP_SECRET> --azure_tenant_domain_name <AZURE_TENANT_DOMAIN> --azure_subscription_id <AZURE_SUB_ID> --azure_subscription_name <AZURE_SUB_NAME> --azure_regions \"REGION1 REGION2\" --azure_feature_type <FEATURE_TYPE> [--azure_app_name <APP_NAME>] [--azure_cloud_type <CLOUD_TYPE>] [--should_replace_app_creds] [--azure_rg_name <RG_NAME>] [--azure_rg_region <RG_REGION>] [--client_id <RSC_CLIENT_ID>] [--client_secret <RSC_CLIENT_SECRET>]"
    echo ""
    echo "Required:"
    echo "  --env_name               : Your Rubrik Security Cloud environment name (e.g., 'rscetf')."
    echo "  --azure_app_id           : Azure AD Application (client) ID."
    echo "  --azure_app_secret_key   : Azure AD Application secret key (value)."
    echo "  --azure_tenant_domain_name: Azure AD Tenant Domain Name (e.g., 'yourcompany.onmicrosoft.com')."
    echo "  --azure_subscription_id  : The Azure Subscription ID to add."
    echo "  --azure_subscription_name: A descriptive name for the Azure subscription."
    echo "  --azure_regions          : Space-separated list of Azure regions to protect (e.g., \"UKSOUTH EASTUS\"). Enclose in quotes."
    echo "  --azure_feature_type     : The Azure feature type to enable (e.g., 'CLOUD_NATIVE_BLOB_PROTECTION', 'AZURE_SQL_DB_PROTECTION')."
    echo ""
    echo "Optional:"
    echo "  --azure_app_name         : Azure AD Application name (default: 'rubrik-rsc-app')."
    echo "  --azure_cloud_type       : Azure Cloud Type (default: 'AZUREPUBLICCLOUD'). Other: 'AZUREGOVERNMENTCLOUD'."
    echo "  --should_replace_app_creds: Flag to replace existing app credentials in RSC."
    echo "  --azure_rg_name          : Optional: Azure Resource Group Name for the feature (e.g., 'rubrik-rg'). Required for some features."
    echo "  --azure_rg_region        : Optional: Azure Resource Group Region for the feature (e.g., 'UKSOUTH'). Required for some features."
    echo "  --client_id              : RSC API Client ID (overrides RUBRIK_CLIENT_ID env var)."
    echo "  --client_secret          : RSC API Client Secret (overrides RUBRIK_CLIENT_SECRET env var)."
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --env_name) ENV_NAME="$2"; shift ;;
        --client_id) CLIENT_ID="$2"; shift ;;
        --client_secret) CLIENT_SECRET="$2"; shift ;;
        --azure_app_id) AZURE_APP_ID="$2"; shift ;;
        --azure_app_name) AZURE_APP_NAME="$2"; shift ;;
        --azure_app_secret_key) AZURE_APP_SECRET_KEY="$2"; shift ;;
        --azure_tenant_domain_name) AZURE_TENANT_DOMAIN_NAME="$2"; shift ;;
        --azure_cloud_type) AZURE_CLOUD_TYPE="$2"; shift ;;
        --should_replace_app_creds) SHOULD_REPLACE_APP_CREDS="true" ;;
        --azure_subscription_id) AZURE_SUBSCRIPTION_ID="$2"; shift ;;
        --azure_subscription_name) AZURE_SUBSCRIPTION_NAME="$2"; shift ;;
        --azure_regions) AZURE_REGIONS=($2); shift ;; # Store regions as an array
        --azure_feature_type) AZURE_FEATURE_TYPE="$2"; shift ;;
        --azure_rg_name) AZURE_RG_NAME="$2"; shift ;;
        --azure_rg_region) AZURE_RG_REGION="$2"; shift ;;
        -h|--help) display_usage ;;
        *) echo "Unknown parameter passed: $1"; display_usage ;;
    esac
    shift
done

# Validate required arguments
if [ -z "$ENV_NAME" ] || [ -z "$AZURE_APP_ID" ] || [ -z "$AZURE_APP_SECRET_KEY" ] || \
   [ -z "$AZURE_TENANT_DOMAIN_NAME" ] || [ -z "$AZURE_SUBSCRIPTION_ID" ] || \
   [ -z "$AZURE_SUBSCRIPTION_NAME" ] || [ -z "${AZURE_REGIONS[@]}" ] || [ -z "$AZURE_FEATURE_TYPE" ]; then
    echo "Error: Missing required arguments."
    display_usage
fi

# Set defaults if not provided
AZURE_APP_NAME=${AZURE_APP_NAME:-"rubrik-rsc-app"}
AZURE_CLOUD_TYPE=${AZURE_CLOUD_TYPE:-"AZUREPUBLICCLOUD"}
SHOULD_REPLACE_APP_CREDS=${SHOULD_REPLACE_APP_CREDS:-"false"}
CLIENT_ID=${CLIENT_ID:-$RUBRIK_CLIENT_ID}
CLIENT_SECRET=${CLIENT_SECRET:-$RUBRIK_CLIENT_SECRET}

# --- Functions ---

# Function to authenticate and get JWT token
authenticate() {
    echo "Authenticating with RSC..."
    AUTH_URL="https://${ENV_NAME}.my.rubrik.com/api/client_token"
    AUTH_PAYLOAD=$(jq -n \
        --arg client_id "$CLIENT_ID" \
        --arg client_secret "$CLIENT_SECRET" \
        '{client_id: $client_id, client_secret: $client_secret}')
    
    AUTH_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
                           -d "$AUTH_PAYLOAD" "$AUTH_URL")
    
    ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')

    if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
        echo "Authentication failed. Response: $AUTH_RESPONSE"
        exit 1
    fi
    echo "Connected to RSC."
}

# Function to send GraphQL calls
send_graphql_call() {
    local PAYLOAD=$1
    local URL="https://${ENV_NAME}.my.rubrik.com/api/graphql"
    local HEADERS="Content-Type: application/json"
    local AUTH_HEADER="Authorization: Bearer $ACCESS_TOKEN"

    RESPONSE=$(curl -s -X POST -H "$HEADERS" -H "$AUTH_HEADER" -d "$PAYLOAD" "$URL")

    if echo "$RESPONSE" | jq -e 'has("errors")' > /dev/null; then
        echo "GraphQL query failed: $(echo "$RESPONSE" | jq -r '.errors[0].message')"
        exit 1
    fi
    echo "$RESPONSE"
}

# Function to delete session
delete_session() {
    echo "Deleting session..."
    SESSION_URL="https://${ENV_NAME}.my.rubrik.com/api/session"
    curl -s -X DELETE -H "Authorization: Bearer $ACCESS_TOKEN" "$SESSION_URL" > /dev/null
    echo "Session deleted successfully."
}

# --- Main Script Logic ---

authenticate

# --- Step 1: Set Azure Customer App Credentials ---
echo -e "\n--- Step 1: Setting Azure Customer App Credentials ---"
STEP1_MUTATION='
mutation AzureSetCustomerAppCredentialsMutation($input: SetAzureCloudAccountCustomerAppCredentialsInput!) {
  setAzureCloudAccountCustomerAppCredentials(input: $input)
}
'
STEP1_VARIABLES=$(jq -n \
--arg appId "$AZURE_APP_ID" \
--arg appName "$AZURE_APP_NAME" \
--arg appSecretKey "$AZURE_APP_SECRET_KEY" \
--arg tenantDomainName "$AZURE_TENANT_DOMAIN_NAME" \
--arg azureCloudType "$AZURE_CLOUD_TYPE" \
--argjson shouldReplace "$SHOULD_REPLACE_APP_CREDS" \
'{
    input: {
        appId: $appId,
        appName: $appName,
        appSecretKey: $appSecretKey,
        tenantDomainName: $tenantDomainName,
        azureCloudType: $azureCloudType,
        shouldReplace: $shouldReplace
    }
}')

# Construct the full GraphQL payload
STEP1_PAYLOAD=$(jq -n \
--arg query "$STEP1_MUTATION" \
--argjson variables "$STEP1_VARIABLES" \
'{query: $query, variables: $variables}')

echo "Setting Azure customer app credentials for tenant: $AZURE_TENANT_DOMAIN_NAME..."
STEP1_RESPONSE=$(send_graphql_call "$STEP1_PAYLOAD")
SET_CREDS_SUCCESS=$(echo "$STEP1_RESPONSE" | jq -r '.data.setAzureCloudAccountCustomerAppCredentials')

if [ "$SET_CREDS_SUCCESS" == "true" ]; then
    echo "Azure customer app credentials set successfully."
else
    echo "Failed to set Azure customer app credentials. Response: $STEP1_RESPONSE"
    delete_session
    exit 1
fi

# --- Step 2: Get Required Permissions for Azure Role ---
echo -e "\n--- Step 2: Getting Required Permissions for Azure Role ---"
STEP2_QUERY='
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
'

# Construct permissions_group_filters dynamically as a JSON array string for jq
PERMS_GROUPS_ARRAY='["BASIC", "RECOVERY"]' # Adjust as needed based on your feature requirements

STEP2_VARIABLES=$(jq -n \
--arg cloudVendor "AZURE" \
--argjson permissionsGroupFilters "[{\"featureType\": \"$AZURE_FEATURE_TYPE\", \"permissionsGroups\": $PERMS_GROUPS_ARRAY}]" \
'{
    cloudVendor: $cloudVendor,
    permissionsGroupFilters: $permissionsGroupFilters
}')

# Construct the full GraphQL payload
STEP2_PAYLOAD=$(jq -n \
--arg query "$STEP2_QUERY" \
--argjson variables "$STEP2_VARIABLES" \
'{query: $query, variables: $variables}')


echo "Retrieving required Azure permissions for feature: $AZURE_FEATURE_TYPE with groups: $(echo "$PERMS_GROUPS_ARRAY" | jq -r '.[] | @json') ..."
STEP2_RESPONSE=$(send_graphql_call "$STEP2_PAYLOAD")
REQUIRED_PERMISSIONS=$(echo "$STEP2_RESPONSE" | jq -r '.data.allCurrentFeaturePermissionsForCloudAccounts[0].featurePermissions')

if [ "$REQUIRED_PERMISSIONS" != "null" ]; then
    echo "Required Azure permissions JSON:"
    echo "$REQUIRED_PERMISSIONS" | jq -r '.[].permissionJson' | jq . # Pretty print the nested JSON
    echo -e "\n!!! IMPORTANT: Manually create a custom Azure role with these permissions and assign it to your Azure AD Application at the subscription level. !!!"
    echo "!!! The script will pause here to allow you to perform this manual step. Press Enter to continue... !!!"
    read -p "Press Enter to continue after creating and assigning the Azure custom role..."
else
    echo "Failed to retrieve required Azure permissions. Response: $STEP2_RESPONSE"
    delete_session
    exit 1
fi

# --- Step 3: Add Cloud Account without OAuth ---
echo -e "\n--- Step 3: Adding Azure Cloud Account without OAuth ---"
STEP3_MUTATION='
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
'

# Convert bash array of regions to JSON array string for jq
AZURE_REGIONS_JSON=$(printf '%s\n' "${AZURE_REGIONS[@]}" | jq -R . | jq -s .)

# Base features input
FEATURES_INPUT='{"featureType": "'"${AZURE_FEATURE_TYPE}"'", "policyVersion": 0, "permissionsGroups": [{"permissionsGroup": "BASIC", "version": 2}, {"permissionsGroup": "RECOVERY", "version": 3}]}'

# Add resourceGroup if provided
if [ -n "$AZURE_RG_NAME" ] && [ -n "$AZURE_RG_REGION" ]; then
    FEATURES_INPUT=$(echo "$FEATURES_INPUT" | jq '. + {"resourceGroup": {"name": "'"${AZURE_RG_NAME}"'", "region": "'"${AZURE_RG_REGION}"'"}}')
fi

# Construct subscriptions array dynamically
SUBSCRIPTIONS_INPUT=$(jq -n \
    --arg features_str "$FEATURES_INPUT" \
    --arg subscription_name "$AZURE_SUBSCRIPTION_NAME" \
    --arg subscription_id "$AZURE_SUBSCRIPTION_ID" \
    '[
        {
            features: [ ( $features_str | fromjson ) ],
            subscription: {
                name: $subscription_name,
                nativeId: $subscription_id
            }
        }
    ]')


STEP3_VARIABLES=$(jq -n \
--arg tenantDomainName "$AZURE_TENANT_DOMAIN_NAME" \
--arg azureCloudType "$AZURE_CLOUD_TYPE" \
--argjson subscriptions "$SUBSCRIPTIONS_INPUT" \
--argjson regions "$AZURE_REGIONS_JSON" \
--argjson isAsynchronous false \
'{
    input: {
        tenantDomainName: $tenantDomainName,
        azureCloudType: $azureCloudType,
        subscriptions: $subscriptions,
        regions: $regions,
        isAsynchronous: $isAsynchronous
    }
}')

# Construct the full GraphQL payload
STEP3_PAYLOAD=$(jq -n \
--arg query "$STEP3_MUTATION" \
--argjson variables "$STEP3_VARIABLES" \
'{query: $query, variables: $variables}')

echo "Adding Azure subscription '${AZURE_SUBSCRIPTION_NAME}' (${AZURE_SUBSCRIPTION_ID}) for tenant '${AZURE_TENANT_DOMAIN_NAME}'..."
STEP3_RESPONSE=$(send_graphql_call "$STEP3_PAYLOAD")

ADD_ACCOUNT_STATUS=$(echo "$STEP3_RESPONSE" | jq -r '.data.addAzureCloudAccountWithoutOauth.status[0].error')

if [ -z "$ADD_ACCOUNT_STATUS" ] || [ "$ADD_ACCOUNT_STATUS" == "null" ]; then
    echo "Azure Cloud Account integration process initiated successfully. Check RSC UI for final status."
    echo "Response: $(echo "$STEP3_RESPONSE" | jq .)"
else
    echo "Failed to add Azure Cloud Account. Error: $ADD_ACCOUNT_STATUS"
    echo "Full Response: $(echo "$STEP3_RESPONSE" | jq .)"
    delete_session
    exit 1
fi

# --- Cleanup ---
delete_session
echo -e "\nScript execution finished."