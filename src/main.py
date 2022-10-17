#!/usr/bin/env python3.9

import argparse
import json
import tkinter as tk
import os
import sys
import Pmw
from dataclasses import dataclass

# ant update their position every TIMER ms
TIMER = 100

# root of the app
ROOT = None

# main frame
FRAME = None


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def init_parser():
    parser = argparse.ArgumentParser(description='The application simulate and visualize a shortest path search in given graph using ACO (Ant Colony Optimization) algorithm.')

    parser.add_argument('-g', '--graph-file', required=True, type=str, help='input JSON file with a graph definition')
    parser.add_argument('-a', '--ants', required=True, type=int, help='number of ants')

    return parser


def check_graph_correctness(graph):
    if graph["start_node_id"] not in graph["nodes"].keys():
        print(f'{bcolors.FAIL}ERROR{bcolors.ENDC}: Start node has invalid ID!', file=sys.stderr)
        sys.exit(1)

    if graph["end_node_id"] not in graph["nodes"].keys():
        print(f'{bcolors.FAIL}ERROR{bcolors.ENDC}: End node has invalid ID!', file=sys.stderr)
        sys.exit(1)

    for edge_id in graph["edges"]:
        node1 = int(edge_id.split(' ')[0])
        node2 = int(edge_id.split(' ')[1])

        if node1 == node2:
            print(f'{bcolors.FAIL}ERROR{bcolors.ENDC}: Edges cannot start and end in the same node!', file=sys.stderr)
            sys.exit(1)

        if node1 not in graph["nodes"].keys():
            print(f'{bcolors.FAIL}ERROR{bcolors.ENDC}: Edge is connected to a non-existing node (ID: {node1})!', file=sys.stderr)
            sys.exit(1)

        if node2 not in graph["nodes"].keys():
            print(f'{bcolors.FAIL}ERROR{bcolors.ENDC}: Edge is connected to a non-existing node (ID: {node2})!', file=sys.stderr)
            sys.exit(1)

    return


def restructure_graph(graph):
    nodes = {}
    edges = {}

    for node in graph["nodes"]:
        nodes[node["id"]] = node

    for edge in graph["edges"]:
        from_node = edge["from_node_id"]
        to_node = edge["to_node_id"]
        edges[f"{from_node} {to_node}"] = edge
        edges[f"{to_node} {from_node}"] = edge

    # update old graph
    graph["nodes"] = nodes
    graph["edges"] = edges

    return graph


def create_circle(x, y, r, canvas):
    return canvas.create_oval(x - r, y - r, x + r, y + r, fill='#3e3e3e', outline='#2c2c2c', width=5, activefill="#4e4e4e")


def ant_timer_event():
    global TIMER, ROOT, FRAME
    canvas = FRAME.canvas
    ants = FRAME.ants

    for id in canvas.find_withtag("ant"):
        x, y = canvas.coords(id)
        canvas.coords(id, (x + 1, y + 1))

    ROOT.after(TIMER, ant_timer_event)



@dataclass
class Ant:
    id: int
    x: int
    y: int
    angle: int = 0
    next_node: int = None


class ACOFrame(tk.Frame):
    def __init__(self, parent, graph, ants):
        tk.Frame.__init__(self, parent)

        # create canvas into which a graph will be displayed
        self.canvas = tk.Canvas(self, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        # for tooltips
        self.balloon = Pmw.Balloon()

        # display graph
        self.draw_edges(graph)
        self.draw_nodes(graph["nodes"])

        # prepare to save ants
        self.ants = {}

        # display ants
        ant_img_path = os.path.dirname(os.path.realpath(__file__)) + '/../gui_images/ant_image_low_res.png'
        self.ant_img = tk.PhotoImage(file=ant_img_path)
        start_node_x = graph['nodes'][graph['start_node_id']]['x']
        start_node_y = graph['nodes'][graph['start_node_id']]['y']

        for i in range(ants):
            id = self.canvas.create_image(start_node_x, start_node_y, image=self.ant_img, tags='ant')
            self.ants[id] = Ant(start_node_x, start_node_y, id)


    def draw_nodes(self, nodes):
        for id, node in nodes.items():
            circle = create_circle(node['x'], node['y'], 25, self.canvas)
            self.balloon.tagbind(self.canvas, circle, f'ID: {id}')

    def draw_edges(self, graph):
        for edge_id in graph['edges'].values():
            start = edge_id["from_node_id"]
            end = edge_id["to_node_id"]

            x1 = graph['nodes'][start]['x']
            y1 = graph['nodes'][start]['y']
            x2 = graph['nodes'][end]['x']
            y2 = graph['nodes'][end]['y']

            line = self.canvas.create_line(x1, y1, x2, y2, fill='#2c2c2c', width=7, activefill="#4e4e4e")
            self.balloon.tagbind(self.canvas, line, f'Pheromone level: {...}')


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()

    # load graph in JSON format
    with open(args.graph_file, 'r') as f:
        graph = json.load(f)

    # restructure graph into faster structure
    graph = restructure_graph(graph)

    # check graph semantically
    check_graph_correctness(graph)

    root = tk.Tk()
    ROOT = root
    Pmw.initialise(root)

    # set window size
    root.geometry('1300x700')
    root.resizable(True, True)

    # set title
    root.title('ACO simulation')

    # set icon
    img_path = os.path.dirname(os.path.realpath(__file__)) + '/../gui_images/ant_icon.png'
    img = tk.Image("photo", file=img_path)
    root.tk.call('wm', 'iconphoto', root._w,img)

    # start window loop
    FRAME = ACOFrame(root, graph, args.ants)
    FRAME.pack(fill="both", expand=True)
    root.after(TIMER, ant_timer_event)
    root.mainloop()
