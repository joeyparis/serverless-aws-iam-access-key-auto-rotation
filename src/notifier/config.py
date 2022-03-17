# (c) 2021 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer Agreement available at
# https://aws.amazon.com/agreement/ or other written agreement between Customer
# and Amazon Web Services, Inc.

"""Config.

Provides configuration for the application.
"""

import os
from dataclasses import dataclass, field
from typing import Dict
from datetime import date, timezone, timedelta
import datetime

@dataclass
class Config:
    lambda_task_root = os.getenv('LAMBDA_TASK_ROOT')
    sender_email: str = os.getenv('SENDER_EMAIL')
    s3_bucket_name = os.getenv('S3_BUCKET_NAME')
    s3_bucket_prefix = os.getenv('S3_BUCKET_PREFIX')
