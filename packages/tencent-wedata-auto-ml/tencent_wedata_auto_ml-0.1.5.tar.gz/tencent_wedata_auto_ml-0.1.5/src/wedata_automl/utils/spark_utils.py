from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def get_or_create_spark():
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception as e:
        raise RuntimeError("Spark is not available in this environment.") from e


def read_table_to_pandas(table: str, spark=None):
    if spark is None:
        spark = get_or_create_spark()
    return spark.read.table(table).toPandas()


def compute_split_and_weights(
    y,
    task: str = "classification",
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
    stratify: bool = True,
    random_state: int = 42,
) -> Tuple["pd.Series", "pd.Series"]:
    """Compute Databricks-style split marker and sample weights.

    Returns:
        split_col: pd.Series with values {0: train, 1: val, 2: test}
        sample_weights: pd.Series aligned to y
    """
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split

    logger.debug("compute_split_and_weights: task=%s train_ratio=%.2f val_ratio=%.2f test_ratio=%.2f stratify=%s",
                 task, train_ratio, val_ratio, test_ratio, stratify)

    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        total = train_ratio + val_ratio + test_ratio
        train_ratio, val_ratio, test_ratio = train_ratio / total, val_ratio / total, test_ratio / total
        logger.info("Ratios normalized: train=%.2f val=%.2f test=%.2f", train_ratio, val_ratio, test_ratio)

    n = len(y)
    idx = np.arange(n)
    can_stratify = False
    if task == "classification" and stratify:
        vc = pd.Series(y).value_counts()
        can_stratify = all(count >= 2 for count in vc.values)
        if can_stratify:
            logger.info("Stratified split enabled: all classes have >=2 samples")
        else:
            logger.warning("Stratified split disabled: some classes have <2 samples, using random split")

    # first split: train vs temp
    strat = y if can_stratify else None
    idx_train, idx_temp, y_train, y_temp = train_test_split(
        idx, y, test_size=(1.0 - train_ratio), random_state=random_state, stratify=strat
    )

    # second split: val vs test
    strat2 = y_temp if (can_stratify and len(np.unique(y_temp)) > 1) else None
    test_size = test_ratio / (val_ratio + test_ratio) if (val_ratio + test_ratio) > 0 else 0.5
    idx_val, idx_test = train_test_split(
        idx_temp, test_size=test_size, random_state=random_state, stratify=strat2
    )

    split_col = pd.Series(index=np.arange(n), dtype=int)
    split_col.loc[idx_train] = 0
    split_col.loc[idx_val] = 1
    split_col.loc[idx_test] = 2

    logger.info("Split indices computed: train=%d (%.1f%%), val=%d (%.1f%%), test=%d (%.1f%%)",
                len(idx_train), 100*len(idx_train)/n,
                len(idx_val), 100*len(idx_val)/n,
                len(idx_test), 100*len(idx_test)/n)

    # sample weights
    if task == "classification":
        from sklearn.utils.class_weight import compute_sample_weight
        sample_weights = pd.Series(compute_sample_weight(class_weight="balanced", y=y))
        logger.info("Sample weights computed (class-balanced): min=%.4f max=%.4f mean=%.4f",
                    sample_weights.min(), sample_weights.max(), sample_weights.mean())
    else:
        sample_weights = pd.Series(np.ones(n, dtype=float))
        logger.debug("Sample weights set to 1.0 for regression task")

    return split_col, sample_weights

