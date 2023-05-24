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
from timeit import default_timer as timer

def find_free_port():
    '''Function that gets a free port for the current process'''
    with closing(socket.socket()) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        return s.getsockname()[1]

def get_local_rank(rank_info, rank_info_list):
    '''Function that figures out the local rank based on a list of rank,
    hostname, and port gathered from each of the workers'''
    # Note that rank_info_vector is sorted by rank, by definition of the MPI allgather routine.
    # Thus, if our current rank is the n-th item in rank_info_vector for which the hostname matches,
    # our local rank is n
    local_rank = 0
    for item in rank_info_list:
        if item['hostname'] == rank_info['hostname']:
            if item['rank'] == rank_info['rank']:
                return local_rank
            else:
                local_rank += 1

def get_rank_info(comm):
    '''Create a dict for this worker containing rank, hostname and port to be used by this worker'''
    rank = comm.Get_rank()
    hostname = socket.gethostname()
    port = find_free_port()
    
    return {
        'rank': rank,
        'hostname': hostname,
        'port': port,
    }

def set_tf_config(rank_info, rank_info_list):
    '''Sets the TF_CONFIG environment variable for the current worker, based on the rank_info_list'''
    worker_list = ['%s:%s' % (item['hostname'], item['port']) for item in rank_info_list]
    
    tf_config = {
        'cluster': {
            'worker': worker_list,
        },
        'task': {'type': 'worker', 'index': rank_info['rank']}
    }
    os.environ["TF_CONFIG"] = json.dumps(tf_config)
    
    print(f"Set TF_CONFIG for rank {rank_info['rank']} to {tf_config}.")
    return tf_config

parser = argparse.ArgumentParser(
                    prog='Tensorflow Distributed Test',
                    description='This program runs a distributed TensorFlow test using the tf.distribute.MultiWorkerMirroredStrategy and the Keras fit API'
)
parser.add_argument('-d', '--device', type=str, default='cpu', choices=['cpu', 'gpu'], help='Device to use for training')
parser.add_argument('--per-worker-batch-size', type=int, default=64, help='Batch size processed by each worker')
parser.add_argument('--per-worker-test-batch-size', type=int, default=512, help='Batch size for computing accuracy on the validation set')
parser.add_argument('--epochs-to-train', type=int, default=10, help='Number of epochs to train')
parser.add_argument('--steps-per-epoch', type=int, default=100, help='Number of steps to train per epoch')
args = parser.parse_args()

print("Importing model architecture and dataloader...")
# Make sure we can import mnist_setup from current dir
if '.' not in sys.path:
  sys.path.insert(0, '.')
import mnist_setup

os.environ.pop('TF_CONFIG', None)


# Multi-worker config
# We'll use mpi4py to figure out our rank, have each process select a socket and hostname,
# and allreduce that information to create a TF_CONFIG
print("Determining local rank, hostname, and selecting a port...")
comm = MPI.COMM_WORLD
rank_info = get_rank_info(comm)
rank_info_list = comm.allgather(rank_info)
local_rank = get_local_rank(rank_info, rank_info_list)
print(f"Rank {rank_info['rank']} has local_rank {local_rank}, hostname {rank_info['hostname']} and port {rank_info['port']}")

tf_config = set_tf_config(rank_info, rank_info_list)
num_workers = len(tf_config['cluster']['worker'])

# Set visible devices and create MultiWorkerMirroredStrategy
print(f"Selecting device: {args.device}")
if args.device == 'gpu':
    # Limit each local rank to its own GPU.
    physical_devices = tf.config.list_physical_devices('GPU')
    try:
        # We could do local_rank % len(physical_devices) if we wanted to support running more than one rank per device
        # The current code doesn't support that
        tf.config.set_visible_devices(physical_devices[local_rank], 'GPU')
        visible_devices = tf.config.get_visible_devices()
        print("Local rank: %s, visible_devices: %s" % (local_rank, visible_devices))
        assert len(visible_devices) == 1
    except:
        print("ERROR: selection of GPU device based on local rank failed. Local rank: %s. Selected devices: %s" 
              % (local_rank, visible_devices))

    # Set communication to NCCL explicitely
    communication_options = tf.distribute.experimental.CommunicationOptions(
        implementation=tf.distribute.experimental.CommunicationImplementation.NCCL)
    strategy = tf.distribute.MultiWorkerMirroredStrategy(communication_options=communication_options)
elif args.device == 'cpu':
    # Run on CPU, so make sure no GPU devices are visible
    tf.config.set_visible_devices([], 'GPU')
    visible_devices = tf.config.get_visible_devices()
    print("Local rank: %s, visible_devices: %s" % (local_rank, visible_devices))    
    strategy = tf.distribute.MultiWorkerMirroredStrategy()
print("Multiworker strategy created")

# Get datasets
global_batch_size = args.per_worker_batch_size * num_workers
global_test_batch_size = args.per_worker_test_batch_size * num_workers
multi_worker_dataset, multi_worker_test_dataset = mnist_setup.mnist_dataset(global_batch_size, global_test_batch_size)

with strategy.scope():
    multi_worker_model = mnist_setup.build_and_compile_cnn_model()

# Run the training
starttime = timer()
multi_worker_model.fit(multi_worker_dataset, epochs=args.epochs_to_train, steps_per_epoch=args.steps_per_epoch, verbose=2)
endtime = timer()
print("Keras fit completed!")

# Compute performance
training_time = endtime-starttime
total_samples_trained = global_batch_size*args.steps_per_epoch*args.epochs_to_train
throughput = total_samples_trained / training_time
if rank_info['rank'] == 0:
    print(f"Total training time: {training_time}")
    print(f"Performance: {throughput} img/s")

# Run evaluation to check accuracy on validation set
print("Run evaluation")
metrics = multi_worker_model.evaluate(multi_worker_test_dataset, verbose=2)
print(f"Final loss: {metrics[multi_worker_model.metrics_names.index('loss')]}")
print(f"Final accuracy: {metrics[multi_worker_model.metrics_names.index('accuracy')]}")
