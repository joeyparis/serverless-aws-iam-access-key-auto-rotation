# (c) 2021 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer Agreement available at
# https://aws.amazon.com/agreement/ or other written agreement between Customer
# and Amazon Web Services, Inc.

"""Config.

Provides configuration for the application.
"""

import os
from dataclasses import dataclass
import datetime

# Logging configuration
import logging
log = logging.getLogger()
log.setLevel(logging.INFO)


@dataclass
class Config:
    """Configuration for the application."""

    # Email Template for Enforce Mode
    emailTemplateEnforce = os.getenv('EMAIL_TEMPLATE_ENFORCE')

    # Email Template for Audit Mode
    emailTemplateAudit = os.getenv('EMAIL_TEMPLATE_AUDIT')

    # The IAM Group being used to exclue users from this IAM key rotation
    # script
    iamExemptionGroup = os.getenv('IAM_EXEMPTION_GROUP')

    # The Arn of the Lambda Function used for Notification
    notifierLambdaArn = os.getenv('NOTIFIER_FUNCTION_ARN')

    # The IAM Assumed Role
    iamAssumedRoleName = os.getenv('IAM_ASSUMED_ROLE_NAME')

    # The IAM Role Session Name
    roleSessionName = os.getenv('ROLE_SESSION_NAME')

    # The number of days after which a key should be rotated
    rotationPeriod = int(os.getenv('ROTATION_PERIOD'))

    # Installation being time between rotation and deactivation
    installation_grace_period = int(os.getenv('INSTALLATION_GRACE_PERIOD'))

    # Recovery between deactivation and deletion
    recovery_grace_period = int(os.getenv('RECOVERY_GRACE_PERIOD'))

    # how many days ahead of time to warn users of pending actions
    pending_action_warn_period = int(os.getenv('PENDING_ACTION_WARN_PERIOD'))

    # Functionality flag that Enables/Disables key rotation functionality. 
    # 'True' only sends notifications to end users (Audit Mode).
    # 'False' preforms key rotation and sends notifications to end users (Remediation Mode)."
    dryrun = str(os.getenv('DRY_RUN_FLAG')).lower() == 'true'

    # Format for name of ASM secrets
    secretNameFormat = 'User_{}_AccessKey'

    # Format for ARN of ASM secrets
    secretArnFormat = 'arn:{partition}:secretsmanager:{region_name}:' \
                      '{account_id}:secret:{secret_name}'

    # Format for Secret Manager Resource Policy
    secretPolicyFormat = """{{
        "Version": "2012-10-17",
        "Statement": [
            {{
                "Effect": "Allow",
                "Principal": {{
                    "AWS": "{user_arn}"
                }},
                "Action": [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecretVersionIds",
                    "secretsmanager:ListSecrets"
                ],
                "Resource": "*"
            }}
        ]
    }}
    """

    iamPolicyFormat = """{{
        "Version": "2012-10-17",
        "Statement": [
            {{
                "Sid": "RetrieveSecretValue",
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecretVersionIds"
                ],
                "Resource": "{secret_arn}"
            }},
            {{
                "Sid": "ListSecret",
                "Effect": "Allow",
                "Action": "secretsmanager:ListSecrets",
                "Resource": "*"
            }}
        ]
    }}
    """
