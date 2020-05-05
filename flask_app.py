#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import datetime

from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask_cors import CORS
from flask import request
from flask import send_from_directory
from flask import send_file

from app_topology import gather_info, save_topology, compare_topologies, TOPOLOGIES_DIR_PATH

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/', methods=['GET'])
def root():
    return app.send_static_file('index.html')

@app.route('/api/v1.0/topology/<string:topology_name>', methods=['GET'])
def get_topology(topology_name):
    if topology_name == 'last':
        # find latest topology
        topology_files = {}
        # looking for topologies files
        for file_name in os.listdir(TOPOLOGIES_DIR_PATH):
            # select files with correct extension
            if file_name.endswith('.json'):
                # getting date and time from filename
                filename_datetime = datetime.datetime.strptime(file_name.strip('.json')[len('topology')+1:],'%Y_%m_%d-%H_%M_%S')
                # adding files to dict with key equal to datetime in unix format
                topology_files[filename_datetime.timestamp()] = file_name
        if len(topology_files) > 0:
            # getting the latest
            topology_key = sorted(topology_files.keys(), reverse=True)[0]
            topology_file_path = os.path.join(TOPOLOGIES_DIR_PATH, topology_files[topology_key])
            return send_file(topology_file_path)
        else:
            abort(404)
    elif topology_name == 'create':
        topology_data = gather_info()
        topology_filename = save_topology(topology_data,datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))
        return jsonify({'data': { 'topology_name': topology_filename.strip('.json'), 'topology_file': topology_filename } })
    elif topology_name == 'list':
        topology_files = []
        # looking for topologies files
        for file_name in os.listdir(TOPOLOGIES_DIR_PATH):
            # select files with correct extension
            if file_name.endswith('.json'):
                # adding files to list
                topology_files.append(file_name)
        if len(topology_files) > 0:
            return jsonify({'data': [ { 'topology_name': value.strip('.json'), 'topology_file': value } for counter, value in enumerate(topology_files)]})
        else:
            abort(404)
    elif topology_name == 'compare':
        file1 = os.path.join(TOPOLOGIES_DIR_PATH, request.args.get('file1', default = '', type = str))
        file2 = os.path.join(TOPOLOGIES_DIR_PATH, request.args.get('file2', default = '', type = str))

        file_diff = compare_topologies(file1,file2)
        if not (file_diff is False):
            return jsonify({'data': { 'compare': file_diff } })
        else:
            abort(404)
    else:
        topology_file = os.path.join(TOPOLOGIES_DIR_PATH, topology_name)
        if os.path.isfile(topology_file):
            return send_file(topology_file)
        else:
            abort(404)
    return

if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5000',debug=True)
