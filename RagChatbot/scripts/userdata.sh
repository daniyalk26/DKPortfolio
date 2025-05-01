#!/bin/bash -ex
echo "#################### Training Started#############################################"
date
#Home Directory
cd /home/ec2-user

#Installing numpy package
pip3 install numpy

#creating scripts directory
mkdir scripts

#copy the scripts and other objects for model creation
aws s3 cp $ARTIFACTORY_BUCKET/chatbot/$MODEL_VERSION/scripts/ scripts/ --recursive
export PATH=$PATH:/home/ssm-user/.local/bin
source ~/.bash_profile

#Train and validate the model
cd scripts
python train_model.py

#Upload the files generated
aws s3 cp models/ $ARTIFACTORY_BUCKET/chatbot/$MODEL_VERSION/scripts/models/ --recursive

#Send a marker file after successful generation of model
touch marker.success
aws s3 cp marker.success $ARTIFACTORY_BUCKET/chatbot/$MODEL_VERSION/marker.success

#send log file
aws s3 cp /$LOG_FILE $ARTIFACTORY_BUCKET/chatbot/$MODEL_VERSION/$LOG_FILE
date
echo "#################### Training Started#############################################"