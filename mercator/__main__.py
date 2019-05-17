import argparse
import datetime
from importlib import import_module
import logging
import logging.config
import os
import sys
import threading
import time

import tqdm
import yaml

from mercator.node import NodeStatus

from mercator.utils import Outfile, print_bold

def _init_logger():
    config_file_path = os.path.join(os.path.dirname(__file__), '..',
                                    'logging.yml')
    config_file_path = os.path.abspath(config_file_path)

    with open(config_file_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
        except yaml.YAMLError as err:
            print_bold('{0} is not a valid YAML file'.format(config_file_path))
            exit(1)
        except ValueError as err:
            print_bold('{0} is not loaded succesfully'.format(config_file_path))
            print(str(err))
            exit(1)

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='config', help='path to config YAML file',
                        type=str, required=True)
    parser.add_argument('-i', dest='exp_id',
                        help='attach to exp_id (only for iotlab)',
                        type=int)
    parser.add_argument('-p', dest='program_firmware',
                        help='program firmware to nodes (only for opentestbed)',
                        default=False, action='store_true')
    parser.add_argument('-o', dest='out_file_path',
                        help='path to an output file',
                        type=str, default='output.jsonl.gz')
    parser.add_argument('-f', dest='overwrite_out_file',
                        help='overwrite an existing file',
                        default=False, action='store_true')
    return parser.parse_args()

def _read_config(config_file_path):
    with open(config_file_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as err:
            config_file_name = os.path.basename(config_file_path)
            print('cannot parse {0} as a YAML file'.format(config_file_name),
                  file=sys.stderr)
            print(err, file=sys.stderr)
            exit(1)
    return config

def _setup_platform(platform_config, args):
    module_name = 'mercator.platform.{0}'.format(platform_config['name'])
    platform_module = import_module(module_name)

    if platform_config['name'] == 'iotlab':
        platform_args = {'exp_id': args.exp_id}
    elif platform_config['name'] == 'opentestbed':
        platform_args = {'program_firmware': args.program_firmware}
    else:
        raise NotImplementedError(
            'Platform {0} is not supported'.format(platform_config['name']))

    return  platform_module.Platform(platform_config, **platform_args)

def _run_transactions(num_transactions, channels, nodes, outfile):
    num_nodes = len(nodes)
    total_exec_num = num_transactions * len(channels) * num_nodes

    outfile.open()
    with tqdm.tqdm(total=total_exec_num, unit='meas') as pbar:
        for trans_ctr in range(num_transactions):
            for channel in channels:
                for node_idx, tx_node in enumerate(nodes):
                    rx_nodes = [node for node in nodes if node != tx_node]

                    _beginning_of_measurement(pbar,
                                             trans_ctr, channel,
                                             node_idx, num_nodes)

                    start_time = datetime.datetime.now()

                    _make_sure_every_node_is_idle(nodes)

                    _make_rx_nodes_start_listening(rx_nodes,
                                                   tx_node, channel, trans_ctr)

                    # start TX and wait to finish
                    tx_node.start_tx(channel, trans_ctr)
                    tx_node.wait_tx_done()

                    _make_rx_nodes_stop_listening(rx_nodes)
                    _save_data(outfile, tx_node, rx_nodes,
                               start_time, trans_ctr, channel)

                    _end_of_measurement(pbar,
                                        trans_ctr, channel, node_idx, num_nodes)

    outfile.flush()
    outfile.close()

def _beginning_of_measurement(pbar, trans_ctr, channel, node_idx, num_nodes):
    logging.info('Beginning of measurement - '
                 + 'trans_ctr: {0}, '.format(trans_ctr)
                 + 'channel: {0}, '.format(channel)
                 + 'tx_node: {0}/{1}'.format(node_idx+1,
                                             num_nodes))

    pbar.set_description('trans_ctr {0}'.format(trans_ctr))
    pbar.set_postfix(ch=channel,
                     tx_node='{0}/{1}'.format(node_idx+1,
                                              num_nodes))

def _make_sure_every_node_is_idle(nodes):
    threads = {}
    for _idx, _node in enumerate(nodes):
        thread = threading.Thread(target=_node.update_status)
        thread.start()
        threads[_idx] = thread
    for _idx, _node in enumerate(nodes):
        threads[_idx].join()
        assert _node.status == NodeStatus.IDLE

def _make_rx_nodes_start_listening(rx_nodes, tx_node, channel, trans_ctr):
    threads = {}
    for _idx, _node in enumerate(rx_nodes):
        thread = threading.Thread(target=_node.start_rx,
                                  args=(channel,
                                        tx_node.mac_addr,
                                        trans_ctr))
        thread.start()
        threads[_idx] = thread
    for _idx, _node in enumerate(rx_nodes):
        threads[_idx].join()
        assert _node.status == NodeStatus.RX

def _make_rx_nodes_stop_listening(rx_nodes):
    threads = {}
    for _idx, _node in enumerate(rx_nodes):
        thread = threading.Thread(target=_node.stop_rx)
        thread.start()
        threads[_idx] = thread
    for _idx, _node in enumerate(rx_nodes):
        threads[_idx].join()
        assert _node.status == NodeStatus.IDLE

def _save_data(outfile, tx_node, rx_nodes, start_time, trans_ctr, channel):
    outfile.write_data('tx',
                       {'datetime': start_time.isoformat(),
                        'trans_ctr': trans_ctr,
                        'channel': channel,
                        'mac_addr': str(tx_node.mac_addr)})
    for rx_node in rx_nodes:
        rx_data = {'mac_addr': str(rx_node.mac_addr),
                   'rssi_records': rx_node.rssi_records}
        outfile.write_data('rx', rx_data)

def  _end_of_measurement(pbar, trans_ctr, channel, node_idx, num_nodes):
    logging.info('End of measurement - '
                 + 'trans_ctr: {0}, '.format(trans_ctr)
                 + 'channel: {0}, '.format(channel)
                 + 'tx_node: {0}/{1}'.format(node_idx+1,
                                             num_nodes))
    pbar.update()

def main():
    _init_logger()

    args = _parse_args()
    config = _read_config(args.config)
    outfile = Outfile(args.out_file_path, config, args.overwrite_out_file)

    logging.info('Start Mercator at '
                 + '"{0}" platform'.format(config['platform']['name']))

    platform = _setup_platform(config['platform'], args)
    nodes = platform.setup_measurement(config['measurement'])

    channels = config['measurement']['channels']
    num_transactions = config['measurement']['num_transactions_num']
    _run_transactions(num_transactions, channels, nodes, outfile)

if __name__ == '__main__':
    main()
