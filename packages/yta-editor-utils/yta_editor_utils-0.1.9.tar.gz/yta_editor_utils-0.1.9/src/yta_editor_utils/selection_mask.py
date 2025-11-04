"""
A selection mask is a numpy array or a texture that
indicates where we should apply the changes from
the processed input in the original input, and also
how much we have todo.

A selection mask that is fulfilled with all ones will
make the output be the processed input, but one with
all zeros will keep the original input as not modified.

(!) If a moderngl texture is detected as the input this
will trigger the detector to raise an Exception if the
library is not installed and it cannot be processed.
"""
from yta_editor_utils.texture import TextureUtils
from yta_validation.parameter import ParameterValidator
from yta_numpy.utils import NumpyUtils
from yta_programming.decorators.requires_dependency import requires_dependency
from typing import Union

import numpy as np


"""
Here we handle the dtypes as strings that
are accepted by opengl ('f4' for 'float32', 'u1'
for 'uint8') where f means float and 4 means
4 * 8 = 32
"""
class _TextureSelectionMaskGenerator:
    """
    *For internal use only*

    Class to be used as a shortcut within the general
    selection mask generator, to simplify the way we
    create selection masks as moderngl textures.
    """

    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_full_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get a full mask (all values are 1.0) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_full_mask_for_input(
                input = input,
                dtype = dtype
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )

    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_full_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get a full mask (all values are 1.0) of the
        provided `width` and `height` given, and the
        `dtype` provided, ready to be used in an
        OpenGL shader.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_full_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_half_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get a half mask (all values are 0.5) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_half_mask_for_input(
                input = input,
                dtype = dtype
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_half_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*
        
        Get a half mask (all values are 0.5) of the
        provided `width` and `height` given, and the
        `dtype` provided, ready to be used in an
        OpenGL shader.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_half_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_empty_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get an empty mask (all values are 0.0) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_empty_mask_for_input(
                input = input,
                dtype = dtype
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_empty_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get an empty mask (all values are 0.0) of the
        provided `width` and `height` given, and the
        `dtype` provided, ready to be used in an
        OpenGL shader.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_empty_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_random_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get a random mask (all values are random values
        in the range [0.0, 1.0]) that fits the
        dimensions and properties of the `input` provided,
        returning it with the given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_random_mask_for_input(
                input = input,
                dtype = dtype
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )

    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_random_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get a random mask (all values are random values
        in the range [0.0, 1.0]) of the provided `width`
        and `height` given, and the `dtype` provided,
        ready to be used in an OpenGL shader.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_random_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_custom_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
        value: float = 0.75,
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get a custom mask (all values are the provided
        `value`, that must be a value in the [0.0, 1.0]
        range) that fits the dimensions and properties
        of the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_custom_mask_for_input(
                input = input,
                dtype = dtype,
                value = value
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def get_custom_mask(
        width: int,
        height: int,
        dtype: str = 'f1',
        value: float = 0.75,
        opengl_context: Union['moderngl.Context', None] = None
    ) -> 'moderngl.Texture':
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Get a custom mask (all values are the provided
        `value`, that must be a value in the [0.0, 1.0]
        range) of the provided `width` and `height` and
        the `dtype` provided.
        """
        return TextureUtils.numpy_to_texture(
            input = _NumpySelectionMaskGenerator.get_custom_mask(
                width = width,
                height = height,
                number_of_channels = 4,
                dtype = dtype,
                value = value
            ),
            opengl_context = opengl_context,
            dtype = dtype
        )


"""
TODO: I think this module is very similar to the 
`yta-numpy` library we have.
"""
class _NumpySelectionMaskGenerator:
    """
    *For internal use only*

    Class to be used as a shortcut within the general
    selection mask generator, to simplify the way we
    create seletion masks as numpy arrays.
    """

    @staticmethod
    def get_full_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
    ) -> 'np.ndarray':
        """
        Get a full mask (all values are 1.0) that fits
        the dimensions and properties of the `input`
        provided, returning it with the given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        width, height, number_of_channels = TextureUtils.get_size_and_number_of_channels_from_texture(input)

        return _NumpySelectionMaskGenerator.get_full_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype
        )
    
    @staticmethod
    def get_full_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1'
    ) -> 'np.ndarray':
        """
        Get a full mask (all values are 1.0) of the
        provided `width` and `height`, also with the
        `number_of_channels` given, and the `dtype`
        provided.

        These are the values according to the `dtype`
        provided:
        - `f1 (np.uint8)` -> `255`
        - `u1 (np.uint8)` -> `255`
        - `f4 (np.float32)` -> `1.0`
        """
        dtype = TextureUtils.texture_dtype_to_numpy_dtype(dtype)

        return NumpyUtils.generator.max(
            shape = (height, width, number_of_channels),
            dtype = dtype
        )
    
    @staticmethod
    def get_half_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
    ) -> 'np.ndarray':
        """
        Get a half mask (all values are 0.5) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.

        These are the values according to the `dtype`
        provided:
        - `f1 (np.uint8)` -> `127`
        - `u1 (np.uint8)` -> `127`
        - `f4 (np.float32)` -> `0.5`
        """
        width, height, number_of_channels = TextureUtils.get_size_and_number_of_channels_from_texture(input)

        return _NumpySelectionMaskGenerator.get_half_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype
        )
    
    @staticmethod
    def get_half_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1'
    ) -> 'np.ndarray':
        """
        Get a half mask (all values are 0.5) of the
        provided `width` and `height`, also with the
        `number_of_channels` given, and the `dtype`
        provided.
        """
        return _NumpySelectionMaskGenerator.get_custom_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype,
            value = 0.5
        )
    
    @staticmethod
    def get_empty_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
    ) -> 'np.ndarray':
        """
        Get an empty mask (all values are 0.0) for the
        that fits the dimensions and properties of
        the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        width, height, number_of_channels = TextureUtils.get_size_and_number_of_channels_from_texture(input)

        return _NumpySelectionMaskGenerator.get_empty_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype
        )
    
    @staticmethod
    def get_empty_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1'
    ) -> 'np.ndarray':
        """
        Get an empty mask (all values are 0.0) of the
        provided `width` and `height`, also with the
        `number_of_channels` given, and the `dtype`
        provided.

        These are the values according to the `dtype`
        provided:
        - `f1 (np.uint8)` -> `0`
        - `u1 (np.uint8)` -> `0`
        - `f4 (np.float32)` -> `0.0`
        """
        return np.zeros(
            shape = (height, width, number_of_channels),
            dtype = TextureUtils.texture_dtype_to_numpy_dtype(dtype)
        )
    
    @staticmethod
    def get_random_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
    ) -> 'np.ndarray':
        """
        Get a random mask (all values are random
        values in the range [0.0, 1.0]) that fits
        the dimensions and properties of the `input`
        provided, returning it with the given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        width, height, number_of_channels = TextureUtils.get_size_and_number_of_channels_from_texture(input)

        return _NumpySelectionMaskGenerator.get_random_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype
        )

    @staticmethod
    def get_random_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1'
    ) -> 'np.ndarray':
        """
        Get a full mask (all values are random values
        in the range [0.0, 1.0]) of the provided `width`
        and `height`, also with the `number_of_channels`
        given, and the `dtype` provided.

        These are the value ranges according to the
        `dtype` provided:
        - `f1 (np.uint8)` -> `[0, 255]`
        - `u1 (np.uint8)` -> `[0, 255]`
        - `f4 (np.float32)` -> `[0.0, 1.0]`
        """
        dtype = TextureUtils.texture_dtype_to_numpy_dtype(dtype)

        return NumpyUtils.generator.random(
            shape = (height, width, number_of_channels),
            dtype = dtype
        )

    @staticmethod
    def get_custom_mask_for_input(
        input: Union['moderngl.Texture', np.ndarray],
        dtype: str = 'f1',
        value: float = 0.75
    ) -> 'np.ndarray':
        """
        Get a custom mask (all values are the provided
        `value`, that must be a value in the [0.0, 1.0]
        range) that fits the dimensions and properties
        of the `input` provided, returning it with the
        given `dtype`.

        The `input` can be a numpy array or an opengl
        texture.
        """
        width, height, number_of_channels = TextureUtils.get_size_and_number_of_channels_from_texture(input)

        return _NumpySelectionMaskGenerator.get_custom_mask(
            width = width,
            height = height,
            number_of_channels = number_of_channels,
            dtype = dtype,
            value = value
        )

    @staticmethod
    def get_custom_mask(
        width: int,
        height: int,
        number_of_channels: int,
        dtype: str = 'f1',
        value: float = 0.75
    ) -> 'np.ndarray':
        """
        Get a custom mask (all values are the provided
        `value`, that must be a value in the [0.0, 1.0]
        range) of the provided `width` and `height`, also
        with the `number_of_channels` given, and the
        `dtype` provided.

        These are the values according to the `dtype`
        provided:
        - `f1 (np.uint8)` -> `value * 255`
        - `u1 (np.uint8)` -> `value * 255`
        - `f4 (np.float32)` -> `value`
        """
        ParameterValidator.validate_mandatory_number_between('value', value, 0.0, 1.0)

        dtype = TextureUtils.texture_dtype_to_numpy_dtype(dtype)

        return NumpyUtils.generator.custom(
            shape = (height, width, number_of_channels),
            dtype = dtype,
            value = value
        )
    
class SelectionMaskGenerator:
    """
    *Class to be used as a static class*
    
    Class to simplify the way we generate selection
    masks, to be used when handling selection mask
    for CPU or GPU processing.
    """

    texture: _TextureSelectionMaskGenerator = _TextureSelectionMaskGenerator
    """
    Shortcut to the generation of the moderngl textures
    selection masks.
    """
    numpy: _NumpySelectionMaskGenerator = _NumpySelectionMaskGenerator
    """
    Shortcut to the generation of numpy arrays as 
    selection masks.
    """
    utils: TextureUtils = TextureUtils
    """
    Shortcut to the utils related to selection masks.
    """
    


