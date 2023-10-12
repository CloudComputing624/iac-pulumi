"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3
import pulumi_aws as aws
import pulumi.log


config = pulumi.Config()
public_subnet_config =config.require_object('public_subnet_configs')
private_subnet_config =config.require_object('private_subnet_configs')
public_cidr_block =config.require('public_route_table_cidr')
vpc_name = config.require('pulumi_vpc_name')
gateway_name= config.require('internet_gateway_name')
public_route_table= config.require('public_route_table')
private_route_table= config.require('private_route_table')

pulumi_vpc = aws.ec2.Vpc("main",
    cidr_block=config.get("vpc_cider_block"),
    instance_tenancy="default",
    tags={
        "Name": vpc_name,
    })

internet_gateway = aws.ec2.InternetGateway("pulumi-igw",
    tags={"Name": gateway_name})

internet_gateway_attachment = aws.ec2.InternetGatewayAttachment("pulumi-igw-attachment",
    vpc_id=pulumi_vpc.id,
    internet_gateway_id=internet_gateway.id)

public_subnets = []
for config in public_subnet_config:
    subnet = aws.ec2.Subnet(config["name"],
        vpc_id=pulumi_vpc.id,
        cidr_block=config["cidr_block"],
        availability_zone=config["availability_zone"], 
        map_public_ip_on_launch=True, 
        tags={
            "Name": config["name"],
        })
    public_subnets.append(subnet.id)

private_subnets = []
for config in private_subnet_config:
    subnet = aws.ec2.Subnet(config["name"],
        vpc_id=pulumi_vpc.id,
        cidr_block=config["cidr_block"],
        availability_zone=config["availability_zone"],  
        map_public_ip_on_launch=True,  
        tags={
            "Name": config["name"],
        })
    private_subnets.append(subnet.id)

public_route_table = aws.ec2.RouteTable("public-route-table",
    vpc_id=pulumi_vpc.id,
    tags={"Name": public_route_table})

aws.ec2.Route("public-route",
    route_table_id=public_route_table.id,
    destination_cidr_block = public_cidr_block, 
    gateway_id=internet_gateway.id,  
)

# Create a custom route table for private subnets
private_route_table = aws.ec2.RouteTable("private-route-table",
    vpc_id=pulumi_vpc.id,
    tags={"Name": private_route_table})

for i, public_subnet in enumerate(public_subnets):
    aws.ec2.RouteTableAssociation(f"public-subnet-association-{i}",
        subnet_id=public_subnet,
        route_table_id=public_route_table.id)
    
for i, private_subnet in enumerate(private_subnets):
    aws.ec2.RouteTableAssociation(f"private-subnet-association-{i}",
        subnet_id=private_subnet,
        route_table_id=private_route_table.id)