## Repository Name : iac-pulumi

## Git Url : git@github.com:SindhuraBandaru99/iac-pulumi.git

## Installations
## AWS Command CLI
- curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

- sudo installer -pkg AWSCLIV2.pkg -target /
- aws configure --profile= dev
- Provide the access key ID,  Secret Access Key and the Region for the account created
- aws configure --profile= demo 
- Provide the access key ID,  Secret Access Key and the Region for the account created

## Pulumi Creation
- pulumi new
  
## To Create Stacks
- Dev stack - pulumi stack init dev
- Demo Stack - pulumi stack init demo

## To Change Stacks
- pulumi stack select dev/demo

## To Remove Stacks
- pulumi stack rm dev/demo

## Create Pulumi 
- pulumi up

## Destroy Pulumi
- pulumi destroy