# RF-DETR For Document Layout Analysis

This is a repository for RF-DETR For Document Layout Analysis training with DocLayNet dataset.

This repository is based on [rf-detr-onnx](https://github.com/PierreMarieCurie/rf-detr-onnx).

|Original Image|Result Image|
|---|---|
|![academic](./assets/academic.jpg) | ![academic_result](./assets/academic_result.jpg) |
|![textbook](./assets/textbook.jpg) | ![textbook_result](./assets/textbook_result.jpg) |

## Installation

```bash
pip install rfdetr-doclayout
```

## Quick Start

```python
from rfdetr_doclayout.rfdetr import RfDetrDoclayout
import time

# Initialize the model
model = RfDetrDoclayout()

# Run inference and get detections
_, labels, boxes, masks = model.predict("path/to/image.jpg")
model.save_detections("path/to/image.jpg", boxes, labels, masks, "path/to/output.jpg")
```


## Training

```bash
git clone https://github.com/neka-nat/rfdetr-doclayout.git
cd rfdetr-doclayout
uv sync --extra train
```

### Download Dataset

```bash
wget https://codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud/dax-doclaynet/1.0.0/DocLayNet_core.zip
unzip DocLayNet_core.zip -d DocLayNet_core
```

Convert dataset to RF-DETR format.

```bash
uv run scripts/convert_dataset.py --src DocLayNet_core --dst dataset
```

### Training Locally

```bash
uv run scripts/doclaynet_train.py --dataset_dir dataset --output_dir models/rfdetr-doclayout
```

### Training on AWS SageMaker

```bash
aws s3 sync dataset/  s3://<your-bucket-name>/dataset
touch .env
echo "AWS_BUCKET_NAME=<your-bucket-name>" >> .env
echo "AWS_SAGEMAKER_ROLE_NAME=<your-role-name>" >> .env
uv run scripts/deploy_train.py
```
