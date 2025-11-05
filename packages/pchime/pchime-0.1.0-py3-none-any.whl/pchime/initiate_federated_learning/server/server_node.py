from typing import Optional, Tuple
import flwr as fl
import numpy as np
from pathlib import Path




class LoggingStrategy(fl.server.strategy.FedAvg):

    def __init__(self, *args, output_dir: str = ".", **kwargs):
        # ...existing code...
        super().__init__(*args, **kwargs)
        self.output_dir = Path(output_dir)
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: could not create output dir {self.output_dir}: {e}")

    
    def aggregate_fit(
        self, server_round, results, failures,
    ) -> Tuple[Optional[fl.common.Parameters], dict]:

        aggregated_result = super().aggregate_fit(server_round, results, failures)

        # Nothing aggregated → return correct type
        if aggregated_result is None:
            return None, {}

        aggregated_parameters, aggregated_metrics = aggregated_result

        # Enforce non-None for type checker
        if aggregated_parameters is None:
            return None, aggregated_metrics

        nd = fl.common.parameters_to_ndarrays(aggregated_parameters)
        coef = np.asarray(nd[0], dtype=np.float64)
        intercept = np.asarray(nd[1], dtype=np.float64)

        print(f"\n--- Round {server_round} Global Model ---")
        print(coef)
        print(intercept)



        np.savez(f"{self.output_dir}/pchime_fl_round_{server_round}_params.npz", coef=coef, intercept=intercept)

        print(f"\n--- Round {server_round} Training Summary ---")
        for client, fit_res in results:
            print(f"Client {client.cid}: samples={fit_res.num_examples}")

        return aggregated_parameters, aggregated_metrics

    def aggregate_evaluate(
        self, server_round, results, failures
    ) -> Tuple[Optional[float], dict]:

        aggregated_result = super().aggregate_evaluate(server_round, results, failures)

        if aggregated_result is None:
            return None, {}

        loss, metrics = aggregated_result

        print(f"\n--- Round {server_round} Evaluation Summary ---")
        for client, ev in results:
            mse = ev.metrics.get("mse")
            if mse is not None:
                print(f"Client {client.cid}: MSE={mse:.6f}, samples={ev.num_examples}")

        return loss, metrics
    
def establish_server(args):
    output_dir = str(getattr(args, "outDirectory", None)) # or getattr(args, "save_to", None) or getattr(args, "output", ".") or "."
    print(f"output_dir is \n{output_dir}")
    print(f"output_dir is \n{output_dir}")
    print(f"output_dir is \n{output_dir}")
    print(f"output_dir is \n{output_dir}")



    fl.server.start_server(
        server_address=str(args.start),
        config=fl.server.ServerConfig(num_rounds=int(args.federatedRounds)),
        strategy=LoggingStrategy(
            fraction_fit=1.0,
            fraction_evaluate=1.0,
            min_available_clients=int(getattr(args, "n_count", 2)),
            min_fit_clients=int(getattr(args, "n_count", 2)),
            min_evaluate_clients=int(getattr(args, "n_count", 2)),
            output_dir=output_dir,
        ),
    )
