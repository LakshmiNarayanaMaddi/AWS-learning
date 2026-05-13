import boto3
import time

REGION = boto3.Session().region_name
ec2 = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)

KEY_NAME = 'boto3-auto-key'
SG_NAME = 'boto3-auto-sg'

print(f"Using Region: {REGION}")

# 1. Create Key Pair
def create_key_pair():
    try:
        response = ec2.create_key_pair(KeyName=KEY_NAME)
        with open(f"{KEY_NAME}.pem", "w") as file:
            file.write(response['KeyMaterial'])
        print(f"Key Pair created: {KEY_NAME}.pem")
    except ec2.exceptions.ClientError:
        print("Key pair already exists")

# 2. Get default VPC
def get_default_vpc():
    vpcs = ec2.describe_vpcs(
        Filters=[{'Name': 'isDefault', 'Values': ['true']}]
    )
    return vpcs['Vpcs'][0]['VpcId']

# 3. Create Security Group
def create_security_group(vpc_id):
    try:
        response = ec2.create_security_group(
            GroupName=SG_NAME,
            Description='Boto3 auto SG',
            VpcId=vpc_id
        )
        sg_id = response['GroupId']

        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        print(f"Security Group created: {sg_id}")
        return sg_id
    except ec2.exceptions.ClientError:
        print("Security group already exists")
        sgs = ec2.describe_security_groups(
            Filters=[{'Name': 'group-name', 'Values': [SG_NAME]}]
        )
        return sgs['SecurityGroups'][0]['GroupId']

# 4. Get latest Amazon Linux AMI
def get_latest_ami():
    images = ec2.describe_images(
        Owners=['amazon'],
        Filters=[{'Name': 'name', 'Values': ['al2023-ami-*']}]
    )
    images_sorted = sorted(images['Images'], key=lambda x: x['CreationDate'], reverse=True)
    return images_sorted[0]['ImageId']

# 5. Launch EC2
def launch_instance(ami_id, sg_id, subnet_id):
    response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t3.micro',
        KeyName=KEY_NAME,
        MinCount=1,
        MaxCount=1,
        SecurityGroupIds=[sg_id],
        SubnetId=subnet_id,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': 'Boto3AutoEC2'}]
            }
        ]
    )
    return response['Instances'][0]['InstanceId']

# MAIN
create_key_pair()
vpc_id = get_default_vpc()

subnets = ec2.describe_subnets(
    Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
)
subnet_id = subnets['Subnets'][0]['SubnetId']

sg_id = create_security_group(vpc_id)
ami_id = get_latest_ami()

print(f"AMI: {ami_id}")
instance_id = launch_instance(ami_id, sg_id, subnet_id)

print(f"Instance launching: {instance_id}")
instance = ec2_resource.Instance(instance_id)

print("Waiting for instance to run...")
instance.wait_until_running()
instance.reload()

print("EC2 Ready!")
print("Public IP:", instance.public_ip_address)