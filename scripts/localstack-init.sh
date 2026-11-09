#!/bin/sh
awslocal sqs create-queue --queue-name creditflow-dlq
DLQ_ARN=$(awslocal sqs get-queue-attributes --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/creditflow-dlq --attribute-names QueueArn --query Attributes.QueueArn --output text)
awslocal sqs create-queue --queue-name creditflow-jobs --attributes "{\"VisibilityTimeout\":\"300\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"5\\\"}\"}"
