import argparse
import logging
import os
import shutil
import sys
import yaml

import gpustat
import pkg_resources


__version__ = "0.2.0"
__pkg__ = __name__



def _data_path(filename):
    # entry point to locate datafile
    resource = os.path.join('data', filename)
    filepath = pkg_resources.resource_filename(__pkg__, resource)
    if not os.path.isfile(filepath):
        filepath = None
    return filepath


def print_data_path():
    filename = _data_path(sys.argv[1])
    if filename is not None:
        print(filename)
    else:
        sys.exit(1)


def create_config():
    parser = argparse.ArgumentParser(
        description='Create a template configuration file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('output', help='Output config file.')
    args = parser.parse_args()

    default = _data_path('config.yaml')
    shutil.copyfile(default, args.output)


def process_katuali_config():
    # Helper entry point for katuali shell wrapper
    parser = argparse.ArgumentParser(
        description='Helper entry point for katuali shell wrapper.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('inputs', nargs='+', help='Inputs: base_config out_config additional_config')

    args=parser.parse_args()
    args.base_configfile = args.inputs[0]
    args.out_configfile = args.inputs[1]
    args.additional_config = args.inputs[2] if len(args.inputs) > 2 else []
    if isinstance(args.additional_config, str):
        args.additional_config = [args.additional_config]

    # sys.argv ignores quotes, so would split e.g.
    # MINI_ASSEMBLE_OPTS="-n 10" GUPPY_OPTS="--hp_correct 1"
    # into
    # ['MINI_ASSEMBLE_OPTS=-n', '10', 'GUPPY_OPTS=--hp_correct', '1']

    fixed = []
    for c in args.additional_config:
        if '=' in c:
            fixed.append(c)
        else:
            fixed[-1] += ' ' + c

    d = {}
    for arg in fixed:
        k, v = arg.split('=')
        d[k] = v

    conf = yaml.load(open(args.base_configfile))
    conf.update(d)
    yaml.dump(conf, open(args.out_configfile, 'w'))


def pick_gpu():
    parser = argparse.ArgumentParser(
        description='Choose GPU to use from enviroment variable, falling back '
        'to GPU with lowest current use.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--env_var', default='SGE_HGR_gpu',
        help='Environment variable from which to extract GPU.')
    args=parser.parse_args()


    logging.basicConfig(
        format='[%(asctime)s - %(name)s] %(message)s',
        datefmt='%H:%M:%S', level=logging.INFO)
    logger = logging.getLogger('pick_gpu')

    gpu = os.getenv(args.env_var)
    if gpu is None:
        stats = gpustat.GPUStatCollection.new_query()
        sorter = lambda s: (s.memory_used, s.utilization, s.temperature)
        gpu = sorted(stats.gpus, key=sorter)[0].index
        logger.info('{} was not set, setting GPU to {} based on memory and utilization'.format(args.env_var, gpu))
    else:
        gpu = gpu.replace('cuda', '')
        logger.info('Using gpu {} from {}'.format(gpu, args.env_var))
    print(gpu)

