import optuna
from gfa_ml.data_model.data_type import ModelType, OptunaSampler
from gfa_ml.data_model.common import (
    LSTMConfig,
    TransformerConfig,
)
import pandas as pd
from gfa_ml.lib.training import mlflow_run
import logging
import traceback
import copy
from gfa_ml.lib.constant import (
    DEFAULT_HIDDEN_NEURONS,
    DEFAULT_NUM_HIDDEN_LAYERS,
    DEFAULT_BATCH_SIZES,
    DEFAULT_LEARNING_RATES,
    DEFAULT_DROPOUT_RATES,
    DEFAULT_ACTIVATION_FUNCTIONS,
    DEFAULT_OPTIMIZERS,
    DEFAULT_LOSSES,
    DEFAULT_NHEADS,
    DEFAULT_DIM_FEEDFORWARDS,
    DEFAULT_D_MODELS,
)
from gfa_ml.data_model.common import RunConfig

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class HyperParameterOptimizer:
    def __init__(
        self,
        experiment_name: str,
        run_config: RunConfig,
        input_cols_list: list,
        history_size_list: list,
        retention_padding_list: list,
        model_type_list: list,
        batch_size_list: list = DEFAULT_BATCH_SIZES,
        drop_rate_list: list = DEFAULT_DROPOUT_RATES,
        loss_list: list = DEFAULT_LOSSES,
        learning_rate_list: list = DEFAULT_LEARNING_RATES,
        num_layers_list: list = DEFAULT_NUM_HIDDEN_LAYERS,
        activation_function_list: list = DEFAULT_ACTIVATION_FUNCTIONS,
        optimizer_list: list = DEFAULT_OPTIMIZERS,
        d_model_list: list = DEFAULT_D_MODELS,
        nhead_list: list = DEFAULT_NHEADS,
        dim_feedforward_list: list = DEFAULT_DIM_FEEDFORWARDS,
        hidden_neurons_list: list = DEFAULT_HIDDEN_NEURONS,
        explainability: bool = True,
        plot_path: str = None,
        interpolate_outliers: bool = False,
        image_extension: str = "png",
        optimization_objective: str = "test_mape",
    ):
        self.df = None
        self.experiment_name = experiment_name
        self.run_config = run_config
        self.input_cols_list = input_cols_list
        self.history_size_list = history_size_list
        self.retention_padding_list = retention_padding_list
        self.model_type_list = model_type_list
        self.batch_size_list = batch_size_list
        self.drop_rate_list = drop_rate_list
        self.loss_list = loss_list
        self.learning_rate_list = learning_rate_list
        self.num_layers_list = num_layers_list
        self.activation_function_list = activation_function_list
        self.optimizer_list = optimizer_list
        self.d_model_list = d_model_list
        self.nhead_list = nhead_list
        self.dim_feedforward_list = dim_feedforward_list
        self.hidden_neurons_list = hidden_neurons_list
        self.explainability = explainability
        self.plot_path = plot_path
        self.interpolate_outliers = interpolate_outliers
        self.image_extension = image_extension
        self.optimization_objective = optimization_objective

    def run_study(
        self,
        df: pd.DataFrame,
        n_trials: int = 20,
        n_jobs: int = 1,
        sampler_type: OptunaSampler = OptunaSampler.QMCSampler,
    ):
        try:
            self.df = df
            if sampler_type == OptunaSampler.TPE:
                sampler = optuna.samplers.TPESampler()
            elif sampler_type == OptunaSampler.CMAES:
                sampler = optuna.samplers.CmaEsSampler()
            elif sampler_type == OptunaSampler.QMCSampler:
                sampler = optuna.samplers.QMCSampler()
            elif sampler_type == OptunaSampler.GRID:
                sampler = optuna.samplers.GridSampler()
            elif sampler_type == OptunaSampler.RANDOM:
                sampler = optuna.samplers.RandomSampler()
            elif sampler_type == OptunaSampler.NSGAII:
                sampler = optuna.samplers.NSGAIISampler()
            elif sampler_type == OptunaSampler.BRUTE_FORCE:
                sampler = optuna.samplers.BruteForceSampler()
            elif sampler_type == OptunaSampler.BOTORCH:
                sampler = optuna.samplers.BoTorchSampler()
            elif sampler_type == OptunaSampler.GP:
                sampler = optuna.samplers.GPSampler()
            else:
                sampler = optuna.samplers.TPESampler()
            study = optuna.create_study(direction="minimize", sampler=sampler)
            study.optimize(self.objective, n_trials=n_trials, n_jobs=n_jobs)
            logging.info(f"Best trial: {study.best_trial.number}")
            logging.info(f"Best value: {study.best_trial.value}")
            logging.info(f"Best params: {study.best_trial.params}")
            return study, study.best_trial
        except Exception as e:
            logging.error(f"Error running study: {e}")
            logging.info(traceback.format_exc())
            return None

    def objective(self, trial: optuna.Trial) -> float:
        try:
            temp_run_config = copy.deepcopy(self.run_config)
            input_cols_index = trial.suggest_int(
                "input_cols_index", 0, len(self.input_cols_list) - 1
            )
            history_size_index = trial.suggest_int(
                "history_size_index", 0, len(self.history_size_list) - 1
            )
            retention_padding_index = trial.suggest_int(
                "retention_padding_index", 0, len(self.retention_padding_list) - 1
            )
            batch_size_index = trial.suggest_int(
                "batch_size_index", 0, len(self.batch_size_list) - 1
            )
            drop_rate_index = trial.suggest_int(
                "drop_rate_index", 0, len(self.drop_rate_list) - 1
            )
            loss_index = trial.suggest_int("loss_index", 0, len(self.loss_list) - 1)
            learning_rate_index = trial.suggest_int(
                "learning_rate_index", 0, len(self.learning_rate_list) - 1
            )
            num_layers_index = trial.suggest_int(
                "num_layers_index", 0, len(self.num_layers_list) - 1
            )
            activation_function_index = trial.suggest_int(
                "activation_function_index", 0, len(self.activation_function_list) - 1
            )
            optimizer_index = trial.suggest_int(
                "optimizer_index", 0, len(self.optimizer_list) - 1
            )
            input_cols = self.input_cols_list[input_cols_index]
            history_size = self.history_size_list[history_size_index]
            retention_padding = self.retention_padding_list[retention_padding_index]
            batch_size = self.batch_size_list[batch_size_index]
            drop_rate = self.drop_rate_list[drop_rate_index]
            loss = self.loss_list[loss_index]
            learning_rate = self.learning_rate_list[learning_rate_index]
            num_layers = self.num_layers_list[num_layers_index]
            activation_function = self.activation_function_list[
                activation_function_index
            ]
            optimizer = self.optimizer_list[optimizer_index]
            trial.set_user_attr("input_cols", input_cols)
            trial.set_user_attr("history_size", history_size)
            trial.set_user_attr("retention_padding", retention_padding)
            trial.set_user_attr("batch_size", batch_size)
            trial.set_user_attr("drop_rate", drop_rate)
            trial.set_user_attr("loss", loss)
            trial.set_user_attr("learning_rate", learning_rate)
            trial.set_user_attr("num_layers", num_layers)
            trial.set_user_attr("activation_function", activation_function)
            trial.set_user_attr("optimizer", optimizer)

            temp_run_config.data_config.input_cols = input_cols
            temp_run_config.data_config.history_size = history_size
            temp_run_config.data_config.retention_padding = retention_padding
            temp_run_config.training_config.batch_size = batch_size
            temp_run_config.ml_model_config.drop_rate = drop_rate
            temp_run_config.ml_model_config.loss = loss
            temp_run_config.ml_model_config.learning_rate = learning_rate
            temp_run_config.ml_model_config.num_layers = num_layers
            temp_run_config.ml_model_config.activation_function = activation_function
            temp_run_config.ml_model_config.optimizer = optimizer

            model_type_index = trial.suggest_int(
                "model_type_index", 0, len(self.model_type_list) - 1
            )
            model_type = self.model_type_list[model_type_index]
            trial.set_user_attr("model_type", model_type)
            model_config_dict = temp_run_config.ml_model_config.to_dict()
            model_config_dict["model_type"] = model_type
            if model_type == ModelType.TRANSFORMER.value:
                d_model_index = trial.suggest_int(
                    "d_model_index", 0, len(self.d_model_list) - 1
                )
                nhead_index = trial.suggest_int(
                    "nhead_index", 0, len(self.nhead_list) - 1
                )
                dim_feedforward_index = trial.suggest_int(
                    "dim_feedforward_index", 0, len(self.dim_feedforward_list) - 1
                )
                d_model = self.d_model_list[d_model_index]
                nhead = self.nhead_list[nhead_index]
                dim_feedforward = self.dim_feedforward_list[dim_feedforward_index]
                trial.set_user_attr("d_model", d_model)
                trial.set_user_attr("nhead", nhead)
                trial.set_user_attr("dim_feedforward", dim_feedforward)
                model_config_dict.update(
                    {
                        "d_model": d_model,
                        "nhead": nhead,
                        "dim_feedforward": dim_feedforward,
                    }
                )
                temp_run_config.ml_model_config = TransformerConfig.from_dict(
                    model_config_dict
                )
            elif model_type == ModelType.LSTM.value:
                hidden_neurons_index = trial.suggest_int(
                    "hidden_neurons_index", 0, len(self.hidden_neurons_list) - 1
                )
                hidden_neurons = self.hidden_neurons_list[hidden_neurons_index]
                trial.set_user_attr("hidden_neurons", hidden_neurons)
                lstm_config_dict = {"hidden_neurons": hidden_neurons}
                temp_run_config.ml_model_config = LSTMConfig.from_dict(lstm_config_dict)

            training_result = mlflow_run(
                df=self.df,
                run_config=temp_run_config,
                experiment_name=self.experiment_name,
                run_name=f"run_{trial.number}",
                explainability=self.explainability,
                plot_path=self.plot_path,
                interpolate_outliers=self.interpolate_outliers,
                image_extension=self.image_extension,
            )
            if training_result is None:
                return float("inf")
            loss_value = training_result.get(self.optimization_objective, float("inf"))
            return loss_value
        except Exception as e:
            logging.error(f"Error in objective function: {e}")
            logging.info(traceback.format_exc())
            return float("inf")
