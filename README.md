# Demo for Learning some Kubernetes

## Prerequisites
Docker Desktop w Kubernetes enabled

## Setup

This application is a combination of two docker containers, one for Python Flask and another for Redis. The Flask app is a simple counter that increments every time the page is refreshed. The Redis container is used to store the counter value. It's really just for learning!

### Running w Docker Compose

- Clone this repo
- Run `docker-compose up --build`
- Navigate to `0.0.0.0:5001` in your browser for the flask app
- Navigate to `0.0.0.0:5001/test` in your browser for the redis app counter demo

### Running w Kubernetes

- Clone this repo
- Run `kubectl apply -f app-deployment.yaml`
- Check the pods are running with `kubectl get pods`
- Check the deployments are running with `kubectl get deployments`
- Check the status of the services with `kubectl get services`

- When you are ready to test, run `kubectl port-forward service/server 5001:5001` to forward the port to your local machine

- navigate to `0.0.0.0:5001` in your browser for the flask app, now running as a k8 cluster
- navigate to `0.0.0.0:5001/test` in your browser for the redis app counter demo, now running as a k8 cluster!
    - there is another flask endpoint, for [http://127.0.0.1:5001/name_receiver?name=etienne] ... set your name and watch the name list increment as you refresh the page with params passed in the url

### Simple deploy test for AWS EKS

- Make sure you have a role, follow setup here: https://docs.aws.amazon.com/eks/latest/userguide/service_IAM_role.html#create-service-role

> IAM role needs permissions for `iam:CreateRole` & `iam:AttachRolePolicy`

```bash
named_profile=atn-developer

aws iam create-role \
  --role-name eksClusterRole \
  --assume-role-policy-document file://"cluster-trust-policy.json" \
  --profile=$named_profile

aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy \
  --role-name eksClusterRole \
  --profile=$named_profile
```

- create the cluster. first get VPC info

```bash
vpc_id=vpc-fb32be86 # FROM YOUR AWS CONSOLE

aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpc_id" --query "Subnets[*].SubnetId" --output text --profile=$named_profile

aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$vpc_id" --query "SecurityGroups[*].GroupId" --output text --profile=$named_profile
```

- try the following but I got an error, so manually creating in https://us-east-1.console.aws.amazon.com/eks/home?region=us-east-1#/cluster-create

```bash
aws eks create-cluster \
  --name flask_demo_k8 \
  --role-arn eksClusterRole \
  --resources-vpc-config subnetIds=subnet-a44c30fb,securityGroupIds=sg-88780d8a \
  --profile=$named_profile
```

- that didn't work, so moving on...

```bash
aws eks update-kubeconfig --name flask_demo --profile=$named_profile
```
```