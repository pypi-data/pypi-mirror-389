from mimetypes import init
import mlflow.pyfunc
from gfa_ml.lib.data_processing import create_time_aware_sequences, extract_dataframe
from gfa_ml.data_model.common import RunConfig, DataConfig
import os
import logging
from matplotlib import pyplot as plt
import traceback
import pandas as pd
import numpy as np
from ..data_model.common import InputColumns

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ModelServing:
    def __init__(
        self,
        model_path: str,
        run_config: RunConfig = None,
        data_config: DataConfig = None,
    ):
        self.run_config = run_config
        self.data_config = data_config
        if run_config:
            self.init_config_from_run(run_config)
        elif data_config:
            self.init_config_from_data_config(data_config)
        else:
            try:
                run_config_path = os.path.join(
                    model_path, "artifacts", "run_config.yaml"
                )
                self.run_config = RunConfig.from_yaml(run_config_path)
                self.init_config_from_data_config(self.run_config.data_config)
            except Exception as e:
                logging.error(f"Error loading run config: {e}")
                logging.error("Either run_config or data_config must be provided.")
        try:
            self.model = mlflow.pyfunc.load_model(model_path)
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            try:
                new_path = os.path.join(model_path, "wrapped-model")
                self.model = mlflow.pyfunc.load_model(new_path)
            except Exception as e:
                logging.error(f"Error loading wrapped model: {e}")
                self.model = None

    def init_config_from_run(self, run_config: RunConfig):
        self.init_config_from_data_config(run_config.data_config)

    def init_config_from_data_config(self, data_config: DataConfig):
        self.data_config = data_config
        self.input_cols = data_config.input_cols
        self.output_col = data_config.output_col
        self.history_size = data_config.history_size
        self.index_col = data_config.index_col
        self.retention_col = data_config.retention_col
        self.retention_padding = data_config.retention_padding
        self.interval_minutes = data_config.interval_minutes
        self.num_rows = data_config.num_rows
        self.min_rows = data_config.min_rows

    def get_num_rows(self) -> int:
        return self.num_rows

    def multiple_inference_and_evaluate(
        self,
        df: pd.DataFrame,
        plot: bool = True,
        column_extension: str = None,
        start_row: int = 0,
        end_row: int = -1,
        figure_size=(12, 6),
    ):
        if self.model is None:
            logging.error("Model is not loaded.")
            return None
        try:
            internal_df = extract_dataframe(df, start_row=start_row, end_row=end_row)
            X_t, y_t, x_t_index, y_t_index = create_time_aware_sequences(
                internal_df,
                input_cols=self.input_cols,
                output_col=self.output_col,
                history_size=self.history_size,
                index_col=self.index_col,
                retention_col=self.retention_col,
                retention_padding=self.retention_padding,
                column_extension=column_extension,
                interval_minutes=self.interval_minutes,
                num_rows=self.num_rows,
                min_rows=self.min_rows,
                return_index=True,
            )

            X_t = X_t.astype("float32")
            y = self.model.predict(X_t)
            mse = ((y - y_t) ** 2).mean()
            mae = (abs(y - y_t)).mean()
            rmse = mse**0.5
            mape = (abs((y - y_t) / y_t)).mean() * 100
            smape = (abs(y - y_t) / ((abs(y) + abs(y_t)) / 2)).mean() * 100
            logging.info(
                f"Evaluation metrics - MSE: {mse}, MAE: {mae}, RMSE: {rmse}, MAPE: {mape}%, SMAPE: {smape}%"
            )

            if plot:
                plt.figure(figsize=figure_size)
                plt.plot(y_t_index, y_t, label="True values")
                plt.plot(y_t_index, y, label="Predicted values")
                plt.legend()
                plt.show()
            return y
        except Exception as e:
            logging.error(f"Error during prediction: {e}")
            logging.info(traceback.format_exc())
            return None

    def single_inference_df(self, df: pd.DataFrame):
        try:
            input_df = pd.DataFrame()
            if (self.history_size % self.interval_minutes) != 0:
                logging.error("History size must be divisible by interval minutes.")
                return None
            window_size = self.history_size // self.interval_minutes
            for col in self.input_cols:
                if isinstance(col, InputColumns):
                    for col_j in col.columns:
                        input_df[col_j] = df[col_j].head(window_size).copy()
                else:
                    input_df[col] = df[col].head(window_size).copy()

            # replace Nan by interpolation
            input_df = input_df.interpolate(method="linear", limit_direction="both")
            input_data = input_df.to_numpy().reshape(1, window_size, -1)
            y = self.model.predict(input_data.astype("float32"))
            return y[0][0]
        except Exception as e:
            logging.error(f"Error creating inference input: {e}")
            logging.info(traceback.format_exc())
            return None

    def single_inference_np(self, input_data: np.ndarray) -> np.ndarray:
        try:
            return self.model.predict(input_data.astype("float32")).mean().item()
        except Exception as e:
            logging.error(f"Error during prediction: {e}")
            logging.info(traceback.format_exc())
            return None
