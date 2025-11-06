"""
keynet-train: MLflow 기반 PyTorch 모델 훈련 및 배포 자동화.

이 패키지는 PyTorch 모델 훈련부터 ONNX 변환, MLflow 로깅, Triton 배포까지
완전히 자동화된 ML 파이프라인을 제공합니다.

주요 기능:
- @trace_pytorch: PyTorch 훈련 자동화 데코레이터
- log_onnx_model: 프레임워크 독립적 ONNX 모델 배포
- TrainConfig: 환경변수 기반 설정 관리

기본 사용법:
    ```python
    import torch
    import torch.nn as nn
    from keynet_train import trace_pytorch

    @trace_pytorch(
        "my_experiment",
        torch.randn(1, 784),
        auto_convert_onnx=True
    )
    def train_model():
        model = nn.Sequential(
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )
        # 훈련 로직...
        return model

    model = train_model()
    ```

프레임워크 독립적 ONNX 배포:
    ```python
    from keynet_train import log_onnx_model

    log_onnx_model(
        experiment_name="tensorflow_experiment",
        onnx_model_path="model.onnx",
        metadata={"framework": "tensorflow"}
    )
    ```

환경 설정:
    ```python
    from keynet_train import TrainConfig

    config = TrainConfig()
    if config.is_production:
        config.check_production_vars()
    ```
"""

__version__ = "0.4.1"

import os

from .config import TrainConfig
from .decorators import log_onnx_model, trace_pytorch
from .utils import DatasetPath

os.environ["GIT_PYTHON_REFRESH"] = "quiet"

__all__ = [
    "__version__",
    "trace_pytorch",
    "log_onnx_model",
    "TrainConfig",
    "DatasetPath",
]
