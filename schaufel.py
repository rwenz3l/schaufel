#! /usr/bin/python3

import os
import sys
import requests
import json
from time import sleep
from requests.exceptions import ConnectionError
from flask import Flask, render_template, jsonify, request
from elasticsearch import Elasticsearch

# CONFIG

with open('config.json') as json_data:
    config = json.load(json_data)
    json_data.close()

LIBRARY_PATH = config['library_path']
ELASTIC_INDEX = config['elastic_index']

# FLASK
app = Flask(__name__)
app.secret_key = 'SchaufelKey'

# INIT
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])


def wait_for_es():
    """
    Make Sure that the connection to
    :return:
    """
    for x in range(0, 5):
        print("Attempt: %i" % x)
        try:
            es.info()
            return 0
        except Exception as e:
            sleep(5)
            pass
        print("Could not Connect to ES")
    sys.exit(1)


@app.route('/')
def root():
    """
    WebApp Root
    :return: index page with random result
    """
    random = {"size": 1, "query": {"function_score": {"functions": [{"random_score": {"seed": "1477072619038"}}]}}}
    res = es.search(index=ELASTIC_INDEX, doc_type="book", body=random)
    return render_template('index.html', results=res['hits']['hits'])


@app.route('/es_status')
def test_elasticsearch():
    try:
        res = requests.get('http://localhost:9200')
        j = json.loads(res.content)
        return jsonify(j)
    except ConnectionError:
        print('Connection Error')
    return 'ElasticSearch is offline'


@app.route('/search', methods=['POST'])
def search_books():
    q = request.form['query']

    query = {"from": 0, "size": 20, "query": {"match": {"filename": {"query": q, "operator": "and"}}}}
    res = es.search(index=ELASTIC_INDEX, doc_type="book", body=query)
    return render_template('search_alt.html', results=res['hits']['hits'])


@app.route('/index')
def index_books():
    # Delete old Index
    es.indices.delete(index=ELASTIC_INDEX, ignore=[400, 404])
    # Read ES-Config from File
    with open('es_schaufel_index.json') as json_data:
        d = json.load(json_data)
        json_data.close()
    # Create new Index
    es.indices.create(index=ELASTIC_INDEX, body=d, ignore=400)
    for r, dirs, files in os.walk(LIBRARY_PATH):
        for file in files:
            file_name, file_ext = os.path.splitext(file)
            file_path = os.path.join(r, file)
            if file_ext in ('.pdf', '.epub', '.mobi'):
                print("Add to Index: %s" % file)
                es.index(index=ELASTIC_INDEX, doc_type="book", body={"filename": file_name, "filetype": file_ext,
                                                                     "filepath": file_path})
    return 'Library Index updated'


if __name__ == '__main__':
    app.debug = True
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        wait_for_es()  # waits for elasticsearch
        index_books()
    # Start Flask App
    app.run(host="0.0.0.0", port=8150)
