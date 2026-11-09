output "alb_dns_name" {
  value = aws_lb.api.dns_name
}

output "api_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "worker_repository_url" {
  value = aws_ecr_repository.worker.repository_url
}

output "queue_url" {
  value = aws_sqs_queue.jobs.url
}

output "documents_bucket" {
  value = aws_s3_bucket.documents.id
}

