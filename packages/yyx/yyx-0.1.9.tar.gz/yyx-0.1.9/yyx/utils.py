import os
from pathlib import Path
import sys
import inspect
from typing import Union, Tuple, Optional
def code2prompt_cmd():
    """
    交互式生成code2prompt命令，优化了排除文件类型的输入方式，更友好的交互体验
    """
    print("===== code2prompt命令生成工具 =====")

    # 1. 获取项目路径（待处理的代码目录）
    while True:
        project_path = input("请输入项目根目录路径：").strip()
        if os.path.isdir(project_path):
            break
        print(f"错误：路径 '{project_path}' 不存在或不是目录，请重新输入！")

    # 2. 获取输出路径（生成文件的保存目录）
    while True:
        output_dir = input("请输入输出文件保存目录：").strip()
        if os.path.isdir(output_dir):
            break
        # 询问是否创建不存在的目录
        create = input(f"目录 '{output_dir}' 不存在，是否创建？(y/n)：").strip().lower()
        if create == 'y':
            os.makedirs(output_dir, exist_ok=True)
            print(f"已创建目录：{output_dir}")
            break
        print("请重新输入输出目录！")

    # 3. 获取输出文件名
    while True:
        filename = input("请输入输出文件名（例如：ai_prompt.md）：").strip()
        if filename:
            # 确保文件名包含扩展名（默认.md）
            if '.' not in filename:
                filename += '.md'
                print(f"自动补充扩展名，文件名变为：{filename}")
            break
        print("文件名不能为空，请重新输入！")

    # 4. 是否需要显示行号
    line_number = input("是否需要包含行号？(y/n，默认y)：").strip().lower()
    line_number_flag = "--line-number" if (not line_number or line_number == 'y') else ""

    # 5. 优化：排除文件类型（支持空格分隔，自动处理为*.xxx格式，默认选项更清晰）
    default_exclude_types = ["txt", "logs", "csv", "cmd", "sh", "md"]  # 仅保留类型名
    default_exclude_display = "、".join(default_exclude_types)  # 显示为“txt、logs、csv...”
    exclude_input = input(
        f"请输入需要排除的文件类型（用空格分隔；直接回车使用默认：{default_exclude_display}）："
    ).strip()

    if not exclude_input:
        # 使用默认排除类型
        exclude_files = ",".join([f"*.{t}" for t in default_exclude_types])
    else:
        # 处理用户输入（空格分隔转成*.xxx,*.yyy格式）
        exclude_types = exclude_input.split()
        exclude_files = ",".join([f"*.{t.lstrip('.')}" for t in exclude_types])  # 兼容用户输入带.的情况（如.txt）

    # 拼接完整输出文件路径
    output_path = os.path.join(output_dir, filename)

    # 生成最终命令（处理路径中的空格，用双引号包裹）
    cmd_parts = [
        "code2prompt",
        f'-p "{project_path}"',
        f'-o "{output_path}"',
        line_number_flag,
        f'-e "{exclude_files}"'
    ]
    # 过滤空值（如不显示行号时）
    cmd = ' '.join(part for part in cmd_parts if part)

    print("\n===== 生成的命令如下 =====")
    print(cmd)
    return cmd
def add_path_to_sys(path: Union[str, Path]) -> Optional[str]:
    """
    将指定路径添加到sys.path中（自动转换为绝对路径，避免重复添加）
    :param path: 要添加的路径（支持字符串或Path对象）
    :return: 成功添加返回路径字符串，已存在返回None
    """
    # 转换为绝对路径字符串（统一格式，避免因相对路径导致的重复）
    abs_path = str(Path(path).resolve())

    # 检查是否已存在，避免重复添加
    if abs_path not in sys.path:
        sys.path.insert(0, abs_path)  # 插入到首位，优先搜索
        print(f"已添加路径到搜索路径：{abs_path}")
        return abs_path
    else:
        print(f"路径已在搜索路径中，无需重复添加：{abs_path}")
        return None
def remove_path_from_sys(path: Union[str, Path]) -> Tuple[bool, str]:
    """
    从sys.path中移除指定路径（自动转换为绝对路径，确保匹配）
    :param path: 要移除的路径（支持字符串或Path对象）
    :return: (是否成功移除, 处理后的绝对路径)
    """
    # 转换为绝对路径字符串（与添加时的格式保持一致）
    abs_path = str(Path(path).resolve())

    # 尝试移除路径
    if abs_path in sys.path:
        sys.path.remove(abs_path)
        print(f"已从搜索路径中移除：{abs_path}")
        return True, abs_path
    else:
        print(f"路径不在搜索路径中，无法移除：{abs_path}")
        return False, abs_path

def copy_from_dataset(target_path):
    """
    从固定源文件夹复制文件到目标路径
    :param target_path: 目标路径（文件夹或具体文件路径）
    """
    source_folder = r"D:\时序预测\常用数据集"

    if not os.path.exists(source_folder):
        print(f"错误：源文件夹不存在 → {source_folder}")
        return

    if os.path.isdir(target_path):
        for filename in os.listdir(source_folder):
            source_file = os.path.join(source_folder, filename)
            if os.path.isfile(source_file):
                try:
                    shutil.copy2(source_file, target_path)
                    print(f"已复制 {filename} 到 {target_path}")
                except Exception as e:
                    print(f"复制 {filename} 失败：{e}")
    else:
        filename = os.path.basename(target_path)
        source_file = os.path.join(source_folder, filename)
        if os.path.isfile(source_file):
            try:
                shutil.copy2(source_file, target_path)
                print(f"已复制到：{target_path}")
            except Exception as e:
                print(f"复制失败：{e}")
        else:
            print(f"源文件夹中不存在文件：{filename}")
