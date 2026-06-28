#!/usr/bin/env python3
"""
Complex Template Expansion — ~45 complex templates (5-10+ steps each) across all 30 sectors.
Generates 500 records, merges into existing train/val/test splits, and validates.

3 expansion patterns:
  1. Prerequisite-chain: Build foundational pieces first, then layer services on top
  2. Deep pipeline: Long linear pipelines with nested dependencies
  3. Multi-level rollback: Every major write action has a compensating rollback

Usage:
    python3 complex_template_expansion.py
"""

import sys, json, os, random, re, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sequence_generator import build_sequence_safe, _validate_variable_refs
from nl_generator import generate_nl
from api_functions import API_FUNCTIONS

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(PROJECT_DIR, "dataset_complex_500.jsonl")

# =============================================================
# ALL 30 SECTORS AND THEIR DOMAIN MAPPINGS
# =============================================================
SECTOR_DOMAIN_MAP = {
    # Cloud Infrastructure (6 sectors)
    "EC2 Compute": "Cloud Infrastructure",
    "S3 Storage": "Cloud Infrastructure",
    "Lambda Serverless": "Cloud Infrastructure",
    "RDS Database": "Cloud Infrastructure",
    "VPC Networking": "Cloud Infrastructure",
    "IAM Security": "Cloud Infrastructure",
    # DevOps/CI-CD (6 sectors)
    "Build Pipelines": "DevOps/CI-CD",
    "Container Orchestration": "DevOps/CI-CD",
    "Monitoring/Alerts": "DevOps/CI-CD",
    "Deployments": "DevOps/CI-CD",
    "Artifact Management": "DevOps/CI-CD",
    "Git/Version Control": "DevOps/CI-CD",
    # CRM/Sales (6 sectors)
    "Leads Management": "CRM/Sales",
    "Accounts Management": "CRM/Sales",
    "Opportunity Pipeline": "CRM/Sales",
    "Campaign Management": "CRM/Sales",
    "Contacts/Communications": "CRM/Sales",
    "Sales Analytics": "CRM/Sales",
    # FinTech/Payments (6 sectors)
    "Payment Processing": "FinTech/Payments",
    "Invoice Management": "FinTech/Payments",
    "Subscriptions": "FinTech/Payments",
    "Compliance/AML": "FinTech/Payments",
    "Transaction Reconciliation": "FinTech/Payments",
    "Vendor Payouts": "FinTech/Payments",
    # HR/SaaS Operations (6 sectors)
    "Employee Management": "HR/SaaS Operations",
    "Onboarding": "HR/SaaS Operations",
    "Payroll Processing": "HR/SaaS Operations",
    "Benefits Administration": "HR/SaaS Operations",
    "Training/LMS": "HR/SaaS Operations",
    "Performance Reviews": "HR/SaaS Operations",
}

COMPLEX_TEMPLATES = []

# -----------------------------------------------------------
# PATTERN: prerequisite-chain — build foundations, then layers
# -----------------------------------------------------------

# T1: EC2 Compute - Full lifecycle with security group prerequisite (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "EC2 Compute", "domain": "Cloud Infrastructure",
    "nl_template": "Set up a complete EC2 compute lifecycle: create security group {group_name} in VPC {vpc_id}, provision a {instance_type} instance with {volume_size_gb}GB volume, create a {bucket_name} S3 bucket, upload config, deploy Lambda {function_name} monitor, create a CPU alert, stop the instance for maintenance, and finally restart it",
    "actions": [
        {"namespace": "AWS.VPC", "function": "CreateSecurityGroup", "params": {"group_name": "{group_name}", "description": "{description}", "vpc_id": "{vpc_id}"}, "output_refs": {"group_id": "Security group ID"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSecurityGroup"}},
        {"namespace": "AWS.EC2", "function": "ProvisionInstance", "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}", "security_group": "{{steps[1].output.group_id}}", "volume_size_gb": "{volume_size_gb}"}, "output_refs": {"instance_id": "Provisioned EC2 instance", "public_ip": "EC2 public IP"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.EC2", "function": "TerminateInstance"}},
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private", "versioning": True, "encryption": "AES256"}, "output_refs": {"bucket_name": "Created data bucket", "bucket_arn": "Bucket ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[3].output.bucket_name}}", "object_key": "{object_key}", "content_type": "application/json", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Uploaded config key", "etag": "Upload ETag"}, "depends_on": [3]},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": "{memory_mb}", "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Monitor Lambda name", "function_arn": "Lambda ARN"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 90.0, "operator": ">", "duration_minutes": "{duration_minutes}", "channels": ["slack", "pagerduty"], "severity": "critical"}, "output_refs": {"alert_id": "CPU alert ID"}, "depends_on": [2]},
        {"namespace": "AWS.EC2", "function": "StopInstance", "params": {"instance_id": "{{steps[2].output.instance_id}}", "hibernate": False}, "output_refs": {"stopped_state": "Stopped state"}, "depends_on": [2]},
        {"namespace": "AWS.EC2", "function": "StartInstance", "params": {"instance_id": "{{steps[2].output.instance_id}}"}, "output_refs": {"new_public_ip": "New public IP"}, "depends_on": [7]},
    ]
})

# T2: S3 Storage - Data lake with IAM (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "S3 Storage", "domain": "Cloud Infrastructure",
    "nl_template": "Build a secure data lake: create bucket {bucket_name} with encryption, upload {object_key} data file, upload {object_key} config, set up event notifications via Lambda {function_name}, attach IAM policy, verify bucket versioning, and configure lifecycle rules",
    "actions": [
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private", "versioning": True, "encryption": "AES256"}, "output_refs": {"bucket_name": "Created bucket", "bucket_arn": "Bucket ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}", "content_type": "application/json", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Data file key", "etag": "Upload ETag"}, "depends_on": [1]},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}", "content_type": "text/csv", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Config key", "etag": "Config ETag"}, "depends_on": [1]},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "python3.9", "memory_mb": "{memory_mb}", "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Event processor", "function_arn": "Lambda ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "{policy_arn}", "target_name": "{target_name}", "target_type": "user"}, "output_refs": {"policy_arn": "Attached policy", "target_name": "Entity"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}", "content_type": "text/plain", "storage_class": "GLACIER"}, "output_refs": {"uploaded_key": "Archived log", "etag": "Archive ETag"}, "depends_on": [1]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Storage", "Requests", "Errors"], "time_range": "last_24h", "refresh_interval_seconds": 60}, "output_refs": {"dashboard_uid": "Storage dashboard ID", "url": "Dashboard URL"}, "depends_on": [1]},
    ]
})

# T3: Lambda Serverless - Full serverless stack (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Lambda Serverless", "domain": "Cloud Infrastructure",
    "nl_template": "Deploy a serverless stack: create IAM user {user_name} for Lambda, attach {policy_arn} policy, build Lambda function {function_name}, invoke it, set up alert {alert_name}, create monitoring dashboard, upload test artifact, and clean up invocation",
    "actions": [
        {"namespace": "AWS.IAM", "function": "CreateUser", "params": {"user_name": "{user_name}", "path": "/service-accounts/"}, "output_refs": {"user_name": "Lambda service user", "user_arn": "User ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[1].output.user_name}}", "target_type": "user"}, "output_refs": {"policy_arn": "Attached policy", "target_name": "Entity"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": "{memory_mb}", "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Lambda function", "function_arn": "Function ARN"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "AWS.Lambda", "function": "InvokeFunction", "params": {"function_name": "{{steps[3].output.function_name}}", "invocation_type": "RequestResponse", "payload": '{"event":"test"}'}, "output_refs": {"status_code": "Invocation result", "log_group": "CloudWatch log group"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 5.0, "operator": ">", "duration_minutes": 5, "channels": ["slack"], "severity": "warning"}, "output_refs": {"alert_id": "Error rate alert"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Invocations", "Duration", "Errors"], "time_range": "last_6h", "refresh_interval_seconds": 60}, "output_refs": {"dashboard_uid": "Lambda dashboard", "url": "Dashboard URL"}, "depends_on": [3]},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "lambda-package.zip", "version": "1.0.0", "repository": "pypi", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Lambda package", "download_url": "Download URL"}, "depends_on": []},
        {"namespace": "AWS.Lambda", "function": "InvokeFunction", "params": {"function_name": "{{steps[3].output.function_name}}", "invocation_type": "Event", "payload": '{"cleanup":"true"}'}, "output_refs": {"status_code": "Cleanup result", "execution_result": "Result payload"}, "depends_on": [3]},
    ]
})

# T4: RDS Database - Full database lifecycle (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "RDS Database", "domain": "Cloud Infrastructure",
    "nl_template": "Provision a production database: create security group {group_name} for DB access, launch {db_name} RDS {engine} instance with {storage_gb}GB storage, create backup bucket {bucket_name}, set up monitoring alert {alert_name}, take a snapshot, configure multi-AZ, and verify endpoint",
    "actions": [
        {"namespace": "AWS.VPC", "function": "CreateSecurityGroup", "params": {"group_name": "{group_name}", "description": "Database access", "vpc_id": "{vpc_id}"}, "output_refs": {"group_id": "DB security group"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSecurityGroup"}},
        {"namespace": "AWS.RDS", "function": "CreateDatabase", "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "{instance_class}", "storage_gb": "{storage_gb}", "multi_az": True, "backup_retention_days": "{backup_retention_days}"}, "output_refs": {"db_instance_id": "RDS instance", "endpoint": "DB endpoint", "arn": "DB ARN"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.RDS", "function": "DeleteDatabase"}},
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private", "versioning": True, "encryption": "AES256"}, "output_refs": {"bucket_name": "Backup bucket", "bucket_arn": "Bucket ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 80.0, "operator": ">", "duration_minutes": 10, "channels": ["pagerduty", "slack"], "severity": "critical"}, "output_refs": {"alert_id": "DB CPU alert"}, "depends_on": [2]},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[3].output.bucket_name}}", "object_key": "{object_key}", "content_type": "application/sql", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "DB snapshot key", "etag": "Snapshot ETag"}, "depends_on": [3]},
        {"namespace": "AWS.RDS", "function": "CreateDatabase", "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "{instance_class}", "storage_gb": "{storage_gb}", "multi_az": True, "backup_retention_days": 30}, "output_refs": {"db_instance_id": "Replica instance", "endpoint": "Replica endpoint"}, "depends_on": [2], "rollback_ref": {"namespace": "AWS.RDS", "function": "DeleteDatabase"}},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "DB Metrics", "panels": ["Connections", "Replication Lag", "IOPS"], "time_range": "last_1h", "refresh_interval_seconds": 30}, "output_refs": {"dashboard_uid": "DB dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
        {"namespace": "AWS.VPC", "function": "CreateSubnet", "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}", "map_public_ip": False}, "output_refs": {"subnet_id": "DB subnet", "vpc_id": "VPC ID"}, "depends_on": [1]},
    ]
})

# T5: VPC Networking - Full network infrastructure (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "VPC Networking", "domain": "Cloud Infrastructure",
    "nl_template": "Create a secure network topology: create security group {group_name}, provision subnet {cidr_block} in {availability_zone}, attach IAM user {user_name} for network admin, create monitoring alert {alert_name}, set up second subnet, configure dashboard, and verify network paths",
    "actions": [
        {"namespace": "AWS.VPC", "function": "CreateSecurityGroup", "params": {"group_name": "{group_name}", "description": "Network security", "vpc_id": "{vpc_id}"}, "output_refs": {"group_id": "Network SG", "group_name": "SG name"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSecurityGroup"}},
        {"namespace": "AWS.VPC", "function": "CreateSubnet", "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}", "map_public_ip": True}, "output_refs": {"subnet_id": "Public subnet", "cidr_block": "Subnet CIDR"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSubnet"}},
        {"namespace": "AWS.IAM", "function": "CreateUser", "params": {"user_name": "{user_name}", "path": "/system/"}, "output_refs": {"user_name": "Network admin", "user_arn": "Admin ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
        {"namespace": "AWS.VPC", "function": "CreateSubnet", "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}", "map_public_ip": False}, "output_refs": {"subnet_id": "Private subnet", "cidr_block": "Private CIDR"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSubnet"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "uptime", "threshold": 99.9, "operator": "<", "duration_minutes": 5, "channels": ["pagerduty"], "severity": "critical"}, "output_refs": {"alert_id": "Network uptime alert"}, "depends_on": [2]},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[3].output.user_name}}", "target_type": "user"}, "output_refs": {"policy_arn": "Attached policy", "target_name": "Entity"}, "depends_on": [3], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "Network Overview", "panels": ["Traffic", "Latency", "Packet Loss"], "time_range": "last_24h", "refresh_interval_seconds": 60}, "output_refs": {"dashboard_uid": "Network dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
    ]
})

# T6: IAM Security - Full IAM lifecycle with policies (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "IAM Security", "domain": "Cloud Infrastructure",
    "nl_template": "Establish complete IAM security: create IAM user {user_name} for automation, attach Admin policy, create a second user {user_name} for backup, set up S3 bucket {bucket_name} for audit logs, upload audit config, create security alert, and generate support tickets for access review",
    "actions": [
        {"namespace": "AWS.IAM", "function": "CreateUser", "params": {"user_name": "{user_name}", "path": "/service-accounts/"}, "output_refs": {"user_name": "Automation user", "user_arn": "User ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[1].output.user_name}}", "target_type": "user"}, "output_refs": {"policy_arn": "Attached policy", "target_name": "Entity"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "AWS.IAM", "function": "CreateUser", "params": {"user_name": "{user_name}", "path": "/system/"}, "output_refs": {"user_name": "Backup user", "user_arn": "Backup ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[3].output.user_name}}", "target_type": "user"}, "output_refs": {"policy_arn": "Backup policy", "target_name": "Entity"}, "depends_on": [3], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "bucket-owner-only", "versioning": True, "encryption": "aws:kms"}, "output_refs": {"bucket_name": "Audit bucket", "bucket_arn": "Bucket ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[5].output.bucket_name}}", "object_key": "{object_key}", "content_type": "application/json", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Audit config", "etag": "Audit config ETag"}, "depends_on": [5]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 3.0, "operator": ">", "duration_minutes": 5, "channels": ["email", "slack"], "severity": "warning"}, "output_refs": {"alert_id": "IAM alert"}, "depends_on": []},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Access review required", "priority": "high", "category": "account", "contact_email": "{contact_email}", "account_id": "{{steps[1].output.user_name}}"}, "output_refs": {"ticket_id": "Access review ticket"}, "depends_on": [1]},
    ]
})

# T7: Build Pipelines - Full CI pipeline with builds (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Build Pipelines", "domain": "DevOps/CI-CD",
    "nl_template": "Set up CI/CD infrastructure: create build pipeline {pipeline_name} for {repository_url}, trigger a build with commit {commit_hash}, upload artifact {artifact_name}, promote build to {target_env}, set up monitoring alert, create deployment dashboard, and revert if needed",
    "actions": [
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}", "build_image": "{build_image}", "timeout_minutes": "{timeout_minutes}", "concurrent_builds": 2}, "output_refs": {"pipeline_id": "CI pipeline", "pipeline_name": "Pipeline name", "webhook_url": "Webhook URL"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Build", "function": "TriggerBuild", "params": {"pipeline_name": "{{steps[1].output.pipeline_name}}", "commit_hash": "{commit_hash}", "variables": {"BUILD_ENV": "staging"}}, "output_refs": {"build_id": "Build execution ID", "status": "Build status"}, "depends_on": [1]},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "{artifact_name}", "version": "1.0.0", "repository": "docker-hub", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Build artifact", "download_url": "Download URL"}, "depends_on": [2]},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[3].output.artifact_id}}", "source_env": "staging", "target_env": "{target_env}", "rollback_strategy": "immediate", "canary_percent": 10}, "output_refs": {"promotion_id": "Promotion ID", "deployment_url": "Deployment URL", "status": "Promotion status"}, "depends_on": [3], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "p99_latency", "threshold": 500.0, "operator": ">", "duration_minutes": 5, "channels": ["slack", "pagerduty"], "severity": "critical"}, "output_refs": {"alert_id": "Latency alert"}, "depends_on": [4]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Build Times", "Deploy Frequency", "Error Rate"], "time_range": "last_24h", "refresh_interval_seconds": 60}, "output_refs": {"dashboard_uid": "CI/CD dashboard", "url": "Dashboard URL"}, "depends_on": [1]},
        {"namespace": "CI.Deploy", "function": "RevertBuild", "params": {"promotion_id": "{{steps[4].output.promotion_id}}", "target_env": "{target_env}", "revert_strategy": "immediate"}, "output_refs": {"promotion_id": "Reverted promotion", "status": "Revert status"}, "depends_on": [4]},
    ]
})

# T8: Container Orchestration - K8s full lifecycle (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Container Orchestration", "domain": "DevOps/CI-CD",
    "nl_template": "Deploy Kubernetes infrastructure: create namespace {namespace} with quotas, deploy service {service_name} with {replicas} replicas, create build pipeline {pipeline_name}, promote artifact, scale deployment, set up alerting, and deploy monitoring dashboard",
    "actions": [
        {"namespace": "K8s.Cluster", "function": "CreateNamespace", "params": {"namespace": "{namespace}", "labels": {"env": "prod"}, "resource_quota_cpu": "20", "resource_quota_memory": "50Gi"}, "output_refs": {"namespace": "K8s namespace", "uid": "Namespace UUID"}, "depends_on": [], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteNamespace"}},
        {"namespace": "K8s.Cluster", "function": "DeployService", "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "{service_name}", "image": "{image}", "replicas": "{replicas}", "cpu_limit": "1", "memory_limit": "1Gi", "expose_port": "{expose_port}"}, "output_refs": {"service_name": "Deployed service", "cluster_ip": "Service cluster IP", "available_replicas": "Ready replicas"}, "depends_on": [1], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteDeployment"}},
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}", "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 2}, "output_refs": {"pipeline_id": "K8s build pipeline", "pipeline_name": "Pipeline name"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "docker-image.tar", "version": "2.3.1", "repository": "docker-hub", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Container image", "download_url": "Download URL"}, "depends_on": [3]},
        {"namespace": "K8s.Cluster", "function": "ScaleDeployment", "params": {"namespace": "{{steps[1].output.namespace}}", "deployment_name": "{{steps[2].output.service_name}}", "replicas": 5}, "output_refs": {"deployment_name": "Scaled deployment", "new_replicas": "New count"}, "depends_on": [2]},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[4].output.artifact_id}}", "source_env": "development", "target_env": "{target_env}", "rollback_strategy": "gradual", "canary_percent": 25}, "output_refs": {"promotion_id": "Deploy promotion", "deployment_url": "Deploy URL"}, "depends_on": [4], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "memory_usage", "threshold": 85.0, "operator": ">", "duration_minutes": 5, "channels": ["slack"], "severity": "warning"}, "output_refs": {"alert_id": "Memory alert"}, "depends_on": [2]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Pod Health", "Resource Usage", "Deployments"], "time_range": "last_6h", "refresh_interval_seconds": 30}, "output_refs": {"dashboard_uid": "K8s dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
    ]
})

# T9: Monitoring/Alerts - Full observability stack (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Monitoring/Alerts", "domain": "DevOps/CI-CD",
    "nl_template": "Set up complete monitoring stack: create CPU alert {alert_name}, set up dashboard {dashboard_name}, create Lambda for event processing, create memory alert, deploy a K8s namespace for monitoring, upload monitoring config, and generate support ticket for review",
    "actions": [
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 90.0, "operator": ">", "duration_minutes": 5, "channels": ["pagerduty", "slack"], "severity": "critical"}, "output_refs": {"alert_id": "CPU critical alert"}, "depends_on": [], "rollback_ref": {"namespace": "Ops.Monitoring", "function": "DismissAlert"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "memory_usage", "threshold": 85.0, "operator": ">", "duration_minutes": 10, "channels": ["slack"], "severity": "warning"}, "output_refs": {"alert_id": "Memory warning alert"}, "depends_on": [], "rollback_ref": {"namespace": "Ops.Monitoring", "function": "DismissAlert"}},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["CPU", "Memory", "Disk", "Network"], "time_range": "last_24h", "refresh_interval_seconds": 30}, "output_refs": {"dashboard_uid": "Main dashboard", "url": "Dashboard URL"}, "depends_on": [1]},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "python3.9", "memory_mb": "{memory_mb}", "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Event processor", "function_arn": "Lambda ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "K8s.Cluster", "function": "CreateNamespace", "params": {"namespace": "{namespace}", "labels": {"tier": "monitoring"}, "resource_quota_cpu": "10", "resource_quota_memory": "20Gi"}, "output_refs": {"namespace": "Monitoring namespace", "uid": "NS UUID"}, "depends_on": [], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteNamespace"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{bucket_name}", "object_key": "{object_key}", "content_type": "application/json", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Alert config", "etag": "Config ETag"}, "depends_on": []},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Monitoring setup review", "priority": "medium", "category": "technical", "contact_email": "{contact_email}", "account_id": "{account_id}"}, "output_refs": {"ticket_id": "Monitoring review ticket"}, "depends_on": []},
    ]
})

# T10: Deployments - Full deployment pipeline with rollback (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Deployments", "domain": "DevOps/CI-CD",
    "nl_template": "Execute a production deployment: create build pipeline {pipeline_name} for {repository_url}, build and upload artifact {artifact_name}, promote to {target_env} with canary, verify with alert {alert_name}, scale up resources, create dashboard, and prepare rollback",
    "actions": [
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}", "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 5}, "output_refs": {"pipeline_id": "Deploy pipeline", "pipeline_name": "Pipeline name", "webhook_url": "Trigger URL"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "{artifact_name}", "version": "release-2024.1", "repository": "docker-hub", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Release artifact", "download_url": "Download URL"}, "depends_on": [1]},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[2].output.artifact_id}}", "source_env": "staging", "target_env": "{target_env}", "rollback_strategy": "gradual", "canary_percent": 10}, "output_refs": {"promotion_id": "Production deploy", "deployment_url": "Service URL", "status": "deploying"}, "depends_on": [2], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 1.0, "operator": ">", "duration_minutes": 5, "channels": ["pagerduty", "slack"], "severity": "critical"}, "output_refs": {"alert_id": "Deploy error alert"}, "depends_on": [3]},
        {"namespace": "K8s.Cluster", "function": "ScaleDeployment", "params": {"namespace": "production", "deployment_name": "{service_name}", "replicas": 10}, "output_refs": {"deployment_name": "Scaled service", "new_replicas": "New count"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Deploy Health", "Traffic", "Errors"], "time_range": "last_1h", "refresh_interval_seconds": 30}, "output_refs": {"dashboard_uid": "Deploy dashboard", "url": "Dashboard URL"}, "depends_on": [3]},
        {"namespace": "CI.Git", "function": "CreateBranch", "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "main"}, "output_refs": {"branch_name": "Release branch", "commit_hash": "Branch HEAD"}, "depends_on": []},
    ]
})

# T11: Artifact Management - Full artifact lifecycle (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Artifact Management", "domain": "DevOps/CI-CD",
    "nl_template": "Manage build artifacts end-to-end: upload artifact {artifact_name} version {version} to {repository}, create build pipeline {pipeline_name}, trigger build for {commit_hash}, promote artifact to {target_env}, set up monitoring, create Git branch for release, and create pull request for review",
    "actions": [
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "{artifact_name}", "version": "{version}", "repository": "{repository}", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Uploaded artifact", "download_url": "Download URL"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Artifacts", "function": "DeleteArtifact"}},
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}", "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 2}, "output_refs": {"pipeline_id": "Build pipeline", "pipeline_name": "Pipeline name"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Build", "function": "TriggerBuild", "params": {"pipeline_name": "{{steps[2].output.pipeline_name}}", "commit_hash": "{commit_hash}", "variables": {"BUILD_ENV": "production"}}, "output_refs": {"build_id": "Triggered build", "status": "Build queued"}, "depends_on": [2]},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[1].output.artifact_id}}", "source_env": "staging", "target_env": "{target_env}", "rollback_strategy": "immediate", "canary_percent": 25}, "output_refs": {"promotion_id": "Artifact promotion", "deployment_url": "Deploy URL"}, "depends_on": [1], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 2.0, "operator": ">", "duration_minutes": 5, "channels": ["slack"], "severity": "warning"}, "output_refs": {"alert_id": "Artifact alert"}, "depends_on": [4]},
        {"namespace": "CI.Git", "function": "CreateBranch", "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "develop"}, "output_refs": {"branch_name": "Release branch", "commit_hash": "Branch commit"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Git", "function": "DeleteBranch"}},
        {"namespace": "CI.Git", "function": "CreatePullRequest", "params": {"repository": "{repository}", "title": "Release new artifact version", "source_branch": "{{steps[6].output.branch_name}}", "target_branch": "main", "reviewers": ["alice", "bob"]}, "output_refs": {"pr_number": "Release PR", "url": "PR URL"}, "depends_on": [6]},
    ]
})

# T12: Git/Version Control - Complete Git workflow (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Git/Version Control", "domain": "DevOps/CI-CD",
    "nl_template": "Execute a Git feature workflow: create branch {branch_name} from {source_branch}, create pull request for {repository}, trigger build pipeline {pipeline_name}, upload artifact, merge PR, deploy to {target_env}, and set up monitoring alert",
    "actions": [
        {"namespace": "CI.Git", "function": "CreateBranch", "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "{source_branch}"}, "output_refs": {"branch_name": "Feature branch", "commit_hash": "Branch HEAD"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Git", "function": "DeleteBranch"}},
        {"namespace": "CI.Git", "function": "CreatePullRequest", "params": {"repository": "{repository}", "title": "New feature implementation", "source_branch": "{{steps[1].output.branch_name}}", "target_branch": "main", "reviewers": ["alice", "bob"]}, "output_refs": {"pr_number": "Feature PR", "url": "PR URL"}, "depends_on": [1]},
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{{steps[1].output.branch_name}}", "build_image": "{build_image}", "timeout_minutes": 15, "concurrent_builds": 2}, "output_refs": {"pipeline_id": "Feature pipeline", "pipeline_name": "Pipeline name"}, "depends_on": [1], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "app.jar", "version": "2.0.0", "repository": "maven-central", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Feature artifact", "download_url": "Download URL"}, "depends_on": [3]},
        {"namespace": "CI.Git", "function": "MergePullRequest", "params": {"repository": "{repository}", "pr_number": "{{steps[2].output.pr_number}}", "merge_method": "squash", "delete_source_branch": True}, "output_refs": {"merge_commit": "Merge commit SHA", "status": "merged"}, "depends_on": [2]},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[4].output.artifact_id}}", "source_env": "staging", "target_env": "{target_env}", "rollback_strategy": "immediate", "canary_percent": 0}, "output_refs": {"promotion_id": "Feature deploy", "deployment_url": "Deploy URL"}, "depends_on": [4], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 5.0, "operator": ">", "duration_minutes": 5, "channels": ["slack", "email"], "severity": "warning"}, "output_refs": {"alert_id": "Deployment alert"}, "depends_on": [6]},
    ]
})

# T13: Leads Management - Lead-to-opportunity pipeline (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Leads Management", "domain": "CRM/Sales",
    "nl_template": "Convert a lead through full sales pipeline: create lead record for {first_name} {last_name} at {company}, qualify lead with BANT criteria, create opportunity {opportunity_name} worth ${amount}, update stage to demo, generate quote, convert to order, and create support ticket",
    "actions": [
        {"namespace": "CRM.Leads", "function": "CreateLead", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "company": "{company}", "source": "{source}", "score": 65}, "output_refs": {"lead_id": "New lead ID", "full_name": "Lead name", "company": "Lead company"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
        {"namespace": "CRM.Leads", "function": "QualifyLead", "params": {"lead_id": "{{steps[1].output.lead_id}}", "budget_available": True, "authority_level": "{authority_level}", "timeline": "{timeline}"}, "output_refs": {"lead_id": "Qualified lead", "qualification_score": "BANT score", "bant_status": "BANT status"}, "depends_on": [1]},
        {"namespace": "CRM.Opportunity", "function": "CreateOpportunity", "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "qualification", "probability": 25, "lead_id": "{{steps[1].output.lead_id}}"}, "output_refs": {"opportunity_id": "Sales opportunity", "amount": "Deal amount", "stage": "Current stage"}, "depends_on": [1], "rollback_ref": {"namespace": "CRM.Opportunity", "function": "DeleteOpportunity"}},
        {"namespace": "CRM.Opportunity", "function": "UpdateOpportunityStage", "params": {"opportunity_id": "{{steps[3].output.opportunity_id}}", "new_stage": "demo", "reason": "Product demo completed"}, "output_refs": {"opportunity_id": "Updated opportunity", "previous_stage": "Old stage", "current_stage": "Demo stage"}, "depends_on": [3]},
        {"namespace": "CRM.Orders", "function": "CreateQuote", "params": {"opportunity_id": "{{steps[3].output.opportunity_id}}", "product": "Enterprise License", "quantity": 10, "unit_price": 999.0, "discount_percent": 10}, "output_refs": {"quote_id": "Sales quote", "total_amount": "Quote total", "status": "Quote status"}, "depends_on": [3], "rollback_ref": {"namespace": "CRM.Orders", "function": "DeleteQuote"}},
        {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder", "params": {"quote_id": "{{steps[5].output.quote_id}}", "payment_terms": "net-30", "shipping_method": "digital-delivery"}, "output_refs": {"order_id": "Converted order", "order_total": "Order amount", "status": "Order confirmed"}, "depends_on": [5]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Onboarding for new customer", "priority": "high", "category": "account", "contact_email": "{email}", "account_id": "{{steps[1].output.lead_id}}"}, "output_refs": {"ticket_id": "Onboarding ticket"}, "depends_on": [6]},
    ]
})

# T14: Accounts Management - Full account lifecycle (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Accounts Management", "domain": "CRM/Sales",
    "nl_template": "Manage enterprise account end-to-end: create account {account_name} in {industry} sector with {size_employees} employees, create lead for primary contact, create sales opportunity {opportunity_name}, generate quote, convert to order, set up support ticket, and create campaign for upsell",
    "actions": [
        {"namespace": "CRM.Accounts", "function": "CreateAccount", "params": {"account_name": "{account_name}", "industry": "{industry}", "size_employees": "{size_employees}", "tier": "enterprise"}, "output_refs": {"account_id": "Enterprise account", "account_name": "Account name", "tier": "Service tier"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Accounts", "function": "DeleteAccount"}},
        {"namespace": "CRM.Leads", "function": "CreateLead", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "company": "{{steps[1].output.account_name}}", "source": "referral", "score": 80}, "output_refs": {"lead_id": "Account lead", "full_name": "Contact name"}, "depends_on": [1], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
        {"namespace": "CRM.Opportunity", "function": "CreateOpportunity", "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "prospecting", "probability": 10, "lead_id": "{{steps[2].output.lead_id}}"}, "output_refs": {"opportunity_id": "Account opportunity", "amount": "Deal amount"}, "depends_on": [2], "rollback_ref": {"namespace": "CRM.Opportunity", "function": "DeleteOpportunity"}},
        {"namespace": "CRM.Orders", "function": "CreateQuote", "params": {"opportunity_id": "{{steps[3].output.opportunity_id}}", "product": "Enterprise License", "quantity": 50, "unit_price": 1999.0, "discount_percent": 15}, "output_refs": {"quote_id": "Account quote", "total_amount": "Quote total"}, "depends_on": [3], "rollback_ref": {"namespace": "CRM.Orders", "function": "DeleteQuote"}},
        {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder", "params": {"quote_id": "{{steps[4].output.quote_id}}", "payment_terms": "net-60", "shipping_method": "digital-delivery"}, "output_refs": {"order_id": "Account order", "order_total": "Order amount", "status": "confirmed"}, "depends_on": [4]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Enterprise account setup", "priority": "high", "category": "account", "contact_email": "{email}", "account_id": "{{steps[1].output.account_id}}"}, "output_refs": {"ticket_id": "Account setup ticket"}, "depends_on": [1]},
        {"namespace": "CRM.Campaigns", "function": "CreateCampaign", "params": {"campaign_name": "{campaign_name}", "type": "email", "budget": 10000.0, "target_audience": "enterprise", "start_date": "{start_date}"}, "output_refs": {"campaign_id": "Upsell campaign", "budget": "Campaign budget", "status": "draft"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Campaigns", "function": "DeleteCampaign"}},
    ]
})

# T15: Opportunity Pipeline - Full opportunity management (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Opportunity Pipeline", "domain": "CRM/Sales",
    "nl_template": "Manage a high-value opportunity through the pipeline: create lead for {first_name} {last_name}, qualify with BANT, create opportunity {opportunity_name} worth ${amount}, advance to demo stage, create quote, convert to order, and launch a campaign for the deal",
    "actions": [
        {"namespace": "CRM.Leads", "function": "CreateLead", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "company": "{company}", "source": "conference", "score": 50}, "output_refs": {"lead_id": "Conference lead", "full_name": "Contact"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
        {"namespace": "CRM.Leads", "function": "QualifyLead", "params": {"lead_id": "{{steps[1].output.lead_id}}", "budget_available": True, "authority_level": "{authority_level}", "timeline": "{timeline}"}, "output_refs": {"lead_id": "Qualified lead", "qualification_score": "BANT score"}, "depends_on": [1]},
        {"namespace": "CRM.Opportunity", "function": "CreateOpportunity", "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "qualification", "probability": 25, "lead_id": "{{steps[1].output.lead_id}}"}, "output_refs": {"opportunity_id": "Deal opportunity", "amount": "Deal value", "stage": "Current stage"}, "depends_on": [1], "rollback_ref": {"namespace": "CRM.Opportunity", "function": "DeleteOpportunity"}},
        {"namespace": "CRM.Opportunity", "function": "UpdateOpportunityStage", "params": {"opportunity_id": "{{steps[3].output.opportunity_id}}", "new_stage": "demo", "reason": "Product demo completed"}, "output_refs": {"opportunity_id": "Advanced opp", "previous_stage": "Old stage", "current_stage": "demo"}, "depends_on": [3]},
        {"namespace": "CRM.Orders", "function": "CreateQuote", "params": {"opportunity_id": "{{steps[3].output.opportunity_id}}", "product": "SaaS Subscription", "quantity": 25, "unit_price": 499.0, "discount_percent": 5}, "output_refs": {"quote_id": "Opportunity quote", "total_amount": "Quote total"}, "depends_on": [3], "rollback_ref": {"namespace": "CRM.Orders", "function": "DeleteQuote"}},
        {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder", "params": {"quote_id": "{{steps[5].output.quote_id}}", "payment_terms": "net-30", "shipping_method": "digital-delivery"}, "output_refs": {"order_id": "Won order", "order_total": "Final amount", "status": "confirmed"}, "depends_on": [5]},
        {"namespace": "CRM.Campaigns", "function": "CreateCampaign", "params": {"campaign_name": "{campaign_name}", "type": "content", "budget": 25000.0, "target_audience": "mid-market", "start_date": "{start_date}"}, "output_refs": {"campaign_id": "Deal campaign", "budget": "Campaign budget"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Campaigns", "function": "DeleteCampaign"}},
    ]
})

# T16: Campaign Management - Full campaign lifecycle (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Campaign Management", "domain": "CRM/Sales",
    "nl_template": "Launch and manage a marketing campaign: create {type} campaign {campaign_name} with ${budget} budget, launch it on multiple channels, create leads from responses, qualify leads, create opportunities, build a dashboard, and generate support tickets",
    "actions": [
        {"namespace": "CRM.Campaigns", "function": "CreateCampaign", "params": {"campaign_name": "{campaign_name}", "type": "{type}", "budget": "{budget}", "target_audience": "{target_audience}", "start_date": "{start_date}"}, "output_refs": {"campaign_id": "Marketing campaign", "campaign_name": "Campaign name", "status": "draft"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Campaigns", "function": "DeleteCampaign"}},
        {"namespace": "CRM.Campaigns", "function": "LaunchCampaign", "params": {"campaign_id": "{{steps[1].output.campaign_id}}", "launch_channels": ["email", "linkedin"]}, "output_refs": {"campaign_id": "Launched campaign", "status": "active", "active_channels": "Active channels"}, "depends_on": [1]},
        {"namespace": "CRM.Leads", "function": "CreateLead", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "company": "{company}", "source": "{type}", "score": 35}, "output_refs": {"lead_id": "Campaign lead", "full_name": "Lead name"}, "depends_on": [2], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
        {"namespace": "CRM.Leads", "function": "QualifyLead", "params": {"lead_id": "{{steps[3].output.lead_id}}", "budget_available": True, "authority_level": "manager", "timeline": "1-3 months"}, "output_refs": {"lead_id": "Qualified lead", "qualification_score": "BANT result"}, "depends_on": [3]},
        {"namespace": "CRM.Opportunity", "function": "CreateOpportunity", "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "prospecting", "probability": 10, "lead_id": "{{steps[3].output.lead_id}}"}, "output_refs": {"opportunity_id": "Campaign opp", "amount": "Deal amount"}, "depends_on": [3], "rollback_ref": {"namespace": "CRM.Opportunity", "function": "DeleteOpportunity"}},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Leads Generated", "Conversion Rate", "ROI"], "time_range": "last_7d", "refresh_interval_seconds": 300}, "output_refs": {"dashboard_uid": "Campaign dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Campaign performance review", "priority": "medium", "category": "feature-request", "contact_email": "{email}", "account_id": "{{steps[3].output.lead_id}}"}, "output_refs": {"ticket_id": "Campaign review ticket"}, "depends_on": [2]},
    ]
})

# T17: Contacts/Communications - Customer engagement flow (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Contacts/Communications", "domain": "CRM/Sales",
    "nl_template": "Build customer engagement pipeline: create account {account_name} in {industry}, create lead for {first_name} {last_name}, qualify lead, create opportunity {opportunity_name}, create support ticket for onboarding, launch campaign {campaign_name}, and upload customer data artifact",
    "actions": [
        {"namespace": "CRM.Accounts", "function": "CreateAccount", "params": {"account_name": "{account_name}", "industry": "{industry}", "size_employees": "{size_employees}", "tier": "standard"}, "output_refs": {"account_id": "Customer account", "account_name": "Account name"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Accounts", "function": "DeleteAccount"}},
        {"namespace": "CRM.Leads", "function": "CreateLead", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "company": "{{steps[1].output.account_name}}", "source": "website", "score": 50}, "output_refs": {"lead_id": "Contact lead", "full_name": "Contact full name"}, "depends_on": [1], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
        {"namespace": "CRM.Leads", "function": "QualifyLead", "params": {"lead_id": "{{steps[2].output.lead_id}}", "budget_available": True, "authority_level": "{authority_level}", "timeline": "1-3 months"}, "output_refs": {"lead_id": "Qualified contact", "qualification_score": "Qual score"}, "depends_on": [2]},
        {"namespace": "CRM.Opportunity", "function": "CreateOpportunity", "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "qualification", "probability": 25, "lead_id": "{{steps[2].output.lead_id}}"}, "output_refs": {"opportunity_id": "Contact opp", "amount": "Deal value"}, "depends_on": [2], "rollback_ref": {"namespace": "CRM.Opportunity", "function": "DeleteOpportunity"}},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Customer onboarding", "priority": "high", "category": "account", "contact_email": "{email}", "account_id": "{{steps[1].output.account_id}}"}, "output_refs": {"ticket_id": "Customer ticket"}, "depends_on": [1]},
        {"namespace": "CRM.Campaigns", "function": "CreateCampaign", "params": {"campaign_name": "{campaign_name}", "type": "email", "budget": 5000.0, "target_audience": "existing-customers", "start_date": "{start_date}"}, "output_refs": {"campaign_id": "Email campaign", "campaign_name": "Campaign name"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Campaigns", "function": "DeleteCampaign"}},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "customer-data.csv", "version": "1.0.0", "repository": "pypi", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Customer data artifact", "download_url": "Download URL"}, "depends_on": []},
    ]
})

# T18: Sales Analytics - Analytics pipeline (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Sales Analytics", "domain": "CRM/Sales",
    "nl_template": "Set up sales analytics infrastructure: create S3 bucket {bucket_name} for sales data, upload analytics config, create Lambda {function_name} for data processing, invoke it, set up monitoring dashboard {dashboard_name}, create CPU alert, and track leads through the pipeline",
    "actions": [
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private", "versioning": True, "encryption": "AES256"}, "output_refs": {"bucket_name": "Analytics bucket", "bucket_arn": "Bucket ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}", "content_type": "application/json", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Analytics config", "etag": "Config ETag"}, "depends_on": [1]},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "python3.11", "memory_mb": "{memory_mb}", "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Analytics function", "function_arn": "Lambda ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "AWS.Lambda", "function": "InvokeFunction", "params": {"function_name": "{{steps[3].output.function_name}}", "invocation_type": "RequestResponse", "payload": '{"dataset":"sales_q1"}'}, "output_refs": {"status_code": "Invocation result", "execution_result": "Query result"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Revenue", "Lead Conversion", "Pipeline Value"], "time_range": "last_7d", "refresh_interval_seconds": 300}, "output_refs": {"dashboard_uid": "Sales dashboard", "url": "Dashboard URL"}, "depends_on": [1]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 80.0, "operator": ">", "duration_minutes": 5, "channels": ["slack"], "severity": "warning"}, "output_refs": {"alert_id": "Analytics alert"}, "depends_on": [3]},
        {"namespace": "CRM.Leads", "function": "CreateLead", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "company": "{company}", "source": "website", "score": 50}, "output_refs": {"lead_id": "Tracked lead", "full_name": "Lead name"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
    ]
})

# ---------- FinTech/Payments (6 sectors) ----------

# T19: Payment Processing - Full payment flow (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Payment Processing", "domain": "FinTech/Payments",
    "nl_template": "Process a complete payment lifecycle: create account {account_name} for customer, capture payment of {amount_cents} cents with {payment_method}, verify payment receipt, create invoice {invoice_number}, process subscription payment, handle compliance check, generate support ticket for payment issue, and process refund if needed",
    "actions": [
        {"namespace": "CRM.Accounts", "function": "CreateAccount", "params": {"account_name": "{account_name}", "industry": "Finance", "size_employees": 500, "tier": "premium"}, "output_refs": {"account_id": "Customer account", "tier": "Account tier"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Accounts", "function": "DeleteAccount"}},
        {"namespace": "Payments.Processing", "function": "CapturePayment", "params": {"customer_id": "{{steps[1].output.account_id}}", "amount_cents": "{amount_cents}", "currency": "{currency}", "payment_method": "{payment_method}", "description": "Monthly subscription"}, "output_refs": {"payment_id": "Payment transaction", "status": "Payment status", "receipt_url": "Receipt URL"}, "depends_on": [1], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        {"namespace": "Payments.Invoice", "function": "GenerateInvoice", "params": {"customer_id": "{{steps[1].output.account_id}}", "amount_cents": "{amount_cents}", "currency": "{currency}", "due_date": "{due_date}", "description": "Monthly subscription fee"}, "output_refs": {"invoice_id": "Generated invoice", "invoice_number": "Invoice", "status": "Invoice status"}, "depends_on": [2]},
        {"namespace": "Payments.Invoice", "function": "SendInvoice", "params": {"invoice_id": "{{steps[3].output.invoice_id}}", "customer_email": "{customer_email}", "include_pdf": True, "due_date": "{due_date}"}, "output_refs": {"invoice_id": "Sent invoice", "status": "Invoice status"}, "depends_on": [3]},
        {"namespace": "Payments.Subscriptions", "function": "CreateSubscription", "params": {"customer_id": "{{steps[1].output.account_id}}", "plan_name": "{plan_name}", "amount_cents": "{amount_cents}", "currency": "{currency}", "billing_cycle": "monthly", "trial_period_days": 0}, "output_refs": {"subscription_id": "Active subscription", "status": "Subscription status", "current_period_end": "Period end"}, "depends_on": [2], "rollback_ref": {"namespace": "Payments.Subscriptions", "function": "CancelSubscription"}},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{{steps[1].output.account_id}}", "check_type": "kyc", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "Compliance check", "status": "Compliance status", "risk_score": "Risk score"}, "depends_on": [1]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Payment inquiry from customer", "priority": "high", "category": "billing", "contact_email": "{customer_email}", "account_id": "{{steps[1].output.account_id}}"}, "output_refs": {"ticket_id": "Payment support ticket"}, "depends_on": [2]},
        {"namespace": "Payments.Processing", "function": "RefundPayment", "params": {"payment_id": "{{steps[2].output.payment_id}}", "amount_cents": 0, "reason": "customer_request"}, "output_refs": {"refund_id": "Payment refund", "status": "Refund status"}, "depends_on": [2]},
    ]
})

# T20: Invoice Management - Full invoice lifecycle (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Invoice Management", "domain": "FinTech/Payments",
    "nl_template": "Manage full invoice lifecycle: capture payment from customer {customer_id} for {amount_cents} cents, generate invoice, send to {customer_email}, schedule subscription {plan_name}, run compliance check, create dashboard, and create support ticket",
    "actions": [
        {"namespace": "Payments.Processing", "function": "CapturePayment", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "payment_method": "{payment_method}", "description": "Invoice payment"}, "output_refs": {"payment_id": "Invoice payment", "status": "Payment status", "receipt_url": "Payment receipt"}, "depends_on": [], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        {"namespace": "Payments.Invoice", "function": "GenerateInvoice", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "due_date": "{due_date}", "description": "Service fee for Q1"}, "output_refs": {"invoice_id": "Service invoice", "invoice_number": "Invoice", "status": "Invoice status"}, "depends_on": [1]},
        {"namespace": "Payments.Invoice", "function": "SendInvoice", "params": {"invoice_id": "{{steps[2].output.invoice_id}}", "customer_email": "{customer_email}", "include_pdf": True, "due_date": "{due_date}"}, "output_refs": {"invoice_id": "Sent invoice", "status": "Delivered"}, "depends_on": [2]},
        {"namespace": "Payments.Subscriptions", "function": "CreateSubscription", "params": {"customer_id": "{customer_id}", "plan_name": "{plan_name}", "amount_cents": "{amount_cents}", "currency": "{currency}", "billing_cycle": "monthly", "trial_period_days": 14}, "output_refs": {"subscription_id": "New subscription", "status": "Subscription status"}, "depends_on": [1], "rollback_ref": {"namespace": "Payments.Subscriptions", "function": "CancelSubscription"}},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{customer_id}", "check_type": "aml", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "AML compliance", "status": "Compliance result", "risk_score": "Risk score"}, "depends_on": []},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Revenue", "Outstanding", "Paid"], "time_range": "last_30d", "refresh_interval_seconds": 600}, "output_refs": {"dashboard_uid": "Invoice dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Invoice dispute resolution", "priority": "high", "category": "billing", "contact_email": "{customer_email}", "account_id": "{customer_id}"}, "output_refs": {"ticket_id": "Invoice dispute ticket"}, "depends_on": [2]},
    ]
})

# T21: Subscriptions - Full subscription lifecycle (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Subscriptions", "domain": "FinTech/Payments",
    "nl_template": "Manage a subscription lifecycle end-to-end: capture initial payment for {customer_id}, create subscription {plan_name} with monthly billing, generate invoice, send invoice to {customer_email}, run AML compliance check, set up dashboard, create customer support ticket, and cancel subscription",
    "actions": [
        {"namespace": "Payments.Processing", "function": "CapturePayment", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "payment_method": "{payment_method}", "description": "Initial subscription payment"}, "output_refs": {"payment_id": "Subscription payment", "status": "Payment status"}, "depends_on": [], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        {"namespace": "Payments.Subscriptions", "function": "CreateSubscription", "params": {"customer_id": "{customer_id}", "plan_name": "{plan_name}", "amount_cents": "{amount_cents}", "currency": "{currency}", "billing_cycle": "monthly", "trial_period_days": 0}, "output_refs": {"subscription_id": "Active subscription", "status": "Subscription status", "current_period_end": "Billing period end"}, "depends_on": [1], "rollback_ref": {"namespace": "Payments.Subscriptions", "function": "CancelSubscription"}},
        {"namespace": "Payments.Invoice", "function": "GenerateInvoice", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "due_date": "{due_date}", "description": "Monthly subscription fee"}, "output_refs": {"invoice_id": "Subscription invoice", "invoice_number": "Invoice", "status": "Invoice status"}, "depends_on": [2]},
        {"namespace": "Payments.Invoice", "function": "SendInvoice", "params": {"invoice_id": "{{steps[3].output.invoice_id}}", "customer_email": "{customer_email}", "include_pdf": True, "due_date": "{due_date}"}, "output_refs": {"invoice_id": "Delivered invoice", "status": "Sent"}, "depends_on": [3]},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{customer_id}", "check_type": "aml", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "AML check", "status": "Compliance status", "risk_score": "Risk level"}, "depends_on": [1]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["MRR", "Churn", "Active Subs"], "time_range": "last_30d", "refresh_interval_seconds": 600}, "output_refs": {"dashboard_uid": "Subscription dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Subscription billing inquiry", "priority": "medium", "category": "billing", "contact_email": "{customer_email}", "account_id": "{customer_id}"}, "output_refs": {"ticket_id": "Subscription ticket"}, "depends_on": [2]},
        {"namespace": "Payments.Subscriptions", "function": "CancelSubscription", "params": {"subscription_id": "{{steps[2].output.subscription_id}}", "reason": "customer_request", "refund_prorated": True}, "output_refs": {"subscription_id": "Cancelled subscription", "status": "Cancel status", "effective_date": "Cancel date"}, "depends_on": [2]},
    ]
})

# T22: Compliance/AML - Full compliance pipeline (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Compliance/AML", "domain": "FinTech/Payments",
    "nl_template": "Execute full compliance pipeline: create customer account {account_name}, run KYC compliance check, capture initial payment of {amount_cents} cents, generate invoice, run AML check, send invoice to {customer_email}, and create support ticket for compliance review",
    "actions": [
        {"namespace": "CRM.Accounts", "function": "CreateAccount", "params": {"account_name": "{account_name}", "industry": "Finance", "size_employees": 200, "tier": "enterprise"}, "output_refs": {"account_id": "Compliance account", "account_name": "Account name"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Accounts", "function": "DeleteAccount"}},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{{steps[1].output.account_id}}", "check_type": "kyc", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "KYC check ID", "status": "KYC status", "risk_score": "KYC risk"}, "depends_on": [1]},
        {"namespace": "Payments.Processing", "function": "CapturePayment", "params": {"customer_id": "{{steps[1].output.account_id}}", "amount_cents": "{amount_cents}", "currency": "{currency}", "payment_method": "{payment_method}", "description": "Compliance fee"}, "output_refs": {"payment_id": "Compliance payment", "status": "Completed", "receipt_url": "Receipt"}, "depends_on": [2], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        {"namespace": "Payments.Invoice", "function": "GenerateInvoice", "params": {"customer_id": "{{steps[1].output.account_id}}", "amount_cents": "{amount_cents}", "currency": "{currency}", "due_date": "{due_date}", "description": "Compliance service fee"}, "output_refs": {"invoice_id": "Compliance invoice", "invoice_number": "Invoice", "status": "draft"}, "depends_on": [3]},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{{steps[1].output.account_id}}", "check_type": "aml", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "AML check ID", "status": "AML status", "risk_score": "AML risk"}, "depends_on": [2]},
        {"namespace": "Payments.Invoice", "function": "SendInvoice", "params": {"invoice_id": "{{steps[4].output.invoice_id}}", "customer_email": "{customer_email}", "include_pdf": True, "due_date": "{due_date}"}, "output_refs": {"invoice_id": "Sent invoice", "status": "Delivered"}, "depends_on": [4]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Compliance review required", "priority": "critical", "category": "billing", "contact_email": "{customer_email}", "account_id": "{{steps[1].output.account_id}}"}, "output_refs": {"ticket_id": "Compliance ticket"}, "depends_on": [5]},
    ]
})

# T23: Transaction Reconciliation (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Transaction Reconciliation", "domain": "FinTech/Payments",
    "nl_template": "Perform end-to-end transaction reconciliation: capture payment from {customer_id} for {amount_cents} cents with {payment_method}, generate invoice, send invoice to {customer_email}, create subscription {plan_name}, run AML check, set up dashboard, and create support ticket for reconciliation review",
    "actions": [
        {"namespace": "Payments.Processing", "function": "CapturePayment", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "payment_method": "{payment_method}", "description": "Transaction reconciliation"}, "output_refs": {"payment_id": "Transaction payment", "status": "Payment status", "charge_fee_cents": "Processing fee"}, "depends_on": [], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        {"namespace": "Payments.Invoice", "function": "GenerateInvoice", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "due_date": "{due_date}", "description": "Monthly reconciliation fee"}, "output_refs": {"invoice_id": "Reconciliation invoice", "invoice_number": "Invoice", "status": "draft"}, "depends_on": [1]},
        {"namespace": "Payments.Invoice", "function": "SendInvoice", "params": {"invoice_id": "{{steps[2].output.invoice_id}}", "customer_email": "{customer_email}", "include_pdf": True, "due_date": "{due_date}"}, "output_refs": {"invoice_id": "Sent invoice", "status": "Delivered"}, "depends_on": [2]},
        {"namespace": "Payments.Subscriptions", "function": "CreateSubscription", "params": {"customer_id": "{customer_id}", "plan_name": "{plan_name}", "amount_cents": "{amount_cents}", "currency": "{currency}", "billing_cycle": "monthly", "trial_period_days": 30}, "output_refs": {"subscription_id": "Recon subscription", "status": "Active", "current_period_end": "Period end"}, "depends_on": [1], "rollback_ref": {"namespace": "Payments.Subscriptions", "function": "CancelSubscription"}},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{customer_id}", "check_type": "aml", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "Transaction AML check", "status": "AML status", "risk_score": "Risk score"}, "depends_on": [1]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Transactions", "Settlements", "Discrepancies"], "time_range": "last_7d", "refresh_interval_seconds": 300}, "output_refs": {"dashboard_uid": "Recon dashboard", "url": "Dashboard URL"}, "depends_on": [1]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Reconciliation discrepancy report", "priority": "high", "category": "technical", "contact_email": "{customer_email}", "account_id": "{customer_id}"}, "output_refs": {"ticket_id": "Recon discrepancy ticket"}, "depends_on": [1]},
    ]
})

# T24: Vendor Payouts (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Vendor Payouts", "domain": "FinTech/Payments",
    "nl_template": "Process vendor payout workflow: capture payment from {customer_id} for services, generate invoice, run KYC compliance check, create subscription {plan_name} for vendor, send invoice to {customer_email}, run AML verification, and create support ticket for payout approval",
    "actions": [
        {"namespace": "Payments.Processing", "function": "CapturePayment", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "payment_method": "{payment_method}", "description": "Vendor payout"}, "output_refs": {"payment_id": "Vendor payment", "status": "Payment status"}, "depends_on": [], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        {"namespace": "Payments.Invoice", "function": "GenerateInvoice", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "due_date": "{due_date}", "description": "Vendor services invoice"}, "output_refs": {"invoice_id": "Vendor invoice", "invoice_number": "Invoice", "status": "draft"}, "depends_on": [1]},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{customer_id}", "check_type": "kyc", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "Vendor KYC", "status": "KYC status", "risk_score": "Risk score"}, "depends_on": []},
        {"namespace": "Payments.Subscriptions", "function": "CreateSubscription", "params": {"customer_id": "{customer_id}", "plan_name": "{plan_name}", "amount_cents": "{amount_cents}", "currency": "{currency}", "billing_cycle": "monthly", "trial_period_days": 0}, "output_refs": {"subscription_id": "Vendor subscription", "status": "Active"}, "depends_on": [1], "rollback_ref": {"namespace": "Payments.Subscriptions", "function": "CancelSubscription"}},
        {"namespace": "Payments.Invoice", "function": "SendInvoice", "params": {"invoice_id": "{{steps[2].output.invoice_id}}", "customer_email": "{customer_email}", "include_pdf": True, "due_date": "{due_date}"}, "output_refs": {"invoice_id": "Sent invoice", "status": "Sent"}, "depends_on": [2]},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{customer_id}", "check_type": "aml", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "Vendor AML", "status": "AML status", "risk_score": "AML risk"}, "depends_on": [3]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Vendor payout approval needed", "priority": "high", "category": "billing", "contact_email": "{customer_email}", "account_id": "{customer_id}"}, "output_refs": {"ticket_id": "Payout approval ticket"}, "depends_on": [1]},
    ]
})

# ---------- HR/SaaS Operations (6 sectors) ----------

# T25: Employee Management - Full lifecycle (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Employee Management", "domain": "HR/SaaS Operations",
    "nl_template": "Manage complete employee lifecycle: create employee profile for {first_name} {last_name}, set up onboarding, process payroll for {salary_amount} salary, enroll in health benefits {benefit_type}, assign training module {module_name}, record in payroll system, create support ticket for HR, and schedule performance review",
    "actions": [
        {"namespace": "HR.Employees", "function": "CreateEmployee", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "department": "{department}", "role": "{role}", "start_date": "{start_date}"}, "output_refs": {"employee_id": "New employee", "email": "Employee email", "department": "Department"}, "depends_on": [], "rollback_ref": {"namespace": "HR.Employees", "function": "DeleteEmployee"}},
        {"namespace": "HR.Onboarding", "function": "CreateOnboardingChecklist", "params": {"employee_id": "{{steps[1].output.employee_id}}", "items": ["IT Setup", "Benefits Enrollment", "Orientation"], "due_date": "{due_date}", "assigned_to": "HR Team"}, "output_refs": {"checklist_id": "Onboarding checklist", "status": "Checklist status"}, "depends_on": [1]},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 20, "benefits": 5}, "bonus": 0}, "output_refs": {"payroll_id": "Payroll record", "net_amount": "Net pay", "status": "Payroll status"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        {"namespace": "HR.Benefits", "function": "EnrollInBenefits", "params": {"employee_id": "{{steps[1].output.employee_id}}", "benefit_type": "{benefit_type}", "coverage_level": "{coverage_level}", "dependents": 2}, "output_refs": {"enrollment_id": "Benefits enrollment", "status": "Enrollment status", "coverage_start": "Coverage start"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Benefits", "function": "CancelBenefits"}},
        {"namespace": "HR.Training", "function": "AssignTrainingModule", "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_name": "{module_name}", "due_date": "{due_date}", "assigned_by": "Manager"}, "output_refs": {"assignment_id": "Training assignment", "module_name": "Module name", "status": "Assignment status"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Training", "function": "RemoveTrainingAssignment"}},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 20, "benefits": 5}, "bonus": 5000}, "output_refs": {"payroll_id": "Bonus payroll", "net_amount": "Net with bonus", "status": "Processed"}, "depends_on": [3]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "HR system access request", "priority": "medium", "category": "technical", "contact_email": "{email}", "account_id": "{{steps[1].output.employee_id}}"}, "output_refs": {"ticket_id": "HR access ticket"}, "depends_on": [1]},
        {"namespace": "HR.Performance", "function": "CreateReviewCycle", "params": {"employee_id": "{{steps[1].output.employee_id}}", "review_period": "{review_period}", "reviewer": "Direct Manager", "rating": 4, "goals": ["Complete Q1 targets", "Improve collaboration"]}, "output_refs": {"review_id": "Performance review", "status": "Review status"}, "depends_on": [1]},
    ]
})

# T26: Onboarding - Full pipeline (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Onboarding", "domain": "HR/SaaS Operations",
    "nl_template": "Execute complete employee onboarding: create new employee {first_name} {last_name} in {department}, generate onboarding checklist, enroll in {benefit_type} benefits, assign {module_name} training module, process initial payroll of {salary_amount}, upload onboarding documents, and create support ticket for IT setup",
    "actions": [
        {"namespace": "HR.Employees", "function": "CreateEmployee", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "department": "{department}", "role": "{role}", "start_date": "{start_date}"}, "output_refs": {"employee_id": "New hire", "email": "Work email", "department": "Department"}, "depends_on": [], "rollback_ref": {"namespace": "HR.Employees", "function": "DeleteEmployee"}},
        {"namespace": "HR.Onboarding", "function": "CreateOnboardingChecklist", "params": {"employee_id": "{{steps[1].output.employee_id}}", "items": ["IT Setup", "Benefits", "Training", "Security Briefing"], "due_date": "{due_date}", "assigned_to": "HR Coordinator"}, "output_refs": {"checklist_id": "Onboarding checklist", "status": "In progress"}, "depends_on": [1]},
        {"namespace": "HR.Benefits", "function": "EnrollInBenefits", "params": {"employee_id": "{{steps[1].output.employee_id}}", "benefit_type": "{benefit_type}", "coverage_level": "{coverage_level}", "dependents": 0}, "output_refs": {"enrollment_id": "Benefits signup", "status": "Enrolled", "coverage_start": "Coverage start date"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Benefits", "function": "CancelBenefits"}},
        {"namespace": "HR.Training", "function": "AssignTrainingModule", "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_name": "{module_name}", "due_date": "{due_date}", "assigned_by": "HR Team"}, "output_refs": {"assignment_id": "Training assignment", "module_name": "Module name", "status": "Assigned"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Training", "function": "RemoveTrainingAssignment"}},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 15, "benefits": 3}, "bonus": 0}, "output_refs": {"payroll_id": "First payroll", "net_amount": "Net salary", "status": "Processed"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "onboarding-docs.pdf", "version": "1.0.0", "repository": "maven-central", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Onboarding docs", "download_url": "Download URL"}, "depends_on": []},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "IT equipment setup for new hire", "priority": "high", "category": "technical", "contact_email": "{email}", "account_id": "{{steps[1].output.employee_id}}"}, "output_refs": {"ticket_id": "IT setup ticket"}, "depends_on": [1]},
    ]
})

# T27: Payroll Processing - Full payroll cycle (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Payroll Processing", "domain": "HR/SaaS Operations",
    "nl_template": "Process full payroll cycle: create employee {first_name} {last_name} in {department}, process payroll of {salary_amount} with deductions, enroll in {benefit_type} benefits, assign {module_name} training, process bonus payroll, create performance review, and generate support ticket",
    "actions": [
        {"namespace": "HR.Employees", "function": "CreateEmployee", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "department": "{department}", "role": "{role}", "start_date": "{start_date}"}, "output_refs": {"employee_id": "Payroll employee", "email": "Employee email"}, "depends_on": [], "rollback_ref": {"namespace": "HR.Employees", "function": "DeleteEmployee"}},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 25, "benefits": 8, "retirement": 5}, "bonus": 0}, "output_refs": {"payroll_id": "Monthly payroll", "net_amount": "Net salary", "status": "Processed"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        {"namespace": "HR.Benefits", "function": "EnrollInBenefits", "params": {"employee_id": "{{steps[1].output.employee_id}}", "benefit_type": "{benefit_type}", "coverage_level": "{coverage_level}", "dependents": 1}, "output_refs": {"enrollment_id": "Benefit enrollment", "status": "Enrolled"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Benefits", "function": "CancelBenefits"}},
        {"namespace": "HR.Training", "function": "AssignTrainingModule", "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_name": "{module_name}", "due_date": "{due_date}", "assigned_by": "Manager"}, "output_refs": {"assignment_id": "Training record", "module_name": "Course name", "status": "Assigned"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Training", "function": "RemoveTrainingAssignment"}},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 25, "benefits": 8}, "bonus": 10000}, "output_refs": {"payroll_id": "Bonus payroll", "net_amount": "Net with bonus", "status": "Completed"}, "depends_on": [2]},
        {"namespace": "HR.Performance", "function": "CreateReviewCycle", "params": {"employee_id": "{{steps[1].output.employee_id}}", "review_period": "{review_period}", "reviewer": "Senior Manager", "rating": 5, "goals": ["Exceed sales targets", "Mentor junior staff"]}, "output_refs": {"review_id": "Annual review", "status": "Review created"}, "depends_on": [1]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Payroll discrepancy inquiry", "priority": "high", "category": "billing", "contact_email": "{email}", "account_id": "{{steps[1].output.employee_id}}"}, "output_refs": {"ticket_id": "Payroll ticket"}, "depends_on": [2]},
    ]
})

# T28: Benefits Administration (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Benefits Administration", "domain": "HR/SaaS Operations",
    "nl_template": "Manage employee benefits program: create employee {first_name} {last_name}, enroll in {benefit_type} plan with {coverage_level} coverage, assign training module {module_name}, process payroll with benefit deductions, process bonus payroll, upload benefits documentation, and create a support ticket for benefits inquiry",
    "actions": [
        {"namespace": "HR.Employees", "function": "CreateEmployee", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "department": "{department}", "role": "{role}", "start_date": "{start_date}"}, "output_refs": {"employee_id": "Benefits employee", "email": "Employee email"}, "depends_on": [], "rollback_ref": {"namespace": "HR.Employees", "function": "DeleteEmployee"}},
        {"namespace": "HR.Benefits", "function": "EnrollInBenefits", "params": {"employee_id": "{{steps[1].output.employee_id}}", "benefit_type": "{benefit_type}", "coverage_level": "{coverage_level}", "dependents": 3}, "output_refs": {"enrollment_id": "Benefit plan", "status": "Enrolled", "coverage_start": "Coverage date"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Benefits", "function": "CancelBenefits"}},
        {"namespace": "HR.Training", "function": "AssignTrainingModule", "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_name": "{module_name}", "due_date": "{due_date}", "assigned_by": "Benefits Admin"}, "output_refs": {"assignment_id": "Benefits training", "module_name": "Course name", "status": "Assigned"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Training", "function": "RemoveTrainingAssignment"}},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 20, "benefits": 10, "retirement": 3}, "bonus": 0}, "output_refs": {"payroll_id": "Benefits payroll", "net_amount": "Net salary", "status": "Completed"}, "depends_on": [2], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 20, "benefits": 10}, "bonus": 7500}, "output_refs": {"payroll_id": "Bonus with benefits", "net_amount": "Net with bonus", "status": "Completed"}, "depends_on": [4]},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "benefits-guide.pdf", "version": "2024.1", "repository": "maven-central", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Benefits guide", "download_url": "Download URL"}, "depends_on": []},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Benefits coverage question", "priority": "medium", "category": "feature-request", "contact_email": "{email}", "account_id": "{{steps[1].output.employee_id}}"}, "output_refs": {"ticket_id": "Benefits ticket"}, "depends_on": [2]},
    ]
})

# T29: Training/LMS (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Training/LMS", "domain": "HR/SaaS Operations",
    "nl_template": "Manage corporate training program: create employee {first_name} {last_name}, assign training module {module_name} with due date, create second training module, process payroll, upload training materials, enroll in benefits {benefit_type}, and create support ticket for LMS access",
    "actions": [
        {"namespace": "HR.Employees", "function": "CreateEmployee", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "department": "{department}", "role": "{role}", "start_date": "{start_date}"}, "output_refs": {"employee_id": "Trainee", "email": "Employee email"}, "depends_on": [], "rollback_ref": {"namespace": "HR.Employees", "function": "DeleteEmployee"}},
        {"namespace": "HR.Training", "function": "AssignTrainingModule", "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_name": "{module_name}", "due_date": "{due_date}", "assigned_by": "LMS Admin"}, "output_refs": {"assignment_id": "Core training", "module_name": "Course name", "status": "Assigned"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Training", "function": "RemoveTrainingAssignment"}},
        {"namespace": "HR.Training", "function": "AssignTrainingModule", "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_name": "{module_name}", "due_date": "{due_date}", "assigned_by": "Compliance Officer"}, "output_refs": {"assignment_id": "Compliance training", "module_name": "Compliance course", "status": "Assigned"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Training", "function": "RemoveTrainingAssignment"}},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 20, "benefits": 5}, "bonus": 0}, "output_refs": {"payroll_id": "Training payroll", "net_amount": "Net pay", "status": "Completed"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "training-materials.zip", "version": "2024.1", "repository": "maven-central", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Training materials", "download_url": "Download URL"}, "depends_on": []},
        {"namespace": "HR.Benefits", "function": "EnrollInBenefits", "params": {"employee_id": "{{steps[1].output.employee_id}}", "benefit_type": "{benefit_type}", "coverage_level": "{coverage_level}", "dependents": 0}, "output_refs": {"enrollment_id": "Training employee benefits", "status": "Enrolled"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Benefits", "function": "CancelBenefits"}},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "LMS access not working", "priority": "medium", "category": "technical", "contact_email": "{email}", "account_id": "{{steps[1].output.employee_id}}"}, "output_refs": {"ticket_id": "LMS support ticket"}, "depends_on": [2]},
    ]
})

# T30: Performance Reviews (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Performance Reviews", "domain": "HR/SaaS Operations",
    "nl_template": "Execute annual performance review cycle: create employee {first_name} {last_name}, create Q1 review cycle with goals, process payroll with {salary_amount} salary and bonus, assign training {module_name}, enroll in {benefit_type} benefits, create Q2 review, and generate support ticket for review feedback",
    "actions": [
        {"namespace": "HR.Employees", "function": "CreateEmployee", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "department": "{department}", "role": "{role}", "start_date": "{start_date}"}, "output_refs": {"employee_id": "Review employee", "email": "Employee email"}, "depends_on": [], "rollback_ref": {"namespace": "HR.Employees", "function": "DeleteEmployee"}},
        {"namespace": "HR.Performance", "function": "CreateReviewCycle", "params": {"employee_id": "{{steps[1].output.employee_id}}", "review_period": "Q1 2024", "reviewer": "Direct Manager", "rating": 4, "goals": ["Complete project milestones", "Improve code quality"]}, "output_refs": {"review_id": "Q1 review", "status": "Review created"}, "depends_on": [1]},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 20, "benefits": 5}, "bonus": 15000}, "output_refs": {"payroll_id": "Review bonus payroll", "net_amount": "Net with bonus", "status": "Completed"}, "depends_on": [2], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        {"namespace": "HR.Training", "function": "AssignTrainingModule", "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_name": "{module_name}", "due_date": "{due_date}", "assigned_by": "Manager"}, "output_refs": {"assignment_id": "Development plan", "module_name": "Training course", "status": "Assigned"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Training", "function": "RemoveTrainingAssignment"}},
        {"namespace": "HR.Benefits", "function": "EnrollInBenefits", "params": {"employee_id": "{{steps[1].output.employee_id}}", "benefit_type": "{benefit_type}", "coverage_level": "{coverage_level}", "dependents": 2}, "output_refs": {"enrollment_id": "Review period benefits", "status": "Enrolled"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Benefits", "function": "CancelBenefits"}},
        {"namespace": "HR.Performance", "function": "CreateReviewCycle", "params": {"employee_id": "{{steps[1].output.employee_id}}", "review_period": "Q2 2024", "reviewer": "Senior Manager", "rating": 4, "goals": ["Lead team project", "Reduce incident count"]}, "output_refs": {"review_id": "Q2 review", "status": "Review saved"}, "depends_on": [2]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Performance review feedback submission", "priority": "low", "category": "feature-request", "contact_email": "{email}", "account_id": "{{steps[1].output.employee_id}}"}, "output_refs": {"ticket_id": "Review feedback ticket"}, "depends_on": [2]},
    ]
})

# ---------- ADDITIONAL 16 TEMPLATES TO REACH ~46 ----------

# T31: EC2 Compute - Multi-level rollback (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "EC2 Compute", "domain": "Cloud Infrastructure",
    "nl_template": "Deploy critical infrastructure with multi-level rollback: create {group_name} security group, provision {instance_type} EC2, create {bucket_name} bucket, deploy Lambda monitor {function_name}, stop instance, create snapshot bucket, restart instance, verify with alert {alert_name}",
    "actions": [
        {"namespace": "AWS.VPC", "function": "CreateSecurityGroup", "params": {"group_name": "{group_name}", "description": "Critical infra SG", "vpc_id": "{vpc_id}"}, "output_refs": {"group_id": "Infra SG", "group_name": "SG name"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSecurityGroup"}},
        {"namespace": "AWS.EC2", "function": "ProvisionInstance", "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}", "security_group": "{{steps[1].output.group_id}}", "volume_size_gb": 100}, "output_refs": {"instance_id": "Critical instance", "public_ip": "Instance IP"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.EC2", "function": "TerminateInstance"}},
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private", "versioning": True, "encryption": "AES256"}, "output_refs": {"bucket_name": "Snapshots bucket", "bucket_arn": "Bucket ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": "{memory_mb}", "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Monitor function", "function_arn": "Function ARN"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "AWS.EC2", "function": "StopInstance", "params": {"instance_id": "{{steps[2].output.instance_id}}", "hibernate": False}, "output_refs": {"stopped_state": "Stopped for maintenance"}, "depends_on": [2]},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[3].output.bucket_name}}", "object_key": "{object_key}", "content_type": "application/sql", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Snapshot upload", "etag": "Snapshot ETag"}, "depends_on": [3]},
        {"namespace": "AWS.EC2", "function": "StartInstance", "params": {"instance_id": "{{steps[2].output.instance_id}}"}, "output_refs": {"new_public_ip": "New IP after restart"}, "depends_on": [5]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 90.0, "operator": ">", "duration_minutes": 5, "channels": ["pagerduty"], "severity": "critical"}, "output_refs": {"alert_id": "Post-deploy alert"}, "depends_on": [7]},
    ]
})

# T32: S3 Storage - Deep pipeline with IAM (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "S3 Storage", "domain": "Cloud Infrastructure",
    "nl_template": "Build secure analytics storage: create IAM user {user_name} for data access, attach S3 policy {policy_arn}, create encrypted bucket {bucket_name}, upload analytics data, create Lambda processor {function_name}, set up dashboard, and create alert",
    "actions": [
        {"namespace": "AWS.IAM", "function": "CreateUser", "params": {"user_name": "{user_name}", "path": "/service-accounts/"}, "output_refs": {"user_name": "Storage user", "user_arn": "User ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[1].output.user_name}}", "target_type": "user"}, "output_refs": {"policy_arn": "S3 policy", "target_name": "Storage user"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private", "versioning": True, "encryption": "aws:kms"}, "output_refs": {"bucket_name": "Analytics bucket", "bucket_arn": "Bucket ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[3].output.bucket_name}}", "object_key": "{object_key}", "content_type": "text/csv", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Analytics data", "etag": "Data ETag"}, "depends_on": [3]},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "python3.11", "memory_mb": "{memory_mb}", "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Data processor", "function_arn": "Processor ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Storage Used", "Requests", "Cost"], "time_range": "last_7d", "refresh_interval_seconds": 300}, "output_refs": {"dashboard_uid": "Storage dashboard", "url": "Dashboard URL"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "disk_usage_percent", "threshold": 85.0, "operator": ">", "duration_minutes": 10, "channels": ["slack"], "severity": "warning"}, "output_refs": {"alert_id": "Storage alert"}, "depends_on": [3]},
    ]
})

# T33: Lambda Serverless - Event-driven (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Lambda Serverless", "domain": "Cloud Infrastructure",
    "nl_template": "Build event-driven serverless pipeline: create IAM user {user_name} for Lambda, attach policy {policy_arn}, create two Lambda functions {function_name} and {function_name}, invoke the first, set up alerting, create dashboard, and upload event config",
    "actions": [
        {"namespace": "AWS.IAM", "function": "CreateUser", "params": {"user_name": "{user_name}", "path": "/service-accounts/"}, "output_refs": {"user_name": "Lambda user", "user_arn": "User ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[1].output.user_name}}", "target_type": "user"}, "output_refs": {"policy_arn": "Lambda policy", "target_name": "User"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "python3.9", "memory_mb": 512, "timeout_seconds": 60, "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Primary Lambda", "function_arn": "Primary ARN"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "nodejs18.x", "memory_mb": 256, "timeout_seconds": 30, "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Secondary Lambda", "function_arn": "Secondary ARN"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "AWS.Lambda", "function": "InvokeFunction", "params": {"function_name": "{{steps[3].output.function_name}}", "invocation_type": "RequestResponse", "payload": '{"event":"process_order"}'}, "output_refs": {"status_code": "Invoke result", "log_group": "CloudWatch log"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 3.0, "operator": ">", "duration_minutes": 5, "channels": ["slack", "pagerduty"], "severity": "critical"}, "output_refs": {"alert_id": "Lambda error alert"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Invocations", "Duration", "Errors", "Cost"], "time_range": "last_24h", "refresh_interval_seconds": 60}, "output_refs": {"dashboard_uid": "Serverless dashboard", "url": "Dashboard URL"}, "depends_on": [3]},
    ]
})

# T34: RDS Database - Deep pipeline (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "RDS Database", "domain": "Cloud Infrastructure",
    "nl_template": "Build production database stack: create security group {group_name}, launch RDS {engine} database {db_name}, create backup bucket {bucket_name}, upload backup script, set up DB monitoring alert, create replica in different subnet, and verify with dashboard",
    "actions": [
        {"namespace": "AWS.VPC", "function": "CreateSecurityGroup", "params": {"group_name": "{group_name}", "description": "Production DB SG", "vpc_id": "{vpc_id}"}, "output_refs": {"group_id": "DB security group"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSecurityGroup"}},
        {"namespace": "AWS.RDS", "function": "CreateDatabase", "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "{instance_class}", "storage_gb": 200, "multi_az": True, "backup_retention_days": 30}, "output_refs": {"db_instance_id": "Production DB", "endpoint": "DB endpoint", "arn": "DB ARN"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.RDS", "function": "DeleteDatabase"}},
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private", "versioning": True, "encryption": "AES256"}, "output_refs": {"bucket_name": "DB backup bucket", "bucket_arn": "Backup ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[3].output.bucket_name}}", "object_key": "{object_key}", "content_type": "application/sql", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Backup script", "etag": "Script ETag"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 75.0, "operator": ">", "duration_minutes": 10, "channels": ["pagerduty"], "severity": "warning"}, "output_refs": {"alert_id": "DB CPU alert"}, "depends_on": [2]},
        {"namespace": "AWS.VPC", "function": "CreateSubnet", "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}", "map_public_ip": False}, "output_refs": {"subnet_id": "DB replica subnet"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSubnet"}},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "Production DB Dashboard", "panels": ["Connections", "IOPS", "Replication Lag"], "time_range": "last_1h", "refresh_interval_seconds": 30}, "output_refs": {"dashboard_uid": "DB dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
    ]
})

# T35: VPC Networking - Deep pipeline (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "VPC Networking", "domain": "Cloud Infrastructure",
    "nl_template": "Build full VPC network stack: create security group {group_name}, create public subnet {cidr_block}, create private subnet, deploy K8s namespace {namespace} for networking, set up monitoring dashboard, create network alert, and upload network config to S3",
    "actions": [
        {"namespace": "AWS.VPC", "function": "CreateSecurityGroup", "params": {"group_name": "{group_name}", "description": "Network services SG", "vpc_id": "{vpc_id}"}, "output_refs": {"group_id": "VPC SG", "group_name": "SG name"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSecurityGroup"}},
        {"namespace": "AWS.VPC", "function": "CreateSubnet", "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}", "map_public_ip": True}, "output_refs": {"subnet_id": "Public subnet", "cidr_block": "Public CIDR"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSubnet"}},
        {"namespace": "AWS.VPC", "function": "CreateSubnet", "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}", "map_public_ip": False}, "output_refs": {"subnet_id": "Private subnet", "cidr_block": "Private CIDR"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSubnet"}},
        {"namespace": "K8s.Cluster", "function": "CreateNamespace", "params": {"namespace": "{namespace}", "labels": {"tier": "networking"}, "resource_quota_cpu": "10", "resource_quota_memory": "20Gi"}, "output_refs": {"namespace": "Network namespace", "uid": "NS UID"}, "depends_on": [], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteNamespace"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "p99_latency", "threshold": 300.0, "operator": ">", "duration_minutes": 5, "channels": ["pagerduty"], "severity": "critical"}, "output_refs": {"alert_id": "Network latency alert"}, "depends_on": [2]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Throughput", "Latency", "Packet Drops"], "time_range": "last_6h", "refresh_interval_seconds": 60}, "output_refs": {"dashboard_uid": "VPC dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{bucket_name}", "object_key": "{object_key}", "content_type": "application/json", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Network config", "etag": "Config ETag"}, "depends_on": []},
    ]
})

# T36: IAM Security - Cross-account (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "IAM Security", "domain": "Cloud Infrastructure",
    "nl_template": "Establish cross-account security framework: create admin user {user_name}, attach Admin access policy, create service account for CI/CD, attach S3 policy, create bucket {bucket_name} for audit, upload security config, and set up monitoring alert",
    "actions": [
        {"namespace": "AWS.IAM", "function": "CreateUser", "params": {"user_name": "{user_name}", "path": "/developers/"}, "output_refs": {"user_name": "Admin user", "user_arn": "Admin ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "arn:aws:iam::aws:policy/AdministratorAccess", "target_name": "{{steps[1].output.user_name}}", "target_type": "user"}, "output_refs": {"policy_arn": "Admin policy", "target_name": "Admin user"}, "depends_on": [1], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "AWS.IAM", "function": "CreateUser", "params": {"user_name": "{user_name}", "path": "/service-accounts/"}, "output_refs": {"user_name": "CI/CD service user", "user_arn": "CI/CD ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
        {"namespace": "AWS.IAM", "function": "AttachPolicy", "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[3].output.user_name}}", "target_type": "user"}, "output_refs": {"policy_arn": "S3 policy", "target_name": "CI/CD user"}, "depends_on": [3], "rollback_ref": {"namespace": "AWS.IAM", "function": "DetachPolicy"}},
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "bucket-owner-only", "versioning": True, "encryption": "aws:kms"}, "output_refs": {"bucket_name": "Security audit bucket", "bucket_arn": "Audit ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[5].output.bucket_name}}", "object_key": "{object_key}", "content_type": "application/json", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Security config", "etag": "Config ETag"}, "depends_on": [5]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 1.0, "operator": ">", "duration_minutes": 5, "channels": ["email", "pagerduty"], "severity": "critical"}, "output_refs": {"alert_id": "Security alert"}, "depends_on": []},
    ]
})

# T37: Build Pipelines - Multi-stage (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Build Pipelines", "domain": "DevOps/CI-CD",
    "nl_template": "Set up multi-stage build pipeline: create pipeline {pipeline_name} for {repository_url}, create Git branch {branch_name} for feature, trigger build with {commit_hash}, upload build artifact {artifact_name}, create pull request, merge it, and deploy to {target_env}",
    "actions": [
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "main", "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 5}, "output_refs": {"pipeline_id": "Release pipeline", "pipeline_name": "Pipeline name", "webhook_url": "Trigger URL"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Git", "function": "CreateBranch", "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "main"}, "output_refs": {"branch_name": "Release branch", "commit_hash": "Branch HEAD"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Git", "function": "DeleteBranch"}},
        {"namespace": "CI.Build", "function": "TriggerBuild", "params": {"pipeline_name": "{{steps[1].output.pipeline_name}}", "commit_hash": "{commit_hash}", "variables": {"BUILD_ENV": "production"}}, "output_refs": {"build_id": "Build trigger", "status": "Build queued"}, "depends_on": [1]},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "{artifact_name}", "version": "2.0.0", "repository": "docker-hub", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Build artifact", "download_url": "Download URL"}, "depends_on": [3]},
        {"namespace": "CI.Git", "function": "CreatePullRequest", "params": {"repository": "{repository}", "title": "Release v2.0.0", "source_branch": "{{steps[2].output.branch_name}}", "target_branch": "main", "reviewers": ["alice", "bob"]}, "output_refs": {"pr_number": "Release PR", "url": "PR URL"}, "depends_on": [2]},
        {"namespace": "CI.Git", "function": "MergePullRequest", "params": {"repository": "{repository}", "pr_number": "{{steps[5].output.pr_number}}", "merge_method": "merge", "delete_source_branch": True}, "output_refs": {"merge_commit": "Merge SHA", "status": "merged"}, "depends_on": [5]},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[4].output.artifact_id}}", "source_env": "staging", "target_env": "{target_env}", "rollback_strategy": "immediate", "canary_percent": 0}, "output_refs": {"promotion_id": "Production deploy", "deployment_url": "Deploy URL"}, "depends_on": [4], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
    ]
})

# T38: Container Orchestration - Multi-service (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Container Orchestration", "domain": "DevOps/CI-CD",
    "nl_template": "Deploy multi-service Kubernetes stack: create namespace {namespace}, deploy {service_name} with {replicas} replicas, deploy API gateway service, create build pipeline {pipeline_name}, scale user service, create alert {alert_name}, and set up monitoring dashboard",
    "actions": [
        {"namespace": "K8s.Cluster", "function": "CreateNamespace", "params": {"namespace": "{namespace}", "labels": {"env": "production"}, "resource_quota_cpu": "50", "resource_quota_memory": "100Gi"}, "output_refs": {"namespace": "Production namespace", "uid": "NS UUID"}, "depends_on": [], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteNamespace"}},
        {"namespace": "K8s.Cluster", "function": "DeployService", "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "{service_name}", "image": "{image}", "replicas": "{replicas}", "cpu_limit": "2", "memory_limit": "2Gi", "expose_port": 8080}, "output_refs": {"service_name": "User service", "cluster_ip": "Cluster IP", "available_replicas": "Ready replicas"}, "depends_on": [1], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteDeployment"}},
        {"namespace": "K8s.Cluster", "function": "DeployService", "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "api-gateway", "image": "nginx:1.25", "replicas": 3, "cpu_limit": "1", "memory_limit": "1Gi", "expose_port": 443}, "output_refs": {"service_name": "API gateway", "cluster_ip": "Gateway IP", "available_replicas": "Ready"}, "depends_on": [1], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteDeployment"}},
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "main", "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 2}, "output_refs": {"pipeline_id": "K8s build pipeline"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "K8s.Cluster", "function": "ScaleDeployment", "params": {"namespace": "{{steps[1].output.namespace}}", "deployment_name": "{{steps[2].output.service_name}}", "replicas": 10}, "output_refs": {"deployment_name": "Scaled service", "new_replicas": "10"}, "depends_on": [2]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 80.0, "operator": ">", "duration_minutes": 5, "channels": ["slack", "pagerduty"], "severity": "critical"}, "output_refs": {"alert_id": "K8s CPU alert"}, "depends_on": [2]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Pod Status", "Resource Usage", "Service Health"], "time_range": "last_6h", "refresh_interval_seconds": 30}, "output_refs": {"dashboard_uid": "K8s overview", "url": "Dashboard URL"}, "depends_on": [2]},
    ]
})

# T39: Monitoring/Alerts - Observability stack (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Monitoring/Alerts", "domain": "DevOps/CI-CD",
    "nl_template": "Build full observability stack: create critical CPU alert {alert_name}, set up dashboard {dashboard_name} with key metrics, create Lambda monitoring function, upload monitoring config to {bucket_name}, create memory warning alert, generate support ticket for review, and deploy K8s monitoring namespace",
    "actions": [
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 90.0, "operator": ">", "duration_minutes": 5, "channels": ["pagerduty", "slack"], "severity": "critical"}, "output_refs": {"alert_id": "Critical CPU alert"}, "depends_on": [], "rollback_ref": {"namespace": "Ops.Monitoring", "function": "DismissAlert"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "memory_usage", "threshold": 85.0, "operator": ">", "duration_minutes": 10, "channels": ["slack"], "severity": "warning"}, "output_refs": {"alert_id": "Memory warning alert"}, "depends_on": [], "rollback_ref": {"namespace": "Ops.Monitoring", "function": "DismissAlert"}},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["System Health", "Error Rates", "Response Times"], "time_range": "last_24h", "refresh_interval_seconds": 60}, "output_refs": {"dashboard_uid": "Ops dashboard", "url": "Dashboard URL"}, "depends_on": [1]},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "python3.9", "memory_mb": 256, "timeout_seconds": 60, "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Metrics Lambda", "function_arn": "Lambda ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{bucket_name}", "object_key": "{object_key}", "content_type": "application/json", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Monitoring config", "etag": "Config ETag"}, "depends_on": []},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Monitoring review: alert tuning", "priority": "medium", "category": "technical", "contact_email": "{contact_email}", "account_id": "{account_id}"}, "output_refs": {"ticket_id": "Observability ticket"}, "depends_on": [1]},
        {"namespace": "K8s.Cluster", "function": "CreateNamespace", "params": {"namespace": "{namespace}", "labels": {"tier": "monitoring"}, "resource_quota_cpu": "10", "resource_quota_memory": "20Gi"}, "output_refs": {"namespace": "Monitoring K8s NS", "uid": "NS UUID"}, "depends_on": [], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteNamespace"}},
    ]
})

# T40: Deployments - Canary deployment (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Deployments", "domain": "DevOps/CI-CD",
    "nl_template": "Execute canary deployment strategy: create pipeline {pipeline_name} for {repository_url}, trigger build with {commit_hash}, upload artifact {artifact_name}, promote to {target_env} with 10% canary, monitor error rate with alert {alert_name}, scale up on success, and create release branch",
    "actions": [
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}", "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 5}, "output_refs": {"pipeline_id": "Canary pipeline", "pipeline_name": "Pipeline name", "webhook_url": "Webhook URL"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Build", "function": "TriggerBuild", "params": {"pipeline_name": "{{steps[1].output.pipeline_name}}", "commit_hash": "{commit_hash}", "variables": {"BUILD_ENV": "production"}}, "output_refs": {"build_id": "Build execution", "status": "Build status"}, "depends_on": [1]},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "{artifact_name}", "version": "2.3.1", "repository": "docker-hub", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Canary artifact", "download_url": "Download URL"}, "depends_on": [2]},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[3].output.artifact_id}}", "source_env": "staging", "target_env": "{target_env}", "rollback_strategy": "gradual", "canary_percent": 10}, "output_refs": {"promotion_id": "Canary deployment", "deployment_url": "Deploy URL", "status": "promoting"}, "depends_on": [3], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 0.5, "operator": ">", "duration_minutes": 5, "channels": ["pagerduty", "slack"], "severity": "critical"}, "output_refs": {"alert_id": "Canary error alert"}, "depends_on": [4]},
        {"namespace": "K8s.Cluster", "function": "ScaleDeployment", "params": {"namespace": "production", "deployment_name": "{service_name}", "replicas": 20}, "output_refs": {"deployment_name": "Canary scaled", "new_replicas": "20"}, "depends_on": [4]},
        {"namespace": "CI.Git", "function": "CreateBranch", "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "main"}, "output_refs": {"branch_name": "Release branch", "commit_hash": "Branch HEAD"}, "depends_on": []},
    ]
})

# T41: Artifact Management - Multi-env (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Artifact Management", "domain": "DevOps/CI-CD",
    "nl_template": "Manage multi-environment artifacts: upload backend artifact {artifact_name} to {repository}, create build pipeline {pipeline_name}, upload frontend bundle, promote backend to {target_env}, set up monitoring alert {alert_name}, create release branch, and generate support ticket",
    "actions": [
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "{artifact_name}", "version": "3.0.0", "repository": "{repository}", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Backend artifact", "download_url": "Download URL"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Artifacts", "function": "DeleteArtifact"}},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "frontend-bundle.zip", "version": "3.0.0", "repository": "npm-registry", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Frontend artifact", "download_url": "Frontend URL"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Artifacts", "function": "DeleteArtifact"}},
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "main", "build_image": "python:3.11", "timeout_minutes": 30, "concurrent_builds": 2}, "output_refs": {"pipeline_id": "Multi-env pipeline"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[1].output.artifact_id}}", "source_env": "staging", "target_env": "{target_env}", "rollback_strategy": "immediate", "canary_percent": 25}, "output_refs": {"promotion_id": "Backend deploy", "deployment_url": "Service URL"}, "depends_on": [1], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 2.0, "operator": ">", "duration_minutes": 5, "channels": ["slack"], "severity": "warning"}, "output_refs": {"alert_id": "Artifact deploy alert"}, "depends_on": [4]},
        {"namespace": "CI.Git", "function": "CreateBranch", "params": {"repository": "{repository}", "branch_name": "release/3.0.0", "source_branch": "main"}, "output_refs": {"branch_name": "Release branch", "commit_hash": "Branch HEAD"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Git", "function": "DeleteBranch"}},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Artifact version mismatch", "priority": "high", "category": "technical", "contact_email": "{contact_email}", "account_id": "{account_id}"}, "output_refs": {"ticket_id": "Artifact support ticket"}, "depends_on": [1]},
    ]
})

# T42: Git/Version Control - Release management (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Git/Version Control", "domain": "DevOps/CI-CD",
    "nl_template": "Execute release management workflow: create release branch {branch_name} from main, create build pipeline {pipeline_name}, trigger build for release, upload release artifact {artifact_name}, create pull request from release to main, merge with squash, and deploy to {target_env}",
    "actions": [
        {"namespace": "CI.Git", "function": "CreateBranch", "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "main"}, "output_refs": {"branch_name": "Release branch", "commit_hash": "Branch commit"}, "depends_on": [], "rollback_ref": {"namespace": "CI.Git", "function": "DeleteBranch"}},
        {"namespace": "CI.Build", "function": "CreateBuildPipeline", "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{{steps[1].output.branch_name}}", "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 2}, "output_refs": {"pipeline_id": "Release pipeline", "pipeline_name": "Pipeline name"}, "depends_on": [1], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        {"namespace": "CI.Build", "function": "TriggerBuild", "params": {"pipeline_name": "{{steps[2].output.pipeline_name}}", "commit_hash": "{commit_hash}", "variables": {"BUILD_ENV": "production"}}, "output_refs": {"build_id": "Release build", "status": "Build status"}, "depends_on": [2]},
        {"namespace": "CI.Artifacts", "function": "UploadArtifact", "params": {"artifact_name": "{artifact_name}", "version": "release-2024.1", "repository": "docker-hub", "checksum": "{checksum}"}, "output_refs": {"artifact_id": "Release artifact", "download_url": "Download URL"}, "depends_on": [3]},
        {"namespace": "CI.Git", "function": "CreatePullRequest", "params": {"repository": "{repository}", "title": "Release to production", "source_branch": "{{steps[1].output.branch_name}}", "target_branch": "main", "reviewers": ["alice", "bob", "charlie"]}, "output_refs": {"pr_number": "Release PR", "url": "PR URL"}, "depends_on": [1]},
        {"namespace": "CI.Git", "function": "MergePullRequest", "params": {"repository": "{repository}", "pr_number": "{{steps[5].output.pr_number}}", "merge_method": "squash", "delete_source_branch": True}, "output_refs": {"merge_commit": "Merge commit", "status": "merged"}, "depends_on": [5]},
        {"namespace": "CI.Deploy", "function": "PromoteBuild", "params": {"artifact_id": "{{steps[4].output.artifact_id}}", "source_env": "staging", "target_env": "{target_env}", "rollback_strategy": "immediate", "canary_percent": 0}, "output_refs": {"promotion_id": "Final deploy", "deployment_url": "Deploy URL"}, "depends_on": [4], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
    ]
})

# T43: Payment Processing - Subscription-based (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Payment Processing", "domain": "FinTech/Payments",
    "nl_template": "Process subscription payment pipeline: capture initial payment from {customer_id} with {payment_method}, create monthly subscription {plan_name}, generate invoice, send invoice to {customer_email}, run KYC compliance check, capture recurring payment, and create support ticket",
    "actions": [
        {"namespace": "Payments.Processing", "function": "CapturePayment", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "payment_method": "{payment_method}", "description": "Initial subscription fee"}, "output_refs": {"payment_id": "Initial payment", "status": "Payment status", "receipt_url": "Receipt"}, "depends_on": [], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        {"namespace": "Payments.Subscriptions", "function": "CreateSubscription", "params": {"customer_id": "{customer_id}", "plan_name": "{plan_name}", "amount_cents": "{amount_cents}", "currency": "{currency}", "billing_cycle": "monthly", "trial_period_days": 0}, "output_refs": {"subscription_id": "Monthly subscription", "status": "Active", "current_period_end": "Period end"}, "depends_on": [1], "rollback_ref": {"namespace": "Payments.Subscriptions", "function": "CancelSubscription"}},
        {"namespace": "Payments.Invoice", "function": "GenerateInvoice", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "due_date": "{due_date}", "description": "Subscription fee"}, "output_refs": {"invoice_id": "Subscription invoice", "invoice_number": "Invoice"}, "depends_on": [2]},
        {"namespace": "Payments.Invoice", "function": "SendInvoice", "params": {"invoice_id": "{{steps[3].output.invoice_id}}", "customer_email": "{customer_email}", "include_pdf": True, "due_date": "{due_date}"}, "output_refs": {"invoice_id": "Sent invoice", "status": "Delivered"}, "depends_on": [3]},
        {"namespace": "Payments.Compliance", "function": "RunComplianceCheck", "params": {"customer_id": "{customer_id}", "check_type": "kyc", "document_id": "{document_id}", "region": "{region}"}, "output_refs": {"check_id": "KYC check", "status": "Compliance status", "risk_score": "Risk score"}, "depends_on": [1]},
        {"namespace": "Payments.Processing", "function": "CapturePayment", "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}", "payment_method": "{payment_method}", "description": "Recurring subscription payment"}, "output_refs": {"payment_id": "Recurring payment", "status": "Completed"}, "depends_on": [2]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "Subscription billing support", "priority": "medium", "category": "billing", "contact_email": "{customer_email}", "account_id": "{customer_id}"}, "output_refs": {"ticket_id": "Subscription ticket"}, "depends_on": [2]},
    ]
})

# T44: Employee Management - Full HR cycle (8 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Employee Management", "domain": "HR/SaaS Operations",
    "nl_template": "Run complete HR operations cycle: create employee {first_name} {last_name}, generate onboarding checklist, process payroll with {salary_amount} salary, enroll in {benefit_type} benefits, assign {module_name} training, create performance review, process bonus payroll, and create IT support ticket",
    "actions": [
        {"namespace": "HR.Employees", "function": "CreateEmployee", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "department": "{department}", "role": "{role}", "start_date": "{start_date}"}, "output_refs": {"employee_id": "HR employee", "email": "Work email", "department": "Dept"}, "depends_on": [], "rollback_ref": {"namespace": "HR.Employees", "function": "DeleteEmployee"}},
        {"namespace": "HR.Onboarding", "function": "CreateOnboardingChecklist", "params": {"employee_id": "{{steps[1].output.employee_id}}", "items": ["Orientation", "IT Setup", "Benefits", "Compliance Training"], "due_date": "{due_date}", "assigned_to": "HR Coordinator"}, "output_refs": {"checklist_id": "Full onboarding", "status": "Checklist status"}, "depends_on": [1]},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "{pay_period}", "deductions": {"tax": 25, "benefits": 10}, "bonus": 0}, "output_refs": {"payroll_id": "First payroll", "net_amount": "Net salary", "status": "Completed"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        {"namespace": "HR.Benefits", "function": "EnrollInBenefits", "params": {"employee_id": "{{steps[1].output.employee_id}}", "benefit_type": "{benefit_type}", "coverage_level": "{coverage_level}", "dependents": 2}, "output_refs": {"enrollment_id": "Family benefits", "status": "Enrolled", "coverage_start": "Coverage date"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Benefits", "function": "CancelBenefits"}},
        {"namespace": "HR.Training", "function": "AssignTrainingModule", "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_name": "{module_name}", "due_date": "{due_date}", "assigned_by": "Manager"}, "output_refs": {"assignment_id": "Training assignment", "module_name": "Course name", "status": "Assigned"}, "depends_on": [1], "rollback_ref": {"namespace": "HR.Training", "function": "RemoveTrainingAssignment"}},
        {"namespace": "HR.Performance", "function": "CreateReviewCycle", "params": {"employee_id": "{{steps[1].output.employee_id}}", "review_period": "Annual 2024", "reviewer": "Senior Manager", "rating": 4, "goals": ["Meet department targets", "Complete certification"]}, "output_refs": {"review_id": "Annual review", "status": "Review saved"}, "depends_on": [1]},
        {"namespace": "HR.Payroll", "function": "ProcessPayroll", "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_amount": "{salary_amount}", "pay_period": "Q4-2024", "deductions": {"tax": 25, "benefits": 10}, "bonus": 20000}, "output_refs": {"payroll_id": "Bonus payroll", "net_amount": "Bonus net", "status": "Completed"}, "depends_on": [3]},
        {"namespace": "CRM.Support", "function": "CreateTicket", "params": {"subject": "HR system IT access request", "priority": "high", "category": "technical", "contact_email": "{email}", "account_id": "{{steps[1].output.employee_id}}"}, "output_refs": {"ticket_id": "HR IT ticket"}, "depends_on": [1]},
    ]
})

# T45: Sales Analytics - Full reporting (7 steps)
COMPLEX_TEMPLATES.append({
    "sector": "Sales Analytics", "domain": "CRM/Sales",
    "nl_template": "Build sales analytics and reporting pipeline: create S3 bucket {bucket_name} for analytics, upload sales data, create Lambda processor {function_name} with {memory_mb}MB, invoke it to process Q1 data, create dashboard {dashboard_name} with revenue metrics, set up alert {alert_name}, and create leads from campaign data",
    "actions": [
        {"namespace": "AWS.S3", "function": "CreateBucket", "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private", "versioning": True, "encryption": "AES256"}, "output_refs": {"bucket_name": "Analytics bucket", "bucket_arn": "Analytics ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        {"namespace": "AWS.S3", "function": "UploadObject", "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}", "content_type": "text/csv", "storage_class": "STANDARD"}, "output_refs": {"uploaded_key": "Sales data key", "etag": "Data ETag"}, "depends_on": [1]},
        {"namespace": "AWS.Lambda", "function": "CreateFunction", "params": {"function_name": "{function_name}", "runtime": "python3.11", "memory_mb": "{memory_mb}", "timeout_seconds": 120, "role_arn": "{role_arn}"}, "output_refs": {"function_name": "Analytics Lambda", "function_arn": "Analytics ARN"}, "depends_on": [], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
        {"namespace": "AWS.Lambda", "function": "InvokeFunction", "params": {"function_name": "{{steps[3].output.function_name}}", "invocation_type": "RequestResponse", "payload": '{"dataset":"sales_q1_2024"}'}, "output_refs": {"status_code": "Query result", "execution_result": "Analytics output"}, "depends_on": [3]},
        {"namespace": "Ops.Monitoring", "function": "SetUpDashboard", "params": {"dashboard_name": "{dashboard_name}", "panels": ["Revenue Trend", "Lead Sources", "Conversion"], "time_range": "last_30d", "refresh_interval_seconds": 300}, "output_refs": {"dashboard_uid": "Sales analytics dashboard", "url": "Dashboard URL"}, "depends_on": [2]},
        {"namespace": "Ops.Monitoring", "function": "CreateAlertRule", "params": {"alert_name": "{alert_name}", "metric": "error_rate", "threshold": 5.0, "operator": ">", "duration_minutes": 5, "channels": ["slack", "email"], "severity": "warning"}, "output_refs": {"alert_id": "Analytics alert"}, "depends_on": [4]},
        {"namespace": "CRM.Leads", "function": "CreateLead", "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}", "company": "{company}", "source": "website", "score": 50}, "output_refs": {"lead_id": "Campaign lead", "full_name": "Lead name"}, "depends_on": [], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
    ]
})

# =============================================================
# VALIDATION HELPER
# =============================================================
def validate_templates(templates):
    """Validate all templates have correct variable references."""
    all_ok = True
    for i, t in enumerate(templates):
        sector = t.get("sector", "?")
        actions = t.get("actions", [])
        is_valid, errors = _validate_variable_refs(actions)
        if not is_valid:
            print(f"  ❌ Template #{i+1} ({sector}): {errors}")
            all_ok = False
    if all_ok:
        print(f"  ✅ All {len(templates)} templates pass variable reference validation")
    return all_ok


def count_variable_refs(actions):
    """Count {{steps[N].output.key}} references in template actions."""
    count = 0
    for a in actions:
        for pname, pvalue in a.get("params", {}).items():
            if isinstance(pvalue, str):
                count += len(re.findall(r'\{\{steps\[\d+\]\.output\.\w+\}\}', pvalue))
    return count


def count_rollbacks(actions):
    """Count actions with rollback_ref."""
    return sum(1 for a in actions if a.get("rollback_ref"))


# =============================================================
# GENERATION FUNCTION
# =============================================================
def generate_complex_dataset(templates, target_count=500, max_retries=20):
    """Generate complex records from templates using build_sequence_safe."""
    records = []
    template_rngs = {}
    
    # Track template usage
    template_attempts = {i: 0 for i in range(len(templates))}
    template_successes = {i: 0 for i in range(len(templates))}
    
    print(f"\nGenerating {target_count} complex records from {len(templates)} templates...")
    
    # Create round-robin order
    template_order = []
    while len(template_order) < target_count * 2:
        for i in range(len(templates)):
            template_order.append(i)
    
    for attempt_idx in range(target_count * 3):
        if len(records) >= target_count:
            break
        
        t_idx = template_order[attempt_idx % len(template_order)]
        template = templates[t_idx]
        
        if t_idx not in template_rngs:
            template_rngs[t_idx] = random.Random(t_idx * 1000 + 42)
        rng = template_rngs[t_idx]
        
        template_attempts[t_idx] += 1
        
        result, errors = build_sequence_safe(template, rng, max_retries=max_retries)
        
        if result is None:
            rng = random.Random(t_idx * 1000 + attempt_idx + 999)
            result, errors = build_sequence_safe(template, rng, max_retries=max_retries)
            if result is None:
                continue
        
        complexity = result.get("complexity", {})
        if complexity.get("level") != "complex":
            continue
        
        main_steps = [a for a in result.get("actions", []) if not a.get("condition")]
        if len(main_steps) < 7:
            continue
        
        params_for_nl = {}
        for action in result.get("actions", []):
            if not action.get("condition"):
                for pname, pvalue in action.get("params", {}).items():
                    if isinstance(pvalue, (str, int, float, bool)):
                        params_for_nl[pname] = pvalue
        
        nl_input = generate_nl(template["nl_template"], params_for_nl, rng)
        
        record = {
            "input": nl_input,
            "output": {
                "actions": result["actions"],
                "dependencies": result["dependencies"],
                "variable_chain": result["variable_chain"],
                "complexity": result["complexity"],
                "sector": template["sector"],
                "domain": template["domain"]
            }
        }
        
        records.append(record)
        template_successes[t_idx] += 1
        
        if len(records) % 100 == 0:
            print(f"  Generated {len(records)}/{target_count} records...")
    
    print(f"\n  Generation complete: {len(records)} records from {len(templates)} templates")
    
    print("\n  Template contribution stats:")
    for i in range(len(templates)):
        suc = template_successes[i]
        if suc > 0:
            print(f"    #{i+1:2d} ({templates[i]['sector']:30s}): {suc:3d} records")
    
    return records


# =============================================================
# MERGE FUNCTION
# =============================================================
def merge_into_splits(records, train_path, val_path, test_path):
    """Merge complex records into existing splits."""
    import json
    
    splits = {}
    existing_counts = {}
    for name, path in [("train", train_path), ("val", val_path), ("test", test_path)]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = [json.loads(line) for line in f if line.strip()]
            splits[name] = data
            existing_counts[name] = len(data)
            print(f"  {name}: {len(data)} existing records")
        else:
            splits[name] = []
            existing_counts[name] = 0
    
    rng = random.Random(99)
    rng.shuffle(records)
    
    n_train_new = min(400, len(records))
    n_val_new = min(50, len(records) - n_train_new)
    n_test_new = min(50, len(records) - n_train_new - n_val_new)
    
    train_new = records[:n_train_new]
    val_new = records[n_train_new:n_train_new + n_val_new]
    test_new = records[n_train_new + n_val_new:n_train_new + n_val_new + n_test_new]
    
    print(f"\n  Appending: {len(train_new)}→train, {len(val_new)}→val, {len(test_new)}→test")
    
    splits["train"].extend(train_new)
    rng.shuffle(splits["train"])
    splits["val"].extend(val_new)
    rng.shuffle(splits["val"])
    splits["test"].extend(test_new)
    rng.shuffle(splits["test"])
    
    for name, path in [("train", train_path), ("val", val_path), ("test", test_path)]:
        with open(path, 'w') as f:
            for rec in splits[name]:
                f.write(json.dumps(rec) + "\n")
        print(f"  Wrote {len(splits[name])} records to {os.path.basename(path)}")
    
    return len(splits["train"]), len(splits["val"]), len(splits["test"])


# =============================================================
# AUDIT FUNCTION
# =============================================================
def audit_dataset(filepath, label=""):
    """Run a thorough audit on a dataset JSONL file."""
    import json
    
    if not os.path.exists(filepath):
        print(f"\n  {label}: FILE NOT FOUND")
        return None
    
    with open(filepath, 'r') as f:
        records = [json.loads(line) for line in f if line.strip()]
    
    print(f"\n{'='*60}")
    print(f"AUDIT: {label} ({len(records)} records)")
    print(f"{'='*60}")
    
    stats = {
        "total": len(records),
        "complex_level": 0,
        "min_steps": float('inf'),
        "max_steps": 0,
        "avg_steps": 0,
        "has_rollback": 0,
        "has_variable_chain": 0,
        "dangling_refs": 0,
        "sectors": {},
        "domains": {},
        "complexity_scores": [],
    }
    
    for record in records:
        output = record.get("output", {})
        complexity = output.get("complexity", {})
        actions = output.get("actions", [])
        variable_chain = output.get("variable_chain", [])
        sector = output.get("sector", "Unknown")
        domain = output.get("domain", "Unknown")
        
        main_actions = [a for a in actions if not a.get("condition")]
        
        if complexity.get("level") == "complex":
            stats["complex_level"] += 1
        
        n_main = len(main_actions)
        stats["min_steps"] = min(stats["min_steps"], n_main)
        stats["max_steps"] = max(stats["max_steps"], n_main)
        stats["avg_steps"] += n_main
        
        if any(a.get("rollback_ref") or a.get("condition") == "on_failure" for a in actions):
            stats["has_rollback"] += 1
        
        if variable_chain:
            stats["has_variable_chain"] += 1
        
        var_pattern = re.compile(r'\{\{steps\[\d+\]\.output\.\w+\}\}')
        for action in actions:
            for pname, pvalue in action.get("params", {}).items():
                if isinstance(pvalue, str) and var_pattern.search(pvalue):
                    stats["dangling_refs"] += 1
        
        stats["sectors"][sector] = stats["sectors"].get(sector, 0) + 1
        stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
        stats["complexity_scores"].append(complexity.get("score", 0))
    
    if stats["total"] > 0:
        stats["avg_steps"] = stats["avg_steps"] / stats["total"]
    
    print(f"  Complex level: {stats['complex_level']}/{stats['total']} ({stats['complex_level']/max(stats['total'],1)*100:.0f}%)")
    print(f"  Main steps: min={stats['min_steps']}, max={stats['max_steps']}, avg={stats['avg_steps']:.1f}")
    print(f"  With rollback: {stats['has_rollback']}/{stats['total']}")
    print(f"  With variable chain: {stats['has_variable_chain']}/{stats['total']}")
    print(f"  Dangling refs found: {stats['dangling_refs']}")
    
    if stats["complexity_scores"]:
        avg_score = sum(stats["complexity_scores"]) / len(stats["complexity_scores"])
        print(f"  Avg complexity score: {avg_score:.0f}")
    
    print(f"\n  Sector distribution ({len(stats['sectors'])} sectors):")
    for sector, count in sorted(stats["sectors"].items(), key=lambda x: -x[1]):
        print(f"    {sector:30s}: {count:4d}")
    
    print(f"\n  Domain distribution ({len(stats['domains'])} domains):")
    for domain, count in sorted(stats["domains"].items(), key=lambda x: -x[1]):
        print(f"    {domain:25s}: {count:4d}")
    
    return stats


# =============================================================
# MAIN EXECUTION
# =============================================================
def main():
    print("=" * 70)
    print("COMPLEX TEMPLATE EXPANSION")
    print(f"{len(COMPLEX_TEMPLATES)} Templates → 500 Records → Merge → Validate")
    print("=" * 70)
    
    templates = COMPLEX_TEMPLATES
    print(f"\nStep 1: Validating {len(templates)} templates...")
    if not validate_templates(templates):
        print("  ❌ Template validation failed — aborting")
        return 1
    
    # Print template structure stats
    print(f"\n  Template structure verification:")
    for i, t in enumerate(templates):
        n_actions = len(t["actions"])
        n_rollbacks = count_rollbacks(t["actions"])
        n_var = count_variable_refs(t["actions"])
        status = "✅" if (n_actions >= 5 and n_rollbacks >= 3 and n_var >= 4) else "⚠️"
        if status == "⚠️":
            print(f"  {status} #{i+1:2d} {t['sector']:30s} actions={n_actions} rollbacks={n_rollbacks} var_refs={n_var}")
    
    print(f"\nStep 2: Generating 500 complex records...")
    records = generate_complex_dataset(templates, target_count=500, max_retries=20)
    
    if len(records) < 500:
        print(f"  ⚠️ Only generated {len(records)} records (target: 500)")
    
    # Stats on main steps
    step_counts = [len([a for a in r["output"]["actions"] if not a.get("condition")]) for r in records]
    if step_counts:
        print(f"  Main steps: min={min(step_counts)}, max={max(step_counts)}, avg={sum(step_counts)/len(step_counts):.1f}")
    
    with open(OUTPUT_FILE, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    print(f"\n  ✅ Wrote {len(records)} records to {os.path.basename(OUTPUT_FILE)}")
    
    print(f"\nStep 3: Auditing generated complex dataset...")
    audit_dataset(OUTPUT_FILE, "dataset_complex_500.jsonl")
    
    print(f"\nStep 4: Merging into existing splits...")
    train_path = os.path.join(PROJECT_DIR, "dataset_train.jsonl")
    val_path = os.path.join(PROJECT_DIR, "dataset_val.jsonl")
    test_path = os.path.join(PROJECT_DIR, "dataset_test.jsonl")
    
    merge_records = records[:500]
    n_train, n_val, n_test = merge_into_splits(merge_records, train_path, val_path, test_path)
    
    print(f"\n  ✅ Final counts: train={n_train}, val={n_val}, test={n_test}")
    expected = (n_train == 1600, n_val == 200, n_test == 200)
    if all(expected):
        print(f"  ✅ All split counts match expected values!")
    else:
        print(f"  ⚠️ Expected: train=1600, val=200, test=200")
    
    print(f"\nStep 5: Final validation of all merged splits...")
    print(f"\n{'='*70}")
    print("FINAL COMPLEXITY DISTRIBUTION SUMMARY — ALL SPLITS")
    print(f"{'='*70}")
    
    combined = {"total": 0, "complex": 0, "medium": 0, "simple": 0, "scores": []}
    
    for split_name in ["dataset_train.jsonl", "dataset_val.jsonl", "dataset_test.jsonl"]:
        path = os.path.join(PROJECT_DIR, split_name)
        with open(path, 'r') as f:
            recs = [json.loads(line) for line in f if line.strip()]
        for rec in recs:
            c = rec.get("output", {}).get("complexity", {})
            lvl = c.get("level", "unknown")
            sc = c.get("score", 0)
            combined["total"] += 1
            if lvl == "complex": combined["complex"] += 1
            elif lvl == "medium": combined["medium"] += 1
            elif lvl == "simple": combined["simple"] += 1
            combined["scores"].append(sc)
    
    if combined["scores"]:
        combined["avg_score"] = sum(combined["scores"]) / len(combined["scores"])
    
    print(f"\n  Total records: {combined['total']}")
    print(f"  Complex:   {combined['complex']:5d} ({combined['complex']/max(combined['total'],1)*100:.1f}%)")
    print(f"  Medium:    {combined['medium']:5d} ({combined['medium']/max(combined['total'],1)*100:.1f}%)")
    print(f"  Simple:    {combined['simple']:5d} ({combined['simple']/max(combined['total'],1)*100:.1f}%)")
    print(f"  Avg score: {combined.get('avg_score', 0):.0f}")
    
    # Save validation report
    report = {
        "total_templates": len(templates),
        "generated_records": len(records),
        "final_splits": {"train": n_train, "val": n_val, "test": n_test},
        "complexity_distribution": combined,
        "validation_passed": all(expected) and len(records) >= 450
    }
    report_path = os.path.join(PROJECT_DIR, "complex_validation_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n  ✅ Validation report saved to complex_validation_report.json")
    
    print(f"\n{'='*70}")
    print("ALL STEPS COMPLETE")
    print(f"{'='*70}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())