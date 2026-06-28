"""
Action Template System — 204 templates across 30 sub-sectors (5 domains × 6 sectors each).
Each template has: sector, domain, nl_template with {placeholders}, actions list.
Requirements per sector:
  - At least 2 templates with rollback/compensation paths
  - At least 1 template with variable passing ({{steps[].output.<key>}} references)
"""

TEMPLATES = []

# ===========================================================================
# DOMAIN 1: Cloud Infrastructure
# ===========================================================================
# --- Sector 1: EC2 Compute ---
domain_c1 = "Cloud Infrastructure"
TEMPLATES.extend([
    # Template 1: Simple provision (3 steps, no variable passing)
    {
        "sector": "EC2 Compute",
        "domain": domain_c1,
        "nl_template": "Provision a {instance_type} instance using AMI {ami_id} in subnet {subnet_id} with {volume_size_gb}GB storage",
        "actions": [
            {"namespace": "AWS.EC2", "function": "ProvisionInstance",
             "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}",
                        "security_group": "{security_group}", "volume_size_gb": "{volume_size_gb}"},
             "output_refs": {"instance_id": "The provisioned instance ID", "public_ip": "Assigned public IP"},
             "depends_on": []},
            {"namespace": "AWS.EC2", "function": "StopInstance",
             "params": {"instance_id": "{{steps[1].output.instance_id}}", "hibernate": "{hibernate}"},
             "output_refs": {"stopped_state": "Current state after stop"},
             "depends_on": [1]},
        ]
    },
    # Template 2: Provision with rollback (variable passing)
    {
        "sector": "EC2 Compute",
        "domain": domain_c1,
        "nl_template": "Create an EC2 {instance_type} instance for {environment} environment and set up auto-shutdown at night",
        "actions": [
            {"namespace": "AWS.EC2", "function": "ProvisionInstance",
             "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}",
                        "security_group": "{security_group}", "volume_size_gb": "{volume_size_gb}"},
             "output_refs": {"instance_id": "The provisioned instance", "public_ip": "Public IP"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.EC2", "function": "TerminateInstance"}},
            {"namespace": "AWS.EC2", "function": "StopInstance",
             "params": {"instance_id": "{{steps[1].output.instance_id}}", "hibernate": "{hibernate}"},
             "output_refs": {"stopped_state": "Current state"},
             "depends_on": [1]},
        ]
    },
    # Template 3: Full workflow with start/stop (variable passing)
    {
        "sector": "EC2 Compute",
        "domain": domain_c1,
        "nl_template": "Provision {instance_type} in subnet {subnet_id}, stop it, then start it again for maintenance",
        "actions": [
            {"namespace": "AWS.EC2", "function": "ProvisionInstance",
             "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}",
                        "security_group": "{security_group}", "volume_size_gb": "{volume_size_gb}"},
             "output_refs": {"instance_id": "The provisioned instance"},
             "depends_on": []},
            {"namespace": "AWS.EC2", "function": "StopInstance",
             "params": {"instance_id": "{{steps[1].output.instance_id}}", "hibernate": "{hibernate}"},
             "output_refs": {"was_stopped": "State after stop"},
             "depends_on": [1]},
            {"namespace": "AWS.EC2", "function": "StartInstance",
             "params": {"instance_id": "{{steps[1].output.instance_id}}"},
             "output_refs": {"new_public_ip": "Public IP after restart"},
             "depends_on": [2]},
        ]
    },
    # Template 4: Provision with security group (rollback)
    {
        "sector": "EC2 Compute",
        "domain": domain_c1,
        "nl_template": "Create a security group for {group_name} and launch {instance_type} in {subnet_id}",
        "actions": [
            {"namespace": "AWS.VPC", "function": "CreateSecurityGroup",
             "params": {"group_name": "{group_name}", "description": "{sg_description}", "vpc_id": "{vpc_id}"},
             "output_refs": {"group_id": "Created security group ID"},
             "depends_on": []},
            {"namespace": "AWS.EC2", "function": "ProvisionInstance",
             "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}",
                        "security_group": "{{steps[1].output.group_id}}", "volume_size_gb": "{volume_size_gb}"},
             "output_refs": {"instance_id": "Provisioned instance"},
             "depends_on": [1]},
        ]
    },
    # Template 5: Multi-instance with rollback
    {
        "sector": "EC2 Compute",
        "domain": domain_c1,
        "nl_template": "Set up a {instance_type} instance group in {subnet_id} with monitored rollback in case of failure",
        "actions": [
            {"namespace": "AWS.EC2", "function": "ProvisionInstance",
             "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}",
                        "security_group": "{security_group}", "volume_size_gb": "{volume_size_gb}"},
             "output_refs": {"instance_id": "Primary instance ID", "public_ip": "Primary public IP"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.EC2", "function": "TerminateInstance"}},
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "{alert_name}", "metric": "cpu_utilization", "threshold": 90.0,
                        "operator": ">", "duration_minutes": 5, "channels": ["slack"], "severity": "critical"},
             "output_refs": {"alert_id": "Alert rule ID"},
             "depends_on": [1]},
        ]
    },
    # Template 6: Provision → terminate rollback path
    {
        "sector": "EC2 Compute",
        "domain": domain_c1,
        "nl_template": "Launch a {instance_type} spot instance, configure it, and store the setup. With automatic cleanup on failure.",
        "actions": [
            {"namespace": "AWS.EC2", "function": "ProvisionInstance",
             "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}",
                        "security_group": "{security_group}", "volume_size_gb": "{volume_size_gb}"},
             "output_refs": {"instance_id": "Spot instance ID", "private_ip": "Private IP"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.EC2", "function": "TerminateInstance"}},
            {"namespace": "AWS.IAM", "function": "AttachPolicy",
             "params": {"policy_arn": "{policy_arn}", "target_name": "{target_name}", "target_type": "role"},
             "output_refs": {"attached_policy": "Attached policy ARN"},
             "depends_on": [1]},
        ]
    },
    # Template 7: Provision, stop, terminate (rollback chain)
    {
        "sector": "EC2 Compute",
        "domain": domain_c1,
        "nl_template": "Provision a {instance_type} instance, stop it for patching, and terminate when patching is done",
        "actions": [
            {"namespace": "AWS.EC2", "function": "ProvisionInstance",
             "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}", "subnet_id": "{subnet_id}",
                        "security_group": "{security_group}", "volume_size_gb": "{volume_size_gb}"},
             "output_refs": {"instance_id": "Instance to patch"},
             "depends_on": []},
            {"namespace": "AWS.EC2", "function": "StopInstance",
             "params": {"instance_id": "{{steps[1].output.instance_id}}", "hibernate": False},
             "output_refs": {"stopped_id": "Stopped instance"},
             "depends_on": [1]},
            {"namespace": "AWS.EC2", "function": "TerminateInstance",
             "params": {"instance_id": "{{steps[1].output.instance_id}}", "force": True},
             "output_refs": {"termination_state": "Termination state"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 2: S3 Storage ---
TEMPLATES.extend([
    # Template 1: Create bucket with versioning
    {
        "sector": "S3 Storage",
        "domain": domain_c1,
        "nl_template": "Create an S3 bucket named {bucket_name} in {region} with versioning and {encryption} encryption",
        "actions": [
            {"namespace": "AWS.S3", "function": "CreateBucket",
             "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "{access_level}",
                        "versioning": "{versioning}", "encryption": "{encryption}"},
             "output_refs": {"bucket_name": "Created bucket name", "bucket_arn": "Bucket ARN"},
             "depends_on": []},
        ]
    },
    # Template 2: Create bucket, upload object (variable passing)
    {
        "sector": "S3 Storage",
        "domain": domain_c1,
        "nl_template": "Create bucket {bucket_name}, then upload {object_key} with {storage_class} storage",
        "actions": [
            {"namespace": "AWS.S3", "function": "CreateBucket",
             "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "{access_level}",
                        "versioning": True, "encryption": "{encryption}"},
             "output_refs": {"bucket_name": "Data bucket", "bucket_arn": "ARN"},
             "depends_on": []},
            {"namespace": "AWS.S3", "function": "UploadObject",
             "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}",
                        "content_type": "{content_type}", "storage_class": "{storage_class}"},
             "output_refs": {"object_key": "Uploaded object", "etag": "Object ETag"},
             "depends_on": [1]},
        ]
    },
    # Template 3: Create bucket with rollback path
    {
        "sector": "S3 Storage",
        "domain": domain_c1,
        "nl_template": "Set up {bucket_name} bucket for {access_level} access with rollback on creation failure",
        "actions": [
            {"namespace": "AWS.S3", "function": "CreateBucket",
             "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "{access_level}",
                        "versioning": False, "encryption": "{encryption}"},
             "output_refs": {"bucket_name": "Created bucket", "bucket_arn": "ARN"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
        ]
    },
    # Template 4: Full bucket lifecycle with rollback
    {
        "sector": "S3 Storage",
        "domain": domain_c1,
        "nl_template": "Create {bucket_name}, upload {object_key}, and make sure we can clean up if anything goes wrong",
        "actions": [
            {"namespace": "AWS.S3", "function": "CreateBucket",
             "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "{access_level}",
                        "versioning": True, "encryption": "{encryption}"},
             "output_refs": {"bucket_name": "Logs bucket", "bucket_arn": "ARN"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteBucket"}},
            {"namespace": "AWS.S3", "function": "UploadObject",
             "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}",
                        "content_type": "{content_type}", "storage_class": "{storage_class}"},
             "output_refs": {"object_key": "Uploaded file key", "etag": "Hash"},
             "depends_on": [1]},
        ]
    },
    # Template 5: Multi-upload with delete rollback
    {
        "sector": "S3 Storage",
        "domain": domain_c1,
        "nl_template": "Upload {object_key} to bucket {bucket_name} with {storage_class} and {encryption} encryption",
        "actions": [
            {"namespace": "AWS.S3", "function": "UploadObject",
             "params": {"bucket_name": "{bucket_name}", "object_key": "{object_key}",
                        "content_type": "{content_type}", "storage_class": "{storage_class}"},
             "output_refs": {"object_key": "Uploaded file", "etag": "Object hash"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.S3", "function": "DeleteObject"}},
        ]
    },
    # Template 6: Bucket with config upload (variable passing)
    {
        "sector": "S3 Storage",
        "domain": domain_c1,
        "nl_template": "Create {bucket_name} to store config files and upload {object_key} for production deployment",
        "actions": [
            {"namespace": "AWS.S3", "function": "CreateBucket",
             "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private",
                        "versioning": True, "encryption": "AES256"},
             "output_refs": {"bucket_name": "Config bucket", "bucket_arn": "ARN"},
             "depends_on": []},
            {"namespace": "AWS.S3", "function": "UploadObject",
             "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}",
                        "content_type": "application/json", "storage_class": "{storage_class}"},
             "output_refs": {"config_key": "Config object key", "etag": "ETag"},
             "depends_on": [1]},
        ]
    },
    # Template 7: Create bucket, upload, then delete (cleanup)
    {
        "sector": "S3 Storage",
        "domain": domain_c1,
        "nl_template": "Create temp bucket {bucket_name} in {region}, upload a {object_key}, then clean up both",
        "actions": [
            {"namespace": "AWS.S3", "function": "CreateBucket",
             "params": {"bucket_name": "{bucket_name}", "region": "{region}", "access_level": "private",
                        "versioning": False, "encryption": "AES256"},
             "output_refs": {"bucket_name": "Temp bucket"},
             "depends_on": []},
            {"namespace": "AWS.S3", "function": "UploadObject",
             "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{object_key}",
                        "content_type": "{content_type}", "storage_class": "STANDARD"},
             "output_refs": {"uploaded_key": "Temp object key"},
             "depends_on": [1]},
            {"namespace": "AWS.S3", "function": "DeleteObject",
             "params": {"bucket_name": "{{steps[1].output.bucket_name}}", "object_key": "{{steps[2].output.uploaded_key}}"},
             "output_refs": {"deleted_object": "Deleted object marker"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 3: Lambda Serverless ---
TEMPLATES.extend([
    {
        "sector": "Lambda Serverless",
        "domain": domain_c1,
        "nl_template": "Create a Lambda function {function_name} with {runtime} runtime and {memory_mb}MB memory",
        "actions": [
            {"namespace": "AWS.Lambda", "function": "CreateFunction",
             "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": "{memory_mb}",
                        "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"},
             "output_refs": {"function_name": "Lambda name", "function_arn": "Lambda ARN"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Lambda Serverless",
        "domain": domain_c1,
        "nl_template": "Create {function_name} Lambda and test it with a {invocation_type} invocation, then clean up if it fails",
        "actions": [
            {"namespace": "AWS.Lambda", "function": "CreateFunction",
             "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": "{memory_mb}",
                        "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"},
             "output_refs": {"function_name": "Lambda function", "function_arn": "ARN"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
            {"namespace": "AWS.Lambda", "function": "InvokeFunction",
             "params": {"function_name": "{{steps[1].output.function_name}}", "invocation_type": "{invocation_type}",
                        "payload": "{payload}"},
             "output_refs": {"status_code": "Invocation status", "execution_result": "Result payload"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Lambda Serverless",
        "domain": domain_c1,
        "nl_template": "Create a {runtime} Lambda function {function_name} with 1024MB memory and invoke it with test payload",
        "actions": [
            {"namespace": "AWS.Lambda", "function": "CreateFunction",
             "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": 1024,
                        "timeout_seconds": 120, "role_arn": "{role_arn}"},
             "output_refs": {"function_name": "Test function", "function_arn": "ARN"},
             "depends_on": []},
            {"namespace": "AWS.Lambda", "function": "InvokeFunction",
             "params": {"function_name": "{{steps[1].output.function_name}}", "invocation_type": "RequestResponse",
                        "payload": "{payload}"},
             "output_refs": {"result_status": "Invocation result"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Lambda Serverless",
        "domain": domain_c1,
        "nl_template": "Build and deploy {function_name} as a {runtime} function, invoke to verify, and roll back on error",
        "actions": [
            {"namespace": "AWS.Lambda", "function": "CreateFunction",
             "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": 512,
                        "timeout_seconds": "{timeout_seconds}", "role_arn": "{role_arn}"},
             "output_refs": {"function_name": "Deployed function", "function_arn": "ARN"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.Lambda", "function": "DeleteFunction"}},
            {"namespace": "AWS.Lambda", "function": "InvokeFunction",
             "params": {"function_name": "{{steps[1].output.function_name}}", "invocation_type": "{invocation_type}",
                        "payload": "{payload}"},
             "output_refs": {"status_code": "200 on success", "execution_result": "Output"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Lambda Serverless",
        "domain": domain_c1,
        "nl_template": "Create, invoke, and delete {function_name} as a cleanup test cycle",
        "actions": [
            {"namespace": "AWS.Lambda", "function": "CreateFunction",
             "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": 256,
                        "timeout_seconds": 60, "role_arn": "{role_arn}"},
             "output_refs": {"function_name": "Temp function", "function_arn": "ARN"},
             "depends_on": []},
            {"namespace": "AWS.Lambda", "function": "InvokeFunction",
             "params": {"function_name": "{{steps[1].output.function_name}}", "invocation_type": "RequestResponse",
                        "payload": '{"event":"test"}'},
             "output_refs": {"test_result": "Invocation output"},
             "depends_on": [1]},
            {"namespace": "AWS.Lambda", "function": "DeleteFunction",
             "params": {"function_name": "{{steps[1].output.function_name}}"},
             "output_refs": {"deleted": "deleted"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Lambda Serverless",
        "domain": domain_c1,
        "nl_template": "Create {function_name} as a {runtime} function that processes orders, attach IAM policy, and test it",
        "actions": [
            {"namespace": "AWS.Lambda", "function": "CreateFunction",
             "params": {"function_name": "{function_name}", "runtime": "{runtime}", "memory_mb": 2048,
                        "timeout_seconds": 300, "role_arn": "{role_arn}"},
             "output_refs": {"function_name": "Order processor", "function_arn": "ARN"},
             "depends_on": []},
            {"namespace": "AWS.IAM", "function": "AttachPolicy",
             "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[1].output.function_name}}", "target_type": "role"},
             "output_refs": {"policy_status": "attached"},
             "depends_on": [1]},
            {"namespace": "AWS.Lambda", "function": "InvokeFunction",
             "params": {"function_name": "{{steps[1].output.function_name}}", "invocation_type": "Event",
                        "payload": "{payload}"},
             "output_refs": {"invoke_status": "Event status"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 4: RDS Database ---
TEMPLATES.extend([
    {
        "sector": "RDS Database",
        "domain": domain_c1,
        "nl_template": "Create a {engine} RDS database named {db_name} with {storage_gb}GB storage and {backup_retention_days} day backup retention",
        "actions": [
            {"namespace": "AWS.RDS", "function": "CreateDatabase",
             "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "{instance_class}",
                        "storage_gb": "{storage_gb}", "multi_az": "{multi_az}", "backup_retention_days": "{backup_retention_days}"},
             "output_refs": {"db_instance_id": "DB instance ID", "endpoint": "Connection endpoint"},
             "depends_on": []},
        ]
    },
    {
        "sector": "RDS Database",
        "domain": domain_c1,
        "nl_template": "Provision a {engine} database {db_name} in {instance_class} with rollback cleanup on failure",
        "actions": [
            {"namespace": "AWS.RDS", "function": "CreateDatabase",
             "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "{instance_class}",
                        "storage_gb": "{storage_gb}", "multi_az": True, "backup_retention_days": 30},
             "output_refs": {"db_instance_id": "Database ID", "endpoint": "Connection host"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.RDS", "function": "DeleteDatabase"}},
        ]
    },
    {
        "sector": "RDS Database",
        "domain": domain_c1,
        "nl_template": "Create {db_name} database, then stop and delete it to free resources",
        "actions": [
            {"namespace": "AWS.RDS", "function": "CreateDatabase",
             "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "{instance_class}",
                        "storage_gb": 100, "multi_az": False, "backup_retention_days": 14},
             "output_refs": {"db_instance_id": "DB to delete", "endpoint": "Endpoint host"},
             "depends_on": []},
            {"namespace": "AWS.RDS", "function": "DeleteDatabase",
             "params": {"db_instance_id": "{{steps[1].output.db_instance_id}}", "skip_final_snapshot": True},
             "output_refs": {"deletion_status": "deleting"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "RDS Database",
        "domain": domain_c1,
        "nl_template": "Set up {db_name} as a {engine} database with automatic rollback if provisioning fails",
        "actions": [
            {"namespace": "AWS.RDS", "function": "CreateDatabase",
             "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "db.r5.large",
                        "storage_gb": 500, "multi_az": True, "backup_retention_days": 35},
             "output_refs": {"db_instance_id": "Production DB", "endpoint": "Primary endpoint", "port": "5432"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.RDS", "function": "DeleteDatabase"}},
            {"namespace": "AWS.VPC", "function": "CreateSecurityGroup",
             "params": {"group_name": "db-{group_suffix}", "description": "Database access", "vpc_id": "{vpc_id}"},
             "output_refs": {"db_sg_id": "DB security group"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "RDS Database",
        "domain": domain_c1,
        "nl_template": "Create {engine} database {db_name} with monitoring alert setup and scheduled backup",
        "actions": [
            {"namespace": "AWS.RDS", "function": "CreateDatabase",
             "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "{instance_class}",
                        "storage_gb": 200, "multi_az": True, "backup_retention_days": "{backup_retention_days}"},
             "output_refs": {"db_instance_id": "Monitored DB", "endpoint": "DB endpoint"},
             "depends_on": []},
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "DB-{db_name}-CPU", "metric": "cpu_utilization", "threshold": 85.0,
                        "operator": ">", "duration_minutes": 10, "channels": ["slack", "email"], "severity": "warning"},
             "output_refs": {"db_alert_id": "DB monitoring alert"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "RDS Database",
        "domain": domain_c1,
        "nl_template": "Create {engine} database {db_name} with subnet setup in {vpc_id} and monitoring",
        "actions": [
            {"namespace": "AWS.VPC", "function": "CreateSubnet",
             "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}",
                        "map_public_ip": False},
             "output_refs": {"subnet_id": "DB subnet ID"},
             "depends_on": []},
            {"namespace": "AWS.RDS", "function": "CreateDatabase",
             "params": {"db_name": "{db_name}", "engine": "{engine}", "instance_class": "{instance_class}",
                        "storage_gb": "{storage_gb}", "multi_az": "{multi_az}", "backup_retention_days": "{backup_retention_days}"},
             "output_refs": {"db_instance_id": "Database in subnet", "endpoint": "Endpoint"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 5: VPC Networking ---
TEMPLATES.extend([
    {
        "sector": "VPC Networking",
        "domain": domain_c1,
        "nl_template": "Create a subnet {cidr_block} in VPC {vpc_id} in {availability_zone}",
        "actions": [
            {"namespace": "AWS.VPC", "function": "CreateSubnet",
             "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}",
                        "map_public_ip": "{map_public_ip}"},
             "output_refs": {"subnet_id": "Created subnet ID"},
             "depends_on": []},
        ]
    },
    {
        "sector": "VPC Networking",
        "domain": domain_c1,
        "nl_template": "Create subnet {cidr_block} in {availability_zone} with rollback deletion on failure",
        "actions": [
            {"namespace": "AWS.VPC", "function": "CreateSubnet",
             "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}",
                        "map_public_ip": True},
             "output_refs": {"subnet_id": "Public subnet"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSubnet"}},
        ]
    },
    {
        "sector": "VPC Networking",
        "domain": domain_c1,
        "nl_template": "Create security group {group_name} in VPC {vpc_id} then create a subnet",
        "actions": [
            {"namespace": "AWS.VPC", "function": "CreateSecurityGroup",
             "params": {"group_name": "{group_name}", "description": "{sg_description}", "vpc_id": "{vpc_id}"},
             "output_refs": {"group_id": "Security group ID"},
             "depends_on": []},
            {"namespace": "AWS.VPC", "function": "CreateSubnet",
             "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}",
                        "availability_zone": "{availability_zone}", "map_public_ip": False},
             "output_refs": {"subnet_id": "Private subnet"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "VPC Networking",
        "domain": domain_c1,
        "nl_template": "Set up multi-subnet architecture: create {group_name} security group and {cidr_block} subnet in {availability_zone}",
        "actions": [
            {"namespace": "AWS.VPC", "function": "CreateSecurityGroup",
             "params": {"group_name": "{group_name}", "description": "{sg_description}", "vpc_id": "{vpc_id}"},
             "output_refs": {"group_id": "Web security group"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.VPC", "function": "DeleteSecurityGroup"}},
            {"namespace": "AWS.VPC", "function": "CreateSubnet",
             "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}",
                        "map_public_ip": True},
             "output_refs": {"subnet_id": "Public web subnet"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "VPC Networking",
        "domain": domain_c1,
        "nl_template": "Create web security group and multiple subnets for high-availability in different AZs",
        "actions": [
            {"namespace": "AWS.VPC", "function": "CreateSecurityGroup",
             "params": {"group_name": "{group_name}", "description": "Web tier security", "vpc_id": "{vpc_id}"},
             "output_refs": {"web_sg": "Web SG ID"},
             "depends_on": []},
            {"namespace": "AWS.VPC", "function": "CreateSubnet",
             "params": {"vpc_id": "{{steps[1].output.web_sg}}", "cidr_block": "{cidr_block}",
                        "availability_zone": "{availability_zone}", "map_public_ip": True},
             "output_refs": {"subnet_a": "Subnet in AZ-a"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "VPC Networking",
        "domain": domain_c1,
        "nl_template": "Create subnet, security group, and launch an EC2 instance inside the VPC",
        "actions": [
            {"namespace": "AWS.VPC", "function": "CreateSubnet",
             "params": {"vpc_id": "{vpc_id}", "cidr_block": "{cidr_block}", "availability_zone": "{availability_zone}",
                        "map_public_ip": True},
             "output_refs": {"subnet_id": "Compute subnet"},
             "depends_on": []},
            {"namespace": "AWS.VPC", "function": "CreateSecurityGroup",
             "params": {"group_name": "{group_name}", "description": "Compute access", "vpc_id": "{vpc_id}"},
             "output_refs": {"compute_sg": "Compute SG ID"},
             "depends_on": [1]},
            {"namespace": "AWS.EC2", "function": "ProvisionInstance",
             "params": {"instance_type": "{instance_type}", "ami_id": "{ami_id}",
                        "subnet_id": "{{steps[1].output.subnet_id}}",
                        "security_group": "{{steps[2].output.compute_sg}}", "volume_size_gb": 50},
             "output_refs": {"instance_id": "Compute instance"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 6: IAM Security ---
TEMPLATES.extend([
    {
        "sector": "IAM Security",
        "domain": domain_c1,
        "nl_template": "Create IAM user {user_name} in {path} path",
        "actions": [
            {"namespace": "AWS.IAM", "function": "CreateUser",
             "params": {"user_name": "{user_name}", "path": "{path}"},
             "output_refs": {"user_name": "Created user", "user_arn": "User ARN"},
             "depends_on": []},
        ]
    },
    {
        "sector": "IAM Security",
        "domain": domain_c1,
        "nl_template": "Create IAM user {user_name}, attach {policy_arn} policy, and set up rollback if creation fails",
        "actions": [
            {"namespace": "AWS.IAM", "function": "CreateUser",
             "params": {"user_name": "{user_name}", "path": "{path}"},
             "output_refs": {"user_name": "Service account", "user_arn": "ARN"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
            {"namespace": "AWS.IAM", "function": "AttachPolicy",
             "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[1].output.user_name}}", "target_type": "user"},
             "output_refs": {"policy_status": "attached"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "IAM Security",
        "domain": domain_c1,
        "nl_template": "Create {user_name} user, attach {policy_arn}, then detach as a cleanup",
        "actions": [
            {"namespace": "AWS.IAM", "function": "CreateUser",
             "params": {"user_name": "{user_name}", "path": "{path}"},
             "output_refs": {"user_name": "Created IAM user"},
             "depends_on": []},
            {"namespace": "AWS.IAM", "function": "AttachPolicy",
             "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[1].output.user_name}}", "target_type": "user"},
             "output_refs": {"policy_arn": "Attached ARN"},
             "depends_on": [1]},
            {"namespace": "AWS.IAM", "function": "DetachPolicy",
             "params": {"policy_arn": "{{steps[2].output.policy_arn}}", "target_name": "{{steps[1].output.user_name}}"},
             "output_refs": {"detached": "detached"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "IAM Security",
        "domain": domain_c1,
        "nl_template": "Create {user_name} as a service account with read-only access and cleanup on failure",
        "actions": [
            {"namespace": "AWS.IAM", "function": "CreateUser",
             "params": {"user_name": "{user_name}", "path": "/service-accounts/"},
             "output_refs": {"user_name": "Service user", "user_arn": "ARN"},
             "depends_on": [], "rollback_ref": {"namespace": "AWS.IAM", "function": "DeleteUser"}},
            {"namespace": "AWS.IAM", "function": "AttachPolicy",
             "params": {"policy_arn": "arn:aws:iam::aws:policy/ReadOnlyAccess",
                        "target_name": "{{steps[1].output.user_name}}", "target_type": "user"},
             "output_refs": {"policy_attached": "ReadOnly attached"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "IAM Security",
        "domain": domain_c1,
        "nl_template": "Create user {user_name}, attach admin policy, then delete as cleanup",
        "actions": [
            {"namespace": "AWS.IAM", "function": "CreateUser",
             "params": {"user_name": "{user_name}", "path": "{path}"},
             "output_refs": {"temp_user": "Temporary user name"},
             "depends_on": []},
            {"namespace": "AWS.IAM", "function": "AttachPolicy",
             "params": {"policy_arn": "{policy_arn}", "target_name": "{{steps[1].output.temp_user}}", "target_type": "user"},
             "output_refs": {"attached_arn": "Policy ARN"},
             "depends_on": [1]},
            {"namespace": "AWS.IAM", "function": "DetachPolicy",
             "params": {"policy_arn": "{{steps[2].output.attached_arn}}", "target_name": "{{steps[1].output.temp_user}}"},
             "output_refs": {"detached_policy": "detached"},
             "depends_on": [2]},
            {"namespace": "AWS.IAM", "function": "DeleteUser",
             "params": {"user_name": "{{steps[1].output.temp_user}}"},
             "output_refs": {"user_deleted": "deleted"},
             "depends_on": [3]},
        ]
    },
    {
        "sector": "IAM Security",
        "domain": domain_c1,
        "nl_template": "Create IAM user {user_name}, attach S3 access policy, and verify with alerting",
        "actions": [
            {"namespace": "AWS.IAM", "function": "CreateUser",
             "params": {"user_name": "{user_name}", "path": "{path}"},
             "output_refs": {"user_name": "S3 access user"},
             "depends_on": []},
            {"namespace": "AWS.IAM", "function": "AttachPolicy",
             "params": {"policy_arn": "arn:aws:iam::aws:policy/AmazonS3FullAccess",
                        "target_name": "{{steps[1].output.user_name}}", "target_type": "user"},
             "output_refs": {"s3_policy": "attached"},
             "depends_on": [1]},
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "IAM-{alert_name}", "metric": "error_rate", "threshold": 5.0,
                        "operator": ">", "duration_minutes": 5, "channels": ["email"], "severity": "warning"},
             "output_refs": {"iam_alert": "IAM alert ID"},
             "depends_on": [2]},
        ]
    },
])

# ===========================================================================
# DOMAIN 2: DevOps/CI-CD
# ===========================================================================
domain_c2 = "DevOps/CI-CD"

# --- Sector 7: Build Pipelines ---
TEMPLATES.extend([
    {
        "sector": "Build Pipelines", "domain": domain_c2,
        "nl_template": "Create a build pipeline {pipeline_name} for repo {repository_url} on {branch} branch",
        "actions": [
            {"namespace": "CI.Build", "function": "CreateBuildPipeline",
             "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}",
                        "build_image": "{build_image}", "timeout_minutes": "{timeout_minutes}",
                        "concurrent_builds": "{concurrent_builds}"},
             "output_refs": {"pipeline_id": "Pipeline ID", "pipeline_name": "Pipeline name"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Build Pipelines", "domain": domain_c2,
        "nl_template": "Create pipeline {pipeline_name} for {repository_url}, trigger a build, and roll back if build fails",
        "actions": [
            {"namespace": "CI.Build", "function": "CreateBuildPipeline",
             "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}",
                        "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 2},
             "output_refs": {"pipeline_id": "CI pipeline", "pipeline_name": "Name"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
            {"namespace": "CI.Build", "function": "TriggerBuild",
             "params": {"pipeline_name": "{{steps[1].output.pipeline_name}}", "commit_hash": "{commit_hash}",
                        "variables": {"BUILD_ENV": "staging"}},
             "output_refs": {"build_id": "Triggered build ID"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Build Pipelines", "domain": domain_c2,
        "nl_template": "Create {pipeline_name} pipeline on {branch}, trigger build with {commit_hash}, deploy to production",
        "actions": [
            {"namespace": "CI.Build", "function": "CreateBuildPipeline",
             "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}",
                        "build_image": "{build_image}", "timeout_minutes": 60, "concurrent_builds": 5},
             "output_refs": {"pipeline_name": "Release pipeline", "pipeline_id": "ID"},
             "depends_on": []},
            {"namespace": "CI.Build", "function": "TriggerBuild",
             "params": {"pipeline_name": "{{steps[1].output.pipeline_name}}", "commit_hash": "{commit_hash}",
                        "variables": {"BUILD_ENV": "production"}},
             "output_refs": {"build_id": "Production build"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Build Pipelines", "domain": domain_c2,
        "nl_template": "Create CI pipeline {pipeline_name}, push a test build, and clean up pipeline when done",
        "actions": [
            {"namespace": "CI.Build", "function": "CreateBuildPipeline",
             "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}",
                        "build_image": "ubuntu:22.04", "timeout_minutes": 15, "concurrent_builds": 1},
             "output_refs": {"pipeline_name": "Test pipeline", "pipeline_id": "ID"},
             "depends_on": []},
            {"namespace": "CI.Build", "function": "TriggerBuild",
             "params": {"pipeline_name": "{{steps[1].output.pipeline_name}}", "commit_hash": "{commit_hash}",
                        "variables": [{"BUILD_ENV": "staging"}]},
             "output_refs": {"build_id": "Test build"},
             "depends_on": [1]},
            {"namespace": "CI.Build", "function": "DeleteBuildPipeline",
             "params": {"pipeline_name": "{{steps[1].output.pipeline_name}}"},
             "output_refs": {"deleted": "deleted"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Build Pipelines", "domain": domain_c2,
        "nl_template": "Create {pipeline_name} pipeline with {build_image} and concurrent build limit {concurrent_builds}",
        "actions": [
            {"namespace": "CI.Build", "function": "CreateBuildPipeline",
             "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}",
                        "build_image": "{build_image}", "timeout_minutes": "{timeout_minutes}",
                        "concurrent_builds": "{concurrent_builds}"},
             "output_refs": {"pipeline_name": "CI pipeline"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Build", "function": "DeleteBuildPipeline"}},
        ]
    },
    {
        "sector": "Build Pipelines", "domain": domain_c2,
        "nl_template": "Set up {pipeline_name} pipeline from {repository_url} with monitoring alerts for build failures",
        "actions": [
            {"namespace": "CI.Build", "function": "CreateBuildPipeline",
             "params": {"pipeline_name": "{pipeline_name}", "repository_url": "{repository_url}", "branch": "{branch}",
                        "build_image": "{build_image}", "timeout_minutes": 30, "concurrent_builds": 2},
             "output_refs": {"pipeline_name": "Monitored pipeline", "pipeline_arn": "ARN"},
             "depends_on": []},
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "Build-{alert_name}", "metric": "error_rate", "threshold": 5.0,
                        "operator": ">", "duration_minutes": 5, "channels": ["slack"], "severity": "critical"},
             "output_refs": {"pipeline_alert": "Alert for build"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 8: Container Orchestration (K8s) ---
TEMPLATES.extend([
    {
        "sector": "Container Orchestration", "domain": domain_c2,
        "nl_template": "Deploy {service_name} service with {replicas} replicas in {namespace} namespace using {image} image",
        "actions": [
            {"namespace": "K8s.Cluster", "function": "CreateNamespace",
             "params": {"namespace": "{namespace}", "labels": {"env": "{env_label}"},
                        "resource_quota_cpu": "{resource_quota_cpu}", "resource_quota_memory": "{resource_quota_memory}"},
             "output_refs": {"namespace": "Target namespace", "uid": "Namespace UUID"},
             "depends_on": []},
            {"namespace": "K8s.Cluster", "function": "DeployService",
             "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "{service_name}",
                        "image": "{image}", "replicas": "{replicas}", "cpu_limit": "{cpu_limit}",
                        "memory_limit": "{memory_limit}", "expose_port": "{expose_port}"},
             "output_refs": {"service_name": "Name", "cluster_ip": "Cluster IP", "available_replicas": "Ready pods"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Container Orchestration", "domain": domain_c2,
        "nl_template": "Create {namespace} namespace with {resource_quota_cpu} CPU quota, deploy {service_name} with rollback",
        "actions": [
            {"namespace": "K8s.Cluster", "function": "CreateNamespace",
             "params": {"namespace": "{namespace}", "labels": {"env": "prod"},
                        "resource_quota_cpu": "{resource_quota_cpu}", "resource_quota_memory": "{resource_quota_memory}"},
             "output_refs": {"namespace": "Production namespace"},
             "depends_on": [], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteNamespace"}},
            {"namespace": "K8s.Cluster", "function": "DeployService",
             "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "{service_name}",
                        "image": "{image}", "replicas": 3, "cpu_limit": "{cpu_limit}",
                        "memory_limit": "{memory_limit}", "expose_port": 80},
             "output_refs": {"service_name": "Deployed service", "cluster_ip": "Internal IP"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Container Orchestration", "domain": domain_c2,
        "nl_template": "Create namespace {namespace}, deploy {service_name}, scale to {scale_replicas} replicas",
        "actions": [
            {"namespace": "K8s.Cluster", "function": "CreateNamespace",
             "params": {"namespace": "{namespace}", "labels": {"env": "staging"},
                        "resource_quota_cpu": "20", "resource_quota_memory": "50Gi"},
             "output_refs": {"namespace": "Staging namespace"},
             "depends_on": []},
            {"namespace": "K8s.Cluster", "function": "DeployService",
             "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "{service_name}",
                        "image": "{image}", "replicas": 1, "cpu_limit": "500m",
                        "memory_limit": "1Gi", "expose_port": 8080},
             "output_refs": {"service_name": "Deployed name", "cluster_ip": "IP"},
             "depends_on": [1]},
            {"namespace": "K8s.Cluster", "function": "ScaleDeployment",
             "params": {"namespace": "{{steps[1].output.namespace}}",
                        "deployment_name": "{{steps[2].output.service_name}}", "replicas": "{scale_replicas}"},
             "output_refs": {"old_replicas": "1", "new_replicas": "Scaled count"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Container Orchestration", "domain": domain_c2,
        "nl_template": "Create {namespace}, deploy {service_name} with monitoring, with automatic rollback on error",
        "actions": [
            {"namespace": "K8s.Cluster", "function": "CreateNamespace",
             "params": {"namespace": "{namespace}", "labels": {"env": "prod"},
                        "resource_quota_cpu": "50", "resource_quota_memory": "100Gi"},
             "output_refs": {"namespace": "Production NS"},
             "depends_on": [], "rollback_ref": {"namespace": "K8s.Cluster", "function": "DeleteNamespace"}},
            {"namespace": "K8s.Cluster", "function": "DeployService",
             "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "{service_name}",
                        "image": "{image}", "replicas": 5, "cpu_limit": "1", "memory_limit": "2Gi",
                        "expose_port": 443},
             "output_refs": {"service_name": "Prod service", "cluster_ip": "Cluster IP"},
             "depends_on": [1]},
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "K8s-{alert_name}", "metric": "cpu_utilization", "threshold": 90.0,
                        "operator": ">", "duration_minutes": 5, "channels": ["pagerduty"], "severity": "critical"},
             "output_refs": {"k8s_alert": "Alert ID"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Container Orchestration", "domain": domain_c2,
        "nl_template": "Create {namespace} namespace, deploy {service_name} on port {expose_port}, then clean up deployment",
        "actions": [
            {"namespace": "K8s.Cluster", "function": "CreateNamespace",
             "params": {"namespace": "{namespace}", "labels": {"env": "dev"},
                        "resource_quota_cpu": "10", "resource_quota_memory": "20Gi"},
             "output_refs": {"namespace": "Dev namespace"},
             "depends_on": []},
            {"namespace": "K8s.Cluster", "function": "DeployService",
             "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "{service_name}",
                        "image": "{image}", "replicas": 1, "cpu_limit": "500m",
                        "memory_limit": "1Gi", "expose_port": "{expose_port}"},
             "output_refs": {"service_name": "Dev service", "cluster_ip": "IP"},
             "depends_on": [1]},
            {"namespace": "K8s.Cluster", "function": "DeleteDeployment",
             "params": {"namespace": "{{steps[1].output.namespace}}",
                        "deployment_name": "{{steps[2].output.service_name}}"},
             "output_refs": {"deleted": "deleted"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Container Orchestration", "domain": domain_c2,
        "nl_template": "Create {namespace} with {image} deployment scaled to {replicas} replicas and monitoring dashboard",
        "actions": [
            {"namespace": "K8s.Cluster", "function": "CreateNamespace",
             "params": {"namespace": "{namespace}", "labels": {"env": "prod"},
                        "resource_quota_cpu": "100", "resource_quota_memory": "200Gi"},
             "output_refs": {"namespace": "Large namespace"},
             "depends_on": []},
            {"namespace": "K8s.Cluster", "function": "DeployService",
             "params": {"namespace": "{{steps[1].output.namespace}}", "service_name": "{service_name}",
                        "image": "{image}", "replicas": "{replicas}", "cpu_limit": "2",
                        "memory_limit": "4Gi", "expose_port": 3000},
             "output_refs": {"service_name": "Large service", "available_replicas": "Ready"},
             "depends_on": [1]},
            {"namespace": "Ops.Monitoring", "function": "SetUpDashboard",
             "params": {"dashboard_name": "K8s-{dashboard_name}", "panels": [["CPU", "Memory", "Disk"]],
                        "time_range": "last_24h", "refresh_interval_seconds": 60},
             "output_refs": {"dashboard_uid": "Dashboard ID"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 9: Monitoring/Alerts ---
TEMPLATES.extend([
    {
        "sector": "Monitoring/Alerts", "domain": domain_c2,
        "nl_template": "Create alert {alert_name} for {metric} when it exceeds {threshold} for {duration_minutes} minutes",
        "actions": [
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "{alert_name}", "metric": "{metric}", "threshold": "{threshold}",
                        "operator": "{operator}", "duration_minutes": "{duration_minutes}",
                        "channels": "{channels}", "severity": "{severity}"},
             "output_refs": {"alert_id": "Alert ID", "alert_name": "Name"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Monitoring/Alerts", "domain": domain_c2,
        "nl_template": "Create alert {alert_name} for {metric} with slack notification, then set up dashboard",
        "actions": [
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "{alert_name}", "metric": "{metric}", "threshold": "{threshold}",
                        "operator": "{operator}", "duration_minutes": 5, "channels": ["slack"], "severity": "{severity}"},
             "output_refs": {"alert_id": "Alert ID"},
             "depends_on": []},
            {"namespace": "Ops.Monitoring", "function": "SetUpDashboard",
             "params": {"dashboard_name": "{{steps[1].output.alert_id}}-dashboard", "panels": "{panels}",
                        "time_range": "{time_range}", "refresh_interval_seconds": "{refresh_interval_seconds}"},
             "output_refs": {"dashboard_uid": "Dashboard UID"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Monitoring/Alerts", "domain": domain_c2,
        "nl_template": "Set up {alert_name} alert for {metric} with automatic dismissal rollback on false alarm",
        "actions": [
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "{alert_name}", "metric": "{metric}", "threshold": "{threshold}",
                        "operator": ">", "duration_minutes": 10, "channels": ["pagerduty", "slack"],
                        "severity": "critical"},
             "output_refs": {"alert_id": "Critical alert ID"},
             "depends_on": [], "rollback_ref": {"namespace": "Ops.Monitoring", "function": "DismissAlert"}},
        ]
    },
    {
        "sector": "Monitoring/Alerts", "domain": domain_c2,
        "nl_template": "Create {metric} monitoring alert {alert_name} and dismiss previous alert {previous_alert} with rollback coverage",
        "actions": [
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "{alert_name}", "metric": "{metric}", "threshold": "{threshold}",
                        "operator": "{operator}", "duration_minutes": "{duration_minutes}",
                        "channels": "{channels}", "severity": "{severity}"},
             "output_refs": {"alert_id": "New alert ID"},
             "depends_on": [], "rollback_ref": {"namespace": "Ops.Monitoring", "function": "DismissAlert"}},
            {"namespace": "Ops.Monitoring", "function": "SetUpDashboard",
             "params": {"dashboard_name": "{dashboard_name}", "panels": ["{panels}"],
                        "time_range": "last_6h", "refresh_interval_seconds": 60},
             "output_refs": {"dashboard_uid": "Dashboard UID"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Monitoring/Alerts", "domain": domain_c2,
        "nl_template": "Create alert {alert_name} for {metric}, set up a dashboard {dashboard_name} to visualize it",
        "actions": [
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "{alert_name}", "metric": "{metric}", "threshold": "{threshold}",
                        "operator": "{operator}", "duration_minutes": "{duration_minutes}",
                        "channels": "{channels}", "severity": "{severity}"},
             "output_refs": {"alert_id": "Alert to visualize"},
             "depends_on": []},
            {"namespace": "Ops.Monitoring", "function": "SetUpDashboard",
             "params": {"dashboard_name": "{dashboard_name}", "panels": "{panels}",
                        "time_range": "{time_range}", "refresh_interval_seconds": "{refresh_interval_seconds}"},
             "output_refs": {"dashboard_uid": "Dashboard"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Monitoring/Alerts", "domain": domain_c2,
        "nl_template": "Set up full monitoring stack: alert {alert_name}, dashboard {dashboard_name}, dismiss on resolution",
        "actions": [
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "{alert_name}", "metric": "{metric}", "threshold": 90.0,
                        "operator": ">", "duration_minutes": 5, "channels": ["slack", "email"], "severity": "critical"},
             "output_refs": {"alert_id": "Alert to monitor"},
             "depends_on": [], "rollback_ref": {"namespace": "Ops.Monitoring", "function": "DismissAlert"}},
            {"namespace": "Ops.Monitoring", "function": "SetUpDashboard",
             "params": {"dashboard_name": "{dashboard_name}", "panels": [["CPU", "Memory", "Disk"]],
                        "time_range": "last_24h", "refresh_interval_seconds": 30},
             "output_refs": {"dashboard_uid": "Monitoring dashboard"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 10: Deployments ---
TEMPLATES.extend([
    {
        "sector": "Deployments", "domain": domain_c2,
        "nl_template": "Promote build {artifact_id} from {source_env} to {target_env} with {rollback_strategy} rollback strategy",
        "actions": [
            {"namespace": "CI.Deploy", "function": "PromoteBuild",
             "params": {"artifact_id": "{artifact_id}", "source_env": "{source_env}", "target_env": "{target_env}",
                        "rollback_strategy": "{rollback_strategy}", "canary_percent": "{canary_percent}"},
             "output_refs": {"promotion_id": "Promotion ID", "artifact_id": "Artifact", "deployment_url": "URL"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Deployments", "domain": domain_c2,
        "nl_template": "Promote {artifact_id} to {target_env} and set up automatic revert with rollback coverage",
        "actions": [
            {"namespace": "CI.Deploy", "function": "PromoteBuild",
             "params": {"artifact_id": "{artifact_id}", "source_env": "{source_env}", "target_env": "{target_env}",
                        "rollback_strategy": "immediate", "canary_percent": 25},
             "output_refs": {"promotion_id": "Canary deploy ID", "deployment_url": "Deploy URL"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
        ]
    },
    {
        "sector": "Deployments", "domain": domain_c2,
        "nl_template": "Promote {artifact_id} to {target_env} with canary {canary_percent} percent, revert on failure",
        "actions": [
            {"namespace": "CI.Deploy", "function": "PromoteBuild",
             "params": {"artifact_id": "{artifact_id}", "source_env": "{source_env}", "target_env": "{target_env}",
                        "rollback_strategy": "gradual", "canary_percent": 10},
             "output_refs": {"promotion_id": "Canary deployment", "deployment_url": "URL"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
            {"namespace": "CI.Deploy", "function": "RevertBuild",
             "params": {"promotion_id": "{{steps[1].output.promotion_id}}", "target_env": "{target_env}",
                        "revert_strategy": "immediate"},
             "output_refs": {"reverted_to": "previous artifact"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Deployments", "domain": domain_c2,
        "nl_template": "Full CI/CD flow: trigger build, promote {artifact_id} to {target_env} with monitoring",
        "actions": [
            {"namespace": "CI.Build", "function": "TriggerBuild",
             "params": {"pipeline_name": "{pipeline_name}", "commit_hash": "{commit_hash}",
                        "variables": {"BUILD_ENV": "production"}},
             "output_refs": {"build_id": "Build ID"},
             "depends_on": []},
            {"namespace": "CI.Deploy", "function": "PromoteBuild",
             "params": {"artifact_id": "{artifact_id}", "source_env": "{source_env}", "target_env": "{target_env}",
                        "rollback_strategy": "{rollback_strategy}", "canary_percent": "{canary_percent}"},
             "output_refs": {"promotion_id": "Deployment", "deployment_url": "URL"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Deployments", "domain": domain_c2,
        "nl_template": "Deploy {artifact_id} to {target_env} with {canary_percent} percent canary and monitor with alerting",
        "actions": [
            {"namespace": "CI.Deploy", "function": "PromoteBuild",
             "params": {"artifact_id": "{artifact_id}", "source_env": "{source_env}", "target_env": "{target_env}",
                        "rollback_strategy": "gradual", "canary_percent": 5},
             "output_refs": {"promotion_id": "Canary ID", "deployment_url": "URL"},
             "depends_on": []},
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "Deploy-{alert_name}", "metric": "error_rate", "threshold": 3.0,
                        "operator": ">", "duration_minutes": 5, "channels": ["slack"], "severity": "critical"},
             "output_refs": {"deploy_alert": "Deployment alert"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Deployments", "domain": domain_c2,
        "nl_template": "Promote {artifact_id} to {target_env}, create alert, and revert immediately if issues detected",
        "actions": [
            {"namespace": "CI.Deploy", "function": "PromoteBuild",
             "params": {"artifact_id": "{artifact_id}", "source_env": "{source_env}", "target_env": "{target_env}",
                        "rollback_strategy": "immediate", "canary_percent": 10},
             "output_refs": {"promotion_id": "Promo ID", "deployment_url": "Deploy URL"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Deploy", "function": "RevertBuild"}},
            {"namespace": "Ops.Monitoring", "function": "CreateAlertRule",
             "params": {"alert_name": "Deploy-{alert_name}", "metric": "error_rate", "threshold": 2.0,
                        "operator": ">", "duration_minutes": 1, "channels": ["slack", "pagerduty"], "severity": "critical"},
             "output_refs": {"monitor_alert": "Alert for deploy issues"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 11: Artifact Management ---
TEMPLATES.extend([
    {
        "sector": "Artifact Management", "domain": domain_c2,
        "nl_template": "Upload {artifact_name} version {version} to {repository} repository",
        "actions": [
            {"namespace": "CI.Artifacts", "function": "UploadArtifact",
             "params": {"artifact_name": "{artifact_name}", "version": "{version}", "repository": "{repository}",
                        "checksum": "{checksum}"},
             "output_refs": {"artifact_id": "Artifact ID", "download_url": "Download URL"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Artifact Management", "domain": domain_c2,
        "nl_template": "Upload {artifact_name} to {repository} with rollback deletion if upload fails",
        "actions": [
            {"namespace": "CI.Artifacts", "function": "UploadArtifact",
             "params": {"artifact_name": "{artifact_name}", "version": "{version}", "repository": "{repository}",
                        "checksum": "{checksum}"},
             "output_refs": {"artifact_id": "Uploaded artifact ID", "download_url": "URL"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Artifacts", "function": "DeleteArtifact"}},
        ]
    },
    {
        "sector": "Artifact Management", "domain": domain_c2,
        "nl_template": "Upload {artifact_name} to {repository}, create a Git branch {branch_name} to tag the release",
        "actions": [
            {"namespace": "CI.Artifacts", "function": "UploadArtifact",
             "params": {"artifact_name": "{artifact_name}", "version": "{version}", "repository": "{repository}",
                        "checksum": "{checksum}"},
             "output_refs": {"artifact_id": "Release artifact ID"},
             "depends_on": []},
            {"namespace": "CI.Git", "function": "CreateBranch",
             "params": {"repository": "{repo_name}", "branch_name": "release/{branch_name}", "source_branch": "main"},
             "output_refs": {"branch_name": "Release branch", "commit_hash": "HEAD"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Artifact Management", "domain": domain_c2,
        "nl_template": "Upload {artifact_name} {version} docker image to hub and verify with checksum",
        "actions": [
            {"namespace": "CI.Artifacts", "function": "UploadArtifact",
             "params": {"artifact_name": "{artifact_name}", "version": "{version}", "repository": "docker-hub",
                        "checksum": "{checksum}"},
             "output_refs": {"artifact_id": "Docker image ID", "download_url": "Pull URL"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Artifacts", "function": "DeleteArtifact"}},
            {"namespace": "CI.Git", "function": "CreatePullRequest",
             "params": {"repository": "{repo_name}", "title": "Release {version}", "source_branch": "release/{version}",
                        "target_branch": "main", "reviewers": ["alice", "bob"]},
             "output_refs": {"pr_number": "Release PR #"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Artifact Management", "domain": domain_c2,
        "nl_template": "Upload {artifact_name} and create a pull request for the release branch",
        "actions": [
            {"namespace": "CI.Artifacts", "function": "UploadArtifact",
             "params": {"artifact_name": "{artifact_name}", "version": "{version}", "repository": "{repository}",
                        "checksum": "{checksum}"},
             "output_refs": {"artifact_id": "Package ID"},
             "depends_on": []},
            {"namespace": "CI.Git", "function": "CreateBranch",
             "params": {"repository": "{repo_name}", "branch_name": "release/{branch_name}", "source_branch": "develop"},
             "output_refs": {"branch_name": "Release branch"},
             "depends_on": [1]},
            {"namespace": "CI.Git", "function": "CreatePullRequest",
             "params": {"repository": "{repo_name}", "title": "Release PR", "source_branch": "release/{branch_name}",
                        "target_branch": "main", "reviewers": ["diana"]},
             "output_refs": {"pr_number": "PR number"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Artifact Management", "domain": domain_c2,
        "nl_template": "Upload {artifact_name} to {repository} with version {version} and delete old artifact",
        "actions": [
            {"namespace": "CI.Artifacts", "function": "UploadArtifact",
             "params": {"artifact_name": "{artifact_name}", "version": "{version}", "repository": "{repository}",
                        "checksum": "{checksum}"},
             "output_refs": {"artifact_id": "New artifact ID"},
             "depends_on": []},
            {"namespace": "CI.Artifacts", "function": "DeleteArtifact",
             "params": {"artifact_id": "{{steps[1].output.artifact_id}}"},
             "output_refs": {"deleted": "deleted"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 12: Git/Version Control ---
TEMPLATES.extend([
    {
        "sector": "Git/Version Control", "domain": domain_c2,
        "nl_template": "Create branch {branch_name} from {source_branch} in repository {repository}",
        "actions": [
            {"namespace": "CI.Git", "function": "CreateBranch",
             "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "{source_branch}"},
             "output_refs": {"branch_name": "New branch", "commit_hash": "HEAD commit"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Git/Version Control", "domain": domain_c2,
        "nl_template": "Create feature branch {branch_name} from {source_branch} in {repository}, then open a pull request with rollback on merge failure",
        "actions": [
            {"namespace": "CI.Git", "function": "CreateBranch",
             "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "{source_branch}"},
             "output_refs": {"branch_name": "Feature branch"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Git", "function": "DeleteBranch"}},
            {"namespace": "CI.Git", "function": "CreatePullRequest",
             "params": {"repository": "{repository}", "title": "{pr_title}", "source_branch": "{branch_name}",
                        "target_branch": "{target_branch}", "reviewers": "{reviewers}"},
             "output_refs": {"pr_number": "PR number", "url": "PR URL"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Git/Version Control", "domain": domain_c2,
        "nl_template": "Create branch {branch_name}, open PR, merge with {merge_method}, and delete the branch",
        "actions": [
            {"namespace": "CI.Git", "function": "CreateBranch",
             "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "{source_branch}"},
             "output_refs": {"branch_name": "Feature branch"},
             "depends_on": []},
            {"namespace": "CI.Git", "function": "CreatePullRequest",
             "params": {"repository": "{repository}", "title": "{pr_title}", "source_branch": "{branch_name}",
                        "target_branch": "{target_branch}", "reviewers": "{reviewers}"},
             "output_refs": {"pr_number": "PR number"},
             "depends_on": [1]},
            {"namespace": "CI.Git", "function": "MergePullRequest",
             "params": {"repository": "{repository}", "pr_number": "{{steps[2].output.pr_number}}", "merge_method": "{merge_method}",
                        "delete_source_branch": True},
             "output_refs": {"merge_commit": "Merge SHA"},
             "depends_on": [2]},
            {"namespace": "CI.Git", "function": "DeleteBranch",
             "params": {"repository": "{repository}", "branch_name": "{{steps[1].output.branch_name}}"},
             "output_refs": {"deleted_branch": "Branch deleted"},
             "depends_on": [3]},
        ]
    },
    {
        "sector": "Git/Version Control", "domain": domain_c2,
        "nl_template": "Create branch {branch_name} in {repository} with rollback if branch creation fails",
        "actions": [
            {"namespace": "CI.Git", "function": "CreateBranch",
             "params": {"repository": "{repository}", "branch_name": "{branch_name}", "source_branch": "{source_branch}"},
             "output_refs": {"branch_name": "Created branch"},
             "depends_on": [], "rollback_ref": {"namespace": "CI.Git", "function": "DeleteBranch"}},
        ]
    },
    {
        "sector": "Git/Version Control", "domain": domain_c2,
        "nl_template": "Open PR for {branch_name} in {repository} targeting {target_branch} with reviewers",
        "actions": [
            {"namespace": "CI.Git", "function": "CreatePullRequest",
             "params": {"repository": "{repository}", "title": "{pr_title}", "source_branch": "{branch_name}",
                        "target_branch": "{target_branch}", "reviewers": "{reviewers}"},
             "output_refs": {"pr_number": "PR number", "url": "URL"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Git/Version Control", "domain": domain_c2,
        "nl_template": "Create branch from {source_branch} in {repository}, open PR targeting {target_branch}, merge with squash",
        "actions": [
            {"namespace": "CI.Git", "function": "CreateBranch",
             "params": {"repository": "{repository}", "branch_name": "feat/{branch_name}", "source_branch": "{source_branch}"},
             "output_refs": {"branch_name": "Feature branch"},
             "depends_on": []},
            {"namespace": "CI.Git", "function": "CreatePullRequest",
             "params": {"repository": "{repository}", "title": "{pr_title}", "source_branch": "feat/{branch_name}",
                        "target_branch": "{target_branch}", "reviewers": "{reviewers}"},
             "output_refs": {"pr_number": "PR #"},
             "depends_on": [1]},
            {"namespace": "CI.Git", "function": "MergePullRequest",
             "params": {"repository": "{repository}", "pr_number": "{{steps[2].output.pr_number}}",
                        "merge_method": "squash", "delete_source_branch": True},
             "output_refs": {"merge_commit": "Squash merge SHA"},
             "depends_on": [2]},
        ]
    },
])

# ===========================================================================
# DOMAIN 3: CRM/Sales
# ===========================================================================
domain_c3 = "CRM/Sales"

# --- Sector 13: Leads Management ---
TEMPLATES.extend([
    {
        "sector": "Leads Management", "domain": domain_c3,
        "nl_template": "Create a lead for {first_name} {last_name} from {company} sourced via {source}",
        "actions": [
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{company}", "source": "{source}", "score": "{score}"},
             "output_refs": {"lead_id": "New lead ID", "full_name": "Lead full name"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Leads Management", "domain": domain_c3,
        "nl_template": "Create lead for {first_name} {last_name} from {company}, qualify with BANT, with rollback if qualification fails",
        "actions": [
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{company}", "source": "{source}", "score": "{score}"},
             "output_refs": {"lead_id": "Qualified lead ID", "full_name": "Name"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
            {"namespace": "CRM.Leads", "function": "QualifyLead",
             "params": {"lead_id": "{{steps[1].output.lead_id}}", "budget_available": "{budget_available}",
                        "authority_level": "{authority_level}", "timeline": "{timeline}"},
             "output_refs": {"qualification_score": "BANT score", "recommended_action": "Next step"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Leads Management", "domain": domain_c3,
        "nl_template": "Create lead {first_name} {last_name}, qualify, and convert to opportunity with rollback safeguards",
        "actions": [
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{company}", "source": "{source}", "score": 65},
             "output_refs": {"lead_id": "Converted lead", "full_name": "Name"},
             "depends_on": []},
            {"namespace": "CRM.Leads", "function": "QualifyLead",
             "params": {"lead_id": "{{steps[1].output.lead_id}}", "budget_available": True,
                        "authority_level": "director", "timeline": "1-3 months"},
             "output_refs": {"qualification_score": "Score", "bant_status": "Pass"},
             "depends_on": [1]},
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": 50000.0, "stage": "qualification",
                        "probability": 50, "lead_id": "{{steps[1].output.lead_id}}"},
             "output_refs": {"opportunity_id": "New opportunity ID"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Leads Management", "domain": domain_c3,
        "nl_template": "Create lead from {source} for {first_name} {last_name} at {company}, qualify, delete on failure",
        "actions": [
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{company}", "source": "{source}", "score": "{score}"},
             "output_refs": {"lead_id": "New lead"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
        ]
    },
    {
        "sector": "Leads Management", "domain": domain_c3,
        "nl_template": "Create {first_name} {last_name} lead from {company} (score {score}) and set up campaign",
        "actions": [
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{company}", "source": "{source}", "score": "{score}"},
             "output_refs": {"lead_id": "New lead ID"},
             "depends_on": []},
            {"namespace": "CRM.Campaigns", "function": "CreateCampaign",
             "params": {"campaign_name": "{campaign_name}", "type": "email", "budget": 5000.0,
                        "target_audience": "{target_audience}", "start_date": "{start_date}"},
             "output_refs": {"campaign_id": "Campaign ID"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Leads Management", "domain": domain_c3,
        "nl_template": "Create lead, qualify BANT, create opportunity, then clean up lead on failure with rollback path",
        "actions": [
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{company}", "source": "conference", "score": 80},
             "output_refs": {"lead_id": "Conference lead", "full_name": "Name"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Leads", "function": "DeleteLead"}},
            {"namespace": "CRM.Leads", "function": "QualifyLead",
             "params": {"lead_id": "{{steps[1].output.lead_id}}", "budget_available": True,
                        "authority_level": "c-level", "timeline": "immediate"},
             "output_refs": {"bant_result": "Qualified", "recommended_action": "Demo"},
             "depends_on": [1]},
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": 100000.0, "stage": "demo",
                        "probability": 75, "lead_id": "{{steps[1].output.lead_id}}"},
             "output_refs": {"opportunity_id": "High-value opp"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 14: Opportunities ---
TEMPLATES.extend([
    {
        "sector": "Opportunities", "domain": domain_c3,
        "nl_template": "Create opportunity {opportunity_name} worth ${amount} at {stage} stage",
        "actions": [
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "{stage}",
                        "probability": "{probability}", "lead_id": "{lead_id}"},
             "output_refs": {"opportunity_id": "Opportunity ID", "close_date": "Expected close"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Opportunities", "domain": domain_c3,
        "nl_template": "Create {opportunity_name} worth ${amount}, move to {new_stage}, roll back if lead is lost",
        "actions": [
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "prospecting",
                        "probability": 25, "lead_id": "{lead_id}"},
             "output_refs": {"opportunity_id": "Sales opp ID"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Opportunity", "function": "DeleteOpportunity"}},
            {"namespace": "CRM.Opportunity", "function": "UpdateOpportunityStage",
             "params": {"opportunity_id": "{{steps[1].output.opportunity_id}}", "new_stage": "{new_stage}",
                        "reason": "{stage_reason}"},
             "output_refs": {"previous_stage": "prospecting", "current_stage": "Updated stage"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Opportunities", "domain": domain_c3,
        "nl_template": "Create a ${amount} {opportunity_name} opportunity, update stage to {new_stage}, create quote",
        "actions": [
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "qualification",
                        "probability": 50, "lead_id": "{lead_id}"},
             "output_refs": {"opportunity_id": "Opp with quote"},
             "depends_on": []},
            {"namespace": "CRM.Opportunity", "function": "UpdateOpportunityStage",
             "params": {"opportunity_id": "{{steps[1].output.opportunity_id}}", "new_stage": "proposal",
                        "reason": "Proposal delivered"},
             "output_refs": {"current_stage": "proposal"},
             "depends_on": [1]},
            {"namespace": "CRM.Orders", "function": "CreateQuote",
             "params": {"opportunity_id": "{{steps[1].output.opportunity_id}}", "product": "{product}",
                        "quantity": "{quantity}", "unit_price": "{unit_price}", "discount_percent": "{discount_percent}"},
             "output_refs": {"quote_id": "Quote ID", "total_amount": "Total"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Opportunities", "domain": domain_c3,
        "nl_template": "Create opportunity and move through pipeline with rollback if deal falls through",
        "actions": [
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "qualification",
                        "probability": 25, "lead_id": "{lead_id}"},
             "output_refs": {"opportunity_id": "Pipeline opportunity"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Opportunity", "function": "DeleteOpportunity"}},
            {"namespace": "CRM.Opportunity", "function": "UpdateOpportunityStage",
             "params": {"opportunity_id": "{{steps[1].output.opportunity_id}}", "new_stage": "demo",
                        "reason": "Product demo completed"},
             "output_refs": {"updated_stage": "demo"},
             "depends_on": [1]},
            {"namespace": "CRM.Opportunity", "function": "UpdateOpportunityStage",
             "params": {"opportunity_id": "{{steps[1].output.opportunity_id}}", "new_stage": "negotiation",
                        "reason": "Budget approved"},
             "output_refs": {"final_stage": "negotiation"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Opportunities", "domain": domain_c3,
        "nl_template": "Close {opportunity_name} at ${amount} with {product} quote and convert to order",
        "actions": [
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "negotiation",
                        "probability": 90, "lead_id": "{lead_id}"},
             "output_refs": {"opportunity_id": "Closing opp"},
             "depends_on": []},
            {"namespace": "CRM.Orders", "function": "CreateQuote",
             "params": {"opportunity_id": "{{steps[1].output.opportunity_id}}", "product": "{product}",
                        "quantity": 10, "unit_price": 999.0, "discount_percent": 10},
             "output_refs": {"quote_id": "Final quote"},
             "depends_on": [1]},
            {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder",
             "params": {"quote_id": "{{steps[2].output.quote_id}}", "payment_terms": "net-30",
                        "shipping_method": "digital-delivery"},
             "output_refs": {"order_id": "Won order", "order_total": "Final amount"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Opportunities", "domain": domain_c3,
        "nl_template": "Create {opportunity_name} for {amount}, update to proposal stage with rollback on lost deal",
        "actions": [
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": "{amount}", "stage": "qualification",
                        "probability": 25, "lead_id": "{lead_id}"},
             "output_refs": {"opportunity_id": "New opp"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Opportunity", "function": "DeleteOpportunity"}},
            {"namespace": "CRM.Opportunity", "function": "UpdateOpportunityStage",
             "params": {"opportunity_id": "{{steps[1].output.opportunity_id}}", "new_stage": "proposal",
                        "reason": "Proposal delivered to client"},
             "output_refs": {"stage_update": "proposal"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 15: Campaigns ---
TEMPLATES.extend([
    {
        "sector": "Campaigns", "domain": domain_c3,
        "nl_template": "Create {campaign_name} campaign with {budget} budget targeting {target_audience}",
        "actions": [
            {"namespace": "CRM.Campaigns", "function": "CreateCampaign",
             "params": {"campaign_name": "{campaign_name}", "type": "{campaign_type}", "budget": "{budget}",
                        "target_audience": "{target_audience}", "start_date": "{start_date}"},
             "output_refs": {"campaign_id": "Campaign ID", "status": "draft"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Campaigns", "domain": domain_c3,
        "nl_template": "Create {campaign_name} campaign and launch it on {launch_channels} with rollback if launch fails",
        "actions": [
            {"namespace": "CRM.Campaigns", "function": "CreateCampaign",
             "params": {"campaign_name": "{campaign_name}", "type": "{campaign_type}", "budget": "{budget}",
                        "target_audience": "{target_audience}", "start_date": "{start_date}"},
             "output_refs": {"campaign_id": "Draft campaign ID"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Campaigns", "function": "DeleteCampaign"}},
            {"namespace": "CRM.Campaigns", "function": "LaunchCampaign",
             "params": {"campaign_id": "{{steps[1].output.campaign_id}}", "launch_channels": "{launch_channels}"},
             "output_refs": {"status": "active", "active_channels": "Live channels"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Campaigns", "domain": domain_c3,
        "nl_template": "Create email campaign for {target_audience} with {budget} budget and track via leads",
        "actions": [
            {"namespace": "CRM.Campaigns", "function": "CreateCampaign",
             "params": {"campaign_name": "{campaign_name}", "type": "email", "budget": "{budget}",
                        "target_audience": "{target_audience}", "start_date": "{start_date}"},
             "output_refs": {"campaign_id": "Email campaign ID"},
             "depends_on": []},
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{company}", "source": "campaign", "score": 35},
             "output_refs": {"lead_id": "Campaign lead ID"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Campaigns", "domain": domain_c3,
        "nl_template": "Create {campaign_name} campaign, launch it, delete if performance is poor with rollback",
        "actions": [
            {"namespace": "CRM.Campaigns", "function": "CreateCampaign",
             "params": {"campaign_name": "{campaign_name}", "type": "{campaign_type}", "budget": 25000.0,
                        "target_audience": "enterprise", "start_date": "2024-03-01"},
             "output_refs": {"campaign_id": "Enterprise campaign"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Campaigns", "function": "DeleteCampaign"}},
            {"namespace": "CRM.Campaigns", "function": "LaunchCampaign",
             "params": {"campaign_id": "{{steps[1].output.campaign_id}}",
                        "launch_channels": ["email", "linkedin"]},
             "output_refs": {"launch_status": "active"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Campaigns", "domain": domain_c3,
        "nl_template": "Create {campaign_name} social campaign with leads tracking and account association",
        "actions": [
            {"namespace": "CRM.Campaigns", "function": "CreateCampaign",
             "params": {"campaign_name": "{campaign_name}", "type": "social", "budget": 10000.0,
                        "target_audience": "mid-market", "start_date": "2024-02-01"},
             "output_refs": {"campaign_id": "Social campaign"},
             "depends_on": []},
            {"namespace": "CRM.Accounts", "function": "CreateAccount",
             "params": {"account_name": "{account_name}", "industry": "{industry}",
                        "size_employees": "{size_employees}", "tier": "{tier}"},
             "output_refs": {"account_id": "Target account"},
             "depends_on": [1]},
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{account_name}", "source": "social", "score": 50},
             "output_refs": {"lead_id": "Campaign lead"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Campaigns", "domain": domain_c3,
        "nl_template": "Create {campaign_name} with {budget} budget for {target_audience}, launch, track with leads",
        "actions": [
            {"namespace": "CRM.Campaigns", "function": "CreateCampaign",
             "params": {"campaign_name": "{campaign_name}", "type": "webinar", "budget": 15000.0,
                        "target_audience": "startups", "start_date": "2024-04-10"},
             "output_refs": {"campaign_id": "Webinar campaign"},
             "depends_on": []},
            {"namespace": "CRM.Campaigns", "function": "LaunchCampaign",
             "params": {"campaign_id": "{{steps[1].output.campaign_id}}",
                        "launch_channels": ["email", "webinar"]},
             "output_refs": {"launched": "active"},
             "depends_on": [1]},
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "Webinar", "last_name": "Attendee", "email": "webinar@example.com",
                        "company": "Startup Inc", "source": "webinar", "score": 60},
             "output_refs": {"lead_id": "Webinar lead"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 16: Contacts/Accounts ---
TEMPLATES.extend([
    {
        "sector": "Contacts/Accounts", "domain": domain_c3,
        "nl_template": "Create account {account_name} in {industry} industry with {size_employees} employees",
        "actions": [
            {"namespace": "CRM.Accounts", "function": "CreateAccount",
             "params": {"account_name": "{account_name}", "industry": "{industry}",
                        "size_employees": "{size_employees}", "tier": "{tier}"},
             "output_refs": {"account_id": "Account ID", "account_name": "Name"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Contacts/Accounts", "domain": domain_c3,
        "nl_template": "Create account {account_name} with {tier} tier and cleanup rollback on creation failure",
        "actions": [
            {"namespace": "CRM.Accounts", "function": "CreateAccount",
             "params": {"account_name": "{account_name}", "industry": "{industry}",
                        "size_employees": "{size_employees}", "tier": "{tier}"},
             "output_refs": {"account_id": "Account ID"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Accounts", "function": "DeleteAccount"}},
        ]
    },
    {
        "sector": "Contacts/Accounts", "domain": domain_c3,
        "nl_template": "Create {industry} account {account_name}, create lead, then create opportunity from it",
        "actions": [
            {"namespace": "CRM.Accounts", "function": "CreateAccount",
             "params": {"account_name": "{account_name}", "industry": "{industry}",
                        "size_employees": 500, "tier": "premium"},
             "output_refs": {"account_id": "Premium account"},
             "depends_on": []},
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{account_name}", "source": "referral", "score": 80},
             "output_refs": {"lead_id": "Account lead"},
             "depends_on": [1]},
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": 75000.0, "stage": "qualification",
                        "probability": 50, "lead_id": "{{steps[2].output.lead_id}}"},
             "output_refs": {"opportunity_id": "Account opp"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Contacts/Accounts", "domain": domain_c3,
        "nl_template": "Create {account_name} with {tier} tier, create support ticket with rollback on account issue",
        "actions": [
            {"namespace": "CRM.Accounts", "function": "CreateAccount",
             "params": {"account_name": "{account_name}", "industry": "{industry}",
                        "size_employees": 1000, "tier": "{tier}"},
             "output_refs": {"account_id": "Enterprise account"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Accounts", "function": "DeleteAccount"}},
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "Account setup - {account_name}", "priority": "medium", "category": "account",
                        "contact_email": "{email}", "account_id": "{{steps[1].output.account_id}}"},
             "output_refs": {"ticket_id": "Account ticket"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Contacts/Accounts", "domain": domain_c3,
        "nl_template": "Create account {account_name} and associated support ticket for onboarding",
        "actions": [
            {"namespace": "CRM.Accounts", "function": "CreateAccount",
             "params": {"account_name": "{account_name}", "industry": "{industry}",
                        "size_employees": "{size_employees}", "tier": "{tier}"},
             "output_refs": {"account_id": "New account ID", "account_name": "Name"},
             "depends_on": []},
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "Onboarding for {account_name}", "priority": "high", "category": "technical",
                        "contact_email": "admin@{account_name}.com", "account_id": "{{steps[1].output.account_id}}"},
             "output_refs": {"ticket_id": "Onboarding ticket"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Contacts/Accounts", "domain": domain_c3,
        "nl_template": "Create {account_name} account, lead, opportunity pipeline with full rollback path",
        "actions": [
            {"namespace": "CRM.Accounts", "function": "CreateAccount",
             "params": {"account_name": "{account_name}", "industry": "{industry}",
                        "size_employees": 200, "tier": "standard"},
             "output_refs": {"account_id": "Account ID"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Accounts", "function": "DeleteAccount"}},
            {"namespace": "CRM.Leads", "function": "CreateLead",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "email": "{email}",
                        "company": "{account_name}", "source": "partner", "score": 70},
             "output_refs": {"lead_id": "Partner lead"},
             "depends_on": [1]},
            {"namespace": "CRM.Opportunity", "function": "CreateOpportunity",
             "params": {"opportunity_name": "{opportunity_name}", "amount": 100000.0, "stage": "qualification",
                        "probability": 50, "lead_id": "{{steps[2].output.lead_id}}"},
             "output_refs": {"opportunity_id": "Pipeline opp"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 17: Quotes/Orders ---
TEMPLATES.extend([
    {
        "sector": "Quotes/Orders", "domain": domain_c3,
        "nl_template": "Create quote for {product} with quantity {quantity} at ${unit_price} each and {discount_percent}% discount",
        "actions": [
            {"namespace": "CRM.Orders", "function": "CreateQuote",
             "params": {"opportunity_id": "{opportunity_id}", "product": "{product}", "quantity": "{quantity}",
                        "unit_price": "{unit_price}", "discount_percent": "{discount_percent}"},
             "output_refs": {"quote_id": "Quote ID", "total_amount": "Total after discount"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Quotes/Orders", "domain": domain_c3,
        "nl_template": "Create quote for {product}, convert to order, with rollback if conversion fails",
        "actions": [
            {"namespace": "CRM.Orders", "function": "CreateQuote",
             "params": {"opportunity_id": "{opportunity_id}", "product": "{product}", "quantity": "{quantity}",
                        "unit_price": "{unit_price}", "discount_percent": 10},
             "output_refs": {"quote_id": "Quote for order", "total_amount": "Total"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Orders", "function": "DeleteQuote"}},
            {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder",
             "params": {"quote_id": "{{steps[1].output.quote_id}}", "payment_terms": "net-30",
                        "shipping_method": "digital-delivery"},
             "output_refs": {"order_id": "Converted order", "order_total": "Final total"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Quotes/Orders", "domain": domain_c3,
        "nl_template": "Create quote for {product}x{quantity}, convert to order, create ticket for support",
        "actions": [
            {"namespace": "CRM.Orders", "function": "CreateQuote",
             "params": {"opportunity_id": "{opportunity_id}", "product": "{product}", "quantity": "{quantity}",
                        "unit_price": 1999.0, "discount_percent": 5},
             "output_refs": {"quote_id": "Quote ID"},
             "depends_on": []},
            {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder",
             "params": {"quote_id": "{{steps[1].output.quote_id}}", "payment_terms": "net-60",
                        "shipping_method": "express"},
             "output_refs": {"order_id": "Order ID", "order_total": "Total"},
             "depends_on": [1]},
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "Order {order_id} - Support", "priority": "low", "category": "technical",
                        "contact_email": "support@example.com", "account_id": "acct_default"},
             "output_refs": {"ticket_id": "Post-order ticket"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Quotes/Orders", "domain": domain_c3,
        "nl_template": "Create quote, convert to order, then delete quote with rollback on conversion",
        "actions": [
            {"namespace": "CRM.Orders", "function": "CreateQuote",
             "params": {"opportunity_id": "{opportunity_id}", "product": "{product}", "quantity": 5,
                        "unit_price": 4999.0, "discount_percent": 15},
             "output_refs": {"quote_id": "Temp quote"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Orders", "function": "DeleteQuote"}},
            {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder",
             "params": {"quote_id": "{{steps[1].output.quote_id}}", "payment_terms": "due-on-receipt",
                        "shipping_method": "standard"},
             "output_refs": {"order_id": "Confirmed order"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Quotes/Orders", "domain": domain_c3,
        "nl_template": "Create {product} quote for opp {opportunity_id}, convert with net-30 terms",
        "actions": [
            {"namespace": "CRM.Orders", "function": "CreateQuote",
             "params": {"opportunity_id": "{opportunity_id}", "product": "{product}", "quantity": 25,
                        "unit_price": 999.0, "discount_percent": "{discount_percent}"},
             "output_refs": {"quote_id": "Bulk quote"},
             "depends_on": []},
            {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder",
             "params": {"quote_id": "{{steps[1].output.quote_id}}", "payment_terms": "net-30",
                        "shipping_method": "{shipping_method}"},
             "output_refs": {"order_id": "Bulk order", "order_total": "Total"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Quotes/Orders", "domain": domain_c3,
        "nl_template": "Enterprise quote for {product} with {discount_percent}% discount, convert to order with support ticket",
        "actions": [
            {"namespace": "CRM.Orders", "function": "CreateQuote",
             "params": {"opportunity_id": "{opportunity_id}", "product": "{product}", "quantity": 100,
                        "unit_price": 499.0, "discount_percent": "{discount_percent}"},
             "output_refs": {"quote_id": "Enterprise quote", "total_amount": "Total"},
             "depends_on": []},
            {"namespace": "CRM.Orders", "function": "ConvertQuoteToOrder",
             "params": {"quote_id": "{{steps[1].output.quote_id}}", "payment_terms": "net-60",
                        "shipping_method": "digital-delivery"},
             "output_refs": {"order_id": "Enterprise order"},
             "depends_on": [1]},
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "Enterprise delivery - {product}", "priority": "high", "category": "technical",
                        "contact_email": "enterprise@company.com", "account_id": "acct_ent"},
             "output_refs": {"ticket_id": "Delivery ticket"},
             "depends_on": [2]},
        ]
    },
])

# --- Sector 18: Customer Service ---
TEMPLATES.extend([
    {
        "sector": "Customer Service", "domain": domain_c3,
        "nl_template": "Create support ticket for {subject} with {priority} priority in {category} category",
        "actions": [
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "{subject}", "priority": "{priority}", "category": "{category}",
                        "contact_email": "{contact_email}", "account_id": "{account_id}"},
             "output_refs": {"ticket_id": "Ticket ID", "status": "open"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Support", "function": "CloseTicket"}},
        ]
    },
    {
        "sector": "Customer Service", "domain": domain_c3,
        "nl_template": "Create {priority} ticket for {subject}, resolve it, close with {satisfaction_score} CSAT score",
        "actions": [
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "{subject}", "priority": "{priority}", "category": "{category}",
                        "contact_email": "{contact_email}", "account_id": "{account_id}"},
             "output_refs": {"ticket_id": "Resolved ticket", "status": "open"},
             "depends_on": []},
            {"namespace": "CRM.Support", "function": "CloseTicket",
             "params": {"ticket_id": "{{steps[1].output.ticket_id}}", "resolution": "{resolution}",
                        "satisfaction_score": "{satisfaction_score}"},
             "output_refs": {"closed_status": "closed", "satisfaction": "Score"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Customer Service", "domain": domain_c3,
        "nl_template": "Create support ticket for {subject}, resolve, with rollback on resolution failure",
        "actions": [
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "{subject}", "priority": "critical", "category": "bug",
                        "contact_email": "{contact_email}", "account_id": "{account_id}"},
             "output_refs": {"ticket_id": "Critical bug ticket"},
             "depends_on": [], "rollback_ref": {"namespace": "CRM.Support", "function": "CloseTicket"}},
            {"namespace": "CRM.Support", "function": "CloseTicket",
             "params": {"ticket_id": "{{steps[1].output.ticket_id}}", "resolution": "Bug fix deployed",
                        "satisfaction_score": 4},
             "output_refs": {"resolved": "closed"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Customer Service", "domain": domain_c3,
        "nl_template": "Support workflow: create ticket for {subject}, escalate, then close with rollback on escalation fail",
        "actions": [
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "{subject}", "priority": "high", "category": "billing",
                        "contact_email": "{contact_email}", "account_id": "{account_id}"},
             "output_refs": {"ticket_id": "Escalated ticket"},
             "depends_on": []},
            {"namespace": "CRM.Support", "function": "CloseTicket",
             "params": {"ticket_id": "{{steps[1].output.ticket_id}}", "resolution": "Issue resolved after escalation",
                        "satisfaction_score": 3},
             "output_refs": {"closed": "closed"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Customer Service", "domain": domain_c3,
        "nl_template": "Handle billing inquiry: create ticket for {subject}, resolve, and close with satisfaction survey",
        "actions": [
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "{subject}", "priority": "medium", "category": "billing",
                        "contact_email": "billing@company.com", "account_id": "{account_id}"},
             "output_refs": {"ticket_id": "Billing ticket"},
             "depends_on": []},
            {"namespace": "CRM.Support", "function": "CloseTicket",
             "params": {"ticket_id": "{{steps[1].output.ticket_id}}", "resolution": "Billing discrepancy corrected",
                        "satisfaction_score": 5},
             "output_refs": {"closed_ticket": "closed"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Customer Service", "domain": domain_c3,
        "nl_template": "Create {priority} priority {category} ticket for urgent issue and resolve it",
        "actions": [
            {"namespace": "CRM.Support", "function": "CreateTicket",
             "params": {"subject": "{subject}", "priority": "{priority}", "category": "{category}",
                        "contact_email": "{contact_email}", "account_id": "{account_id}"},
             "output_refs": {"ticket_id": "Urgent ticket"},
             "depends_on": []},
            {"namespace": "CRM.Support", "function": "CloseTicket",
             "params": {"ticket_id": "{{steps[1].output.ticket_id}}", "resolution": "{resolution}",
                        "satisfaction_score": "{satisfaction_score}"},
             "output_refs": {"status": "closed", "csat": "Score"},
             "depends_on": [1]},
        ]
    },
])

# ===========================================================================
# DOMAIN 4: FinTech/Payments
# ===========================================================================
domain_c4 = "FinTech/Payments"

# --- Sector 19: Payment Processing ---
TEMPLATES.extend([
    {
        "sector": "Payment Processing", "domain": domain_c4,
        "nl_template": "Capture payment of ${amount_cents/100} from customer {customer_id} using {payment_method}",
        "actions": [
            {"namespace": "Payments.Processing", "function": "CapturePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}",
                        "payment_method": "{payment_method}", "description": "{description}"},
             "output_refs": {"payment_id": "Payment ID", "status": "completed", "receipt_url": "Receipt"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Payment Processing", "domain": domain_c4,
        "nl_template": "Capture {currency} {amount_cents/100} from {customer_id}, refund if customer requests cancellation",
        "actions": [
            {"namespace": "Payments.Processing", "function": "CapturePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}",
                        "payment_method": "credit_card", "description": "{description}"},
             "output_refs": {"payment_id": "Payable payment", "receipt_url": "Receipt"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        ]
    },
    {
        "sector": "Payment Processing", "domain": domain_c4,
        "nl_template": "Authorize {currency} {amount_cents/100} from {customer_id}, capture, then full refund with rollback",
        "actions": [
            {"namespace": "Payments.Processing", "function": "AuthorizePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}",
                        "payment_method": "credit_card"},
             "output_refs": {"authorization_id": "Auth hold ID", "status": "authorized"},
             "depends_on": []},
            {"namespace": "Payments.Processing", "function": "CapturePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}",
                        "payment_method": "credit_card", "description": "Authorized payment capture"},
             "output_refs": {"payment_id": "Captured payment", "charge_fee_cents": "Fee"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Payment Processing", "domain": domain_c4,
        "nl_template": "Capture {currency} {amount_cents/100} from {customer_id} and set up refund rollback for subscription cancellation",
        "actions": [
            {"namespace": "Payments.Processing", "function": "CapturePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": 9999, "currency": "{currency}",
                        "payment_method": "debit_card", "description": "Monthly subscription"},
             "output_refs": {"payment_id": "Subscription payment", "receipt_url": "Receipt URL"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Processing", "function": "RefundPayment"}},
        ]
    },
    {
        "sector": "Payment Processing", "domain": domain_c4,
        "nl_template": "Authorize {amount_cents/100} from {customer_id}, capture full amount with fraud check",
        "actions": [
            {"namespace": "Payments.Processing", "function": "AuthorizePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": "{amount_cents}", "currency": "{currency}",
                        "payment_method": "credit_card"},
             "output_refs": {"authorization_id": "Auth hold", "expires_at": "Expire time"},
             "depends_on": []},
            {"namespace": "Payments.Processing", "function": "CapturePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": "{{steps[1].output.authorization_id}}",
                        "currency": "{currency}", "payment_method": "credit_card",
                        "description": "Authorized payment capture"},
             "output_refs": {"payment_id": "Final payment ID"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Payment Processing", "domain": domain_c4,
        "nl_template": "Process customer refund: capture original payment of {amount_cents}, then refund with reason",
        "actions": [
            {"namespace": "Payments.Processing", "function": "CapturePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": 49999, "currency": "USD",
                        "payment_method": "credit_card", "description": "Original purchase"},
             "output_refs": {"payment_id": "Original payment ID"},
             "depends_on": []},
            {"namespace": "Payments.Processing", "function": "RefundPayment",
             "params": {"payment_id": "{{steps[1].output.payment_id}}", "amount_cents": 0,
                        "reason": "customer_request"},
             "output_refs": {"refund_id": "Full refund", "amount_cents": "Refunded amount"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 20: Invoicing/Billing ---
TEMPLATES.extend([
    {
        "sector": "Invoicing/Billing", "domain": domain_c4,
        "nl_template": "Create invoice for customer {customer_id} with {currency} billing and {tax_rate_percent}% tax",
        "actions": [
            {"namespace": "Payments.Invoicing", "function": "CreateInvoice",
             "params": {"customer_id": "{customer_id}", "line_items": "{line_items}", "due_date": "{due_date}",
                        "tax_rate_percent": "{tax_rate_percent}", "currency": "{currency}"},
             "output_refs": {"invoice_id": "Invoice ID", "total_cents": "Total in cents", "status": "pending"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Invoicing/Billing", "domain": domain_c4,
        "nl_template": "Create invoice for {customer_id}, send it, void if customer disputes with rollback",
        "actions": [
            {"namespace": "Payments.Invoicing", "function": "CreateInvoice",
             "params": {"customer_id": "{customer_id}", "line_items": "{line_items}", "due_date": "{due_date}",
                        "tax_rate_percent": 10.0, "currency": "{currency}"},
             "output_refs": {"invoice_id": "Sent invoice"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Invoicing", "function": "VoidInvoice"}},
            {"namespace": "Payments.Invoicing", "function": "SendInvoice",
             "params": {"invoice_id": "{{steps[1].output.invoice_id}}", "delivery_method": "email",
                        "cc_emails": "{cc_emails}"},
             "output_refs": {"sent_status": "sent", "delivery_method": "email"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Invoicing/Billing", "domain": domain_c4,
        "nl_template": "Create {currency} invoice for {customer_id}, send to customer, capture payment against it",
        "actions": [
            {"namespace": "Payments.Invoicing", "function": "CreateInvoice",
             "params": {"customer_id": "{customer_id}", "line_items": "{line_items}", "due_date": "{due_date}",
                        "tax_rate_percent": 8.5, "currency": "{currency}"},
             "output_refs": {"invoice_id": "Payable invoice", "total_cents": "Amount due"},
             "depends_on": []},
            {"namespace": "Payments.Invoicing", "function": "SendInvoice",
             "params": {"invoice_id": "{{steps[1].output.invoice_id}}", "delivery_method": "email",
                        "cc_emails": ["finance@company.com", "admin@company.com"]},
             "output_refs": {"sent": "sent"},
             "depends_on": [1]},
            {"namespace": "Payments.Processing", "function": "CapturePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": "{{steps[1].output.total_cents}}",
                        "currency": "{currency}", "payment_method": "ach", "description": "Invoice payment"},
             "output_refs": {"payment_id": "Payment for invoice"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Invoicing/Billing", "domain": domain_c4,
        "nl_template": "Create invoice {customer_id}, send with cc, void on customer request with rollback safeguards",
        "actions": [
            {"namespace": "Payments.Invoicing", "function": "CreateInvoice",
             "params": {"customer_id": "{customer_id}", "line_items": "{line_items}", "due_date": "{due_date}",
                        "tax_rate_percent": 5.0, "currency": "USD"},
             "output_refs": {"invoice_id": "USD invoice"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Invoicing", "function": "VoidInvoice"}},
            {"namespace": "Payments.Invoicing", "function": "SendInvoice",
             "params": {"invoice_id": "{{steps[1].output.invoice_id}}", "delivery_method": "email",
                        "cc_emails": ["billing@company.com"]},
             "output_refs": {"sent_date": "Timestamp"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Invoicing/Billing", "domain": domain_c4,
        "nl_template": "Full billing cycle: create invoice, send, capture payment, refund if service cancelled",
        "actions": [
            {"namespace": "Payments.Invoicing", "function": "CreateInvoice",
             "params": {"customer_id": "{customer_id}", "line_items": "{line_items}", "due_date": "2024-02-15",
                        "tax_rate_percent": 13.0, "currency": "EUR"},
             "output_refs": {"invoice_id": "EUR invoice", "total_cents": "Total EUR"},
             "depends_on": []},
            {"namespace": "Payments.Invoicing", "function": "SendInvoice",
             "params": {"invoice_id": "{{steps[1].output.invoice_id}}", "delivery_method": "portal",
                        "cc_emails": []},
             "output_refs": {"sent": "sent via portal"},
             "depends_on": [1]},
            {"namespace": "Payments.Processing", "function": "CapturePayment",
             "params": {"customer_id": "{customer_id}", "amount_cents": "{{steps[1].output.total_cents}}",
                        "currency": "EUR", "payment_method": "wire", "description": "Invoice payment EUR"},
             "output_refs": {"payment_id": "EUR payment ID", "receipt_url": "Receipt"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Invoicing/Billing", "domain": domain_c4,
        "nl_template": "Create invoice with {tax_rate_percent} tax for {customer_id}, send, capture + refund rollback path",
        "actions": [
            {"namespace": "Payments.Invoicing", "function": "CreateInvoice",
             "params": {"customer_id": "{customer_id}", "line_items": "{line_items}", "due_date": "2024-03-01",
                        "tax_rate_percent": "{tax_rate_percent}", "currency": "{currency}"},
             "output_refs": {"invoice_id": "Invoice", "total_cents": "Total"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Invoicing", "function": "VoidInvoice"}},
            {"namespace": "Payments.Invoicing", "function": "SendInvoice",
             "params": {"invoice_id": "{{steps[1].output.invoice_id}}", "delivery_method": "email",
                        "cc_emails": "{cc_emails}"},
             "output_refs": {"delivery_status": "sent"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 21: Account Management (Payments) ---
TEMPLATES.extend([
    {
        "sector": "Account Management", "domain": domain_c4,
        "nl_template": "Open a {account_type} account for {owner_name} with {currency} currency and {initial_deposit_cents} initial deposit",
        "actions": [
            {"namespace": "Payments.Accounts", "function": "CreateAccount",
             "params": {"owner_name": "{owner_name}", "account_type": "{account_type}",
                        "initial_deposit_cents": "{initial_deposit_cents}", "branch_code": "{branch_code}",
                        "currency": "{currency}"},
             "output_refs": {"account_id": "New account ID", "balance_cents": "Initial balance", "status": "active"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Account Management", "domain": domain_c4,
        "nl_template": "Open {account_type} account, deposit {initial_deposit_cents}, transfer funds with rollback if transfer fails",
        "actions": [
            {"namespace": "Payments.Accounts", "function": "CreateAccount",
             "params": {"owner_name": "{owner_name}", "account_type": "{account_type}",
                        "initial_deposit_cents": "{initial_deposit_cents}", "branch_code": "{branch_code}",
                        "currency": "{currency}"},
             "output_refs": {"account_id": "Source account", "balance_cents": "Balance"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Accounts", "function": "CloseAccount"}},
            {"namespace": "Payments.Accounts", "function": "TransferFunds",
             "params": {"source_account_id": "{{steps[1].output.account_id}}", "destination_account_id": "{dest_account}",
                        "amount_cents": 50000, "memo": "{transfer_memo}"},
             "output_refs": {"transfer_id": "Transfer ID", "status": "completed"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Account Management", "domain": domain_c4,
        "nl_template": "Open {owner_name}'s {account_type} account, deposit, transfer, and close with rollback path",
        "actions": [
            {"namespace": "Payments.Accounts", "function": "CreateAccount",
             "params": {"owner_name": "{owner_name}", "account_type": "checking", "initial_deposit_cents": 100000,
                        "branch_code": "NYC001", "currency": "USD"},
             "output_refs": {"account_id": "Checking account", "balance_cents": "100000"},
             "depends_on": []},
            {"namespace": "Payments.Accounts", "function": "TransferFunds",
             "params": {"source_account_id": "{{steps[1].output.account_id}}", "destination_account_id": "{dest_account}",
                        "amount_cents": 50000, "memo": "Initial transfer"},
             "output_refs": {"transfer_id": "Transfer txn ID"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Account Management", "domain": domain_c4,
        "nl_template": "Create merchant account for {owner_name}, flag fraud, clear flag with rollback on fraud",
        "actions": [
            {"namespace": "Payments.Accounts", "function": "CreateAccount",
             "params": {"owner_name": "{owner_name}", "account_type": "merchant", "initial_deposit_cents": 0,
                        "branch_code": "{branch_code}", "currency": "{currency}"},
             "output_refs": {"account_id": "Merchant account"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Accounts", "function": "CloseAccount"}},
        ]
    },
    {
        "sector": "Account Management", "domain": domain_c4,
        "nl_template": "Open escrow account, transfer settlement funds, generate report of all activity",
        "actions": [
            {"namespace": "Payments.Accounts", "function": "CreateAccount",
             "params": {"owner_name": "{owner_name}", "account_type": "escrow", "initial_deposit_cents": 500000,
                        "branch_code": "LON001", "currency": "GBP"},
             "output_refs": {"account_id": "Escrow account", "balance_cents": "Balance"},
             "depends_on": []},
            {"namespace": "Payments.Accounts", "function": "TransferFunds",
             "params": {"source_account_id": "{{steps[1].output.account_id}}", "destination_account_id": "{dest_account}",
                        "amount_cents": 250000, "memo": "Settlement disbursement"},
             "output_refs": {"settlement_txn": "Transfer complete"},
             "depends_on": [1]},
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "settlement_report", "start_date": "2024-01-01", "end_date": "2024-01-31",
                        "format": "csv", "group_by": "day"},
             "output_refs": {"report_id": "Settlement report", "download_url": "Report URL"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Account Management", "domain": domain_c4,
        "nl_template": "Open accounts for {owner_name}, transfer {transfer_memo}, generate report, close account rollback",
        "actions": [
            {"namespace": "Payments.Accounts", "function": "CreateAccount",
             "params": {"owner_name": "{owner_name}", "account_type": "savings", "initial_deposit_cents": 500000,
                        "branch_code": "BR001", "currency": "USD"},
             "output_refs": {"account_id": "Savings account"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Accounts", "function": "CloseAccount"}},
            {"namespace": "Payments.Accounts", "function": "TransferFunds",
             "params": {"source_account_id": "{{steps[1].output.account_id}}", "destination_account_id": "{dest_account}",
                        "amount_cents": 100000, "memo": "{transfer_memo}"},
             "output_refs": {"txn_id": "Transfer ID"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 22: Fraud Detection ---
TEMPLATES.extend([
    {
        "sector": "Fraud Detection", "domain": domain_c4,
        "nl_template": "Flag transaction {transaction_id} with risk score {risk_score} and {review_priority} priority",
        "actions": [
            {"namespace": "Payments.Fraud", "function": "FlagTransaction",
             "params": {"transaction_id": "{transaction_id}", "risk_score": "{risk_score}",
                        "flags": "{flags}", "review_priority": "{review_priority}"},
             "output_refs": {"flag_id": "Fraud flag ID", "risk_score": "Score", "status": "under_review"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Fraud Detection", "domain": domain_c4,
        "nl_template": "Flag transaction {transaction_id}, clear as false positive, with rollback if fraud confirmed",
        "actions": [
            {"namespace": "Payments.Fraud", "function": "FlagTransaction",
             "params": {"transaction_id": "{transaction_id}", "risk_score": 65, "flags": ["unusual_location"],
                        "review_priority": "high"},
             "output_refs": {"flag_id": "Flagged txn", "status": "under_review"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Fraud", "function": "ClearFlag"}},
            {"namespace": "Payments.Fraud", "function": "ClearFlag",
             "params": {"flag_id": "{{steps[1].output.flag_id}}", "review_result": "false_positive",
                        "reviewer_notes": "Customer verified identity"},
             "output_refs": {"cleared": "cleared", "previous_risk_score": "65"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Fraud Detection", "domain": domain_c4,
        "nl_template": "Flag {transaction_id} with velocity check flags and medium priority, clear if legitimate",
        "actions": [
            {"namespace": "Payments.Fraud", "function": "FlagTransaction",
             "params": {"transaction_id": "{transaction_id}", "risk_score": 40,
                        "flags": ["velocity_check", "new_device"], "review_priority": "medium"},
             "output_refs": {"flag_id": "Velocity flag"},
             "depends_on": []},
            {"namespace": "Payments.Fraud", "function": "ClearFlag",
             "params": {"flag_id": "{{steps[1].output.flag_id}}", "review_result": "legitimate",
                        "reviewer_notes": "Transaction matches usual pattern"},
             "output_refs": {"cleared_flag": "cleared"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Fraud Detection", "domain": domain_c4,
        "nl_template": "Flag high-risk transaction {transaction_id} with immediate review and KYC verification",
        "actions": [
            {"namespace": "Payments.Fraud", "function": "FlagTransaction",
             "params": {"transaction_id": "{transaction_id}", "risk_score": 85, "flags": ["large_amount", "high_risk_country"],
                        "review_priority": "immediate"},
             "output_refs": {"flag_id": "High risk flag"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Fraud", "function": "ClearFlag"}},
            {"namespace": "Payments.Compliance", "function": "SubmitKYC",
             "params": {"customer_id": "{customer_id}", "document_type": "passport", "country": "US",
                        "verification_level": "enhanced"},
             "output_refs": {"kyc_id": "KYC for flagged txn"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Fraud Detection", "domain": domain_c4,
        "nl_template": "Full fraud workflow: flag transaction, clear as false positive, submit KYC for customer",
        "actions": [
            {"namespace": "Payments.Fraud", "function": "FlagTransaction",
             "params": {"transaction_id": "{transaction_id}", "risk_score": 55,
                        "flags": ["unusual_location"], "review_priority": "medium"},
             "output_refs": {"flag_id": "Fraud review flag"},
             "depends_on": []},
            {"namespace": "Payments.Fraud", "function": "ClearFlag",
             "params": {"flag_id": "{{steps[1].output.flag_id}}", "review_result": "false_positive",
                        "reviewer_notes": "IP matched known location"},
             "output_refs": {"cleared_status": "cleared"},
             "depends_on": [1]},
            {"namespace": "Payments.Compliance", "function": "SubmitKYC",
             "params": {"customer_id": "{customer_id}", "document_type": "drivers_license", "country": "US",
                        "verification_level": "standard"},
             "output_refs": {"kyc_id": "KYC after flag"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Fraud Detection", "domain": domain_c4,
        "nl_template": "Flag {transaction_id} with {risk_score} risk score, clear with reviewer notes rollback coverage",
        "actions": [
            {"namespace": "Payments.Fraud", "function": "FlagTransaction",
             "params": {"transaction_id": "{transaction_id}", "risk_score": "{risk_score}",
                        "flags": "{flags}", "review_priority": "{review_priority}"},
             "output_refs": {"flag_id": "Flagged ID"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Fraud", "function": "ClearFlag"}},
        ]
    },
])

# --- Sector 23: Reporting/Analytics ---
TEMPLATES.extend([
    {
        "sector": "Reporting/Analytics", "domain": domain_c4,
        "nl_template": "Generate {report_type} report from {start_date} to {end_date} in {format} format grouped by {group_by}",
        "actions": [
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "{report_type}", "start_date": "{start_date}", "end_date": "{end_date}",
                        "format": "{format}", "group_by": "{group_by}"},
             "output_refs": {"report_id": "Report ID", "download_url": "URL", "record_count": "Count"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Reporting", "function": "DeleteReport"}},
        ]
    },
    {
        "sector": "Reporting/Analytics", "domain": domain_c4,
        "nl_template": "Generate {report_type} in {format} format for {start_date} to {end_date} and flag for review",
        "actions": [
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "{report_type}", "start_date": "{start_date}", "end_date": "{end_date}",
                        "format": "{format}", "group_by": "month"},
             "output_refs": {"report_id": "Monthly report ID"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Reporting", "function": "DeleteReport"}},
        ]
    },
    {
        "sector": "Reporting/Analytics", "domain": domain_c4,
        "nl_template": "Generate revenue report, chargeback report, and compliance KYC check in sequence",
        "actions": [
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "revenue_by_product", "start_date": "2024-01-01", "end_date": "2024-03-31",
                        "format": "xlsx", "group_by": "product"},
             "output_refs": {"revenue_report": "Revenue report URL", "start_date_used": "Start date of report"},
             "depends_on": []},
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "chargeback_report", "start_date": "{{steps[1].output.start_date_used}}", "end_date": "2024-03-31",
                        "format": "csv", "group_by": "week"},
             "output_refs": {"chargeback_report": "Chargeback report"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Reporting/Analytics", "domain": domain_c4,
        "nl_template": "Generate {report_type} for {start_date} to {end_date} grouped by {group_by} with rollback on missing data",
        "actions": [
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "{report_type}", "start_date": "{start_date}", "end_date": "{end_date}",
                        "format": "json", "group_by": "{group_by}"},
             "output_refs": {"report_id": "JSON report", "download_url": "URL"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Reporting/Analytics", "domain": domain_c4,
        "nl_template": "End-of-month: generate daily summary, monthly statement, and settlement report",
        "actions": [
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "daily_summary", "start_date": "2024-01-01", "end_date": "2024-01-31",
                        "format": "csv", "group_by": "day"},
             "output_refs": {"daily_report": "Daily summary URL"},
             "depends_on": []},
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "monthly_statement", "start_date": "2024-01-01", "end_date": "2024-01-31",
                        "format": "pdf", "group_by": "month"},
             "output_refs": {"monthly_statement": "PDF URL"},
             "depends_on": [1]},
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "settlement_report", "start_date": "2024-01-01", "end_date": "2024-01-31",
                        "format": "xlsx", "group_by": "product"},
             "output_refs": {"settlement_rpt": "Settlement report"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Reporting/Analytics", "domain": domain_c4,
        "nl_template": "Generate {report_type} from {start_date} to {end_date}, filter by {group_by} dimension",
        "actions": [
            {"namespace": "Payments.Reporting", "function": "GenerateReport",
             "params": {"report_type": "{report_type}", "start_date": "{start_date}", "end_date": "{end_date}",
                        "format": "{format}", "group_by": "{group_by}"},
             "output_refs": {"report_id": "Filtered report"},
             "depends_on": []},
        ]
    },
])

# --- Sector 24: Compliance/KYC ---
TEMPLATES.extend([
    {
        "sector": "Compliance/KYC", "domain": domain_c4,
        "nl_template": "Submit KYC for customer {customer_id} with {document_type} document from {country}",
        "actions": [
            {"namespace": "Payments.Compliance", "function": "SubmitKYC",
             "params": {"customer_id": "{customer_id}", "document_type": "{document_type}", "country": "{country}",
                        "verification_level": "{verification_level}"},
             "output_refs": {"kyc_id": "KYC submission ID", "status": "submitted"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Compliance/KYC", "domain": domain_c4,
        "nl_template": "Submit KYC for {customer_id}, approve, with rejection rollback if docs are insufficient",
        "actions": [
            {"namespace": "Payments.Compliance", "function": "SubmitKYC",
             "params": {"customer_id": "{customer_id}", "document_type": "{document_type}", "country": "{country}",
                        "verification_level": "standard"},
             "output_refs": {"kyc_id": "Submitted KYC"},
             "depends_on": []},
            {"namespace": "Payments.Compliance", "function": "ApproveKYC",
             "params": {"kyc_id": "{{steps[1].output.kyc_id}}", "notes": "Documents verified"},
             "output_refs": {"kyc_status": "approved", "verification_level": "standard"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Compliance/KYC", "domain": domain_c4,
        "nl_template": "Submit KYC for {customer_id} with {document_type}, approve or reject with rollback path",
        "actions": [
            {"namespace": "Payments.Compliance", "function": "SubmitKYC",
             "params": {"customer_id": "{customer_id}", "document_type": "{document_type}", "country": "{country}",
                        "verification_level": "enhanced"},
             "output_refs": {"kyc_id": "Enhanced KYC"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Compliance", "function": "RejectKYC"}},
            {"namespace": "Payments.Compliance", "function": "ApproveKYC",
             "params": {"kyc_id": "{{steps[1].output.kyc_id}}", "notes": "Identity confirmed"},
             "output_refs": {"approved": "approved", "verification_level": "enhanced"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Compliance/KYC", "domain": domain_c4,
        "nl_template": "Full compliance: submit KYC for {customer_id}, approve, and flag transaction for monitoring",
        "actions": [
            {"namespace": "Payments.Compliance", "function": "SubmitKYC",
             "params": {"customer_id": "{customer_id}", "document_type": "{document_type}", "country": "US",
                        "verification_level": "full"},
             "output_refs": {"kyc_id": "Full KYC submission"},
             "depends_on": []},
            {"namespace": "Payments.Compliance", "function": "ApproveKYC",
             "params": {"kyc_id": "{{steps[1].output.kyc_id}}", "notes": "All checks passed"},
             "output_refs": {"status": "approved", "customer_id": "Verified customer"},
             "depends_on": [1]},
            {"namespace": "Payments.Fraud", "function": "FlagTransaction",
             "params": {"transaction_id": "{transaction_id}", "risk_score": 30,
                        "flags": ["new_device"], "review_priority": "low"},
             "output_refs": {"flag_id": "Post-KYC flag"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Compliance/KYC", "domain": domain_c4,
        "nl_template": "Submit KYC with {document_type} for {customer_id}, approve, reject failed with rollback coverage",
        "actions": [
            {"namespace": "Payments.Compliance", "function": "SubmitKYC",
             "params": {"customer_id": "{customer_id}", "document_type": "passport", "country": "{country}",
                        "verification_level": "basic"},
             "output_refs": {"kyc_id": "Basic KYC"},
             "depends_on": [], "rollback_ref": {"namespace": "Payments.Compliance", "function": "RejectKYC"}},
            {"namespace": "Payments.Compliance", "function": "ApproveKYC",
             "params": {"kyc_id": "{{steps[1].output.kyc_id}}", "notes": "Basic verification passed"},
             "output_refs": {"approved_kyc": "approved"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Compliance/KYC", "domain": domain_c4,
        "nl_template": "Enhanced KYC for {customer_id} in {country} with full document verification and fraud check",
        "actions": [
            {"namespace": "Payments.Compliance", "function": "SubmitKYC",
             "params": {"customer_id": "{customer_id}", "document_type": "national_id", "country": "{country}",
                        "verification_level": "enhanced"},
             "output_refs": {"kyc_id": "Enhanced KYC submission"},
             "depends_on": []},
            {"namespace": "Payments.Compliance", "function": "ApproveKYC",
             "params": {"kyc_id": "{{steps[1].output.kyc_id}}", "notes": "Enhanced checks completed"},
             "output_refs": {"approved": "approved"},
             "depends_on": [1]},
        ]
    },
])

# ===========================================================================
# DOMAIN 5: HR/SaaS Operations
# ===========================================================================
domain_c5 = "HR/SaaS Operations"

# --- Sector 25: Employee Onboarding ---
TEMPLATES.extend([
    {
        "sector": "Employee Onboarding", "domain": domain_c5,
        "nl_template": "Create employee profile for {first_name} {last_name} as {job_title} in {department}",
        "actions": [
            {"namespace": "HR.Onboarding", "function": "CreateEmployeeProfile",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "department": "{department}",
                        "job_title": "{job_title}", "employment_type": "{employment_type}", "start_date": "{start_date}"},
             "output_refs": {"employee_id": "New hire ID", "email": "Work email"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Employee Onboarding", "domain": domain_c5,
        "nl_template": "Onboard {first_name} {last_name} as {job_title}, assign equipment, with termination rollback if onboarding fails",
        "actions": [
            {"namespace": "HR.Onboarding", "function": "CreateEmployeeProfile",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "department": "{department}",
                        "job_title": "{job_title}", "employment_type": "full-time", "start_date": "{start_date}"},
             "output_refs": {"employee_id": "New employee", "email": "Email"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Onboarding", "function": "TerminateEmployee"}},
            {"namespace": "HR.Onboarding", "function": "AssignEquipment",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "equipment_type": "laptop",
                        "equipment_model": "{equipment_model}", "asset_tag": "{asset_tag}"},
             "output_refs": {"asset_id": "Laptop assignment ID", "assignment_date": "Date"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Employee Onboarding", "domain": domain_c5,
        "nl_template": "Hire {first_name} {last_name} as {job_title}, assign equipment, set compensation, enroll in training",
        "actions": [
            {"namespace": "HR.Onboarding", "function": "CreateEmployeeProfile",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "department": "{department}",
                        "job_title": "{job_title}", "employment_type": "full-time", "start_date": "2024-02-01"},
             "output_refs": {"employee_id": "Engineering hire", "email": "Email"},
             "depends_on": []},
            {"namespace": "HR.Onboarding", "function": "AssignEquipment",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "equipment_type": "laptop",
                        "equipment_model": "MacBook Pro 16", "asset_tag": "{asset_tag}"},
             "output_refs": {"asset_id": "Asset assigned"},
             "depends_on": [1]},
            {"namespace": "HR.Payroll", "function": "SetCompensation",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_annual_cents": 12000000,
                        "currency": "USD", "effective_date": "2024-02-01"},
             "output_refs": {"compensation_id": "Salary record"},
             "depends_on": [2]},
            {"namespace": "HR.Training", "function": "EnrollEmployee",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_id": "{module_id}",
                        "due_date": "2024-03-31"},
             "output_refs": {"enrollment_id": "Training enrollment"},
             "depends_on": [3]},
        ]
    },
    {
        "sector": "Employee Onboarding", "domain": domain_c5,
        "nl_template": "Create employee profile for {first_name} {last_name}, enroll in security training with rollback on hire failure",
        "actions": [
            {"namespace": "HR.Onboarding", "function": "CreateEmployeeProfile",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "department": "{department}",
                        "job_title": "{job_title}", "employment_type": "full-time", "start_date": "{start_date}"},
             "output_refs": {"employee_id": "New employee ID", "email": "Email"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Onboarding", "function": "TerminateEmployee"}},
            {"namespace": "HR.Training", "function": "EnrollEmployee",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "module_id": "TRN-101",
                        "due_date": "2024-04-01"},
             "output_refs": {"enrollment_id": "Security training"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Employee Onboarding", "domain": domain_c5,
        "nl_template": "Full onboarding: create profile, assign laptop, set salary, submit leave request on first day",
        "actions": [
            {"namespace": "HR.Onboarding", "function": "CreateEmployeeProfile",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "department": "Engineering",
                        "job_title": "Software Engineer", "employment_type": "full-time", "start_date": "2024-03-04"},
             "output_refs": {"employee_id": "New SWE", "email": "swe@company.com"},
             "depends_on": []},
            {"namespace": "HR.Onboarding", "function": "AssignEquipment",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "equipment_type": "laptop",
                        "equipment_model": "Dell Latitude 5540", "asset_tag": "{asset_tag}"},
             "output_refs": {"asset_id": "Asset tag"},
             "depends_on": [1]},
            {"namespace": "HR.Payroll", "function": "SetCompensation",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "salary_annual_cents": 10000000,
                        "currency": "USD", "effective_date": "2024-03-04"},
             "output_refs": {"compensation_id": "Salary"},
             "depends_on": [2]},
            {"namespace": "HR.Leave", "function": "SubmitLeaveRequest",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "leave_type": "annual",
                        "start_date": "2024-04-01", "end_date": "2024-04-05", "reason": "Vacation"},
             "output_refs": {"leave_id": "Leave request"},
             "depends_on": [3]},
        ]
    },
    {
        "sector": "Employee Onboarding", "domain": domain_c5,
        "nl_template": "Create {first_name} {last_name} as {job_title} in {department}, assign equipment, terminate if probation fails with rollback",
        "actions": [
            {"namespace": "HR.Onboarding", "function": "CreateEmployeeProfile",
             "params": {"first_name": "{first_name}", "last_name": "{last_name}", "department": "Engineering",
                        "job_title": "{job_title}", "employment_type": "contract", "start_date": "{start_date}"},
             "output_refs": {"employee_id": "Contractor ID", "email": "Contractor email"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Onboarding", "function": "TerminateEmployee"}},
            {"namespace": "HR.Onboarding", "function": "AssignEquipment",
             "params": {"employee_id": "{{steps[1].output.employee_id}}", "equipment_type": "laptop",
                        "equipment_model": "ThinkPad X1 Carbon", "asset_tag": "{asset_tag}"},
             "output_refs": {"contractor_asset": "Asset assignment"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 26: Payroll ---
TEMPLATES.extend([
    {
        "sector": "Payroll", "domain": domain_c5,
        "nl_template": "Process payroll from {pay_period_start} to {pay_period_end} for {department_filter} department",
        "actions": [
            {"namespace": "HR.Payroll", "function": "ProcessPayroll",
             "params": {"pay_period_start": "{pay_period_start}", "pay_period_end": "{pay_period_end}",
                        "department_filter": "{department_filter}", "include_bonuses": "{include_bonuses}",
                        "overtime_rate": "{overtime_rate}"},
             "output_refs": {"payroll_id": "Payroll run ID", "employee_count": "Paid employees", "pay_date": "Scheduled"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Payroll", "domain": domain_c5,
        "nl_template": "Process bi-weekly payroll for {department_filter}, reverse with rollback if overpayment error",
        "actions": [
            {"namespace": "HR.Payroll", "function": "ProcessPayroll",
             "params": {"pay_period_start": "{pay_period_start}", "pay_period_end": "{pay_period_end}",
                        "department_filter": "{department_filter}", "include_bonuses": True, "overtime_rate": 1.5},
             "output_refs": {"payroll_id": "Payroll ID", "total_net_cents": "Net pay"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        ]
    },
    {
        "sector": "Payroll", "domain": domain_c5,
        "nl_template": "Process payroll with bonuses for {department_filter}, then set compensation for new hires",
        "actions": [
            {"namespace": "HR.Payroll", "function": "ProcessPayroll",
             "params": {"pay_period_start": "2024-01-01", "pay_period_end": "2024-01-15",
                        "department_filter": "Engineering", "include_bonuses": True, "overtime_rate": 1.5},
             "output_refs": {"payroll_id": "Engineering payroll", "total_net_cents": "Net amount", "pay_date": "Scheduled pay date"},
             "depends_on": []},
            {"namespace": "HR.Payroll", "function": "SetCompensation",
             "params": {"employee_id": "{employee_id}", "salary_annual_cents": 15000000,
                        "currency": "USD", "effective_date": "{{steps[1].output.pay_date}}"},
             "output_refs": {"compensation_id": "New comp record"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Payroll", "domain": domain_c5,
        "nl_template": "Process {department_filter} payroll with bonuses, reverse on error with rollback coverage",
        "actions": [
            {"namespace": "HR.Payroll", "function": "ProcessPayroll",
             "params": {"pay_period_start": "{pay_period_start}", "pay_period_end": "{pay_period_end}",
                        "department_filter": "{department_filter}", "include_bonuses": "{include_bonuses}",
                        "overtime_rate": 2.0},
             "output_refs": {"payroll_id": "Processed payroll"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
        ]
    },
    {
        "sector": "Payroll", "domain": domain_c5,
        "nl_template": "Monthly payroll: process for all departments, set bonuses, set individual compensation",
        "actions": [
            {"namespace": "HR.Payroll", "function": "ProcessPayroll",
             "params": {"pay_period_start": "2024-01-01", "pay_period_end": "2024-01-31",
                        "department_filter": "all", "include_bonuses": True, "overtime_rate": 1.5},
             "output_refs": {"payroll_id": "Monthly payroll run"},
             "depends_on": []},
            {"namespace": "HR.Payroll", "function": "SetCompensation",
             "params": {"employee_id": "{employee_id}", "salary_annual_cents": 18000000,
                        "currency": "USD", "effective_date": "2024-02-01"},
             "output_refs": {"comp_id": "Compensation"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Payroll", "domain": domain_c5,
        "nl_template": "Process payroll for {department_filter} with overtime {overtime_rate}x and rollback on miscalculation",
        "actions": [
            {"namespace": "HR.Payroll", "function": "ProcessPayroll",
             "params": {"pay_period_start": "{pay_period_start}", "pay_period_end": "{pay_period_end}",
                        "department_filter": "Sales", "include_bonuses": True, "overtime_rate": 2.0},
             "output_refs": {"payroll_id": "Sales payroll"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Payroll", "function": "ReversePayroll"}},
            {"namespace": "HR.Payroll", "function": "SetCompensation",
             "params": {"employee_id": "{employee_id}", "salary_annual_cents": 22000000,
                        "currency": "USD", "effective_date": "{pay_period_start}"},
             "output_refs": {"sales_comp": "Sales comp"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 27: Performance Reviews ---
TEMPLATES.extend([
    {
        "sector": "Performance Reviews", "domain": domain_c5,
        "nl_template": "Create {cycle_name} review cycle with {rating_scale} rating scale",
        "actions": [
            {"namespace": "HR.Performance", "function": "CreateReviewCycle",
             "params": {"cycle_name": "{cycle_name}", "review_period_start": "{review_period_start}",
                        "review_period_end": "{review_period_end}", "rating_scale": "{rating_scale}",
                        "include_self_review": "{include_self_review}", "include_peer_review": "{include_peer_review}"},
             "output_refs": {"cycle_id": "Review cycle ID", "cycle_name": "Name", "status": "open"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Performance Reviews", "domain": domain_c5,
        "nl_template": "Create {cycle_name} review cycle, submit review for employee, close with rollback on review failure",
        "actions": [
            {"namespace": "HR.Performance", "function": "CreateReviewCycle",
             "params": {"cycle_name": "{cycle_name}", "review_period_start": "{review_period_start}",
                        "review_period_end": "{review_period_end}", "rating_scale": "1-5",
                        "include_self_review": True, "include_peer_review": True},
             "output_refs": {"cycle_id": "Active review cycle"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Performance", "function": "CloseReviewCycle"}},
            {"namespace": "HR.Performance", "function": "SubmitReview",
             "params": {"cycle_id": "{{steps[1].output.cycle_id}}", "employee_id": "{employee_id}",
                        "reviewer_id": "{reviewer_id}", "rating": "{rating}", "comments": "{comments}"},
             "output_refs": {"review_id": "Submitted review"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Performance Reviews", "domain": domain_c5,
        "nl_template": "Create annual review cycle, submit reviews for multiple employees, close cycle",
        "actions": [
            {"namespace": "HR.Performance", "function": "CreateReviewCycle",
             "params": {"cycle_name": "Annual 2024 Review", "review_period_start": "2024-01-01",
                        "review_period_end": "2024-12-31", "rating_scale": "1-5",
                        "include_self_review": True, "include_peer_review": True},
             "output_refs": {"cycle_id": "Annual cycle ID"},
             "depends_on": []},
            {"namespace": "HR.Performance", "function": "SubmitReview",
             "params": {"cycle_id": "{{steps[1].output.cycle_id}}", "employee_id": "{employee_id}",
                        "reviewer_id": "{reviewer_id}", "rating": 4, "comments": "Strong performance annually"},
             "output_refs": {"review_id": "Annual review"},
             "depends_on": [1]},
            {"namespace": "HR.Performance", "function": "CloseReviewCycle",
             "params": {"cycle_id": "{{steps[1].output.cycle_id}}"},
             "output_refs": {"closed": "closed", "completion_rate": "Completion %"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Performance Reviews", "domain": domain_c5,
        "nl_template": "Create Q1 review cycle with self and peer review, submit ratings, rollback on poor cycle design",
        "actions": [
            {"namespace": "HR.Performance", "function": "CreateReviewCycle",
             "params": {"cycle_name": "Q1 2024 Review", "review_period_start": "2024-01-01",
                        "review_period_end": "2024-03-31", "rating_scale": "meets-exceeds",
                        "include_self_review": True, "include_peer_review": False},
             "output_refs": {"cycle_id": "Q1 cycle"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Performance", "function": "CloseReviewCycle"}},
        ]
    },
    {
        "sector": "Performance Reviews", "domain": domain_c5,
        "nl_template": "Mid-year review: create cycle, submit for {employee_id}, submit feedback, close out",
        "actions": [
            {"namespace": "HR.Performance", "function": "CreateReviewCycle",
             "params": {"cycle_name": "Mid-Year 2024", "review_period_start": "2024-01-01",
                        "review_period_end": "2024-06-30", "rating_scale": "1-10",
                        "include_self_review": True, "include_peer_review": True},
             "output_refs": {"cycle_id": "Mid-year cycle"},
             "depends_on": []},
            {"namespace": "HR.Performance", "function": "SubmitReview",
             "params": {"cycle_id": "{{steps[1].output.cycle_id}}", "employee_id": "{employee_id}",
                        "reviewer_id": "{reviewer_id}", "rating": 7, "comments": "Solid mid-year progress"},
             "output_refs": {"midyear_review": "Review submitted"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Performance Reviews", "domain": domain_c5,
        "nl_template": "Create {cycle_name} with {rating_scale} scale, submit reviews, close cycle with rollback coverage",
        "actions": [
            {"namespace": "HR.Performance", "function": "CreateReviewCycle",
             "params": {"cycle_name": "{cycle_name}", "review_period_start": "{review_period_start}",
                        "review_period_end": "{review_period_end}", "rating_scale": "{rating_scale}",
                        "include_self_review": "{include_self_review}", "include_peer_review": "{include_peer_review}"},
             "output_refs": {"cycle_id": "Review cycle"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Performance", "function": "CloseReviewCycle"}},
            {"namespace": "HR.Performance", "function": "SubmitReview",
             "params": {"cycle_id": "{{steps[1].output.cycle_id}}", "employee_id": "{employee_id}",
                        "reviewer_id": "{reviewer_id}", "rating": "{rating}", "comments": "{comments}"},
             "output_refs": {"review_id": "Employee review"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 28: Leave Management ---
TEMPLATES.extend([
    {
        "sector": "Leave Management", "domain": domain_c5,
        "nl_template": "Submit {leave_type} leave request for employee {employee_id} from {start_date} to {end_date}",
        "actions": [
            {"namespace": "HR.Leave", "function": "SubmitLeaveRequest",
             "params": {"employee_id": "{employee_id}", "leave_type": "{leave_type}", "start_date": "{start_date}",
                        "end_date": "{end_date}", "reason": "{reason}"},
             "output_refs": {"leave_id": "Leave request ID", "days_requested": "Days count", "status": "pending"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Leave Management", "domain": domain_c5,
        "nl_template": "Submit {leave_type} request, approve, cancel if plans change with rollback",
        "actions": [
            {"namespace": "HR.Leave", "function": "SubmitLeaveRequest",
             "params": {"employee_id": "{employee_id}", "leave_type": "{leave_type}", "start_date": "{start_date}",
                        "end_date": "{end_date}", "reason": "{reason}"},
             "output_refs": {"leave_id": "Leave to approve"},
             "depends_on": []},
            {"namespace": "HR.Leave", "function": "ApproveLeave",
             "params": {"leave_id": "{{steps[1].output.leave_id}}", "approved_by": "{approved_by}",
                        "notes": "Approved"},
             "output_refs": {"approved_status": "approved", "approved_at": "Timestamp"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Leave Management", "domain": domain_c5,
        "nl_template": "Submit {leave_type} leave, approve by manager, cancel with rollback on cancellation",
        "actions": [
            {"namespace": "HR.Leave", "function": "SubmitLeaveRequest",
             "params": {"employee_id": "{employee_id}", "leave_type": "{leave_type}", "start_date": "{start_date}",
                        "end_date": "{end_date}", "reason": "{reason}"},
             "output_refs": {"leave_id": "Leave request"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Leave", "function": "CancelLeaveRequest"}},
            {"namespace": "HR.Leave", "function": "ApproveLeave",
             "params": {"leave_id": "{{steps[1].output.leave_id}}", "approved_by": "{approved_by}", "notes": "Enjoy your leave"},
             "output_refs": {"approved": "approved"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Leave Management", "domain": domain_c5,
        "nl_template": "Submit sick leave for {employee_id}, approve, then cancel if health recovers",
        "actions": [
            {"namespace": "HR.Leave", "function": "SubmitLeaveRequest",
             "params": {"employee_id": "{employee_id}", "leave_type": "sick", "start_date": "2024-01-22",
                        "end_date": "2024-01-26", "reason": "Medical appointment"},
             "output_refs": {"leave_id": "Sick leave request"},
             "depends_on": []},
            {"namespace": "HR.Leave", "function": "ApproveLeave",
             "params": {"leave_id": "{{steps[1].output.leave_id}}", "approved_by": "{approved_by}", "notes": "Get well soon"},
             "output_refs": {"sick_approved": "approved"},
             "depends_on": [1]},
            {"namespace": "HR.Leave", "function": "CancelLeaveRequest",
             "params": {"leave_id": "{{steps[1].output.leave_id}}", "cancellation_reason": "Health recovered"},
             "output_refs": {"cancelled": "cancelled"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Leave Management", "domain": domain_c5,
        "nl_template": "Maternity leave for {employee_id}: submit, approve, with rollback on scheduling conflict",
        "actions": [
            {"namespace": "HR.Leave", "function": "SubmitLeaveRequest",
             "params": {"employee_id": "{employee_id}", "leave_type": "maternity", "start_date": "2024-04-15",
                        "end_date": "2024-07-15", "reason": "Maternity leave"},
             "output_refs": {"leave_id": "Maternity leave"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Leave", "function": "CancelLeaveRequest"}},
            {"namespace": "HR.Leave", "function": "ApproveLeave",
             "params": {"leave_id": "{{steps[1].output.leave_id}}", "approved_by": "{approved_by}", "notes": "Approved - coverage arranged"},
             "output_refs": {"maternity_approved": "approved"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Leave Management", "domain": domain_c5,
        "nl_template": "Submit annual leave for {employee_id}, approve by manager, with cancellation rollback",
        "actions": [
            {"namespace": "HR.Leave", "function": "SubmitLeaveRequest",
             "params": {"employee_id": "{employee_id}", "leave_type": "annual", "start_date": "{start_date}",
                        "end_date": "{end_date}", "reason": "Vacation"},
             "output_refs": {"leave_id": "Annual leave ID"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Leave", "function": "CancelLeaveRequest"}},
            {"namespace": "HR.Leave", "function": "ApproveLeave",
             "params": {"leave_id": "{{steps[1].output.leave_id}}", "approved_by": "{approved_by}", "notes": "Enjoy your vacation"},
             "output_refs": {"leave_approved": "approved"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 29: Recruiting ---
TEMPLATES.extend([
    {
        "sector": "Recruiting", "domain": domain_c5,
        "nl_template": "Create job posting for {job_title} in {department} at {location} with salary range ${salary_range_min}-${salary_range_max}",
        "actions": [
            {"namespace": "HR.Recruiting", "function": "CreateJobPosting",
             "params": {"job_title": "{job_title}", "department": "{department}", "location": "{location}",
                        "employment_type": "{employment_type}", "salary_range_min": "{salary_range_min}",
                        "salary_range_max": "{salary_range_max}"},
             "output_refs": {"posting_id": "Job posting ID", "application_url": "Apply URL", "status": "published"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Recruiting", "domain": domain_c5,
        "nl_template": "Create {job_title} posting, schedule interview with candidate, close posting with rollback on hire failure",
        "actions": [
            {"namespace": "HR.Recruiting", "function": "CreateJobPosting",
             "params": {"job_title": "{job_title}", "department": "{department}", "location": "{location}",
                        "employment_type": "full-time", "salary_range_min": 120000, "salary_range_max": 180000},
             "output_refs": {"posting_id": "Active job posting"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Recruiting", "function": "CloseJobPosting"}},
            {"namespace": "HR.Recruiting", "function": "ScheduleInterview",
             "params": {"candidate_name": "{candidate_name}", "posting_id": "{{steps[1].output.posting_id}}",
                        "interview_date": "{interview_date}", "interview_type": "{interview_type}",
                        "interviewers": "{interviewers}"},
             "output_refs": {"interview_id": "Scheduled interview", "status": "scheduled"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Recruiting", "domain": domain_c5,
        "nl_template": "Post {job_title} role in {department}, interview candidates, close when filled",
        "actions": [
            {"namespace": "HR.Recruiting", "function": "CreateJobPosting",
             "params": {"job_title": "{job_title}", "department": "{department}", "location": "{location}",
                        "employment_type": "{employment_type}", "salary_range_min": 150000, "salary_range_max": 220000},
             "output_refs": {"posting_id": "Senior role posting"},
             "depends_on": []},
            {"namespace": "HR.Recruiting", "function": "ScheduleInterview",
             "params": {"candidate_name": "{candidate_name}", "posting_id": "{{steps[1].output.posting_id}}",
                        "interview_date": "{interview_date}", "interview_type": "technical",
                        "interviewers": ["EMP-001", "EMP-002"]},
             "output_refs": {"interview_id": "Tech interview"},
             "depends_on": [1]},
            {"namespace": "HR.Recruiting", "function": "CloseJobPosting",
             "params": {"posting_id": "{{steps[1].output.posting_id}}", "reason": "position_filled"},
             "output_refs": {"closed_posting": "closed"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Recruiting", "domain": domain_c5,
        "nl_template": "Create {job_title} posting for {department} in {location}, schedule panel interview, close with rollback",
        "actions": [
            {"namespace": "HR.Recruiting", "function": "CreateJobPosting",
             "params": {"job_title": "{job_title}", "department": "Engineering", "location": "San Francisco, CA",
                        "employment_type": "full-time", "salary_range_min": 180000, "salary_range_max": 250000},
             "output_refs": {"posting_id": "Engineering posting"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Recruiting", "function": "CloseJobPosting"}},
            {"namespace": "HR.Recruiting", "function": "ScheduleInterview",
             "params": {"candidate_name": "{candidate_name}", "posting_id": "{{steps[1].output.posting_id}}",
                        "interview_date": "2024-02-01T10:00:00", "interview_type": "panel",
                        "interviewers": ["EMP-001", "EMP-004", "EMP-005"]},
             "output_refs": {"interview_id": "Panel interview"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Recruiting", "domain": domain_c5,
        "nl_template": "Post remote {job_title} role for {department}, interview by phone, close on hire",
        "actions": [
            {"namespace": "HR.Recruiting", "function": "CreateJobPosting",
             "params": {"job_title": "Senior Software Engineer", "department": "{department}", "location": "Remote - US",
                        "employment_type": "full-time", "salary_range_min": 120000, "salary_range_max": 180000},
             "output_refs": {"posting_id": "Remote posting"},
             "depends_on": []},
            {"namespace": "HR.Recruiting", "function": "ScheduleInterview",
             "params": {"candidate_name": "Alex Thompson", "posting_id": "{{steps[1].output.posting_id}}",
                        "interview_date": "2024-01-20T10:00:00", "interview_type": "phone_screen",
                        "interviewers": ["EMP-003"]},
             "output_refs": {"phone_interview": "Phone screen"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Recruiting", "domain": domain_c5,
        "nl_template": "Full recruiting: post {job_title}, interview {candidate_name}, close, with rollback if no candidates",
        "actions": [
            {"namespace": "HR.Recruiting", "function": "CreateJobPosting",
             "params": {"job_title": "{job_title}", "department": "{department}", "location": "{location}",
                        "employment_type": "{employment_type}", "salary_range_min": "{salary_range_min}",
                        "salary_range_max": "{salary_range_max}"},
             "output_refs": {"posting_id": "Job posting", "status": "published"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Recruiting", "function": "CloseJobPosting"}},
            {"namespace": "HR.Recruiting", "function": "ScheduleInterview",
             "params": {"candidate_name": "{candidate_name}", "posting_id": "{{steps[1].output.posting_id}}",
                        "interview_date": "{interview_date}", "interview_type": "{interview_type}",
                        "interviewers": "{interviewers}"},
             "output_refs": {"interview_id": "Scheduled interview"},
             "depends_on": [1]},
        ]
    },
])

# --- Sector 30: Training ---
TEMPLATES.extend([
    {
        "sector": "Training", "domain": domain_c5,
        "nl_template": "Create training module {module_name} in {category} category with {duration_hours} hours duration",
        "actions": [
            {"namespace": "HR.Training", "function": "CreateTrainingModule",
             "params": {"module_name": "{module_name}", "category": "{category}", "duration_hours": "{duration_hours}",
                        "required_for_all": "{required_for_all}", "certification_available": "{certification_available}"},
             "output_refs": {"module_id": "Module ID", "module_name": "Name", "status": "published"},
             "depends_on": []},
        ]
    },
    {
        "sector": "Training", "domain": domain_c5,
        "nl_template": "Create {module_name} training module, enroll employees, complete with scores with rollback on enrollment failure",
        "actions": [
            {"namespace": "HR.Training", "function": "CreateTrainingModule",
             "params": {"module_name": "{module_name}", "category": "{category}", "duration_hours": 4.0,
                        "required_for_all": True, "certification_available": True},
             "output_refs": {"module_id": "Published module"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Training", "function": "DeleteTrainingModule"}},
            {"namespace": "HR.Training", "function": "EnrollEmployee",
             "params": {"employee_id": "{employee_id}", "module_id": "{{steps[1].output.module_id}}",
                        "due_date": "{due_date}"},
             "output_refs": {"enrollment_id": "Enrolled employee"},
             "depends_on": [1]},
            {"namespace": "HR.Training", "function": "CompleteTraining",
             "params": {"enrollment_id": "{{steps[2].output.enrollment_id}}", "score": 90,
                        "feedback": "Very helpful training"},
             "output_refs": {"completed": "completed", "score": "90", "certificate_url": "Cert URL"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Training", "domain": domain_c5,
        "nl_template": "Create {module_name} compliance module, enroll {employee_id}, complete, delete module when deprecated",
        "actions": [
            {"namespace": "HR.Training", "function": "CreateTrainingModule",
             "params": {"module_name": "Security Awareness", "category": "compliance", "duration_hours": 2.0,
                        "required_for_all": True, "certification_available": False},
             "output_refs": {"module_id": "Compliance module"},
             "depends_on": []},
            {"namespace": "HR.Training", "function": "EnrollEmployee",
             "params": {"employee_id": "{employee_id}", "module_id": "{{steps[1].output.module_id}}", "due_date": "2024-03-01"},
             "output_refs": {"enrollment_id": "Compliance enrollment"},
             "depends_on": [1]},
            {"namespace": "HR.Training", "function": "CompleteTraining",
             "params": {"enrollment_id": "{{steps[2].output.enrollment_id}}", "score": 85, "feedback": "Good content"},
             "output_refs": {"completed": "completed"},
             "depends_on": [2]},
            {"namespace": "HR.Training", "function": "DeleteTrainingModule",
             "params": {"module_id": "{{steps[1].output.module_id}}"},
             "output_refs": {"deleted": "deleted"},
             "depends_on": [3]},
        ]
    },
    {
        "sector": "Training", "domain": domain_c5,
        "nl_template": "Create {category} training module {module_name}, enroll multiple employees with rollback on content issues",
        "actions": [
            {"namespace": "HR.Training", "function": "CreateTrainingModule",
             "params": {"module_name": "{module_name}", "category": "technical", "duration_hours": 8.0,
                        "required_for_all": False, "certification_available": True},
             "output_refs": {"module_id": "Technical module"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Training", "function": "DeleteTrainingModule"}},
            {"namespace": "HR.Training", "function": "EnrollEmployee",
             "params": {"employee_id": "{employee_id}", "module_id": "{{steps[1].output.module_id}}",
                        "due_date": "2024-06-30"},
             "output_refs": {"enrollment_id": "Enrolled"},
             "depends_on": [1]},
        ]
    },
    {
        "sector": "Training", "domain": domain_c5,
        "nl_template": "Full training lifecycle: create {module_name}, enroll, complete, certify with score",
        "actions": [
            {"namespace": "HR.Training", "function": "CreateTrainingModule",
             "params": {"module_name": "AWS Fundamentals", "category": "technical", "duration_hours": 16.0,
                        "required_for_all": False, "certification_available": True},
             "output_refs": {"module_id": "AWS training"},
             "depends_on": []},
            {"namespace": "HR.Training", "function": "EnrollEmployee",
             "params": {"employee_id": "{employee_id}", "module_id": "{{steps[1].output.module_id}}",
                        "due_date": "2024-04-01"},
             "output_refs": {"enrollment_id": "AWS enrollment"},
             "depends_on": [1]},
            {"namespace": "HR.Training", "function": "CompleteTraining",
             "params": {"enrollment_id": "{{steps[2].output.enrollment_id}}", "score": 95, "feedback": "Excellent course"},
             "output_refs": {"certificate_url": "AWS cert URL"},
             "depends_on": [2]},
        ]
    },
    {
        "sector": "Training", "domain": domain_c5,
        "nl_template": "Create {module_name} {category} module, enroll employees, track completion with rollback coverage",
        "actions": [
            {"namespace": "HR.Training", "function": "CreateTrainingModule",
             "params": {"module_name": "{module_name}", "category": "{category}", "duration_hours": "{duration_hours}",
                        "required_for_all": "{required_for_all}", "certification_available": "{certification_available}"},
             "output_refs": {"module_id": "New module"},
             "depends_on": [], "rollback_ref": {"namespace": "HR.Training", "function": "DeleteTrainingModule"}},
            {"namespace": "HR.Training", "function": "EnrollEmployee",
             "params": {"employee_id": "{employee_id}", "module_id": "{{steps[1].output.module_id}}",
                        "due_date": "{due_date}"},
             "output_refs": {"enrollment_id": "Enrollment"},
             "depends_on": [1]},
            {"namespace": "HR.Training", "function": "CompleteTraining",
             "params": {"enrollment_id": "{{steps[2].output.enrollment_id}}", "score": "{score}",
                        "feedback": "{feedback}"},
             "output_refs": {"completed": "completed", "certificate_url": "Cert URL"},
             "depends_on": [2]},
        ]
    },
])

# Verification
sectors = set(t["sector"] for t in TEMPLATES)
domains = set(t["domain"] for t in TEMPLATES)
print(f"TEMPLATES: {len(TEMPLATES)} templates across {len(sectors)} sectors in {len(domains)} domains")

# Count rollback coverage
rollback_templates = [t for t in TEMPLATES if any(
    a.get("rollback_ref") for a in t["actions"]
)]
print(f"Templates with rollback paths: {len(rollback_templates)}")

# Count variable passing coverage
variable_templates = [t for t in TEMPLATES if any(
    "{{steps[" in str(a.get("params", {})) for a in t["actions"]
)]
print(f"Templates with variable passing: {len(variable_templates)}")