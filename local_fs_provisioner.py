#!/usr/bin/env python3

import kubernetes
import logging, os, platform, math
import subprocess

# logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s:%(lineno)s: %(message)s",
#                     level=os.getenv("LOGGING_LEVEL", "DEBUG"))

logging.basicConfig(format="[%(levelname)s] line:%(lineno)s: %(message)s",
                    level=os.getenv("LOGGING_LEVEL", "DEBUG"))

kubernetes.config.load_kube_config()
#kubernetes.config.load_incluster_config()
v1 = kubernetes.client.CoreV1Api()

#my_node_name = os.getenv('MY_NODE_NAME')
my_node_name = platform.node()
my_host_path = os.getenv('MY_HOST_PATH')

w = kubernetes.watch.Watch()
logging.info(f"Watching PVCs on {my_node_name}. Filesystem volumes path: {my_host_path}")
for event in w.stream(v1.list_persistent_volume_claim_for_all_namespaces):
    if event['type'] == 'ADDED':
        obj = event['object']
        meta = obj.metadata
        spec = obj.spec
        storage = int("".join([c for c in list(spec.resources.requests['storage']) if c.isdigit()]))
        storage += math.ceil(storage * 0.05)
        
        #print(meta)
        if (spec.storage_class_name == 'local-storage'
            and meta.annotations and not 'pv.kubernetes.io/bind-completed' in meta.annotations
            and 'kubernetes.io/hostname' in meta.annotations
            and meta.annotations['kubernetes.io/hostname'] == my_node_name):    

            logging.info(f"New PVC which needs free PV from storage class: {spec.storage_class_name} on my node: {my_node_name}")
            logging.info(f"NAMESPACE: {meta.namespace} NAME: {meta.name} STORAGE: {storage}")

            vol_name = meta.name
            cmds = f'''
            truncate -s {storage}GiB /{my_host_path}/disk_{vol_name}
            mkdir /{my_host_path}/vol_{vol_name}
            mkfs.ext4 /{my_host_path}/disk_{vol_name}
            mount /{my_host_path}/disk_{vol_name} /{my_host_path}/vol_{vol_name}            
            '''
            try:
                process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                out, err = process.communicate(cmds, timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                logging.error(f"Timeout expired when running cmds: {cmds}")
            
            if process.returncode != 0:
                logging.error(f"{err}")   
            else:
                logging.info(f"Created disk/vol_{vol_name}")
