import json
from pathlib import Path
import boto3
import os
from botocore.exceptions import ClientError

base_path = str(Path.cwd())  + '\\testpp\\cronproj'
root_file_path = base_path + '\\root.json'
root_file = open(root_file_path,'r')
root_creds = json.load(root_file)
root_access = root_creds['user']
awsid = root_creds['awsid']
root_secret = root_creds['pass']

root_iam_client = boto3.client('iam',aws_access_key_id=root_access,
aws_secret_access_key=root_secret ,region_name = 'us-east-1')
#create iam client variabl for root use
user ='CrontUser'
create_user_resp = root_iam_client.create_user(UserName = user)
#create user that will be used through out the project
create_key_response = root_iam_client.create_access_key(UserName=user)
#generate authentication keys for the iam user
iam_path = base_path + '\\iam'
Path(iam_path).mkdir(exist_ok = True,parents =True)
#create a path for the user
access = create_key_response['AccessKey']['AccessKeyId']
secret = create_key_response['AccessKey']['SecretAccessKey']
creds_file = open(str(iam_path)+ '\\creds.json','w')
json.dump({'id': access, 'pass': secret},creds_file)
creds_file.close()

iam_path = base_path + '\\iam'
Path(iam_path).mkdir(exist_ok = True,parents =True)
inline_path = iam_path + '\\inline_policies'
Path(inline_path).mkdir(exist_ok = True,parents =True)
aws_policy_path = iam_path + '\\policies'
Path(aws_policy_path).mkdir(exist_ok = True,parents =True)
arn_path = aws_policy_path + '\\arn.json'
arn_dict = json.load(open(arn_path,"r"))
for item in arn_dict.values():
    attach_iam__ec2_response = root_iam_client.attach_user_policy(UserName=user,PolicyArn=item )


for item in os.listdir(inline_path):
    try:
        policy = arn_dict = json.load(open(inline_path + f"\\{item}","r"))
        policy_name = item.replace('.json',"")
        root_iam_client.create_policy(PolicyName=  policy_name, PolicyDocument = json.dumps(policy))
        root_iam_client.attach_user_policy(UserName=user,
        PolicyArn=create_policy['Policy']['Arn'])
    except ClientError:
        policy = arn_dict = json.load(open(inline_path + f"\\{item}","r"))
        policy_name = item.replace('.json',"")
        root_iam_client.delete_policy(PolicyArn=f"arn:aws:iam::{awsid}:policy/{  policy_name}")
        policy = arn_dict = json.load(open(inline_path + f"\\{item}","r"))
        create_policy= root_iam_client.create_policy(PolicyName= policy_name, PolicyDocument = json.dumps(policy))
        root_iam_client.attach_user_policy(UserName=user,
        PolicyArn=create_policy['Policy']['Arn'])
        
        

role_path = iam_path + '\\role'
trust_policy_path =  role_path + '\\ec2_trust_policy.json'
ec2_trust_policy_file = open(trust_policy_path,"r")
ec2_trust_policy = json.load(ec2_trust_policy_file)
role_name = 'PipelineRole'


try:
    create_ec2_role_response = root_iam_client.create_role(RoleName = role_name,
    AssumeRolePolicyDocument = json.dumps(ec2_trust_policy))
except ClientError:
    print('new_role_name')
    
    
role_policy_path =  role_path + '\\role_policies.json'
role_policy_file = open(role_policy_path,"r")
role_policy= json.load(role_policy_file)        

for item in role_policy.values():
    root_iam_client.attach_role_policy(RoleName =role_name,PolicyArn = item)
    
instance_profile_name = 'DeployProfile'  
try:
    instance_profile = root_iam_client.create_instance_profile (InstanceProfileName = instance_profile_name )
#use boto3 to create the instance pofile
    root_iam_client.add_role_to_instance_profile(InstanceProfileName = instance_profile_name ,RoleName = role_name)
#attach the DeployPipeline role to the DeployProjectProfile instance profile
except ClientError:   
    print('new_instance_profile_name')
    
iam_output = open(iam_path + '\\iam.json','w')
iam_output.write(json.dumps({'role' : role_name, 'instancedP':instance_profile_name  }))
iam_output.close()