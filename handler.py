def handle(event, context):
    return event['Records'][0]['s3']['bucket']['name']