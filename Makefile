# ******************************* Makefile **********************************
#  Course: Soft Computing (SFC) - FIT BUT
#  Project name: Shortest path search simulation using ACO
#  Author: Beranek Tomas (xberan46)
#  Date: 26.11.2022
#  Up2date sources: https://github.com/TomasBeranek/but-sfc-project
# ***************************************************************************

ANTS_NUM=50
GRAPH_FILE=graphs/graph3.json

MERLIN_ANTS_NUM=5

run-merlin:
	python3.6 src/aco.py --merlin -a $(MERLIN_ANTS_NUM) -g $(GRAPH_FILE)

run:
	python3.8 src/aco.py -a $(ANTS_NUM) -g $(GRAPH_FILE)

install:
	python3.8 -m pip install -r requirements.txt

zip:
	zip -9 -r xberan46.zip doc-src/ documentation-cz.pdf graphs/ gui_images/ Makefile README.md requirements.txt src/

clean:
	rm -f xberan46.zip
