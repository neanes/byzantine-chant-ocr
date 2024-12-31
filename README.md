# Byzantine Chant OCR

This project is a toolset for performing optical character recognition (OCR) on Byzantine chant notation. It can process both PDFs and image files. Built in Python, the toolset uses OpenCV for image processing, PyTorch for deep learning, and a MobileNetV2 convolutional neural network (CNN) model for feature extraction and classification.

## How-to

This guide assumes some familiarity with the command line.

### Get the source

Install [git](https://git-scm.com/downloads), and then clone the repository.

```bash
git clone https://github.com/neanes/byzantine-ocr
```

### Install dependencies

1. Install [Python](https://www.python.org/downloads/). The scripts were developed and tested with Python `3.12`, but the latest version will probably work, too.
2. If you are already familiar with Python and use it for other tasks, then it is recommended that you create a [virtual environment](https://docs.python.org/3/library/venv.html). If you do not know what this means, or do not intend to you use Python for anything other than these scripts, you may skip this step.
3. Install the required Python libraries via `pip install -r requirements.txt`.

### Download the model

Download the latest model from the [Releases](https://github.com/neanes/byzantine-chant-ocr/releases/tag/latest) page. The file is called `current_model.pth`. Save this file to `models/`.

### Perform OCR on a file

> [!NOTE]  
> If you are using Windows, the command to run Python may be `py` instead of `python`.

Below are the commands that can be used to perform OCR on images and PDFs. The resulting output will be a file called `output.yaml`. This file lists the line number, coordinates, and size of each contour found in the files, as well as the model's prediction (e.g. `ison`, `oligon`, etc.).

To learn how to use this file, see the next section.

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

### Import into Neanes

The resulting `output.yaml` can be imported into [Neanes](https://github.com/neanes/neanes) using the import script found in `integrations/neanes`.

First, install the LTS version of [Node.js](https://nodejs.org/en/download).

Next, copy `output.yaml` to `integrations/neanes` and run the following commands.

```bash
cd integrations/neanes
corepack enable npm # only needed the first time you run the importer
npm install # only needed the first time you run the importer
npm run start
```

This will convert `output.yaml` into a Neanes file called `output.byzx`.

Eventually, it will be possible to import directly into Neanes by opening the YAML file within Neanes. However, the import script is still under heavy development. Once the script stabilizes, it will be moved into Neanes.

### The Neanes file is not as accurate as I would have hoped. What can I do?

It is generally expected that the OCR result will be at least 90% accurate for most common cases. You can use the martyria as a guide for finding and correcting errors. That is, if a martyria is not the expected value, then there must be an issue somewhere between the incorrect martyria and the last correct martyria.

If the resulting file is not sufficiently accurate, there are three possible causes.

1. The image or PDF file is not clear, or is tilted. Eventually the OCR engine will be updated to correct misaligned images.
2. There is a bug or inefficiency with the Neanes importer.
3. The model needs more training.

If the font used for the neumes is significantly different from [the fonts that the model was trained with](./SOURCES.md), then the results will be less accurate. If you want to help make the model better, see the [contribution guide](./CONTRIBUTING.md). The maintainers of this repository will likely priortize training the model on fonts that are the most common and that will impact the most users. But if you want to train on a more obscure font or on handwritten works, pull requests are welcome.

If the image contains a lot of extraneous text that is not part of the lyrics, but that is also close to the neumes, the text removal process may fail to remove this text before performing OCR. In this case, the text may be misinterpreted as neumes belonging to the closest baseline. You can manually remove the text yourself from the image and try again.

If the YAML output is accurate, but the Neanes file is not, then this is possibly and issue with the Neanes importer and should be reported as such.

## License

This project is licensed under the [GNU General Public License, version 3](./LICENSE).
