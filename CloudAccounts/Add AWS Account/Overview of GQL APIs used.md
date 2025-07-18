# Add AWS Account Operations for Cloud-Native Protection

This document outlines the GraphQL operations used to integrate an AWS cloud account with Rubrik Security Cloud (RSC) for cloud-native protection. The process involves three distinct GraphQL calls that need to be executed in sequence, with an intervening manual step in the AWS console.

-----

## 1\. AwsCloudAccountValidateAndInitiateMutation

This mutation initiates the AWS cloud account creation process in RSC. It validates the provided account details and returns the necessary information to create the required IAM roles in your AWS environment via a CloudFormation template.

**Operation:**

```graphql
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
```

**Variables:**

The `input` variable specifies the AWS account to be added and the features to be enabled.

```json
{
    "input": {
        "action": "CREATE",
        "features": [
            "CLOUD_NATIVE_PROTECTION"
        ],
        "awsChildAccounts": [
            {
                "nativeId": "805594410305",
                "accountName": "RSPIES-ZURICH-TEST",
                "cloudType": "STANDARD"
            }
        ],
        "featuresWithPermissionsGroups": [
            {
                "featureType": "CLOUD_NATIVE_PROTECTION",
                "permissionsGroups": [
                    "BASIC"
                ]
            }
        ]
    }
}
```

**Response:**

A successful response will include the `initiateResponse` object, providing details like the `cloudFormationUrl` and `templateUrl`.

```json
{
  "data": {
    "validateAndCreateAwsCloudAccount": {
      "validateResponse": null,
      "initiateResponse": {
        "cloudFormationUrl": "https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/parameters?stackName=rubrik-polaris-nTZkjQ&templateURL=https%3A%2F%2Fspark-cloud-accounts-prod-000-64a46be8-71c3-11e9-82f7-983b8fd69.s3.amazonaws.com%2Ftemplate%2Frubrik-rbkpso20%2Fstack%2Fbba150b9-f7f5-464b-8189-4a6baf28c612.json%3FX-Amz-Algorithm%3DAWS4-HMAC-SHA256%26X-Amz-Credential%3DAKIAVVIPOTFW5B4LWPVO%252F20250716%252Fus-east-1%252Fs3%252Faws4_request%26X-Amz-Date%3D20250716T095137Z%26X-Amz-Expires%3D604800%26X-Amz-SignedHeaders%3Dhost%26X-Amz-Signature%3D56c08e2825621adaa9db51d3d92570535f12c671b6be367b2e357eeb99f8ddb4",
        "templateUrl": "https://spark-cloud-accounts-prod-000-64a46be8-71c3-11e9-82f7-983b8fd69.s3.amazonaws.com/template/rubrik-rbkpso20/stack/bba150b9-f7f5-464b-8189-4a6baf28c612.json?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVVIPOTFW5B4LWPVO%2F20250716%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250716T095137Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host%26X-Amz-Signature%3D56c08e2825621adaa9db51d3d92570535f12c671b6be367b2e357eeb99f8ddb4",
        "stackName": "rubrik-polaris-nTZkjQ",
        "externalId": "",
        "awsIamPairId": "",
        "featureVersions": [
          {
            "feature": "CLOUD_NATIVE_PROTECTION",
            "version": 0,
            "permissionsGroupVersions": [
              {
                "permissionsGroup": "BASIC",
                "version": 4,
                "__typename": "PermissionsGroupWithVersion"
              }
            ],
            "__typename": "AwsCloudAccountFeatureVersion"
          }
        ],
        "__typename": "AwsCloudAccountCreateResponse"
      },
      "__typename": "ValidateAndCreateAwsCloudAccountReply"
    }
  }
}
```

**Action Required:** Download the AWS CloudFormation Template from the `templateUrl` in the response. Deploy this template in your AWS account via the AWS CloudFormation service. Once the stack deployment is complete, copy the resulting **Role ARN** (e.g., `arn:aws:iam::805594410305:role/RSC-CloudNativeProtectionSetup-CrossAccountRole-wtyv7NKSBEze`). This ARN is required for the final step.

-----

## 2\. AwsCloudAccountProcessMutation

This mutation allows you to finalize the protection setup by specifying the AWS regions where Rubrik RSC should discover and protect cloud-native resources.

**Operation:**

```graphql
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
```

**Variables:**

The `input` includes the AWS account details and the specific regions to be protected.

```json
{
    "input": {
        "action": "CREATE",
        "awsChildAccounts": [
            {
                "nativeId": "805594410305",
                "accountName": "RSPIES-ZURICH-TEST",
                "cloudType": "STANDARD"
            }
        ],
        "features": [
            "CLOUD_NATIVE_PROTECTION"
        ],
        "awsRegions": [
            "EU_WEST_2"
        ],
        "featuresWithPermissionsGroups": [
            {
                "featureType": "CLOUD_NATIVE_PROTECTION",
                "permissionsGroups": [
                    "BASIC"
                ]
            }
        ]
    }
}
```

**Response:**

The response confirms the processing of the specified AWS child accounts and regions.

```json
{
  "data": {
    "finalizeAwsCloudAccountProtection": {
      "awsChildAccounts": [
        {
          "id": "3d725885-03c0-4cef-b1c7-5f4a8a0e9635",
          "nativeId": "805594410305",
          "__typename": "AwsCloudAccount"
        }
      ],
      "__typename": "FinalizeAwsCloudAccountProtectionReply"
    }
  }
}
```

-----

## 3\. RegisterAwsFeatureArtifactsMutation

This final mutation registers the AWS artifacts, specifically the Cross-Account Role ARN obtained from the CloudFormation stack deployment, with RSC. This step securely connects your AWS account with Rubrik Security Cloud.

**Operation:**

```graphql
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
```

**Variables:**

The `input` contains the `awsNativeId` and the `externalArtifacts` that include the `CROSSACCOUNT_ROLE_ARN`.

```json
{
    "input": {
        "awsArtifacts": [
            {
                "awsNativeId": "805594410305",
                "features": [
                    "CLOUD_NATIVE_PROTECTION"
                ],
                "externalArtifacts": [
                    {
                        "externalArtifactKey": "CROSSACCOUNT_ROLE_ARN",
                        "externalArtifactValue": "arn:aws:iam::805594410305:role/RSC-CloudNativeProtectionSetup-CrossAccountRole-wtyv7NKSBEze"
                    }
                ]
            }
        ],
        "cloudType": "STANDARD"
    }
}
```

**Response:**

A successful response confirms that the AWS artifacts, including the Cross-Account Role ARN, have been registered.

```json
{
  "data": {
    "registerAwsFeatureArtifacts": {
      "allAwsNativeIdtoRscIdMappings": [
        {
          "awsCloudAccountId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
          "awsNativeId": "805594410305",
          "message": null,
          "__typename": "AwsNativeIdToRscIdMapping"
        }
      ],
      "__typename": "RegisterAwsFeatureArtifactsReply"
    }
  }
}
```

-----