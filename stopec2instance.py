import boto3

REGION = boto3.Session().region_name
ec2 = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)

TAG_KEY = 'Name'
TAG_VALUE = 'Boto3AutoEC2'


def get_instance_by_tag():
    response = ec2.describe_instances(
        Filters=[
            {'Name': f'tag:{TAG_KEY}', 'Values': [TAG_VALUE]},
            {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
        ]
    )

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            return instance['InstanceId']

    return None


def stop_instance(instance_id):
    instance = ec2_resource.Instance(instance_id)
    state = instance.state['Name']

    print(f"Instance {instance_id} current state: {state}")

    if state == 'running':
        print("Stopping instance...")
        instance.stop()
        instance.wait_until_stopped()
        print("Instance stopped successfully.")
    elif state == 'stopped':
        print("Instance is already stopped.")
    else:
        print(f"Instance is in '{state}' state. Try again later.")


if __name__ == "__main__":
    instance_id = get_instance_by_tag()

    if not instance_id:
        print("No instance found with tag Name=Boto3AutoEC2")
    else:
        stop_instance(instance_id)