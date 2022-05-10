# Server

### Train yolo

![](docs/TrainingYOLO.png)

##### 修改sys.ini

```ini
[Annotations]
train_set_dir = data/train2014
train_annotation_path = data/instances_train2014.json
test_set_dir = data/test2014
test_annotation_path = data/instances_test2014.json

[Save_dir]
checkpoints = checkpoints
weights = weights
configs = configs
logs = logs
train_processed_data = data/bbox/train
test_processed_data = data/bbox/test
```

sys.ini內包含了COCO資料集路徑、COCO資料集標記文件路徑、存檔位置

##### 建立一個classes.txt檔，每一行紀錄要辨識的物件名稱

```
person
car
horse
```

##### 產生YOLO設定檔(.json)

```commandline
python3 makeYoloConfig.py -n myModelName -c classes.txt -s 416 -sc 0.5 -bs 4 -ep 50 -ts 2000 -vs 100
```

設定檔內包含模型資訊、物件種類、尺寸、存檔位置、訓練資訊等參數

```json
{
  "name": "myModelName",
  "model_path": "checkpoints/myModelName",
  "weight_path": "weights/myModelName.h5",
  "logdir": "logs/myModelName",
  "frame_work": "tf",
  "model_type": "yolov4",
  "size": 416,
  "tiny": false,
  "max_output_size_per_class": 40,
  "max_total_size": 50,
  "iou_threshold": 0.5,
  "score_threshold": 0.5,
  "YOLO": {
    "CLASSES": [
      "person",
      "car",
      "horse"
    ],
    "ANCHORS": [
      5,
      13,
      21,
      34,
      38,
      108,
      50,
      158,
      113,
      121,
      66,
      219,
      351,
      95,
      184,
      384,
      339,
      373
    ],
    "ANCHORS_V3": [
      5,
      13,
      21,
      34,
      38,
      108,
      50,
      158,
      113,
      121,
      66,
      219,
      351,
      95,
      184,
      384,
      339,
      373
    ],
    "ANCHORS_TINY": [
      12,
      23,
      45,
      108,
      69,
      175,
      351,
      95,
      184,
      384,
      339,
      373
    ],
    "STRIDES": [
      8,
      16,
      32
    ],
    "STRIDES_TINY": [
      16,
      32
    ],
    "XYSCALE": [
      1.2,
      1.1,
      1.05
    ],
    "XYSCALE_TINY": [
      1.05,
      1.05
    ],
    "ANCHOR_PER_SCALE": 3,
    "IOU_LOSS_THRESH": 0.5
  },
  "TRAIN": {
    "ANNOT_PATH": "data/bbox/train/myModelName.bbox",
    "BATCH_SIZE": 4,
    "INPUT_SIZE": 416,
    "DATA_AUG": true,
    "LR_INIT": 0.001,
    "LR_END": 1e-06,
    "WARMUP_EPOCHS": 2,
    "INIT_EPOCH": 0,
    "FIRST_STAGE_EPOCHS": 0,
    "SECOND_STAGE_EPOCHS": 50,
    "PRETRAIN": null
  },
  "TEST": {
    "ANNOT_PATH": "data/bbox/test/myModelName.bbox",
    "BATCH_SIZE": 4,
    "INPUT_SIZE": 416,
    "DATA_AUG": false,
    "SCORE_THRESHOLD": 0.5,
    "IOU_THRESHOLD": 0.5
  }
}
```

##### 開始訓練

```commandline
python3 train.py configs/myModelName.json
```

如果在訓練過程意外中斷，可以直接重新執行，程式會直接從上一個存檔點接著執行下去。  
執行完後，你應該能在 *weights/* 底下找到模型的權重檔(.h5)，之後使用我們實作的Detector，就可以快速的還原模型以及辨識影像。

```python
configs = './configs/'
detector = Detector(configs)
detector.load_model('yolov4-416')
```

### Socket I/O

輸入:先接受4個Byte，並且轉換成整數N，接受整數N個Bytes(UTF-8)，轉換成字串M，最後將M解析成JSON格式，再次循環。  
輸出:將JSON解析成字串，再轉換成Bytes M，計算M的長度N，傳送N(4 Bytes)，傳送M(N Bytes)，再次循環。  
![](docs/SocketFormat.png)
![](docs/MessageExchange.png)

### Software Architecture

![](docs/SoftwareArchitecture.png)
![](docs/Layers.png)

### Remote detect

由於在Jetson nano GPU上使用YOLOv4偵測影像，會導致一個我們無法修復的BUG，我們有兩個解決方案。

1. 使用CPU運算，但是FPS會大幅減少(YOLOv4 Tiny FPS ~= 1)
2. 建立一個專門負責YOLO運算的伺服器，將影像傳回伺服器偵測，必且取回結果，再連同影像以及結果傳回客戶端, FPS取決於伺服器的運算能力，與此同時網路的連線品質也會影響到FPS的高低。

![](docs/Remotedetect.png)

### MultiThread diagram

![](docs/MultiThreadDiagram.png)

### LED Monitor

![](docs/Monitor.png)  
解析度 128 * 32  
用來標示伺服器IP、啟用時間、客戶端IP、客戶端占用時間，使用者可以藉由上面的標示判斷無人車目前的基本狀態。
![](docs/MonitorReal.jpg)

### PWM

### Benchmark

![](docs/Benchmark.png)

### Learning Rate

![](docs/LearningRate.png)

### Loss

![](docs/loss.png)
