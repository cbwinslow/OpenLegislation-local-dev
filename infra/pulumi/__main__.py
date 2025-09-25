"""Pulumi entry point for multi-cloud OpenLegislation infrastructure."""

import pulumi
import pulumi_aws as aws
import pulumi_digitalocean as do
import pulumi_hetznercloud as hcloud
import pulumi_cloudflare as cloudflare
import pulumi_gcp as gcp
from pulumi import export, ResourceOptions

# Import stack-specific configs (e.g., from config.py or env)
import os

ENV = os.getenv('ENVIRONMENT', 'dev')
STACK = pulumi.get_stack()

# Common resources across clouds (orchestrated here)
# Example: Deploy app container to AWS ECS, DB to DO, edge to CF, etc.

# AWS: ECS for app containers
cluster = aws.ecs.Cluster(f"openleg-{ENV}-cluster",
    capacity_providers=["FARGATE"],
    default_capacity_provider_strategy=[aws.ecs.ClusterDefaultCapacityProviderStrategyArgs(
        capacity_provider="FARGATE",
        weight=1
    )])

task_role = aws.iam.Role(f"openleg-{ENV}-task-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }))

task_exec_role = aws.iam.Role(f"openleg-{ENV}-task-exec-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }))

aws.iam.RolePolicyAttachment(f"openleg-{ENV}-task-exec",
    role= task_exec_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy")

task_def = aws.ecs.TaskDefinition(f"openleg-{ENV}-task",
    family="openleg-app",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_exec_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=json.dumps([{
        "name": "openleg-app",
        "image": "your-repo/openlegislation:latest",  # ECR or public
        "portMappings": [{"containerPort": 8080}],
        "environment": [{"name": "ENV", "value": ENV}],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "/ecs/openleg",
                "awslogs-region": "us-east-1",
                "awslogs-stream-prefix": "ecs"
            }
        }
    }]))

service = aws.ecs.Service(f"openleg-{ENV}-service",
    name="openleg-service",
    cluster=cluster.arn,
    task_definition=task_def.arn,
    desired_count=1,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=["subnet-12345678"],  # From TF or data source
        security_groups=["sg-12345678"],
        assign_public_ip=True
    ),
    opts=ResourceOptions(depends_on=[task_def]))

# DigitalOcean: Managed DB
do_db = do.DatabaseCluster(f"openleg-{ENV}-db",
    engine="pg",
    version="15",
    size="db-s-1vcpu-1gb",
    region="nyc3",
    node_count=1 if ENV == "dev" else 3,
    tags=[ENV])

# Hetzner: Storage server
hcloud_server = hcloud.Server(f"openleg-{ENV}-storage",
    name=f"storage-{ENV}",
    image="ubuntu-22.04",
    server_type="cx22",
    location="fsn1",
    ssh_keys=[hcloud.SshKey("default").id],
    user_data="""#!/bin/bash
apt update
apt install -y docker.io
docker run -d -p 8080:8080 --name storage-app your-image:latest
""",
    labels={"environment": ENV})

# Cloudflare: DNS and Worker
cf_zone = cloudflare.Zone(f"openleg-{ENV}-zone",
    zone= "openlegislation.com",  # Var
    type="full")

cf_record = cloudflare.Record(f"openleg-{ENV}-a",
    zone_id=cf_zone.id,
    name="app",
    value=service.load_balancers[0].dns_name,  # From AWS ALB
    type="A",
    proxied=True)

cf_worker = cloudflare.WorkerScript(f"openleg-{ENV}-worker",
    name="api-worker",
    content="addEventListener('fetch', event => { event.respondWith(handleRequest(event.request)) }) async function handleRequest(request) { return new Response('Hello from edge!') }")

cf_route = cloudflare.WorkerRoute(f"openleg-{ENV}-route",
    zone_id=cf_zone.id,
    pattern="api.*.openlegislation.com/*",
    script_name=cf_worker.name)

# GCP: AI/ML endpoint (Vertex AI)
gcp_endpoint = gcp.vertex.AiEndpoint(f"openleg-{ENV}-endpoint",
    name=f"bill-analysis-{ENV}",
    region="us-central1",
    deployed_models=[gcp.vertex.AiEndpointDeployedModelArgs(
        model=gcp.vertex.AiModel("gemini-model").id,
        display_name="gemini-deployment",
        machine_type="n1-standard-4"
    )])

# Monitoring: Prometheus/Grafana on AWS ECS (simple)
prom_task = aws.ecs.TaskDefinition(f"openleg-{ENV}-prom",
    family="monitoring",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_exec_role.arn,
    container_definitions=json.dumps([{
        "name": "prometheus",
        "image": "prom/prometheus:latest",
        "portMappings": [{"containerPort": 9090}],
        "logConfiguration": {"logDriver": "awslogs", "options": {"awslogs-group": "/ecs/monitoring", "awslogs-region": "us-east-1"}}
    }, {
        "name": "grafana",
        "image": "grafana/grafana:latest",
        "portMappings": [{"containerPort": 3000}],
        "environment": [{"name": "GF_SECURITY_ADMIN_PASSWORD", "value": "admin"}],
        "logConfiguration": {"logDriver": "awslogs", "options": {"awslogs-group": "/ecs/monitoring", "awslogs-region": "us-east-1"}}
    }]))

prom_service = aws.ecs.Service(f"openleg-{ENV}-monitoring",
    cluster=cluster.arn,
    task_definition=prom_task.arn,
    desired_count=1,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=["subnet-12345678"],
        security_groups=["sg-monitoring"],
        assign_public_ip=True
    ))

# CI/CD: GitHub Actions workflow (Pulumi outputs for integration)
# Note: Workflow file in .github/workflows/deploy.yml (create separately)

# Exports
export("aws_cluster_arn", cluster.arn)
export("do_db_host", do_db.host)
export("hcloud_server_ip", hcloud_server.ipv4_address)
export("cf_zone_id", cf_zone.id)
export("gcp_endpoint_name", gcp_endpoint.name)
export("monitoring_service_arn", prom_service.arn)