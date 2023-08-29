# Demo following on AWS Guide for EKS

- https://docs.aws.amazon.com/eks/latest/userguide/sample-deployment.html

## Simple deploy test for AWS EKS

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


### Create EKS Cluster

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

### Update local kubectl for deployment

- Update local kubeconfig for newly creates eks cluster

  ```bash
  aws eks update-kubeconfig --name flask_demo_k8 --profile=$named_profile
  ``` 

  > if you get *Cluster status is CREATING*, give your eks baby some time to start up and try again 🐣

- Check your cluster is running

  ```bash
  kubectl get svc
  ```

### Create compute (nodegroup on ec2)

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

  while [[ $(aws eks describe-nodegroup --cluster-name $your_cluster_name \
  --nodegroup-name $your_nodegroup_name --profile=$named_profile | jq -r '.nodegroup.status') == 'CREATING']]; do echo "waiting for nodegroup creation to complete..."; sleep 5; done
  ```

### Apply cluster manifest to eks
- Excellent, go ahead and apply your manifests to your cluster

  ```bash
  # create namespace
  kubectl create namespace eks-sample-app

  # two sample files provided by aws eks guide
  kubectl apply -f aws-eks-demo/eks-sample-deployment.yaml
  kubectl apply -f aws-eks-demo/eks-sample-service.yaml
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

### Connect to container via shell

- from there you can connect to the containers shell:

  ```bash
  kubectl exec -it eks-sample-linux-deployment-... -n eks-sample-app -- /bin/bash
  ```

- how to make it publicly accessible over port 80? good question maybe for another time...

### Terminate environment (computer & cluster)

- destroy the node group, and cluster

  ```bash
  aws eks delete-nodegroup --cluster-name $your_cluster_name --nodegroup-name $your_nodegroup_name --profile=$named_profile
  ```

- wait for the node group to delete, then delete the cluster


  ```bash
  while [[ $(aws eks describe-nodegroup --cluster-name $your_cluster_name --nodegroup-name $your_nodegroup_name --profile=$named_profile | jq -r '.nodegroup.status') == "DELETING" ]]; do echo "waiting for nodegroup to delete..."; sleep 5; done

  aws eks delete-cluster --name $your_cluster_name --profile=$named_profile
  ```

### Push container to ECR

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
