ANTS_NUM=50
GRAPH_FILE=graphs/graph3.json

run:
	python3 src/main.py -a $(ANTS_NUM) -g $(GRAPH_FILE)
