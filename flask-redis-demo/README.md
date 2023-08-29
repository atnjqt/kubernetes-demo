# Flask Redis demo

## Setup, Goals, & Objectives

This application is a combination of two docker containers, one for Python Flask and another for Redis. The Flask app is a simple counter that increments every time the page is refreshed. The Redis container is used to store the counter value. The goal is really for learning Kubernetes, so the app is simple enough and the focus is on the deployment. Helpful to start with the guide published for getting started with EKS, ideally to build on this using python flask.

## Running with Docker Compose (local)

- Clone this repo
- Run `docker-compose up --build`


- Navigate to [http://0.0.0.0:5001](http://0.0.0.0:5001) in browser for the flask app
- Navigate to [http://0.0.0.0:5001/test](http://0.0.0.0:5001/test) in browser for the redis app counter demo. Refresh the page to demo the counter incrementing

## Running with Kubernetes (local, docker-desktop context)

- Confirm your kubectl context is set to docker-desktop

    ```bash
    kubectl config get-contexts
    kubectl config use-context docker-desktop
    ```

- Make sure to docker build the images first, 

    ```bash
    cd services/server
    docker build ./ -t flask-app:latest
    ```

- Apply your deployment & service manifests:

    ```bash
    cd ../..
    kubectl apply -f app-deployment.yaml
    kubectl apply -f app-service.yaml
    ```

- Check on cluster:
    - Check the pods are running with `kubectl get pods`
    - Check the deployments are running with `kubectl get deployments`
    - Check the status of the services with `kubectl get services`

- When you are ready to test, run to forward the port to your local machine 

    ```bash
    kubectl port-forward service/server 5001:5001
    ``` 

- navigate to [http://0.0.0.0:5001](http://0.0.0.0:5001) in your browser for the flask app, now running as a k8 cluster

- navigate to [http://0.0.0.0:5001/test](http://0.0.0.0:5001/test) in your browser for the redis app counter demo, now running as a k8 cluster!
    - there is another flask endpoint, for [http://127.0.0.1:5001/name_receiver?name=etienne] ... set your name and watch the name list increment as you refresh the page with params passed in the url