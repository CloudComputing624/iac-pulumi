"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3
import pulumi_aws as aws
import pulumi.log
import base64


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
parameter_group_name = config.require('rds_parameter_group_name')
family_group_name = config.require('rds_parameter_family')
db_subnet_group_name = config.require('rds_db_subnet_group')
db_security_group_name = config.require('rds_db_security_group_name')
rds_Instance_Name = config.require('rds_Instance_Name')
db_instance_identifier_name = config.require('db_instance_identifier')
db_instance_class = config.require('instance_class')
db_name = config.require('db_name')
db_engine = config.require('db_engine')
db_engine_version = config.require('db_engine_version')
db_username = config.require('username')
db_password = config.require('password')
rds_storage_type = config.require('rds_storage_type')
parameter_group_name_pa = config.require('parameter_group_name_pa')
parameter_group_value = config.require('parameter_group_value')
apply_method = config.require('apply_method')
env_path = config.require('ENV_FILE_PATH')
zone_ID = config.require('existing_hostedZone_ID')
role_name = config.require('role_Name')
resource_name = config.require('resource_name')
policy_arn = config.require('policy_arn')
instance_profile = config.require('instance_profile')
a_record_name = config.require('a_record_name')
record_type = config.require('record_type')
record_ttl = config.require('record_ttl')
lb_security_group_name = config.require('lb_security_group_name') 
launchTemplateName = config.require('launch_Template_Name')
auto_scaling_group_name = config.require('as_group_name')




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
    


load_balancer_security_group = aws.ec2.SecurityGroup(
    lb_security_group_name,
    vpc_id= pulumi_vpc.id,  
    description="Load Balancer Security Group",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": [cidr_block_http],  
        },
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": [cidr_block_tcp],  
        },
    ],
    egress=[
        {
        "protocol": "-1",
        "fromPort": 0,
        "toPort": 0,
        "cidrBlocks": ["0.0.0.0/0"],
        },
    ],
    tags={
        "Name": lb_security_group_name,
    },
)

pulumi_security_group = aws.ec2.SecurityGroup(
    security_group_name,
    vpc_id= pulumi_vpc.id,  
    description="Pulumi Security Group",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": [cidr_block_ssh],  
        },
        {
            "protocol": "tcp",
            "from_port": port,
            "to_port": port,
            "securityGroups": [load_balancer_security_group.id],  
        },
    ],
    egress=[
        {
        "protocol": "-1",
        "fromPort": 0,
        "toPort": 0,
        "cidrBlocks": ["0.0.0.0/0"],
        },
    ],
    tags={
        "Name": security_group_name,
    },
)

rds_Security_Group = aws.ec2.SecurityGroup(
    db_security_group_name,
    vpc_id= pulumi_vpc.id, 
    description="RDS Security Group",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 3306,
            "to_port": 3306,
            "securityGroups": [pulumi_security_group.id],  
        },
    ],
    tags={
        "Name": db_security_group_name,
    },
)

rds_parameter_group = aws.rds.ParameterGroup(
    parameter_group_name,
    family=family_group_name,
    parameters=[
        aws.rds.ParameterGroupParameterArgs(
            name=parameter_group_name_pa,
            value=parameter_group_value,
            apply_method=apply_method
        ),
    ]
    )


rds_subnet_group = aws.rds.SubnetGroup(db_subnet_group_name,
    subnet_ids = private_subnets,
    tags={
        "Name": db_subnet_group_name,
    })


pulumi_rds_instance = aws.rds.Instance(rds_Instance_Name,
    allocated_storage=20,
    db_name= db_name,
    engine=db_engine,
    engine_version= db_engine_version,
    identifier = db_instance_identifier_name,
    username=db_username,
    password=db_password,
    instance_class=db_instance_class,
    parameter_group_name=rds_parameter_group.name,
    vpc_security_group_ids=[rds_Security_Group.id],
    db_subnet_group_name = rds_subnet_group.name,
    skip_final_snapshot=True,
    apply_immediately= True,
    publicly_accessible=False,
    multi_az = False,
    storage_type = rds_storage_type,
    tags={
        "Name": rds_Instance_Name,  
    },
)
rdsEndpoint = pulumi_rds_instance.endpoint
# pulumi_rds_instance = pulumi.Output.from_input(rdsEndpoint)
#rdsEndpointOutput = pulumi.Output.create(rdsEndpoint, { "value" : rdsEndpoint })

endpoint_value = rdsEndpoint.apply(lambda args: args[0].split(":")[0])


user_data_script = pulumi_rds_instance.endpoint.apply(lambda endpoint:
f"""#!/bin/bash
# Set your database configuration
NEW_DB_NAME={db_name}
NEW_DB_USER={db_username}
NEW_DB_PASSWORD={db_password}
NEW_DB_HOST={endpoint.split(":")[0]}
ENV_FILE_PATH={env_path}
 
if [ -e "$ENV_FILE_PATH" ]; then
    sed -i -e "s/DB_HOST=.*/DB_HOST=$NEW_DB_HOST/" \
           -e "s/DB_USER=.*/DB_USER=$NEW_DB_USER/" \
           -e "s/DB_PASSWORD=.*/DB_PASSWORD=$NEW_DB_PASSWORD/" \
           -e "s/DB_NAME=.*/DB_NAME=$NEW_DB_NAME/" \
           "$ENV_FILE_PATH"
else
    echo "$ENV_FILE_PATH not found. Make sure the .env file exists"
fi
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/csye6225/webapp/cloudwatch-config.json \
    -s
sudo systemctl restart amazon-cloudwatch-agent
""")
 
base64_encoded_user_data = pulumi.Output.all(user_data_script).apply(lambda values:
    base64.b64encode(values[0].encode('utf-8')).decode('utf-8')
)



# user_data_script = f"""#!/bin/bash
# NEW_DB_USER={db_username}
# NEW_DB_PASSWORD={db_password}
# NEW_DB_HOST={endpoint_value}
# NEW_DB_NAME={db_name}
# ENV_FILE_PATH={env_path}

# if [ -e "$ENV_FILE_PATH" ]; then
# sed -i -e "s/DB_HOST=.*/DB_HOST=$NEW_DB_HOST/" \
# -e "s/DB_USER=.*/DB_USER=$NEW_DB_USER/" \
# -e "s/DB_PASSWORD=.*/DB_PASSWORD=$NEW_DB_PASSWORD/" \
# -e "s/DB_NAME=.*/DB_NAME=$NEW_DB_NAME/" \
# "$ENV_FILE_PATH"
# else
# echo "$ENV_FILE_PATH not found. Make sure the .env file exists"
# fi

# sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
#     -a fetch-config \
#     -m ec2 \
#     -c file:/opt/csye6225/webapp/cloudwatch-config.json \
#     -s
# """
# encoded_user_data = pulumi.Output.all(endpoint_value).apply(lambda args: base64.b64encode(user_data_script.encode('utf-8')).decode('utf-8'))


# user_data_script_value = pulumi.Output.secret(user_data_script)
# encoded_user_data = (lambda path: base64.b64encode(path.encode()).decode())(user_data_script_value)

# encoded_user_data = base64.b64encode(user_data_script.encode('utf-8')).decode('utf-8')



# user_data_script_value = pulumi.Output.secret(user_data_script)
# encoded_user_data = base64.b64encode(user_data_script_value.encode()).decode()


role = aws.iam.Role(
    role_name,
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com" 
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }""",
)

role_policy_attachment = aws.iam.RolePolicyAttachment(
    resource_name=resource_name,
    role=role.name,
    policy_arn=policy_arn,
)

cw_instance_profile = aws.iam.InstanceProfile(
    instance_profile,
    role=role.name,
)



# ec2_instance = aws.ec2.Instance(
#     ec2_name,  
#     ami=ami_id,  
#     instance_type=instanceType, 
#     subnet_id= private_subnet[0],  
#     vpc_security_group_ids=[pulumi_security_group.id],
#     associate_public_ip_address=True,
#     user_data= user_data_script,
#     user_data_replace_on_change=True,
#     key_name=keyName,
#     iam_instance_profile=cw_instance_profile.name,  
#     root_block_device={
#         "volume_size": 25,
#         "volume_type": "gp2",
#         "delete_on_termination": True,
#     },
#     tags={
#         "Name": ec2_name,  
#     },
# )





load_balancer_target_group = aws.lb.TargetGroup("lb-Target-Group",
    port=3000,
    protocol="HTTP",
    vpc_id=pulumi_vpc.id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        path="/healthz",
        port="3000",
    )
    )

# network_interface = aws.ec2.NetworkInterface("pulumi-network-interface",
#     security_groups=[pulumi_security_group.id],
# )

load_balancer = aws.lb.LoadBalancer(
    "Pulumi-load-balancer",
    internal=False,
    load_balancer_type="application",
    subnets= public_subnets,
    security_groups=[load_balancer_security_group.id],
    enable_deletion_protection=False, 
)

listener = aws.lb.Listener("frontEndListener",
    load_balancer_arn=load_balancer.arn,
    port=80,
    protocol="HTTP",
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        type="forward",
        target_group_arn=load_balancer_target_group.arn,
    )])

ec2_launch_template = aws.ec2.LaunchTemplate(
    launchTemplateName,
    name=launchTemplateName,
    description="Ec2 Launch Template",
    block_device_mappings=[
        {
            "device_name": "/dev/sdf",
            "ebs": {
                "volume_size": 30,
                "volume_type": "gp2",
                "delete_on_termination": True,
            },
        },
    ],
    image_id=ami_id,  
    instance_type=instanceType, 
    network_interfaces=[aws.ec2.LaunchTemplateNetworkInterfaceArgs(
        security_groups=[pulumi_security_group.id],
        associate_public_ip_address="true",
    )],
    user_data= base64_encoded_user_data,
    key_name=keyName,
    iam_instance_profile=aws.ec2.LaunchTemplateIamInstanceProfileArgs(
        name=cw_instance_profile.name,
    ),
    tags={
        "Name": launchTemplateName,  
    },
    
)

auto_scaling_group = aws.autoscaling.Group(
    auto_scaling_group_name,
    launch_template=aws.autoscaling.GroupLaunchTemplateArgs(
        id=ec2_launch_template.id,
        version="$Latest",
    ),
    desired_capacity=1,
    min_size=1,
    max_size=3,
    vpc_zone_identifiers=public_subnets,
    health_check_type="ELB",
    default_cooldown=60,
    tags=[
        aws.autoscaling.GroupTagArgs(
            key="Name",
            value="Application Server",
            propagate_at_launch=True,
        )
    ],
)

lb_attachment = aws.autoscaling.Attachment("lb-attachment",
    autoscaling_group_name=auto_scaling_group.id,
    lb_target_group_arn= load_balancer_target_group.arn,
)

scale_up_policy = aws.autoscaling.Policy(
    "scale-up-policy",
    scaling_adjustment=1,
    cooldown=60,  # 5 minutes cooldown
    adjustment_type="ChangeInCapacity",
    autoscaling_group_name=auto_scaling_group.name,
    name="scale-up",
)
cpu_high_alarm = aws.cloudwatch.MetricAlarm(
    "cpu-high-alarm",
    comparison_operator="GreaterThanOrEqualToThreshold",
    evaluation_periods=1,  # Adjust as needed
    metric_name="CPUUtilization",
    namespace="AWS/EC2",
    period=300,  # 5 minutes
    statistic="Average",
    threshold=5,
    dimensions={
        "AutoScalingGroupName": auto_scaling_group.name,
    },
    alarm_description="This metric monitors ec2 cpu utilization",
    alarm_actions=[scale_up_policy.arn],
)


scale_down_policy = aws.autoscaling.Policy(
    "scale-down-policy",
    scaling_adjustment=-1,
    cooldown=60,  # 5 minutes cooldown
    adjustment_type="ChangeInCapacity",
    autoscaling_group_name=auto_scaling_group.name,
    name="scale-down",
)

cpu_low_alarm = aws.cloudwatch.MetricAlarm(
    "cpu-low-alarm",
    comparison_operator="LessThanOrEqualToThreshold",
    evaluation_periods=1,  # Adjust as needed
    metric_name="CPUUtilization",
    namespace="AWS/EC2",
    period=300,  # 5 minutes
    statistic="Average",
    threshold=3,
    dimensions={
        "AutoScalingGroupName": auto_scaling_group.name,
    },
    alarm_description="This metric monitors ec2 cpu utilization",
    alarm_actions=[scale_down_policy.arn],
)

load_balancer_dns_name = load_balancer.dns_name
a_record = aws.route53.Record(
    a_record_name,
    zone_id=zone_ID,
    name="",
    type=record_type,
    aliases=[aws.route53.RecordAliasArgs(
        name=load_balancer.dns_name,
        zone_id=load_balancer.zone_id,
        evaluate_target_health=True,
    )]
)



pulumi.export("rds_endpoint", pulumi_rds_instance.endpoint)
pulumi.export("load_balancer_dns_name", load_balancer_dns_name)
# pulumi.export("EC2 Instance Public IP", ec2_instance.public_ip)
pulumi.export("EC2 Instance Role Name ", role.name)

