# Contributing

## Install the Development Dependencies

Install the development dependencies via the following command.

```bash
pip install -r requirements-dev.txt
```

## Repo Struture

- `data/`: Contains the model's dataset.
- `integrations/`: Contains scripts that use the output of the OCR engine to integrate with other software applications.
- `models/`: Contains the model(s) and any supporting files.
- `scripts/`: Contains scripts that are used for building the dataset, training the model, and using the OCR engine to perform OCR on images and PDFs.
- `src/`: Contains the OCR engine.

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

If you add new sources, use the same `snake_case` naming convention and update [SOURCES.md](./SOURCES.md).

### Extracting Images for Classification

This toolset contains several scripts that extract images in the correct format and naming convention from a PDF file.

#### Basics

To extract images, use the following command.

```bash
python create_dataset.py file.pdf 100 105
```

This will extract all images from pages 100-105 of `file.pdf`. Before extraction, the script will attempt to remove all lyric text.

The extracted images can be found in `data/__unclassified`.

At this point, you may either manually move the images into the correct folder within `data/dataset`, or you may use a tool such as FiftyOne to tag images and move them over with a Python script.

#### Using FiftyOne

After running `create_dataset.py`, you can launch FiftyOne via the following command.

```bash
python fo.py
```

This will launch FiftyOne inside a browser window at `http://localhost:5151`. Choose the dataset that was created. You can then select one or more images and add sample tags corresponding to the name of the class that the images belong to.

After you have tagged the samples, you can copy the tagged images to `data/dataset` via the following command.

```bash
python update_dataset.py DATASET_NAME
```

See [FiftyOne's documentation](https://docs.voxel51.com/user_guide/app.htm) for more information about what FiftyOne is capable of doing.

Note that `create_dataset.py` script also runs each image through the model to predict each image. You can filter the images in FiftyOne by using the `Labels` filter in the left sidebar. This can help you more quickly find a particular class of neumes.

#### Finding Rare Neumes

The above methods work well for finding the most common neumes, but it can be tedious to search through many images for rarer neumes such as the ypsili or certain fthores. To aid in the search, there are several scripts that attempt to extract only certain types of neumes. The scripts take the same arguments as the `create_dataset.py` script.

- `find_circles.py`: This script searches for circular neumes such as the diatonic fthores for PA, GA, DI, and KE, as well as sharps and flats.

- `find_ypsili.py`: This script searches for ypsili neumes.

## Training the model

To train the model, run the following commands.

```bash
python train.py
```

The resulting file will be called `current_model.pth`. Copy this file into `models/` to use it with `do_ocr.py`.

A log of the training process will be saved as `train_log.txt`. This log can be plotted with the following command.

```bash
python plot_training_metrics.py
```

### Goal

The goal of training is to maximize accuracy while minimizing loss.

#### What is accuracy and loss?

Accuracy is the percentage of neumes that are correctly predicted.

Loss is a measure of how far off the model's predictions are from the actual values. It's important to note that loss is not the same as the percentage of incorrect predictions. When the model makes a prediction, it also assigns a confidence level to that prediction. If the model makes an incorrect prediction with high confidence, the loss will be larger, reflecting the severity of the error.

## Q & A

### Why MobileNet v2?

MobileNet v2 was chosen as a compromise between accuracy and efficiency. Most users will probably not have a fast, GPU-enabled machine to run the OCR engine. MobileNet is designed to work on less powerful machines.

However, there is no barrier to using a different model. If anyone wants to experiment with more powerful models, such as ResNet, pull requests are welcome.
