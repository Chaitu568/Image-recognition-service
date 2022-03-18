# App Tier

# The following python script runs the app tier functionalities of the project 1.

import base64
import json
import os
import time
import socket
import boto3
from concurrent.futures import ThreadPoolExecutor
import subprocess

awsRegion = "us-east-1"
sqsInputQueueName = "aws-request-sqs-g45"
sqsOutputQueueName = "aws-response-sqs-g45"
s3InputBucketName = "g45-input-bucket"
s3OutputBucketName = "g45-output-bucket"
teammateAccountID = "229504196507"  # Chaitanya's AWS Account ID.
sqsWaitTime = 5  # in seconds. Change to 20 or something more suitable later.
sqsMaxNumberMessages = 1  # Number of messages to read from the queue. Change to 10 or something more suitable later
maxThreadPoolWorkers = 1  # Better to keep it same as sqsMaxNumberMessages.
sleepTime = 5  # in seconds.
instanceTerminationThresholdTime = 1  # in minutes
'''
    Number of idle executions allowed for the instance before terminating.
        SleepTime : 5 seconds
        instanceTerminationThreshold: 4 minutes
'''
ThresholdCount = (instanceTerminationThresholdTime * 60) / sleepTime


# Sleep time is 5 seconds after one execution of processSqsMessages. If that function returns
def createS3Bucket(bucketParams) -> object:
    """

    :param bucketParams:
    :return: bucket
    """
    print("Inside Create S3 function")
    s3 = boto3.resource("s3", region_name=bucketParams["region"])
    bucket = s3.create_bucket(
        Bucket=bucketParams["name"])
    return bucket


def getS3Bucket(bucketParams) -> object:
    """

    :param: bucketParams
    :return: bucket
    """
    s3 = boto3.resource("s3", region_name=bucketParams["region"])
    iterator = s3.buckets.all()
    # Check if the required s3 bucket is already present.
    for bucket in iterator:
        if bucket.name == bucketParams["name"]:
            print(f"found the required bucket -- {bucket.name}")
            return bucket
    bucket = createS3Bucket(bucketParams)
    return bucket


def getSqsQueue(queueParams) -> object:
    """

    :param queueParams:
    :return queue:
    """
    stsClient = boto3.client('sts')
    assumedRole = stsClient.assume_role(
        RoleArn="arn:aws:iam::229504196507:role/SqsAccessToAshishAccount",
        RoleSessionName="AssumeRoleSession1"
    )
    credentials = assumedRole['Credentials']
    sqs = boto3.resource('sqs',
                         aws_access_key_id=credentials['AccessKeyId'],
                         aws_secret_access_key=credentials['SecretAccessKey'],
                         aws_session_token=credentials['SessionToken'],
                         region_name=queueParams["region"])
    queue = sqs.get_queue_by_name(
        QueueName=queueParams["name"],
        QueueOwnerAWSAccountId=queueParams["accountId"]
    )
    print("The url of the fetched SQS queue is: " + queue.url)
    # print("The Supported attributes of this queue are as follows")
    # for value in queue.attributes:
    #     print("The attributes of the queue are: " + value)
    return queue


def runImageClassification(message):
    """

    :param message:
    :return queue:
    """
    # Adding input to the input S3 bucket
    # print(message.body)
    messageBody = json.loads(message.body)
    if message.message_attributes is not None:
        messageRequestId = message.message_attributes.get('RequestId')
    else:
        messageRequestId = ''

    # Processing the image.
    for key, value in messageBody.items():
        imageName = key
        imageInString = value
    image = base64.decodebytes(str.encode(imageInString))
    # image = base64.b64decode(imageInString).encode()
    inputBucketParams = {"name": s3InputBucketName, "region": awsRegion}
    inputBucket = getS3Bucket(inputBucketParams)
    inputBucket.put_object(Body=image, Key=imageName)

    '''
        Saving the received image string to a file and running classification algorithm.
        The results are saved to a dictionary in the the following format.
        {
            'ImageFileName.jpg':'Result',
            'RequestId': 'RequestId cached from input message'
        }
    '''
    workdir = os.getcwd()
    localFileName = os.path.join(workdir, imageName)
    print(localFileName)
    if not os.path.exists(localFileName):
        with open(localFileName, "wb") as file:
            file.write(image)
            file.close()
    # Deleting the message on sqs as it is read properly.
    message.delete()
    print("Message " + str(imageName))

    result = subprocess.run(['python3', 'face_recognition.py', localFileName], capture_output=True). \
        stdout.decode().strip()
    # dictResult = {imageName: result, 'RequestId': messageRequestId}
    dictResult = {imageName: result}

    # Saving the output to the output S3 bucket
    outputBucketParams = {"name": s3OutputBucketName, "region": awsRegion}
    outputBucket = getS3Bucket(outputBucketParams)
    imageNameWithoutExt = os.path.splitext(imageName)[0]
    outputBucket.put_object(Body=result, Key=imageNameWithoutExt)

    # Deleting the local file to save space.
    if os.path.exists(localFileName):
        os.remove(localFileName)

    # Deleting the message on sqs as it is read properly.
    message.delete()
    return dictResult


def processSqsMessages():
    """
    Receives the messages from the sqs queue and spawns them into worker threads to process it.
    """
    inputQueueParams = {"name": sqsInputQueueName, "accountId": teammateAccountID, "region": awsRegion}
    inputQueue = getSqsQueue(inputQueueParams)
    print("Getting messages from SQS queue...")
    messages = inputQueue.receive_messages(MessageAttributeNames=['RequestId'],
                                           WaitTimeSeconds=sqsWaitTime,
                                           MaxNumberOfMessages=sqsMaxNumberMessages)
    if messages:
        idle = False
        print("Entering non-null block")
        # Distributing the recognition tasks to multiple workers.
        with ThreadPoolExecutor(max_workers=maxThreadPoolWorkers) as executor:
            classificationResults = executor.map(runImageClassification, messages)

        # Sending the results back to the output/response Sqs queue.
        outputQueueParams = {"name": sqsOutputQueueName, "accountId": teammateAccountID, "region": awsRegion}
        outputQueue = getSqsQueue(outputQueueParams)
        for result in classificationResults:
            print(result)
            outputQueue.send_message(MessageBody=str(result))
            # , MessageAttributes = {
            #     'RequestId': result['RequestId']  # Need to add a request ID in the web tier.
            # }
    else:
        print("The messages received is null, exiting.....")
        idle = True
    result = {"IsInstanceIdle": idle}
    return result


def stopCurrentInstance():
    """
        Stops the current running instance using its private DNS name.
    """
    ec2 = boto3.resource("ec2", region_name=awsRegion)
    # Trying to get the private DNS name of this Ec2 instance.
    # NOTE: Only works when deployed on ec2.
    instanceHostName = socket.gethostname()
    fetchInstanceApiParams = [{'Name': 'private-dns-name', 'Values': [instanceHostName]}]
    print("Stopping this ec2 instance as it is dormant for the past " +
          str(instanceTerminationThresholdTime) + " minutes")
    ec2.instances.filter(Filters=fetchInstanceApiParams).stop()


def main():
    """
    Main function that processes the incoming SQS messages in a loop periodically.
    Also incorporates to auto-scale down the app tier when demand is low.

    :parameter: None
    :return: None
    """
    exiting = False
    instanceIdleCount = 0
    while not exiting:
        print("Current instanceIdleCount is: " + str(instanceIdleCount))
        result = processSqsMessages()
        if result["IsInstanceIdle"]:
            instanceIdleCount = instanceIdleCount + 1
            if instanceIdleCount < ThresholdCount:
                time.sleep(5)  # Sleep for 5 seconds and process the Sqs messages again.
            else:
                # The instance has been idle since the 'instanceTerminationThresholdTime' minutes.
                stopCurrentInstance()
                exiting = True


if __name__ == '__main__':
    main()
