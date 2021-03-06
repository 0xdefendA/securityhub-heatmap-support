#!/usr/bin/env python3
from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_ecr as ecr,
)
from aws_cdk.aws_elasticloadbalancingv2 import ApplicationProtocol
from aws_cdk.aws_ecr_assets import DockerImageAsset
import json


class HeatmapStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        vpc = ec2.Vpc(self, "HeatMapVPC", max_azs=2)  # default is all AZs in region
        cluster = ecs.Cluster(self, "HeatmapCluster", vpc=vpc)
        cluster.add_default_cloud_map_namespace(name="heatmap.local")

        # Subscription repo is:
        # 117940112483.dkr.ecr.us-east-1.amazonaws.com/7884b327-1a1a-4f59-8d04-0a6edfc28697/cg-1674965903/securityhub-heatmap:1-latest
        repo = ecr.Repository.from_repository_arn(
            self,
            "heatmap_repo",
            "arn:aws:ecr:us-east-1:117940112483:repository/7884b327-1a1a-4f59-8d04-0a6edfc28697/cg-1674965903/securityhub-heatmap",
        )
        repo_image = ecs.ContainerImage.from_ecr_repository(
            repository=repo, tag="1-latest"
        )

        policy_json = None
        with open("cdk_deployment/heatmap_policy.json") as f:
            policy_json = json.loads(f.read())

        policy_doc = iam.PolicyDocument.from_json(policy_json)
        heatmap_role = iam.Role(
            self,
            "HeatmapIAMRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies=[policy_doc],
        )
        heatmap_role.grant(heatmap_role.grant_principal, "sts:AssumeRole")

        heatmap_task = ecs.FargateTaskDefinition(
            self,
            "heatmap-task",
            cpu=512,
            memory_limit_mib=2048,
            task_role=heatmap_role,
            execution_role=heatmap_role,
        )

        # You will want to set environment variables
        # for your particular configuration
        # every option in config.yml
        # can be over-ridden with an environment variable
        heatmap_task.add_container(
            "heatmap",
            image=repo_image,
            essential=True,
            environment={
                "LOCALDOMAIN": "heatmap.local",
                "ENVIRONMENT": "prod",
                "DEBUG": "False",
                "SERVER_NAME": "heatmap.mydomain.com",
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="HeatmapContainer",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
        ).add_port_mappings(ecs.PortMapping(container_port=80, host_port=80))

        heatmap_service = ecs_patterns.NetworkLoadBalancedFargateService(
            self,
            id="heatmap-service",
            service_name="heatmap",
            cluster=cluster,  # Required
            cloud_map_options=ecs.CloudMapOptions(name="heatmap"),
            cpu=512,  # Default is 256
            desired_count=1,  # Default is 1
            task_definition=heatmap_task,
            memory_limit_mib=2048,  # Default is 512
            listener_port=80,
            public_load_balancer=True,
        )

        heatmap_service.service.connections.allow_from_any_ipv4(
            ec2.Port.tcp(80), "heatmap inbound"
        )


app = core.App()
ecs = HeatmapStack(app, "HeatmapStack")
app.synth()
