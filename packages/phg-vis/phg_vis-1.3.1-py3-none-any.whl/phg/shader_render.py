import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import sys
import time

class Camera:
    """Camera class with mouse interaction controls"""
    
    def __init__(self):
        # Start further back to see the whole scene
        self.position = np.array([0.0, 3.0, 12.0], dtype=np.float32)  # Camera position - further back
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)     # Look at target
        self.up = np.array([0.0, 1.0, 0.0], dtype=np.float32)         # Up direction
        
        # Camera parameters
        self.fov = 45.0  # Field of view
        self.zoom_speed = 0.5  # Increased zoom speed
        self.rotate_speed = 0.01  # Increased rotate speed
        self.pan_speed = 0.02  # Increased pan speed
        
        # Mouse state
        self.last_mouse_pos = None
        self.is_rotating = False
        self.is_panning = False
        
    def zoom(self, delta):
        """Zoom control"""
        direction = self.target - self.position
        distance = np.linalg.norm(direction)
        
        # Limit min and max distance
        min_distance = 1.0
        max_distance = 100.0
        
        new_distance = distance * (1.0 - delta * self.zoom_speed)
        new_distance = np.clip(new_distance, min_distance, max_distance)
        
        self.position = self.target - direction * (new_distance / distance)
        print(f"Zoom: position={self.position}, distance={new_distance}")
    
    def rotate(self, delta_x, delta_y):
        """Rotation control"""
        # Calculate vector from target to camera (inverse of camera to target)
        direction = self.position - self.target
        distance = np.linalg.norm(direction)
        
        if distance < 0.001:
            return
            
        # Spherical coordinates rotation
        # Convert to spherical coordinates
        theta = np.arctan2(direction[0], direction[2])  # Horizontal angle (around Y axis)
        phi = np.arctan2(direction[1], np.sqrt(direction[0]**2 + direction[2]**2))  # Vertical angle
        
        # Apply rotation (inverted for more intuitive control)
        theta -= delta_x * self.rotate_speed
        phi += delta_y * self.rotate_speed  # Inverted Y for more natural control
        
        # Limit vertical angle (avoid flipping)
        phi = np.clip(phi, -np.pi/2 + 0.1, np.pi/2 - 0.1)
        
        # Convert back to Cartesian coordinates
        new_x = distance * np.sin(theta) * np.cos(phi)
        new_y = distance * np.sin(phi)
        new_z = distance * np.cos(theta) * np.cos(phi)
        
        self.position = self.target + np.array([new_x, new_y, new_z])
        
        print(f"Rotate: position={self.position}")
    
    def pan(self, delta_x, delta_y):
        """Pan control"""
        # Calculate camera coordinate system
        forward = normalize(self.target - self.position)
        right = normalize(np.cross(forward, self.up))
        up = normalize(np.cross(right, forward))
        
        # Apply pan (inverted for more intuitive control)
        pan_distance = 0.1
        pan_vector = -delta_x * right * self.pan_speed + delta_y * up * self.pan_speed
        
        self.position += pan_vector
        self.target += pan_vector
        
        print(f"Pan: position={self.position}, target={self.target}")

def normalize(v):
    """Normalize a vector"""
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

class ShaderRenderer:
    """
    Shader renderer class for visualizing GLSL shaders
    
    Usage:
    renderer = ShaderRenderer()
    renderer.render_shader(fragment_shader_code)
    """
    
    def __init__(self, width=800, height=600, title="Shader Renderer"):
        """
        Initialize Shader renderer
        
        Args:
            width: Window width
            height: Window height  
            title: Window title
        """
        self.width = width
        self.height = height
        self.title = title
        self.is_running = False
        self.shader_program = None
        self.start_time = 0
        self.camera = Camera()
        self.show_help = True
        
        self.vertex_shader_src = """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec2 aTexCoord;

        out vec2 TexCoord;

        void main()
        {
            gl_Position = vec4(aPos, 1.0);
            TexCoord = aTexCoord;
        }
        """
        
        self._init_pygame()
        self._init_opengl()
        self._create_geometry()
        self._init_font()
    
    def _init_pygame(self):
        """Initialize Pygame and OpenGL context"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption(self.title)
    
    def _init_opengl(self):
        """Initialize OpenGL settings"""
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    def _init_font(self):
        """Initialize font for text rendering"""
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
    
    def _create_geometry(self):
        """Create geometry required for rendering"""
        # Vertex data: position + texture coordinates
        self.vertices = np.array([
            # Position          # Texture coordinates
            -1.0, -1.0, 0.0, 0.0, 0.0,
             1.0, -1.0, 0.0, 1.0, 0.0,
             1.0,  1.0, 0.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 0.0, 1.0
        ], dtype=np.float32)
        
        self.indices = np.array([
            0, 1, 2,
            2, 3, 0
        ], dtype=np.uint32)
        
        # Create VAO, VBO, EBO
        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)
        self.EBO = glGenBuffers(1)
        
        glBindVertexArray(self.VAO)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        # Position attribute
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * self.vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Texture coordinate attribute
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * self.vertices.itemsize, ctypes.c_void_p(3 * self.vertices.itemsize))
        glEnableVertexAttribArray(1)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
    
    def _compile_shader(self, fragment_src):
        """
        Compile shader program
        
        Args:
            fragment_src: Fragment shader code
            
        Returns:
            shader_program: Compiled shader program, None if failed
        """
        try:
            vertex_shader = compileShader(self.vertex_shader_src, GL_VERTEX_SHADER)
            fragment_shader = compileShader(fragment_src, GL_FRAGMENT_SHADER)
            shader_program = compileProgram(vertex_shader, fragment_shader)
            return shader_program
        except Exception as e:
            print(f"Shader compilation error: {e}")
            return None
    
    def _render_help_text(self):
        """Render help text on screen"""
        # Switch to 2D rendering for text
        glDisable(GL_DEPTH_TEST)
        
        # Create a semi-transparent background for better readability
        help_lines = [
            "=== CAMERA CONTROLS ===",
            "LEFT CLICK + DRAG: Rotate Camera",
            "MIDDLE CLICK + DRAG: Pan Camera", 
            "MOUSE WHEEL: Zoom In/Out",
            "R: Reset Camera Position",
            "H: Toggle This Help",
            "ESC: Exit Renderer",
            "",
            "Camera debugging enabled - check console"
        ]
        
        y_offset = 20
        for i, line in enumerate(help_lines):
            if i == 0:  # Header
                text_surface = self.font.render(line, True, (255, 255, 0))
            else:
                text_surface = self.small_font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surface, (20, y_offset))
            y_offset += 22 if i == 0 else 18
        
        # Camera position info
        cam_info = [
            f"Camera Pos: ({self.camera.position[0]:.1f}, {self.camera.position[1]:.1f}, {self.camera.position[2]:.1f})",
            f"Camera Target: ({self.camera.target[0]:.1f}, {self.camera.target[1]:.1f}, {self.camera.target[2]:.1f})"
        ]
        
        y_offset += 10
        for info in cam_info:
            text_surface = self.small_font.render(info, True, (0, 255, 255))
            self.screen.blit(text_surface, (20, y_offset))
            y_offset += 18
        
        glEnable(GL_DEPTH_TEST)
    
    def render_shader(self, fragment_shader, duration=0, interactive=True):
        """
        Render specified shader
        
        Args:
            fragment_shader: Fragment shader code string
            duration: Render duration in seconds, 0 for infinite
            interactive: Allow interaction (ESC to exit)
            
        Returns:
            success: Whether rendering was successful
        """
        # Compile shader
        self.shader_program = self._compile_shader(fragment_shader)
        if not self.shader_program:
            return False
        
        # Get uniform locations
        time_loc = glGetUniformLocation(self.shader_program, "time")
        resolution_loc = glGetUniformLocation(self.shader_program, "resolution")
        mouse_loc = glGetUniformLocation(self.shader_program, "mouse")
        camera_pos_loc = glGetUniformLocation(self.shader_program, "cameraPosition")
        camera_target_loc = glGetUniformLocation(self.shader_program, "cameraTarget")
        camera_up_loc = glGetUniformLocation(self.shader_program, "cameraUp")
        camera_fov_loc = glGetUniformLocation(self.shader_program, "cameraFov")
        
        self.is_running = True
        self.start_time = time.time()
        clock = pygame.time.Clock()
        
        mouse_pos = [0.0, 0.0]
        
        print("Renderer started! Camera controls:")
        print("- Left mouse button + drag: Rotate")
        print("- Middle mouse button + drag: Pan") 
        print("- Mouse wheel: Zoom")
        print("- R: Reset camera")
        print("- H: Toggle help")
        
        while self.is_running:
            current_time = time.time() - self.start_time
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and interactive:
                        self.is_running = False
                    elif event.key == pygame.K_r:  # R key to reset camera
                        self.camera = Camera()
                        print("Camera reset to default position")
                    elif event.key == pygame.K_h:  # H key to toggle help
                        self.show_help = not self.show_help
                        print(f"Help display: {'ON' if self.show_help else 'OFF'}")
                
                # Handle mouse events for camera control
                if interactive:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Left button - rotate
                            self.camera.is_rotating = True
                            self.camera.last_mouse_pos = event.pos
                            print("Rotation started")
                        elif event.button == 2:  # Middle button - pan
                            self.camera.is_panning = True
                            self.camera.last_mouse_pos = event.pos
                            print("Panning started")
                        elif event.button == 4:  # Wheel up - zoom in
                            self.camera.zoom(1.0)
                        elif event.button == 5:  # Wheel down - zoom out
                            self.camera.zoom(-1.0)
                            
                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:  # Left button release
                            self.camera.is_rotating = False
                            print("Rotation ended")
                        elif event.button == 2:  # Middle button release
                            self.camera.is_panning = False
                            print("Panning ended")
                        self.camera.last_mouse_pos = None
                        
                    elif event.type == pygame.MOUSEMOTION:
                        # Update mouse position for shader
                        mouse_pos[0] = event.pos[0] / self.width
                        mouse_pos[1] = 1.0 - event.pos[1] / self.height
                        
                        # Handle camera movement
                        if self.camera.last_mouse_pos is not None:
                            delta_x = event.pos[0] - self.camera.last_mouse_pos[0]
                            delta_y = event.pos[1] - self.camera.last_mouse_pos[1]
                            
                            if self.camera.is_rotating:
                                self.camera.rotate(delta_x, delta_y)
                            elif self.camera.is_panning:
                                self.camera.pan(delta_x, delta_y)
                            
                            self.camera.last_mouse_pos = event.pos
            
            # Check duration
            if duration > 0 and current_time >= duration:
                break
            
            # Render
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glUseProgram(self.shader_program)
            
            # Set uniforms
            if time_loc != -1:
                glUniform1f(time_loc, current_time)
            if resolution_loc != -1:
                glUniform2f(resolution_loc, self.width, self.height)
            if mouse_loc != -1:
                glUniform2f(mouse_loc, mouse_pos[0], mouse_pos[1])
            if camera_pos_loc != -1:
                glUniform3f(camera_pos_loc, 
                           self.camera.position[0], 
                           self.camera.position[1], 
                           self.camera.position[2])
            if camera_target_loc != -1:
                glUniform3f(camera_target_loc, 
                           self.camera.target[0], 
                           self.camera.target[1], 
                           self.camera.target[2])
            if camera_up_loc != -1:
                glUniform3f(camera_up_loc, 
                           self.camera.up[0], 
                           self.camera.up[1], 
                           self.camera.up[2])
            if camera_fov_loc != -1:
                glUniform1f(camera_fov_loc, self.camera.fov)
            
            glBindVertexArray(self.VAO)
            glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
            
            # Render help text if enabled
            if self.show_help:
                self._render_help_text()
            
            pygame.display.flip()
            clock.tick(60)
        
        return True
    
    def close(self):
        """Clean up resources"""
        if self.shader_program:
            glDeleteProgram(self.shader_program)
        pygame.quit()

# Convenience function
def render_shader(fragment_shader, width=800, height=600, duration=0, title="Shader Renderer"):
    """
    Convenience function: Directly render shader
    
    Args:
        fragment_shader: Fragment shader code
        width: Window width
        height: Window height
        duration: Render duration in seconds
        title: Window title
    """
    renderer = ShaderRenderer(width, height, title)
    success = renderer.render_shader(fragment_shader, duration)
    renderer.close()
    return success