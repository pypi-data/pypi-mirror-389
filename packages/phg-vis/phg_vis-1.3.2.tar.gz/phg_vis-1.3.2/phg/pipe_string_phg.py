"""
Pipe String to PHG Converter
============================

This module provides functionality to convert pipe strings into PHG (Python Graphics) scripts.
Supports both world coordinate system and local coordinate system pipe descriptions.

Main Features:
- world_pipe_to_phg: World coordinate system pipe conversion
- local_pipe_to_phg: Local coordinate system pipe conversion  
- world_pipestr_vis: Direct visualization for world coordinate pipes
- local_pipestr_vis: Direct visualization for local coordinate pipes

Pipe String Format:
- F: Forward
- B: Backward  
- R: Right
- L: Left
- U: Up
- D: Down
"""

import phg
from coordinate_system import vec3, quat, coord3

# Default color and pipe radius
DEFAULT_PIPE_COLOR = (0, 55, 255)
DEFAULT_PIPE_RADIUS = 0.3

def world_pipe_to_phg(world_pipe_str, start_c, pipe_color=DEFAULT_PIPE_COLOR, pipe_radius=DEFAULT_PIPE_RADIUS):
    """
    Convert world coordinate system pipe string to PHG script
    
    Parameters:
        world_pipe_str: World coordinate pipe string (e.g., "FFRUD")
        start_c: Starting coordinate system
        pipe_color: Pipe color as (R, G, B) tuple
        pipe_radius: Pipe radius
    
    Returns:
        PHG script string
    """
    
    # World coordinate direction definitions
    world_directions = {
        'F': vec3(0, 0, 1),   # Forward (World Z+)
        'B': vec3(0, 0, -1),  # Backward (World Z-)
        'R': vec3(1, 0, 0),   # Right (World X+)
        'L': vec3(-1, 0, 0),  # Left (World X-)
        'U': vec3(0, 1, 0),   # Up (World Y+)
        'D': vec3(0, -1, 0)   # Down (World Y-)
    }

    # Parse color
    r, g, b = pipe_color
    
    # Pipe component mapping (all components use fixed length 1.0)
    pipe_components = {
        'F': f'{{{{rgb:{r},{g},{b};md:cylinder {pipe_radius} 1.0;rx:90;z:-0.5;}};z:1.0}}',
        'B': f'{{{{rgb:{r},{g},{b};md:cylinder {pipe_radius} 1.0;rx:-90;z:{-1.0-0.5};}};z:1.0}}',
        'R': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}ry:90;x:1.0;z:-1.0}}}},{{x:1.0;ry:-90;}}',
        'L': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}ry:-90;m:x;z:-1.0;x:-1.0}}}},{{x:-1.0;ry:90;}}',
        'U': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}rz:90;y:1.0;z:-1}}}},{{y:1.0;rx:90;}}',
        'D': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}rz:-90;y:-1;z:-1}}}},{{y:-1.0;rx:-90;}}'
    }

    # Initialize current coordinate system (using starting coordinate)
    cur_c = coord3(start_c.o, start_c.Q())
    
    # Store all pipe component scripts
    script_parts = []
    
    # Iterate through each character in pipe string
    for move_char in world_pipe_str:
        if move_char not in pipe_components:
            print(f"Warning: Unknown pipe character '{move_char}', skipped")
            continue
        
        # Get current movement direction in world coordinates
        world_dir = world_directions[move_char]
        
        # Transform world direction to current local coordinate system
        local_dir = vec3(
            world_dir.dot(cur_c.ux),  # Component in local X-axis
            world_dir.dot(cur_c.uy),  # Component in local Y-axis
            world_dir.dot(cur_c.uz)   # Component in local Z-axis
        )
        
        # Find component with largest absolute value to determine main movement direction
        abs_components = [abs(local_dir.x), abs(local_dir.y), abs(local_dir.z)]
        max_idx = abs_components.index(max(abs_components))
        
        # Determine local movement direction based on maximum component
        if max_idx == 0:  # X-axis
            local_move = 'R' if local_dir.x > 0 else 'L'
        elif max_idx == 1:  # Y-axis
            local_move = 'U' if local_dir.y > 0 else 'D'
        else:  # Z-axis
            local_move = 'F' if local_dir.z > 0 else 'B'
        
        # Add corresponding pipe component script
        script_parts.append(pipe_components[local_move])
        
        # Update current coordinate system (simulate new position and direction after movement)
        if local_move == 'F':
            # Forward: move 1.0 unit along local Z-axis positive direction
            cur_c = cur_c * coord3(vec3(0, 0, 1.0))
        elif local_move == 'B':
            # Backward: move 1.0 unit along local Z-axis negative direction
            cur_c = cur_c * coord3(vec3(0, 0, -1.0))
        elif local_move == 'R':
            # Right turn: rotate -90 degrees around Y-axis, then move 1.0 unit along X-axis
            rotation = quat(-3.1416 / 2, cur_c.uy)
            cur_c = cur_c * rotation
            cur_c = cur_c * coord3(vec3(1.0, 0, 0))
        elif local_move == 'L':
            # Left turn: rotate 90 degrees around Y-axis, then move 1.0 unit along X-axis
            rotation = quat(3.1416 / 2, cur_c.uy)
            cur_c = cur_c * rotation
            cur_c = cur_c * coord3(vec3(-1.0, 0, 0))
        elif local_move == 'U':
            # Up turn: rotate 90 degrees around X-axis, then move 1.0 unit along Y-axis
            rotation = quat(3.1416 / 2, cur_c.ux)
            cur_c = cur_c * rotation
            cur_c = cur_c * coord3(vec3(0, 1.0, 0))
        elif local_move == 'D':
            # Down turn: rotate -90 degrees around X-axis, then move 1.0 unit along Y-axis
            rotation = quat(-3.1416 / 2, cur_c.ux)
            cur_c = cur_c * rotation
            cur_c = cur_c * coord3(vec3(0, -1.0, 0))

    # Combine all pipe component scripts
    inner_script = ',\n'.join(script_parts)
    
    # Get quaternion of starting coordinate system
    q = start_c.Q()
    
    # Build complete PHG script
    complete_script = f"""{{
    {{xyz:{start_c.o.x},{start_c.o.y},{start_c.o.z};q:{q.w},{q.x},{q.y},{q.z};s:0.5;
    <{inner_script}>}}
    }}"""
    
    return complete_script


def local_pipe_to_phg(local_pipe_str, start_c, pipe_color=DEFAULT_PIPE_COLOR, pipe_radius=DEFAULT_PIPE_RADIUS):
    """
    Convert local coordinate system pipe string to PHG script

    Parameters:
        local_pipe_str: Local coordinate pipe string (e.g., "FFRUD")
        start_c: Starting coordinate system
        pipe_color: Pipe color as (R, G, B) tuple
        pipe_radius: Pipe radius

    Returns:
        PHG script string
    """

    # Parse color
    r, g, b = pipe_color

    # Pipe component mapping (all components use fixed length 1.0)
    pipe_components = {
        'F': f'{{{{rgb:{r},{g},{b};md:cylinder {pipe_radius} 1.0;rx:90;z:-0.5;}};z:1.0}}',
        'B': f'{{{{rgb:{r},{g},{b};md:cylinder {pipe_radius} 1.0;rx:-90;z:{-1.0-0.5};}};z:1.0}}',
        'R': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}ry:90;x:1.0;z:-1.0}}}},{{x:1.0;ry:-90;}}',
        'L': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}ry:-90;m:x;z:-1.0;x:-1.0}}}},{{x:-1.0;ry:90;}}',
        'U': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}rz:90;y:1.0;z:-1}}}},{{y:1.0;rx:90;}}',
        'D': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}rz:-90;y:-1;z:-1}}}},{{y:-1.0;rx:-90;}}'
    }

    # Store all pipe component scripts
    script_parts = []

    # Iterate through each character in pipe string
    for move_char in local_pipe_str:
        if move_char not in pipe_components:
            print(f"Warning: Unknown pipe character '{move_char}', skipped")
            continue

        # Directly use local coordinate system movement commands
        script_parts.append(pipe_components[move_char])

    # Combine all pipe component scripts
    inner_script = ',\n'.join(script_parts)

    # Get quaternion of starting coordinate system
    q = start_c.Q()

    # Build complete PHG script
    complete_script = f"""{{
    {{xyz:{start_c.o.x},{start_c.o.y},{start_c.o.z};q:{q.w},{q.x},{q.y},{q.z};s:0.5;
    <{inner_script}>}}
    }}"""

    return complete_script


def world_pipestr_vis(world_pipe_strs, start_c=None, pipe_colors=None, pipe_radius=DEFAULT_PIPE_RADIUS):
    """
    Direct visualization for world coordinate pipe strings with support for multiple pipes
    
    Parameters:
        world_pipe_strs: World coordinate pipe string or list of strings (e.g., "FFRUD" or ["FFR", "LLU"])
        start_c: Starting coordinate system, defaults to origin
        pipe_colors: Single color or list of colors as (R, G, B) tuples
        pipe_radius: Pipe radius
    
    Returns:
        PHG script string
    """
    # Handle single string input
    if isinstance(world_pipe_strs, str):
        world_pipe_strs = [world_pipe_strs]
    
    # Handle single color input
    if pipe_colors is None:
        pipe_colors = [DEFAULT_PIPE_COLOR] * len(world_pipe_strs)
    elif isinstance(pipe_colors, tuple):
        pipe_colors = [pipe_colors] * len(world_pipe_strs)
    
    # Ensure colors list matches pipes list length
    if len(pipe_colors) != len(world_pipe_strs):
        pipe_colors = [DEFAULT_PIPE_COLOR] * len(world_pipe_strs)
        print("Warning: Colors list length doesn't match pipes list, using default colors")
    
    # Use default origin if no starting coordinate provided
    if start_c is None:
        start_c = coord3(vec3(0, 0, 0), quat(1, 0, 0, 0))

    # Generate PHG scripts for all pipes
    script_parts = []
    for i, (pipe_str, color) in enumerate(zip(world_pipe_strs, pipe_colors)):
        phg_script = world_pipe_to_phg(pipe_str, start_c, color, pipe_radius)
        # Extract inner content between outer braces
        inner_content = phg_script.strip()[1:-1].strip()
        script_parts.append(inner_content)

    # Combine all pipe scripts
    combined_script = "{\n" + ",\n".join(script_parts) + "\n}"

    # Call visualization function
    try:
        phg.vis(combined_script)
        print(f"Visualizing {len(world_pipe_strs)} world coordinate pipes")
    except ImportError:
        print("Warning: Cannot import visualization module, returning PHG script")

    return combined_script


def local_pipestr_vis(local_pipe_strs, start_c=None, pipe_colors=None, pipe_radius=DEFAULT_PIPE_RADIUS):
    """
    Direct visualization for local coordinate pipe strings with support for multiple pipes
    
    Parameters:
        local_pipe_strs: Local coordinate pipe string or list of strings (e.g., "FFRUD" or ["FFR", "LLU"])
        start_c: Starting coordinate system, defaults to origin
        pipe_colors: Single color or list of colors as (R, G, B) tuples
        pipe_radius: Pipe radius
    
    Returns:
        PHG script string
    """
    # Handle single string input
    if isinstance(local_pipe_strs, str):
        local_pipe_strs = [local_pipe_strs]
    
    # Handle single color input
    if pipe_colors is None:
        pipe_colors = [DEFAULT_PIPE_COLOR] * len(local_pipe_strs)
    elif isinstance(pipe_colors, tuple):
        pipe_colors = [pipe_colors] * len(local_pipe_strs)
    
    # Ensure colors list matches pipes list length
    if len(pipe_colors) != len(local_pipe_strs):
        pipe_colors = [DEFAULT_PIPE_COLOR] * len(local_pipe_strs)
        print("Warning: Colors list length doesn't match pipes list, using default colors")
    
    # Use default origin if no starting coordinate provided
    if start_c is None:
        start_c = coord3(vec3(0, 0, 0), quat(1, 0, 0, 0))

    # Generate PHG scripts for all pipes
    script_parts = []
    for i, (pipe_str, color) in enumerate(zip(local_pipe_strs, pipe_colors)):
        phg_script = local_pipe_to_phg(pipe_str, start_c, color, pipe_radius)
        # Extract inner content between outer braces
        inner_content = phg_script.strip()[1:-1].strip()
        script_parts.append(inner_content)

    # Combine all pipe scripts
    combined_script = "{\n" + ",\n".join(script_parts) + "\n}"

    # Call visualization function
    try:
        phg.vis(combined_script)
        print(f"Visualizing {len(local_pipe_strs)} local coordinate pipes")
    except ImportError:
        print("Warning: Cannot import visualization module, returning PHG script")

    return combined_script


def multiple_pipes_vis(pipe_configs, coordinate_system='world'):
    """
    Advanced visualization for multiple pipes with individual configurations
    
    Parameters:
        pipe_configs: List of pipe configuration dictionaries with keys:
            - 'pipe_str': Pipe string (required)
            - 'start_c': Starting coordinate (optional, defaults to origin)
            - 'color': Pipe color (optional, defaults to DEFAULT_PIPE_COLOR)
            - 'radius': Pipe radius (optional, defaults to DEFAULT_PIPE_RADIUS)
        coordinate_system: 'world' or 'local' coordinate system
    
    Returns:
        PHG script string
    """
    script_parts = []
    
    for i, config in enumerate(pipe_configs):
        pipe_str = config.get('pipe_str')
        start_c = config.get('start_c', coord3(vec3(0, 0, 0), quat(1, 0, 0, 0)))
        color = config.get('color', DEFAULT_PIPE_COLOR)
        radius = config.get('radius', DEFAULT_PIPE_RADIUS)
        
        if coordinate_system.lower() == 'world':
            phg_script = world_pipe_to_phg(pipe_str, start_c, color, radius)
        else:
            phg_script = local_pipe_to_phg(pipe_str, start_c, color, radius)
        
        # Extract inner content
        inner_content = phg_script.strip()[1:-1].strip()
        script_parts.append(inner_content)
    
    # Combine all pipe scripts
    combined_script = "{\n" + ",\n".join(script_parts) + "\n}"
    
    # Call visualization
    try:
        phg.vis(combined_script)
        print(f"Visualizing {len(pipe_configs)} pipes in {coordinate_system} coordinate system")
    except ImportError:
        print("Warning: Cannot import visualization module, returning PHG script")
    
    return combined_script


# Usage Examples
if __name__ == "__main__":
    # Create starting coordinate system (example)
    start_coord = coord3(vec3(0, 0, 0), quat(1, 0, 0, 0))

    # Example 1: Single world coordinate pipe string
    example_world_pipe = "FFRUD"  # Forward twice, right, up, down
    print("World Coordinate Pipe Example:")
    phg_script = world_pipe_to_phg(example_world_pipe, start_coord)
    print("Generated PHG Script:")
    print(phg_script)
    print()

    # Example 2: Single local coordinate pipe string
    example_local_pipe = "FFRUD"  # Movements in local coordinate system
    print("Local Coordinate Pipe Example:")
    phg_script = local_pipe_to_phg(example_local_pipe, start_coord)
    print("Generated PHG Script:")
    print(phg_script)
    print()

    # Example 3: Multiple pipes visualization
    print("Multiple Pipes Visualization Example:")
    
    # Multiple world coordinate pipes with different colors
    world_pipes = ["FFR", "LLU", "RRD"]
    world_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
    world_pipestr_vis(world_pipes, start_coord, world_colors)
    print()

    # Multiple local coordinate pipes
    local_pipes = ["FFR", "BBL", "UUD"]
    local_colors = [(255, 255, 0), (255, 0, 255), (0, 255, 255)]  # Yellow, Magenta, Cyan
    local_pipestr_vis(local_pipes, start_coord, local_colors)
    print()

    # Example 4: Advanced multiple pipes configuration
    print("Advanced Multiple Pipes Configuration:")
    pipe_configs = [
        {
            'pipe_str': 'FFR',
            'start_c': coord3(vec3(0, 0, 0), quat(1, 0, 0, 0)),
            'color': (255, 100, 100),
            'radius': 0.4
        },
        {
            'pipe_str': 'LLU', 
            'start_c': coord3(vec3(5, 0, 0), quat(1, 0, 0, 0)),
            'color': (100, 255, 100),
            'radius': 0.3
        },
        {
            'pipe_str': 'RRD',
            'start_c': coord3(vec3(0, 5, 0), quat(1, 0, 0, 0)),
            'color': (100, 100, 255),
            'radius': 0.2
        }
    ]
    
    multiple_pipes_vis(pipe_configs, 'world')