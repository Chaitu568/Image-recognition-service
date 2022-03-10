import base64
import sys
import json


from flask import Flask, request, render_template
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
    return render_template('index.html')

@app.route('/', methods=['GET'])
def get_result():

    pass












if __name__ == '__main__':
    app.run(debug= True)
