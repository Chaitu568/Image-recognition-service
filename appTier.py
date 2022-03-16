# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


import boto3

awsRegion = "us-east-1"
# sqsInputQueueUrl = "https://sqs.us-east-1.amazonaws.com/229504196507/aws-sqs-g19"
sqsInputQueueName = "aws-sqs-g19"
s3InputBucketName = "g45-input-bucket"
s3InputBucketName = "g45-output-bucket"
TeammateAccountID = "229504196507" # Chaitanaya's AWS Account ID.


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


def getSqsQueue(queueParams):
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
    print("The Supported attributes of this queue are as follows")
    for value in queue.attributes:
        print("The attributes of the queue are: " + value)  # + " and type of this is: " + str(type(value))
    return queue


def processSqsMessages():
    inputQueueParams = {"name": sqsInputQueueName, "accountId": TeammateAccountID, "region": awsRegion}
    intputQueue = getSqsQueue(inputQueueParams)
    print("Getting messages from SQS queue...")
    workDir = "classifier"


# def getLenOfQueue(sqs_g19, sqsUrl_g19):
#     response = sqs_g19.get_queue_attributes(QueueUrl=sqsUrl_g19, AttributeNames=['ApproximateNumberOfMessages', ])
#     print(response, "Response")
#     response = int(response['Attributes']['ApproximateNumberOfMessages'])
#     return response




# def processImagesfromSQS():
#   s3 = boto.s3.connect_to_region(awsRegion)
#   sqs = boto.sqs.connect_to_region(awsRegion)
#   sqsQueue =  sqs.lookup(sqsQueueName)
#   print("Getting messages from SQS queue...")
#   messages = sqsQueue.get_messages(wait_time_seconds=20)
#   workDir = "classifier"
#   if messages:
#       for m in messages:
#           job = json.loads(m.get_body())
#           m.delete()
#           action = job[0]
#           if action == 'process':
#               s3BucketName = job[1]
#               s3Inputfolder = job[2]
#               s3OutputFolder = job[3]
#               fileName = job[4]
#               status = processImageandSavetoS3(s3, s3BucketName, s3Inputfolder, s3OutputFolder, fileName, workDir)
#               if (status):
#                   print("Message processed correctly ...")
#   else:
#       print("No Messages")
#
#
# def processImageandSavetoS3(s3, s3BucketName, s3Inputfolder, s3OutputFolder, fileName, workDir):
#     file_type = fileName.split(".")[1]
#     k=4
#     if(file_type=="jpeg" or file_type=="JPEG"):
#         k=5
#     elif (file_type == "png" or file_type=="PNG"):
#         k=4
#     s3BucketInput = s3.get_bucket(s3BucketName+"-"+s3Inputfolder)
#     s3BucketOutput = s3.get_bucket(s3BucketName+"-"+s3OutputFolder)
#     downloadInputPath = os.path.join(workDir, fileName)
#     downloadOutputPath =  os.path.join(workDir, fileName[:-k]+'.txt')
#     remoteInputPath = fileName
#     remoteOutputPath =  fileName[:-k]+'.txt'
#     if not os.path.isdir(workDir):
#         os.system('sudo mkdir work && sudo chmod 777 work')
#     key = s3BucketInput.get_key(remoteInputPath)
#     s3 = boto3.client('s3')
#     s3.download_file(s3BucketName+"-"+"inputfolder", remoteInputPath, downloadInputPath)
#     key.get_contents_to_filename(workDir+"/"+fileName)
#     os.system('python3 classifier/image_classification.py '+downloadInputPath+' > '+downloadOutputPath)
#     with open(downloadOutputPath) as f:
#         content = f.readlines()
#     with open(downloadOutputPath, "w") as f:
#         f.write(str(remoteInputPath)+":"+content[0])
#     key = Key(s3BucketOutput)
#     key.key = remoteOutputPath
#     key.set_contents_from_filename(downloadOutputPath)
#     return True

def main():
    inputBucketParams = {"name": s3InputBucketName, "region": awsRegion}
    inputQueueParams = {"name": sqsInputQueueName, "accountId": TeammateAccountID, "region": awsRegion}
    inputBucket = getS3Bucket(inputBucketParams)
    intputQueue = getSqsQueue(inputQueueParams)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # createS3Bucket(bucketParams)
    main()
