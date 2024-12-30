# Byzantine Chant OCR

This project is a collection of Python scripts that perform optical character recognition of Byzantine chant. It can process either PDFs or images.

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

### Train the model

> [!NOTE]  
> If you are using Windows, the command to run Python may be `py` instead of `python`.

The model is not currently included in the repository. Once the model is more stable, it will be made available either as a Github release, or committed to this repo.

To build the model, run the following commands.

```bash
cd scripts
python train.py
```

This will take some time, so be patient. Once the script completes, a file called `current_model.pth` will be created. Copy this file to `models/`.

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

## License

This project is licensed under the [GNU General Public License, version 3](./LICENSE).
