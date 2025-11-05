import boto3

# s3_client = boto3.client(
#     's3',
#     endpoint_url="https://s3.cloud-ai.ir",
#     aws_access_key_id='OAF0MC26UA7DV9WS11X5',
#     aws_secret_access_key='6SY2dTxhcIVEsjbfpjRUBhe3k7mMJIjZpccwvw3d',
#     config=Config(signature_version='s3v4')
# )
# response = s3_client.list_objects_v2(Bucket='mlops', Prefix='Datasets/zai-org-CC-Bench-trajectories/')
# print(response.get('Contents', []))


def list_s3_files(s3_client, bucket, prefix):
    files = []
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            files.append(f"s3://{bucket}/{obj['Key']}")
    return files

s3_client = boto3.client(
    's3',
    endpoint_url='https://s3.cloud-ai.ir',
    aws_access_key_id="OAF0MC26UA7DV9WS11X5",
    aws_secret_access_key="6SY2dTxhcIVEsjbfpjRUBhe3k7mMJIjZpccwvw3d"
)
files = list_s3_files(s3_client, 'mlops', 'Datasets/zai-org-CC-Bench-trajectories/')


list(map(lambda file: print(file), files))