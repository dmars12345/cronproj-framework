from pathlib import Path
import boto3
import os
from botocore.exceptions import ClientError
import json

base_path = str(Path.cwd())  + '\\testpp\\cronproj'
root_file_path = base_path + '\\root.json'
root_file = open(root_file_path,'r')
root_creds = json.load(root_file)
root_access = root_creds['user']
awsid = root_creds['awsid']
root_secret = root_creds['pass']
ecr_path = base_path + '\\ecr'

ecr_client = boto3.client('ecr',aws_access_key_id=root_access,
aws_secret_access_key=root_secret ,region_name = 'us-east-1')
ecr_name = "cron-ecr-repository"
ecr_response = ecr_client.create_repository(repositoryName=ecr_name,imageTagMutability='IMMUTABLE',imageScanningConfiguration={'scanOnPush': True},encryptionConfiguration={ 'encryptionType': 'AES256'})
#use boto 3 to create a ecr repository
ecr_policy = open(ecr_path + '\\ecr_policy.json','r')
ecr_policy =  json.load(ecr_policy)
ecr_client.set_repository_policy(repositoryName=ecr_name,policyText=json.dumps(ecr_policy))
#create and set policy for ecr
ecrArn = ecr_response['repository']['repositoryArn']
#save the arn as a variable
ecrUri =  ecr_response['repository']['repositoryUri']
#save the name as a variable
ecr_dict = {'Uri': ecrUri,'Arn':ecrArn, 'name': ecr_name}
#save a variable that will be used for output later 
ecr_path = base_path + '\\ecr'
Path(ecr_path).mkdir(exist_ok = True,parents =True) 
ecr_output = open(ecr_path + '\\ecr.json','w')
ecr_output.write(json.dumps(ecr_dict))
ecr_output.close()
