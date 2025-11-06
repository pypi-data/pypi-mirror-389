from typing import Any, Dict, List, Optional

import mlflow
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline as SkPipe
from sklearn.metrics import accuracy_score
import logging

logger = logging.getLogger(__name__)


# Robust import for FLAML across versions
try:
    from flaml import AutoML  # preferred public import
    import flaml as flaml_pkg
except Exception:  # pragma: no cover - fallback for certain versions
    from flaml.automl import AutoML  # older/internal path
    import flaml as flaml_pkg

from wedata_automl.config import normalize_config
from wedata_automl.utils.sk_pipeline import build_numeric_preprocessor
from wedata_automl.artifact_contract import (
    log_feature_list,
    log_best_config_overall,
    log_best_config_per_estimator,
    log_engine_meta,
)
from wedata_automl.utils.spark_utils import compute_split_and_weights
from wedata_automl.utils.print_utils import safe_print, print_section, print_dict


def _load_pdf_from_cfg(cfg: Dict[str, Any], spark) -> pd.DataFrame:
    if cfg.get("table"):
        if spark is None:
            raise RuntimeError("Spark session is required to read table. Provide 'spark' or run in Spark notebook.")
        return spark.read.table(cfg["table"]).toPandas()
    raise ValueError("No data source specified. Provide 'table' in config for V1.")


def run(cfg: Dict[str, Any], spark=None, pdf: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    cfg = normalize_config(cfg)
    # Setup logging based on config
    level_name = str(cfg.get("log_level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            force=True
        )

    logger.setLevel(level)

    # Print to stdout for Notebook visibility
    print_section("WeData AutoML - FLAML Engine")
    safe_print(f"Engine: {cfg['engine']} | Task: {cfg['task']} | Metric: {cfg['metric']}")
    safe_print(f"Time Budget: {cfg['time_budget']}s | Seed: {cfg.get('seed')}")
    safe_print(f"Data Source: table={cfg.get('table')}, provided_pdf={pdf is not None}")


    # 1) Load data
    if pdf is None:
        pdf = _load_pdf_from_cfg(cfg, spark)

    safe_print(f"Loaded data with shape={getattr(pdf, 'shape', None)}")


    label = cfg["label_col"]
    disable_cols = set(cfg.get("disable_cols", [])) | {label}
    features: List[str] = [c for c in pdf.columns if c not in disable_cols]

    safe_print(f"Label column: {label}; Selected {len(features)} feature columns")

    if cfg["task"] == "classification":
        try:
            _dist = pd.Series(pdf[label]).value_counts().to_dict()
            safe_print(f"Label distribution (top 10): {dict(list(_dist.items())[:10])}", level="DEBUG")
        except Exception:
            pass


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

    train_cnt = int((pdf["_automl_split_col_0000"] == 0).sum())
    val_cnt = int((pdf["_automl_split_col_0000"] == 1).sum())
    test_cnt = int((pdf["_automl_split_col_0000"] == 2).sum())
    safe_print(f"Split counts: train={train_cnt}, val={val_cnt}, test={test_cnt}")

    if cfg["task"] == "classification":
        import numpy as _np
        _sw = sample_weights.values if hasattr(sample_weights, "values") else sample_weights
        safe_print(f"Sample weights: min={float(_np.min(_sw)):.4f}, mean={float(_np.mean(_sw)):.4f}, max={float(_np.max(_sw)):.4f}")


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

    safe_print(f"Split shapes: X_train={getattr(X_train, 'shape', None)}, X_val={getattr(X_val, 'shape', None)}, X_test={getattr(X_test, 'shape', None)}")


    # Fit preprocessor on train only to avoid leakage
    X_train_num = pre.fit_transform(X_train)
    X_val_num = pre.transform(X_val)

    safe_print(f"Preprocessor fitted. Transformed shapes: X_train_num={getattr(X_train_num, 'shape', None)}, X_val_num={getattr(X_val_num, 'shape', None)}")


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

    safe_print(f"FLAML version={getattr(flaml_pkg, '__version__', 'unknown')}")
    safe_print(f"FLAML settings: time_budget={settings['time_budget']}s, metric={settings['metric']}, estimators={settings['estimator_list']}, seed={settings['seed']}")


    with mlflow.start_run(run_name=f"{cfg['engine']}_automl_main"):
        safe_print(f"MLflow run started: run_id={mlflow.active_run().info.run_id}", level="START")

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
        log_engine_meta({"engine": "flaml", "version": getattr(flaml_pkg, "__version__", "unknown")})

        # 5) Train with FLAML using our validation split
        safe_print(f"Starting AutoML.fit: X_train_num={getattr(X_train_num, 'shape', None)}, X_val_num={getattr(X_val_num, 'shape', None)}", level="START")

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
        _bpe = getattr(automl, "best_config_per_estimator", {}) or {}
        safe_print(f"AutoML finished. best_estimator={best_est}, best_loss={getattr(automl, 'best_loss', None)}", level="SUCCESS")
        safe_print(f"AutoML trials summary: estimators_tried={len(_bpe)}, per-estimator best configs={list(_bpe.keys()) if isinstance(_bpe, dict) else type(_bpe)}")
        mlflow.log_param("best_estimator", best_est)

        # 6) Build serving pipeline: DataFrame -> pre -> estimator
        clf = automl.model
        pipe = SkPipe([("preprocess", pre), ("clf", clf)])
        safe_print(f"Serving pipeline built. Fitting pipeline on raw X_train with shape={getattr(X_train, 'shape', None)}")

        pipe.fit(X_train, y_train)

        # quick metrics on all splits (unweighted + weighted)
        if cfg["task"] == "classification":
            for name, X, y_true, sw in [
                ("train", X_train, y_train, sw_train),
                ("val", X_val, y_val, sw_val),
                ("test", X_test, y_test, sw_test),
            ]:
                pred = pipe.predict(X)
                acc = float(accuracy_score(y_true, pred))
                accw = float(accuracy_score(y_true, pred, sample_weight=sw))
                safe_print(f"{name} metrics: accuracy={acc:.4f}, accuracy_weighted={accw:.4f}, n={len(y_true)}")
                mlflow.log_metric(f"{name}_accuracy", acc)
                mlflow.log_metric(f"{name}_accuracy_weighted", accw)

        # 7) Registration via WeData client.log_model
        input_example = X_train.head(3)
        uri = f"runs:/{mlflow.active_run().info.run_id}/{cfg.get('artifact_path', 'model')}"
        version = None

        register_config = cfg.get("register", {})
        register_enabled = register_config.get("enable", False)

        # Print registration status to stdout for Notebook
        print_section("模型注册配置")
        safe_print(f"注册启用: {register_enabled}")
        if register_enabled:
            safe_print(f"注册后端: {register_config.get('backend', 'wedata')}")
            safe_print(f"模型名称: {register_config.get('model_name', 'wedata_model')}")

        if register_enabled:
            backend = cfg["register"].get("backend", "wedata")
            base = cfg["register"].get("model_name", "wedata_model")
            per_cand = cfg["register"].get("per_candidate", False)
            register_name = f"{base}_{best_est}" if per_cand else base

            safe_print(f"开始注册模型: {register_name} (后端: {backend})", level="START")


            if backend == "wedata":
                try:
                    from wedata.feature_store.client import FeatureStoreClient
                    from wedata.feature_store.entities.feature_lookup import FeatureLookup

                    if spark is None:
                        raise RuntimeError("Spark session is required for WeData registration.")
                    client = FeatureStoreClient(spark)
                    safe_print("WeData FeatureStoreClient initialized")

                    training_set_obj = None
                    if cfg["feature_store"].get("use_training_set", True):
                        fs_table = cfg["feature_store"].get("table_name") or cfg.get("table")
                        pks = list(cfg["feature_store"].get("primary_keys", []))
                        safe_print(f"Feature store config: use_training_set=True, table={fs_table}, primary_keys={pks}, label={label}")

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
                            safe_print(f"TrainingSet created: table={fs_table}, pk={pk}, exclude_columns={exclude_cols}")
                        else:
                            safe_print("No or multiple primary_keys provided; skip TrainingSet creation.", level="WARNING")
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
                    _with_ts = training_set_obj is not None
                    safe_print(f"Calling WeData client.log_model: artifact_path={cfg.get('artifact_path', 'model')}, registered_model_name={register_name}, with_training_set={_with_ts}")

                    # Call client.log_model and get model version
                    model_info = client.log_model(**log_kwargs)

                    # Extract version from model_info if available
                    if hasattr(model_info, 'registered_model_version'):
                        version = int(model_info.registered_model_version)
                        safe_print(f"WeData 注册成功: {register_name} (版本: {version})", level="SUCCESS")
                    else:
                        safe_print(f"WeData 注册成功: {register_name} (版本信息不可用)", level="SUCCESS")

                    mlflow.log_text(register_name, "artifacts/registered_model_name.txt")
                    if version is not None:
                        mlflow.log_text(str(version), "artifacts/registered_model_version.txt")

                except Exception as e:
                    mlflow.log_text(str(e), "artifacts/registration_error.txt")
                    safe_print(f"WeData 注册失败: {str(e)}", level="ERROR")
                    # Keep logger.error for stack trace in logs
                    logger.error("WeData registration failed: %s", str(e), exc_info=True)

            else:
                # fallback to plain mlflow logging/registration if requested
                safe_print(f"Using plain MLflow logging/registration: artifact_path={cfg.get('artifact_path', 'model')}, register_name={register_name}")

                mlflow.sklearn.log_model(pipe, artifact_path=cfg.get("artifact_path", "model"), input_example=input_example)
                mlflow.log_text(register_name, "artifacts/registered_model_name.txt")
                try:
                    mv = mlflow.register_model(uri, register_name)
                    version = int(mv.version)
                    safe_print(f"MLflow register_model succeeded: name={register_name}, version={version}", level="SUCCESS")

                except Exception as e:
                    mlflow.log_text(str(e), "artifacts/registration_error.txt")
                    safe_print(f"Plain MLflow registration failed: {str(e)}", level="ERROR")
                    # Keep logger.error for stack trace in logs
                    logger.error("Plain MLflow registration failed: %s", str(e), exc_info=True)
        else:
            safe_print("模型注册已禁用。要启用注册，请设置 cfg['register']['enable']=True", level="WARNING")

        # Always log the computed model URI
        mlflow.log_text(uri, "artifacts/model_uri.txt")

        # Print final summary to stdout
        print_section("AutoML 训练完成!")
        safe_print(f"最佳估计器: {best_est}", level="COMPLETE")
        safe_print(f"模型 URI: {uri}")
        safe_print(f"模型版本: {version if version else 'N/A'}")

        return {
            "best_estimator": best_est,
            "best_config": best_cfg,
            "model_uri": uri,
            "model_version": version,
        }

