import argparse
import timeit
import os

import numpy as np

import torch.backends.cudnn as cudnn
import torch.nn.functional as F
import torch.optim as optim
import torch.utils.data.distributed
from torchvision import models


# Benchmark settings
parser = argparse.ArgumentParser(description='PyTorch Synthetic Benchmark',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--fp16-allreduce', action='store_true', default=False,
                    help='use fp16 compression during allreduce')

parser.add_argument('--model', type=str, default='resnet50',
                    help='model to benchmark')
parser.add_argument('--batch-size', type=int, default=32,
                    help='input batch size')

parser.add_argument('--num-warmup-batches', type=int, default=10,
                    help='number of warm-up batches that don\'t count towards benchmark')
parser.add_argument('--num-batches-per-iter', type=int, default=10,
                    help='number of batches per benchmark iteration')
parser.add_argument('--num-iters', type=int, default=10,
                    help='number of benchmark iterations')

parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='disables CUDA training')

parser.add_argument('--use-adasum', action='store_true', default=False,
                    help='use adasum algorithm to do reduction')
parser.add_argument('--use-horovod', action='store_true', default=False)
parser.add_argument('--use-ddp', action='store_true', default=False)

parser.add_argument('--use-amp', action='store_true', default=False,
                    help='Use PyTorch Automatic Mixed Precision (AMP)')
parser.add_argument('--world-size', type=int, default=1,
                    help='Define the world size for ddp')
parser.add_argument('--master-port', type=int, default=False,
                    help='Define a master port for ddp')
parser.add_argument('--master-address', type=str, default='localhost',
                    help='Define a master address for ddp')

args = parser.parse_args()
args.cuda = not args.no_cuda and torch.cuda.is_available()

if args.use_horovod and args.use_ddp:
    print("You can't specify to use both Horovod and Pytorch DDP, exiting...")
    exit(1)

# Set MASTER_ADDR and MASTER_PORT environment variables
# By doing it as part of this python script, we don't need to have the launchers export them
# This saves us from having to find a launcher-agnostic way of exporting variables
os.environ['MASTER_ADDR'] = args.master_address
os.environ['MASTER_PORT'] = '%s' % args.master_port

# Set a default rank and world size, also for when ddp and horovod are not used
rank = 0
world_size = args.world_size
if args.use_horovod:
    import horovod.torch as hvd
    hvd.init()
    rank = hvd.local_rank()
    world_size = hvd.size()

    if args.cuda:
        # If launched with srun, you are in a CGROUP with only 1 GPU, so you don't need to set it.
        # If launched with mpirun, you see ALL local GPUs on the node, and you need to set which one
        # this rank should use.
        visible_gpus = torch.cuda.device_count()
        # Horovod: pin GPU to local rank.
        if visible_gpus > 1:
            torch.cuda.set_device(hvd.local_rank())

    # Should only be uncommented for debugging
    # In ReFrame tests, a print from each rank can mess up the output file, causing
    # performance and sanity patterns to not be found
    # print(f"hvd.local_rank: {rank}", flush=True)


if args.use_ddp:
    from socket import gethostname
    import torch.distributed as dist
    from torch.nn.parallel import DistributedDataParallel as DDP

    # world_size = int(os.environ["SLURM_NTASKS"])  ## No longer needed now we pass it as argument?
    # If launched with mpirun, get rank from this
    rank = int(os.environ.get("OMPI_COMM_WORLD_RANK", -1))
    if rank == -1:
        # Else it's launched with srun, get rank from this
        rank = int(os.environ.get("SLURM_PROCID", -1))
    if rank == -1:
        err_msg = "ERROR: cannot determine local rank. This test currently only supports OpenMPI"
        err_msg += " and srun as launchers. If you've configured a different launcher for your system"
        err_msg += " this test will need to be extended with a method to get it's local rank for that launcher."
        print(err_msg)

    # If launched with srun, you are in a CGROUP with only 1 GPU, so you don't need to set it.
    # If launched with mpirun, you see ALL local GPUs on the node, and you need to set which one
    # this rank should use.
    visible_gpus = torch.cuda.device_count()
    if visible_gpus > 1:
        print("Listing visible devices")
        for i in range(torch.cuda.device_count()):
            print(f"Device {i}: {torch.cuda.device(i)}")
        # This assumes compact mapping of ranks to available hardware
        # e.g. rank 0-x to node 1, rank x-y to node 2, etc
        # Assuming the set_compact_process_binding hook from the EESSI testsuite is called,
        # this condition should be satisfied
        local_rank = rank - visible_gpus * (rank // visible_gpus)
        torch.cuda.set_device(local_rank)
        print("Listing visible devices after setting one")
        for i in range(torch.cuda.device_count()):
            print(f"Device {i}: {torch.cuda.device(i)}")
        # We should also set CUDA_VISIBLE_DEVICES, which gets respected by NCCL
        os.environ['CUDA_VISIBLE_DEVICES'] = '%s' % local_rank
        print(f"host: {gethostname()}, rank: {rank}, local_rank: {local_rank}")
    else:
        print(f"host: {gethostname()}, rank: {rank}")

    def setup(rank, world_size):

        # initialize the process group
        if args.cuda:
            dist.init_process_group("nccl", rank=rank, world_size=world_size)
        else:
            dist.init_process_group("gloo", rank=rank, world_size=world_size)

    def cleanup():
        # clean up the distributed environment
        dist.destroy_process_group()

    setup(rank, world_size)
    if rank == 0:
        print(f"Group initialized? {dist.is_initialized()}", flush=True)


# This relies on the 'rank' set in the if args.use_horovod or args.use_ddp sections
def log(s, nl=True):
    if (args.use_horovod or args.use_ddp) and rank != 0:
        return
    print(s, end='\n' if nl else '', flush=True)


log(f"World size: {world_size}")

torch.set_num_threads(int(os.environ['OMP_NUM_THREADS']))
torch.set_num_interop_threads(2)

cudnn.benchmark = True

# Set up standard model.
model = getattr(models, args.model)()

# By default, Adasum doesn't need scaling up learning rate.
lr_scaler = hvd.size() if not args.use_adasum and args.use_horovod else 1

if args.cuda:
    # Move model to GPU.
    model.cuda()
    # If using GPU Adasum allreduce, scale learning rate by local_size.
    if args.use_horovod and args.use_adasum and hvd.nccl_built():
        lr_scaler = hvd.local_size()

# If using DDP, wrap model
if args.use_ddp:
    model = DDP(model)

optimizer = optim.SGD(model.parameters(), lr=0.01 * lr_scaler)

# Horovod: (optional) compression algorithm.
if args.use_horovod:
    compression = hvd.Compression.fp16 if args.fp16_allreduce else hvd.Compression.none

# Horovod: wrap optimizer with DistributedOptimizer.
if args.use_horovod:
    optimizer = hvd.DistributedOptimizer(optimizer,
                                         named_parameters=model.named_parameters(),
                                         compression=compression,
                                         op=hvd.Adasum if args.use_adasum else hvd.Average)

    # Horovod: broadcast parameters & optimizer state.
    hvd.broadcast_parameters(model.state_dict(), root_rank=0)
    hvd.broadcast_optimizer_state(optimizer, root_rank=0)

# Set up fixed fake data
data = torch.randn(args.batch_size, 3, 224, 224)
target = torch.LongTensor(args.batch_size).random_() % 1000
if args.cuda:
    data, target = data.cuda(), target.cuda()

# Create GradScaler for automatic mixed precision
scaler = torch.cuda.amp.GradScaler(enabled=args.use_amp)

# Set device_type for AMP
if args.cuda:
    device_type = "cuda"
else:
    device_type = "cpu"


def benchmark_step():
    optimizer.zero_grad()
    with torch.autocast(device_type=device_type, enabled=args.use_amp):
        output = model(data)
        loss = F.cross_entropy(output, target)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()


log('Model: %s' % args.model)
log('Batch size: %d' % args.batch_size)
device = 'GPU' if args.cuda else 'CPU'
if args.use_horovod:
    log('Number of %ss: %d' % (device, hvd.size()))

# Warm-up
log('Running warmup...')
timeit.timeit(benchmark_step, number=args.num_warmup_batches)

# Benchmark
log('Running benchmark...')
img_secs = []
for x in range(args.num_iters):
    time = timeit.timeit(benchmark_step, number=args.num_batches_per_iter)
    img_sec = args.batch_size * args.num_batches_per_iter / time
    log('Iter #%d: %.1f img/sec per %s' % (x, img_sec, device))
    img_secs.append(img_sec)

# Results
img_sec_mean = np.mean(img_secs)
img_sec_conf = 1.96 * np.std(img_secs)
log('Img/sec per %s: %.1f +-%.1f' % (device, img_sec_mean, img_sec_conf))
log('Total img/sec on %d %s(s): %.1f +-%.1f' %
    (world_size, device, world_size * img_sec_mean, world_size * img_sec_conf))
