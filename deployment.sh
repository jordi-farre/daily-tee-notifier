#!/bin/bash

configure() {
	aws configure set default.region us-east-1
	aws configure set output json
}

ROLE_ARN="none"
createRole() {
    aws iam create-role --role-name ${ROLE_NAME} --assume-role-policy-document file://assumeRolePolicyDocument.json
    aws iam put-role-policy --role-name ${ROLE_NAME} --policy-name s3 --policy-document file://s3PolicyFile.json
    aws iam put-role-policy --role-name ${ROLE_NAME} --policy-name logs --policy-document file://logPolicyFile.json
    ROLE_ARN=$(aws iam get-role --role-name ${ROLE_NAME} | jq -r '.Role.Arn')
    echo "Role $ROLE_NAME created with arn $ROLE_ARN"
}

uploadArtifactS3() {
    mv target/${FILE_NAME} ${RELEASE_NAME}
	aws s3 cp ${RELEASE_NAME} s3://${S3_BUCKET}/
    echo "File $RELEASE_NAME copied to $S3_BUCKET bucket"
}

createFunction() {
    FUNCTION_VERSION=$(aws lambda create-function --region us-east-1 --function-name $FUNCTION_NAME --code S3Bucket=${S3_BUCKET},S3Key=${RELEASE_NAME} --role ${ROLE_ARN} --handler tee.finder.qwertee.Application::handleRequest --runtime java8 --timeout 30 --memory-size 256 --environment Variables={QWERTEE_URL=https://www.qwertee.com/rss,S3_BUCKET=site-tees-production} --publish | jq -r '.Version')
    echo "Function $FUNCTION_NAME created with version $FUNCTION_VERSION"
    FUNCTION_ERROR=$(aws lambda invoke --function-name $FUNCTION_NAME /dev/null | jq -r ".FunctionError")
    echo "Function $FUNCTION_NAME executed with error $FUNCTION_ERROR"
    if [ "$FUNCTION_ERROR" = null ]; then
        aws lambda create-alias --function-name $FUNCTION_NAME --name PRODUCTION --function-version $FUNCTION_VERSION
        echo "Alias PRODUCTION created for $FUNCTION_NAME with version $FUNCTION_VERSION"
    else
        exit 1
    fi
}

updateFunction() {
    aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment Variables={QWERTEE_URL=https://www.qwertee.com/rss,S3_BUCKET=site-tees-production}
    aws lambda update-function-code --function-name $FUNCTION_NAME --s3-bucket ${S3_BUCKET} --s3-key ${RELEASE_NAME}
    FUNCTION_VERSION=$(aws lambda publish-version --function-name $FUNCTION_NAME | jq -r '.Version')
    echo "Function $FUNCTION_NAME updated with version $FUNCTION_VERSION"
    FUNCTION_ERROR=$(aws lambda invoke --function-name $FUNCTION_NAME /dev/null | jq -r ".FunctionError")
    echo "Function $FUNCTION_NAME executed with error $FUNCTION_ERROR"
    if [ "$FUNCTION_ERROR" = null ]; then
        aws lambda update-alias --function-name $FUNCTION_NAME --name PRODUCTION --function-version $FUNCTION_VERSION
        echo "Alias PRODUCTION updated for $FUNCTION_NAME with version $FUNCTION_VERSION"
    else
        exit 1
    fi
}

createLambdaFunction() {
	if aws lambda get-function --function-name ${FUNCTION_NAME} --query 'Configuration.FunctionName'
	then
        updateFunction
	else
        createFunction
	fi
}

createEvent() {
    RULE_ARN=$(aws events put-rule --name every_hour --schedule-expression "cron(0 0/1 * * ? *)" | jq -r '.RuleArn')
    echo "Created/updated rule $RULE_ARN"
    aws lambda add-permission --function-name ${FUNCTION_NAME}:PRODUCTION --statement-id $FUNCTION_NAME --action 'lambda:InvokeFunction' --principal events.amazonaws.com --source-arn $RULE_ARN
    FUNCTION_ARN=$(aws lambda get-alias --function-name $FUNCTION_NAME --name PRODUCTION | jq -r '.AliasArn')
    echo "Adding event to function $FUNCTION_ARN"
    aws events put-targets --rule every_hour --targets "Id"="1","Arn"="$FUNCTION_ARN"
}

ROLE_NAME="daily-tee-notifier-lambda-role"
FILE_NAME="daily-tee-notifier-1.0-SNAPSHOT.jar"
RELEASE_NAME="daily-tee-notifier-${CIRCLE_BUILD_NUM}.jar"
FUNCTION_NAME="daily-tee-notifier"
S3_BUCKET="daily-tee-finder-deployment"
configure
createRole
uploadArtifactS3
rm ${FILE_NAME}
createLambdaFunction
# createEvent
