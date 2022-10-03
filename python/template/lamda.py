
import json
from pathlib import Path
import boto3
import shutil
import time


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
script_name = 'test-scriptt'

creds_file = open(str(iam_path)+ '\\creds.json','r')
create_key_response = json.load(creds_file)
access = create_key_response['id']
secret = create_key_response['pass']

infa = {'ecr': ecr_dict,'s3':s3_dict,'ec2':ec2_dict,'iam' :iam_dict}

s3_resource =  boto3.resource('s3',aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-1')
s3_client=  boto3.client('s3',aws_access_key_id=access,
aws_secret_access_key=secret)

script_name = 'test-scriptt'
script_bucket = f'{script_name}-bucket'
scipt_infa_path = base_path + '\\script_infascturcture'
current_infa_path  = scipt_infa_path + f'\\{script_name}'
current_infa_path_image =  current_infa_path + '\\image'
script_path = scipt_infa_path + '\\code'

lambda_code = f'''import json
import boto3
def lambda_handler(event, context): 
    s3_client = boto3.client('s3',aws_access_key_id='|ACCESS|',
    aws_secret_access_key='|SECRET|',region_name = 'us-east-1')
    ec2_client= boto3.client('ec2',aws_access_key_id='|ACCESS|',
    aws_secret_access_key='|SECRET|',region_name = 'us-east-1')
    response = s3_client.list_objects_v2(Bucket = '|INSTANCE|')
    all = response['Contents']        
    latest = max(all, key=lambda x: x['LastModified'])['Key']
    stop = ec2_client.terminate_instances(InstanceIds= [latest])
    return json.dumps(stop)
'''
#the lambda code will terminate the instance after the docker container add thes data to s3 bucket
#we created 

lambda_code = lambda_code.replace('|ACCESS|',access)
lambda_code= lambda_code.replace('|SECRET|',secret)
lambda_code= lambda_code.replace('|INSTANCE|',infa['s3']['instance'])

open(str(script_path) + f'\\{script_name}_crontab.py','w')
lambda_path = script_path / 'lambda'
lambda_path.mkdir(exist_ok = True,parents =True)
lambda_py = open(str(lambda_path) +'\\lambda_function.py','w')
lambda_py.write(lambda_code)
lambda_py.close()
shutil.make_archive(str(lambda_path) +'\\lambda', 'zip', str(lambda_path))
s3_client.upload_file(str(lambda_path) +'\\lambda.zip', infa['s3']['code'], f'{script_name}/livelambda.zip')
# make a zipfile with the code and end to 3 

lambda_client= boto3.client('lambda',aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-1')
iam_client= boto3.client('iam',aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-1')
lambda_trust_policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
#create a variable for the lambda trust policy
lambda_role_response = iam_client.create_role(RoleName = f"-{script_name}-instance-role",
#create the trust policy roll
AssumeRolePolicyDocument = json.dumps(lambda_trust_policy))

try:
    create_lambda_response = lambda_client.create_function(FunctionName = f"{script_name}-instance-function",
    Code = {'S3Bucket':  infa['s3']['code'],'S3Key':f'{script_name}/livelambda.zip'},Role = lambda_role_response['Role']['Arn'], Runtime = 'python3.9',Handler=   'lambda_function.lambda_handler')
except:
    time.sleep(10)
    create_lambda_response = lambda_client.create_function(FunctionName = f"{script_name}-instance-function",
    Code = {'S3Bucket':  infa['s3']['code'],'S3Key':f'{script_name}/livelambda.zip'},Role = lambda_role_response['Role']['Arn'], Runtime = 'python3.9',Handler=   'lambda_function.lambda_handler')
#create the lambda function
    
lambda_client.add_permission(FunctionName=  create_lambda_response['FunctionName'],Action= 'lambda:InvokeFunction',
Principal='s3.amazonaws.com',SourceArn= f"arn:aws:s3:::{script_bucket}",StatementId = f'{script_name}-bucket-configuration-notif') 
#allow s3 to invoke the lmabda function
trig_doc = {'LambdaFunctionConfigurations': []}
trig_doc['LambdaFunctionConfigurations'] = []   
trig_doc["LambdaFunctionConfigurations"] .append({"Id": "live-placements-instance-term-statement",
"LambdaFunctionArn": create_lambda_response['FunctionArn'],"Events": ["s3:ObjectCreated:Put"],
'Filter': {'Key':{'FilterRules': [{'Name':'Prefix', 'Value' :  ""},
{'Name': 'Suffix', 'Value': ''}]}}})
#create a variable for the functionconfirugration that allow the s3 bucket to invoke the lambda function
try:
    create_put_notification_con = s3_client.put_bucket_notification_configuration(Bucket = script_bucket,NotificationConfiguration =  trig_doc)

except:
    time.sleep(20)
    create_put_notification_con = s3_client.put_bucket_notification_configuration(Bucket = script_bucket,NotificationConfiguration =  trig_doc)
#push to aws



scipt_infa_path = base_path + '\\script_infascturcture'
current_infa_path  = scipt_infa_path + f'\\{script_name}'
current_infa_path_lambda =  current_infa_path + '\\lambda'
Path(current_infa_path_lambda).mkdir()

script_lambda_file = open(current_infa_path_lambda + '\\lambda.json','w')
script_lambda_file.write(json.dumps({'trust_policy': json.dumps(lambda_trust_policy ), "arn": create_lambda_response['FunctionArn'],
                                     
                                    'config': json.dumps(trig_doc) }))
script_lambda_file.close()
