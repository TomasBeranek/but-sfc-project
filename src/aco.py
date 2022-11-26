#!/usr/bin/env python3.8

# ******************************* aco.py ************************************
#  Course: Soft Computing (SFC) - FIT BUT
#  Project name: Shortest path search simulation using ACO
#  Author: Beranek Tomas (xberan46)
#  Date: 26.11.2022
#  Up2date sources: https://github.com/TomasBeranek/but-sfc-project
# ***************************************************************************


import argparse
import json
import tkinter as tk
import tkinter.ttk as ttk
import os
import sys
import random
import math
import numpy as np
from PIL import Image, ImageTk


# just because some dependencies are missing on Merlin server
RUNNING_ON_MERLIN = False

# ant update their position every TIMER ms
TIMER = 25

# root of the app
ROOT = None

# main frame
FRAME = None

# ACO settings
MIN_PHEROMONE_LEVEL = 0.001
MAX_PHEROMONE_LEVEL = 1
ITERATION_CNT = 1
BEST_FOUND_PATH_LEN = sys.maxsize
BEST_FOUND_PATH = []
MAX_EDGE_LEN = -1
HIGHEST_PHEROMONE_LEVEL = MIN_PHEROMONE_LEVEL

# GUI controls values
ALPHA = None
BETA = None
ALPHA_LABEL = None
BETA_LABEL = None
INCREMENT_TYPE = None
EVAPORATION_PER_SECOND = None
EVAPORATION_LABEL = None
SPEED_LABEL = None
ANT_SPEED = None


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
    parser.add_argument('--merlin', action='store_true', help='if program should run on Merlin server')

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
    global MIN_PHEROMONE_LEVEL, MAX_EDGE_LEN

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
        edge['pheromone_level'] = MIN_PHEROMONE_LEVEL

    MAX_EDGE_LEN = max([edge['length'] for edge in edges.values()])

    # update old graph
    graph["nodes"] = nodes
    graph["edges"] = edges

    return graph


def create_circle(x, y, r, canvas, fill='#3e3e3e', activefill='#4e4e4e'):
    return canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline='#2c2c2c', width=5, activefill=activefill)

def calculate_alpha_beta(x):
    # x can alpha or beta, but they are calculated in a same way from slider value
    return (x - 100) / 100

def evaporate_pheromone_trails(canvas, graph):
    global ITERATION_CNT, TIMER
    # evaporate hormones every second by given amount
    if ITERATION_CNT % (1000 // TIMER) == 0:
        for edge in graph['edges'].values():
            edge['pheromone_level'] *= EVAPORATION_PER_SECOND.get()/100
            edge['pheromone_level'] = max(edge['pheromone_level'], MIN_PHEROMONE_LEVEL)
    ITERATION_CNT += 1


def get_next_node(curr_node, edges, last_node_id, start_node_id):
    global ALPHA, BETA
    adjacent_node_ids = curr_node['adjacent_nodes']
    curr_node_id = curr_node['id']

    if len(adjacent_node_ids) == 1:
        return next(iter(adjacent_node_ids))

    coefs = {}
    coef_sum = 0

    for node_id in adjacent_node_ids:
        if (curr_node_id == start_node_id) or (last_node_id != node_id):
            edge_id = f'{node_id} {curr_node_id}'
            alpha = calculate_alpha_beta(ALPHA.get())
            beta = calculate_alpha_beta(BETA.get())
            edge_coef = edges[edge_id]['pheromone_level']**alpha * (1 / edges[edge_id]['length'])**beta # Qij
            coefs[node_id] = edge_coef
            coef_sum += edge_coef

    threshold = random.uniform(0, 1)

    curr_threshold = 0

    for node_id, edge_coef in coefs.items():
        curr_threshold += edge_coef / coef_sum

        if threshold <= curr_threshold:
            return node_id


def update_path_color(canvas, line_id, pheromone_level):
    global HIGHEST_PHEROMONE_LEVEL, MIN_PHEROMONE_LEVEL

    # all the edges are pheromone free
    if HIGHEST_PHEROMONE_LEVEL == MIN_PHEROMONE_LEVEL:
        return

    pheromone_range = HIGHEST_PHEROMONE_LEVEL - MIN_PHEROMONE_LEVEL
    # in range <0,1>
    new_red_value = (pheromone_level - MIN_PHEROMONE_LEVEL)/pheromone_range
    # in range <0,255>
    new_red_value *= 255
    hex_new_red = "%0.2X" % int(new_red_value)
    # set new color
    canvas.itemconfigure(line_id, fill='#' + hex_new_red + '2c2c')


def add_pheromones_to_edge(canvas, ant):
    ant.graph['edges'][ant.last_edge_id]['pheromone_level'] += ant.pheromone_increment


def calculate_image_angle(new_next_node, ant):
    path_vector_x = new_next_node['x'] - ant.next_node['x']
    # flip Y axis, since positive y is at the bottom in windows
    path_vector_y = -1 *(new_next_node['y'] - ant.next_node['y'])

    # calculate angle in degrees of edge from next_node to new_next_node
    path_vector = complex(path_vector_x, path_vector_y)
    angle = np.angle(path_vector, deg=True)

    # correction -- in numpy 0.0 angle points up, we want 0.0 point right
    return angle - 90


def update_ant_image(canvas, ant, angle, ant_id):
    global FRAME

    if ant.has_food:
        ant_img_tk = FRAME.ant_food_img.rotate(angle)
    else:
        ant_img_tk = FRAME.ant_img.rotate(angle)

    ant.ant_img = ImageTk.PhotoImage(ant_img_tk)
    canvas.itemconfig(ant_id, image=ant.ant_img)


def get_move_ammount(ant, x, y):
    global ANT_SPEED

    if ANT_SPEED.get() == 0:
        return 0, 0

    # get remaining distance to next node
    x_distance = ant.next_node['x'] - x
    y_distance = ant.next_node['y'] - y

    # distance
    distance = math.sqrt(x_distance**2 + y_distance**2)

    # number of moves the ant need to take to arrive to the next node
    steps = math.ceil(distance / ANT_SPEED.get())

    # calculate ammount of pixels for ant's move
    x_move_ammount = x_distance / steps
    y_move_ammount = y_distance / steps

    return x_move_ammount, y_move_ammount


def set_food_information(ant):
    if ant.next_node['id'] == ant.graph['end_node_id']:
        if not ant.has_food:
            ant.recently_acquired_food = True
        ant.has_food = True
    elif ant.next_node['id'] == ant.graph['start_node_id']:
        if ant.has_food:
            ant.recently_deposited_food = True
        ant.has_food = False


def save_node_to_path(ant):
    # check if there is a loop in the path
    if ant.next_node['id'] in ant.path:
        start_of_loop_index = ant.path.index(ant.next_node['id'])
        # remove whole loop
        ant.path = ant.path[:start_of_loop_index]
    ant.path.append(ant.next_node['id'])


# function runs only immediately after picking up food
def calculate_pheromone_increments(canvas, ant):
    global BEST_FOUND_PATH_LEN, INCREMENT_TYPE, MAX_EDGE_LEN, BEST_FOUND_PATH

    path = ant.path.copy()
    path.append(ant.graph['end_node_id'])

    edges = []
    prev_node_id = path[0]

    for node_id in path[1:]:
        edges.append(f'{prev_node_id} {node_id}')
        prev_node_id = node_id

    # get lengths for each edge
    path_lens = [ant.graph['edges'][edge_id]['length'] for edge_id in edges]
    entire_length = sum(path_lens)

    if entire_length < BEST_FOUND_PATH_LEN:
        BEST_FOUND_PATH_LEN = entire_length
        BEST_FOUND_PATH = path
        print(f'New best path with length {BEST_FOUND_PATH_LEN}: ', end='')
        print(BEST_FOUND_PATH)

        # clear all highlighting
        for edge in ant.graph['edges'].values():
            line_border_id = edge['line_border_object_id']
            canvas.itemconfigure(line_border_id, fill='white')

        # highlight the best path
        for edge_id in edges:
            line_border_id = ant.graph['edges'][edge_id]['line_border_object_id']
            canvas.itemconfigure(line_border_id, fill='#2ba8fc')


    if INCREMENT_TYPE.get() == '1 (constant)':
        ant.pheromone_increment = 1
    elif INCREMENT_TYPE.get() == '1/P (P - cost of path)':
        ant.pheromone_increment = 1/entire_length
    elif INCREMENT_TYPE.get() == 'C/P (C - max edge cost)':
        ant.pheromone_increment = MAX_EDGE_LEN/entire_length
    elif INCREMENT_TYPE.get() == 'Pb/P (Pb - best path cost)':
        ant.pheromone_increment = BEST_FOUND_PATH_LEN/entire_length


def ant_timer_event():
    global TIMER, ANT_SPEED, ROOT, FRAME, ITERATION_CNT, EVAPORATION_PER_SECOND, MIN_PHEROMONE_LEVEL, HIGHEST_PHEROMONE_LEVEL
    canvas = FRAME.canvas
    ants = FRAME.ants

    for ant_id in canvas.find_withtag("ant"):
        x, y = canvas.coords(ant_id)
        ant = ants[ant_id]

        if ant.start_delay:
            ant.start_delay = False
            break

        # if ant arrived to the next node
        if x == ant.next_node['x'] and y == ant.next_node['y']:
            # determine whether ant carries food
            set_food_information(ant)

            if ant.has_food and ant.path:
                # ant is coming back to start on given path
                # add pheromones, but don't add them to edge before end
                if not ant.recently_acquired_food:
                    add_pheromones_to_edge(canvas, ant)

                if ant.recently_acquired_food:
                    # calculate pheromone increments for each edge
                    calculate_pheromone_increments(canvas, ant)

                ant.recently_acquired_food = False

                # ant is going in a reversed path
                new_next_node_id = ant.path.pop()
            else:
                # ant is looking for food
                # save last node to ant's path
                save_node_to_path(ant)

                # add pheromones to the last edge before ant deposited food
                if ant.recently_deposited_food:
                    add_pheromones_to_edge(canvas, ant)
                    ant.recently_deposited_food = False

                # calculate the new next node
                new_next_node_id = get_next_node(ant.next_node, ant.graph['edges'], ant.last_node_id, ant.graph['start_node_id'])

            new_next_node = ant.graph['nodes'][new_next_node_id]

            # calculate new rotation of ant image
            angle = calculate_image_angle(new_next_node, ant)

            # save current path/edge
            ant.last_edge_id = f"{ant.next_node['id']} {new_next_node_id}"

            # update next node
            ant.last_node_id = ant.next_node['id']
            ant.next_node = new_next_node

            # rotate ant towards next node
            update_ant_image(canvas, ant, angle, ant_id)
        else:
            # make one step
            x_move_ammount, y_move_ammount = get_move_ammount(ant, x, y)
            canvas.move(ant_id, x_move_ammount, y_move_ammount)

    # evaporate some portion of pheromone on all paths
    evaporate_pheromone_trails(canvas, FRAME.graph)

    # get highest pheromone level in graph
    HIGHEST_PHEROMONE_LEVEL = max(edge['pheromone_level'] for edge in FRAME.graph['edges'].values())

    # update color of all paths
    for edge in FRAME.graph['edges'].values():
        line_id = edge['line_object_id']
        pheromone_level = edge['pheromone_level']
        update_path_color(canvas, line_id, pheromone_level)

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
        self.last_node_id = graph['start_node_id']
        self.path = []
        self.recently_deposited_food = False
        self.pheromone_increment = None
        self.start_delay = True


class ACOFrame(tk.Frame):
    def __init__(self, parent, graph, ants):
        tk.Frame.__init__(self, parent)

        # create canvas into which a graph will be displayed
        self.canvas = tk.Canvas(self, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        # python3.6 on Merlin does not have Pmw
        if not RUNNING_ON_MERLIN:
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

        # draw edges borders before ants, so that ants are in higher canvas level
        self.draw_edges_border(graph)

        for i in range(ants):
            id = self.canvas.create_image(start_node_x, start_node_y, image=ant_img_tk, tags='ant')
            ant = Ant(id, graph)
            ant.ant_img = ant_img_tk
            self.ants[id] = ant

        # display graph over ants
        self.draw_edges(graph)
        self.draw_nodes(graph)

        self.graph = graph


    def draw_nodes(self, graph):
        nodes = graph['nodes']

        for id, node in nodes.items():
            if id == graph['start_node_id']:
                circle = create_circle(node['x'], node['y'], 25, self.canvas, fill='green', activefill='darkgreen')
                # python3.6 on Merlin does not have Pmw
                if not RUNNING_ON_MERLIN:
                    self.balloon.tagbind(self.canvas, circle, f'START ID: {id}')
            elif id == graph['end_node_id']:
                circle = create_circle(node['x'], node['y'], 25, self.canvas, fill='yellow', activefill='orange')
                # python3.6 on Merlin does not have Pmw
                if not RUNNING_ON_MERLIN:
                    self.balloon.tagbind(self.canvas, circle, f'END ID: {id}')
            else:
                circle = create_circle(node['x'], node['y'], 25, self.canvas)
                # python3.6 on Merlin does not have Pmw
                if not RUNNING_ON_MERLIN:
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

    def draw_edges_border(self, graph):
        for edge in graph['edges'].values():
            start = edge["from_node_id"]
            end = edge["to_node_id"]

            x1 = graph['nodes'][start]['x']
            y1 = graph['nodes'][start]['y']
            x2 = graph['nodes'][end]['x']
            y2 = graph['nodes'][end]['y']

            line_border = self.canvas.create_line(x1, y1, x2, y2, fill='white', width=13)
            edge['line_border_object_id'] = line_border


def create_increment_type_dropdown(root):
    global INCREMENT_TYPE

    # dropdown menu options
    increment_options = [   "1 (constant)",
                            "1/P (P - cost of path)",
                            "C/P (C - max edge cost)",
                            "Pb/P (Pb - best path cost)" ]

    # datatype of menu text
    INCREMENT_TYPE = tk.StringVar()

    # create label
    label = tk.Label(root, text="Pheromone increment type", bg="white")
    label.place(x=1095, y=20)

    # create dropdown menu
    drop = ttk.Combobox(root, state="readonly", textvariable=INCREMENT_TYPE, values=increment_options, width=21)
    drop.set(increment_options[0])
    # drop.bind("<<ComboboxSelected>>", lambda e: frame.focus_force())
    drop.place(x=1100, y=50)

    # create style for all comboboxes
    combostyle = ttk.Style()
    combostyle.theme_create('combostyle', parent='alt',
                             settings = {'TCombobox':
                                         {'configure':
                                          {'selectbackground': '#777777',
                                           'fieldbackground': 'white',
                                           'background': 'white'
                                           }}}
                             )
    combostyle.theme_use('combostyle')


def update_evaporation_slider_label(event):
    global EVAPORATION_PER_SECOND, EVAPORATION_LABEL

    val = EVAPORATION_PER_SECOND.get()/100
    EVAPORATION_LABEL.config(text='{0:.2f}'.format(val))


def create_evaporation_slider(root):
    global EVAPORATION_PER_SECOND, EVAPORATION_LABEL

    # create label
    label = tk.Label(root, text="Evaporation coeff (per s)", bg="white")
    label.place(x=1095, y=90)

    # create label with slider value
    EVAPORATION_LABEL = tk.Label(root, text="0.98", bg="white")
    EVAPORATION_LABEL.place(x=1260, y=120)

    EVAPORATION_PER_SECOND = tk.DoubleVar()
    slider = ttk.Scale(root, from_=0, to=100, variable=EVAPORATION_PER_SECOND, length=150, command=update_evaporation_slider_label)
    slider.set(98)
    slider.place(x=1100, y=120)


def update_speed_slider_label(event):
    global ANT_SPEED, SPEED_LABEL

    SPEED_LABEL.config(text=str(ANT_SPEED.get()))


def create_speed_slider(root):
    global ANT_SPEED, SPEED_LABEL

    # create label
    label = tk.Label(root, text="Speed of ants", bg="white")
    label.place(x=1095, y=160)

    # create label with slider value
    SPEED_LABEL = tk.Label(root, text="10", bg="white")
    SPEED_LABEL.place(x=1260, y=190)

    ANT_SPEED = tk.IntVar()
    slider = ttk.Scale(root, from_=0, to=100, variable=ANT_SPEED, length=150, command=update_speed_slider_label)
    slider.set(10)
    slider.place(x=1100, y=190)


def update_alpha_slider_label(event):
    global ALPHA, ALPHA_LABEL

    alpha = calculate_alpha_beta(ALPHA.get())
    ALPHA_LABEL.config(text=('%0.2f' % alpha).rjust(5))


def create_alpha_slider(root):
    global ALPHA, ALPHA_LABEL

    # create label
    label = tk.Label(root, text="Alpha (pheromones)", bg="white")
    label.place(x=1095, y=230)

    # create label with slider value
    ALPHA_LABEL = tk.Label(root, text="1", bg="white")
    ALPHA_LABEL.place(x=1257, y=260)

    ALPHA = tk.IntVar()
    slider = ttk.Scale(root, from_=0, to=200, variable=ALPHA, length=150, command=update_alpha_slider_label)
    slider.set(200)
    slider.place(x=1100, y=260)


def update_beta_slider_label(event):
    global BETA, BETA_LABEL

    beta = calculate_alpha_beta(BETA.get())
    BETA_LABEL.config(text=('%0.2f' % beta).rjust(5))


def create_beta_slider(root):
    global BETA, BETA_LABEL

    # create label
    label = tk.Label(root, text="Beta (edge length)", bg="white")
    label.place(x=1095, y=300)

    # create label with slider value
    BETA_LABEL = tk.Label(root, text="1", bg="white")
    BETA_LABEL.place(x=1257, y=330)

    BETA = tk.IntVar()
    slider = ttk.Scale(root, from_=0, to=200, variable=BETA, length=150, command=update_beta_slider_label)
    slider.set(200)
    slider.place(x=1100, y=330)


def create_controls(root):
    create_increment_type_dropdown(root)
    create_evaporation_slider(root)
    create_speed_slider(root)
    create_alpha_slider(root)
    create_beta_slider(root)


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()

    if args.merlin:
        RUNNING_ON_MERLIN = True

    # load graph in JSON format
    with open(args.graph_file, 'r') as f:
        graph = json.load(f)

    # restructure graph into faster structure
    graph = restructure_graph(graph)

    # check graph semantically
    check_graph_correctness(graph)

    root = tk.Tk()
    ROOT = root

    # python3.6 on Merlin does not have Pmw
    if not RUNNING_ON_MERLIN:
        import Pmw
        Pmw.initialise(root)

    # set window size
    root.geometry('1300x700')
    root.resizable(False, False)

    # set title
    root.title('ACO simulation')

    # set icon
    img_path = os.path.dirname(os.path.realpath(__file__)) + '/../gui_images/ant_icon.png'
    img = ImageTk.PhotoImage(Image.open(img_path))
    root.tk.call('wm', 'iconphoto', root._w,img)

    # create frame with graph
    FRAME = ACOFrame(root, graph, args.ants)
    FRAME.pack(fill="both", expand=True)

    # create GUI controls
    create_controls(root)

    # start window loop
    root.after(TIMER, ant_timer_event)
    root.mainloop()
