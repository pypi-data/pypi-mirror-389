from typing import Any, Dict, List, Optional

import mlflow
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline as SkPipe
from sklearn.metrics import accuracy_score

from flaml import AutoML

from wedata_automl.config import normalize_config
from wedata_automl.utils.sk_pipeline import build_numeric_preprocessor
from wedata_automl.artifact_contract import (
    log_feature_list,
    log_best_config_overall,
    log_best_config_per_estimator,
    log_engine_meta,
)
from wedata_automl.utils.spark_utils import compute_split_and_weights


def _load_pdf_from_cfg(cfg: Dict[str, Any], spark) -> pd.DataFrame:
    if cfg.get("table"):
        if spark is None:
            raise RuntimeError("Spark session is required to read table. Provide 'spark' or run in Spark notebook.")
        return spark.read.table(cfg["table"]).toPandas()
    raise ValueError("No data source specified. Provide 'table' in config for V1.")


def run(cfg: Dict[str, Any], spark=None, pdf: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    cfg = normalize_config(cfg)

    # 1) Load data
    if pdf is None:
        pdf = _load_pdf_from_cfg(cfg, spark)

    label = cfg["label_col"]
    disable_cols = set(cfg.get("disable_cols", [])) | {label}
    features: List[str] = [c for c in pdf.columns if c not in disable_cols]

    # 2) Compute split marker and sample weights
    split_col, sample_weights = compute_split_and_weights(
        y=pdf[label].values,
        task=cfg["task"],
        train_ratio=float(cfg["split"]["train_ratio"]),
        val_ratio=float(cfg["split"]["val_ratio"]),
        test_ratio=float(cfg["split"]["test_ratio"]),
        stratify=bool(cfg["split"]["stratify"]),
        random_state=int(cfg.get("seed", 42)),
    )
    pdf["_automl_split_col_0000"] = split_col.values
    pdf["_automl_sample_weight_0000"] = sample_weights.values

    # 3) Build preprocessor and split dataframes
    pre = build_numeric_preprocessor(features)
    train_df = pdf[pdf["_automl_split_col_0000"] == 0]
    val_df = pdf[pdf["_automl_split_col_0000"] == 1]
    test_df = pdf[pdf["_automl_split_col_0000"] == 2]

    X_train = train_df[features]
    y_train = train_df[label].values
    sw_train = train_df["_automl_sample_weight_0000"].values

    X_val = val_df[features]
    y_val = val_df[label].values
    sw_val = val_df["_automl_sample_weight_0000"].values

    X_test = test_df[features]
    y_test = test_df[label].values
    sw_test = test_df["_automl_sample_weight_0000"].values

    # Fit preprocessor on train only to avoid leakage
    X_train_num = pre.fit_transform(X_train)
    X_val_num = pre.transform(X_val)

    # 4) FLAML settings
    automl = AutoML()
    settings = {
        "task": cfg["task"],
        "metric": cfg["metric"],
        "time_budget": int(cfg["time_budget"]),
        "eval_method": "holdout",
        "ensemble": False,
        "verbose": 2,
        "estimator_list": cfg.get("estimators", ["lgbm", "xgboost", "rf", "lrl1"]),
        "seed": int(cfg.get("seed", 42)),
    }

    with mlflow.start_run(run_name=f"{cfg['engine']}_automl_main"):
        # Parent run logging
        mlflow.log_params({
            "table": cfg.get("table"),
            "label": label,
            "n_rows": len(pdf),
            "n_features": len(features),
            **{f"flaml__{k}": v for k, v in settings.items()},
        })
        mlflow.log_dict({
            "train_ratio": cfg["split"]["train_ratio"],
            "val_ratio": cfg["split"]["val_ratio"],
            "test_ratio": cfg["split"]["test_ratio"],
            "stratify": cfg["split"]["stratify"],
            "counts": {
                "train": int((pdf["_automl_split_col_0000"] == 0).sum()),
                "val": int((pdf["_automl_split_col_0000"] == 1).sum()),
                "test": int((pdf["_automl_split_col_0000"] == 2).sum()),
            }
        }, "artifacts/split_stats.json")
        log_feature_list(features)
        log_engine_meta({"engine": "flaml", "version": getattr(AutoML, "__version__", "unknown")})

        # 5) Train with FLAML using our validation split
        automl.fit(
            X_train=X_train_num,
            y_train=y_train,
            X_val=X_val_num,
            y_val=y_val,
            mlflow_logging=False,
            **settings,
        )

        best_est = automl.best_estimator
        best_cfg = automl.best_config
        log_best_config_overall(best_cfg)
        if getattr(automl, "best_config_per_estimator", None):
            log_best_config_per_estimator(automl.best_config_per_estimator)
        mlflow.log_param("best_estimator", best_est)

        # 6) Build serving pipeline: DataFrame -> pre -> estimator
        clf = automl.model
        pipe = SkPipe([("preprocess", pre), ("clf", clf)])
        pipe.fit(X_train, y_train)

        # quick metrics on all splits (unweighted + weighted)
        if cfg["task"] == "classification":
            for name, X, y_true, sw in [
                ("train", X_train, y_train, sw_train),
                ("val", X_val, y_val, sw_val),
                ("test", X_test, y_test, sw_test),
            ]:
                pred = pipe.predict(X)
                mlflow.log_metric(f"{name}_accuracy", float(accuracy_score(y_true, pred)))
                mlflow.log_metric(f"{name}_accuracy_weighted", float(accuracy_score(y_true, pred, sample_weight=sw)))

        # 7) Registration via WeData client.log_model
        input_example = X_train.head(3)
        uri = f"runs:/{mlflow.active_run().info.run_id}/{cfg.get('artifact_path', 'model')}"
        version = None
        if cfg.get("register", {}).get("enable"):
            backend = cfg["register"].get("backend", "wedata")
            base = cfg["register"].get("model_name", "wedata_model")
            per_cand = cfg["register"].get("per_candidate", False)
            register_name = f"{base}_{best_est}" if per_cand else base

            if backend == "wedata":
                try:
                    from wedata.feature_store.client import FeatureStoreClient
                    from wedata.feature_store.entities.feature_lookup import FeatureLookup

                    if spark is None:
                        raise RuntimeError("Spark session is required for WeData registration.")
                    client = FeatureStoreClient(spark)

                    training_set_obj = None
                    if cfg["feature_store"].get("use_training_set", True):
                        fs_table = cfg["feature_store"].get("table_name") or cfg.get("table")
                        pks = list(cfg["feature_store"].get("primary_keys", []))
                        if len(pks) == 1:
                            pk = pks[0]
                            # Build inference df with PK + label
                            inf_df = spark.read.table(fs_table).select(pk, label)
                            fl = FeatureLookup(table_name=fs_table, lookup_key=pk)
                            # Exclude columns: user-provided + label
                            exclude_cols = list(set(cfg["feature_store"].get("exclude_columns", [])) | {label})
                            training_set_obj = client.create_training_set(
                                df=inf_df,
                                feature_lookups=[fl],
                                label=label,
                                exclude_columns=exclude_cols,
                            )
                        else:
                            mlflow.log_text("No or multiple primary_keys provided; skip TrainingSet creation.", "artifacts/registration_warning.txt")

                    # Use client.log_model (with or without training_set)
                    log_kwargs = dict(
                        model=pipe,
                        artifact_path=cfg.get("artifact_path", "model"),
                        flavor=mlflow.sklearn,
                        registered_model_name=register_name,
                    )
                    if training_set_obj is not None:
                        log_kwargs["training_set"] = training_set_obj
                    client.log_model(**log_kwargs)
                    mlflow.log_text(register_name, "artifacts/registered_model_name.txt")
                except Exception as e:
                    mlflow.log_text(str(e), "artifacts/registration_error.txt")
            else:
                # fallback to plain mlflow logging/registration if requested
                mlflow.sklearn.log_model(pipe, artifact_path=cfg.get("artifact_path", "model"), input_example=input_example)
                mlflow.log_text(register_name, "artifacts/registered_model_name.txt")
                try:
                    mv = mlflow.register_model(uri, register_name)
                    version = int(mv.version)
                except Exception as e:
                    mlflow.log_text(str(e), "artifacts/registration_error.txt")

        # Always log the computed model URI
        mlflow.log_text(uri, "artifacts/model_uri.txt")

        return {
            "best_estimator": best_est,
            "best_config": best_cfg,
            "model_uri": uri,
            "model_version": version,
        }

