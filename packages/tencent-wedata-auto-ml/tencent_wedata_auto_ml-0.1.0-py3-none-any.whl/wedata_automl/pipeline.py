# -*- coding: utf-8 -*-
from __future__ import annotations
import traceback
from typing import Optional, Dict, Any
import mlflow
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

from .logging_utils import safe_print, silence_third_party_logs, mute_external_io
from .training import train_and_select, _prob_or_pred
from .mlflow_utils import set_experiment_safely, log_register_verify

DEFAULT_EXPERIMENT_NAME = "blueszzhang-test-automl"
DEFAULT_REGISTERED_MODEL_NAME = "flaml_best_model"
DEFAULT_ARTIFACT_SUBDIR = "model"


def run_pipeline(
    X: Optional["pd.DataFrame"] = None,
    y: Optional["pd.Series"] = None,
    experiment_name: str = DEFAULT_EXPERIMENT_NAME,
    registered_model_name: str = DEFAULT_REGISTERED_MODEL_NAME,
    artifact_subdir: str = DEFAULT_ARTIFACT_SUBDIR,
    automl_config: Optional[Dict[str, Any]] = None,
    random_state: int = 42,
) -> Dict[str, Any]:
    """End-to-end pipeline: data split -> AutoML/RF training -> MLflow logging/registry.

    Returns a dict with best estimator info, metrics and model registry metadata.
    """
    silence_third_party_logs()
    safe_print("\n========= [DEBUG] run_pipeline() 启动 =========")

    # Lazy imports for type hints
    import pandas as pd  # type: ignore

    # Data
    if X is None or y is None:
        safe_print("[STEP] 准备示例数据（breast_cancer）…")
        X, y = load_breast_cancer(return_X_y=True, as_frame=True)
        X = X.iloc[:, :10]
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=random_state
    )
    X_valid, X_test, y_valid, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=random_state
    )
    safe_print("✅ 数据完成: ",
               f"X_train={X_train.shape}, X_valid={X_valid.shape}, X_test={X_test.shape}")

    # Experiment
    safe_print(f"[STEP] set_experiment: {experiment_name}")
    try:
        set_experiment_safely(experiment_name)
        safe_print("✅ set_experiment 完成")
    except Exception:
        safe_print("❌ set_experiment 失败"); traceback.print_exc(); raise

    # Parent run
    with mute_external_io():
        parent_ctx = mlflow.start_run(run_name="pipeline_parent")
    with parent_ctx as parent_run:
        with mute_external_io():
            mlflow.log_params({"n_train": len(X_train), "n_valid": len(X_valid)})

        # Train & select
        best_model, best_cfg, best_est_str = train_and_select(
            X_train, X_valid, y_train, y_valid, automl_config=automl_config
        )
        y_valid_pred = _prob_or_pred(best_model, X_valid)
        y_test_pred = _prob_or_pred(best_model, X_test)
        valid_auc = roc_auc_score(y_valid, y_valid_pred)
        test_auc = roc_auc_score(y_test, y_test_pred)
        with mute_external_io():
            mlflow.log_metric("valid_auc_best", valid_auc)
            mlflow.log_metric("test_auc_best", test_auc)
            mlflow.log_param("best_estimator", best_est_str)
        safe_print(f"✅ 评估: valid_auc={valid_auc:.6f}, test_auc={test_auc:.6f}")

        # Child run: log -> register -> verify
        with mute_external_io():
            child_ctx = mlflow.start_run(run_name=f"best_model__{best_est_str}", nested=True)
        with child_ctx as child_run:
            child_run_id = child_run.info.run_id
            safe_print(f"[INFO] 子 run id: {child_run_id}")
            with mute_external_io():
                mlflow.log_params({f"best_cfg__{k}": v for k, v in (best_cfg or {}).items()})
                mlflow.log_metrics({"valid_auc": valid_auc, "test_auc": test_auc})
            mv_version, src_uri = log_register_verify(
                model=best_model,
                X_train=X_train,
                X_test=X_test,
                child_run_id=child_run_id,
                artifact_subdir=artifact_subdir,
                registered_model_name=registered_model_name,
            )
            safe_print(f"[DONE] 版本就绪: name={registered_model_name}, version={mv_version}")
            safe_print(f"[DONE] source={src_uri}")

    safe_print("\n========= ✅ 流程结束 =========\n")
    return {
        "best_estimator": best_est_str,
        "best_cfg": best_cfg,
        "valid_auc": float(valid_auc),
        "test_auc": float(test_auc),
        "model_version": int(mv_version),
        "model_source": src_uri,
        "experiment_name": experiment_name,
        "registered_model_name": registered_model_name,
    }


def main():
    run_pipeline()


if __name__ == "__main__":
    main()

