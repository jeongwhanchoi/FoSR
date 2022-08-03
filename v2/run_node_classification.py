from attrdict import AttrDict
from torch_geometric.datasets import WebKB, WikipediaNetwork, Actor, Planetoid
from torch_geometric.utils import to_networkx, from_networkx
from experiments.node_classification import Experiment
import torch
import numpy as np
import pandas as pd
from hyperparams import get_args_from_input
from preprocessing import rewiring, sdrf, robustness

cornell = WebKB(root="data", name="Cornell")
wisconsin = WebKB(root="data", name="Wisconsin")
texas = WebKB(root="data", name="Texas")
chameleon = WikipediaNetwork(root="data", name="chameleon")
squirrel = WikipediaNetwork(root="data", name="squirrel")
actor = Actor(root="data")
cora = Planetoid(root="data", name="cora")
citeseer = Planetoid(root="data", name="citeseer")
pubmed = Planetoid(root="data", name="pubmed")
datasets = {"cornell": cornell, "wisconsin": wisconsin, "texas": texas, "chameleon": chameleon, "squirrel": squirrel, "actor": actor, "cora": cora, "citeseer": citeseer, "pubmed": pubmed}

def log_to_file(message, filename="results/node_classification_results.txt"):
    print(message)
    file = open(filename, "a")
    file.write(message)
    file.close()

default_args = AttrDict({
    "dropout": 0.5,
    "num_layers": 3,
    "hidden_dim": 128,
    "learning_rate": 1e-3,
    "layer_type": "R-GCN",
    "display": False,
    "num_trials": 30,
    "eval_every": 1,
    "rewiring": None,
    "num_iterations": 15
    })

def run(args=AttrDict({})):
    results = []
    args = default_args + args
    args += get_args_from_input()
    for key in datasets:
        accuracies = []
        print(f"TESTING: {key} ({default_args.rewiring})")
        dataset = datasets[key]
        dataset.data.edge_index, dataset.data.num_nodes = rewiring.to_undirected(dataset.data)
        if args.rewiring == "edge_rewire":
            G = to_networkx(dataset.data, to_undirected=True)
            robustness.edge_rewire(G, num_iterations=args.num_iterations)
            dataset.data.edge_index = from_networkx(G).edge_index
        for trial in range(args.num_trials):
            print(f"TRIAL {trial+1}")
            train_acc, validation_acc, test_acc = Experiment(args=args, dataset=dataset).run()
            result_dict = {"train_acc": train_acc, "validation_acc": validation_acc, "test_acc": test_acc, "dataset": key}
            results.append(args + result_dict)
            accuracies.append(test_acc)

        log_to_file(f"RESULTS FOR {key} ({default_args.rewiring}):\n")
        log_to_file(f"average acc: {np.mean(accuracies)}\n")
        log_to_file(f"plus/minus:  {2 * np.std(accuracies)/(args.num_trials ** 0.5)}\n\n")
        results_df = pd.DataFrame(results)
        results_df.to_csv('results/node_classification_results.csv', mode='a')

if __name__ == '__main__':
    run()