"""
PHG - Python Hypergraphics Library
===================================

A powerful graphics library for procedural 3D visualization using PHG scripts.

Main Features:
- PHG script visualization via vis.exe
- Shader-based rendering with GLSL conversion
- Pipe system visualization with world/local coordinate systems
- Multiple pipe visualization support
- Real-time and image rendering capabilities

Version: 1.3.1
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
    local_pipestr_vis,
    multiple_pipes_vis
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

def visualize_pipe_variants(pipe_variants, start_position=None, colors=None, coordinate_system='world'):
    """
    Visualize multiple pipe variants for comparison
    
    Parameters:
        pipe_variants: List of pipe strings or configuration dictionaries
        start_position: Starting coordinate (optional)
        colors: List of colors for each pipe variant
        coordinate_system: 'world' or 'local' coordinate system
    
    Returns:
        PHG script string
    """
    from coordinate_system import vec3, quat, coord3
    
    # Handle start position
    if start_position is None:
        start_c = coord3(vec3(0, 0, 0), quat(1, 0, 0, 0))
    else:
        start_c = start_position
    
    # Handle different input formats
    if isinstance(pipe_variants[0], str):
        # Simple list of pipe strings
        if colors is None:
            # Generate distinct colors for each variant
            import colorsys
            colors = []
            for i in range(len(pipe_variants)):
                hue = i / len(pipe_variants)
                rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
                colors.append(tuple(int(c * 255) for c in rgb))
        
        if coordinate_system == 'world':
            return world_pipestr_vis(pipe_variants, start_c, colors)
        else:
            return local_pipestr_vis(pipe_variants, start_c, colors)
    
    else:
        # List of configuration dictionaries
        pipe_configs = []
        for i, variant in enumerate(pipe_variants):
            if isinstance(variant, str):
                config = {
                    'pipe_str': variant,
                    'start_c': start_c,
                    'color': colors[i] if colors else None,
                    'radius': 0.3
                }
            else:
                config = variant
                if 'start_c' not in config:
                    config['start_c'] = start_c
            
            pipe_configs.append(config)
        
        return multiple_pipes_vis(pipe_configs, coordinate_system)

def create_pipe_comparison_grid(pipe_strings, grid_size=(2, 2), start_position=None, 
                               base_color=(0, 55, 255), coordinate_system='world'):
    """
    Create a grid layout for comparing multiple pipe paths
    
    Parameters:
        pipe_strings: List of pipe strings to compare
        grid_size: (rows, cols) for grid layout
        start_position: Base starting position
        base_color: Base color for pipes
        coordinate_system: 'world' or 'local'
    
    Returns:
        PHG script string
    """
    from coordinate_system import vec3, quat, coord3
    
    if start_position is None:
        start_position = coord3(vec3(0, 0, 0), quat(1, 0, 0, 0))
    
    rows, cols = grid_size
    spacing = 5.0  # Space between pipes in grid
    
    pipe_configs = []
    
    for i, pipe_str in enumerate(pipe_strings):
        if i >= rows * cols:
            break
            
        row = i // cols
        col = i % cols
        
        # Calculate position in grid
        x_offset = col * spacing
        z_offset = row * spacing
        
        # Create individual start position for this pipe
        individual_start = coord3(
            vec3(
                start_position.o.x + x_offset,
                start_position.o.y,
                start_position.o.z + z_offset
            ),
            start_position.Q()
        )
        
        # Generate color variation
        color_variation = (
            min(255, base_color[0] + (i * 30) % 100),
            min(255, base_color[1] + (i * 50) % 100),
            min(255, base_color[2] + (i * 70) % 100)
        )
        
        pipe_configs.append({
            'pipe_str': pipe_str,
            'start_c': individual_start,
            'color': color_variation,
            'radius': 0.25 + (i * 0.05)  # Vary radius slightly
        })
    
    return multiple_pipes_vis(pipe_configs, coordinate_system)

def generate_pipe_variants_from_rules(base_pipe, num_variants=5, apply_rules=None):
    """
    Generate pipe variants using transformation rules
    
    Parameters:
        base_pipe: Base pipe string
        num_variants: Number of variants to generate
        apply_rules: List of rules to apply ('swap', 'insert', 'cancel')
    
    Returns:
        List of pipe variant strings
    """
    if apply_rules is None:
        apply_rules = ['swap', 'insert', 'cancel']
    
    variants = [base_pipe]
    
    # Import the pipe transformer if available
    try:
        from .pipe_string_phg import PipeStringTransformer
        transformer = PipeStringTransformer()
        
        for _ in range(num_variants - 1):
            current_pipe = base_pipe
            
            # Apply random transformations
            import random
            for _ in range(random.randint(1, 3)):
                rule = random.choice(apply_rules)
                
                if rule == 'swap' and len(current_pipe) >= 2:
                    i, j = random.sample(range(len(current_pipe)), 2)
                    current_pipe = transformer.swap_positions(current_pipe, i, j)
                
                elif rule == 'insert':
                    position = random.randint(0, len(current_pipe))
                    direction = random.choice(list(transformer.CANCEL_PAIRS.keys()))
                    current_pipe = transformer.insert_cancel_pair(current_pipe, position, direction)
                
                elif rule == 'cancel':
                    current_pipe = transformer.cancel_adjacent_pairs(current_pipe)
            
            # Simplify and add if valid
            simplified = transformer.simplify_path(current_pipe)
            if simplified not in variants:
                variants.append(simplified)
    
    except ImportError:
        # Fallback: simple variant generation
        import random
        for i in range(num_variants - 1):
            # Simple character shuffling
            pipe_list = list(base_pipe)
            random.shuffle(pipe_list)
            variant = ''.join(pipe_list)
            if variant not in variants:
                variants.append(variant)
    
    return variants[:num_variants]

# Enhanced pipe visualization with transformation support
def visualize_pipe_with_transformations(pipe_string, start_position=None, 
                                      transformations=None, show_variants=3):
    """
    Visualize a pipe string along with its transformed variants
    
    Parameters:
        pipe_string: Base pipe string
        start_position: Starting coordinate
        transformations: List of transformation rules to apply
        show_variants: Number of variants to show
    
    Returns:
        PHG script string
    """
    # Generate variants
    variants = generate_pipe_variants_from_rules(
        pipe_string, 
        num_variants=show_variants + 1,  # +1 for original
        apply_rules=transformations
    )
    
    # Create comparison visualization
    return visualize_pipe_variants(variants, start_position)

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
    'multiple_pipes_vis',
    
    # Enhanced pipe visualization
    'visualize_pipe_variants',
    'create_pipe_comparison_grid',
    'generate_pipe_variants_from_rules',
    'visualize_pipe_with_transformations',
]

__version__ = "1.3.1"
__author__ = "PanGuoJun"
__description__ = "Python Hypergraphics Library"

# Package initialization information
print(f"PHG {__version__} - {__description__}")
print("[OK] Visualization module loaded")
print("[OK] Shader converter loaded") 
print("[OK] Pipe visualization loaded")
print("[OK] Multiple pipe visualization support loaded")
print("[OK] Pipe transformation utilities loaded")