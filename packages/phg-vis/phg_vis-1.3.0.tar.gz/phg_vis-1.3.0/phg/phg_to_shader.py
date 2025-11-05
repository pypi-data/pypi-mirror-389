"""
phg_to_shader.py
PHG to Shader Converter Core Library
"""

import re
import math
from typing import Dict, List, Any, Tuple

class PHGToShaderConverter:
    """PHG to Shader converter"""
    
    def __init__(self):
        self.nodes = {}
        self.geometry_types = {
            'cylinder': 'CYLINDER',
            'sphere': 'SPHERE', 
            'cube': 'BOX',
            'box': 'BOX',
            'cone': 'CONE',
            'torus': 'TORUS',
            'plane': 'PLANE'
        }
        self.primitive_count = 0
        
    def parse_phg(self, phg_script: str) -> Dict[str, Any]:
        """Parse PHG script and extract node information"""
        # Remove comments
        phg_clean = re.sub(r'#.*$', '', phg_script, flags=re.MULTILINE)
        
        # Extract node definitions
        node_pattern = r'(\w+)\s*\{([^}]*)\}'
        nodes = {}
        
        for match in re.finditer(node_pattern, phg_clean):
            node_name = match.group(1)
            node_content = match.group(2)
            
            # Parse node properties
            properties = self._parse_node_properties(node_content)
            nodes[node_name] = properties
            
        return nodes
    
    def _parse_node_properties(self, content: str) -> Dict[str, Any]:
        """Parse node properties"""
        properties = {}
        
        # Property pattern: property:value1,value2;
        prop_pattern = r'(\w+):([^;]+);'
        
        for match in re.finditer(prop_pattern, content):
            prop_name = match.group(1)
            prop_value = match.group(2).strip()
            
            # Handle different property types
            if prop_name == 'md':
                # Geometry definition
                properties['geometry'] = self._parse_geometry(prop_value)
            elif prop_name in ['xyz', 'sxyz', 'hpr', 'rot']:
                # Vector values
                properties[prop_name] = self._parse_vector(prop_value)
            elif prop_name in ['x', 'y', 'z', 'rx', 'ry', 'rz', 's']:
                # Scalar values
                properties[prop_name] = float(prop_value)
            elif prop_name == 'rgb':
                # Color values
                properties['color'] = self._parse_color(prop_value)
                
        return properties
    
    def _parse_geometry(self, geom_str: str) -> Dict[str, Any]:
        """Parse geometry definition"""
        parts = geom_str.strip().split()
        if not parts:
            return {}
            
        geom_type = parts[0]
        
        geometry = {'type': geom_type}
        
        try:
            if geom_type == 'cylinder':
                geometry['radius'] = float(parts[1])
                geometry['height'] = float(parts[2])
            elif geom_type == 'sphere':
                geometry['radius'] = float(parts[1])
            elif geom_type == 'cube':
                geometry['size'] = [float(parts[1])] * 3
            elif geom_type == 'box':
                if len(parts) >= 4:
                    geometry['size'] = [float(parts[1]), float(parts[2]), float(parts[3])]
                else:
                    geometry['size'] = [1.0, 1.0, 1.0]
            elif geom_type == 'cone':
                geometry['radius1'] = float(parts[1])
                geometry['radius2'] = float(parts[2]) if len(parts) > 2 else 0.0
                geometry['height'] = float(parts[3]) if len(parts) > 3 else 1.0
            elif geom_type == 'torus':
                geometry['radius1'] = float(parts[1])
                geometry['radius2'] = float(parts[2]) if len(parts) > 2 else 0.3
            elif geom_type == 'plane':
                geometry['normal'] = [float(parts[1]), float(parts[2]), float(parts[3])] if len(parts) > 3 else [0, 1, 0]
        except (IndexError, ValueError):
            print(f"Warning: Geometry parameter parsing error: {geom_str}")
            
        return geometry
    
    def _parse_vector(self, vec_str: str) -> List[float]:
        """Parse vector values"""
        try:
            return [float(x.strip()) for x in vec_str.split(',')]
        except ValueError:
            return [0.0, 0.0, 0.0]
    
    def _parse_color(self, color_str: str) -> List[float]:
        """Parse color values and normalize to 0-1"""
        try:
            rgb = [float(x.strip()) for x in color_str.split(',')]
            return [c / 255.0 for c in rgb]
        except ValueError:
            return [0.7, 0.7, 0.7]
    
    def geometry_to_sdf_params(self, geometry: Dict[str, Any], transform: Dict[str, Any]) -> List[str]:
        """Convert geometry to SDF parameter array"""
        geom_type = geometry.get('type', 'sphere')
        color = transform.get('color', [0.7, 0.7, 0.7])
        position = transform.get('xyz', [0, 0, 0])
        
        # Determine SDF type
        sdf_type = self.geometry_types.get(geom_type, 'SPHERE')
        
        params = []
        
        # params[0]: position + type
        params.append(f"vec4({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f}, float({sdf_type}))")
        
        # params[1]: size parameters
        if geom_type == 'cylinder':
            radius = geometry.get('radius', 1.0)
            height = geometry.get('height', 2.0)
            params.append(f"vec4({radius:.3f}, {height:.3f}, 0.0, 0.0)")
        elif geom_type == 'sphere':
            radius = geometry.get('radius', 1.0)
            params.append(f"vec4({radius:.3f}, 0.0, 0.0, 0.0)")
        elif geom_type in ['cube', 'box']:
            size = geometry.get('size', [1.0, 1.0, 1.0])
            params.append(f"vec4({size[0]:.3f}, {size[1]:.3f}, {size[2]:.3f}, 0.0)")
        elif geom_type == 'cone':
            r1 = geometry.get('radius1', 1.0)
            r2 = geometry.get('radius2', 0.0)
            h = geometry.get('height', 2.0)
            params.append(f"vec4({r1:.3f}, {h:.3f}, {r2:.3f}, 0.0)")
        elif geom_type == 'torus':
            r1 = geometry.get('radius1', 1.0)
            r2 = geometry.get('radius2', 0.3)
            params.append(f"vec4({r1:.3f}, {r2:.3f}, 0.0, 0.0)")
        elif geom_type == 'plane':
            normal = geometry.get('normal', [0, 1, 0])
            params.append(f"vec4({normal[0]:.1f}, {normal[1]:.1f}, {normal[2]:.1f}, 0.0)")
        else:
            params.append("vec4(1.0, 0.0, 0.0, 0.0)")
        
        # params[2]: rotation/direction
        rotation = transform.get('hpr', transform.get('rot', [0, 0, 0]))
        params.append(f"vec4({rotation[0]:.1f}, {rotation[1]:.1f}, {rotation[2]:.1f}, 0.0)")
        
        # params[3]: color
        params.append(f"vec4({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f}, 0.0)")
        
        return params
    
    def generate_shader_code(self, phg_script: str) -> str:
        """Generate complete GLSL shader code"""
        self.nodes = self.parse_phg(phg_script)
        
        # Collect all geometries
        primitives = []
        for node_name, properties in self.nodes.items():
            if 'geometry' in properties:
                primitives.append((node_name, properties))
        
        self.primitive_count = len(primitives)
        
        if self.primitive_count == 0:
            return self._create_empty_shader()
        
        # Generate shader code
        shader_code = self._create_shader_template()
        shader_code = self._insert_primitives(shader_code, primitives)
        
        return shader_code
    
    def _create_empty_shader(self) -> str:
        """Create shader for empty scene"""
        return """
#version 330 core
out vec4 fragColor;
uniform float time;
uniform vec2 resolution;
uniform vec2 mouse;
uniform vec3 cameraPosition;
uniform vec3 cameraTarget;
uniform vec3 cameraUp;
uniform float cameraFov;

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 color = vec3(0.1, 0.2, 0.4);
    fragColor = vec4(color, 1.0);
}
"""
    
    def _create_shader_template(self) -> str:
        """Create shader template with camera support"""
        return """
#version 330 core
out vec4 fragColor;

uniform float time;
uniform vec2 resolution;
uniform vec2 mouse;
uniform vec3 cameraPosition;
uniform vec3 cameraTarget;
uniform vec3 cameraUp;
uniform float cameraFov;

#define MAX_STEPS 100
#define MAX_DIST 200.0
#define SURF_DIST 0.001

// Primitive type enum
#define SPHERE 0
#define BOX 1
#define CYLINDER 2
#define TORUS 3
#define PLANE 4
#define CONE 5

// Primitive parameter definitions
{primitive_definitions}

// SDF function definitions
float sdfSphere(vec3 p, vec4 params) {
    return length(p) - params.x;
}

float sdfBox(vec3 p, vec4 params) {
    vec3 b = params.xyz;
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float sdfCylinder(vec3 p, vec4 params) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(params.x, params.y);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

float sdfTorus(vec3 p, vec4 params) {
    vec2 q = vec2(length(p.xz) - params.x, p.y);
    return length(q) - params.y;
}

float sdfPlane(vec3 p, vec4 params) {
    return dot(p, normalize(params.xyz));
}

float sdfCone(vec3 p, vec4 params) {
    // params.x = base radius, params.y = height, params.z = top radius
    vec2 q = vec2(length(p.xz), -p.y);
    float d = length(q);
    float angle = atan(params.z - params.x, params.y);
    float c = cos(angle);
    float s = sin(angle);
    return max(dot(q, vec2(c, s)), -p.y - params.y);
}

// Unified SDF dispatcher function
float mapPrimitive(vec3 p, vec4 params[4]) {
    int type = int(params[0].w);
    
    if (type == SPHERE) return sdfSphere(p - params[0].xyz, params[1]);
    if (type == BOX) return sdfBox(p - params[0].xyz, params[1]);
    if (type == CYLINDER) return sdfCylinder(p - params[0].xyz, params[1]);
    if (type == TORUS) return sdfTorus(p - params[0].xyz, params[1]);
    if (type == PLANE) return sdfPlane(p - params[0].xyz, params[1]);
    if (type == CONE) return sdfCone(p - params[0].xyz, params[1]);
    
    return 1000.0;
}

// Scene SDF
float mapScene(vec3 p) {
    float minDist = 1000.0;
    
{primitive_calls}
    
    return minDist;
}

// Normal calculation
vec3 calculateNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        mapScene(p + e.xyy) - mapScene(p - e.xyy),
        mapScene(p + e.yxy) - mapScene(p - e.yxy),
        mapScene(p + e.yyx) - mapScene(p - e.yyx)
    ));
}

// Ray marching
float rayMarch(vec3 ro, vec3 rd) {
    float depth = 0.0;
    
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + depth * rd;
        float dist = mapScene(p);
        depth += dist;
        
        if (dist < SURF_DIST || depth > MAX_DIST) break;
    }
    
    return depth;
}

// Get hit object color
vec3 getObjectColor(vec3 p) {
    float minDist = 1000.0;
    vec3 color = vec3(0.5);
    
{color_calls}
    
    return color;
}

// Calculate camera ray direction using camera uniforms
vec3 getCameraRay(vec2 uv, vec3 camPos, vec3 camTarget, vec3 camUp, float fov) {
    vec3 forward = normalize(camTarget - camPos);
    vec3 right = normalize(cross(forward, camUp));
    vec3 up = normalize(cross(right, forward));
    
    float tanFov = tan(radians(fov) * 0.5);
    vec3 rayDir = normalize(forward + right * uv.x * tanFov * (resolution.x / resolution.y) + up * uv.y * tanFov);
    
    return rayDir;
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * resolution.xy) / resolution.y;
    
    // Use camera uniforms from Python for ray direction
    vec3 ro = cameraPosition;
    vec3 rd = getCameraRay(uv, cameraPosition, cameraTarget, cameraUp, cameraFov);
    
    // Ray marching
    float dist = rayMarch(ro, rd);
    
    // Shading
    vec3 color = vec3(0.1, 0.2, 0.4);
    
    if (dist < MAX_DIST) {
        vec3 p = ro + rd * dist;
        vec3 normal = calculateNormal(p);
        vec3 objColor = getObjectColor(p);
        
        // Simple lighting
        vec3 lightDir = normalize(vec3(1.0, 3.0, 2.0));
        float diff = max(dot(normal, lightDir), 0.2);
        
        color = objColor * diff;
        
        // Add some ambient occlusion
        float ao = 1.0 - (1.0 / (1.0 + dist * 0.1));
        color *= ao;
    }
    
    fragColor = vec4(color, 1.0);
}
"""
    
    def _insert_primitives(self, template: str, primitives: List[Tuple[str, Dict]]) -> str:
        """Insert primitive definitions and call code"""
        primitive_definitions = []
        primitive_calls = []
        color_calls = []
        
        for i, (node_name, properties) in enumerate(primitives):
            geometry = properties['geometry']
            params = self.geometry_to_sdf_params(geometry, properties)
            
            # Generate primitive parameter definitions
            primitive_definitions.append(f"// {node_name}")
            for j, param in enumerate(params):
                primitive_definitions.append(f"vec4 prim_{i}_{j} = {param};")
            primitive_definitions.append("")
            
            # Generate SDF calls
            primitive_calls.append(f"    // {node_name}")
            primitive_calls.append(f"    vec4 prim_{i}[4] = vec4[4](prim_{i}_0, prim_{i}_1, prim_{i}_2, prim_{i}_3);")
            primitive_calls.append(f"    float dist_{i} = mapPrimitive(p, prim_{i});")
            primitive_calls.append(f"    minDist = min(minDist, dist_{i});")
            primitive_calls.append("")
            
            # Generate color calls
            color_calls.append(f"    // {node_name}")
            color_calls.append(f"    vec4 color_prim_{i}[4] = vec4[4](prim_{i}_0, prim_{i}_1, prim_{i}_2, prim_{i}_3);")
            color_calls.append(f"    float color_dist_{i} = mapPrimitive(p, color_prim_{i});")
            color_calls.append(f"    if (color_dist_{i} < SURF_DIST && color_dist_{i} < minDist) {{")
            color_calls.append(f"        minDist = color_dist_{i};")
            color_calls.append(f"        color = prim_{i}_3.xyz;")
            color_calls.append(f"    }}")
            color_calls.append("")
        
        # Replace placeholders in template
        shader_code = template.replace("{primitive_definitions}", "\n".join(primitive_definitions))
        shader_code = shader_code.replace("{primitive_calls}", "\n".join(primitive_calls))
        shader_code = shader_code.replace("{color_calls}", "\n".join(color_calls))
        
        return shader_code

# Convenient conversion function
def phg_to_shader(phg_script: str) -> str:
    """
    Convert PHG script to GLSL shader code
    
    Args:
        phg_script: PHG script string
        
    Returns:
        shader_code: GLSL shader code
    """
    converter = PHGToShaderConverter()
    return converter.generate_shader_code(phg_script)