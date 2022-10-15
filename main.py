#!/usr/bin/env python3

import argparse
import json


def init_parser():
    parser = argparse.ArgumentParser(description='The application simulate and visualize a shortest path search in given graph using ACO (Ant Colony Optimization) algorithm.')

    parser.add_argument('-g', '--graph-file', required=True, type=str, help='input JSON file with a graph definition')

    return parser


def check_graph_correctness(start_node_id, end_node_id, nodes, edges):
    return

if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()

    # load graph in JSON format
    with open(args.graph_file, 'r') as f:
        graph = json.load(f)

    # load individual graph components from JSON
    start_node_id = graph['start_node_id']
    end_node_id = graph['end_node_id']
    edges = graph['edges']
    nodes = graph['nodes']

    # check graph semantically
    check_graph_correctness(start_node_id, end_node_id, nodes, edges)


    print(graph)
