import boto3
from botocore.exceptions import ClientError
import json
import logging
import os


ami_id ='ami-07ab1fd3a20f0cfbf'

asg_client = boto3.client('autoscaling',region_name='eu-west-1')
ec2_client = boto3.client('ec2')
sns = boto3.client("sns")

def get_launch_template_id_for_asg(asg_name):
    try:
        asg_describe = asg_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name])

        # Make sure the Auto Scaling group exists
        if len(asg_describe['AutoScalingGroups']) == 0:
            raise ValueError(
                 "The configured Auto Scaling group "
                 "does not exist: {}".format(asg_name))

        asg_details = asg_describe['AutoScalingGroups'][0]

        # ASG may have a LaunchTemplate, MixedInstancePolicy or LaunchConfiguration
        if 'LaunchTemplate' in asg_details.keys():
            return(asg_details['LaunchTemplate']['LaunchTemplateId'])
        elif 'MixedInstancesPolicy' in asg_details.keys():
            return(asg_details['MixedInstancesPolicy']
                              ['LaunchTemplate']
                              ['LaunchTemplateSpecification']
                              ['LaunchTemplateId'])
        else:
            return(None)

    except ClientError as e:
        logging.error("Error describing Auto Scaling group.")
        raise e

def create_launch_template_version_with_new_ami(lt_id, ami_id):
    try:
        latest_lt_version = ec2_client.describe_launch_templates(
            LaunchTemplateIds=[lt_id])['LaunchTemplates'][0]['LatestVersionNumber']

        response = ec2_client.create_launch_template_version(
                          LaunchTemplateId=lt_id,
                          SourceVersion=str(latest_lt_version),
                          LaunchTemplateData={'ImageId': ami_id})
        logging.info("Created new launch template version for {} : {} with "
                     "image {}".format(lt_id, str(latest_lt_version), ami_id))
        return(response)

    except ClientError as e:
        logging.error('Error creating the new launch template version')
        raise e




paginator = asg_client.get_paginator('describe_auto_scaling_groups')
page_iterator = paginator.paginate(
    PaginationConfig={'PageSize': 100})

substring='eks'
filtered_args = page_iterator.search(f"AutoScalingGroups[?contains(AutoScalingGroupName,`{substring}`)][]")


for asg in filtered_args:
    print(asg['AutoScalingGroupName'])

    lt_id = get_launch_template_id_for_asg(asg['AutoScalingGroupName'])
    create_launch_template_version_with_new_ami(lt_id, ami_id)
    print (lt_id)

