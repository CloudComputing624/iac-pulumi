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
ami_id= config.require('ami_id')
instanceType= config.require('instance_type')
keyName= config.require('key_pair_name')
ec2_name= config.require('EC2_Instance_Name')
port= config.require('port')
cidr_block_http= config.require('cidr_block_http')
cidr_block_ssh= config.require('cidr_block_ssh')
cidr_block_aaplication= config.require('cidr_block_application')
cidr_block_tcp= config.require('cidr_block_tcp')
security_group_name= config.require('pulumi_security_group_name')

availability_zones = aws.get_availability_zones()
limited_availability_zones = availability_zones.names
if len(availability_zones.names)>3:
    limited_availability_zones = availability_zones.names[0:3]

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
for i,publicConfig in enumerate(limited_availability_zones):
    publicConfig = public_subnet_config[i]
    subnet = aws.ec2.Subnet(publicConfig["name"],
        vpc_id=pulumi_vpc.id,
        cidr_block=publicConfig["cidr_block"],
        availability_zone= limited_availability_zones[i],
        map_public_ip_on_launch=True, 
        tags={
            "Name": publicConfig["name"],
        })
    public_subnets.append(subnet.id)

private_subnets = []
for i,privateConfig in enumerate(limited_availability_zones):
    privateConfig = private_subnet_config[i]
    subnet = aws.ec2.Subnet(privateConfig["name"],
        vpc_id=pulumi_vpc.id,
        cidr_block=privateConfig["cidr_block"],
        availability_zone= limited_availability_zones[i],  
        map_public_ip_on_launch=True,  
        tags={
            "Name": privateConfig["name"],
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
    

pulumi_security_group = aws.ec2.SecurityGroup(
    security_group_name,
    vpc_id= pulumi_vpc.id,  # Replace with the ID of your VPC
    description="Pulumi Security Group",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": [cidr_block_ssh],  # Adjust the CIDR block for your needs
        },
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": [cidr_block_http],  # Adjust the CIDR block for your needs
        },
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": [cidr_block_tcp],  # Adjust the CIDR block for your needs
        },
        {
            "protocol": "tcp",
            "from_port": port,
            "to_port": port,
            "cidr_blocks": [cidr_block_aaplication],  # Adjust the CIDR block for your needs
        },
    ],
    tags={
        "Name": security_group_name,
    },
)

ec2_instance = aws.ec2.Instance(
    ec2_name,  # Provide a name for the instance
    ami=ami_id,  # Replace with your desired AMI ID
    instance_type=instanceType,  # Specify the instance type
    subnet_id= public_subnets[0],  # Specify the subnet ID
    vpc_security_group_ids=[pulumi_security_group.id],
    associate_public_ip_address=True,
    key_name=keyName,  # Specify the key pair for SSH access
    root_block_device={
        "volume_size": 25,
        "volume_type": "gp2",
        "delete_on_termination": True,
    },
    tags={
        "Name": ec2_name,  # Add any tags you want
    },
)


    

pulumi.export("availability_zones", availability_zones.names)