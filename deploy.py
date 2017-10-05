import boto3

client = boto3.client("iam")

def createRole(roleName):
    try:
        role = client.get_role(RoleName = roleName)
        return role["Role"]["Arn"]
    except client.exceptions.NoSuchEntityException:
        with open("assumeRolePolicyDocument.json", "r") as policy_file:
            policy = policy_file.read()
            role = client.create_role(RoleName=roleName, AssumeRolePolicyDocument=policy)
            return role["Role"]["Arn"]

def putRolePolicy(roleName, policyName, policyFileName):
    with open(policyFileName, "r") as policyFile:
        policyContent = policyFile.read()
        client.put_role_policy(RoleName=roleName, PolicyName=policyName, PolicyDocument=policyContent)


if __name__ == '__main__':
    roleName = "daily-tee-notifier-lambda-role"
    roleArn = createRole(roleName = roleName)
    putRolePolicy(roleName, "s3", "s3PolicyFile.json")
    putRolePolicy(roleName, "log", "logPolicyFile.json")