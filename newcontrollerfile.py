import boto3
import time




MASTER_ID=""

def NumOfRunningInstances(ec2):
    numOfrunningInstances = 0
    for each_inst in ec2.instances.all():
        if (each_inst.state['Name'] == 'running' or each_inst.state['Name'] == 'pending') and each_inst.id != MASTER_ID:
            numOfrunningInstances += 1
    return numOfrunningInstances

def NumOfStoppedInstances(ec2):
    numOfstoppedInstances = 0
    for each_inst in ec2.instances.all():
        if(each_inst.state['Name'] == 'stopped' or each_inst.state['Name'] == 'stopping') and each_inst.id != MASTER_ID:
            numOfstoppedInstances += 1
    return numOfstoppedInstances

def getRunningInstIDs(ec2):  # getRunningInstances
    run_instances = []
    for each_inst in ec2.instances.all():
        if (each_inst.state['Name'] == 'running' or each_inst.state['Name'] == 'pending') and each_inst.id != MASTER_ID:
            run_instances.append(each_inst.id)
    return run_instances

def getStoppedInstIDs(ec2):  # getStoppedInstances
    stop_instances = []
    for each_inst in ec2.instances.all():
        if (each_inst.state['Name'] == 'stopped' or each_inst.state['Name'] == 'stopping') and each_inst.id != MASTER_ID:
            stop_instances.append(each_inst.id)
    return stop_instances


def startOneInstance():
    new_ec2_client=boto3.client('ec2')
    response = new_ec2_client.run_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {

                    'DeleteOnTermination': True,
                    'VolumeSize': 8,
                    'VolumeType': 'gp2'
                }, },
        ],
        ImageId='',  # ami instance
        InstanceType='t2.micro',
        KeyName='',  # key file name
        MaxCount=1,
        MinCount=1,
        Monitoring={
            'Enabled': False
        },
        SecurityGroupIds=[
            # securityGroupIds    # remove comments and add new pcp
        ],
    )
    return response

def startReqNumberofInstance(req_ec2_count):
    new_ec2_client = boto3.client('ec2')
    for i in req_ec2_count:
        response=startOneInstance()
        instance = response["Instances"][0]
        try:
            new_ec2_client.create_tags(Resources=[instance["InstanceId"]],
                               Tags=[{'Key': 'Name', 'Value': 'app_tier ' + str(i)}])
        except:
            print("tags cannot be created that means that insctance might have been terminated...")
        print(response)








def main():
    sqs_g_45 = boto3.client('sqs')
    sqsUrl_g45 = ''

    ec2_g45 = boto3.resource('ec2',region_name='us-east-1')
    max_limit_instances = 19
    runningInstances = NumOfRunningInstances(ec2_g45)
    stoppedInstances = NumOfStoppedInstances(ec2_g45)

    while True:
        response_sqs_g45 = sqs_g_45.get_queue_attributes(QueueUrl=sqsUrl_g45,
                                                         AttributeNames=['ApproximateNumberOfMessages', ])
        response_queue_len = int(response_sqs_g45['Attributes']['ApproximateNumberOfMessages'])
        if (runningInstances + stoppedInstances) < 19:
            no_of_inst_to_create = 19 - (runningInstances + stoppedInstances)
            startReqNumberofInstance(no_of_inst_to_create)
        if response_queue_len > runningInstances:
            stopped_ids = getStoppedInstIDs(ec2_g45)  # all the stopped instance IDs are appended here | stoppedIds
            start = min(stoppedInstances, response_queue_len - runningInstances)

            if start != 0:
                ec2_g45.instances.filter(InstanceIds=stopped_ids[:start]).start()  # starting stopped instances
                print("Started " + str(stopped_ids[:start]) + " instances")
                time.sleep(5)


if __name__ == '__main__':
    main()




