# CellPhase: Whole-Cell Segmentation for Label-Free Quantitative Phase Imaging

CellPhase performs **whole-cell instance segmentation** in label-free **Quantitative Phase Imaging (QPI)**.  
Unlike nuclear-only segmentation methods, CellPhase accurately captures **full cell boundaries**, enabling measurements of **cell shape, growth, motility, and biophysical dynamics** without fluorescence or chemical staining.

---

## 🌐 Web Demo (No Installation Required)

**Try CellPhase instantly in your browser:**  
https://huggingface.co/spaces/Cellphase/cellphase_demo

This interactive demo allows you to:
- Upload your own phase / DPC / QPI images  
- Adjust segmentation parameters (diameter, flow threshold, etc.)  
- Visualize instance masks and cell boundaries directly  
- Export segmentation results for downstream analysis  

No installation, GPU, or command line needed.

---

## 📦 Python Installation
# Recommended Environment Setup (Conda)

To ensure a clean and reproducible setup, we recommend installing CellPhase inside a conda environment.
This prevents conflicts with system-level packages and ensures GPU libraries are properly recognized.

```
# Create a new environment (Python 3.9 or above recommended)
conda create -n cellphase_env python=3.10 -y

# Activate the environment
conda activate cellphase_env
```
Once the environment is active, install CellPhase:

```
pip install cellphase
```

If a GPU is available, CellPhase will automatically utilize it; otherwise, it will run on CPU.

---
# Tutorial with minimal example

## Parameter Exploration (Recommended First Step Using Jupyter Notebook)

Before performing large-scale segmentation, identify by visualizing an appropriate cell diameter and flow threshold for your specific imaging system and cell line.

```
from cellphase import run_cellphase_grid_search

fig = run_cellphase_grid_search(
    input_dir="test_images/",
    crop_size=None  # set to e.g., 256 to test segmentation on random crops
)
fig.show()
```
**Function Parameters**

| Parameter   | Type        | Description                                                                 |
|------------|-------------|-----------------------------------------------------------------------------|
| `input_dir` | `str`        | Directory containing representative test images.                            |
| `crop_size` | `int` or `None` | Optional. If set (e.g., `256`), segmentation is previewed on random crops—useful for very large images. |


## Batch Segmentation with Selected Parameters

After identifying suitable parameters, apply CellPhase to an entire image directory.

```
from cellphase import run_cellphase_batch_predict

run_cellphase_batch_predict(
    input_dir="test_images/",
    diameter=100,
    flow_threshold=0.4,
    num_images=5,
    visualize=True
)
```
**Function Parameters**

| Parameter        | Type              | Description                                                                                   |
|------------------|-------------------|-----------------------------------------------------------------------------------------------|
| `input_dir`      | `str`             | Directory containing input images (`.tif`, `.png`, `.jpg`, `.ome.tif`).                      |
| `diameter`       | `float` or `int`  | Approximate mean cell diameter in pixels.                                                     |
| `flow_threshold` | `float`           | Controls separation of touching cells (higher = stronger separation).                         |
| `num_images`     | `int` or `None`   | Number of images to process (`None` = process all).                                           |
| `visualize`      | `bool`            | Display segmentation overlays during processing if `True`.                                    |

Segmented instance masks are saved in the same directory as the original images.

## Exporting FIJI-Compatible Single-Cell ROIs
For downstream cell-level morphology analysis, you can export each segmented cell as a FIJI ROI.

```
from cellphase import run_cellphase_batch_predict_with_rois

run_cellphase_batch_predict_with_rois(
    input_dir="test_images/",
    diameter=100,
    flow_threshold=0.4,
    num_images=1
)
```
## Output Structure
```
image.png
image_pred.png
image_ROIs/
    cell_1.roi
    cell_2.roi
    cell_3.roi
    ...
```
These ROI files can be opened directly in Fiji → ROI Manager.

---

##  Citation
If you use CellPhase in your work, please consider citing:
```
@article{sengupta2025cellphase,
  title   = {CellPhase: An Open-Source Whole-Cell Segmentation Tool in Label-free Quantitative Phase Imaging},
  author  = {Sengupta, Sourya et al.},
  journal = {In preparation},
  year    = {2025}
}
```
---

## Acknowledgements

CellPhase 1.0 was developed and released by the **Center for Label-free Imaging and Multiscale Biophotonics**  
at the **Beckman Institute**, **University of Illinois Urbana-Champaign**.

This work is supported by the  
**National Institutes of Health / National Institute of Biomedical Imaging and Bioengineering (NIBIB)**  
**Award #: P41EB031772**.

---

## License
CellPhase is released under the MIT License:

```
MIT License

Copyright (c) 2025 CellPhase contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell  
copies of the Software, and to permit persons to whom the Software is  
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in  
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING  
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER  
DEALINGS IN THE SOFTWARE.
```
