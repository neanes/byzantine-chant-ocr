# Contributing

## Get the source

Install [git](https://git-scm.com/downloads), and then clone the repository.

```bash
git clone https://github.com/neanes/byzantine-chant-ocr.git
```

## Install dependencies

1. Install [Python 3.12](https://www.python.org/downloads/).
2. If you are already familiar with Python and use it for other tasks, then it is recommended that you create a [virtual environment](https://docs.python.org/3/library/venv.html). If you do not know what this means, or do not intend to you use Python for anything other than these scripts, you may skip this step.
3. Install the required Python libraries via `pip install -r requirements-dev.txt`.

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

### Viewing Dataset Metrics

You can view the number of images per class via the following scripts.

- `plot_dataset_metrics_by_source.py`: Use this to see the distribution of images broken up by each source.
- `plot_dataset_metrics_for_source.py`: Use this to view the total number of images in each class for a single source only.
- `plot_dataset_metrics.py`: Use this to view the total number of images in each class, regardless of source.

## Training the Model

To train the model, run the following commands.

```bash
python train.py
```

This script splits the monolithic dataset into training, validation and test datasets using a 70/15/15 percent ratio.

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

## Converting the Model to ONNX

The main OCR engine does not use PyTorch directly, but rather uses an ONNX model. The main motivation for this is that the PyTorch library is quite large and would bloat the native binaries created by PyInstaller. The ONNX runtime, on the other hand, is comparatively lightweight.

To convert the model from PyTorch's format to ONNX, use the following command.

```bash
python convert_to_onnx.py
```

By default, this will convert `models/current_model.pth` into `models/current_model.onnx`.

## Testing the Model

To test the model against a portion of the dataset, use the following command.

```bash
python test.py
```

This command will show you the accuracy and loss for the test, as well as a JSON formatted list of incorrect predictions.

## Perform OCR on a file

Below are the commands that can be used to perform OCR on images and PDFs. The resulting output will be a file called `output.yaml`. This file lists the line number, coordinates, and size of each contour found in the files, as well as the model's prediction (e.g. `ison`, `oligon`, etc.).

#### Images

```bash
cd scripts
python do_ocr.py image.png
```

#### PDFs

The following command performs OCR on page 123 of `doc.pdf`.

##### Single page

```bash
cd scripts
python do_ocr.py doc.pdf 123
```

##### Multiple pages

The following command performs OCR on pages 100-105 of `doc.pdf`.

```bash
cd scripts
python do_ocr.py doc.pdf 100 105
```

## End-to-End (E2E) Testing

To run the E2E tests, make sure you are in your Python virtual environment (if you are using one), and go to the `e2e` directory. Before running the tests the first time, you must first run

```bash
npm install
```

After that, run the tests with the following command.

```bash
npm test
```

In addition to the standard jest report, these tests will also generate a file called `OcrImporter.report.json`, which contain more detailed results.

### What do the tests do?

The `e2e/data` folder contains images of pages from Byzantine chant publications, as well as a Neanes file that matches the image. The tests loop over these pages and does the following for each page.

1. Runs the OCR engine on the page.
2. Generates a Neanes file from the OCR output.
3. Compare the generated Neanes file with the expected Neanes file found in the `e2e/data` folder.

Comparison uses the [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance) as metric of correctness. This currently only takes into account the similarity in the sequence of quantitative neumes. It does not consider gorgons, fthores, qualitative neumes, etc. The threshold to pass is set at 90% similarity, as of the writing of this document.

## Q & A

### Why MobileNetV2?

MobileNetV2 was chosen as a compromise between accuracy and efficiency. Most users will probably not have a fast, GPU-enabled machine to run the OCR engine. MobileNet is designed to work on less powerful machines.

However, there is no barrier to using a different model. If anyone wants to experiment with more powerful models, such as ResNet, pull requests are welcome.
