from flask import Flask, request, jsonify, abort
from waitress import serve
import subprocess
import json
import os
import threading
import secret
import math
from pathlib import Path

app = Flask(__name__)

IS_RESTARTING = dict()

@app.route('/')
def index():
  return 'Web App with Python Flask!'

def restart_docker_compose_internal(files, docker_path):
  global IS_RESTARTING

  docker_compose = ['docker', 'compose']
  restarting_files = []

  docker_folder = os.path.basename(os.path.normpath(docker_path))

  for file in files:
    file_key = docker_folder + '/' + file
    if file_key not in IS_RESTARTING or not IS_RESTARTING[file_key]:
      restarting_files.append(file_key)
      docker_compose.append('-f')
      docker_compose.append(file)

  if len(docker_compose) <= 2: return
  
  try:
    # docker compose down
    p = subprocess.Popen([*docker_compose, 'down'], cwd=docker_path)
    p.wait()

    # docker compose up -d
    p = subprocess.Popen([*docker_compose, 'up', '-d'], cwd=docker_path)
    p.wait()
  finally:
    for file in restarting_files:
      IS_RESTARTING[file] = False

def get_indexer_status_internal():
  global IS_RESTARTING

  docker_compose = ['docker', 'compose', '-f', 'compose-all-services.yml', 'exec', 'cli']
  graph_cli_command = ['graph', 'indexer', 'status', '--output=json']

  docker_folder = secret.DOCKER_FOLDER

  # exec shell command
  process = subprocess.Popen([*docker_compose, *graph_cli_command], cwd=docker_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = process.communicate()
  errcode = process.returncode

  if errcode:
    return {
      'error_code': errcode,
      'err': err.decode('utf-8'),
    }
  else:
    print(out.decode('utf-8'))
    return json.loads(out.decode('utf-8'))
  
def upgrade_allocation_internal(oldDeployment, newDeployment):
  indexer_status = get_indexer_status_internal()
  rules = indexer_status["indexingRules"]

  docker_compose = ['docker', 'compose', '-f', 'compose-all-services.yml', 'exec']
  docker_folder = secret.DOCKER_FOLDER

  hasOldDeployment = False

  for rule in rules:
    if rule['subgraphDeployment'].lower() == oldDeployment:
      hasOldDeployment = True
      allocationAmount = math.ceil(int(rule['allocationAmount']['hex'], base=16) / 1e18)

  if hasOldDeployment:
    print('Stop indexing ' + oldDeployment)
    process = subprocess.Popen([*docker_compose, 'cli', 'graph', 'indexer', 'rules', 'delete', oldDeployment], cwd=docker_folder)
    process.wait()
    
    print('Remove old subgraph ' + oldDeployment)
    process = subprocess.Popen([*docker_compose, 'index-node-0', 'graphman', 'drop', oldDeployment], cwd=docker_folder)
    process.wait()

    print('Index new subgraph ' + newDeployment)
    process = subprocess.Popen([*docker_compose, 'cli', 'graph', 'indexer', 'rules', 'set', newDeployment, 'decisionBasis', 'always', 'allocationAmount', str(allocationAmount)], cwd=docker_folder)
    process.wait()
  else:
    print('Missing allocation ' + oldDeployment)

@app.route('/upgrade_allocation', methods=['POST'])
def upgrade_allocation():
  body = request.json

  upgrade_allocation_internal(body['oldDeployment'], body['newDeployment'])

  return jsonify({
    'success': True,
  })

@app.route('/indexer_status', methods=['GET'])
def get_indexer_status():
  return get_indexer_status_internal()

@app.route('/docker_compose_is_restarting/<string:docker_folder>/<string:filename>', methods=['GET'])
def get_docker_compose_is_restarting(docker_folder, filename):
  global IS_RESTARTING
  file_key = docker_folder + '/' + filename
  return jsonify({
    'is_restarting': file_key in IS_RESTARTING and IS_RESTARTING[file_key]
  })

@app.route('/restart_docker_compose', methods=['POST'])
def restart_docker_compose():
  data = request.get_json()

  restart_docker_compose_internal(data['files'], data['docker_path'])

  return jsonify(data)

@app.route('/controller/volume_size/<string:volume_name>', methods=['GET'])
def get_volume_size(volume_name):
  try:
    cmd = ['docker', 'volume', 'inspect', volume_name]
    out = subprocess.check_output(cmd)

    info = json.loads(out)
    folder = Path(info[0]['Mountpoint'])
    volume_size = sum(f.stat().st_size for f in folder.glob('**/*') if f.is_file())

    return jsonify({
      # 'mount_point': info[0]['Mountpoint'],
      'volume_size': volume_size
    })
  except:
    return abort(404)

if __name__ == "__main__":
  print("Server running at port 1111")
  serve(app, host='0.0.0.0', port=1111)
  # app.run(host='0.0.0.0', port=1111)
  