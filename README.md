---
# For detailed documentation, see https://modelscope.cn/docs/%E5%88%9B%E7%A9%BA%E9%97%B4%E5%8D%A1%E7%89%87
domain: # Domain: cv/nlp/audio/multi-modal/AutoML
# - cv
tags: # Custom tags
-
datasets: # Associated datasets
  evaluation:
  #- iic/ICDAR13_HCTR_Dataset
  test:
  #- iic/MTWI
  train:
  #- iic/SIBR
models: # Associated models
#- iic/ofa_ocr-recognition_general_base_zh

## Startup file (If SDK is Gradio/Streamlit, default is app.py, if Static HTML, default is index.html)
deployspec:
  entry_file: app.py
license: Apache License 2.0
---
#### Clone with HTTP
```bash
 git clone https://www.modelscope.cn/studios/OhMyDearAI/hawarma-preview.git
```


This is an application for previewing the cooking game layout in HPMA (Harry Potter: Magic Awakened). Based on user input recipes, it outputs the layout of ingredients, cookers, and condiments for the cooking interface.

The program generates an ordered list from the 4 input recipes, passes them to corresponding functions, and gets result dictionaries for ingredients, cookers, and condiments, where keys are item names and values are position numbers. This data is organized and displayed as the result.

The results are displayed in two forms: one is JSON, and the other is a combined image (simulating the actual interface):
- On the left is the ingredients bar, where ingredients are arranged from left to right, bottom to top, with the order being the reverse of the selected recipe order (FILO), with a maximum of 2 elements per row;
- In the middle is the cookers bar, arranged from left to right, with a maximum of 4 elements;
- On the right is the condiments bar, where condiments are arranged from left to right, bottom to top, with the order being the same as the selected recipe order (FIFO), with a maximum of 2 elements per row. Each element is a PNG image with the corresponding name from the images directory.

If you need to add new recipes, you need to modify three parts:
- recipes.json: Add new recipe information
- translation.yaml: Add new recipe name translations
- images/: 创建一个recipe.slug的同名目录，目录下Add PNG files with the same name as the new recipe slug for recipe selection (355x355 or 395x395), add files named "order-{recipe.slug}.png" for result display (275x255). If there are new ingredients, add PNG files with the same name (107x107), which need to correspond to the names in recipes.json. 
新cookers和新condiments直接存放在images/目录下，方便复用。

If you modify the data structure of recipes.json, you also need to modify the corresponding parts of the Recipe class in app.py.
