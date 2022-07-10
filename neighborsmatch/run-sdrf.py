from attrdict import AttrDict
from experiment import Experiment
import torch
import numpy as np
import task
import rewiring
import rewiring_rlef
from torch.nn.functional import one_hot
from torch_geometric.utils import to_networkx, from_networkx



G = task.path_of_cliques(3, 10)
vertices_to_label = list(range(0, 9))


iteration_counts = list(range(50, 1050, 50))

def produce_rewired_dataset(dataset_source, num_iterations):
    dset = dataset_source
    n = len(dset)
    for i in range(n):
        print(i)
        edge_index = np.array(dset[i].edge_index)
        G = to_networkx(dset[i], to_undirected=True)
        for j in range(num_iterations):
            rewiring.sdrf(G)
        dset[i].edge_index = from_networkx(G).edge_index
    return dset

def log_to_file(message, filename="neighborsmatch_results.txt"):
    print(message)
    file = open(filename, "a")
    file.write(message)
    file.close()

for iteration_count in iteration_counts:
    nmatch = task.create_neighborsmatch_dataset(G, 29, vertices_to_label, 10000)
    nmatch = produce_rewired_dataset(nmatch, num_iterations=iteration_count)
    hyperparams = {
    "neighborsmatch": AttrDict({"dropout": 0.0, "num_layers": 6, "hidden_dim": 256, "learning_rate": 0.001})
    }

    num_trials=1
    name = "neighborsmatch"
    accuracies = []
    print(f"TESTING: {name} (SDRF), ITERATION COUNT: {iteration_count}")
    for trial in range(num_trials):

        args = AttrDict({"dataset": nmatch, "layer_type": "GAT", "display": True})
        args += hyperparams["neighborsmatch"]
        train_acc, validation_acc, test_acc = Experiment(args).run()
        accuracies.append(train_acc.item())
        torch.cuda.empty_cache()
        log_to_file(f"RESULTS FOR {name} (SDRF), ITERATION COUNT: {iteration_count}:\n")
        log_to_file(f"average acc: {np.mean(accuracies)}\n")
        log_to_file(f"plus/minus:  {2 * np.std(accuracies)/(num_trials ** 0.5)}\n\n")
    