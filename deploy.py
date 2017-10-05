import boto3
import pip
import shutil

iam = boto3.client("iam")
s3 = boto3.resource('s3')

def create_role(role_name):
    try:
        role = iam.get_role(RoleName = role_name)
        return role["Role"]["Arn"]
    except iam.exceptions.NoSuchEntityException:
        with open("assumeRolePolicyDocument.json", "r") as policy_file:
            policy = policy_file.read()
            role = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=policy)
            return role["Role"]["Arn"]

def put_role_policy(role_name, policy_name, policy_file_name):
    with open(policy_file_name, "r") as policyFile:
        policyContent = policyFile.read()
        iam.put_role_policy(RoleName=role_name, PolicyName=policy_name, PolicyDocument=policyContent)

def create_package(package_name):
    pip.main(["install", "-r", "requirements.txt", "-t", "."])
    shutil.make_archive(package_name, 'zip', ".")

def upload_to_s3(source, bucket, key):
    s3.meta.client.upload_file(Filename=source, Bucket=bucket, Key=key)


if __name__ == '__main__':
    roleName = "daily-tee-notifier-lambda-role"
    roleArn = create_role(role_name= roleName)
    put_role_policy(roleName, "s3", "s3PolicyFile.json")
    put_role_policy(roleName, "log", "logPolicyFile.json")
    create_package("daily-tee-notifier")
    upload_to_s3("daily-tee-notifier.zip", "daily-tee-finder-deployment", "daily-tee-notifier.zip")