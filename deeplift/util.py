from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import sys
import os
import os.path
import numpy as np
from collections import namedtuple
from collections import OrderedDict
import json
import deeplift

NEAR_ZERO_THRESHOLD = 10**(-7)

def enum(**enums):
    class Enum(object):
        pass
    to_return = Enum;
    for key,val in enums.items():
        if hasattr(val, '__call__'): 
            setattr(to_return, key, staticmethod(val))
        else:
            setattr(to_return,key,val);
    to_return.vals = [x for x in enums.values()];
    to_return.the_dict = enums
    return to_return;


def assert_is_type(instance, the_class, instance_var_name):
    if (not superclass_in_base_classes(
             instance.__class__.__bases__, the_class)):
        raise RuntimeError(instance_var_name+" should be an instance of "
                +the_class.__name__+" but is "+str(instance.__class__)); 
    return True


def superclass_in_base_classes(base_classes, the_class):
    """
        recursively determine if the_class is among or is a superclass of
         one of the classes in base_classes. The comparison is done by
         name so that even if reload is called on a module, this still
         works.
    """
    for base_class in base_classes:
        if base_class.__name__ == the_class.__name__:
            return True 
        else:
            #if the base class in turn has base classes of its own
            if len(base_class.__bases__)!=1 or\
                base_class.__bases__[0].__name__ != 'object':
                #check them. If there's a hit, return True
                if (superclass_in_base_classes(
                    base_classes=base_class.__bases__,
                    the_class=the_class)):
                    return True
    #if 'True' was not returned in the code above, that means we don't
    #have a superclass
    return False


def run_function_in_batches(func,
                            input_data_list,
                            batch_size=10,
                            progress_update=1000):
    #func has a return value such that the first index is the
    #batch. This function will run func in batches on the inputData
    #and will extend the result into one big list.
    assert isinstance(input_data_list, list), "input_data_list must be a list"
    #input_datas is an array of the different input_data modes.
    to_return = [];
    i = 0;
    while i < len(input_data_list[0]):
        if (progress_update is not None):
            if (i%progress_update == 0):
                print("Done",i)
        to_return.extend(func(*[x[i:i+batch_size] for x in input_data_list]));
        i += batch_size;
    return to_return


def mean_normalise_weights_for_sequence_convolution(weights,
                                                    bias,
                                                    normalise_across_rows,
                                                    weightsHeight=4):
    #weights: outputchannels, inputChannels, windowDims
    assert len(weights.shape)==4
    assert weights.shape[1]==1, weights.shape
    axis_for_normalisation = 2 if normalise_across_rows else 3
    if (normalise_across_rows):
        assert weights.shape[axis_for_normalisation]==\
         weightsHeight, weights.shape
    else:
        assert weights.shape[axis_for_normalisation]==\
         weightsHeight, weights.shape
        
    mean_weights_at_positions=np.mean(weights,axis=axis_for_normalisation)
    new_bias = bias + np.sum(np.sum(mean_weights_at_positions,
                                    axis=2),axis=1)
    if (normalise_across_rows):
        mean_weights_at_positions=mean_weights_at_positions[:,:,None,:]
    else:
        mean_weights_at_positions=mean_weights_at_positions[:,:,:,None]
    renormalised_weights=weights-mean_weights_at_positions
    return renormalised_weights, new_bias


def mean_normalise_rnn_weights(weights, bias):
    assert len(weights.shape)==2
    assert weights.shape[0]==4
    mean_per_unit = np.mean(weights, axis=0) 
    new_weights = weights-mean_per_unit[None,:]
    new_bias = bias + mean_per_unit
    return new_weights, new_bias


def get_mean_normalised_softmax_weights(weights, biases):
    new_weights = weights - np.mean(weights, axis=1)[:,None]
    new_biases = biases - np.mean(biases)
    return new_weights, new_biases


def get_effective_width_and_stride(widths,strides):
    effectiveStride = strides[0] 
    effectiveWidth = widths[0]
    assert len(strides)==len(widths)
    if len(strides)>1:
        for (stride, width) in zip(strides[1:],widths[1:]):
            effectiveWidth = ((width-1)*effectiveStride)+effectiveWidth 
            effectiveStride = effectiveStride*stride
    return effectiveWidth, effectiveStride


def get_lengthwise_widths_and_strides(layers):
    """
        layers: a list of convolutional/pooling blobs
    """
    import deeplift.blobs
    widths = [] 
    strides = []
    for layer in layers:
        if type(layer).__name__ == "Conv2D":
            strides.append(layer.strides[1]) 
            widths.append(layer.W.shape[3])
        elif isinstance(layer, deeplift.blobs.Activation):
            pass
        else:
            raise RuntimeError("Please implement how to extract width and"
                               "stride from layer of type: "
                               +type(layer).__name__)
    return widths, strides


def get_lengthwise_effective_width_and_stride(layers):
    widths, strides = get_lengthwise_widths_and_strides(layers)
    return get_effective_width_and_stride(widths, strides)


def load_yaml_data_from_file(file_name):
    file_handle = get_file_handle(file_name)
    data = yaml.load(file_handle) 
    file_handle.close()
    return data


def get_file_handle(file_name, mode='r'):
    use_gzip_open = False
    #if want to read from file, check that is gzipped and set
    #use_gzip_open to True if it is 
    if (mode=="r" or mode=="rb"):
        if (is_gzipped(file_name)):
            mode="rb"
            use_gzip_open = True
    #Also check if gz or gzip is in the name, and use gzip open
    #if writing to the file.
    if (re.search('.gz$',filename) or re.search('.gzip',filename)):
        #check for the case where the file name implies the file
        #is gzipped, but the file is not actually detected as gzipped,
        #and warn the user accordingly
        if (mode=="r" or mode=="rb"):
            if (use_gzip_open==False):
                print("Warning: file has gz or gzip in name, but was not"
                      " detected as gzipped")
        if (mode=="w"):
            use_gzip_open = True
            #I think write will actually append if the file already
            #exists...so you want to remove it if it exists
            if os.path.isfile(file_name):
                os.remove(file_name)
    if (use_gzip_open):
        return gzip.open(file_name,mode)
    else:
        return open(file_name,mode) 


def is_gzipped(file_name):
    file_handle = open(file_name, 'rb')
    magic_number = file_handle.read(2)
    file_handle.close()
    is_gzipped = (magic_number == b'\x1f\x8b' )
    return is_gzipped


def apply_softmax_normalization_if_needed(layer, previous_layer):
    if (type(layer)==deeplift.blobs.Softmax):
        #mean normalise the inputs to the softmax
        previous_layer.W, previous_layer.b =\
         deeplift.util.get_mean_normalised_softmax_weights(
            previous_layer.W, previous_layer.b)


def connect_list_of_layers(deeplift_layers):
    if (len(deeplift_layers) > 1):
        #string the layers together so that subsequent layers take the previous
        #layer as input
        last_layer_processed = deeplift_layers[0] 
        for layer in deeplift_layers[1:]:
            apply_softmax_normalization_if_needed(layer, last_layer_processed)
            layer.set_inputs(last_layer_processed)
            last_layer_processed = layer


def format_json_dump(json_data, indent=2):
    return json.dumps(jsonData, indent=indent, separators=(',', ': ')) 