#Building a containerized batch pipeline for AI inference with triggers from a REST API

## Introduction

Welcome to our question answering API interface. This interface allows a user to upload a csv file containing ‘questions’ and ‘context’ and populates the answer using AI model.
The application uses 

This repository contains the pipeline specifications and code for making batch pipelines for the larger [Hugging  Face Transformers](https://huggingface.co/models) based Question Answer model. Our application uses the "distilled-bert" model for answering questions, given context.

### Application Architecture
The application uses REST API to make calls to the service hosted on google cloud.<br>
A user can trigger API requests containing a csv file with questions and context using the link - https://mgmt590-restapi-es7glm5rsq-uc.a.run.app/upload. When a client request is made via a RESTful API, it transfers a representation of the state of the resource to the Google Cloud Storage bucket. Our batch pipeline job runs every 5 mins to perform the following operations -
1) Scans the Google Cloud Storage bucket to check and consume any user input csv file
2) Generates answers to the questions asked by user
3) Outputs the file in an output folder
4) Stores the answers generated by a script in the PostgreSQL database
5) Cleans the Google Cloud Storage to remove the above processed raw csv file

Now to ensure that all the above steps are performed, our application relies on the below technology services -

1) **Pachyderm Hub** - Pachyderm hub is a SaaS platform that gives one access to all of Pachyderm's functionalities without the burden of deploying and maintaining it locally or in a third-party cloud platform.

We use pachyderm to create batch pipelines that regularly scan our cloud buckets to check and process. Our code has 2 batch pipelines -
* Pipeline 1 - Periodically (once every 5 mins) pulls in new files from our GCS bucket, processes the files using distilled-bert QA model to produce answer. It then deletes the ingress file from the GCS bucket. The output file with answers is stored in pfs/out and fed into pachyderm's pipeline2

* Pipelien 2 - Reads in the output repository of the first pipeline as its inputs and pushes each row of the processed data as records in our PostgreSQL database.


2) **Docker Hub** - Docker Hub is a service provided by Docker for creating and sharing container images for the project. Docker images are pushed to Docker Hub through the ``` docker push``` command. A single Docker Hub repository can hold many Docker images.

For our application, we are using GitHub actions to create our images on docker hub. Here is a snippet of our .yml file. Note that DOCKERHUB_USERNAME and DOCKERHUB_TOKEN are the user's dockerhub account's username and password. We have defined them as git hub secrets for security.

We are pushing 2 images as our application has 2 pipelines.

```
- name: Login to DockerHub
      uses: docker/login-action@v1
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}

    - name: Build and push
      run: |-
        cd pipeline1 && docker build -t esha212/mgmt590-gcs:${{  github.sha }} .
        docker push esha212/mgmt590-gcs:${{  github.sha }} && cd ../
        cd pipeline2 && docker build -t esha212/mgmt590-sql:${{  github.sha }} .
        docker push esha212/mgmt590-sql:${{  github.sha }}
```

3) **Google Cloud Services** -

Here is our architecture diagram. <br>

<img src="/images/techflow.PNG">

### Creating batch pipelines in Pachyderm
A Pachyderm Pipeline can be defined in three steps:

1) **Define a Dockerfile** We begin by building a Docker image for our code. This is relatively simple - we clone the repository into the image and install the requirements. There are occasions where a system library is needed, which can be easily solved by adding it to the Dockerfile. Once the Docker image is built, the entire system needed to run the classifier is encapsulated in a snapshot.

2) **Create an Entrypoint** In the original code, there is a run.sh script that reads sample data and outputs predictions (along with intermediate files necessary to produce the prediction). This script can be used as the entrypoint to the container. This equivalent to the entrypoint for a Docker image.

3) **Create a Pipeline Spec** The Pipeline Spec is a JSON file that is used to tell Pachyderm how to deploy the pipeline. We define the inputs, the Docker image to be used, the entrypoint, and any other configuration needed. A full list of the pipeline specification parameters can be found [here](https://docs.pachyderm.com/latest/reference/pipeline_spec/) .

### Dependencies
The application uses a lot of python packages and libraries to ensure that both the REST API and batch pipelines are functional. We specify  Packages currently in use are -

|Packages|Function|installation|
|----|----|----|
|streamlit|Use to render the UI|pip install streamlit|
|pandas|Used to work with data files |pip install pandas
|requests|Used to get and send requests to API |pip install requests
|transformers==4.2.2|Used to get Huggingface's transformers|pip install transformers==4.2.2|
|flask|Used to create a flask application|pip install flask
|torch|Used to access pyTorch based model in Higgingface models |pip install torch
|pytest==6.2.2|Used to run unit test suit|pip install pytest
|psycopg2-binary|Used to access Postgre sql database hosted on google cloud |pip install psycopg2
|werkzeug|Comprehensive WSGI web application library |pip install werkzeug
|google-cloud-storage|Used to access google cloud file system |pip install google-cloud-storage
|pybase64|Used to perform base64 encoding of credentials |pip install pybase64

### Build and Run the pipelines locally on google cloud
To build and run the application locally a user would need to follow the below process - <br>
1) **Get the application** - To run the application locally, one needs to get the application source code onto their local machine. Our application is already developed and the code can be accessed in respective pipeline folders. User can start by cloning our repo command.<br>

2) **Setting up enviornment variables locally** - We have parameterized all database and cloud storage access credentials in our application. A user would need to create the same and pass them through the git hub workflow's yml file to the Google cloud for further working.<br>
Since the pachyderm pipeline will take these credentials directly from the cloud, we would need to define them as enviornment variables in the cloud.<br>
A user can use the following command to accomplish the same in their cloud terminal -<br>
Make sure to first copy all the cloud service account's certificate files cloud shell.-<br>

```
export GOOGLE_APPLICATION_CREDENTIALS="/home/user1/gcs-example/credentials.json"
export PG_HOST=<public url of sql database>
export PG_PASSWORD=<passsword of sql database>
export PG_SSLROOTCERT="/home/user1/server-ca.pem"
export PG_SSLCERT="/home/user1/client-cert.pem"
export PG_SSLKEY="/home/user1/client-key.pem"
```
<br> Once done when the user wishes to connect the shell to pachyderm, they can simply run our create_secret.sh script, which will decode various credential files and enable the pipelines to interact with user's cloud account.


```
#!/bin/bash

# Make a copy of our secrets template
cp secret_template.json secret.json
cp secret_template_db.json secret_db.json

# Encode our GCS creds
GCS_ENCODED=$(cat $GOOGLE_APPLICATION_CREDENTIALS | base64 -w 0)

# Substitute those creds into our secrets file
sed -i -e 's|'REPLACE_GCS_CREDS'|'"$GCS_ENCODED"'|g' secret.json

# Encode our SSL certs
SSLROOTCERT_ENCODED=$(echo $PG_SSLROOTCERT | base64 -w 0)
SSLCERT_ENCODED=$(echo $PG_SSLCERT | base64 -w 0)
SSLKEY_ENCODED=$(echo $PG_SSLKEY | base64 -w 0)

# Substitute those creds into our secrets file
sed -i -e 's|'REPLACE_PG_HOST'|'"$PG_HOST"'|g' secret_db.json
sed -i -e 's|'REPLACE_PG_PASSWORD'|'"$PG_PASSWORD"'|g' secret_db.json
sed -i -e 's|'REPLACE_PG_SSLROOTCERT'|'"$SSLROOTCERT_ENCODED"'|g' secret_db.json
sed -i -e 's|'REPLACE_PG_SSLCERT'|'"$SSLCERT_ENCODED"'|g' secret_db.json
sed -i -e 's|'REPLACE_PG_SSLKEY'|'"$SSLKEY_ENCODED"'|g' secret_db.json

# Create our secrets
pachctl create secret -f secret.json
pachctl create secret -f secret_db.json

```


2) **Deploy your pipelines via Pachyderm** - Below are the steps to deploy your pipelines via Pachyderm:
- 1. Sign-in to Pachyderm
- 2. Create a new workspace as shown below
   <img width="309" alt="1" src="https://user-images.githubusercontent.com/84465734/121768778-fb98e400-cb2d-11eb-91c4-46e1946636f2.PNG">

- 3. Install pachctl on your machine
   The "pachctl" or pach control is a command line tool that you can use to interact with a Pachyderm cluster in your terminal. For a Debian based Linux 64-bit or Windows 10    or later running on WSL run the following code:
   ```
   curl -o /tmp/pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v1.13.2/pachctl_1.13.2_amd64.deb && sudo dpkg -i /tmp/pachctl.deb
   ```
   For macOS use the below command:
   ```
   brew tap pachyderm/tap && brew install pachyderm/tap/pachctl@1.13
   ```
   For all other Linux systems use below command:
   ```
   curl -o /tmp/pachctl.tar.gz -L https://github.com/pachyderm/pachyderm/releases/download/v1.13.2/pachctl_1.13.2_linux_amd64.tar.gz && tar -xvf /tmp/pachctl.tar.gz -C /tmp && sudo cp /tmp/pachctl_1.13.2_linux_amd64/pachctl /usr/local/bin
   ```

- 4. Connect to your Pachyderm workspace

   Click "Connnect" on your Pachyderm workspace and follow the below listed steps to connect to your workspace via the machine
   
   <img width="306" alt="2" src="https://user-images.githubusercontent.com/84465734/121769024-50892a00-cb2f-11eb-8546-97b039618abb.PNG">
    
- 5. Create a new pachctl repo using the below command
   ```
    pachctl create repo reponamehere
   ```
- 6. Verify that the repo was created using the below command
```
    pachctl list repo
```
Refer to [this helpful tutorial](https://docs.pachyderm.com/latest/getting_started/beginner_tutorial/) to make your pipeline spec. <br>

- 7. Create your pipeline 
Following is a template command to make your pipeline
```
pachctl create pipeline -f pipeline_01.json
pachctl create pipeline -f pipeline_02.json

- 8. Track your jobs 
```
pachctl list job
watch pachctl list job
pachctl logs -j <job_id>
```
