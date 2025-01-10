# Byzantine Chant OCR

This project is a toolset for performing optical character recognition (OCR) on Byzantine chant notation. It can process both PDFs and image files. Built in Python, the toolset uses OpenCV for image processing, PyTorch for deep learning, and a MobileNetV2 convolutional neural network (CNN) model for feature extraction and classification.

## How-to

### Download the app

Download the latest app version from the [Releases page](https://github.com/neanes/byzantine-chant-ocr/releases). Unzip the files to any directory.

### Download the model

Download the latest model from the [Releases page](https://github.com/neanes/byzantine-chant-ocr/releases). Copy the files `current_model.onnx` and `metadata.json` to the same folder where the executable is located.

### Run the app

Run the app and select a file to perform OCR on. For PDF files, input a page range. Then press Go and choose a location to save the file.

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

1. The image or PDF file is not clear, or contains a severe tilt or non-linear distortions (e.g. a picture of a curved page).
2. There is a bug or inefficiency with the Neanes importer.
3. The model needs more training.

If the font used for the neumes is significantly different from [the fonts that the model was trained with](./SOURCES.md), then the results will be less accurate. If you want to help make the model better, see the [contribution guide](./CONTRIBUTING.md). The maintainers of this repository will likely priortize training the model on fonts that are the most common and that will impact the most users. But if you want to train on a more obscure font or on handwritten works, pull requests are welcome.

If the image contains a lot of extraneous text that is not part of the lyrics, but that is also close to the neumes, the text removal process may fail to remove this text before performing OCR. In this case, the text may be misinterpreted as neumes belonging to the closest baseline. You can manually remove the text yourself from the image and try again.

If the YAML output is accurate, but the Neanes file is not, then this is possibly and issue with the Neanes importer and should be reported as such.

## License

This project is licensed under the [GNU General Public License, version 3](./LICENSE).

## Acknowledgements

This project was inspired by and builds upon concepts from the following paper:

C. Dalitz, G.K. Michalakis, C. Pranzas: _[Optical Recognition of Psaltic Byzantine Chant Notation](https://lionel.kr.hs-niederrhein.de/~dalitz/data/publications/ijdar-psaltiki.pdf)_. International Journal of Document Analysis and Recognition, vol. 11, no. 3, pp. 143-158 (2008)
