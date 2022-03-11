import base64

import json


from flask import Flask, request, render_template, redirect, url_for
import boto3

app = Flask(__name__)



@app.route('/', methods=['POST'])
def upload_image_to_sqs():
    # invoke the s3 bucket and sqs service using boto3 client
    sqs_queue_client = boto3.client('sqs', region_name='us-east-1')
    if request.method=="POST":
        for one_file in request.files.getlist('file'):
            # reference for conversion taken from https://www.geeksforgeeks.org/python-convert-image-to-string-and-vice-versa/
            converted_string = base64.b64encode(one_file.read()).decode('utf-8')
            if one_file.filename != "":
                dic = {one_file.filename: converted_string}
                #message=json.dumps(dic)
                #message = {"key": "value"}
                response = sqs_queue_client.send_message(
                    QueueUrl="https://sqs.us-east-1.amazonaws.com/229504196507/aws-sqs-g19",
                    MessageBody=json.dumps(dic)
                )
    return redirect(url_for('get_result'))

@app.route('/', methods=['GET'])
def get_result():
    sqs = boto3.resource('sqs',
                         region_name='us-east-1'
                         )
    response_queue_name = '' #response queue name
    aws_response_sqs_g19 = sqs.get_queue_by_name(QueueName=response_queue_name)
    all_messages=[]
    while 1:
        temp_mem_del_msg = []
        for msg in aws_response_sqs_g19.receive_messages(MaxNumberOfMessages=10):
            # take only body of the message from the dictionary using json loads
            body = json.loads(msg.body)
            # add each of the messages into a temp list
            all_messages.append(body)
            # keep track of each message id and its receipt handle to remove this
            temp_mem_del_msg.append({'Id': msg.message_id, 'ReceiptHandle': msg.receipt_handle})
        # check for the messages in the list
        if len(all_messages) == 0:
            break
        # if any element in list then delete the element from the sqs queue.
        else:
            deleted_message = aws_response_sqs_g19.delete_messages(
                Entries=temp_mem_del_msg)
    print(len(all_messages))
    return render_template('index.html', ans='')


if __name__ == '__main__':
    app.run(debug= True)
