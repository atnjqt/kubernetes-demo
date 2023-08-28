# Demo for Learning some Kubernetes

## Prerequisites
Docker Desktop w Kubernetes enabled

## Setup, Goals, & Objectives

This application is a combination of two docker containers, one for Python Flask and another for Redis. The Flask app is a simple counter that increments every time the page is refreshed. The Redis container is used to store the counter value. The goal is really for learning Kubernetes, so the app is simple enough and the focus is on the deployment. Helpful to start with the guide published for getting started with EKS, ideally to build on this using python flask.

### Running with Docker Compose (local)

- Clone this repo
- Run `docker-compose up --build`
- Navigate to `0.0.0.0:5001` in your browser for the flask app
- Navigate to `0.0.0.0:5001/test` in your browser for the redis app counter demo

### Running with Kubernetes (local, docker-desktop context)

- Clone this repo
- Make sure to docker build the images first, `docker build -t flask-app:latest`
- Run `kubectl apply -f app-deployment.yaml`
- Check the pods are running with `kubectl get pods`
- Check the deployments are running with `kubectl get deployments`
- Check the status of the services with `kubectl get services`

- When you are ready to test, run `kubectl port-forward service/server 5001:5001` to forward the port to your local machine

- navigate to `0.0.0.0:5001` in your browser for the flask app, now running as a k8 cluster
- navigate to `0.0.0.0:5001/test` in your browser for the redis app counter demo, now running as a k8 cluster!
    - there is another flask endpoint, for [http://127.0.0.1:5001/name_receiver?name=etienne] ... set your name and watch the name list increment as you refresh the page with params passed in the url

### Simple deploy test for AWS EKS

- Make sure you have a IAM role preconfigured, follow setup here: https://docs.aws.amazon.com/eks/latest/userguide/service_IAM_role.html#create-service-role


  ```bash
  named_profile=atn-developer

  eks_iam_role=eksClusterRole

  aws iam create-role \
    --role-name $eks_iam_role \
    --assume-role-policy-document file://"cluster-trust-policy.json" \
    --profile=$named_profile

  aws iam attach-role-policy \
    --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy \
    --role-name $eks_iam_role \
    --profile=$named_profile
  ```

  > IAM role needs permissions for `iam:CreateRole` & `iam:AttachRolePolicy`, in order to create recommended eksClusterRole and attach AmazonEKSClusterPolicy


#### Create EKS Cluster

- To create your EKS cluster, you need your VPC's subnet information:

  ```bash
  # FROM YOUR AWS CONSOLE
  vpc_id=vpc-fb32be86 

  # get three subnets
  vpc_id_vals=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpc_id" --query "Subnets[*].SubnetId" --profile=$named_profile --output=json | jq -r '.[3:5]')

  # using default security group
  aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$vpc_id" --query "SecurityGroups[*].GroupId" --output json --profile=$named_profile
  ```

- Create your EKS Cluster using 
  - See manual here: https://us-east-1.console.aws.amazon.com/eks/home?region=us-east-1#/cluster-create

  ```bash
  your_cluster_name=flask_demo_k8

  aws eks create-cluster \
    --name $your_cluster_name \
    --role-arn arn:aws:iam::579747246975:role/$eks_iam_role \
    --resources-vpc-config subnetIds=$vpc_id_vals,securityGroupIds=sg-88780d8a \
    --profile=$named_profile

  while [[ $(aws eks describe-cluster --name $your_cluster_name --profile=$named_profile | jq -r '.cluster.status') == "CREATING" ]]; do echo "waiting for cluster creation to complete..."; sleep 5; done
  ```

#### Update local kubectl for deployment

- Update local kubeconfig for newly creates eks cluster

  ```bash
  aws eks update-kubeconfig --name flask_demo_k8 --profile=$named_profile
  ``` 

  > if you get *Cluster status is CREATING*, give your eks baby some time to start up and try again 🐣

- Check your cluster is running

  ```bash
  kubectl get svc
  ```

#### Create compute (nodegroup on ec2)

- Create a Node Group to associated with your EKS cluster:

  ```bash
  your_nodegroup_name=my-node-group-demo
  eks_node_role=AmazonEKSNodeRole
  min_size=1
  desired_size=1
  max_size=2
  instance_types=t2.medium
  disk_size=5

  aws eks create-nodegroup \
    --cluster-name $your_cluster_name \
    --nodegroup-name $your_nodegroup_name \
    --node-role arn:aws:iam::579747246975:role/$eks_node_role \
    --subnets $vpc_id_vals \
    --scaling-config minSize=$min_size,maxSize=$max_size,desiredSize=$desired_size \
    --instance-types $instance_types \
    --disk-size $disk_size \
    --profile=$named_profile
  ```

#### Apply cluster manifest to eks
- Excellent, go ahead and apply your manifests to your cluster

  ```bash
  # create namespace
  kubectl create namespace eks-sample-app

  # two sample files provided by aws eks guide
  kubectl apply -f eks-sample-deployment.yaml
  kubectl apply -f eks-sample-service.yaml
  ```

- Check your pods are running

  ```bash
  kubectl -n eks-sample-app describe service eks-sample-linux-service
  kubectl get pods -n eks-sample-app
  ```

- describe your pods to check logs, etc...

  ```bash
  kubectl -n eks-sample-app describe pod eks-sample-linux-deployment-...
  ```

#### Connect to container via shell

- from there you can connect to the containers shell:

  ```bash
  kubectl exec -it eks-sample-linux-deployment-... -n eks-sample-app -- /bin/bash
  ```

- how to make it publicly accessible over port 80? good question maybe for another time...

#### Terminate environment (computer & cluster)

- destroy the node group, and cluster

  ```bash
  aws eks delete-nodegroup --cluster-name $your_cluster_name --nodegroup-name $your_nodegroup_name --profile=$named_profile
  ```

- wait for the node group to delete, then delete the cluster


  ```bash
  while [[ $(aws eks describe-nodegroup --cluster-name $your_cluster_name --nodegroup-name $your_nodegroup_name --profile=$named_profile | jq -r '.nodegroup.status') == "DELETING" ]]; do echo "waiting for nodegroup to delete..."; sleep 5; done

  aws eks delete-cluster --name $your_cluster_name --profile=$named_profile
  ```

#### Push container to ECR

- create an ecr registry:

  ```bash
  aws ecr create-repository --repository-name flask-app --profile=$named_profile
  ```

- build local container

  ```bash
  cd flask_demo/service
  docker build -t flask-app:latest .
  ```

- push container to ecr

  ```bash
  docker push 579747246975.dkr.ecr.us-east-1.amazonaws.com/flask-app:latest
  ```

- update manifest to include endpoint for ecr

  ```diff
  - image: flask-app:latest
  + image: 579747246975.dkr.ecr.us-east-1.amazonaws.com/flask-app:latest
  ```

- apply the manifest

  ```bash
  kubectl apply -f app-deployment.yaml
  ```

- all of the above hasn't been tested for ecr! but it should work 🤞 (it was AI assisted after all)
