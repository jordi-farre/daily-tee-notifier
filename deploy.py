import boto3
import pip
import shutil

iamClient = boto3.client("iam")
s3Client = boto3.resource('s3')
lambdaClient = boto3.client('lambda', region_name="us-east-1")
roleName = "daily-tee-notifier-lambda-role"
package = "daily-tee-notifier"
packageZip = package + ".zip"
bucket = "daily-tee-finder-deployment"

def create_role(role_name):
    try:
        role = iamClient.get_role(RoleName = role_name)
        return role["Role"]["Arn"]
    except iamClient.exceptions.NoSuchEntityException:
        with open("assumeRolePolicyDocument.json", "r") as policy_file:
            policy = policy_file.read()
            role = iamClient.create_role(RoleName=role_name, AssumeRolePolicyDocument=policy)
            return role["Role"]["Arn"]

def put_role_policy(role_name, policy_name, policy_file_name):
    with open(policy_file_name, "r") as policyFile:
        policyContent = policyFile.read()
        iamClient.put_role_policy(RoleName=role_name, PolicyName=policy_name, PolicyDocument=policyContent)

def create_package(package_name):
    pip.main(["install", "-r", "requirements.txt", "-t", "."])
    shutil.make_archive(package_name, 'zip', ".")

def upload_to_s3(source, bucket, key):
    s3Client.meta.client.upload_file(Filename=source, Bucket=bucket, Key=key)

def createOrUpdateFunction(function_name, role_arn, s3_bucket, s3_key):
    try:
        function = lambdaClient.get_function(FunctionName=function_name)
        updateFunction(function=function)
        return function
    except lambdaClient.exceptions.ResourceNotFoundException:
        return createFunction(function_name=function_name, role_arn=role_arn, s3_bucket=s3_bucket, s3_key=s3_key)

def createFunction(function_name, role_arn, s3_bucket, s3_key):
    return lambdaClient.create_function(
        FunctionName=function_name,
        Runtime='python3.6',
        Role=role_arn,
        Handler="handler.handle",
        Code={"S3Bucket":s3_bucket, "S3Key":s3_key},
        Publish=True
    )

def updateFunction(function):
    return

if __name__ == '__main__':
    roleArn = create_role(role_name= roleName)
    put_role_policy(roleName, "s3", "s3PolicyFile.json")
    put_role_policy(roleName, "log", "logPolicyFile.json")
    create_package(package)
    upload_to_s3(packageZip, bucket, packageZip)
    createOrUpdateFunction(function_name=package, role_arn=roleArn, s3_bucket=bucket, s3_key=packageZip)