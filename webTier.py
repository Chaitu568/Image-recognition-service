import base64

import json


from flask import Flask, request, render_template, redirect, url_for
import boto3

app = Flask(__name__)

def createSqsQueue(queueName):
    sqs = boto3.resource('sqs', region_name = 'us-east-1')
    try:
        Queue_45 = sqs.get_queue_by_name(QueueName = queueName)
        return Queue_45
    except:
        Queue_45 = sqs.create_queue(QueueName = queueName)
        return Queue_45


@app.route('/', methods=['POST', 'GET'])
def upload_image_to_sqs():
    # invoke the s3 bucket and sqs service using boto3 client
    sqs_queue_client = boto3.client('sqs', region_name='us-east-1')
    inputSqsQueue_45 = createSqsQueue('aws-request-sqs-g45')  # input_queue_name
    if request.method == "POST":
        for one_file in request.files.getlist('file'):
            # reference for conversion taken from https://www.geeksforgeeks.org/python-convert-image-to-string-and-vice-versa/
            converted_string = base64.b64encode(one_file.read()).decode('utf-8')
            if one_file.filename != "":
                dic = {one_file.filename: converted_string}
                #message=json.dumps(dic)
                #message = {"key": "value"}
                response = sqs_queue_client.send_message(
                    QueueUrl=inputSqsQueue_45.url,
                    MessageBody=json.dumps(dic)
                )
            if one_file.filename == "":
                return render_template('index.html')
        return redirect(url_for('get_result'))
    else:
        return render_template('index.html')

@app.route('/result', methods=['GET'])
def get_result():
    sqs = boto3.resource('sqs',
                         region_name='us-east-1'
                         )
    responseSqsQueue_45 = createSqsQueue('aws-response-sqs-g45')  # response_queue_name

    all_messages = []
    while True:
        temp_mem_del_msg = []
        for msg in responseSqsQueue_45.receive_messages(MaxNumberOfMessages=10):
            # take only body of the message from the dictionary using json loads
            print(type(msg.body))
            j_string = json.dumps(msg.body)
            print(type(j_string))

            body = json.loads(j_string)
            print(type(body))
            # add each of the messages into a temp list
            all_messages.append(body)
            # keep track of each message id and its receipt handle to remove this
            temp_mem_del_msg.append({'Id': msg.message_id, 'ReceiptHandle': msg.receipt_handle})
            print('hi')
        # check for the messages in the list
        if len(temp_mem_del_msg) == 0:
            break
        # if any element in list then delete the element from the sqs queue.
        else:
            deleted_message = responseSqsQueue_45.delete_messages(
                Entries=temp_mem_del_msg)
    keys = []

    for msgg in all_messages:
        final_message = eval(msgg)
        for key, val in final_message.items():
            keys.append( key + ' - ' + val)

    print(keys)
    return render_template('answers.html', key=keys)


if __name__ == '__main__':
    app.run(debug = True)
