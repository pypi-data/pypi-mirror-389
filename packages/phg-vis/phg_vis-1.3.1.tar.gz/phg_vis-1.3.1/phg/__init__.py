"""
PHG - Python Hypergraphics Library
===================================

A powerful graphics library for procedural 3D visualization using PHG scripts.

Main Features:
- PHG script visualization via vis.exe
- Shader-based rendering with GLSL conversion
- Pipe system visualization with world/local coordinate systems
- Real-time and image rendering capabilities

Version: 0.2.0
Author: PanGuoJun
License: MIT
"""

from .visphg import vis, image
from .shader_render import ShaderRenderer, render_shader
from .phg_to_shader import PHGToShaderConverter, phg_to_shader
from .pipe_string_phg import (
    world_pipe_to_phg,
    local_pipe_to_phg,
    world_pipestr_vis,
    local_pipestr_vis
)

# Extend ShaderRenderer class to support direct PHG rendering
class PHGShaderRenderer(ShaderRenderer):
    """Shader renderer that supports direct PHG rendering"""
    
    def render_phg(self, phg_script: str, duration=0, interactive=True):
        """
        Render PHG script
        
        Parameters:
            phg_script: PHG script code
            duration: Render duration
            interactive: Whether to allow interaction
            
        Returns:
            success: Whether rendering was successful
        """
        converter = PHGToShaderConverter()
        shader_code = converter.generate_shader_code(phg_script)
        
        if not shader_code:
            print("Error: PHG conversion failed")
            return False
            
        return self.render_shader(shader_code, duration, interactive)

# Convenience functions
def render_phg(phg_script: str, width=800, height=600, duration=0, title="PHG Renderer"):
    """
    Directly render PHG script
    
    Parameters:
        phg_script: PHG script code
        width: Window width
        height: Window height  
        duration: Render duration
        title: Window title
    """
    renderer = PHGShaderRenderer(width, height, title)
    success = renderer.render_phg(phg_script, duration)
    renderer.close()
    return success

def convert_phg_to_shader(phg_script: str) -> str:
    """
    Convert PHG script to GLSL shader code

    Parameters:
        phg_script: PHG script

    Returns:
        shader_code: GLSL shader code
    """
    return phg_to_shader(phg_script)

__all__ = [
    # Core visualization functions
    'vis',
    'image',

    # Shader rendering
    'ShaderRenderer',
    'render_shader',
    'render_phg',
    'PHGShaderRenderer',

    # PHG conversion
    'PHGToShaderConverter',
    'phg_to_shader',
    'convert_phg_to_shader',

    # Pipe visualization
    'world_pipe_to_phg',
    'local_pipe_to_phg',
    'world_pipestr_vis',
    'local_pipestr_vis',
]

__version__ = "1.3.1"
__author__ = "PanGuoJun"
__description__ = "Python Hypergraphics Library"

# Package initialization information
print(f"PHG {__version__} - {__description__}")
print("[OK] Visualization module loaded")
print("[OK] Shader converter loaded")
print("[OK] Pipe visualization loaded")