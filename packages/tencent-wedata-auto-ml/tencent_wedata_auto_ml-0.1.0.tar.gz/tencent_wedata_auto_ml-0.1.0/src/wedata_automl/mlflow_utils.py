# -*- coding: utf-8 -*-
from __future__ import annotations
from time import sleep
import traceback
from typing import Tuple
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.models import infer_signature
from .logging_utils import safe_print, mute_external_io


def set_experiment_safely(name: str):
    with mute_external_io():
        mlflow.set_experiment(name)


def _detect_flavor(base_model):
    is_xgb = is_lgb = False
    try:
        import xgboost as xgb  # type: ignore
        is_xgb = isinstance(base_model, (xgb.XGBClassifier, xgb.XGBRegressor, xgb.Booster))
    except Exception:
        pass
    try:
        import lightgbm as lgb  # type: ignore
        is_lgb = isinstance(base_model, (lgb.LGBMClassifier, lgb.LGBMRegressor, lgb.Booster))
    except Exception:
        pass
    return is_xgb, is_lgb


def log_register_verify(
    model,
    X_train,
    X_test,
    child_run_id: str,
    artifact_subdir: str = "model",
    registered_model_name: str = "flaml_best_model",
) -> Tuple[int, str]:
    """Log model into current run, register to Model Registry, wait READY, try loading.

    Returns (model_version, model_uri_for_registry)
    """
    base_model = getattr(model, "model", model)
    safe_print(f"[INFO] best_model={type(model)}, base_model={type(base_model)}")

    is_xgb, is_lgb = _detect_flavor(base_model)
    safe_print(f"[INFO] flavor: is_xgb={is_xgb}, is_lgb={is_lgb}")

    input_example = X_train.iloc[:5]
    with mute_external_io():
        try:
            signature = infer_signature(X_train, base_model.predict(X_train))
        except Exception:
            signature = None
    safe_print("✅ 签名准备完成")

    with mute_external_io():
        if is_xgb:
            import mlflow.xgboost  # type: ignore
            mlflow.xgboost.log_model(
                base_model, artifact_path=artifact_subdir,
                signature=signature, input_example=input_example
            )
        elif is_lgb:
            import mlflow.lightgbm  # type: ignore
            mlflow.lightgbm.log_model(
                base_model, artifact_path=artifact_subdir,
                signature=signature, input_example=input_example
            )
        else:
            import mlflow.sklearn  # type: ignore
            mlflow.sklearn.log_model(
                base_model, artifact_path=artifact_subdir,
                signature=signature, input_example=input_example
            )
    safe_print("✅ 模型落盘成功")

    items = MlflowClient().list_artifacts(run_id=child_run_id, path=artifact_subdir)
    if not items:
        safe_print("❌ 该 artifact 子目录为空（log_model 未产出文件）")
        raise RuntimeError("empty_artifacts")
    safe_print(f"[INFO] artifact 文件数：{len(items)}")

    client = MlflowClient()
    try:
        client.get_registered_model(registered_model_name)
    except Exception:
        with mute_external_io():
            client.create_registered_model(registered_model_name)
    model_uri_for_registry = f"runs:/{child_run_id}/{artifact_subdir}"
    safe_print(f"[INFO] 注册 source（runs:/）: {model_uri_for_registry}")
    with mute_external_io():
        mv = client.create_model_version(
            name=registered_model_name,
            source=model_uri_for_registry,
            run_id=child_run_id,
        )
    safe_print(f"✅ create_model_version: v={mv.version}, status={mv.status}")

    safe_print("[STEP] 等待 READY …")
    while True:
        with mute_external_io():
            cur = client.get_model_version(registered_model_name, mv.version)
        status = cur.status
        safe_print(f"[DEBUG] 当前状态: {status}")
        if status == "READY":
            safe_print(f"🎯 READY: {registered_model_name} v{cur.version}")
            break
        if status == "FAILED_REGISTRATION":
            safe_print("❌ 模型注册失败"); raise RuntimeError(cur)
        sleep(1)

    try:
        with mute_external_io():
            loaded = mlflow.pyfunc.load_model(f"models:/{registered_model_name}/{mv.version}")
            _ = loaded.predict(X_test.iloc[:3])
        safe_print("✅ Registry 加载 & 试推理成功")
    except Exception:
        safe_print("⚠️ Registry 加载或推理验证失败（不影响落盘/注册，但建议检查 flavor 环境）")
        traceback.print_exc()

    return mv.version, model_uri_for_registry

