"""
__init__.py
PHG主库 - 集成PHG到Shader转换功能
"""

from .visphg import vis, image
from .shader_render import ShaderRenderer, render_shader
from .phg_to_shader import PHGToShaderConverter, phg_to_shader

# 扩展ShaderRenderer类以支持PHG直接渲染
class PHGShaderRenderer(ShaderRenderer):
    """支持PHG直接渲染的Shader渲染器"""
    
    def render_phg(self, phg_script: str, duration=0, interactive=True):
        """
        渲染PHG脚本
        
        参数:
            phg_script: PHG脚本代码
            duration: 渲染持续时间
            interactive: 是否允许交互
            
        返回:
            success: 是否成功渲染
        """
        converter = PHGToShaderConverter()
        shader_code = converter.generate_shader_code(phg_script)
        
        if not shader_code:
            print("错误: PHG转换失败")
            return False
            
        return self.render_shader(shader_code, duration, interactive)

# 便捷函数
def render_phg(phg_script: str, width=800, height=600, duration=0, title="PHG Renderer"):
    """
    直接渲染PHG脚本
    
    参数:
        phg_script: PHG脚本代码
        width: 窗口宽度
        height: 窗口高度  
        duration: 渲染持续时间
        title: 窗口标题
    """
    renderer = PHGShaderRenderer(width, height, title)
    success = renderer.render_phg(phg_script, duration)
    renderer.close()
    return success

def convert_phg_to_shader(phg_script: str) -> str:
    """
    将PHG脚本转换为GLSL着色器代码
    
    参数:
        phg_script: PHG脚本
        
    返回:
        shader_code: GLSL着色器代码
    """
    return phg_to_shader(phg_script)

__all__ = [
    'vis', 
    'image', 
    'ShaderRenderer', 
    'render_shader',
    'PHGToShaderConverter',
    'PHGShaderRenderer', 
    'render_phg',
    'convert_phg_to_shader',
    'phg_to_shader'
]

__version__ = "0.2.0"
__author__ = "PHG Development Team"
__description__ = "Python Graphics Library with PHG to Shader conversion"

# 包初始化信息
print(f"PHG {__version__} - {__description__}")
print("PHG to Shader转换器已加载")