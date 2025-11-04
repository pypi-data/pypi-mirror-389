"""
Module for the effects and nodes that are made by
putting different nodes together.
"""
from yta_editor_nodes.processor import _ProcessorGPUAndCPU
from yta_editor_nodes.utils import instantiate_cpu_and_gpu_processors
from typing import Union


class _NodeComplex(_ProcessorGPUAndCPU):
    """
    *Abstract class*
    
    *Singleton class*

    *For internal use only*

    *This class must be inherited by the specific
    implementation of some complex node that will be
    done by CPU or GPU (at least one of the options)*

    A complex node, which is a node made by other nodes,
    that is capable of processing inputs and obtain a
    single output by using the GPU or the CPU.

    This type of node is for complex modifications.
    """

    def __init__(
        self,
        node_complex_cpu: Union['_NodeComplexCPU', None] = None,
        node_complex_gpu: Union['_NodeComplexGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        """
        The `node_complex_cpu` and `node_complex_gpu` have to be
        set by the developer when building the specific classes,
        but the `do_use_gpu` boolean flag will be set by the user
        when instantiating the class to choose between GPU and CPU.
        """
        super().__init__(
            # TODO: I should rename the base class to something
            # more general related to CPU and GPU but compatible
            # with processors, complex and composition nodes
            processor_cpu = node_complex_cpu,
            processor_gpu = node_complex_gpu,
            do_use_gpu = do_use_gpu
        )

    def __reinit__(
        self,
        node_complex_cpu: Union['_NodeComplexCPU', None] = None,
        node_complex_gpu: Union['_NodeComplexGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        super().__reinit__(
            # TODO: I should rename the base class to something
            # more general related to CPU and GPU but compatible
            # with processors, complex and composition nodes
            processor_cpu = node_complex_cpu,
            processor_gpu = node_complex_gpu,
            do_use_gpu = do_use_gpu
        )

    def process(
        self,
        # TODO: What about the type (?)
        input: Union['np.ndarray', 'moderngl.Texture'],
        **kwargs
    # TODO: What about the output type (?)
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'input' with GPU or CPU 
        according to the internal flag.
        """
        return self._processor.process(
            input = input,
            **kwargs
        )

"""
Specific implementations below this class.
"""

class DisplayOverAtNodeComplex(_NodeComplex):
    """
    The overlay input is positioned with the given position,
    rotation and size, and then put as an overlay of the
    also given base input.

    Information:
    - The scene size is `(1920, 1080)`, so provide the
    `position` parameter according to it, where it is
    representing the center of the texture.
    - The `rotation` is in degrees, where `rotation=90`
    means rotating 90 degrees to the right.
    - The `size` parameter must be provided according to
    the previously mentioned scene size `(1920, 1080)`.

    TODO: This has no inheritance, is special and we need
    to be able to identify it as a valid one.
    """

    def __init__(
        self,
        do_use_gpu: bool = True,
    ):
        # Dynamic way to import it
        node_complex_cpu, node_complex_gpu = instantiate_cpu_and_gpu_processors(
            class_name = 'DisplayOverAtNodeComplex',
            cpu_module_path = None,
            cpu_kwargs = None,
            gpu_module_path = 'yta_editor_nodes_gpu.complex',
            gpu_kwargs = {
                'opengl_context': None,
                # TODO: Do not hardcode please...
                'output_size': (1920, 1080),
            }
        )

        # TODO: This dynamic way of importing the instances
        # is not working well, but it is validating that the
        # library exists, and that is available...

        super().__init__(
            node_complex_cpu = node_complex_cpu,
            node_complex_gpu = node_complex_gpu,
            do_use_gpu = do_use_gpu
        )

    def __reinit__(
        self,
        node_complex_cpu: Union['_NodeComplexCPU', None] = None,
        node_complex_gpu: Union['_NodeComplexGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        # Dynamic way to import it
        node_complex_cpu, node_complex_gpu = instantiate_cpu_and_gpu_processors(
            class_name = 'DisplayOverAtNodeComplex',
            cpu_module_path = None,
            cpu_kwargs = None,
            gpu_module_path = 'yta_editor_nodes_gpu.complex',
            gpu_kwargs = {
                'opengl_context': None,
                # TODO: Do not hardcode please...
                'output_size': (1920, 1080),
            }
        )

        super().__reinit__(
            node_complex_cpu = node_complex_cpu,
            node_complex_gpu = node_complex_gpu,
            do_use_gpu = do_use_gpu
        )

    def process(
        self,
        # TODO: What about the type (?)
        base_input: Union['np.ndarray', 'moderngl.Texture'],
        overlay_input: Union['np.ndarray', 'moderngl.Texture'],
        **kwargs
    # TODO: What about the output type (?)
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'input' with GPU or CPU 
        according to the internal flag.
        """
        return self._processor.process(
            base_input = base_input,
            overlay_input = overlay_input,
            **kwargs
        )