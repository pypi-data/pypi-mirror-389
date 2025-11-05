# -*- coding: utf-8 -*-

# 卫星中心自动化建模工具

import argparse
import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime

import pandas as pd
from autowaterqualitymodeler.run import main as get_modeler

from .utils.encryption import encrypt_data_to_file

logger = logging.getLogger(__name__)


def check_pipe_input() -> bool:
    """检查是否有管道输入"""
    try:
        return not sys.stdin.isatty()
    except Exception:
        # 在某些环境下isatty可能不可用
        import select

        try:
            ready, _, _ = select.select([sys.stdin], [], [], 0)
            return bool(ready)
        except Exception:
            # 如果所有检测方法都失败，则默认为没有管道输入
            return False


def parse_data(spectrum_path: str, measure_paths: list[str]) -> pd.DataFrame:
    """解析光谱数据文件"""
    if os.path.exists(spectrum_path):
        # 读取光谱数据文件,包含样本日期，经度，纬度，第5列至第455列为波长，第456列之后为光谱反演的指标数据
        spectrum_uav_data = pd.read_csv(spectrum_path, header=0)
    else:
        logger.error(f"光谱数据文件路径无效: {spectrum_path}")
        raise FileNotFoundError(f"光谱数据文件路径无效: {spectrum_path}")

    measure_data = pd.DataFrame()
    for measure_path in measure_paths:
        if os.path.exists(measure_path):
            # 读取实测指标文件,包含样本编号，日期，经度，纬度，之后为实测指标数据
            data = pd.read_csv(measure_path, header=0)
            measure_data = pd.concat([measure_data, data])
        else:
            logger.error(f"测量数据文件路径无效: {measure_path}")
            continue

    if not spectrum_uav_data.empty:
        logger.info(f"光谱数据文件路径: {spectrum_path} 解析成功")
        logger.info(
            f"光谱数据时间、经度、纬度列名：{spectrum_uav_data.columns.tolist()[:3]}"
        )
        logger.info(f"光谱数据波长列名：{spectrum_uav_data.columns.tolist()[3:454]}")
        logger.info(f"光谱数据指标列名：{spectrum_uav_data.columns.tolist()[454:]}")
    else:
        logger.error(f"光谱数据文件路径: {spectrum_path} 解析失败")
        raise ValueError(f"光谱数据文件路径: {spectrum_path} 解析失败")

    if not measure_data.empty:
        logger.info(f"测量数据文件路径: {measure_paths} 解析成功")
        logger.info(
            f"测量数据时间、经度、纬度列名：{measure_data.columns.tolist()[:3]}"
        )
        logger.info(f"测量数据指标列名：{measure_data.columns.tolist()[3:]}")
    else:
        logger.error(f"测量数据文件路径: {measure_paths} 解析失败")
        raise ValueError(f"测量数据文件路径: {measure_paths} 解析失败")

    # 根据日期，经纬度匹配数据
    return match_data(spectrum_uav_data, measure_data)


def _find_best_match(
    measure_row: pd.Series,
    spectrum_copy: pd.DataFrame,
    date_col: str,
    lon_col: str,
    lat_col: str,
    spatial_tolerance: float,
    logger: logging.Logger,
) -> tuple[int | None, float, int | None]:
    """查找单个测量数据的最佳匹配光谱数据

    Args:
        measure_row: 单个测量数据行
        spectrum_copy: 光谱数据 DataFrame 副本
        date_col: 日期列名
        lon_col: 经度列名
        lat_col: 纬度列名
        spatial_tolerance: 经纬度容差
        logger: 日志记录器

    Returns:
        tuple[best_match_idx, best_distance, date_diff_days]:
            - best_match_idx: 匹配的光谱数据索引（None 表示未找到）
            - best_distance: 最小距离
            - date_diff_days: 日期差（天）
    """
    measure_date = measure_row[date_col]
    measure_lon = measure_row[lon_col]
    measure_lat = measure_row[lat_col]

    if pd.isna(measure_date) or pd.isna(measure_lon) or pd.isna(measure_lat):
        return None, float("inf"), None

    # 第一阶段：优先在同一天内找
    same_day_candidates = spectrum_copy[
        spectrum_copy[date_col].dt.date == measure_date.date()
    ].copy()

    best_match_idx = None
    best_distance = float("inf")
    date_diff_days = None

    if not same_day_candidates.empty:
        # 在同一天的数据中计算距离
        distances = (
            (same_day_candidates[lon_col] - measure_lon) ** 2
            + (same_day_candidates[lat_col] - measure_lat) ** 2
        ) ** 0.5

        # 找最近的
        best_idx_in_candidates = distances.idxmin()
        best_distance = distances.loc[best_idx_in_candidates]
        best_match_idx = best_idx_in_candidates
        date_diff_days = 0

        logger.debug(
            f"在同一天内找到候选，距离{best_distance:.4f}度"
        )

    # 第二阶段：如果同一天未找到，降级到前后一天范围
    if best_match_idx is None:
        date_lower = measure_date - pd.Timedelta(days=1)
        date_upper = measure_date + pd.Timedelta(days=1)

        nearby_candidates = spectrum_copy[
            (spectrum_copy[date_col] >= date_lower)
            & (spectrum_copy[date_col] <= date_upper)
        ].copy()

        if not nearby_candidates.empty:
            # 计算距离
            distances = (
                (nearby_candidates[lon_col] - measure_lon) ** 2
                + (nearby_candidates[lat_col] - measure_lat) ** 2
            ) ** 0.5

            # 找最近的
            best_idx_in_candidates = distances.idxmin()
            best_distance = distances.loc[best_idx_in_candidates]
            best_match_idx = best_idx_in_candidates
            date_diff_days = (
                nearby_candidates.loc[best_idx_in_candidates, date_col]
                - measure_date
            ).days

            logger.debug(
                f"在前后一天范围内找到候选，"
                f"日期差{date_diff_days}天，距离{best_distance:.4f}度"
            )
        else:
            logger.debug("在前后一天范围内无对应光谱数据")

    return best_match_idx, best_distance, date_diff_days


# 根据日期，经纬度匹配数据
def match_data(
    spectrum_uav_data: pd.DataFrame,
    measure_data: pd.DataFrame,
    date_col: str | None = None,
    lon_col: str | None = None,
    lat_col: str | None = None,
    spatial_tolerance: float = 0.01,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    根据日期和经纬度匹配光谱数据和测量数据

    匹配流程：
    1. 对于 measure_data 中的每个样本，在 spectrum_uav_data 中查找匹配
    2. 优先匹配同一天的数据中经纬度最近的
    3. 如果同一天无匹配，降级到前后一天范围内经纬度最近的样本

    结果：三个样本量相同的 DataFrame，每行是对应匹配的数据

    Args:
        spectrum_uav_data: 光谱数据DataFrame
        measure_data: 测量数据DataFrame
        date_col: 日期列名（默认自动检测为第0列）
        lon_col: 经度列名（默认自动检测为第1列）
        lat_col: 纬度列名（默认自动检测为第2列）
        spatial_tolerance: 经纬度容差（度，默认0.01度≈1.1km）

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            - 匹配后的光谱波长数据（第 3-453 列）
            - 匹配后的光谱指标数据（第 455+ 列）
            - 匹配后的测量数据（第 3+ 列）
            三个 DataFrame 行数相同，按匹配顺序对齐
    """
    if spectrum_uav_data.empty or measure_data.empty:
        raise ValueError("光谱数据或测量数据为空")

    # 自动检测列名
    if date_col is None:
        date_col = spectrum_uav_data.columns[0]
    if lon_col is None:
        lon_col = spectrum_uav_data.columns[1]
    if lat_col is None:
        lat_col = spectrum_uav_data.columns[2]

    logger.info(f'使用列名进行匹配: 日期={date_col}, 经度={lon_col}, 纬度={lat_col}')

    spectrum_copy = spectrum_uav_data.copy()
    measure_copy = measure_data.copy()

    # 确保日期列为datetime类型
    spectrum_copy[date_col] = pd.to_datetime(spectrum_copy[date_col], errors='coerce')
    measure_copy[date_col] = pd.to_datetime(measure_copy[date_col], errors='coerce')

    matched_spectrum_indices = []
    matched_measure_indices = []

    logger.info('开始匹配：measure_data 逐样本在 spectrum_uav_data 中查找')

    for measure_idx, measure_row in measure_copy.iterrows():
        # 使用辅助函数查找最佳匹配
        best_match_idx, best_distance, date_diff_days = _find_best_match(
            measure_row,
            spectrum_copy,
            date_col,
            lon_col,
            lat_col,
            spatial_tolerance,
            logger,
        )

        # 如果找到匹配且距离在容差范围内
        if best_match_idx is not None and best_distance <= spatial_tolerance:
            matched_spectrum_indices.append(best_match_idx)
            matched_measure_indices.append(measure_idx)

            logger.debug(
                f'匹配成功: 测量数据{measure_idx} <-> 光谱数据{best_match_idx}, '
                f'日期差{date_diff_days}天, 距离{best_distance:.4f}度'
            )
        else:
            if best_match_idx is None:
                logger.debug(f'测量数据 {measure_idx} 无可用匹配')
            else:
                logger.debug(
                    f'测量数据 {measure_idx} 的最近匹配距离 {best_distance:.4f}度 '
                    f'超出容差范围 {spatial_tolerance:.4f}度，跳过'
                )

    if not matched_spectrum_indices:
        logger.warning("未找到任何匹配的数据对")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # 按匹配顺序提取对应的行
    matched_spectrum_df = spectrum_copy.loc[matched_spectrum_indices].reset_index(
        drop=True
    )

    matched_measure_df = measure_copy.loc[matched_measure_indices].reset_index(
        drop=True
    )

    logger.info(
        f"匹配完成，共找到 {len(matched_spectrum_df)} 个匹配的数据对"
        f"（measure_data总数：{len(measure_copy)}）"
    )

    return (
        matched_spectrum_df.iloc[:, 3:454],
        matched_spectrum_df.iloc[:, 455:],
        matched_measure_df.iloc[:, 3:],
    )


# 格式化波段为数字
def format_band_name(df: pd.DataFrame) -> pd.DataFrame:
    """格式化波段名为数字类型

    将 DataFrame 的列名转换为数字类型（浮点数），
    用于光谱波长数据的标准化处理。
    支持字符串和数字列名的混合转换。

    Args:
        df: 输入 DataFrame，列名为波长信息（字符串或数字格式）

    Returns:
        列名转换为浮点数的 DataFrame

    Raises:
        ValueError: 所有列名都无法转换为数字时抛异常

    Examples:
        >>> df = pd.DataFrame({"400": [1, 2], "405": [3, 4]})
        >>> result = format_band_name(df)
        >>> result.columns.tolist()
        [400.0, 405.0]
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"输入必须是 pandas DataFrame，而非 {type(df).__name__}")

    if df.empty:
        logger.warning("输入 DataFrame 为空")
        return df

    # 创建新的列名映射
    rename_mapping: dict[str | int | float, float] = {}
    numeric_count = 0

    for col in df.columns:
        try:
            # 尝试将列名转换为浮点数
            numeric_col = float(col)
            rename_mapping[col] = numeric_col
            numeric_count += 1
        except (ValueError, TypeError) as e:
            logger.warning(f"列名 '{col}' 无法转换为数字: {e}，将保持原名")
            # 如果转换失败，保持原列名
            rename_mapping[col] = col

    # 检查是否有成功转换的列
    if numeric_count == 0:
        raise ValueError(
            f"未能将任何列名转换为数字类型。列名示例: {df.columns.tolist()[:5]}"
        )

    # 重命名列
    df_renamed = df.rename(columns=rename_mapping)

    # 获取数字列并统计
    numeric_cols = sorted(
        [col for col in df_renamed.columns if isinstance(col, (int, float))]
    )

    logger.info(
        f"波段格式化完成，共 {len(df.columns)} 列 → {len(numeric_cols)} 列数字波段"
    )

    if numeric_cols:
        logger.info(
            f"波段范围: {numeric_cols[0]:.1f} - {numeric_cols[-1]:.1f} nm "
            f"（共 {len(numeric_cols)} 个波段）"
        )

    return df_renamed


def standardize_indicator_names(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    """标准化指标名称

    将 DataFrame 的列名转换为标准指标名称。
    使用配置文件中定义的映射关系，支持大小写不敏感匹配。
    未映射的列转为小写后保留。

    Args:
        data: 包含原始指标列名的 DataFrame

    Returns:
        tuple[pd.DataFrame, list[str]]:
            - 重命名后的 DataFrame
            - 标准化后的列名列表

    Examples:
        >>> df = pd.DataFrame({"浊度": [1, 2], "turbidity": [3, 4]})
        >>> std_df, cols = standardize_indicator_names(df)
        >>> std_df.columns.tolist()
        ['Turb', 'Turb']
    """
    from satellitecenter.utils import IndicatorStandardizer

    try:
        standardizer = IndicatorStandardizer()
        return standardizer.standardize_dataframe(data, keep_unmapped=True)
    except Exception as e:
        logger.error(f"指标标准化失败: {e}")
        raise


def setup_memory_logging() -> logging.handlers.MemoryHandler:
    """初始化内存日志处理器，先将日志缓存在内存中

    Returns:
        MemoryHandler 实例
    """
    # 创建内存处理器（capacity=10000 表示最多缓存10000条日志）
    memory_handler = logging.handlers.MemoryHandler(capacity=10000, target=None)
    memory_handler.setLevel(logging.DEBUG)

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    memory_handler.setFormatter(formatter)

    # 配置根记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(memory_handler)

    return memory_handler


def setup_file_logging(log_dir: str, memory_handler: logging.handlers.MemoryHandler) -> str:
    """设置日志配置，创建时间戳日志文件，并转发内存中的日志

    Args:
        log_dir: 日志文件保存目录
        memory_handler: 内存处理器

    Returns:
        日志文件路径
    """
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"execution_{timestamp}.log")

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 将内存处理器的目标设置为文件处理器
    memory_handler.setTarget(file_handler)

    # 刷新内存中的日志到文件
    memory_handler.flush()

    # 移除内存处理器，添加文件处理器
    root_logger = logging.getLogger()
    root_logger.removeHandler(memory_handler)
    root_logger.addHandler(file_handler)

    return log_file


def setup_logging(log_dir: str) -> str:
    """设置日志配置，创建时间戳日志文件

    Args:
        log_dir: 日志文件保存目录

    Returns:
        日志文件路径
    """
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"execution_{timestamp}.log")

    # 清除已有的处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 配置日志处理器（仅文件，不打印到控制台）
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 配置根记录器
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    return log_file


def _load_config(
    args: argparse.Namespace,
    memory_handler: logging.handlers.MemoryHandler,
) -> tuple[str, list[str], str, int]:
    """加载配置参数

    Args:
        args: 命令行参数
        memory_handler: 内存日志处理器

    Returns:
        tuple[spectrum_path, measure_paths, save_dir, return_code]:
            - spectrum_path: 光谱数据文件路径
            - measure_paths: 测量数据文件路径列表
            - save_dir: 保存目录
            - return_code: 返回码（0 表示成功，1 表示失败）
    """
    if args.spectrum is not None and args.measure is not None:
        return args.spectrum, args.measure, args.save_dir, 0

    # 如果未提供光谱数据文件路径或测量数据文件路径，则从标准输入读取
    if not check_pipe_input():
        logger.error('未提供光谱数据文件路径或测量数据文件路径')
        log_file = setup_file_logging(args.save_dir, memory_handler)
        logger.info(f'日志已保存到: {log_file}')
        return '', [], '', 1

    # 从标准输入读取内容
    stdin_content = sys.stdin.read().strip()

    # 移除 UTF-8 BOM（如果存在）
    if stdin_content.startswith('\ufeff'):
        stdin_content = stdin_content[1:]

    if not stdin_content:
        logger.error('从标准输入读取的内容为空')
        log_file = setup_file_logging(args.save_dir, memory_handler)
        logger.info(f'日志已保存到: {log_file}')
        return '', [], '', 1

    config = None
    config_source = None

    # 先尝试判断是否是文件路径
    if os.path.exists(stdin_content):
        try:
            # 如果是文件路径，读取文件并解析
            with open(stdin_content, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config_source = f'文件路径: {stdin_content}'
            logger.info(f'从配置文件读取: {stdin_content}')
        except json.JSONDecodeError as e:
            logger.error(f'配置文件 {stdin_content} 不是有效的 JSON 格式: {e}')
            log_file = setup_file_logging(args.save_dir, memory_handler)
            logger.info(f'日志已保存到: {log_file}')
            return '', [], '', 1
        except Exception as e:
            logger.error(f'读取配置文件 {stdin_content} 失败: {e}')
            log_file = setup_file_logging(args.save_dir, memory_handler)
            logger.info(f'日志已保存到: {log_file}')
            return '', [], '', 1
    else:
        # 如果不是文件路径，尝试直接解析为 JSON 字符串
        try:
            config = json.loads(stdin_content)
            config_source = 'JSON 字符串'
            logger.info('从 JSON 字符串读取配置')
        except json.JSONDecodeError as e:
            logger.error(f'输入既不是有效的文件路径也不是有效的 JSON 字符串: {e}')
            log_file = setup_file_logging(args.save_dir, memory_handler)
            logger.info(f'日志已保存到: {log_file}')
            return '', [], '', 1

    # 验证配置中是否包含必需的键
    if not config or not isinstance(config, dict):
        logger.error(f'配置不是有效的字典格式。来源: {config_source}')
        log_file = setup_file_logging(args.save_dir, memory_handler)
        logger.info(f'日志已保存到: {log_file}')
        return '', [], '', 1

    required_keys = {'spectrum', 'measure', 'save_dir'}
    missing_keys = required_keys - set(config.keys())

    if missing_keys:
        logger.error(
            f'配置缺少必需的键: {', '.join(missing_keys)}。'
            f'来源: {config_source}'
        )
        log_file = setup_file_logging(args.save_dir, memory_handler)
        logger.info(f'日志已保存到: {log_file}')
        return '', [], '', 1

    logger.info(f'配置加载成功，来源: {config_source}')
    return config['spectrum'], config['measure'], config['save_dir'], 0


def _run_modeling(
    spectrum_data: pd.DataFrame,
    uav_data: pd.DataFrame,
    measure_data: pd.DataFrame,
    save_dir: str,
) -> int:
    """执行建模过程

    Args:
        spectrum_data: 光谱数据
        uav_data: UAV 数据
        measure_data: 测量数据
        save_dir: 保存目录

    Returns:
        返回码（0 表示成功，1 表示失败）
    """
    # 调用建模，自动微调或者重新建模
    logger.info('开始建模')
    model_func, _ = get_modeler(spectrum_data, uav_data, measure_data)

    # 加密模型为bin文件
    if not os.path.exists(save_dir):
        logger.error(f'保存路径：{save_dir}不存在！开始创建此路径。。。')
        os.makedirs(save_dir, exist_ok=True)
        if not os.path.exists(save_dir):
            logger.error(f'路径：{save_dir} 创建失败！')
            raise FileExistsError(f'路径：{save_dir} 创建失败！')
        else:
            logger.info(f'路径：{save_dir} 创建成功！')

    if not model_func:
        logger.warning('建模结果为空，没有结果可以加密保存')
        return 1

    try:
        # 使用加密函数
        logger.info('开始加密模型')
        encrypted_path = encrypt_data_to_file(
            data_obj=model_func,
            password=b'water_quality_analysis_key',
            salt=b'water_quality_salt',
            iv=b'fixed_iv_16bytes',
            output_dir=save_dir,
            logger=logger,
        )

        if encrypted_path:
            # 打印output_path的绝对路径
            abspath = os.path.abspath(encrypted_path)
            logger.info(f'模型加密成功，保存路径: {abspath}')
            print(abspath)
            return 0
        else:
            logger.error('加密结果路径为空')
            return 1
    except Exception as e:
        logger.error(f'加密结果时出错: {str(e)}', exc_info=True)
        return 1


def main():
    # 初始化内存日志处理器，先将日志缓存在内存中
    memory_handler = setup_memory_logging()

    # 此时日志只会保存在内存中，不会创建文件
    logger.info('=' * 80)
    logger.info('程序启动，初始化内存日志缓冲')
    logger.info('=' * 80)

    parser = argparse.ArgumentParser(description='卫星中心自动化建模工具')
    parser.add_argument('--spectrum', type=str, help='光谱数据文件路径')
    parser.add_argument('--measure', type=list, help='测量数据文件路径列表')
    parser.add_argument('--save_dir', type=str, default='./', help='日志和结果保存目录')
    args = parser.parse_args()

    # 加载配置
    spectrum_path, measure_paths, save_dir, config_status = _load_config(args, memory_handler)
    if config_status != 0:
        return config_status

    # 现在 save_dir 已经确定，初始化文件日志并转发内存日志
    log_file = setup_file_logging(save_dir, memory_handler)
    logger.info(f'日志文件已创建: {log_file}')
    logger.info('=' * 80)
    logger.info('程序开始执行')
    logger.info('=' * 80)

    try:
        # 解析光谱数据文件
        logger.info('开始解析光谱数据文件')
        spectrum_data, uav_data, measure_data = parse_data(spectrum_path, measure_paths)

        # 格式化波段名为数字类型
        logger.info('开始格式化波段名')
        spectrum_data = format_band_name(spectrum_data)

        # 标准化指标名称
        logger.info('开始标准化指标名称')
        uav_data, uav_indicator_names = standardize_indicator_names(uav_data)
        measure_data, measure_indicator_names = standardize_indicator_names(measure_data)

        logger.info(f'UAV 数据指标: {', '.join(uav_indicator_names)}')
        logger.info(f'测量数据指标: {', '.join(measure_indicator_names)}')

        # 执行建模
        return_code = _run_modeling(spectrum_data, uav_data, measure_data, save_dir)
        if return_code != 0:
            return return_code

        logger.info('=' * 80)
        logger.info('程序执行完成，执行结果：成功')
        logger.info('=' * 80)
        return 0

    except Exception as e:
        logger.error('=' * 80)
        logger.error(f'程序执行过程中出现异常: {str(e)}', exc_info=True)
        logger.error('=' * 80)
        return 1
    finally:
        logger.info(f'日志已保存到: {log_file}')


if __name__ == "__main__":
    sys.exit(main())
