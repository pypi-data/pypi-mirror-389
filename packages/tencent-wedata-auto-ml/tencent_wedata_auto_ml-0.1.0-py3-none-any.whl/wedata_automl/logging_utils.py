# -*- coding: utf-8 -*-
import os, sys, logging, warnings, contextlib


def safe_print(*args, **kwargs):
    """Print and flush immediately (safer under buffers)."""
    print(*args, **kwargs)
    sys.stdout.flush()


def silence_third_party_logs():
    """Reduce noisy logs from common libs in production environments."""
    warnings.filterwarnings("ignore")
    logging.getLogger().setLevel(logging.WARNING)
    for name in [
        "mlflow",
        "mlflow.store",
        "mlflow.tracking",
        "mlflow.gateway",
        "sqlalchemy.engine",
        "urllib3",
        "werkzeug",
        "gunicorn",
        "sklearn",
        "xgboost",
        "lightgbm",
        "wedata",
    ]:
        logging.getLogger(name).setLevel(logging.ERROR)
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")


@contextlib.contextmanager
def mute_external_io():
    """Context manager that silences stdout/stderr of code inside the block."""
    _out, _err = sys.stdout, sys.stderr
    try:
        dev = open(os.devnull, "w")
        sys.stdout = dev
        sys.stderr = dev
        yield
    finally:
        try:
            dev.close()
        except Exception:
            pass
        sys.stdout, sys.stderr = _out, _err

