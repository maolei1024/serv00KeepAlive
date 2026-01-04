#!/usr/bin/env python3
"""
Serv00 KeepAlive - 自动登录保活工具

用于定期登录 serv00 面板，防止账号因 90 天不登录被封禁
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any

import yaml

from serv00_login import Serv00Client, LoginResult, AccountStatus
from logger import setup_logger, StatusPrinter


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 验证配置
    if 'accounts' not in config or not config['accounts']:
        raise ValueError("配置文件中没有定义账号")
    
    return config


def execute_shell_command(command: str, logger) -> bool:
    """
    执行 shell 命令
    
    Args:
        command: 要执行的命令
        logger: 日志记录器
    
    Returns:
        执行是否成功
    """
    try:
        logger.info(f"执行自定义命令: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                logger.debug(f"命令输出: {result.stdout.strip()}")
            return True
        else:
            logger.warning(f"命令返回非零状态: {result.returncode}")
            if result.stderr.strip():
                logger.warning(f"错误输出: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("命令执行超时")
        return False
    except Exception as e:
        logger.error(f"命令执行失败: {e}")
        return False


def check_account(account: Dict[str, Any], settings: Dict[str, Any], logger) -> LoginResult:
    """
    检查单个账号状态
    
    Args:
        account: 账号配置
        settings: 全局设置
        logger: 日志记录器
    
    Returns:
        登录结果
    """
    panel_url = account['panel_url']
    username = account['username']
    password = account['password']
    
    timeout = settings.get('timeout', 30)
    retry_count = settings.get('retry_count', 3)
    
    # 提取面板编号用于日志显示
    panel_id = panel_url.split('//')[1].split('.')[0] if '//' in panel_url else panel_url
    
    logger.info(f"[{panel_id}] 正在检查账号 {username}...")
    
    with Serv00Client(panel_url, timeout=timeout) as client:
        result = client.login(username, password, retry_count=retry_count)
    
    # 根据状态打印不同样式的消息
    if result.status == AccountStatus.ACTIVE:
        msg = StatusPrinter.success(f"[{panel_id}] {username}: 账号正常")
        if result.details:
            msg += f" ({result.details})"
        logger.info(msg)
        
    elif result.status == AccountStatus.BANNED:
        msg = StatusPrinter.error(f"[{panel_id}] {username}: 账号已被封禁")
        if result.details:
            msg += f" ({result.details})"
        logger.warning(msg)
        
        # 执行封禁时的自定义命令
        on_banned = account.get('on_banned')
        if on_banned:
            execute_shell_command(on_banned, logger)
            
    elif result.status == AccountStatus.LOGIN_FAILED:
        msg = StatusPrinter.warning(f"[{panel_id}] {username}: 登录失败")
        if result.details:
            msg += f" ({result.details})"
        logger.warning(msg)
        
    elif result.status == AccountStatus.NETWORK_ERROR:
        msg = StatusPrinter.error(f"[{panel_id}] {username}: 网络错误")
        if result.details:
            msg += f" ({result.details})"
        logger.error(msg)
        
    else:
        msg = StatusPrinter.warning(f"[{panel_id}] {username}: 未知状态")
        if result.details:
            msg += f" ({result.details})"
        logger.warning(msg)
    
    return result


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='Serv00 KeepAlive - 自动登录保活工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 使用默认配置文件 config.yaml
  %(prog)s -c my_config.yaml  # 使用自定义配置文件
  %(prog)s --no-log           # 不输出日志到文件
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    parser.add_argument(
        '--no-log',
        action='store_true',
        help='不输出日志到文件'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细输出'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    try:
        # 如果配置路径是相对路径，相对于脚本所在目录
        config_path = args.config
        if not os.path.isabs(config_path):
            script_dir = Path(__file__).parent
            config_path = script_dir / config_path
        
        config = load_config(str(config_path))
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except (yaml.YAMLError, ValueError) as e:
        print(f"配置文件格式错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 获取设置
    settings = config.get('settings', {})
    log_file = None if args.no_log else settings.get('log_file', 'serv00.log')
    
    # 设置日志
    logger = setup_logger('serv00', log_file)
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    # 开始检查
    logger.info("=" * 50)
    logger.info("开始检查 serv00 账号状态...")
    logger.info("=" * 50)
    
    accounts = config['accounts']
    results: List[LoginResult] = []
    
    for account in accounts:
        try:
            result = check_account(account, settings, logger)
            results.append(result)
        except Exception as e:
            logger.error(f"检查账号时发生错误: {e}")
            results.append(LoginResult(
                status=AccountStatus.UNKNOWN,
                message=str(e),
                panel_url=account.get('panel_url', 'unknown'),
                username=account.get('username', 'unknown')
            ))
    
    # 统计结果
    active_count = sum(1 for r in results if r.status == AccountStatus.ACTIVE)
    banned_count = sum(1 for r in results if r.status == AccountStatus.BANNED)
    failed_count = sum(1 for r in results if r.status in (
        AccountStatus.LOGIN_FAILED, 
        AccountStatus.NETWORK_ERROR, 
        AccountStatus.UNKNOWN
    ))
    
    logger.info("=" * 50)
    logger.info(f"检查完成: {active_count} 正常, {banned_count} 封禁, {failed_count} 失败")
    logger.info("=" * 50)
    
    # 返回状态码
    if banned_count > 0 or failed_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
