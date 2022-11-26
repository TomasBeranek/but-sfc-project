ANTS_NUM=50
GRAPH_FILE=graphs/graph3.json

run-merlin:
	python3.6 src/main.py --merlin -a $(ANTS_NUM) -g $(GRAPH_FILE)

run:
	python3.8 src/main.py -a $(ANTS_NUM) -g $(GRAPH_FILE)

install:
	python3.8 -m pip install -r requirements.txt
