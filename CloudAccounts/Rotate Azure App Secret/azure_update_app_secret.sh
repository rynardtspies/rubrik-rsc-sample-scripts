#!/bin/bash

# Script to update the App Secret for all Azure Subscriptions from a single Azure Tenant in Rubrik Security Cloud (RSC)
# This script uses curl to make GraphQL API calls.

# --- Configuration ---
# Set these environment variables or pass them as arguments
# export RUBRIK_CLIENT_ID="your_rsc_client_id"
# export RUBRIK_CLIENT_SECRET="your_rsc_client_secret"

# --- Argument Parsing ---
display_usage() {
    echo "Usage: $0 --env_name <RSC_ENV> --azure_app_secret_key <AZURE_APP_SECRET> --azure_tenant_domain_name <AZURE_TENANT_DOMAIN> [--azure_cloud_type <CLOUD_TYPE>] [--client_id <RSC_CLIENT_ID>] [--client_secret <RSC_CLIENT_SECRET>]"
    echo ""
    echo "Required:"
    echo "  --env_name               : Your Rubrik Security Cloud environment name (e.g., 'rscetf')."
    echo "  --azure_app_secret_key   : Azure AD Application secret key (value)."
    echo "  --azure_tenant_domain_name: Azure AD Tenant Domain Name (e.g., 'yourcompany.onmicrosoft.com')."
    echo ""
    echo "Optional:"
    echo "  --azure_cloud_type       : Azure Cloud Type (default: 'AZUREPUBLICCLOUD'). Other: 'AZUREGOVERNMENTCLOUD'."
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
        --azure_app_secret_key) AZURE_APP_SECRET_KEY="$2"; shift ;;
        --azure_tenant_domain_name) AZURE_TENANT_DOMAIN_NAME="$2"; shift ;;
        --azure_cloud_type) AZURE_CLOUD_TYPE="$2"; shift ;;
        -h|--help) display_usage ;;
        *) echo "Unknown parameter passed: $1"; display_usage ;;
    esac
    shift
done

# Validate required arguments
if [ -z "$ENV_NAME" ] || [ -z "$AZURE_APP_SECRET_KEY" ] || \
   [ -z "$AZURE_TENANT_DOMAIN_NAME" ]; then
    echo "Error: Missing required arguments."
    display_usage
fi

# Set defaults if not provided
AZURE_CLOUD_TYPE=${AZURE_CLOUD_TYPE:-"AZUREPUBLICCLOUD"}
SHOULD_REPLACE_APP_CREDS=${SHOULD_REPLACE_APP_CREDS:-"false"}
CLIENT_ID=${CLIENT_ID:-$RUBRIK_CLIENT_ID}
CLIENT_SECRET=${CLIENT_SECRET:-$RUBRIK_CLIENT_SECRET}
AZURE_FEATURE=${AZURE_FEATURE:-"CLOUD_NATIVE_PROTECTION"}

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
# --- Step 1: Getting required app Information from RSC ---
echo -e "\n--- Step 1: Getting required app Information from RSC ---"
STEP1_QUERY='
query AllAzureCloudAccountTenants($includeSubscriptionDetails: Boolean!, $features: [CloudAccountFeature!], $feature: CloudAccountFeature!) {
  allAzureCloudAccountTenants(includeSubscriptionDetails: $includeSubscriptionDetails, features: $features, feature: $feature) {
    appName
    clientId
    azureCloudAccountTenantRubrikId
    domainName
    cloudType
  }
}
'
STEP1_VARIABLES=$(jq -n \
  --arg feature "$AZURE_FEATURE" \
  --arg azureTenants "$AZURE_TENANT_DOMAIN_NAME" \
  '{
    includeSubscriptionDetails: true,
    feature: $feature,
    azureTenants: $azureTenants
  }')
# Construct the full GraphQL payload
STEP1_PAYLOAD=$(jq -n \
--arg query "$STEP1_QUERY" \
--argjson variables "$STEP1_VARIABLES" \
'{query: $query, variables: $variables}')

STEP1_RESPONSE=$(send_graphql_call "$STEP1_PAYLOAD")
AZURE_APP_NAME=$(echo "$STEP1_RESPONSE" | jq -r '.data.allAzureCloudAccountTenants[0].appName')
AZURE_APP_ID=$(echo "$STEP1_RESPONSE" | jq -r '.data.allAzureCloudAccountTenants[0].clientId')
AZURE_DOMAIN_NAME=$(echo "$STEP1_RESPONSE" | jq -r '.data.allAzureCloudAccountTenants[0].domainName')
AZURE_CLOUD_TYPE=$(echo "$STEP1_RESPONSE" | jq -r '.data.allAzureCloudAccountTenants[0].cloudType')
# --- Step 2: Updating the Client Secret ---
echo -e "\n--- Step 2: Updating the Client Secret ---"
STEP2_MUTATION='
mutation AzureSetCustomerAppCredentialsMutation($input: SetAzureCloudAccountCustomerAppCredentialsInput!) {
  setAzureCloudAccountCustomerAppCredentials(input: $input)
}
'
STEP2_VARIABLES=$(jq -n \
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
STEP2_PAYLOAD=$(jq -n \
--arg mutation "$STEP2_MUTATION" \
--argjson variables "$STEP2_VARIABLES" \
'{query: $mutation, variables: $variables}')    

STEP2_RESPONSE=$(send_graphql_call "$STEP2_PAYLOAD")
STEP2_SUCCESS=$(echo "$STEP2_RESPONSE" | jq -r '.data.setAzureCloudAccountCustomerAppCredentials')

if [ "$STEP2_SUCCESS" = "true" ]; then
    echo "Azure App Secret updated successfully."
else
    echo "Failed to update the Azure App Secret."
    echo "Response: $STEP2_RESPONSE"
fi

# --- Cleanup ---
delete_session
echo -e "\nScript execution finished."