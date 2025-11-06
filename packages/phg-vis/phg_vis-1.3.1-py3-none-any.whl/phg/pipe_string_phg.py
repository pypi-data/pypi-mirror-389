"""
Pipe String to PHG Converter
============================

该模块提供了管道字符串转换为PHG（Python Graphics）脚本的功能。
支持世界坐标系和局部坐标系两种管道描述方式。

主要功能：
- world_pipe_to_phg: 世界坐标系管道转换
- local_pipe_to_phg: 局部坐标系管道转换
- world_pipestr_vis: 世界坐标系管道直接可视化
- local_pipestr_vis: 局部坐标系管道直接可视化

管道字符串格式：
- F: 前进 (Forward)
- B: 后退 (Back)
- R: 右转 (Right)
- L: 左转 (Left)
- U: 上转 (Up)
- D: 下转 (Down)
"""

import phg
from coordinate_system import vec3, quat, coord3

# 默认颜色和管径
DEFAULT_PIPE_COLOR = (0, 55, 255)
DEFAULT_PIPE_RADIUS = 0.3

def world_pipe_to_phg(world_pipe_str, start_c, pipe_color=DEFAULT_PIPE_COLOR, pipe_radius=DEFAULT_PIPE_RADIUS):
    """
    将世界坐标系下的管道字符串转换为PHG脚本
    
    参数:
        world_pipe_str: 世界坐标系管道字符串（如 "FFRUD"）
        start_c: 起始坐标系
        pipe_color: 管道颜色，格式为(R, G, B)元组
        pipe_radius: 管道半径
    
    返回:
        PHG脚本字符串
    """
    
    # 世界坐标系方向定义
    world_directions = {
        'F': vec3(0, 0, 1),   # 前（世界Z+）
        'B': vec3(0, 0, -1),  # 后（世界Z-）
        'R': vec3(1, 0, 0),   # 右（世界X+）
        'L': vec3(-1, 0, 0),  # 左（世界X-）
        'U': vec3(0, 1, 0),   # 上（世界Y+）
        'D': vec3(0, -1, 0)   # 下（世界Y-）
    }

    # 解析颜色
    r, g, b = pipe_color
    
    # 管道部件映射（所有部件使用固定长度1.0）
    pipe_components = {
        'F': f'{{{{rgb:{r},{g},{b};md:cylinder {pipe_radius} 1.0;rx:90;z:-0.5;}};z:1.0}}',
        'B': f'{{{{rgb:{r},{g},{b};md:cylinder {pipe_radius} 1.0;rx:-90;z:{-1.0-0.5};}};z:1.0}}',
        'R': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}ry:90;x:1.0;z:-1.0}}}},{{x:1.0;ry:-90;}}',
        'L': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}ry:-90;m:x;z:-1.0;x:-1.0}}}},{{x:-1.0;ry:90;}}',
        'U': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}rz:90;y:1.0;z:-1}}}},{{y:1.0;rx:90;}}',
        'D': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}rz:-90;y:-1;z:-1}}}},{{y:-1.0;rx:-90;}}'
    }

    # 初始化当前坐标系（使用起始坐标系）
    cur_c = coord3(start_c.o, start_c.Q())
    
    # 存储所有管道部件的脚本
    script_parts = []
    
    # 遍历管道字符串中的每个字符
    for move_char in world_pipe_str:
        if move_char not in pipe_components:
            print(f"警告: 未知的管道字符 '{move_char}'，已跳过")
            continue
        
        # 获取当前移动在世界坐标系中的方向
        world_dir = world_directions[move_char]
        
        # 将世界方向转换到当前局部坐标系
        local_dir = vec3(
            world_dir.dot(cur_c.ux),  # 在局部X轴的分量
            world_dir.dot(cur_c.uy),  # 在局部Y轴的分量
            world_dir.dot(cur_c.uz)   # 在局部Z轴的分量
        )
        
        # 找到绝对值最大的分量来确定主要移动方向
        abs_components = [abs(local_dir.x), abs(local_dir.y), abs(local_dir.z)]
        max_idx = abs_components.index(max(abs_components))
        
        # 根据最大分量确定局部移动方向
        if max_idx == 0:  # X轴
            local_move = 'R' if local_dir.x > 0 else 'L'
        elif max_idx == 1:  # Y轴
            local_move = 'U' if local_dir.y > 0 else 'D'
        else:  # Z轴
            local_move = 'F' if local_dir.z > 0 else 'B'
        
        # 添加对应的管道部件脚本
        script_parts.append(pipe_components[local_move])
        
        # 更新当前坐标系（模拟移动后的新位置和方向）
        if local_move == 'F':
            # 前进：沿局部Z轴正方向移动1.0单位
            cur_c = cur_c * coord3(vec3(0, 0, 1.0))
        elif local_move == 'B':
            # 后退：沿局部Z轴负方向移动1.0单位
            cur_c = cur_c * coord3(vec3(0, 0, -1.0))
        elif local_move == 'R':
            # 右转：绕Y轴旋转-90度，然后沿X轴移动1.0单位
            rotation = quat(-3.1416 / 2, cur_c.uy)
            cur_c = cur_c * rotation
            cur_c = cur_c * coord3(vec3(1.0, 0, 0))
        elif local_move == 'L':
            # 左转：绕Y轴旋转90度，然后沿X轴移动1.0单位
            rotation = quat(3.1416 / 2, cur_c.uy)
            cur_c = cur_c * rotation
            cur_c = cur_c * coord3(vec3(-1.0, 0, 0))
        elif local_move == 'U':
            # 上转：绕X轴旋转90度，然后沿Y轴移动1.0单位
            rotation = quat(3.1416 / 2, cur_c.ux)
            cur_c = cur_c * rotation
            cur_c = cur_c * coord3(vec3(0, 1.0, 0))
        elif local_move == 'D':
            # 下转：绕X轴旋转-90度，然后沿Y轴移动1.0单位
            rotation = quat(-3.1416 / 2, cur_c.ux)
            cur_c = cur_c * rotation
            cur_c = cur_c * coord3(vec3(0, -1.0, 0))

    # 组合所有管道部件的脚本
    inner_script = ',\n'.join(script_parts)
    
    # 获取起始坐标系的四元数
    q = start_c.Q()
    
    # 构建完整的PHG脚本
    complete_script = f"""{{
    {{xyz:{start_c.o.x},{start_c.o.y},{start_c.o.z};q:{q.w},{q.x},{q.y},{q.z};s:0.5;
    <{inner_script}>}}
    }}"""
    
    return complete_script


def local_pipe_to_phg(local_pipe_str, start_c, pipe_color=DEFAULT_PIPE_COLOR, pipe_radius=DEFAULT_PIPE_RADIUS):
    """
    将局部坐标系下的管道字符串转换为PHG脚本

    参数:
        local_pipe_str: 局部坐标系管道字符串（如 "FFRUD"）
        start_c: 起始坐标系
        pipe_color: 管道颜色，格式为(R, G, B)元组
        pipe_radius: 管道半径

    返回:
        PHG脚本字符串
    """

    # 解析颜色
    r, g, b = pipe_color

    # 管道部件映射（所有部件使用固定长度1.0）
    pipe_components = {
        'F': f'{{{{rgb:{r},{g},{b};md:cylinder {pipe_radius} 1.0;rx:90;z:-0.5;}};z:1.0}}',
        'B': f'{{{{rgb:{r},{g},{b};md:cylinder {pipe_radius} 1.0;rx:-90;z:{-1.0-0.5};}};z:1.0}}',
        'R': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}ry:90;x:1.0;z:-1.0}}}},{{x:1.0;ry:-90;}}',
        'L': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}ry:-90;m:x;z:-1.0;x:-1.0}}}},{{x:-1.0;ry:90;}}',
        'U': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}rz:90;y:1.0;z:-1}}}},{{y:1.0;rx:90;}}',
        'D': f'{{{{{{rgb:{r},{g},{b};md:elbow 90 0.5 {pipe_radius};x:0.5;z:0.5;}}rz:-90;y:-1;z:-1}}}},{{y:-1.0;rx:-90;}}'
    }

    # 存储所有管道部件的脚本
    script_parts = []

    # 遍历管道字符串中的每个字符
    for move_char in local_pipe_str:
        if move_char not in pipe_components:
            print(f"警告: 未知的管道字符 '{move_char}'，已跳过")
            continue

        # 直接使用局部坐标系的移动命令
        script_parts.append(pipe_components[move_char])

    # 组合所有管道部件的脚本
    inner_script = ',\n'.join(script_parts)

    # 获取起始坐标系的四元数
    q = start_c.Q()

    # 构建完整的PHG脚本
    complete_script = f"""{{
    {{xyz:{start_c.o.x},{start_c.o.y},{start_c.o.z};q:{q.w},{q.x},{q.y},{q.z};s:0.5;
    <{inner_script}>}}
    }}"""

    return complete_script


def world_pipestr_vis(world_pipe_str, start_c=None, pipe_color=DEFAULT_PIPE_COLOR, pipe_radius=DEFAULT_PIPE_RADIUS):
    """
    世界坐标系管道字符串直接可视化

    参数:
        world_pipe_str: 世界坐标系管道字符串（如 "FFRUD"）
        start_c: 起始坐标系，默认为原点
        pipe_color: 管道颜色，格式为(R, G, B)元组
        pipe_radius: 管道半径

    返回:
        PHG脚本字符串
    """
    # 如果没有提供起始坐标系，使用默认原点
    if start_c is None:
        start_c = coord3(vec3(0, 0, 0), quat(1, 0, 0, 0))

    # 生成PHG脚本
    phg_script = world_pipe_to_phg(world_pipe_str, start_c, pipe_color, pipe_radius)

    # 调用可视化函数
    try:
        from .visphg import vis
        vis(phg_script)
    except ImportError:
        print("警告: 无法导入可视化模块，返回PHG脚本")

    return phg_script


def local_pipestr_vis(local_pipe_str, start_c=None, pipe_color=DEFAULT_PIPE_COLOR, pipe_radius=DEFAULT_PIPE_RADIUS):
    """
    局部坐标系管道字符串直接可视化

    参数:
        local_pipe_str: 局部坐标系管道字符串（如 "FFRUD"）
        start_c: 起始坐标系，默认为原点
        pipe_color: 管道颜色，格式为(R, G, B)元组
        pipe_radius: 管道半径

    返回:
        PHG脚本字符串
    """
    # 如果没有提供起始坐标系，使用默认原点
    if start_c is None:
        start_c = coord3(vec3(0, 0, 0), quat(1, 0, 0, 0))

    # 生成PHG脚本
    phg_script = local_pipe_to_phg(local_pipe_str, start_c, pipe_color, pipe_radius)

    # 调用可视化函数
    try:
        from .visphg import vis
        vis(phg_script)
    except ImportError:
        print("警告: 无法导入可视化模块，返回PHG脚本")

    return phg_script


# 使用示例
if __name__ == "__main__":
    # 创建起始坐标系（示例）
    start_coord = coord3(vec3(0, 0, 0), quat(1, 0, 0, 0))

    # 示例1: 世界坐标系管道字符串
    example_world_pipe = "FFRUD"  # 前进2次，右转，上转，下转
    print("世界坐标系管道示例:")
    phg_script = world_pipe_to_phg(example_world_pipe, start_coord)
    print("生成的PHG脚本:")
    print(phg_script)
    print()

    # 示例2: 局部坐标系管道字符串
    example_local_pipe = "FFRUD"  # 在局部坐标系中的移动
    print("局部坐标系管道示例:")
    phg_script = local_pipe_to_phg(example_local_pipe, start_coord)
    print("生成的PHG脚本:")
    print(phg_script)
    print()

    # 示例3: 直接可视化
    print("直接可视化示例:")
    # world_pipestr_vis(example_world_pipe)  # 世界坐标系可视化
    # local_pipestr_vis(example_local_pipe)  # 局部坐标系可视化