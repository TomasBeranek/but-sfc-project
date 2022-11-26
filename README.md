# Shortest Path Search Simulation Using ACO Algorithm
The application simulate and visualize a shortest path search in given graph using [ACO](https://en.wikipedia.org/wiki/Ant_colony_optimization_algorithms) (Ant Colony Optimization) algorithm. The project is created for the [Soft Computing](https://www.fit.vut.cz/study/course/SFC/.en) course at [FIT BUT](https://www.fit.vut.cz/.en).

## How to Install

#### Ubuntu
To install the dependencies, run:

```
make install
```

Alternatively, you can use ```requirements.txt``` as follows:

```
python3.8 -m pip install -r requirements.txt
```

#### Merlin Server
All packages are already installed on the Merlin server, but it is necessary to run the program with python3.6.

## How to Run
#### Ubuntu
To use a Makefile with predefined parameter values, run:

```
make run
```

Or you can define the parameters yourself as follows:

```
python3.8 src/aco.py -a ANTS_NUM -g GRAPH_FILE
```

For more information, run:

```
python3.8 src/aco.py --help
```

#### Merlin Server
Again, to use a Makefile with predefined parameter values, run:

```
make run-merlin
```

When running on the Merlin server, you must add the ```--merlin``` option as follows:

```
python3.6 src/aco.py --merlin -a ANTS_NUM -g GRAPH_FILE
```

The ```--merlin``` option will disable tooltips (showing node IDs) because the ```Pmw``` package is missing on Merlin.

## Input
The application input is the number of ants and a graph in JSON format. Examples of graphs are in the ```graphs/``` directory.

## License
MIT License
