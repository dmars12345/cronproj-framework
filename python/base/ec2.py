from pathlib import Path
import boto3
import os
import json
from botocore.exceptions import ClientError
import time



base_path = str(Path.cwd())  + '\\testpp\\cronproj'
root_file_path = base_path + '\\root.json'
root_file = open(root_file_path,'r')
root_creds = json.load(root_file)
root_access = root_creds['user']
awsid = root_creds['awsid']
root_secret = root_creds['pass']
iam_path = base_path + '\\iam'


creds_file = open(str(iam_path)+ '\\creds.json','r')
create_key_response = json.load(creds_file)
access = create_key_response['id']
secret = create_key_response['pass']

ec2_client = boto3.client('ec2',aws_access_key_id=root_access,
aws_secret_access_key=root_secret,region_name = 'us-east-1')
ec2_resource = boto3.resource('ec2',aws_access_key_id=root_access,
aws_secret_access_key=root_secret,region_name = 'us-east-1')

s3_client = boto3.client('s3',aws_access_key_id=root_access,
aws_secret_access_key=root_secret ,region_name = 'us-east-1')
s3_resource = boto3.resource('s3',aws_access_key_id=root_access,
aws_secret_access_key=root_secret ,region_name = 'us-east-1')

s3_path = base_path + '\\s3'
s3_file = open(s3_path + '\\s3.json','r')
s3_dict = json.load(s3_file)

iam_path = base_path + '\\iam'
iam_file = open(iam_path + '\\iam.json','r')
iam_dict = json.load(iam_file)

live_instance_bucket = s3_dict['instance']

instance_profile_name = iam_dict['instancedP']


vpc = ec2_resource.create_vpc(CidrBlock='172.31.0.0/16')
#create a vpc resource
ig = ec2_resource.create_internet_gateway()
#create an internergateway 
vpc.attach_internet_gateway(InternetGatewayId=ig.id)
#assign the vpc to the interenet gateway
route_table = vpc.create_route_table()
#create a route table for the vpc
route = route_table.create_route(DestinationCidrBlock='0.0.0.0/0',GatewayId=ig.id)
#create a route to the  with the internet gateway we made
subnet = ec2_resource.create_subnet(CidrBlock='172.31.0.0/16', VpcId=vpc.id)
#create a subnet
route_table.associate_with_subnet(SubnetId=subnet.id)
#assosicate the route table witht the subnet
sec_group = ec2_resource.create_security_group(GroupName='CronPProjectSG', Description='only allow SSH traffic',  VpcId=vpc.id)
#create a secuirty group That only allows ssh traffic
sec_group.authorize_ingress(CidrIp='0.0.0.0/0', IpProtocol='tcp', FromPort=22, ToPort=22)
#authorize the ssh traffic
key_name = 'cron_keyy'
#save the key name
create_key = ec2_client.create_key_pair(KeyName = key_name, KeyType = 'rsa')
#create an rsa key file
key_file = open(str(Path.cwd()/ f'{key_name}.pem'),'w')
#open a file for the key on ur local drive
key_file.write(create_key['KeyMaterial'])
#write the created key to the file
key_file.close()
#save the file

user_data_script_depend = '''#!/bin/bash
cd /root/
sudo DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y
sudo apt install needrestart
sudo sed -i 's/#$nrconf{restart} = '"'"'i'"'"';/$nrconf{restart} = '"'"'a'"'"';/g' /etc/needrestart/needrestart.conf
sudo apt install zip -y
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip 
sudo ./aws/install
aws --profile default configure set aws_access_key_id "|ACCESS|"
aws --profile default configure set aws_secret_access_key "|SECRET|"
aws --profile default configure set region "us-east-1"
sudo apt-get install software-properties-common
sudo apt-add-repository universe
sudo apt-get update
sudo apt-get install python3-pip -y
pip3 install boto3
sudo apt-get install cron -y
aws s3 cp s3://temp-instance-bucket/start.py /root/start.py
mkdir start
(crontab -l ; echo "0 */1 * * * python3 /root/start.py >> /root/start/start.logs") | sort - | uniq - | crontab -
(crontab -l ; echo "*/5 * * * * sh /root/start.sh >> /root/start/sh.logs") | sort - | uniq - | crontab -
'''
#user data scrript that  installs, aws cli, pip, boto3, crontab and then adds two cron schedules to the instance
#start.py check s3 to see if any pipelines have not yet depoloyed, if there is on that has not yet been deployed,
#it will create a folder and move the code from 3 to the instance and create a start.sh file
#the start.sh file creates a cron schedule for the on the ec2 for the pipeline
cron_auto = '''
import boto3
import json
import os
import time
from pathlib import Path
s3_client = boto3.client('s3',aws_access_key_id='|ACCESS|',
aws_secret_access_key='|SECRET|',region_name = 'us-east-1')
response = s3_client.list_objects_v2(Bucket = '|CODE|')
all = response['Contents']
latest = max(all, key=lambda x: x['LastModified'])['Key']
script_name = latest.split('/')[0]
latest= f"""#!/bin/bash
mkdir {script_name}
cd {script_name}
aws s3 cp s3://|CODE|/{script_name}/{script_name}_user_data.sh /root/{script_name}/{script_name}_user_data.sh
aws s3 cp s3://|CODE|/{script_name}/{script_name}_crontab.py /root/{script_name}/{script_name}_crontab.py
(crontab -l ; echo "0 6 * * * /root/{script_name}/python3 /root/{script_name}/{script_name}_crontab.py >> /root/{script_name}/{script_name}_crontab.log") | sort - | uniq - | crontab -
"""
file = open(str(Path.cwd() / 'start.sh' ),'w')
file.write(latest)
file.close()
time.sleep(120)
os.remove(str(Path.cwd() / 'start.sh' ))
'''
user_data_script_depend = user_data_script_depend.replace('|ACCESS|',access)
user_data_script_depend = user_data_script_depend.replace('|SECRET|',secret)
cron_auto = cron_auto.replace('|ACCESS|',access)
cron_auto = cron_auto.replace('|SECRET|',secret)
cron_auto = cron_auto.replace('|CODE|',s3_dict['code'])
#replace all keys and buckets with the keys and buckets that were created earler.

init = open(str(Path.cwd()) + '\\init.py', 'w')
#make a file for the start.py script
init.write(cron_auto)
#write the code to the file
init.close()
#save the file
temp_bucket = 'temp-instance-bucket'
#create bucket so we can stream line docker containers
temp_obj = s3_resource.create_bucket(Bucket = temp_bucket )
s3_resource.create_bucket(Bucket = temp_bucket )
#create the bucket
s3_client.put_public_access_block(Bucket = live_instance_bucket ,PublicAccessBlockConfiguration={"BlockPublicAcls":True ,
"IgnorePublicAcls": True,"BlockPublicPolicy":True,"RestrictPublicBuckets":True})
s3_resource.meta.client.upload_file(str(Path.cwd()) + '\\init.py',
temp_bucket ,'start.py')
#upload the cronauto /start.py script to s3 so when we create the home instance where the pipelines are ran from
#it grab the code from s3

instances = ec2_resource.create_instances(
    ImageId="ami-052efd3df9dad4825", InstanceType='t2.micro', MaxCount=1, MinCount=1, KeyName=key_name,UserData = user_data_script_depend,
    IamInstanceProfile = {'Name': instance_profile_name },
    NetworkInterfaces=[{'SubnetId': subnet.id, 'DeviceIndex': 0, 'AssociatePublicIpAddress': True, 'Groups': [sec_group.group_id]}])
#create the home_instance where the pipelines will get ran from

ec2_dict = {'netwok': {'SubnetId': subnet.id, 'DeviceIndex': 0, 'AssociatePublicIpAddress': True, 'Groups': [sec_group.group_id]},
            'home': instances[0].id, 'key': key_name,'instanceP': instance_profile_name}
#make a ec2 dict that will be used for output


time.sleep(600)

b ='temp-instance-bucket'
s3_resource.Bucket(b).objects.all().delete()
s3_resource.Bucket(b).delete()


ec2_path = base_path + '\\ec2'
Path(ec2_path).mkdir(exist_ok = True,parents =True) 
ec2_output = open(ec2_path + '\\ec2.json','w')
ec2_output.write(json.dumps(ec2_dict))
ec2_output.close()
