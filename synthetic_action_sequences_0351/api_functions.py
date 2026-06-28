"""
API Function Library — ~95 realistic API functions across 5 domains.
Each function has: namespace, function name, parameter schemas with realistic values,
return type, output_fields. Every "write" function has a paired rollback function.
"""

API_FUNCTIONS = [
    # =========================================================================
    # DOMAIN 1: Cloud Infrastructure (AWS)
    # =========================================================================
    # --- Compute (EC2) ---
    {
        "namespace": "AWS.EC2",
        "function": "ProvisionInstance",
        "description": "Provision a new EC2 instance",
        "params": [
            {"name": "instance_type", "type": "string", "description": "EC2 instance type",
             "values": ["t3.micro", "t3.medium", "t3.large", "m5.large", "m5.xlarge", "c5.2xlarge", "r5.4xlarge"]},
            {"name": "ami_id", "type": "string", "description": "AMI image ID",
             "values": ["ami-0c55b159cbfafe1f0", "ami-0abcdef1234567890", "ami-0ff8a91507f77f867"]},
            {"name": "subnet_id", "type": "string", "description": "VPC subnet",
             "values": ["subnet-abc123", "subnet-def456", "subnet-ghi789", "subnet-jkl012"]},
            {"name": "security_group", "type": "string", "description": "Security group ID",
             "values": ["sg-01020304", "sg-05060708", "sg-09101112"]},
            {"name": "key_name", "type": "string", "description": "SSH key pair name",
             "values": ["prod-key", "staging-key", "dev-key"]},
            {"name": "volume_size_gb", "type": "integer", "description": "EBS volume size in GB",
             "values": [20, 30, 50, 100, 200, 500, 1000]},
        ],
        "return_type": "object",
        "output_fields": {
            "instance_id": "The provisioned EC2 instance ID (e.g., i-0abcd1234)",
            "public_ip": "Public IP address assigned to instance",
            "private_ip": "Private IP address in the VPC",
            "state": "Current state of the instance (running)"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.EC2",
        "function": "TerminateInstance",
        "description": "Terminate an EC2 instance (rollback for ProvisionInstance)",
        "params": [
            {"name": "instance_id", "type": "string", "description": "Instance ID to terminate",
             "values": []},  # Will be populated dynamically
            {"name": "force", "type": "boolean", "description": "Force termination even if running",
             "values": [True, False]},
        ],
        "return_type": "object",
        "output_fields": {
            "instance_id": "The terminated instance ID",
            "termination_time": "Timestamp of termination",
            "state": "Final state (terminated)"
        },
        "rollback_of": "ProvisionInstance"
    },
    {
        "namespace": "AWS.EC2",
        "function": "StopInstance",
        "description": "Stop a running EC2 instance",
        "params": [
            {"name": "instance_id", "type": "string", "description": "Instance ID to stop",
             "values": []},
            {"name": "hibernate", "type": "boolean", "description": "Whether to hibernate",
             "values": [True, False]},
        ],
        "return_type": "object",
        "output_fields": {
            "instance_id": "The stopped instance ID",
            "previous_state": "State before stopping",
            "current_state": "State after stopping (stopped)"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.EC2",
        "function": "StartInstance",
        "description": "Start a stopped EC2 instance",
        "params": [
            {"name": "instance_id", "type": "string", "description": "Instance ID to start",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "instance_id": "The started instance ID",
            "public_ip": "New or existing public IP",
            "state": "Running"
        },
        "rollback_of": "StopInstance"
    },
    # --- Storage (S3) ---
    {
        "namespace": "AWS.S3",
        "function": "CreateBucket",
        "description": "Create an S3 storage bucket",
        "params": [
            {"name": "bucket_name", "type": "string", "description": "Globally unique bucket name",
             "values": ["data-lake-prod", "backup-storage", "logs-archive", "media-assets", "config-store", "artifacts-release"]},
            {"name": "region", "type": "string", "description": "AWS region",
             "values": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-2", "eu-central-1"]},
            {"name": "access_level", "type": "string", "description": "Bucket access level",
             "values": ["private", "public-read", "bucket-owner-only", "authenticated-read"]},
            {"name": "versioning", "type": "boolean", "description": "Enable versioning",
             "values": [True, False]},
            {"name": "encryption", "type": "string", "description": "Encryption type",
             "values": ["AES256", "aws:kms", "none"]},
        ],
        "return_type": "object",
        "output_fields": {
            "bucket_name": "The created bucket name",
            "bucket_arn": "ARN of the bucket",
            "location": "Bucket location/region"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.S3",
        "function": "DeleteBucket",
        "description": "Delete an S3 bucket (rollback complementary to CreateBucket)",
        "params": [
            {"name": "bucket_name", "type": "string", "description": "Bucket name to delete",
             "values": []},
            {"name": "force_delete", "type": "boolean", "description": "Force delete non-empty bucket",
             "values": [True, False]},
        ],
        "return_type": "object",
        "output_fields": {
            "bucket_name": "The deleted bucket name",
            "status": "deleted"
        },
        "rollback_of": "CreateBucket"
    },
    {
        "namespace": "AWS.S3",
        "function": "UploadObject",
        "description": "Upload an object to S3 bucket",
        "params": [
            {"name": "bucket_name", "type": "string", "description": "Target bucket",
             "values": []},
            {"name": "object_key", "type": "string", "description": "Object key/path",
             "values": ["logs/app.log", "backups/db-20230101.sql", "config/prod.json", "media/thumbnail.png", "data/export.csv"]},
            {"name": "content_type", "type": "string", "description": "MIME type",
             "values": ["application/json", "text/plain", "image/png", "text/csv", "application/sql"]},
            {"name": "storage_class", "type": "string", "description": "Storage class",
             "values": ["STANDARD", "INTELLIGENT_TIERING", "GLACIER", "ONEZONE_IA"]},
        ],
        "return_type": "object",
        "output_fields": {
            "object_key": "The uploaded object key",
            "etag": "ETag hash of the uploaded object",
            "version_id": "Version ID if versioning enabled",
            "size_bytes": "Size of uploaded object"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.S3",
        "function": "DeleteObject",
        "description": "Delete an object from S3 (rollback for UploadObject)",
        "params": [
            {"name": "bucket_name", "type": "string", "description": "Bucket containing the object",
             "values": []},
            {"name": "object_key", "type": "string", "description": "Object key to delete",
             "values": []},
            {"name": "version_id", "type": "string", "description": "Specific version to delete",
             "values": ["null", "v1", "v2"]},
        ],
        "return_type": "object",
        "output_fields": {
            "object_key": "The deleted object key",
            "delete_marker": "Whether a delete marker was created",
            "version_id": "Version ID if versioning enabled"
        },
        "rollback_of": "UploadObject"
    },
    # --- Serverless (Lambda) ---
    {
        "namespace": "AWS.Lambda",
        "function": "CreateFunction",
        "description": "Create a Lambda function",
        "params": [
            {"name": "function_name", "type": "string", "description": "Lambda function name",
             "values": ["process-orders", "send-notifications", "image-resizer", "data-validator", "auth-handler", "event-processor"]},
            {"name": "runtime", "type": "string", "description": "Runtime environment",
             "values": ["python3.9", "python3.11", "nodejs18.x", "java11", "go1.x"]},
            {"name": "memory_mb", "type": "integer", "description": "Memory in MB",
             "values": [128, 256, 512, 1024, 2048, 3008]},
            {"name": "timeout_seconds", "type": "integer", "description": "Execution timeout",
             "values": [30, 60, 120, 300, 600]},
            {"name": "role_arn", "type": "string", "description": "IAM role ARN",
             "values": ["arn:aws:iam::123456789012:role/lambda-exec", "arn:aws:iam::123456789012:role/lambda-vpc"]},
        ],
        "return_type": "object",
        "output_fields": {
            "function_name": "The Lambda function name",
            "function_arn": "ARN of the function",
            "version": "Initial version ($LATEST)"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.Lambda",
        "function": "DeleteFunction",
        "description": "Delete a Lambda function (rollback for CreateFunction)",
        "params": [
            {"name": "function_name", "type": "string", "description": "Function name to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "function_name": "The deleted function name",
            "status": "deleted"
        },
        "rollback_of": "CreateFunction"
    },
    {
        "namespace": "AWS.Lambda",
        "function": "InvokeFunction",
        "description": "Invoke a Lambda function",
        "params": [
            {"name": "function_name", "type": "string", "description": "Function to invoke",
             "values": []},
            {"name": "invocation_type", "type": "string", "description": "Invocation type",
             "values": ["RequestResponse", "Event", "DryRun"]},
            {"name": "payload", "type": "object", "description": "JSON payload string",
             "values": ['{"key":"value"}', '{"order_id":"ORD-123"}', '{"event":"test"}']},
        ],
        "return_type": "object",
        "output_fields": {
            "status_code": "HTTP status code (200 on success)",
            "execution_result": "Function execution result payload",
            "log_group": "CloudWatch log group name"
        },
        "rollback_of": None
    },
    # --- Database (RDS) ---
    {
        "namespace": "AWS.RDS",
        "function": "CreateDatabase",
        "description": "Create an RDS database instance",
        "params": [
            {"name": "db_name", "type": "string", "description": "Database name",
             "values": ["appdb", "analytics", "inventory", "userdata", "transactions", "catalog"]},
            {"name": "engine", "type": "string", "description": "Database engine",
             "values": ["postgres", "mysql", "mariadb", "aurora-postgresql"]},
            {"name": "instance_class", "type": "string", "description": "Instance class",
             "values": ["db.t3.micro", "db.t3.medium", "db.r5.large", "db.r5.xlarge"]},
            {"name": "storage_gb", "type": "integer", "description": "Allocated storage GB",
             "values": [20, 50, 100, 200, 500, 1000]},
            {"name": "multi_az", "type": "boolean", "description": "Multi-AZ deployment",
             "values": [True, False]},
            {"name": "backup_retention_days", "type": "integer", "description": "Backup retention period",
             "values": [7, 14, 30, 35]},
        ],
        "return_type": "object",
        "output_fields": {
            "db_instance_id": "The RDS instance identifier",
            "endpoint": "Connection endpoint hostname",
            "port": "Connection port number",
            "arn": "ARN of the database instance"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.RDS",
        "function": "DeleteDatabase",
        "description": "Delete an RDS database instance (rollback for CreateDatabase)",
        "params": [
            {"name": "db_instance_id", "type": "string", "description": "Instance ID to delete",
             "values": []},
            {"name": "skip_final_snapshot", "type": "boolean", "description": "Skip creating final snapshot",
             "values": [True, False]},
            {"name": "final_snapshot_identifier", "type": "string", "description": "Final snapshot name",
             "values": ["final-snap-prod", "final-snap-staging"]},
        ],
        "return_type": "object",
        "output_fields": {
            "db_instance_id": "The deleted instance ID",
            "status": "deleting",
            "final_snapshot": "Final snapshot identifier if created"
        },
        "rollback_of": "CreateDatabase"
    },
    # --- VPC Networking ---
    {
        "namespace": "AWS.VPC",
        "function": "CreateSubnet",
        "description": "Create a VPC subnet",
        "params": [
            {"name": "vpc_id", "type": "string", "description": "VPC ID",
             "values": ["vpc-0a1b2c3d", "vpc-4e5f6g7h", "vpc-8i9j0k1l"]},
            {"name": "cidr_block", "type": "string", "description": "CIDR block",
             "values": ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24", "10.0.10.0/24", "172.16.0.0/24"]},
            {"name": "availability_zone", "type": "string", "description": "Availability zone",
             "values": ["us-east-1a", "us-east-1b", "us-east-1c", "us-west-2a"]},
            {"name": "map_public_ip", "type": "boolean", "description": "Auto-assign public IP",
             "values": [True, False]},
        ],
        "return_type": "object",
        "output_fields": {
            "subnet_id": "The created subnet ID",
            "vpc_id": "Parent VPC ID",
            "cidr_block": "CIDR block of the subnet",
            "availability_zone": "AZ where subnet was created"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.VPC",
        "function": "DeleteSubnet",
        "description": "Delete a VPC subnet (rollback for CreateSubnet)",
        "params": [
            {"name": "subnet_id", "type": "string", "description": "Subnet ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "subnet_id": "The deleted subnet ID",
            "status": "deleted"
        },
        "rollback_of": "CreateSubnet"
    },
    {
        "namespace": "AWS.VPC",
        "function": "CreateSecurityGroup",
        "description": "Create a security group",
        "params": [
            {"name": "group_name", "type": "string", "description": "Security group name",
             "values": ["web-sg", "db-sg", "api-sg", "internal-sg", "admin-sg"]},
            {"name": "description", "type": "string", "description": "Group description",
             "values": ["Web server access", "Database access", "API endpoint access", "Internal service access"]},
            {"name": "vpc_id", "type": "string", "description": "VPC ID",
             "values": ["vpc-0a1b2c3d", "vpc-4e5f6g7h"]},
        ],
        "return_type": "object",
        "output_fields": {
            "group_id": "Security group ID (sg-...)",
            "group_name": "Security group name",
            "vpc_id": "Associated VPC"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.VPC",
        "function": "DeleteSecurityGroup",
        "description": "Delete a security group (rollback for CreateSecurityGroup)",
        "params": [
            {"name": "group_id", "type": "string", "description": "Security group ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "group_id": "The deleted group ID",
            "status": "deleted"
        },
        "rollback_of": "CreateSecurityGroup"
    },
    # --- IAM Security ---
    {
        "namespace": "AWS.IAM",
        "function": "CreateUser",
        "description": "Create an IAM user",
        "params": [
            {"name": "user_name", "type": "string", "description": "IAM user name",
             "values": ["deploy-bot", "ci-service-account", "backup-user", "monitoring-agent", "admin-john"]},
            {"name": "path", "type": "string", "description": "Path for the user",
             "values": ["/", "/service-accounts/", "/developers/", "/system/"]},
        ],
        "return_type": "object",
        "output_fields": {
            "user_name": "Created IAM user name",
            "user_arn": "ARN of the user",
            "user_id": "Unique user ID",
            "create_date": "Creation timestamp"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.IAM",
        "function": "DeleteUser",
        "description": "Delete an IAM user (rollback for CreateUser)",
        "params": [
            {"name": "user_name", "type": "string", "description": "User name to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "user_name": "Deleted user name",
            "status": "deleted"
        },
        "rollback_of": "CreateUser"
    },
    {
        "namespace": "AWS.IAM",
        "function": "AttachPolicy",
        "description": "Attach an IAM policy to a user or role",
        "params": [
            {"name": "policy_arn", "type": "string", "description": "Policy ARN",
             "values": ["arn:aws:iam::aws:policy/AdministratorAccess", "arn:aws:iam::aws:policy/ReadOnlyAccess", "arn:aws:iam::aws:policy/AmazonS3FullAccess"]},
            {"name": "target_name", "type": "string", "description": "User or role name",
             "values": []},
            {"name": "target_type", "type": "string", "description": "Target type",
             "values": ["user", "role", "group"]},
        ],
        "return_type": "object",
        "output_fields": {
            "policy_arn": "Attached policy ARN",
            "target_name": "Entity the policy was attached to",
            "status": "attached"
        },
        "rollback_of": None
    },
    {
        "namespace": "AWS.IAM",
        "function": "DetachPolicy",
        "description": "Detach an IAM policy (rollback for AttachPolicy)",
        "params": [
            {"name": "policy_arn", "type": "string", "description": "Policy ARN to detach",
             "values": []},
            {"name": "target_name", "type": "string", "description": "User or role name",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "policy_arn": "Detached policy ARN",
            "target_name": "Entity policy was detached from",
            "status": "detached"
        },
        "rollback_of": "AttachPolicy"
    },
    # =========================================================================
    # DOMAIN 2: DevOps/CI-CD
    # =========================================================================
    # --- Build Pipelines ---
    {
        "namespace": "CI.Build",
        "function": "CreateBuildPipeline",
        "description": "Create a CI build pipeline",
        "params": [
            {"name": "pipeline_name", "type": "string", "description": "Pipeline name",
             "values": ["frontend-build", "backend-service", "mobile-app", "data-pipeline", "infra-as-code"]},
            {"name": "repository_url", "type": "string", "description": "Git repository URL",
             "values": ["https://github.com/org/frontend", "https://github.com/org/backend-api", "https://github.com/org/data-infra"]},
            {"name": "branch", "type": "string", "description": "Branch to build",
             "values": ["main", "develop", "release/1.0", "staging", "master"]},
            {"name": "build_image", "type": "string", "description": "Build environment image",
             "values": ["ubuntu:22.04", "node:18", "python:3.11", "golang:1.20"]},
            {"name": "timeout_minutes", "type": "integer", "description": "Build timeout",
             "values": [10, 15, 30, 60, 120]},
            {"name": "concurrent_builds", "type": "integer", "description": "Max concurrent builds",
             "values": [1, 2, 5, 10]},
        ],
        "return_type": "object",
        "output_fields": {
            "pipeline_id": "Unique pipeline identifier",
            "pipeline_arn": "ARN of the pipeline",
            "pipeline_name": "Name of the pipeline",
            "webhook_url": "Webhook URL for triggering builds"
        },
        "rollback_of": None
    },
    {
        "namespace": "CI.Build",
        "function": "DeleteBuildPipeline",
        "description": "Delete a CI build pipeline (rollback for CreateBuildPipeline)",
        "params": [
            {"name": "pipeline_name", "type": "string", "description": "Pipeline name to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "pipeline_name": "Deleted pipeline name",
            "status": "deleted"
        },
        "rollback_of": "CreateBuildPipeline"
    },
    {
        "namespace": "CI.Build",
        "function": "TriggerBuild",
        "description": "Trigger a build execution",
        "params": [
            {"name": "pipeline_name", "type": "string", "description": "Pipeline to trigger",
             "values": []},
            {"name": "commit_hash", "type": "string", "description": "Git commit hash",
             "values": ["a1b2c3d4e5f6", "f6e5d4c3b2a1", "0a1b2c3d4e5f", "1a2b3c4d5e6f"]},
            {"name": "variables", "type": "object", "description": "Build variables",
             "values": [{"BUILD_ENV": "production"}, {"BUILD_ENV": "staging"}, {"RELEASE_TAG": "v1.2.3"}]},
        ],
        "return_type": "object",
        "output_fields": {
            "build_id": "Unique build execution ID",
            "pipeline_name": "Pipeline being executed",
            "status": "queued",
            "start_time": "Build start timestamp"
        },
        "rollback_of": None
    },
    # --- Container Orchestration (K8s) ---
    {
        "namespace": "K8s.Cluster",
        "function": "CreateNamespace",
        "description": "Create a Kubernetes namespace",
        "params": [
            {"name": "namespace", "type": "string", "description": "Namespace name",
             "values": ["production", "staging", "development", "monitoring", "logging", "ingress-nginx"]},
            {"name": "labels", "type": "object", "description": "Namespace labels",
             "values": [{"env": "prod"}, {"env": "staging"}, {"env": "dev"}, {"tier": "infrastructure"}]},
            {"name": "resource_quota_cpu", "type": "string", "description": "CPU quota",
             "values": ["10", "20", "50", "100"]},
            {"name": "resource_quota_memory", "type": "string", "description": "Memory quota",
             "values": ["20Gi", "50Gi", "100Gi", "200Gi"]},
        ],
        "return_type": "object",
        "output_fields": {
            "namespace": "Created namespace name",
            "status": "active",
            "uid": "Namespace UUID"
        },
        "rollback_of": None
    },
    {
        "namespace": "K8s.Cluster",
        "function": "DeleteNamespace",
        "description": "Delete a Kubernetes namespace (rollback for CreateNamespace)",
        "params": [
            {"name": "namespace", "type": "string", "description": "Namespace to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "namespace": "Deleted namespace name",
            "status": "terminating"
        },
        "rollback_of": "CreateNamespace"
    },
    {
        "namespace": "K8s.Cluster",
        "function": "DeployService",
        "description": "Deploy a Kubernetes service",
        "params": [
            {"name": "namespace", "type": "string", "description": "Target namespace",
             "values": []},
            {"name": "service_name", "type": "string", "description": "Service name",
             "values": ["api-gateway", "user-service", "order-service", "notification-svc", "payment-svc"]},
            {"name": "image", "type": "string", "description": "Container image",
             "values": ["nginx:1.25", "node:18-alpine", "python:3.11-slim", "golang:1.20", "alpine:3.18"]},
            {"name": "replicas", "type": "integer", "description": "Number of replicas",
             "values": [1, 2, 3, 5, 10]},
            {"name": "cpu_limit", "type": "string", "description": "CPU limit per pod",
             "values": ["500m", "1", "2", "4"]},
            {"name": "memory_limit", "type": "string", "description": "Memory limit per pod",
             "values": ["512Mi", "1Gi", "2Gi", "4Gi"]},
            {"name": "expose_port", "type": "integer", "description": "Container port to expose",
             "values": [80, 443, 3000, 8080, 9090]},
        ],
        "return_type": "object",
        "output_fields": {
            "service_name": "Deployed service name",
            "namespace": "Namespace of service",
            "cluster_ip": "Cluster-internal IP",
            "service_uid": "Service UUID",
            "available_replicas": "Number of ready replicas"
        },
        "rollback_of": None
    },
    {
        "namespace": "K8s.Cluster",
        "function": "ScaleDeployment",
        "description": "Scale a Kubernetes deployment",
        "params": [
            {"name": "namespace", "type": "string", "description": "Namespace",
             "values": []},
            {"name": "deployment_name", "type": "string", "description": "Deployment name",
             "values": ["api-gateway", "user-service", "order-service", "notification-svc"]},
            {"name": "replicas", "type": "integer", "description": "Desired replica count",
             "values": [0, 1, 3, 5, 10, 20]},
        ],
        "return_type": "object",
        "output_fields": {
            "deployment_name": "Scaled deployment name",
            "old_replicas": "Previous replica count",
            "new_replicas": "New replica count",
            "status": "scaling"
        },
        "rollback_of": None
    },
    {
        "namespace": "K8s.Cluster",
        "function": "DeleteDeployment",
        "description": "Delete a Kubernetes deployment (rollback for DeployService)",
        "params": [
            {"name": "namespace", "type": "string", "description": "Namespace",
             "values": []},
            {"name": "deployment_name", "type": "string", "description": "Deployment name to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "deployment_name": "Deleted deployment name",
            "namespace": "Namespace",
            "status": "deleted"
        },
        "rollback_of": "DeployService"
    },
    # --- Monitoring/Alerts ---
    {
        "namespace": "Ops.Monitoring",
        "function": "CreateAlertRule",
        "description": "Create a monitoring alert rule",
        "params": [
            {"name": "alert_name", "type": "string", "description": "Alert name",
             "values": ["HighCPU", "HighMemory", "DiskFull", "LatencySpike", "ErrorRateSpike", "InstanceDown"]},
            {"name": "metric", "type": "string", "description": "Metric to monitor",
             "values": ["cpu_utilization", "memory_usage", "disk_usage_percent", "p99_latency", "error_rate", "uptime"]},
            {"name": "threshold", "type": "float", "description": "Alert threshold value",
             "values": [80.0, 85.0, 90.0, 95.0, 300.0, 500.0, 1000.0]},
            {"name": "operator", "type": "string", "description": "Comparison operator",
             "values": [">", ">=", "<", "<=", "=="]},
            {"name": "duration_minutes", "type": "integer", "description": "Evaluation duration",
             "values": [1, 5, 10, 15, 30]},
            {"name": "channels", "type": "array", "description": "Notification channels",
             "values": [["slack", "email"], ["pagerduty", "slack"], ["email"], ["pagerduty"], ["slack", "teams"]]},
            {"name": "severity", "type": "string", "description": "Alert severity",
             "values": ["critical", "warning", "info", "error"]},
        ],
        "return_type": "object",
        "output_fields": {
            "alert_id": "Unique alert rule ID",
            "alert_name": "Name of the alert rule",
            "status": "active"
        },
        "rollback_of": None
    },
    {
        "namespace": "Ops.Monitoring",
        "function": "DismissAlert",
        "description": "Dismiss an active alert (rollback/complement for CreateAlertRule)",
        "params": [
            {"name": "alert_id", "type": "string", "description": "Alert rule ID to dismiss",
             "values": []},
            {"name": "reason", "type": "string", "description": "Dismissal reason",
             "values": ["Resolved", "False alarm", "Maintenance window", "Acknowledged"]},
        ],
        "return_type": "object",
        "output_fields": {
            "alert_id": "Dismissed alert ID",
            "previous_state": "Previous alert state",
            "current_state": "dismissed",
            "acknowledged_by": "Dismissal authority"
        },
        "rollback_of": "CreateAlertRule"
    },
    {
        "namespace": "Ops.Monitoring",
        "function": "SetUpDashboard",
        "description": "Set up a monitoring dashboard",
        "params": [
            {"name": "dashboard_name", "type": "string", "description": "Dashboard name",
             "values": ["Production Overview", "Service Health", "Infrastructure Metrics", "Business KPIs"]},
            {"name": "panels", "type": "array", "description": "Dashboard panels",
             "values": [["CPU", "Memory", "Disk"], ["Latency", "Throughput", "Errors"], ["Uptime", "Requests", "Saturation"]]},
            {"name": "time_range", "type": "string", "description": "Default time range",
             "values": ["last_1h", "last_6h", "last_24h", "last_7d"]},
            {"name": "refresh_interval_seconds", "type": "integer", "description": "Auto-refresh interval",
             "values": [30, 60, 300, 600]},
        ],
        "return_type": "object",
        "output_fields": {
            "dashboard_uid": "Dashboard unique identifier",
            "dashboard_name": "Dashboard name",
            "url": "Dashboard URL for viewing",
            "version": "Dashboard version"
        },
        "rollback_of": None
    },
    # --- Deployments ---
    {
        "namespace": "CI.Deploy",
        "function": "PromoteBuild",
        "description": "Promote a build artifact to the next environment",
        "params": [
            {"name": "artifact_id", "type": "string", "description": "Build artifact ID",
             "values": ["build-1001", "build-1002", "build-1003", "package-101", "release-2024-01"]},
            {"name": "source_env", "type": "string", "description": "Source environment",
             "values": ["development", "staging", "testing", "qa"]},
            {"name": "target_env", "type": "string", "description": "Target environment",
             "values": ["staging", "production", "qa", "preview"]},
            {"name": "rollback_strategy", "type": "string", "description": "Rollback strategy on failure",
             "values": ["immediate", "gradual", "manual", "none"]},
            {"name": "canary_percent", "type": "integer", "description": "Canary traffic percentage",
             "values": [0, 5, 10, 25, 50, 100]},
        ],
        "return_type": "object",
        "output_fields": {
            "promotion_id": "Promotion request ID",
            "artifact_id": "Promoted artifact",
            "source_env": "Source environment",
            "target_env": "Target environment",
            "deployment_url": "URL of the deployed service",
            "status": "promoting"
        },
        "rollback_of": None
    },
    {
        "namespace": "CI.Deploy",
        "function": "RevertBuild",
        "description": "Revert a build promotion (rollback for PromoteBuild)",
        "params": [
            {"name": "promotion_id", "type": "string", "description": "Promotion ID to revert",
             "values": []},
            {"name": "target_env", "type": "string", "description": "Environment to revert",
             "values": []},
            {"name": "revert_strategy", "type": "string", "description": "Revert strategy",
             "values": ["immediate", "gradual", "phased"]},
        ],
        "return_type": "object",
        "output_fields": {
            "promotion_id": "Reverted promotion ID",
            "previous_artifact": "Previously deployed artifact being restored",
            "target_env": "Environment reverted",
            "status": "reverted"
        },
        "rollback_of": "PromoteBuild"
    },
    # --- Artifact Management ---
    {
        "namespace": "CI.Artifacts",
        "function": "UploadArtifact",
        "description": "Upload a build artifact",
        "params": [
            {"name": "artifact_name", "type": "string", "description": "Artifact name",
             "values": ["app.jar", "frontend-bundle.zip", "docker-image.tar", "lambda-package.zip", "helm-chart.tgz"]},
            {"name": "version", "type": "string", "description": "Artifact version tag",
             "values": ["1.0.0", "2.3.1", "0.9.0-beta", "latest", "release-2024.1"]},
            {"name": "repository", "type": "string", "description": "Artifact repository",
             "values": ["maven-central", "npm-registry", "docker-hub", "pypi", "helm-charts"]},
            {"name": "checksum", "type": "string", "description": "Artifact checksum",
             "values": ["sha256:a1b2c3d4", "sha256:e5f6g7h8", "md5:9i0j1k2l"]},
        ],
        "return_type": "object",
        "output_fields": {
            "artifact_id": "Unique artifact identifier",
            "artifact_name": "Name of the artifact",
            "version": "Version tag",
            "download_url": "URL to download artifact"
        },
        "rollback_of": None
    },
    {
        "namespace": "CI.Artifacts",
        "function": "DeleteArtifact",
        "description": "Delete an artifact from registry (rollback for UploadArtifact)",
        "params": [
            {"name": "artifact_id", "type": "string", "description": "Artifact ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "artifact_id": "Deleted artifact ID",
            "status": "deleted"
        },
        "rollback_of": "UploadArtifact"
    },
    # --- Git/Version Control ---
    {
        "namespace": "CI.Git",
        "function": "CreateBranch",
        "description": "Create a Git branch",
        "params": [
            {"name": "repository", "type": "string", "description": "Repository name",
             "values": ["frontend", "backend-api", "mobile-app", "data-infra", "docs"]},
            {"name": "branch_name", "type": "string", "description": "Branch name",
             "values": ["feature/new-login", "bugfix/null-pointer", "release/2.0", "hotfix/security-patch", "feat/pipeline-optimization"]},
            {"name": "source_branch", "type": "string", "description": "Source branch",
             "values": ["main", "develop", "master", "staging"]},
        ],
        "return_type": "object",
        "output_fields": {
            "branch_name": "Created branch name",
            "repository": "Repository name",
            "commit_hash": "HEAD commit hash on the new branch",
            "source_branch": "Source branch used"
        },
        "rollback_of": None
    },
    {
        "namespace": "CI.Git",
        "function": "DeleteBranch",
        "description": "Delete a Git branch (rollback for CreateBranch)",
        "params": [
            {"name": "repository", "type": "string", "description": "Repository name",
             "values": []},
            {"name": "branch_name", "type": "string", "description": "Branch to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "branch_name": "Deleted branch name",
            "repository": "Repository name",
            "status": "deleted"
        },
        "rollback_of": "CreateBranch"
    },
    {
        "namespace": "CI.Git",
        "function": "CreatePullRequest",
        "description": "Create a pull request",
        "params": [
            {"name": "repository", "type": "string", "description": "Repository name",
             "values": ["frontend", "backend-api", "mobile-app", "data-infra"]},
            {"name": "title", "type": "string", "description": "PR title",
             "values": ["Add login feature", "Fix memory leak", "Update dependencies", "Add API documentation"]},
            {"name": "source_branch", "type": "string", "description": "Source branch",
             "values": []},
            {"name": "target_branch", "type": "string", "description": "Target branch",
             "values": ["main", "develop", "master"]},
            {"name": "reviewers", "type": "array", "description": "Reviewer usernames",
             "values": [["alice", "bob"], ["charlie"], ["diana", "eve", "frank"], ["grace"]]},
        ],
        "return_type": "object",
        "output_fields": {
            "pr_number": "Pull request number",
            "repository": "Repository name",
            "title": "PR title",
            "status": "open",
            "url": "URL to the pull request"
        },
        "rollback_of": None
    },
    {
        "namespace": "CI.Git",
        "function": "MergePullRequest",
        "description": "Merge a pull request",
        "params": [
            {"name": "repository", "type": "string", "description": "Repository",
             "values": []},
            {"name": "pr_number", "type": "integer", "description": "PR number to merge",
             "values": [1, 2, 3, 4, 5]},
            {"name": "merge_method", "type": "string", "description": "Merge strategy",
             "values": ["merge", "squash", "rebase"]},
            {"name": "delete_source_branch", "type": "boolean", "description": "Delete source after merge",
             "values": [True, False]},
        ],
        "return_type": "object",
        "output_fields": {
            "merge_commit": "Merge commit SHA",
            "pr_number": "Merged PR number",
            "repository": "Repository name",
            "status": "merged"
        },
        "rollback_of": None
    },
    # =========================================================================
    # DOMAIN 3: CRM/Sales
    # =========================================================================
    # --- Leads Management ---
    {
        "namespace": "CRM.Leads",
        "function": "CreateLead",
        "description": "Create a new lead record",
        "params": [
            {"name": "first_name", "type": "string", "description": "Lead first name",
             "values": ["John", "Sarah", "Michael", "Emma", "David", "Lisa", "James", "Maria"]},
            {"name": "last_name", "type": "string", "description": "Lead last name",
             "values": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]},
            {"name": "email", "type": "string", "description": "Email address",
             "values": ["john@acme.com", "sarah@techcorp.io", "mike@startup.co", "emma@enterprise.com"]},
            {"name": "company", "type": "string", "description": "Company name",
             "values": ["Acme Corp", "TechCorp", "Innovate.io", "Enterprise Inc", "DataFlow Ltd"]},
            {"name": "source", "type": "string", "description": "Lead source",
             "values": ["website", "referral", "linkedin", "conference", "cold-outreach", "partner"]},
            {"name": "score", "type": "integer", "description": "Lead score 1-100",
             "values": [20, 35, 50, 65, 80, 95]},
        ],
        "return_type": "object",
        "output_fields": {
            "lead_id": "Unique lead identifier",
            "full_name": "Lead full name",
            "email": "Lead email",
            "company": "Lead company",
            "score": "Lead score assigned",
            "created_date": "Creation timestamp"
        },
        "rollback_of": None
    },
    {
        "namespace": "CRM.Leads",
        "function": "DeleteLead",
        "description": "Delete a lead record (rollback for CreateLead)",
        "params": [
            {"name": "lead_id", "type": "string", "description": "Lead ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "lead_id": "Deleted lead ID",
            "status": "deleted"
        },
        "rollback_of": "CreateLead"
    },
    {
        "namespace": "CRM.Leads",
        "function": "QualifyLead",
        "description": "Qualify a lead with BANT criteria",
        "params": [
            {"name": "lead_id", "type": "string", "description": "Lead ID to qualify",
             "values": []},
            {"name": "budget_available", "type": "boolean", "description": "Has budget",
             "values": [True, False]},
            {"name": "authority_level", "type": "string", "description": "Decision-maker authority",
             "values": ["user", "manager", "director", "vp", "c-level"]},
            {"name": "timeline", "type": "string", "description": "Purchase timeline",
             "values": ["immediate", "1-3 months", "3-6 months", "6-12 months", "exploring"]},
        ],
        "return_type": "object",
        "output_fields": {
            "lead_id": "Qualified lead ID",
            "qualification_score": "Overall qualification score",
            "bant_status": "BANT criteria status",
            "recommended_action": "Suggested next step"
        },
        "rollback_of": None
    },
    # --- Opportunities ---
    {
        "namespace": "CRM.Opportunity",
        "function": "CreateOpportunity",
        "description": "Create a sales opportunity",
        "params": [
            {"name": "opportunity_name", "type": "string", "description": "Opportunity name",
             "values": ["Enterprise License Deal", "SaaS Subscription - Q1", "Consulting Engagement", "Platform Migration", "Data Analytics Package"]},
            {"name": "amount", "type": "float", "description": "Deal amount in USD",
             "values": [10000.0, 25000.0, 50000.0, 75000.0, 100000.0, 250000.0, 500000.0]},
            {"name": "stage", "type": "string", "description": "Sales stage",
             "values": ["prospecting", "qualification", "demo", "proposal", "negotiation", "closed_won"]},
            {"name": "probability", "type": "integer", "description": "Win probability %",
             "values": [10, 25, 50, 75, 90]},
            {"name": "lead_id", "type": "string", "description": "Associated lead ID",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "opportunity_id": "Unique opportunity identifier",
            "opportunity_name": "Name of the opportunity",
            "amount": "Deal amount",
            "stage": "Current sales stage",
            "close_date": "Expected close date"
        },
        "rollback_of": None
    },
    {
        "namespace": "CRM.Opportunity",
        "function": "DeleteOpportunity",
        "description": "Delete an opportunity (rollback for CreateOpportunity)",
        "params": [
            {"name": "opportunity_id", "type": "string", "description": "Opportunity ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "opportunity_id": "Deleted opportunity ID",
            "status": "deleted"
        },
        "rollback_of": "CreateOpportunity"
    },
    {
        "namespace": "CRM.Opportunity",
        "function": "UpdateOpportunityStage",
        "description": "Update opportunity sales stage",
        "params": [
            {"name": "opportunity_id", "type": "string", "description": "Opportunity ID",
             "values": []},
            {"name": "new_stage", "type": "string", "description": "New sales stage",
             "values": ["qualification", "demo", "proposal", "negotiation", "closed_won", "closed_lost"]},
            {"name": "reason", "type": "string", "description": "Reason for stage change",
             "values": ["Product demo completed", "Proposal delivered", "Budget approved", "Competitor selected"]},
        ],
        "return_type": "object",
        "output_fields": {
            "opportunity_id": "Updated opportunity ID",
            "previous_stage": "Previous stage",
            "current_stage": "Current stage",
            "updated_date": "Update timestamp"
        },
        "rollback_of": None
    },
    # --- Campaigns ---
    {
        "namespace": "CRM.Campaigns",
        "function": "CreateCampaign",
        "description": "Create a marketing campaign",
        "params": [
            {"name": "campaign_name", "type": "string", "description": "Campaign name",
             "values": ["Summer Sale 2024", "Product Launch Q1", "Holiday Promotion", "Webinar Series", "Email Nurture Flow", "Partner Referral Program"]},
            {"name": "type", "type": "string", "description": "Campaign type",
             "values": ["email", "social", "webinar", "content", "paid-ad", "event"]},
            {"name": "budget", "type": "float", "description": "Campaign budget USD",
             "values": [5000.0, 10000.0, 25000.0, 50000.0, 100000.0]},
            {"name": "target_audience", "type": "string", "description": "Target audience segment",
             "values": ["enterprise", "mid-market", "startups", "existing-customers", "all"]},
            {"name": "start_date", "type": "string", "description": "Campaign start",
             "values": ["2024-01-15", "2024-02-01", "2024-03-01", "2024-04-10", "2024-06-01"]},
        ],
        "return_type": "object",
        "output_fields": {
            "campaign_id": "Unique campaign identifier",
            "campaign_name": "Campaign name",
            "type": "Campaign type",
            "budget": "Allocated budget",
            "status": "draft"
        },
        "rollback_of": None
    },
    {
        "namespace": "CRM.Campaigns",
        "function": "DeleteCampaign",
        "description": "Delete a marketing campaign (rollback for CreateCampaign)",
        "params": [
            {"name": "campaign_id", "type": "string", "description": "Campaign ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "campaign_id": "Deleted campaign ID",
            "status": "deleted"
        },
        "rollback_of": "CreateCampaign"
    },
    {
        "namespace": "CRM.Campaigns",
        "function": "LaunchCampaign",
        "description": "Launch a campaign to active state",
        "params": [
            {"name": "campaign_id", "type": "string", "description": "Campaign ID",
             "values": []},
            {"name": "launch_channels", "type": "array", "description": "Channels to launch on",
             "values": [["email", "linkedin"], ["twitter", "google-ads"], ["webinar", "email"], ["all"]]},
        ],
        "return_type": "object",
        "output_fields": {
            "campaign_id": "Launched campaign ID",
            "status": "active",
            "launch_date": "Launch timestamp",
            "active_channels": "Channels now active"
        },
        "rollback_of": None
    },
    # --- Contacts/Accounts ---
    {
        "namespace": "CRM.Accounts",
        "function": "CreateAccount",
        "description": "Create a customer account",
        "params": [
            {"name": "account_name", "type": "string", "description": "Company/account name",
             "values": ["Acme Corporation", "GlobalTech Solutions", "DataStream Inc", "CloudNine Services", "Quantum Analytics", "Apex Innovations"]},
            {"name": "industry", "type": "string", "description": "Industry vertical",
             "values": ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Education"]},
            {"name": "size_employees", "type": "integer", "description": "Employee count",
             "values": [50, 200, 500, 1000, 5000, 10000]},
            {"name": "tier", "type": "string", "description": "Account tier",
             "values": ["basic", "standard", "premium", "enterprise"]},
        ],
        "return_type": "object",
        "output_fields": {
            "account_id": "Unique account identifier",
            "account_name": "Account name",
            "tier": "Account service tier",
            "created_date": "Creation timestamp"
        },
        "rollback_of": None
    },
    {
        "namespace": "CRM.Accounts",
        "function": "DeleteAccount",
        "description": "Delete a customer account (rollback for CreateAccount)",
        "params": [
            {"name": "account_id", "type": "string", "description": "Account ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "account_id": "Deleted account ID",
            "status": "deleted"
        },
        "rollback_of": "CreateAccount"
    },
    # --- Quotes/Orders ---
    {
        "namespace": "CRM.Orders",
        "function": "CreateQuote",
        "description": "Create a sales quote",
        "params": [
            {"name": "opportunity_id", "type": "string", "description": "Associated opportunity",
             "values": []},
            {"name": "product", "type": "string", "description": "Product or service",
             "values": ["Enterprise License", "SaaS Subscription", "Professional Services", "Support Package", "Training Bundle"]},
            {"name": "quantity", "type": "integer", "description": "Quantity",
             "values": [1, 5, 10, 25, 50, 100, 500]},
            {"name": "unit_price", "type": "float", "description": "Unit price USD",
             "values": [99.0, 199.0, 499.0, 999.0, 1999.0, 4999.0, 9999.0]},
            {"name": "discount_percent", "type": "integer", "description": "Discount percentage",
             "values": [0, 5, 10, 15, 20, 25]},
        ],
        "return_type": "object",
        "output_fields": {
            "quote_id": "Unique quote identifier",
            "total_amount": "Total amount after discount",
            "product": "Quoted product",
            "status": "draft",
            "expiry_date": "Quote expiry date"
        },
        "rollback_of": None
    },
    {
        "namespace": "CRM.Orders",
        "function": "DeleteQuote",
        "description": "Delete a sales quote (rollback for CreateQuote)",
        "params": [
            {"name": "quote_id", "type": "string", "description": "Quote ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "quote_id": "Deleted quote ID",
            "status": "deleted"
        },
        "rollback_of": "CreateQuote"
    },
    {
        "namespace": "CRM.Orders",
        "function": "ConvertQuoteToOrder",
        "description": "Convert a quote to a sales order",
        "params": [
            {"name": "quote_id", "type": "string", "description": "Quote ID to convert",
             "values": []},
            {"name": "payment_terms", "type": "string", "description": "Payment terms",
             "values": ["net-30", "net-15", "due-on-receipt", "net-60"]},
            {"name": "shipping_method", "type": "string", "description": "Shipping method",
             "values": ["digital-delivery", "express", "standard", "pickup"]},
        ],
        "return_type": "object",
        "output_fields": {
            "order_id": "New order identifier",
            "quote_id": "Source quote ID",
            "order_total": "Order total amount",
            "status": "confirmed",
            "estimated_delivery": "Estimated delivery date"
        },
        "rollback_of": None
    },
    # --- Customer Service ---
    {
        "namespace": "CRM.Support",
        "function": "CreateTicket",
        "description": "Create a support ticket",
        "params": [
            {"name": "subject", "type": "string", "description": "Ticket subject",
             "values": ["Cannot login to dashboard", "Billing discrepancy", "Feature request: export API", "Performance degradation", "Account access issue"]},
            {"name": "priority", "type": "string", "description": "Priority level",
             "values": ["low", "medium", "high", "critical"]},
            {"name": "category", "type": "string", "description": "Issue category",
             "values": ["billing", "technical", "account", "feature-request", "bug"]},
            {"name": "contact_email", "type": "string", "description": "Contact email",
             "values": ["support@acme.com", "help@techcorp.io"]},
            {"name": "account_id", "type": "string", "description": "Customer account ID",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "ticket_id": "Unique ticket identifier (TKT-...)",
            "subject": "Ticket subject",
            "priority": "Assigned priority",
            "status": "open",
            "created_at": "Creation timestamp"
        },
        "rollback_of": None
    },
    {
        "namespace": "CRM.Support",
        "function": "CloseTicket",
        "description": "Close a support ticket",
        "params": [
            {"name": "ticket_id", "type": "string", "description": "Ticket ID to close",
             "values": []},
            {"name": "resolution", "type": "string", "description": "Resolution notes",
             "values": ["Issue resolved", "User education provided", "Bug fix deployed", "Known limitation"]},
            {"name": "satisfaction_score", "type": "integer", "description": "CSAT score 1-5",
             "values": [1, 2, 3, 4, 5]},
        ],
        "return_type": "object",
        "output_fields": {
            "ticket_id": "Closed ticket ID",
            "resolution": "Resolution summary",
            "status": "closed",
            "closed_at": "Close timestamp",
            "satisfaction_score": "Customer satisfaction score"
        },
        "rollback_of": None
    },
    # =========================================================================
    # DOMAIN 4: FinTech/Payments
    # =========================================================================
    # --- Payment Processing ---
    {
        "namespace": "Payments.Processing",
        "function": "CapturePayment",
        "description": "Capture a payment from customer",
        "params": [
            {"name": "customer_id", "type": "string", "description": "Customer identifier",
             "values": ["cus_abc123", "cus_def456", "cus_ghi789", "cus_jkl012", "cus_mno345"]},
            {"name": "amount_cents", "type": "integer", "description": "Amount in cents",
             "values": [999, 1999, 4999, 9999, 14999, 29999, 99999]},
            {"name": "currency", "type": "string", "description": "Currency code",
             "values": ["USD", "EUR", "GBP", "CAD", "AUD"]},
            {"name": "payment_method", "type": "string", "description": "Payment method",
             "values": ["credit_card", "debit_card", "ach", "wire", "crypto"]},
            {"name": "description", "type": "string", "description": "Payment description",
             "values": ["Monthly subscription", "One-time purchase", "Invoice payment", "Service fee", "Deposit"]},
        ],
        "return_type": "object",
        "output_fields": {
            "payment_id": "Unique payment transaction ID (pi_...)",
            "customer_id": "Customer charged",
            "amount_cents": "Amount charged",
            "currency": "Currency",
            "status": "completed",
            "charge_fee_cents": "Processing fee charged",
            "receipt_url": "URL to payment receipt"
        },
        "rollback_of": None
    },
    {
        "namespace": "Payments.Processing",
        "function": "RefundPayment",
        "description": "Refund a captured payment (rollback for CapturePayment)",
        "params": [
            {"name": "payment_id", "type": "string", "description": "Payment ID to refund",
             "values": []},
            {"name": "amount_cents", "type": "integer", "description": "Amount to refund (0 = full)",
             "values": [0, 999, 4999, 9999]},
            {"name": "reason", "type": "string", "description": "Refund reason",
             "values": ["customer_request", "duplicate_charge", "product_return", "service_cancellation", "fraud_suspicion"]},
        ],
        "return_type": "object",
        "output_fields": {
            "refund_id": "Unique refund identifier (rf_...)",
            "payment_id": "Original payment ID",
            "amount_cents": "Refunded amount",
            "status": "completed"
        },
        "rollback_of": "CapturePayment"
    },
    {
        "namespace": "Payments.Processing",
        "function": "AuthorizePayment",
        "description": "Authorize a payment (hold funds)",
        "params": [
            {"name": "customer_id", "type": "string", "description": "Customer identifier",
             "values": ["cus_abc123", "cus_def456", "cus_ghi789"]},
            {"name": "amount_cents", "type": "integer", "description": "Amount to authorize",
             "values": [5000, 10000, 25000, 50000]},
            {"name": "currency", "type": "string", "description": "Currency",
             "values": ["USD", "EUR", "GBP"]},
            {"name": "payment_method", "type": "string", "description": "Payment method",
             "values": ["credit_card", "debit_card"]},
        ],
        "return_type": "object",
        "output_fields": {
            "authorization_id": "Authorization hold ID (auth_...)",
            "amount_cents": "Amount on hold",
            "currency": "Currency",
            "status": "authorized",
            "expires_at": "Hold expiration timestamp"
        },
        "rollback_of": None
    },
    # --- Invoicing/Billing ---
    {
        "namespace": "Payments.Invoicing",
        "function": "CreateInvoice",
        "description": "Create a customer invoice",
        "params": [
            {"name": "customer_id", "type": "string", "description": "Customer ID",
             "values": ["cus_abc123", "cus_def456", "cus_ghi789", "cus_jkl012"]},
            {"name": "line_items", "type": "array", "description": "Invoice line items",
             "values": [
                 [{"description": "Monthly subscription", "amount": 9999}],
                 [{"description": "Setup fee", "amount": 5000}, {"description": "Monthly license", "amount": 29999}],
                 [{"description": "Consulting hours", "amount": 15000}, {"description": "Training", "amount": 5000}]
             ]},
            {"name": "due_date", "type": "string", "description": "Payment due date",
             "values": ["2024-01-15", "2024-02-01", "2024-02-15", "2024-03-01", "2024-03-15"]},
            {"name": "tax_rate_percent", "type": "float", "description": "Tax rate",
             "values": [0.0, 5.0, 8.5, 10.0, 13.0, 20.0]},
            {"name": "currency", "type": "string", "description": "Currency",
             "values": ["USD", "EUR", "GBP", "CAD"]},
        ],
        "return_type": "object",
        "output_fields": {
            "invoice_id": "Invoice identifier (inv_...)",
            "customer_id": "Customer billing ID",
            "total_cents": "Total amount in cents",
            "status": "pending",
            "invoice_pdf_url": "URL to invoice PDF",
            "due_date": "Payment due date"
        },
        "rollback_of": None
    },
    {
        "namespace": "Payments.Invoicing",
        "function": "VoidInvoice",
        "description": "Void a pending invoice (rollback for CreateInvoice)",
        "params": [
            {"name": "invoice_id", "type": "string", "description": "Invoice ID to void",
             "values": []},
            {"name": "reason", "type": "string", "description": "Void reason",
             "values": ["customer_request", "duplicate_entry", "incorrect_amount"]},
        ],
        "return_type": "object",
        "output_fields": {
            "invoice_id": "Voided invoice ID",
            "previous_status": "Status before voiding",
            "status": "voided"
        },
        "rollback_of": "CreateInvoice"
    },
    {
        "namespace": "Payments.Invoicing",
        "function": "SendInvoice",
        "description": "Send an invoice to customer",
        "params": [
            {"name": "invoice_id", "type": "string", "description": "Invoice ID to send",
             "values": []},
            {"name": "delivery_method", "type": "string", "description": "Delivery method",
             "values": ["email", "portal", "mail", "edi"]},
            {"name": "cc_emails", "type": "array", "description": "CC email addresses",
             "values": [["finance@company.com"], ["admin@company.com", "billing@company.com"]]},
        ],
        "return_type": "object",
        "output_fields": {
            "invoice_id": "Sent invoice ID",
            "sent_at": "Send timestamp",
            "status": "sent",
            "delivery_method": "How it was sent"
        },
        "rollback_of": None
    },
    # --- Account Management ---
    {
        "namespace": "Payments.Accounts",
        "function": "CreateAccount",
        "description": "Create a payment account",
        "params": [
            {"name": "owner_name", "type": "string", "description": "Account owner name",
             "values": ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Ross", "Edward Chen"]},
            {"name": "account_type", "type": "string", "description": "Account type",
             "values": ["checking", "savings", "merchant", "escrow"]},
            {"name": "initial_deposit_cents", "type": "integer", "description": "Initial deposit in cents",
             "values": [0, 50000, 100000, 500000, 1000000]},
            {"name": "branch_code", "type": "string", "description": "Branch identifier",
             "values": ["BR001", "BR002", "BR003", "NYC001", "LON001"]},
            {"name": "currency", "type": "string", "description": "Account currency",
             "values": ["USD", "EUR", "GBP", "CHF", "JPY"]},
        ],
        "return_type": "object",
        "output_fields": {
            "account_id": "Account identifier (acct_...)",
            "account_number": "Masked account number",
            "owner_name": "Account owner",
            "balance_cents": "Current balance",
            "status": "active"
        },
        "rollback_of": None
    },
    {
        "namespace": "Payments.Accounts",
        "function": "CloseAccount",
        "description": "Close a payment account (rollback for CreateAccount)",
        "params": [
            {"name": "account_id", "type": "string", "description": "Account ID to close",
             "values": []},
            {"name": "transfer_remaining", "type": "boolean", "description": "Transfer remaining balance",
             "values": [True, False]},
        ],
        "return_type": "object",
        "output_fields": {
            "account_id": "Closed account ID",
            "final_balance_cents": "Final balance",
            "status": "closed"
        },
        "rollback_of": "CreateAccount"
    },
    {
        "namespace": "Payments.Accounts",
        "function": "TransferFunds",
        "description": "Transfer funds between accounts",
        "params": [
            {"name": "source_account_id", "type": "string", "description": "Source account",
             "values": []},
            {"name": "destination_account_id", "type": "string", "description": "Destination account",
             "values": []},
            {"name": "amount_cents", "type": "integer", "description": "Amount in cents",
             "values": [50000, 100000, 250000, 500000, 1000000, 5000000]},
            {"name": "memo", "type": "string", "description": "Transfer memo",
             "values": ["Monthly settlement", "Invoice payment", "Fund allocation", "Profit distribution", "Loan disbursement"]},
        ],
        "return_type": "object",
        "output_fields": {
            "transfer_id": "Transfer transaction ID",
            "source_account": "Source account ID",
            "destination_account": "Destination account ID",
            "amount_cents": "Amount transferred",
            "status": "completed",
            "completion_time": "Transfer timestamp"
        },
        "rollback_of": None
    },
    # --- Fraud Detection ---
    {
        "namespace": "Payments.Fraud",
        "function": "FlagTransaction",
        "description": "Flag a transaction as potentially fraudulent",
        "params": [
            {"name": "transaction_id", "type": "string", "description": "Transaction ID to flag",
             "values": []},
            {"name": "risk_score", "type": "integer", "description": "Risk score 1-100",
             "values": [25, 40, 55, 70, 85, 95]},
            {"name": "flags", "type": "array", "description": "Risk indicators",
             "values": [["unusual_location", "large_amount"], ["velocity_check"], ["new_device", "high_risk_country"], ["amount_mismatch"]]},
            {"name": "review_priority", "type": "string", "description": "Review priority",
             "values": ["low", "medium", "high", "immediate"]},
        ],
        "return_type": "object",
        "output_fields": {
            "flag_id": "Fraud flag identifier",
            "transaction_id": "Flagged transaction",
            "risk_score": "Assigned risk score",
            "status": "under_review"
        },
        "rollback_of": None
    },
    {
        "namespace": "Payments.Fraud",
        "function": "ClearFlag",
        "description": "Clear a fraud flag (rollback for FlagTransaction)",
        "params": [
            {"name": "flag_id", "type": "string", "description": "Flag ID to clear",
             "values": []},
            {"name": "review_result", "type": "string", "description": "Review conclusion",
             "values": ["legitimate", "false_positive", "confirmed_fraud_reported"]},
            {"name": "reviewer_notes", "type": "string", "description": "Reviewer notes",
             "values": ["Customer verified identity", "Transaction matches usual pattern", "IP matched known location"]},
        ],
        "return_type": "object",
        "output_fields": {
            "flag_id": "Cleared flag ID",
            "previous_risk_score": "Previous risk score",
            "status": "cleared",
            "reviewed_by": "Reviewer identifier"
        },
        "rollback_of": "FlagTransaction"
    },
    # --- Reporting/Analytics ---
    {
        "namespace": "Payments.Reporting",
        "function": "GenerateReport",
        "description": "Generate a financial report",
        "params": [
            {"name": "report_type", "type": "string", "description": "Report type",
             "values": ["daily_summary", "monthly_statement", "revenue_by_product", "chargeback_report", "settlement_report", "tax_summary"]},
            {"name": "start_date", "type": "string", "description": "Report start date",
             "values": ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"]},
            {"name": "end_date", "type": "string", "description": "Report end date",
             "values": ["2024-01-31", "2024-02-28", "2024-03-31", "2024-04-30"]},
            {"name": "format", "type": "string", "description": "Output format",
             "values": ["csv", "pdf", "xlsx", "json"]},
            {"name": "group_by", "type": "string", "description": "Grouping dimension",
             "values": ["day", "week", "month", "product", "region"]},
        ],
        "return_type": "object",
        "output_fields": {
            "report_id": "Report identifier (rpt_...)",
            "report_type": "Type of report",
            "download_url": "URL to download report",
            "record_count": "Number of records in report",
            "generated_at": "Generation timestamp"
        },
        "rollback_of": None
    },

    {
        "namespace": "Payments.Reporting",
        "function": "DeleteReport",
        "description": "Delete a generated report (rollback for GenerateReport)",
        "params": [
            {"name": "report_id", "type": "string", "description": "Report ID to delete",
             "values": []}
        ],
        "return_type": "object",
        "output_fields": {
            "status": "deleted"
        },
        "rollback_of": "GenerateReport"
    },
    # --- Compliance/KYC ---
    {
        "namespace": "Payments.Compliance",
        "function": "SubmitKYC",
        "description": "Submit KYC documents for verification",
        "params": [
            {"name": "customer_id", "type": "string", "description": "Customer ID",
             "values": ["cus_abc123", "cus_def456", "cus_ghi789"]},
            {"name": "document_type", "type": "string", "description": "Document type",
             "values": ["passport", "drivers_license", "national_id", "utility_bill"]},
            {"name": "country", "type": "string", "description": "Country of residence",
             "values": ["US", "UK", "DE", "CA", "AU", "SG"]},
            {"name": "verification_level", "type": "string", "description": "Verification level",
             "values": ["basic", "standard", "enhanced", "full"]},
        ],
        "return_type": "object",
        "output_fields": {
            "kyc_id": "KYC submission identifier",
            "customer_id": "Customer under verification",
            "status": "submitted",
            "estimated_completion": "Estimated verification time"
        },
        "rollback_of": None
    },
    {
        "namespace": "Payments.Compliance",
        "function": "ApproveKYC",
        "description": "Approve KYC verification",
        "params": [
            {"name": "kyc_id", "type": "string", "description": "KYC submission ID",
             "values": []},
            {"name": "notes", "type": "string", "description": "Approval notes",
             "values": ["Documents verified", "Identity confirmed", "All checks passed"]},
        ],
        "return_type": "object",
        "output_fields": {
            "kyc_id": "Approved KYC ID",
            "customer_id": "Verified customer",
            "status": "approved",
            "verification_level": "Assigned verification level"
        },
        "rollback_of": None
    },
    {
        "namespace": "Payments.Compliance",
        "function": "RejectKYC",
        "description": "Reject KYC verification (rollback for ApproveKYC)",
        "params": [
            {"name": "kyc_id", "type": "string", "description": "KYC submission ID",
             "values": []},
            {"name": "reason", "type": "string", "description": "Rejection reason",
             "values": ["document_expired", "identity_mismatch", "fraud_suspicion", "incomplete_submission"]},
        ],
        "return_type": "object",
        "output_fields": {
            "kyc_id": "Rejected KYC ID",
            "customer_id": "Customer ID",
            "status": "rejected",
            "reason": "Rejection reason"
        },
        "rollback_of": "ApproveKYC"
    },
    # =========================================================================
    # DOMAIN 5: HR/SaaS Operations
    # =========================================================================
    # --- Employee Onboarding ---
    {
        "namespace": "HR.Onboarding",
        "function": "CreateEmployeeProfile",
        "description": "Create a new employee profile",
        "params": [
            {"name": "first_name", "type": "string", "description": "Employee first name",
             "values": ["Alice", "Bob", "Carol", "Dan", "Eve", "Frank", "Grace", "Henry"]},
            {"name": "last_name", "type": "string", "description": "Employee last name",
             "values": ["Anderson", "Baker", "Clark", "Davis", "Evans", "Foster", "Green", "Hill"]},
            {"name": "department", "type": "string", "description": "Department",
             "values": ["Engineering", "Marketing", "Sales", "Finance", "HR", "Operations", "Design", "Legal"]},
            {"name": "job_title", "type": "string", "description": "Job title",
             "values": ["Software Engineer", "Product Manager", "Sales Rep", "Data Analyst", "UX Designer", "DevOps Engineer"]},
            {"name": "employment_type", "type": "string", "description": "Employment type",
             "values": ["full-time", "part-time", "contract", "intern"]},
            {"name": "start_date", "type": "string", "description": "Start date",
             "values": ["2024-01-08", "2024-02-01", "2024-03-04", "2024-04-01", "2024-06-03"]},
        ],
        "return_type": "object",
        "output_fields": {
            "employee_id": "Unique employee ID (EMP-...)",
            "full_name": "Employee full name",
            "email": "Work email address",
            "department": "Department assigned",
            "job_title": "Job title",
            "start_date": "Employment start date"
        },
        "rollback_of": None
    },
    {
        "namespace": "HR.Onboarding",
        "function": "TerminateEmployee",
        "description": "Terminate an employee (rollback for CreateEmployeeProfile)",
        "params": [
            {"name": "employee_id", "type": "string", "description": "Employee ID to terminate",
             "values": []},
            {"name": "termination_type", "type": "string", "description": "Termination type",
             "values": ["voluntary", "involuntary", "retirement", "end_of_contract"]},
            {"name": "effective_date", "type": "string", "description": "Termination effective date",
             "values": ["2024-01-15", "2024-02-01", "2024-03-01"]},
            {"name": "severance_weeks", "type": "integer", "description": "Severance weeks",
             "values": [0, 2, 4, 8, 12]},
        ],
        "return_type": "object",
        "output_fields": {
            "employee_id": "Terminated employee ID",
            "final_working_date": "Last working day",
            "status": "terminated",
            "severance_amount": "Severance payment amount"
        },
        "rollback_of": "CreateEmployeeProfile"
    },
    {
        "namespace": "HR.Onboarding",
        "function": "AssignEquipment",
        "description": "Assign equipment to an employee",
        "params": [
            {"name": "employee_id", "type": "string", "description": "Employee ID",
             "values": []},
            {"name": "equipment_type", "type": "string", "description": "Equipment type",
             "values": ["laptop", "monitor", "keyboard", "phone", "headset", "docking_station"]},
            {"name": "equipment_model", "type": "string", "description": "Equipment model",
             "values": ["MacBook Pro 16", "Dell Latitude 5540", "ThinkPad X1 Carbon", "HP EliteBook 840"]},
            {"name": "asset_tag", "type": "string", "description": "Asset tag number",
             "values": ["AST-001", "AST-002", "AST-003", "AST-004", "AST-005"]},
        ],
        "return_type": "object",
        "output_fields": {
            "asset_id": "Asset assignment identifier",
            "employee_id": "Employee assigned",
            "equipment_type": "Type of equipment",
            "equipment_model": "Model assigned",
            "assignment_date": "Assignment date"
        },
        "rollback_of": None
    },
    # --- Payroll ---
    {
        "namespace": "HR.Payroll",
        "function": "ProcessPayroll",
        "description": "Process payroll for a period",
        "params": [
            {"name": "pay_period_start", "type": "string", "description": "Period start date",
             "values": ["2024-01-01", "2024-01-15", "2024-02-01", "2024-02-15"]},
            {"name": "pay_period_end", "type": "string", "description": "Period end date",
             "values": ["2024-01-15", "2024-01-31", "2024-02-15", "2024-02-29"]},
            {"name": "department_filter", "type": "string", "description": "Department filter",
             "values": ["all", "Engineering", "Sales", "Executive", "Operations"]},
            {"name": "include_bonuses", "type": "boolean", "description": "Include bonus payments",
             "values": [True, False]},
            {"name": "overtime_rate", "type": "float", "description": "Overtime multiplier",
             "values": [1.0, 1.5, 2.0]},
        ],
        "return_type": "object",
        "output_fields": {
            "payroll_id": "Payroll run identifier",
            "period": "Pay period covered",
            "total_gross_cents": "Total gross pay in cents",
            "total_net_cents": "Total net pay in cents",
            "employee_count": "Number of employees paid",
            "status": "processed",
            "pay_date": "Scheduled pay date"
        },
        "rollback_of": None
    },
    {
        "namespace": "HR.Payroll",
        "function": "ReversePayroll",
        "description": "Reverse a processed payroll (rollback for ProcessPayroll)",
        "params": [
            {"name": "payroll_id", "type": "string", "description": "Payroll ID to reverse",
             "values": []},
            {"name": "reason", "type": "string", "description": "Reversal reason",
             "values": ["error_correction", "duplicate_run", "incorrect_calculations"]},
        ],
        "return_type": "object",
        "output_fields": {
            "payroll_id": "Reversed payroll ID",
            "previous_total_cents": "Previously disbursed amount",
            "status": "reversed",
            "reversal_date": "Reversal timestamp"
        },
        "rollback_of": "ProcessPayroll"
    },
    {
        "namespace": "HR.Payroll",
        "function": "SetCompensation",
        "description": "Set employee compensation",
        "params": [
            {"name": "employee_id", "type": "string", "description": "Employee ID",
             "values": []},
            {"name": "salary_annual_cents", "type": "integer", "description": "Annual salary in cents",
             "values": [8000000, 10000000, 12000000, 15000000, 18000000, 22000000, 25000000]},
            {"name": "currency", "type": "string", "description": "Currency",
             "values": ["USD", "EUR", "GBP"]},
            {"name": "effective_date", "type": "string", "description": "Effective date",
             "values": ["2024-01-01", "2024-02-01", "2024-04-01", "2024-07-01"]},
        ],
        "return_type": "object",
        "output_fields": {
            "compensation_id": "Compensation record ID",
            "employee_id": "Employee ID",
            "annual_salary_cents": "Annual salary",
            "effective_date": "Effective from date",
            "status": "active"
        },
        "rollback_of": None
    },
    # --- Performance Reviews ---
    {
        "namespace": "HR.Performance",
        "function": "CreateReviewCycle",
        "description": "Create a performance review cycle",
        "params": [
            {"name": "cycle_name", "type": "string", "description": "Review cycle name",
             "values": ["Q1 2024 Review", "Q2 2024 Review", "Annual 2024 Review", "Mid-Year 2024"]},
            {"name": "review_period_start", "type": "string", "description": "Review period start",
             "values": ["2024-01-01", "2024-04-01", "2024-07-01", "2024-01-01"]},
            {"name": "review_period_end", "type": "string", "description": "Review period end",
             "values": ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"]},
            {"name": "rating_scale", "type": "string", "description": "Rating scale type",
             "values": ["1-5", "1-10", "meets-exceeds", "three-tier"]},
            {"name": "include_self_review", "type": "boolean", "description": "Include self-assessment",
             "values": [True, False]},
            {"name": "include_peer_review", "type": "boolean", "description": "Include 360 feedback",
             "values": [True, False]},
        ],
        "return_type": "object",
        "output_fields": {
            "cycle_id": "Review cycle identifier",
            "cycle_name": "Name of the cycle",
            "status": "open",
            "deadline": "Review submission deadline"
        },
        "rollback_of": None
    },
    {
        "namespace": "HR.Performance",
        "function": "CloseReviewCycle",
        "description": "Close a performance review cycle (rollback for CreateReviewCycle)",
        "params": [
            {"name": "cycle_id", "type": "string", "description": "Cycle ID to close",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "cycle_id": "Closed review cycle ID",
            "previous_status": "Previous status",
            "status": "closed",
            "completion_rate": "Percentage of reviews completed"
        },
        "rollback_of": "CreateReviewCycle"
    },
    {
        "namespace": "HR.Performance",
        "function": "SubmitReview",
        "description": "Submit a performance review for an employee",
        "params": [
            {"name": "cycle_id", "type": "string", "description": "Review cycle ID",
             "values": []},
            {"name": "employee_id", "type": "string", "description": "Employee being reviewed",
             "values": []},
            {"name": "reviewer_id", "type": "string", "description": "Reviewer employee ID",
             "values": []},
            {"name": "rating", "type": "integer", "description": "Overall rating",
             "values": [1, 2, 3, 4, 5]},
            {"name": "comments", "type": "string", "description": "Review comments",
             "values": ["Exceeds expectations in all areas", "Solid performance, room for growth", "Needs improvement in key areas", "Outstanding contribution this quarter"]},
        ],
        "return_type": "object",
        "output_fields": {
            "review_id": "Review submission ID",
            "employee_id": "Reviewed employee",
            "cycle_id": "Review cycle",
            "rating": "Assigned rating",
            "status": "submitted"
        },
        "rollback_of": None
    },
    # --- Leave Management ---
    {
        "namespace": "HR.Leave",
        "function": "SubmitLeaveRequest",
        "description": "Submit a leave request",
        "params": [
            {"name": "employee_id", "type": "string", "description": "Employee ID",
             "values": []},
            {"name": "leave_type", "type": "string", "description": "Type of leave",
             "values": ["annual", "sick", "personal", "maternity", "paternity", "bereavement"]},
            {"name": "start_date", "type": "string", "description": "Leave start date",
             "values": ["2024-01-22", "2024-02-12", "2024-03-11", "2024-04-15", "2024-05-06"]},
            {"name": "end_date", "type": "string", "description": "Leave end date",
             "values": ["2024-01-26", "2024-02-16", "2024-03-15", "2024-04-19", "2024-05-10"]},
            {"name": "reason", "type": "string", "description": "Leave reason",
             "values": ["Vacation", "Family event", "Medical appointment", "Personal matters"]},
        ],
        "return_type": "object",
        "output_fields": {
            "leave_id": "Leave request identifier (LV-...)",
            "employee_id": "Employee on leave",
            "leave_type": "Type of leave",
            "days_requested": "Number of days",
            "status": "pending",
            "submitted_at": "Submission timestamp"
        },
        "rollback_of": None
    },
    {
        "namespace": "HR.Leave",
        "function": "ApproveLeave",
        "description": "Approve a leave request",
        "params": [
            {"name": "leave_id", "type": "string", "description": "Leave request ID",
             "values": []},
            {"name": "approved_by", "type": "string", "description": "Manager employee ID",
             "values": []},
            {"name": "notes", "type": "string", "description": "Approval notes",
             "values": ["Approved", "Enjoy your time off", "Coverage arranged"]},
        ],
        "return_type": "object",
        "output_fields": {
            "leave_id": "Approved leave request ID",
            "status": "approved",
            "approved_by": "Approver",
            "approved_at": "Approval timestamp"
        },
        "rollback_of": None
    },
    {
        "namespace": "HR.Leave",
        "function": "CancelLeaveRequest",
        "description": "Cancel a leave request (rollback for SubmitLeaveRequest)",
        "params": [
            {"name": "leave_id", "type": "string", "description": "Leave request ID",
             "values": []},
            {"name": "cancellation_reason", "type": "string", "description": "Cancellation reason",
             "values": ["Change of plans", "Work requirements", "Health recovered"]},
        ],
        "return_type": "object",
        "output_fields": {
            "leave_id": "Cancelled leave ID",
            "previous_status": "Status before cancellation",
            "status": "cancelled"
        },
        "rollback_of": "SubmitLeaveRequest"
    },
    # --- Recruiting ---
    {
        "namespace": "HR.Recruiting",
        "function": "CreateJobPosting",
        "description": "Create a job posting",
        "params": [
            {"name": "job_title", "type": "string", "description": "Job title",
             "values": ["Senior Software Engineer", "Product Designer", "Marketing Manager", "Data Scientist", "DevOps Lead", "Sales Director"]},
            {"name": "department", "type": "string", "description": "Department",
             "values": ["Engineering", "Design", "Marketing", "Data", "Operations", "Sales"]},
            {"name": "location", "type": "string", "description": "Job location",
             "values": ["San Francisco, CA", "New York, NY", "London, UK", "Remote - US", "Berlin, DE", "Sydney, AU"]},
            {"name": "employment_type", "type": "string", "description": "Employment type",
             "values": ["full-time", "part-time", "contract", "internship"]},
            {"name": "salary_range_min", "type": "integer", "description": "Min salary",
             "values": [80000, 100000, 120000, 150000, 180000]},
            {"name": "salary_range_max", "type": "integer", "description": "Max salary",
             "values": [120000, 150000, 180000, 220000, 250000]},
        ],
        "return_type": "object",
        "output_fields": {
            "posting_id": "Job posting identifier (JOB-...)",
            "job_title": "Position title",
            "status": "published",
            "application_url": "URL to apply",
            "posted_date": "Posting date"
        },
        "rollback_of": None
    },
    {
        "namespace": "HR.Recruiting",
        "function": "CloseJobPosting",
        "description": "Close a job posting (rollback for CreateJobPosting)",
        "params": [
            {"name": "posting_id", "type": "string", "description": "Posting ID to close",
             "values": []},
            {"name": "reason", "type": "string", "description": "Closure reason",
             "values": ["position_filled", "position_cancelled", "position_on_hold"]},
        ],
        "return_type": "object",
        "output_fields": {
            "posting_id": "Closed posting ID",
            "previous_status": "Previous status",
            "status": "closed"
        },
        "rollback_of": "CreateJobPosting"
    },
    {
        "namespace": "HR.Recruiting",
        "function": "ScheduleInterview",
        "description": "Schedule a candidate interview",
        "params": [
            {"name": "candidate_name", "type": "string", "description": "Candidate full name",
             "values": ["Alex Thompson", "Jordan Lee", "Morgan Patel", "Taylor Williams", "Casey Kim"]},
            {"name": "posting_id", "type": "string", "description": "Job posting ID",
             "values": []},
            {"name": "interview_date", "type": "string", "description": "Interview date/time",
             "values": ["2024-01-20T10:00:00", "2024-01-22T14:00:00", "2024-01-25T09:00:00", "2024-02-01T11:00:00"]},
            {"name": "interview_type", "type": "string", "description": "Interview type",
             "values": ["phone_screen", "technical", "behavioral", "panel", "take_home"]},
            {"name": "interviewers", "type": "array", "description": "Interviewer employee IDs",
             "values": [["EMP-001", "EMP-002"], ["EMP-003"], ["EMP-001", "EMP-004", "EMP-005"]]},
        ],
        "return_type": "object",
        "output_fields": {
            "interview_id": "Interview identifier",
            "candidate_name": "Candidate name",
            "job_title": "Position applied for",
            "interview_date": "Scheduled date/time",
            "status": "scheduled",
            "calendar_event_url": "Calendar invite URL"
        },
        "rollback_of": None
    },
    # --- Training ---
    {
        "namespace": "HR.Training",
        "function": "CreateTrainingModule",
        "description": "Create a training module",
        "params": [
            {"name": "module_name", "type": "string", "description": "Training module name",
             "values": ["Security Awareness", "AWS Fundamentals", "Leadership Skills", "Data Privacy GDPR", "Agile Methodology", "Diversity & Inclusion"]},
            {"name": "category", "type": "string", "description": "Module category",
             "values": ["compliance", "technical", "soft_skills", "leadership", "onboarding"]},
            {"name": "duration_hours", "type": "float", "description": "Estimated duration in hours",
             "values": [1.0, 2.0, 4.0, 8.0, 16.0]},
            {"name": "required_for_all", "type": "boolean", "description": "Mandatory for all employees",
             "values": [True, False]},
            {"name": "certification_available", "type": "boolean", "description": "Offers certification",
             "values": [True, False]},
        ],
        "return_type": "object",
        "output_fields": {
            "module_id": "Training module identifier (TRN-...)",
            "module_name": "Module name",
            "category": "Training category",
            "status": "published",
            "enrollment_url": "URL to enroll"
        },
        "rollback_of": None
    },
    {
        "namespace": "HR.Training",
        "function": "DeleteTrainingModule",
        "description": "Delete a training module (rollback for CreateTrainingModule)",
        "params": [
            {"name": "module_id", "type": "string", "description": "Module ID to delete",
             "values": []},
        ],
        "return_type": "object",
        "output_fields": {
            "module_id": "Deleted module ID",
            "status": "deleted"
        },
        "rollback_of": "CreateTrainingModule"
    },
    {
        "namespace": "HR.Training",
        "function": "EnrollEmployee",
        "description": "Enroll an employee in training",
        "params": [
            {"name": "employee_id", "type": "string", "description": "Employee ID",
             "values": []},
            {"name": "module_id", "type": "string", "description": "Training module ID",
             "values": []},
            {"name": "due_date", "type": "string", "description": "Completion due date",
             "values": ["2024-02-15", "2024-03-01", "2024-03-31", "2024-06-30"]},
        ],
        "return_type": "object",
        "output_fields": {
            "enrollment_id": "Enrollment record ID",
            "employee_id": "Employee enrolled",
            "module_id": "Training module",
            "status": "enrolled",
            "progress_percent": "Initial progress (0)"
        },
        "rollback_of": None
    },
    {
        "namespace": "HR.Training",
        "function": "CompleteTraining",
        "description": "Mark training as completed",
        "params": [
            {"name": "enrollment_id", "type": "string", "description": "Enrollment ID",
             "values": []},
            {"name": "score", "type": "integer", "description": "Assessment score percent",
             "values": [60, 70, 80, 85, 90, 95, 100]},
            {"name": "feedback", "type": "string", "description": "Employee feedback",
             "values": ["Very helpful training", "Good content", "Could be more practical", "Excellent course"]},
        ],
        "return_type": "object",
        "output_fields": {
            "enrollment_id": "Completed enrollment ID",
            "status": "completed",
            "score": "Assessment score",
            "completed_at": "Completion timestamp",
            "certificate_url": "Certificate URL if applicable"
        },
        "rollback_of": None
    },
]

# Verify count
assert len(API_FUNCTIONS) >= 85, f"Expected >=85 API functions, got {len(API_FUNCTIONS)}"

# Build lookup maps
FUNCTION_MAP = {f["function"]: f for f in API_FUNCTIONS}

ROLLBACK_MAP = {}
for func in API_FUNCTIONS:
    if func["rollback_of"]:
        ROLLBACK_MAP[func["rollback_of"]] = func["function"]