from yta_editor_nodes.abstract import _ProcessorGPUAndCPU
from yta_editor_nodes.utils import instantiate_cpu_and_gpu_processors
from typing import Union


class _NodeCompositor(_ProcessorGPUAndCPU):
    """
    *Abstract class*
    
    *Singleton class*

    *For internal use only*

    *This class must be inherited by the specific
    implementation of some node that will be positioning
    inputs, done by CPU or GPU (at least one of the
    options)*

    A node specifically designed to build a scene by
    positioning inputs in different positions and 
    obtaining a single output by using GPU or CPU.
    """

    def __init__(
        self,
        node_compositor_cpu: Union['_NodeCompositorCPU', None] = None,
        node_compositor_gpu: Union['_NodeCompositorGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        """
        The `node_compositor_cpu` and `node_compositor_gpu` have to be
        set by the developer when building the specific classes,
        but the `do_use_gpu` boolean flag will be set by the user
        when instantiating the class to choose between GPU and CPU.
        """
        super().__init__(
            # TODO: I should rename the base class to something
            # more general related to CPU and GPU but compatible
            # with processors, complex and composition nodes
            processor_cpu = node_compositor_cpu,
            processor_gpu = node_compositor_gpu,
            do_use_gpu = do_use_gpu
        )

    def __reinit__(
        self,
        node_compositor_cpu: Union['_NodeCompositorCPU', None] = None,
        node_compositor_gpu: Union['_NodeCompositorGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        super().__reinit__(
            # TODO: I should rename the base class to something
            # more general related to CPU and GPU but compatible
            # with processors, complex and composition nodes
            processor_cpu = node_compositor_cpu,
            processor_gpu = node_compositor_gpu,
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

class DisplacementWithRotationNodeCompositor(_NodeCompositor):
    """
    The frame, but moving and rotating over other frame.
    """

    def __init__(
        self,
        do_use_gpu: bool = True,
    ):
        """
        The `node_compositor_cpu` and `node_compositor_gpu` have
        to be set by the developer when building the specific
        classes, but the `do_use_gpu` boolean flag will be set
        by the user when instantiating the class to choose 
        between GPU and CPU.
        """
        # Dynamic way to import it
        node_compositor_cpu, node_compositor_gpu = instantiate_cpu_and_gpu_processors(
            class_name = 'DisplacementWithRotationNodeCompositor',
            cpu_module_path = None,
            cpu_kwargs = None,
            gpu_module_path = 'yta_editor_nodes_gpu.compositor',
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
            node_compositor_cpu = node_compositor_cpu,
            node_compositor_gpu = node_compositor_gpu,
            do_use_gpu = do_use_gpu
        )

    def __reinit__(
       self,
        node_compositor_cpu: Union['_NodeCompositorCPU', None] = None,
        node_compositor_gpu: Union['_NodeCompositorGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        # Dynamic way to import it
        node_compositor_cpu, node_compositor_gpu = instantiate_cpu_and_gpu_processors(
            class_name = 'DisplacementWithRotationNodeCompositor',
            cpu_module_path = None,
            cpu_kwargs = None,
            gpu_module_path = 'yta_editor_nodes_gpu.compositor',
            gpu_kwargs = {
                'opengl_context': None,
                # TODO: Do not hardcode please...
                'output_size': (1920, 1080),
            }
        )

        super().__reinit__(
            node_compositor_cpu = node_compositor_cpu,
            node_compositor_gpu = node_compositor_gpu,
            do_use_gpu = do_use_gpu
        )

    def process(
        self,
        # TODO: What about the type (?)
        base_input: Union['np.ndarray', 'moderngl.Texture'],
        overlay_input: Union['np.ndarray', 'moderngl.Texture'],
        position: tuple[int, int] = (1920 / 2 * 1.5, 1080 / 2 * 1.5),
        size: tuple[int, int] = (1920 / 2 * 1.5, 1080 / 2 * 1.5),
        rotation: int = 45,
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
            # TODO: Do I really need this 'output_size' (?)
            output_size = (1920, 1080),
            position = position,
            size = size,
            rotation = rotation,
            **kwargs
        )