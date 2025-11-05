# -*- coding: utf-8 -*-
from __future__ import annotations
import numpy as np
from typing import Tuple, Dict, Any, Optional
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from .logging_utils import safe_print, mute_external_io


def _prob_or_pred(model, X):
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        if isinstance(proba, np.ndarray) and proba.ndim == 2 and proba.shape[1] >= 2:
            return proba[:, 1]
    if hasattr(model, "decision_function"):
        s = np.asarray(model.decision_function(X)).reshape(-1)
        smin, smax = float(s.min()), float(s.max())
        return (s - smin) / (smax - smin + 1e-9)
    return np.asarray(model.predict(X)).reshape(-1)


def try_import_automl():
    """Try to import FLAML AutoML; return None if not available."""
    try:
        from flaml import AutoML  # type: ignore
        return AutoML
    except Exception:
        try:
            from flaml.automl import AutoML  # type: ignore
            return AutoML
        except Exception:
            return None


def train_and_select(
    X_train,
    X_valid,
    y_train,
    y_valid,
    automl_config: Optional[Dict[str, Any]] = None,
) -> Tuple[object, Optional[Dict[str, Any]], str]:
    """Train with FLAML when available, otherwise fallback to RF small search.

    Returns (best_model, best_config, best_estimator_name)
    """
    AutoML = try_import_automl()
    if AutoML is not None:
        safe_print("[STEP] 训练 AutoML（优先）…")
        cfg = {
            "task": "classification",
            "metric": "roc_auc",
            "time_budget": 300,
            "eval_method": "holdout",
            "ensemble": False,
            "verbose": 0,
            "estimator_list": ["rf", "lrl1", "xgboost"],
        }
        if automl_config:
            cfg.update(automl_config)
        with mute_external_io():
            automl = AutoML()
            automl.fit(
                X_train=X_train,
                y_train=y_train,
                X_val=X_valid,
                y_val=y_valid,
                **cfg,
            )
        best_model = automl.model
        best_cfg = getattr(automl, "best_config", None)
        best_est = str(getattr(automl, "best_estimator", "")) or "unknown_estimator"
        safe_print(f"✅ AutoML 完成: best_estimator={best_est}")
        return best_model, best_cfg, best_est
    else:
        safe_print("[STEP] AutoML 不可用 → 回退 RandomForest 简单搜索…")
        candidates = [
            dict(n_estimators=100, max_depth=6, max_features=0.6),
            dict(n_estimators=200, max_depth=10, max_features=0.8),
            dict(n_estimators=300, max_depth=12, max_features=0.7),
        ]
        best_model, best_cfg, best_score = None, None, -1.0
        for cfg in candidates:
            with mute_external_io():
                m = RandomForestClassifier(
                    n_estimators=cfg["n_estimators"],
                    max_depth=cfg["max_depth"],
                    max_features=cfg["max_features"],
                    random_state=42,
                    n_jobs=-1,
                )
                m.fit(X_train, y_train)
                score = roc_auc_score(y_valid, _prob_or_pred(m, X_valid))
            if score > best_score:
                best_model, best_cfg, best_score = m, cfg, score
        safe_print(f"✅ RF 搜索完成: best_cfg={best_cfg}, valid_auc={best_score:.6f}")
        return best_model, best_cfg, "rf"

