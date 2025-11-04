"""
By now we are only accepting these values:
- Texture dtypes: `f1`
- Numpy dtypes: `np.uint8, np.float32`
"""
from yta_programming.decorators.requires_dependency import requires_dependency
from yta_numpy.converter import NumpyConverter
from yta_validation import PythonValidator
from yta_validation.parameter import ParameterValidator
from typing import Union

import numpy as np


class TextureUtils:
    """
    *Class to be used as a static class*

    Class to wrap some functionalities related to
    textures, numpy arrays and conversions.

    We only accept `np.uint8`, `np.float32` and the
    `f1` moderngl dtype.
    """

    ACCEPTED_TEXTURE_DTYPES = ['f1']
    """
    The texture dtypes we accept in our system. Any
    other type received will raise an Exception.
    """
    ACCEPTED_NUMPY_DTYPES = ['uint8', 'float32']
    """
    The numpy dtypes we accept in our system. Any
    other type received will raise an Exception.
    """
    TEXTURE_DTYPE_TO_NUMPY_DTYPE = {
        'f1': 'uint8'
    }
    """
    The conversion table from texture dtype to the
    numpy dtype.
    """
    NUMPY_DTYPE_TO_TEXTURE_DTYPE = {
        'uint8': 'f1'
    }
    """
    The conversion table from numpy dtype to the
    texture dtype.
    """

    @staticmethod
    def get_size_and_number_of_channels_from_texture(
        texture: Union['moderngl.Texture', np.ndarray]
    ) -> tuple[int, int]:
        """
        Get the size and the number of channels of the provided
        `texture` as (width, height, number_of_channels).
        """
        return (
            TextureUtils._get_size_and_number_of_channels_from_numpy_texture(texture)
            if PythonValidator.is_numpy_array(texture) else
            TextureUtils._get_size_and_number_of_channels_from_moderngl_texture(texture)
        )
    
    @staticmethod
    def _get_size_and_number_of_channels_from_moderngl_texture(
        texture: 'moderngl.Texture'
    ) -> tuple[int, int, int]:
        """
        *Optional `moderngl` library (imported as `moderngl`) required*

        Get the size and the number of channels of the
        provided moderngl `texture` as (width, height,
        number_of_channels).
        """
        return (
            *TextureUtils._get_size_from_moderngl_texture(texture),
            TextureUtils._get_number_of_channels_from_moderngl_texture(texture)
        )
    
    @staticmethod
    def _get_size_and_number_of_channels_from_numpy_texture(
        texture: np.ndarray
    ) -> tuple[int, int, int]:
        """
        Get the size and the number of channels of the
        provided numpy `texture` as (width, height,
        number_of_channels).
        """
        return (
            *TextureUtils._get_size_from_numpy_texture(texture),
            TextureUtils._get_number_of_channels_from_numpy_texture(texture)
        )
    
    @staticmethod
    def get_size_from_texture(
        texture: Union['moderngl.Texture', np.ndarray]
    ) -> tuple[int, int]:
        """
        Get the size as (width, height) of the provided
        `texture`.
        """
        return (
            TextureUtils._get_size_from_numpy_texture(texture)
            if PythonValidator.is_numpy_array(texture) else
            TextureUtils._get_size_from_moderngl_texture(texture)
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def _get_size_from_moderngl_texture(
        texture: 'moderngl.Texture'
    ) -> tuple[int, int]:
        """
        *Optional `moderngl` library (imported as `moderngl`) required*

        Get the size as (width, height) of the provided
        moderngl `texture`.
        """
        return texture.size

    @staticmethod
    def _get_size_from_numpy_texture(
        texture: np.ndarray
    ) -> tuple[int, int]:
        """
        Get the size as (width, height) of the provided
        numpy `texture`.
        """
        return (
            # Remember that moderngl stores the numpy array in
            # h,w so we need to transform
            texture.shape[1],
            texture.shape[0]
        )
    
    @staticmethod
    def get_number_of_channels_from_texture(
        texture: Union['moderngl.Texture', np.ndarray]
    ) -> tuple[int, int]:
        """
        Get the number of channels of the provided `texture`.
        """
        return (
            TextureUtils._get_number_of_channels_from_numpy_texture(texture)
            if PythonValidator.is_numpy_array(texture) else
            TextureUtils._get_number_of_channels_from_moderngl_texture(texture)
        )

    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def _get_number_of_channels_from_moderngl_texture(
        texture: 'moderngl.Texture'
    ) -> int:
        """
        *For internal use only*

        Get the number of channels of the provided moderngl
        `texture`.
        """
        return texture.components

    @staticmethod
    def _get_number_of_channels_from_numpy_texture(
        texture: np.ndarray
    ) -> int:
        """
        *For internal use only*

        Get the number of channels of the provided numpy
        `texture`.
        """
        return (
            texture.shape[2]
            if texture.ndim == 3 else
            1
        )
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def numpy_to_texture(
        input: np.ndarray,
        opengl_context: Union['moderngl.Context', None],
        dtype: str = 'f1'
        # TODO: This below is for the pyav frame
        # numpy_format: str = 'rgb24'
    ) -> 'moderngl.Texture':
        """
        *Optional `moderngl` library (imported as `moderngl`) required*

        Transform the provided `input` numpy array into
        a moderngl texture, by using the `opengl_context`
        provided, and adding the NEAREST filter by default.

        (!) This method is useful to transform a
        frame into a texture quick and for a single
        use, but we have the GPUTextureHandler class
        to handle it in an specific contexto to 
        optimize the performance and avoid creating
        textures but rewriting on them.
        """
        import moderngl

        ParameterValidator.validate_mandatory_numpy_array('input', input)

        TextureUtils._validate_numpy_input(input)
        TextureUtils._validate_texture_dtype(dtype)

        opengl_context = (
            moderngl.create_context(standalone = True)
            if opengl_context is None else
            opengl_context
        )

        def pyav_frame_to_numpy_frame(
            frame: any,
            # TODO: What about the format (?)
            # format = ???
        ) -> np.ndarray:
            """
            Transform the `frame` numpy array provided into
            a pyav frame.

            (!) This code is to create an alternative method
            to turn a pyav frame into a numpy frame, but we 
            need to import the pyav library and I'm not doing
            it here...
            """
            #return input.to_ndarray(format = numpy_format)
            pass

        # OpenGL stores textures with the 'y' inverted
        input = np.flipud(input)

        """
        Textures are, by default (and according to
        the limitations we set in our system), stored
        with `f1` dtype, which is a RGBA [0, 255], so
        we need the equivalent, which is np.uint8
        """
        input = TextureUtils.numpy_to_uint8(input)

        """
        This is the way to create a new texture, but
        it only should be used like this when we are
        using it isolated. If we need to write again
        and again one texture, we should create it
        once and then only rewriting its content.
        """
        h, w, number_of_components = TextureUtils._get_size_and_number_of_channels_from_numpy_texture(input)

        texture = opengl_context.texture(
            size = (h, w),
            components = number_of_components,
            data = input.tobytes(),
            dtype = 'f1'
        )

        # Default filter
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)

        return texture
        
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def texture_to_numpy(
        texture: 'moderngl.Texture',
        do_include_alpha: bool = True
    ) -> np.ndarray:
        """
        *Optional `moderngl` library (imported as `moderngl`) required*

        Transform the provided moderngl `texture` into
        a numpy array, removing the alpha channel if
        the `do_include_alpha` parameter is set as True,
        and flipping the content as the textures are 
        stored in OpenGL with the Y axis inverted.
        """
        import moderngl

        ParameterValidator.validate_mandatory_instance_of('texture', texture, moderngl.Texture)

        numpy_dtype = TextureUtils.texture_dtype_to_numpy_dtype(texture.dtype)

        # Validate that the type of the texture is accepted
        TextureUtils._validate_numpy_dtype(numpy_dtype)
        
        data = texture.read()

        # The texture is stored with the shape as
        # (height, width), so we need to read it
        # as it is
        frame = np.frombuffer(
            buffer = data,
            dtype = numpy_dtype
        ).reshape(
            texture.height,
            texture.width,
            texture.components
        )

        # Discard alpha channel if not needed
        frame = (
            frame
            if do_include_alpha else
            frame[:, :, :3]
        )

        # OpenGL stores textures with the 'y' inverted
        frame = np.flipud(frame)

        return frame
    
    @staticmethod
    def texture_to_pyav_frame(
        texture: 'moderngl.Texture',
        do_include_alpha: bool = True
    ) -> 'VideoFrame':
        """
        Transform the provided moderngl `texture` into
        a pyav video frame, removing the alpha channel if
        the `do_include_alpha` parameter is set as True,
        and flipping the content as the textures are 
        stored in OpenGL with the Y axis inverted.
        """
        return TextureUtils.numpy_frame_to_pyav_frame(
            frame = TextureUtils.texture_to_numpy(
                texture = texture,
                do_include_alpha = do_include_alpha
            )
        )
    
    @staticmethod
    @requires_dependency('yta_numpy', 'yta_editor_utils', 'yta_numpy')
    @requires_dependency('PIL', 'yta_editor_utils', 'pillow')
    def texture_to_file(
        texture: 'moderngl.Texture',
        output_filename: str
    ) -> str:
        """
        *Optional dependency `pillow` (imported as `PIL`) required*

        *Optional dependency `yta_editor_utils` (imported as `yta_editor_utils`) required*

        Export the provided OpenGL texture 'texture' as a
        file with the given 'output_filename' name.
        """
        from yta_numpy.utils import numpy_to_file

        return numpy_to_file(TextureUtils.texture_to_numpy(texture), output_filename)

    @staticmethod
    def texture_dtype_to_numpy_dtype(
        dtype: str
    ) -> np.dtype:
        """
        Get the corresponding numpy dtype to the texture
        `dtype` provided.

        This will transform a `f1` into a `np.uint8`.

        We are only accepting a few dtypes.
        """
        TextureUtils._validate_texture_dtype(dtype)

        return np.dtype(TextureUtils.TEXTURE_DTYPE_TO_NUMPY_DTYPE.get(dtype, None))
    
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    @requires_dependency('av', 'yta_editor_utils', 'av')
    def numpy_frame_to_pyav_frame(
        frame: np.ndarray
    ) -> any:
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        *Optional dependency `av` (imported as `av`) required*

        Transform the `frame` numpy array provided into
        a pyav video frame.
        """
        import av

        # TODO: Make this 'reformat' customizable
        return av.VideoFrame.from_ndarray(frame, format = 'rgba').reformat(format = 'yuv420p')
    
    @staticmethod
    def numpy_dtype_to_texture_dtype(
        dtype: np.dtype
    ) -> str:
        """
        Get the corresponding texture dtype to the numpy
        `dtype` provided.

        This will transform a `np.uint8` into a `f1`.

        We are only accepting a few dtypes.
        """
        TextureUtils._validate_numpy_dtype(dtype)
        dtype = np.dtype(dtype)

        return TextureUtils.NUMPY_DTYPE_TO_TEXTURE_DTYPE.get(str(dtype), None)
    
    @staticmethod
    def numpy_to_float32(
        input: np.ndarray
    ) -> np.ndarray:
        """
        Transform the provided `input` numpy array to the 
        np.float32 dtype if needed. The np.float32 has values
        in the range [0.0, 1.0] and is necesary for some
        operations.

        This method will raise an exception if the dtype of
        the `input` numpy array provided is not accepted by
        our system.

        The formula:
        - `(input.astype(np.float32) / 255.0)`
        (if the dtype is `np.uint8`)
        """
        TextureUtils._validate_numpy_input(input)

        return NumpyConverter.to_dtype(
            array = input,
            dtype = np.float32
        )

    @staticmethod
    def numpy_to_uint8(
        input: np.ndarray
    ) -> np.ndarray:
        """
        Transform the provided `input` numpy array to the 
        np.uint8 dtype if needed. The np.uint8 has values
        in the range [0, 255] and is necesary for some
        operations.

        This method will raise an exception if the dtype of
        the `input` numpy array provided is not accepted by
        our system.

        The formula:
        - `np.clip(input * 255.0, 0, 255).astype(np.uint8)`
        (if the dtype is `np.float32`)
        """
        TextureUtils._validate_numpy_input(input)
        
        return NumpyConverter.to_dtype(
            array = input,
            dtype = np.uint8
        )
    
    @staticmethod
    def numpy_to_texture_dtype(
        input: np.ndarray,
        texture_dtype: str = 'f1'
    ) -> np.ndarray:
        """
        Process the provided `input` numpy array to be
        able to use it as a texture of the dtype given
        as the `texture_dtype` parameter.

        This method will adapt the array values according
        to the expected `texture_dtype` and the `input`
        dtype.

        (!) This method doesn't flip the array.
        """
        TextureUtils._validate_numpy_input(input)
        TextureUtils._validate_texture_dtype(texture_dtype)

        return {
            'f1': lambda: TextureUtils.numpy_to_uint8(input)
            # TODO: Add more when available in our system
        }.get(texture_dtype)()
    
    @staticmethod
    def _is_numpy_dtype_accepted(
        dtype: np.ndarray
    ) -> bool:
        """
        Check if the numpy `dtype` provided is accepted by our
        system.
        """
        return str(np.dtype(dtype)) in TextureUtils.ACCEPTED_NUMPY_DTYPES
    
    @staticmethod
    def _is_texture_dtype_accepted(
        dtype: str
    ) -> bool:
        """
        Check if the texture `dtype` provided is accepted by our
        system.
        """
        return dtype in TextureUtils.ACCEPTED_TEXTURE_DTYPES
    
    @staticmethod
    def _validate_numpy_input(
        input: np.ndarray
    ) -> None:
        """
        Validate that the `input` numpy array has one of
        the accepted dtypes or raise an exception if not.
        """
        if not TextureUtils._is_numpy_dtype_accepted(input.dtype):
            raise Exception(f'The dtype of the "input" numpy array provided ({input.dtype}) is not accepted by our system: {", ".join(TextureUtils.ACCEPTED_NUMPY_DTYPES)}')
        
    @staticmethod
    def _validate_numpy_dtype(
        dtype: np.dtype
    ) -> None:
        """
        Validate that the `dtype` provided is one of the
        accepted ones for the numpy arrays, or raise an
        exception if not.
        """
        if not TextureUtils._is_numpy_dtype_accepted(dtype):
            raise Exception(f'The numpy dtype "{dtype}" provided is not accepted by our system: {", ".join(TextureUtils.ACCEPTED_NUMPY_DTYPES)}')
        
    @staticmethod
    @requires_dependency('moderngl', 'yta_editor_utils', 'moderngl')
    def _validate_texture_input(
        input: 'moderngl.Texture'
    ) -> None:
        """
        *Optional dependency `moderngl` (imported as `moderngl`) required*

        Validate that the `input` texture has one of the
        accepted dtypes by our system, or raise an exception
        if not.
        """
        import moderngl
        
        if not TextureUtils._is_texture_dtype_accepted(input.dtype):
            raise Exception(f'The dtype of the "input" texture provided ({input.dtype}) is not accepted by our system: {", ".join(TextureUtils.ACCEPTED_TEXTURE_DTYPES)}')
        
    @staticmethod
    def _validate_texture_dtype(
        dtype: str
    ) -> None:
        """
        Validate that the `dtype` provided is one of the
        accepted ones for the moderngl textures, or raise
        an exception if not.
        """
        if not TextureUtils._is_texture_dtype_accepted(dtype):
            raise Exception(f'The texture dtype "{dtype}" provided is not accepted by our system: {", ".join(TextureUtils.ACCEPTED_TEXTURE_DTYPES)}')
        
"""
Notes for the developers:
- The numpy arrays have specific type classes, but
the moderngl textures have only a string that is
identified and transformed into the corresponding
numpy dtype. Thats why we can compare texture dtypes
easier than numpy dtypes.
"""