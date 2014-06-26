'''
Some utility functions for pyoseo
'''

import importlib

def import_class(python_path):
    '''
    '''

    module_path, sep, class_name = python_path.rpartition('.')
    the_module = importlib.import_module(module_path)
    the_class = getattr(the_module, class_name)
    instance = the_class()
    return instance
