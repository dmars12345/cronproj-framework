import json
from pathlib import Path
import boto3
import shutil


# inf = open(str(Path.cwd()) + '\\cloud.json','r')
# infa = json.load(inf)
#open up the infrasctructue dict from the output of the infrastructure.py script

base_path = str(Path.cwd())  + '\\testpp\\cronproj'
s3_path = base_path + '\\s3'
s3_file = open(s3_path + '\\s3.json','r')
s3_dict = json.load(s3_file)
iam_path = base_path + '\\iam'
iam_file = open(iam_path + '\\iam.json','r')
iam_dict = json.load(iam_file)
ecr_path = base_path + '\\ecr'
ecr_file = open(ecr_path + '\\ecr.json','r')
ecr_dict = json.load(ecr_file)
ec2_path = base_path + '\\ec2'
ec2_file = open(ec2_path + '\\ec2.json','r')
ec2_dict = json.load(ec2_file)

creds_file = open(str(iam_path)+ '\\creds.json','r')
create_key_response = json.load(creds_file)
access = create_key_response['id']
secret = create_key_response['pass']

infa = {'ecr': ecr_dict,'s3':s3_dict,'ec2':ec2_dict,'iam' :iam_dict}

#save the iam user created secret and access keys as variables

s3r =  boto3.resource('s3',aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-2')
s3_client=  boto3.client('s3',aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-2')

script_name = 'test-scriptt'
#name the code that will be put on aws

#make directory
script_bucket = f'{script_name}-bucket'
#bucket string name
aws_script_bucket = s3r.create_bucket(Bucket = script_bucket,CreateBucketConfiguration={'LocationConstraint' :  'us-east-2'})
#bucket aws object
put_block_public_access = s3_client.put_public_access_block(Bucket = script_bucket,PublicAccessBlockConfiguration={"BlockPublicAcls":True ,
"IgnorePublicAcls": True,"BlockPublicPolicy":True,"RestrictPublicBuckets":True})
#response of making the bucket private