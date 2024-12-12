import torch
import torch.nn as nn
import torchvision.models as models

pth_file_path = "mobilenetv2_with_augmentation_32.pth"
onnx_file_path = "mobilenetv2_with_augmentation_32.onnx"

model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
num_features = model.last_channel  # Get the size of the last layer
model.classifier[1] = nn.Linear(num_features, 54)  # Replace classifier

model.load_state_dict(torch.load(pth_file_path))
model.eval()

size = 224
dummy_input = torch.randn(1, 3, size, size)

torch.onnx.export(
    model,
    dummy_input,
    onnx_file_path,
    export_params=True,  # Store the trained parameters in the model file
    opset_version=11,  # ONNX version to use (11 is commonly supported)
    input_names=["input"],  # Name of input layer(s)
    output_names=["output"],  # Name of output layer(s)
    dynamic_axes={
        "input": {0: "batch_size", 2: "height", 3: "width"},
    },
)
