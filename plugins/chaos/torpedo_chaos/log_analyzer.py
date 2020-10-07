import ast
import json
import logging
import os
import requests
import subprocess
import sys

from datetime import datetime

from common.driver.kubernetes.pods import Pods

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
stream_handle = logging.StreamHandler()
formatter = logging.Formatter(
    '(%(name)s): %(asctime)s %(levelname)s %(message)s')
stream_handle.setFormatter(formatter)
LOG.addHandler(stream_handle)

token = subprocess.check_output(
    "cat /var/run/secrets/kubernetes.io/serviceaccount/token",
    stderr=subprocess.STDOUT,
    shell=True).decode('utf-8').strip("\n")

kubeconf_path = '/root/.kube'

kubeconf = """
apiVersion: v1
kind: Config
clusters:
- name: default-cluster
  cluster:
    insecure-skip-tls-verify: true

    server: "https://kubernetes.default.svc.cluster.local:443"

contexts:
- name: default-context
  context:
    cluster: default-cluster
    namespace: default
    user: default-user
current-context: default-context
users:
- name: default-user
  user:

    token: "%s"
""" % (token)

try:
    os.mkdir(kubeconf_path)
except OSError:
    print ("Creation of the directory %s failed" % kubeconf_path)

with open(kubeconf_path + '/config', 'w') as f:
    f.write(kubeconf)
pod_conn = Pods()

def log_analyzer(log_dir, service_list):

    result_list = []
    log_list = []
    log_list.extend(pod_conn.get_pods(
        namespace="metacontroller",
        label_selector="resiliency=enabled")[0])
    cur_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    for svc in service_list:
        svc_file = "".join(
            [x for x in log_list if (svc['service'] in x and "traffic" in x)])
        chaos_file = "".join(
            [x for x in log_list if (svc['service'] in x and "chaos" in x)])
        pass_search = (
            "grep -i %s/%s.log -e 'pass'|wc -l") % (log_dir,
                                                      svc_file)
        fail_search = (
            "grep -i %s/%s.log -e 'fail'|wc -l") % (log_dir,
                                                      svc_file)
        pods_killed = (
            "grep -i %s/%s.log -e 'INFO Deleting pod'|wc -l"
            ) % (log_dir, chaos_file)
        pass_tc = subprocess.check_output(pass_search,
                                          stderr=subprocess.STDOUT,
                                          shell=True).decode(
                                          'utf-8').strip("\n")
        fail_tc = subprocess.check_output(fail_search,
                                          stderr=subprocess.STDOUT,
                                          shell=True).decode(
                                          'utf-8').strip("\n")
        kill_tc = subprocess.check_output(pods_killed,
                                          stderr=subprocess.STDOUT,
                                          shell=True).decode(
                                          'utf-8').strip("\n")
        result_dict = {
                       "Test Case": svc['service'],
                       "Cluster Name": svc['cluster-type'],
                       "TimeStamp": cur_time,
                       "Duration": svc['duration'],
                       "Number of pods killed": kill_tc,
                       "Pass test count": pass_tc,
                       "Fail test count": fail_tc
                      }
        #push Test_results to elasticsearch
        if 'elasticsearch' in svc:
            url = svc['elasticsearch']['elasticsearch-apiendpoint']
            index = svc['elasticsearch']['index']
            auth = (svc['elasticsearch']['user'], svc['elasticsearch']['password'])
            doc_type = svc['service']
            data = json.dumps(result_dict)
            headers={'Content-Type': 'application/json'}
            req = requests.get(url+index,auth=auth)
            if req.status_code != 200:
                index_obj = requests.put(url+index,auth=auth)
                es_push_log_url = index_obj.url + "/" + doc_type
            else:
                es_push_log_url = url + index + "/" + doc_type
            push = requests.post(es_push_log_url,data=data,auth=auth,headers=headers)
            if push.status_code != 201:
                LOG.error("Logs are not pushed to ELK \n" + json.dumps(
                 push.text, indent=2))
            else:
                LOG.info("Resiliency Test Results pushed in ELK \n")
        result_list.append(result_dict)
    with open(os.path.join(log_dir, "test_results"), "w") as f:
        json.dump(result_list, f)
    LOG.info("Resiliency Test Results \n" + json.dumps(
             result_list, indent=2))
    LOG.info("All the logs are written to %s" % (log_dir))


if __name__ == "__main__":
    inputs = sys.argv
    cur_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_dir = os.path.join("/var/log/resiliency", "resiliency_" + cur_time)
    cmd = "bash log_collector.sh %s" % (log_dir)
    subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                            shell=True).decode('utf-8')
    service_list = ast.literal_eval(inputs[1])
    log_analyzer(log_dir, service_list)
