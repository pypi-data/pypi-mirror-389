## 🤗 Citation

This code was forked from [yolov9pip](https://github.com/kadirnar/yolov9-pip).

## Description

This code is lightly updated to allow use of Pytorch >2.6 as an imported library.

This repo is a packaged version of the [Yolov9](https://github.com/WongKinYiu/yolov9) model.

### ⭐ Installation

```
pip install yolov9pip
```

### 🌠 Yolov9 Inference

```python
import yolov9

# load pretrained or custom model
model = yolov9.load(
    "yolov9-c.pt",
    device="cpu",
)

# set model parameters
model.conf = 0.25  # NMS confidence threshold
model.iou = 0.45  # NMS IoU threshold
model.classes = None  # (optional list) filter by class

# set image
imgs = "data/zidane.jpg"

# perform inference
results = model(imgs)

# inference with larger input size and test time augmentation
results = model(img, size=640)

# parse results
predictions = results.pred[0]
boxes = predictions[:, :4]  # x1, y1, x2, y2
scores = predictions[:, 4]
categories = predictions[:, 5]

# show detection bounding boxes on image
results.show()
```

## 😍 Contributing

```bash
pip install -r dev-requirements.txt
pre-commit install
pre-commit run --all-files
```
