from os import environ
from base64 import b64decode
from boto3 import resource, client


# gets environmental variables
def get_environ_var(key, encrypted=False):
    if not encrypted:
        return environ[key]
    else:
        cipher_text_blob = b64decode(environ[key])
        return client('kms').decrypt(CiphertextBlob=cipher_text_blob)['Plaintext']


# pulls html file from the s3 bucket
def get_file(bucket_name, key):
    s3 = resource('s3')
    bucket = s3.Bucket(bucket_name)
    obj = bucket.Object(key)
    return obj.get()['Body'].read()
