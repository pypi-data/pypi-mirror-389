"""
Generative AI workflow functions
"""

from typing import Union

def _recursive_convert_to_dict(obj):
    if hasattr(obj, '__dict__'):
        # Recursively convert the __dict__ values
        return {k: _recursive_convert_to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: _recursive_convert_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_recursive_convert_to_dict(item) for item in obj]
    elif isinstance(obj, bytes):
        # Handle bytes objects (common in image responses)
        return obj.decode('utf-8', errors='ignore')
    else:
        # For primitives and other objects, just return as-is
        return obj
    
def _recursive_keep_keys(obj, keep_keys: list[str]):
    if hasattr(obj, '__dict__'):
        return {k: _recursive_keep_keys(v, keep_keys) 
                for k, v in obj.__dict__.items() if k in keep_keys}
    elif isinstance(obj, dict):
        return {k: _recursive_keep_keys(v, keep_keys) 
                for k, v in obj.items() if k in keep_keys}
    elif isinstance(obj, list):
        return [_recursive_keep_keys(item, keep_keys) for item in obj]
    else:
        return obj
    
def convert_response_to_dict(response, keep_keys: list[str]=None):
    """
    Convert a generative AI response to a dictionary.
    
    Args:
        response: The response from a generative AI model.
        keep_keys: The keys to keep in the dictionary.
    
    Returns:
        A dictionary of the response.
    """
    
    response_dict = _recursive_convert_to_dict(response)
    
    if keep_keys is not None:
        response_dict = _recursive_keep_keys(response_dict, keep_keys)

    return response_dict

def gather_image_from_generative_ai(response, image_key: Union[str, list[str], None]=None, 
                                    image_type: Union[str, list[str]]=None,
                                    output_format='png', output_path=None, max_search_depth=3):
    """
    Gather an image from a generative AI response.
    
    Args:
        response: The response from a generative AI model.
        image_key: The key of the image in the response.
        image_type: The type of image to gather.
        output_format: The format of the output image.
        output_path: The path to save the output image.
        max_search_depth: The maximum depth to search for the image in the response.
    
    If image_key is not provided, the function will walk through the keys of the response to find the image.
    If image_type is not provided, the function will look for different image types (e.g. URL, base64).
    
    """
    raise NotImplementedError("gather_image_from_generative_ai not yet implemented.")