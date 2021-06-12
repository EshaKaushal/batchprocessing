import csv
import os
import time
import logging
from google.cloud import storage
from transformers.pipelines import pipeline

environment = ''
bucket = ''
models = {}
delimiter='/'

# function to read file from input directory
# answer the questions and write it to output directory
def question_answer(qa_file):
    # importing the file using pandas library
    # data = pd.read_csv(qa_file)
    final_answer = []

    hg_comp = pipeline('question-answering', model="distilbert-base-uncased-distilled-squad",
                       tokenizer="distilbert-base-uncased-distilled-squad")
    answer = []
    questions = []
    contexts = []

    with open(qa_file, 'r') as file:
        print("inside file reading loop")
        reader = csv.DictReader(file)
        print("file read complete")
        for row in reader:
            print("Inside File Row Read loop")
            print(row)
            context = row["context"]
            question = row["question"]
            answer.append(hg_comp({'question': question, 'context': context})['answer'])
            questions.append(question)
            contexts.append(context)
        final_answer.append(questions)
        final_answer.append(contexts)
        final_answer.append(answer)
        print(final_answer)
    # for idx, row in data.iterrows():
    #    context = row['context']
    #    question = row['question']
    #    questions.append(question)
    #    answer.append(hg_comp({'question': question, 'context': context})['answer'])
    timestamp = str(int(time.time()))
    output_folder = os.getcwd() + '\pfs\out'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, mode=0o777)
    with open(output_folder + delimiter+'answer_' + timestamp + ".csv", 'w') as f:
        fileWriter = csv.writer(f, delimiter=',')
        for row in zip(*final_answer):
            fileWriter.writerow(row)

    # data["answer"] = answer
    # data.to_csv("/pfs/out/"+"question_answer"+timestamp+".csv", index=False)


def downloadFiles():

    print('Inside Download Files')

    bucket_name = 'mgmt590-assgn4'
    storage_client = storage.Client.from_service_account_json('../test/credentials.json')
    bucket = storage_client.get_bucket(bucket_name)

    # Create this folder locally if not exists
    output_folder = os.getcwd()+'\pfs\in'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, mode=0o777)
    try:
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.download_to_filename(output_folder+delimiter+blob.name)
    except Exception as ex:
     print("Exception occurred while trying to download files ", ex)


if __name__ == '__main__':

    environment = "local"

    if environment == "local":
        # bucket_name = 'mgmt590-storage'
        # storage_client = storage.Client.from_service_account_json('credentials.json')
        # bucket = storage_client.get_bucket(bucket_name)
        downloadFiles()
    elif environment == "prod":
        bucket_name = 'mgmt590-assgn4'
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        print("Downloading Files")
        downloadFiles()
    output_folder = os.getcwd()+'\pfs\in'
    # walk /pfs/question_answer and call question_answer on every file found
    for dirpath, dirs, files in os.walk(output_folder):
        for file in files:
            print("We are looping in the files")
            print("File Name: " + file)
            print(os.path.join(dirpath, file))
            question_answer(os.path.join(dirpath, file))

