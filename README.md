DeepLIFT: Deep Learning Important FeaTures
===
An algorithm for computing importance scores of deep neural networks. [Paper](https://arxiv.org/abs/1605.01713)

##Installation

```
git clone https://github.com/kundajelab/deeplift.git #will clone the folder
pip install --editable deeplift/ #will install from the cloned folder. --editable means changes to the code will be picked up automatically.
```

DeepLIFT depends on theano (>= 0.8) and numpy (>= 1.9). It can also autoconvert keras models trained with keras 0.3. Support for keras 1.0 is in the works (on [this branch](https://github.com/kundajelab/deeplift/tree/keras_1_compatibility) started by @jisungk).

The recommended way to obtain theano and numpy is through [anaconda](https://www.continuum.io/downloads).