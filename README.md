---
# 详细文档见https://modelscope.cn/docs/%E5%88%9B%E7%A9%BA%E9%97%B4%E5%8D%A1%E7%89%87
domain: #领域：cv/nlp/audio/multi-modal/AutoML
# - cv
tags: #自定义标签
-
datasets: #关联数据集
  evaluation:
  #- iic/ICDAR13_HCTR_Dataset
  test:
  #- iic/MTWI
  train:
  #- iic/SIBR
models: #关联模型
#- iic/ofa_ocr-recognition_general_base_zh

## 启动文件(若SDK为Gradio/Streamlit，默认为app.py, 若为Static HTML, 默认为index.html)
deployspec:
  entry_file: app.py
license: Apache License 2.0
---
#### Clone with HTTP
```bash
 git clone https://www.modelscope.cn/studios/OhMyDearAI/hawarma-preview.git
```


这是一个用于预览HPMA(Harry Potter: Magic Awakened)中的烹饪游戏的布局的应用，根据用户输入的食谱，输出烹饪界面的食材、厨具、调味品的布局。

程序根据输入将输入的4个菜谱生成一个有序列表，输入相应的函数，得到食材、厨具、调味品的结果字典，键为物品名称，值为位置序号。这些数据被整理后作为结果被展示。

结果用两种形式展示，一种是json（以实现），另一种是图片组合（模拟真实界面）：左侧是ingredients栏，顺序为从左到右，从下到上排列，每行最多2个元素；中间是cooker栏，从左到右排列，最多4个元素；右侧是condiments栏，顺序为从左到右，从下到上排列，每行最多2个元素。每个元素是images目录下对应名称的一张png图片。
Ingredients will be on the left (2/row, bottom-to-top), cookware in the center (max 4, left-to-right), and condiments on the right (2/row, bottom-to-top), with all images sourced  from the images/ directory.