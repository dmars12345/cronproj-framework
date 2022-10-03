
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


s3_client = boto3.client('s3',aws_access_key_id=root_access,
aws_secret_access_key=root_secret ,region_name = 'us-east-1')
s3_resource = boto3.resource('s3',aws_access_key_id=root_access,
aws_secret_access_key=root_secret ,region_name = 'us-east-1')

code_bucket = 'cron-project-code'
# create a bucket so our user data scripts can easily grab our code
create_code_object = s3_resource.create_bucket(Bucket = code_bucket)
create_code_bucket = s3_client.put_public_access_block(Bucket = code_bucket,
PublicAccessBlockConfiguration={"BlockPublicAcls":True ,"IgnorePublicAcls": True,"BlockPublicPolicy":True,"RestrictPublicBuckets":True})
#block public access

live_instance_bucket = 'cron-instance-bucket'
#create bucket so we can stream line docker containers
create_live_instance_bucket = s3_resource.create_bucket(Bucket = live_instance_bucket)
s3_resource.create_bucket(Bucket = live_instance_bucket)
s3_client.put_public_access_block(Bucket = live_instance_bucket,PublicAccessBlockConfiguration={"BlockPublicAcls":True ,
"IgnorePublicAcls": True,"BlockPublicPolicy":True,"RestrictPublicBuckets":True})
#block public access
s3_dict = {'code': code_bucket , 'instance' : live_instance_bucket}
s3_path = base_path + '\\s3'
Path(s3_path).mkdir(exist_ok = True,parents =True)   
s3_output = open(s3_path + '\\s3.json','w')
s3_output.write(json.dumps(s3_dict))
s3_output.close()