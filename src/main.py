#!/usr/bin/env python3.9

import argparse
import json
import tkinter as tk
import os
import sys
import Pmw
import random
import math
import numpy as np
from PIL import Image, ImageTk

# ant update their position every TIMER ms
TIMER = 25

# speed of an ant
ANT_SPEED = 10

# root of the app
ROOT = None

# main frame
FRAME = None

# ACO settings
DEFAULT_PHEROMONE_LEVEL = 0.01
MIN_PHEROMONE_LEVEL = DEFAULT_PHEROMONE_LEVEL
MAX_PHEROMONE_LEVEL = 1
EVAPORATION_PER_SECOND = 0.98 # per second
ITERATION_CNT = 1
ALPHA = 1
BETA = 1


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
    global DEFAULT_PHEROMONE_LEVEL

    nodes = {}
    edges = {}

    for node in graph["nodes"]:
        node["adjacent_nodes"] = set()
        nodes[node["id"]] = node

    for edge in graph["edges"]:
        from_node_id = edge["from_node_id"]
        to_node_id = edge["to_node_id"]
        edges[f"{from_node_id} {to_node_id}"] = edge
        edges[f"{to_node_id} {from_node_id}"] = edge

        # add information about adjacency
        nodes[from_node_id]["adjacent_nodes"].add(to_node_id)
        nodes[to_node_id]["adjacent_nodes"].add(from_node_id)

        # set length (weight) and pheromone level
        x = nodes[from_node_id]['x'] - nodes[to_node_id]['x']
        y = nodes[from_node_id]['y'] - nodes[to_node_id]['y']
        edge['length'] = math.sqrt(x**2 + y**2)
        edge['pheromone_level'] = DEFAULT_PHEROMONE_LEVEL

    # update old graph
    graph["nodes"] = nodes
    graph["edges"] = edges

    return graph


def create_circle(x, y, r, canvas):
    return canvas.create_oval(x - r, y - r, x + r, y + r, fill='#3e3e3e', outline='#2c2c2c', width=5, activefill="#4e4e4e")


def evaporate_pheromone_trails(graph):
    global ITERATION_CNT, TIMER
    # evaporate hormones every second by given amount
    if ITERATION_CNT % (1000 // TIMER) == 0:
        for edge in graph['edges'].values():
            edge['pheromone_level'] *= EVAPORATION_PER_SECOND
            edge['pheromone_level'] = max(edge['pheromone_level'], MIN_PHEROMONE_LEVEL)

    ITERATION_CNT += 1


def get_next_node(curr_node, edges, last_node_id):
    global ALPHA, BETA
    adjacent_node_ids = curr_node['adjacent_nodes']
    curr_node_id = curr_node['id']

    coefs = {}
    coef_sum = 0

    for node_id in adjacent_node_ids:
        if last_node_id != node_id:
            edge_id = f'{node_id} {curr_node_id}'
            edge_coef = edges[edge_id]['pheromone_level']**ALPHA * (1 / edges[edge_id]['length'])**BETA # Qij
            coefs[node_id] = edge_coef
            coef_sum += edge_coef

    threshold = random.uniform(0, 1)

    curr_threshold = 0

    for node_id, edge_coef in coefs.items():
        curr_threshold += edge_coef / coef_sum

        if threshold <= curr_threshold:
            return node_id


def update_path_color(canvas, line_id, pheromone_level):
    hex_color = canvas.itemcget(line_id, 'fill')
    hex_red = hex_color[1:3]
    red = int(hex_red, 16)
    DEFAULT_RED = 44
    new_red = min(255, DEFAULT_RED + pheromone_level)
    hex_new_red = "%0.2X" % int(new_red)
    # set new color
    canvas.itemconfigure(line_id, fill='#' + hex_new_red + '2c2c')


def ant_timer_event():
    global TIMER, ANT_SPEED, ROOT, FRAME, ITERATION_CNT, EVAPORATION_PER_SECOND, MIN_PHEROMONE_LEVEL
    canvas = FRAME.canvas
    ants = FRAME.ants

    for ant_id in canvas.find_withtag("ant"):
        x, y = canvas.coords(ant_id)
        ant = ants[ant_id]

        # if ant arrived to the next node
        if x == ant.next_node['x'] and y == ant.next_node['y']:
            # add pheromones to the last edge
            if ant.last_edge_id:
                if ant.has_food:
                    ant.graph['edges'][ant.last_edge_id]['pheromone_level'] += 100

                # update color of given path based on pheromone level
                line_id = ant.graph['edges'][ant.last_edge_id]['line_object_id']
                pheromone_level = ant.graph['edges'][ant.last_edge_id]['pheromone_level']
                update_path_color(canvas, line_id, pheromone_level)

            # calculate the new next node
            new_next_node_id = get_next_node(ant.next_node, ant.graph['edges'], ant.last_node_id)
            new_next_node = ant.graph['nodes'][new_next_node_id]

            # calculate rotation of ant image
            path_vector_x = new_next_node['x'] - ant.next_node['x']
            # flip Y axis, since positive y is at the bottom in windows
            path_vector_y = -1 *(new_next_node['y'] - ant.next_node['y'])

            # calculate angle in degrees of edge from next_node to new_next_node
            path_vector = complex(path_vector_x, path_vector_y)
            angle = np.angle(path_vector, deg=True)

            # correction -- in numpy 0.0 angle points up, we want 0.0 point right
            angle = angle - 90

            # save current path/edge
            next_node_id = ant.next_node['id']
            ant.last_edge_id = f"{next_node_id} {new_next_node_id}"

            # update next node
            ant.last_node_id = ant.next_node['id']
            ant.next_node = new_next_node

            # rotate ant towards next node
            print(ant.has_food)
            if ant.has_food:
                ant_img_tk = FRAME.ant_food_img.rotate(angle)
            else:
                ant_img_tk = FRAME.ant_img.rotate(angle)

            ant.ant_img = ImageTk.PhotoImage(ant_img_tk)
            canvas.itemconfig(ant_id,image=ant.ant_img)

            if ant.last_node_id == ant.graph['end_node_id']:
                ant.has_food = True

            if ant.last_node_id == ant.graph['start_node_id']:
                ant.has_food = False
        else:
            # get remaining distance to next node
            x_distance = ant.next_node['x'] - x
            y_distance = ant.next_node['y'] - y

            # distance
            distance = math.sqrt(x_distance**2 + y_distance**2)

            # number of moves the ant need to take to arrive to the next node
            steps = math.ceil(distance / ANT_SPEED)

            # make one step
            x_move_ammount = math.ceil(x_distance / steps)
            y_move_ammount = math.ceil(y_distance / steps)
            canvas.move(ant_id, x_move_ammount, y_move_ammount)

    # evaporate some portion of pheromone on all paths
    evaporate_pheromone_trails(FRAME.graph)

    ROOT.after(TIMER, ant_timer_event)


class Ant:
    def __init__(self, id, graph):
        self.id = id
        self.graph = graph
        start_node_id = graph['start_node_id']
        self.next_node = graph['nodes'][start_node_id]
        self.running = False
        self.last_edge_id = None
        self.has_food = False
        self.last_node_id = None


class ACOFrame(tk.Frame):
    def __init__(self, parent, graph, ants):
        tk.Frame.__init__(self, parent)

        # create canvas into which a graph will be displayed
        self.canvas = tk.Canvas(self, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        # for tooltips
        self.balloon = Pmw.Balloon()

        # prepare to save ants
        self.ants = {}

        # save ant with food image for later use
        ant_food_img_path = os.path.dirname(os.path.realpath(__file__)) + '/../gui_images/ant_image_low_res_with_food.png'
        self.ant_food_img = Image.open(ant_food_img_path)

        # display ants
        ant_img_path = os.path.dirname(os.path.realpath(__file__)) + '/../gui_images/ant_image_low_res.png'
        self.ant_img = Image.open(ant_img_path)
        ant_img_tk = ImageTk.PhotoImage(self.ant_img)

        start_node_x = graph['nodes'][graph['start_node_id']]['x']
        start_node_y = graph['nodes'][graph['start_node_id']]['y']

        for i in range(ants):
            id = self.canvas.create_image(start_node_x, start_node_y, image=ant_img_tk, tags='ant')
            ant = Ant(id, graph)
            ant.ant_img = ant_img_tk
            self.ants[id] = ant

        # display graph over ants
        self.draw_edges(graph)
        self.draw_nodes(graph["nodes"])

        self.graph = graph


    def draw_nodes(self, nodes):
        for id, node in nodes.items():
            circle = create_circle(node['x'], node['y'], 25, self.canvas)
            self.balloon.tagbind(self.canvas, circle, f'ID: {id}')

    def draw_edges(self, graph):
        for edge in graph['edges'].values():
            start = edge["from_node_id"]
            end = edge["to_node_id"]

            x1 = graph['nodes'][start]['x']
            y1 = graph['nodes'][start]['y']
            x2 = graph['nodes'][end]['x']
            y2 = graph['nodes'][end]['y']

            line = self.canvas.create_line(x1, y1, x2, y2, fill='#2c2c2c', width=7)
            edge['line_object_id'] = line
            # self.balloon.tagbind(self.canvas, line, f'Pheromone level: {...}')


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
