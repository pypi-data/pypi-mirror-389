import flwr as fl
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
# from sklearn.preprocessing import StandardScaler
from flwr.common import Scalar
# import joblib # for dumpingg scaled pkls


class LinRegClient(fl.client.NumPyClient):
    def __init__(self, data_path: str):
        df = pd.read_csv(data_path)

        X = df.drop(columns=["MedHouseVal"]).apply(pd.to_numeric, errors="coerce").fillna(0).values
        y = df["MedHouseVal"].to_numpy(dtype=np.float64)

        # enforce scaler when required, add argument parameter for scaler preference

        # scaler = StandardScaler()
        # _ = scaler.fit(X)
        # joblib.dump(scaler, "scalers/client_scaler_0.pkl")

        self.X = X
        self.y = y
        self.model = LinearRegression()

    def get_parameters(self, config):
        coef = getattr(self.model, "coef_", np.zeros(self.X.shape[1], dtype=np.float64))
        intercept = getattr(self.model, "intercept_", 0.0)

        coef = np.asarray(coef, dtype=np.float64)
        intercept = np.asarray([intercept], dtype=np.float64)

        return [coef, intercept]

    def fit(self, parameters, config):
        coef, intercept = parameters
        self.model.coef_ = np.asarray(coef, dtype=np.float64)
        self.model.intercept_ = float(np.asarray(intercept).ravel()[0])

        self.model.fit(self.X, self.y)

        return self.get_parameters(config), len(self.X), {}

    def evaluate(
        self,
        parameters,
        config: dict[str, Scalar],
    ) -> tuple[float, int, dict[str, Scalar]]:

        coef, intercept = parameters
        self.model.coef_ = np.asarray(coef, dtype=np.float64)
        self.model.intercept_ = float(np.asarray(intercept).ravel()[0])

        preds = self.model.predict(self.X)
        loss = mean_squared_error(self.y, preds)

        return float(loss), len(self.X), {"mse": float(loss)}



def start_client(args):
    client = LinRegClient(args.project)
    fl.client.start_client(
        server_address=(args.start),
        client=client.to_client()
    )
