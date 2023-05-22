# Author: Caspar van Leeuwen (SURF)
# Based on the example for the MultiWorkerMirroredStrategy with keras from
# https://www.tensorflow.org/tutorials/distribute/multi_worker_with_keras
import json
import os
import sys
import tensorflow as tf
import socket
import argparse
from contextlib import closing
from mpi4py import MPI

parser = argparse.ArgumentParser(
                    prog='Tensorflow Distributed Test',
                    description='This program runs a distributed TensorFlow test using the tf.distribute.MultiWorkerMirroredStrategy and the Keras fit API'
)
parser.add_argument('-d', '--device', type=str, default='cpu', choices=['cpu', 'gpu'], help='Device to use for training')
args = parser.parse_args()

print("Importing model architecture and dataloader...")
# Make sure we can import mnist_setup from current dir
if '.' not in sys.path:
  sys.path.insert(0, '.')
import mnist_setup

os.environ.pop('TF_CONFIG', None)

def find_free_port():
    with closing(socket.socket()) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        return s.getsockname()[1]


# Multi-worker config
# We'll use mpi4py to figure out our rank, have each process select a socket and hostname,
# and allreduce that information to create a TF_CONFIG
print("Determining local rank, hostname, and selecting a port...")
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
hostname = socket.gethostname()
port = find_free_port()

rank_info = {
    'rank': rank,
    'hostname': hostname,
    'port': port,
}

rank_info_vector = comm.allgather(rank_info)
# print(f"Rank_info_vector: {rank_info_vector}")

# Get the local rank
def get_local_rank(rank_info_vector):
    # Note that rank_info_vector is sorted by rank, by definition of the MPI allgather routine.
    # Thus, if our current rank is the n-th item in rank_info_vector for which the hostname matches,
    # our local rank is n
    local_rank = 0
    for item in rank_info_vector:
        if item['hostname'] == hostname:
            if item['rank'] == rank:
                return local_rank
            else:
                local_rank += 1

local_rank = get_local_rank(rank_info_vector)
print(f"Rank {rank} has local_rank {local_rank}, hostname {hostname} and port {port}")

worker_list = ['%s:%s' % (item['hostname'], item['port']) for item in rank_info_vector]

tf_config = {
    'cluster': {
        'worker': worker_list,
    },
    'task': {'type': 'worker', 'index': rank}
}
os.environ["TF_CONFIG"] = json.dumps(tf_config)

print(f'Set TF_CONFIG for rank {rank} to {tf_config}.')
per_worker_batch_size = 64
per_worker_test_batch_size = 512
num_workers = len(tf_config['cluster']['worker'])

if args.device == 'gpu':
    # Limit each local rank to its own GPU.
    # Note that we need to create the MultiWorkerMirroredStrategy before calling tf.config.list_logical_devices
    # To avoid running into this error https://github.com/tensorflow/tensorflow/issues/34568
    physical_devices = tf.config.list_physical_devices('GPU')
    try:
        # Todo: we could do local_rank % len(physical_devices)
        tf.config.set_visible_devices(physical_devices[local_rank], 'GPU')
        visible_devices = tf.config.get_visible_devices('GPU')
        print("Local rank: %s, visible_devices: %s" % (local_rank, visible_devices))
        assert len(visible_devices) == 1
    except:
        print("ERROR: selection of GPU device based on local rank failed. Local rank: %s. Selected devices: %s" 
              % (local_rank, visible_devices))

    # Set communication to NCCL explicitely
    communication_options = tf.distribute.experimental.CommunicationOptions(
        implementation=tf.distribute.experimental.CommunicationImplementation.NCCL)
    strategy = tf.distribute.MultiWorkerMirroredStrategy(communication_options=communication_options)
else:
    physical_devices = tf.config.list_physical_devices('CPU')
    tf.config.set_visible_devices(physical_devices, 'CPU')
    visible_devices = tf.config.get_visible_devices('CPU')
    print("Local rank: %s, visible_devices: %s" % (local_rank, visible_devices))    
    strategy = tf.distribute.MultiWorkerMirroredStrategy()

print("Multiworker strategy created")
global_batch_size = per_worker_batch_size * num_workers
global_test_batch_size = per_worker_test_batch_size * num_workers
multi_worker_dataset, multi_worker_test_dataset = mnist_setup.mnist_dataset(global_batch_size, global_test_batch_size)

with strategy.scope():
    multi_worker_model = mnist_setup.build_and_compile_cnn_model()

multi_worker_model.fit(multi_worker_dataset, validation_data=multi_worker_test_dataset, epochs=10, steps_per_epoch=100)

print("Keras fit completed!")
