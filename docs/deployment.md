# Deployment

Terraform creates a two-AZ VPC, private ECS/RDS/Redis, public TLS ALB, KMS encryption, private versioned S3, SQS/DLQ, ECR, CloudWatch, IAM, and autoscaling. API scales on CPU; workers scale against visible queue depth. Production enables RDS Multi-AZ, deletion protection, longer backups, and S3 Object Lock.

1. Build and scan API/worker images; push immutable SHA tags to ECR.
2. Configure Terraform S3 state/locking, validated ACM certificate, OIDC issuer, DNS, and approved provider secret.
3. `terraform init && terraform plan -out plan.tfplan`; security/operator review the plan.
4. Apply staging, run migrations as a one-off ECS task, then smoke/e2e/security tests.
5. Production GitHub Environment requires approval. GitHub assumes AWS role through OIDC; no long-lived keys.
6. ECS uses rolling deployments and circuit breaker in the final environment overlay. Roll back by restoring the prior task-definition image SHA; database migrations must be expand/contract compatible.

No infrastructure was deployed by this project generation. The checked-in Terraform requires environment-specific review and a remote backend configuration.

## Approximate cost profile

Dominant costs are RDS Multi-AZ/storage/IO, NAT gateways, Fargate worker time, Redis replicas, logs, embeddings, and LLM inference. A lightly used staging environment is commonly hundreds of USD/month; production can be thousands or substantially more. Obtain current AWS/provider calculator estimates using actual region, retention, throughput, and model mix—these are not quoted guarantees.
