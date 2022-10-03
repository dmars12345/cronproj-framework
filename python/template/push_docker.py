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

s3_resource =  boto3.resource('s3',aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-1')
s3_client=  boto3.client('s3',aws_access_key_id=access,
aws_secret_access_key=secret)

script_name = 'test-scriptt'
script_bucket = f'{script_name}-bucket'

scipt_infa_path = base_path + '\\script_infascturcture'
current_infa_path  = scipt_infa_path + f'\\{script_name}'
current_infa_path_image =  current_infa_path + '\\image'
Path(current_infa_path_image).mkdir()
script_path = scipt_infa_path + '\\code'
Path(script_path).mkdir()


script_code = '''print('hi')
'''
script_code = script_code.replace('|ACCESS|',access)
script_code = script_code.replace('|SECRET|',secret)
script_code = script_code.replace('|BUCKET|',script_bucket)

script_file_path = str(script_path) + '\\main.py'
script_file = open(str(script_file_path),'w')
script_file.write(script_code)
script_file.close()
s3_resource.meta.client.upload_file(script_file_path , f"{infa['s3']['code']}",f'{script_name}/main.py')
#upload the python file to s3

Dockerfile_path = str(script_path) + '\\Dockerfile'
Dockerfile_object = open(Dockerfile_path ,'w')
#create a docker file for the script
Dockerfile_script = '''FROM python:3.9
WORKDIR /app
RUN pip3 install boto3
RUN pip3 install pandas
RUN pip3 install requests
RUN pip3 install xmltodict
COPY main.py main.py
CMD ["python",  "main.py"]
'''
Dockerfile_object.write(Dockerfile_script)
Dockerfile_object.close()
s3_resource.meta.client.upload_file(Dockerfile_path ,infa['s3']['code'],f'{script_name}/Dockerfile')
#upload the docker file to s3

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
sudo aa-remove-unknown
sudo apt-get remove docker docker-engine docker.io
sudo apt-get update
sudo apt install docker.io -y
sudo snap install docker
timedatectl set-timezone America/New_York
docker login -u DOCKERUSER -p DOCKERPASS'''
user_data_script_depend = user_data_script_depend.replace('|ACCESS|',access)
user_data_script_depend= user_data_script_depend.replace('|SECRET|',secret)
#create a user data script that our home instance will pass when creating a temporary instance that builds the containers

docker_image = f'{script_name}'
docker_tag = 'lp'
###needs manually flow
create_docker = f'''
aws s3 cp s3://{infa['s3']['code']}/{script_name}/Dockerfile /root/
aws s3 cp s3://{infa['s3']['code']}/{script_name}/main.py /root/
docker build -t {docker_image}:{docker_tag} .
docker run -d {docker_image}:{docker_tag}
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin |AWSID|dkr.ecr.us-east-1.amazonaws.com
docker tag {docker_image}:{docker_tag} {infa['ecr']['Uri']}:{docker_image}
docker push {infa['ecr']['Uri']}:{docker_image}
aws s3 cp s3://{infa['s3']['instance']}/instance.sh /root/
chmod +x instance.sh
sh instance.sh
'''
#create another part the user data script that runs the docker container for the script  and sends to the ECR
image_user_data = user_data_script_depend + create_docker


ec2_client = boto3.resource('ec2',aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-1')
sg = {'vpc':'vpc-006b9173fa9abbb97','id': 'sg-07451250d618ed197'}
image_instance= ec2_client.create_instances(ImageId="ami-052efd3df9dad4825",
                                            NetworkInterfaces = [infa['ec2']['netwok']],
                                            MinCount=1,MaxCount=1,
                                            InstanceType="t2.micro",
                                            UserData = image_user_data ,
                                            KeyName=infa['ec2']['key'],
                                            IamInstanceProfile = {'Name': infa['ec2']['instanceP']},
                                            )

#create the instance and pass the user data sript
instance_id = str(image_instance[0].id)
instance_shell = open(str(script_path)+ '\\instance.sh','w')
instance_shell.write(f'aws ec2 terminate-instances --instance-ids {instance_id}')
instance_shell.close()
s3_resource.meta.client.upload_file(str(script_path)+ '\\instance.sh',
f"{infa['s3']['instance']}" ,'instance.sh')
#uploaded the instance ID to s3 so the userdata scripts knows what instance to terminate.

ecr_client = boto3.client('ecr', aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-1')
images = ecr_client.list_images(repositoryName=infa['ecr']['name'])['imageIds']
import time
bash_commands = []
images = ecr_client.list_images(repositoryName=infa['ecr']['name'])['imageIds']
while time_counter == 0:
    tag_list = []
    print(tag_list)
    for item in images:
        tag_list.append(item['imageTag'])
    print(tag_list)
    images = ecr_client.list_images(repositoryName=infa['ecr']['name'])['imageIds']
    if script_name in tag_list:
        bash_commands.append(f"""
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 515530543057.dkr.ecr.us-east-1.amazonaws.com
docker pull {infa['ecr']['Uri']}:{script_name}
docker create {infa['ecr']['Uri']}:{script_name}
docker run -d {infa['ecr']['Uri']}:{script_name}
    """)
        time_counter = 1
    else:
        print('sleep')
        time.sleep(60)


#run a while loop that checks the ecr for the docke rimage we just made . once it has been pushed the while loop ends
# the loops creates bash commands that run the image for a user data scrip that runs the pipeline
string_commands = "".join(bash_commands)
#concat the bash_command list with join
container_user_data = user_data_script_depend  + string_commands
### create the user data script that runs the containers on the home instance
user_data = open(str(script_path) + f'\\{script_name}_user_data.sh','w')
user_data.write(container_user_data)
user_data.close()
s3_resource.meta.client.upload_file(str(script_path) + f'\\{script_name}_user_data.sh', f"{infa['s3']['code']}",f'{script_name}/{script_name}_user_data.sh')
#upload to s3
s3_resource = boto3.resource('s3',aws_access_key_id=access,
aws_secret_access_key=secret,region_name = 'us-east-1')
python_cron = open(str(script_path)  + f'\\{script_name}_crontab.py','w')
ud = f'{script_name}/{script_name}_user_data.sh'

python_file = '''import json
from pathlib import Path
import boto3
ec2_client = boto3.resource('ec2',aws_access_key_id='|ACCESS|',
aws_secret_access_key='|SECRET|',region_name = 'us-east-1')
s3_client = boto3.client('s3',aws_access_key_id='|ACCESS|',
aws_secret_access_key='|SECRET|',region_name = 'us-east-1')
s3_resource = boto3.resource('s3',aws_access_key_id='|ACCESS|',
aws_secret_access_key='|SECRET|',region_name = 'us-east-1')
code_bucket = '|CODE|'
obj = s3_client.get_object(Bucket= code_bucket,Key =  USERDATA)
user_data_ec2= obj['Body'].read()
run_image_instance= ec2_client.create_instances(ImageId="ami-052efd3df9dad4825",
NetworkInterfaces = [{'SubnetId': 'subnet-09f141037429d9880','DeviceIndex': 0,'AssociatePublicIpAddress': True,'Groups': ['sg-04236ebf67dca62d1']}],
 MinCount=1,MaxCount=1,InstanceType="t2.micro",UserData = user_data_ec2,KeyName='ssh',IamInstanceProfile = {'Name': 'DeployProjectProfile'})
                                            
instance_id = run_image_instance[0].id
file = open(str(Path.cwd()/ instance_id),'w')
file.close()
s3_resource.meta.client.upload_file(str(Path.cwd()/ instance_id),
'|INSTANCE|',instance_id)'''
#create the python file that runs the pipeline's container on the home instance

python_file = python_file.replace('|ACCESS|',access)
python_file= python_file.replace('|SECRET|',secret)
python_file= python_file.replace('|CODE|',infa['s3']['code'])
python_file= python_file.replace('|INSTANCE|',infa['s3']['instance'])

python_file = python_file.replace("USERDATA",f"'{ud}'")
python_cron.write(python_file)
python_cron.close()
s3_resource.meta.client.upload_file(str(script_path) + f'\\{script_name}_crontab.py', f"{infa['s3']['code']}",f'{script_name}/{script_name}_crontab.py')
#upload to s3



script_image_file = open(current_infa_path_image + '\\image.json','w')
script_image_file.write(json.dumps({'image' :f"{infa['ecr']['Uri']}:{script_name}"}))
script_image_file.close()






