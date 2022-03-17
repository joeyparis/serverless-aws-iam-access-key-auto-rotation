# (c) 2021 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer Agreement available at
# https://aws.amazon.com/agreement/ or other written agreement between Customer
# and Amazon Web Services, Inc.

"""Key Action Handler.

This module provides the functions to log, execute,
rotate, deactivate, and delete IAM Keys.
"""

import json

from config import Config, log
from aws_partitions import get_partition_for_region, get_iam_region,\
    get_partition_regions

config = Config()


def log_actions(action_queue, dryrun=False):
    if not action_queue:
        log.info("No actions to be taken on this account.")
        return

    for action_spec in action_queue:
        action = action_spec['action']
        key_metadata = action_spec['key']
        access_key_id = key_metadata["AccessKeyId"]
        reason = action_spec['reason'].value

        if action == 'ROTATE':
            if dryrun:
                log.info(
                    f"Would create new key to replace {access_key_id}"
                    f" -- {reason}")
            else:
                log.info(
                    f"Creating new key to replace {access_key_id}"
                    f" -- {reason}")
        elif action == 'DEACTIVATE':
            if dryrun:
                log.info(
                    f"Would deactivate {access_key_id}"
                    f" -- {reason}")
            else:
                log.info(
                    f"Deactivating {access_key_id}"
                    f" -- {reason}")
        elif action == 'DELETE':
            if dryrun:
                log.info(
                    f"Would delete {access_key_id}"
                    f" -- {reason}")
            else:
                log.info(
                    f"Deleting {access_key_id}"
                    f" -- {reason}")


def execute_actions(action_queue, account_session):
    for action_spec in action_queue:
        action = action_spec['action']
        key_metadata = action_spec['key']

        if action == 'ROTATE':
            rotate_key(key_metadata, account_session)
        elif action == 'DEACTIVATE':
            deactivate_key(key_metadata, account_session)
        elif action == 'DELETE':
            delete_key(key_metadata, account_session)


def rotate_key(key_metadata, account_session):
    user_name = key_metadata['UserName']
    access_key_id = key_metadata['AccessKeyId']
    log.info(f'Rotating user {user_name} key {access_key_id}')

    iam_client = account_session.client('iam')
    sts_client = account_session.client('sts')

    # get account id and region from session
    account_id = sts_client.get_caller_identity()["Account"]
    my_region = account_session.region_name

    # use default iam regions to store secret
    partition = get_partition_for_region(my_region)
    iam_region = get_iam_region(partition)
    sm_client = account_session.client(
        'secretsmanager', region_name=iam_region)
    replication_regions = get_partition_regions(partition)

    # TODO: parameterize this instead of hardcoding
    if partition == 'aws-us-gov':
        replication_regions = ['us-gov-east-1']
    elif partition == 'aws':
        replication_regions = ['us-east-2', 'us-west-1', 'us-west-2']

    # Create new access key
    new_access_key = iam_client.create_access_key(
        UserName=user_name)['AccessKey']
    new_access_key_str = json.dumps(
        new_access_key, indent=4, sort_keys=True, default=str)

    secret_name = config.secretNameFormat.format(user_name)
    secret_arn = config.secretArnFormat.format(
        partition=partition, account_id=account_id, secret_name=secret_name,
        region_name=iam_region)

    # Create new secret, or store in existing
    try:
        # will throw error if secret does not yet exist
        secret = sm_client.describe_secret(
            SecretId=secret_name)
        # update secret
        sm_client.put_secret_value(SecretId=secret_name,
                                   SecretString=new_access_key_str)
        # make sure secret is replicated to all regions
        replication_status = secret.get('ReplicationStatus', [])
        current_replication_regions = [x['Region'] for x in replication_status]
        missing_regions = [x for x in replication_regions
                           if x not in current_replication_regions]
        if missing_regions:
            sm_client.replicate_secret_to_regions(
                SecretId=secret_name,
                AddReplicaRegions=[{'Region': x} for x in missing_regions],
                ForceOverwriteReplicaSecret=True
            )
    except sm_client.exceptions.ClientError as error:
        # create if we caught an error on describe
        if error.response['Error']['Code'] == 'ResourceNotFoundException':
            sm_client.create_secret(
                Name=secret_name, Description='Auto-created secret',
                SecretString=new_access_key_str,
                AddReplicaRegions=[{'Region': x} for x in replication_regions],
                ForceOverwriteReplicaSecret=True
            )
        else:
            raise error

    user = iam_client.get_user(
        UserName=user_name
    )['User']
    user_arn = user['Arn']

    resource_policy_document = config.secretPolicyFormat.format(
        user_arn=user_arn)
    sm_client.put_resource_policy(SecretId=secret_name,
                                  ResourcePolicy=resource_policy_document,
                                  BlockPublicPolicy=True)

    policy_name = 'SecretsAccessPolicy'
    try:
        iam_client.get_user_policy(UserName=user_name, PolicyName=policy_name)
    except iam_client.exceptions.ClientError as error:
        # TODO - IAM uses IAM.Client.exceptions.NoSuchEntityException
        #  Find out if it inherits from ClientError. If it does, this code is probably ok,
        #  but may need to change ResourceNotFoundException to NoSuchEntityException
        if error.response['Error']['Code'] == 'NoSuchEntity':
            policy_document = config.iamPolicyFormat.format(
                account_id=account_id, secret_arn=secret_arn)
            iam_client.put_user_policy(UserName=user_name,
                                       PolicyName=policy_name,
                                       PolicyDocument=policy_document)
        else:
            raise error

    return


def deactivate_key(key_metadata, account_session):
    user_name = key_metadata['UserName']
    access_key_id = key_metadata['AccessKeyId']
    log.info(f'Deactivating user {user_name} key {access_key_id}')

    iam_client = account_session.client('iam')
    iam_client.update_access_key(UserName=user_name,
                                 AccessKeyId=access_key_id,
                                 Status='Inactive')


def delete_key(key_metadata, account_session):
    user_name = key_metadata['UserName']
    access_key_id = key_metadata['AccessKeyId']
    log.info(f'Deleting user {user_name} key {access_key_id}')

    iam_client = account_session.client('iam')
    iam_client.delete_access_key(UserName=user_name,
                                 AccessKeyId=access_key_id)
