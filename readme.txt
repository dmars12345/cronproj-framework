Problem:

Imagine an application that needs data to be refreshed every single day. Setting up the cloud infrastructure can be tedious,
costly and difficult to manage.
The cronproj framework solves this problem by automating the process of deploying infrastructure on aws for 
code that is written in python. Once you have the python code written and functioning, 
all you need to do is pass in your root credentials into the "root.json" file and create a template for each script and define your cron schedules.

the framework is broken down into two parts. base infrastructure (the cronproj folder) and then script infrastructure (this part is variable).

file tree:

| root.json
|---> ec2\ ---> ec2.json
|---> ecr\ ---> ecr_policy.json
|---> ecr\ ---> ecr.json
|---> iam\ ---> inline_policies\ ---> ecr_resource_access.json
|---> iam\ ---> inline_policies\ ---> run_instance.json
|---> iam\ ---> inline_policies\ ---> s3_resource.json
|---> iam\ ---> policies\ ---> arn.json
|---> iam\ ---> role\ ---> ec2_trust_policy.json
|---> iam\ ---> role\ ---> role_policies.json
|---> iam\ ---> iam.json
|---> iam\ ---> creds.json
|---> s3\ ---> s3.json
#### there will be a folder for each script inside of script_infasctructure 
|---> script_infrastructure\ ---> test-scriptt ---> image ---> image.json
|---> script_infrastructure\ ---> test-scriptt ---> lambda ---> lambda.json
|---> script_infrastructure\ ---> test-scriptt ---> s3 ---> bucket.json


High Level Overview:

step one: create an iam user and assigns policies to that user that you define.
step two: create a role and assigns policies to that role that you define and also creates an instance profile from that role.
step three: create code bucket where which enables code to be collected easily throughout aws.
step four: create an instance bucket that allows temporary instances to be terminated.
step five: create an ecr
step six: create a security group that only allows ssh traffic.
step seven: create a home instance where all cronjobs are set and ran from.
step eight: create a name for your script template and paste the code into the python file and run the tempalte,
this will automatically deploy the cloud infrastructure and set up the cronjob on the home instance.


Python File Overview:

Base --------------------------------------------------------------------------------------------------------

iam.py:

define the name of the user in the user variable, create json files in the inline_policies folder and create
a dictionary in the arn file of all the AWS managed policies you would like the user to have.
The code will create the iam user, create and store the access and secret keys and will assign and create all the policies you define.
next create the name of the role, and in the role_policies.json file, create a dictionary with the ARN of all the policies that you want attached to that role.
next create the name of the instance profile and the code will attach the role and its policies to the new 
instance profile.
The code will then store the user credentials and the names of the role and instance_profile in a json file.

s3.py:

define the name of the code bucket.
the code bucket is used for whenever a new script is added all of the necessary file get sent to this bucket under the prefix of the name of script. this enables cron schedules to be automated.
define the name of the instance bucket.
whenever its time to run a docker container on the home instance the python code will send the id of the instance to this bucket. When the data get placed into the script data bucket, the lambda function will
terminate the temporary instance.
the code will store the names of this buckets in a json file.

ecr.py:

create a ecr repo for all docker images to be pulled from on the temp instance.
the code will store the name of the ecr in a json file.

ec2.py: 
this python file creates the home instance where all the temp instances and cron schedules get created from.
The file creates a security group and an instance.
The instance has a user data script that installs boto3 ,crontab and awscli and authenticates with the user we created in the iam.py file.

template  --------------------------------------------------------------------------------------

s3.py:

create a s3 bucket and makes the object not public, your python script must put objects in this bucket.

push_docker.py:
copy and paste the python code into the  script_code variable and copy the ur docker file into the 
dockerfile_script variable. 
The code will create an ec2 instance that creates the docker image and pushes it to the ecr we made in the base
infrastructure code and then it gets terminated.
the code then also pushes the python_file variable to s3.
The python_file is the code that get executed on the home ec2_instance. The code creates a temporary ec2_instance with 
a user data script that pulls the image out of the ecr and runs the container.


lambda.py:

the final piece is the lambda function. The lambda function terminates the instance the python_file code creates.
The function is evoked when a put gets made in the scripts bucket. In order for this to work, the code 
adds a LambdaFunctionConfiguration to the s3 bucket. This makes saves costs because it terminates the instance
as soon as the container dumps the data into s3.
