<!--
title: 'AWS IAM Access Key Auto Rotation'
description: 'Serverless configuration and Python scripts for automatically rotating AWS IAM User Access Keys and notifying their users'
layout: Doc
framework: v2
platform: AWS
language: python
priority: 2
authorLink: 'https://github.com/joeyparis'
authorName: 'Joey Paris'
authorAvatar: 'https://avatars1.githubusercontent.com/u/13742415?s=200&v=4'
-->


# AWS IAM Access Key Auto Rotation

This serverless configuration and Python scripts were adapted from [this Amazon guide](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/automatically-rotate-iam-user-access-keys-at-scale-with-aws-organizations-and-aws-secrets-manager.html) which relies on [this github repository](https://github.com/aws-samples/aws-iam-access-key-auto-rotation). The original guide was too "involved" for my liking with steps like manually uploading code to S3, creating multiple CloudFormation tempaltes, etc. so this repo simplifies all those steps into an easy to run serverless config.

Deployment will set up an auto-rotation function that will automatically rotate your AWS IAM User Access Keys every 90 days. At 100 days it will then disable the old Access Keys. And finally at 110 days it will delete the old Access Keys. (These timeframes are adjustable). It will also set up a secret inside AWS Secrets Manager to store the new Access Keys, with a resource policy that permits only the AWS IAM User access to them. There is also automation to send emails with a custome email template via SES that will alert account owners when rotation occurs.

## Minimum Configuration

The minimum configuration for a successful deployment requires the following environment variables:

Variable|Type|Description
--------|----|-----------
DRY_RUN_FLAG|boolean|Defaults to `true`, must be turned to `false` to actually rotate keys. A test run is recommended before beginning rotations.
SLS_ORG|string|Your organization name from [serverless.com](https://www.serverless.com)
PRIMARY_ACCOUNT_ID|string|Your primary AWS account ID
AWS_ORG_ID|string|Your account's [AWS organization ID](https://console.aws.amazon.com/organizations)
SENDER_EMAIL|string|The SES email address used to send the rotation notification emails
RECIPIENT_EMAIL|string|The SES email to receive rotation notification emails. *This only applies if your primary accounts does not have access to the `organizations:ListAccounts` permission, such as if you are part of a consolidated billing organization. Otherwise the recipient will be the email of each account.*
SES_DOMAIN|string|The confirmed SES domain for sending emails.

## Optional Configuration

Variable|Type|Default|Description
--------|----|-------|-----------
ROTATION_PERIOD|int|90|The number of days between each rotation
INSTALLATION_GRACE_PERIOD|int|10|The number of days between rotation and deactivation
RECOVERY_GRACE_PERIOD|int|10|The number of days between deactivation and deletion
PENDING_ACTION_WARN_PERIOD|int|7|The number of days ahead of time to warn users of pending actions
IAM_EXEMPTION_GROUP|string|ASAIAMExemptionsGroup|The name of the user group for rotation exempted accounts
IAM_ASSUMED_ROLE_NAME|string|aws-iam-access-key-auto-rotation-lambda-assumed-role|The name of the assumed role generated by serverless
EXECUTION_ROLE_NAME|string|aws-iam-access-key-auto-rotation-lambda-execution-role|The name of the execution role generated by serverless
ROLE_SESSION_NAME|string|aws-iam-access-key-auto-rotation-dev-AccessKeyRotate|The name of the role session generated by serverless
EMAIL_TEMPLATE_ENFORCE|string|iam-auto-key-rotation-enforcement.html|The html file used for notifying users of key rotations *When DRY_RUN_FLAG is `false`*
EMAIL_TEMPLATE_AUDIT|string|iam-auto-key-rotation-enforcement.html|The html file used for notifying users of key rotations *When DRY_RUN_FLAG is `true`*

### Deployment

Deployment is super easy once you have `serverless` installed. Just install dependencies and use the `deploy` command! Accounts keys will be checked for rotation needs once every 24 hours

```
$ yarn install
$ serverless deploy
```

### Invocation

You can manually invoke the check by running:

```bash
serverless invoke --function AccountInventory
```

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

