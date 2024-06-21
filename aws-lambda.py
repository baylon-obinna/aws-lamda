import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    # Delete snapshots not associated with any volume or attached to a terminated instance
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
    for snapshot in snapshots:
        snapshot_id = snapshot['SnapshotId']
        
        if 'VolumeId' not in snapshot:
            # Delete snapshot not associated with any volume
            ec2.delete_snapshot(SnapshotId=snapshot_id)
            print(f"Deleted snapshot: {snapshot_id}")
        else:
            # Check if the volume's instance is terminated
            volume_id = snapshot['VolumeId']
            instance_id = ec2.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]['Attachments'][0]['InstanceId']
            instance_state = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['State']['Name']
            
            if instance_state == 'terminated':
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                print(f"Deleted snapshot attached to volume {volume_id}, terminated instance.")
    
    # Terminate dormant EC2 instances
    cutoff_time = datetime.now() - timedelta(days=7)
    instances = ec2.describe_instances()['Reservations']
    
    for reservation in instances:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            launch_time = instance['LaunchTime']
            state = instance['State']['Name']
            
            if launch_time < cutoff_time and state == 'stopped':
                ec2.terminate_instances(InstanceIds=[instance_id])
                print(f"Terminated instance: {instance_id}")
    
    return {
        'statusCode': 200,
        'body': 'EBS snapshots, volumes, and dormant EC2 instances cleanup complete'
    }
