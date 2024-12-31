# Contributing

## Curating the Dataset

### Dataset Structure

The dataset is stored in `data/dataset`. Inside this folder are many subfolders, corresponding to each class recognized by the model. Inside the class folders are 224x224 black and white greyscale images. The images are inverted such that the "ink" is white, and the background is black.

The images use a naming convention that encodes the following information.

- The source of the image
- The page number from the source
- The (x, y) coordinates and the width and height of the bounding rectangle
- The (cx, cy) coordinates of the center of the bounding circle, and the radius of the bounding circle.

Example:

```
heirmologion_john_p0010_x0374_y0933_w0106_h0026_cx0426_cy0945_r0053.png
```

From this name, we can determine that this image comes from page 10 of the Heirmologion of John the Protopsaltist. The image is located within a rectangle whose top left corner is at (374, 933) and whose dimensions are 106x26. The center of the image is located at (426, 945). The radius of the bounding circle is 53.

## Training the model

To train the model, run the following commands.

```bash
python train.py
```

The resulting file will be called `current_model.pth`. A log of the training process will be saved as `train_log.txt`. This log can be plotted with the following command.

```bash
python plot_training_metrics.py
```

### Goal

The goal of training is to maximize accuracy while minimizing loss.

#### What is accuracy and loss?

Accuracy is the percentage of neumes that are correctly predicted.

Loss is a measure of how far off the model's predictions are from the actual values. It's important to note that loss is not the same as the percentage of incorrect predictions. When the model makes a prediction, it also assigns a confidence level to that prediction. If the model makes an incorrect prediction with high confidence, the loss will be larger, reflecting the severity of the error.

# Q & A

## Why MobileNet v2?

MobileNet v2 was chosen as a compromise between accuracy and efficiency. Most users will probably not have a fast, GPU-enabled machine to run the OCR engine. MobileNet is designed to work on less powerful machines.

However, there is no barrier to using a different model. If anyone wants to experiment with more powerful models, such as ResNet, pull requests are welcome.
