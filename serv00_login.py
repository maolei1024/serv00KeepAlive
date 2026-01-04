"""
Serv00 登录核心模块
使用 HTTP 请求模拟登录，检测账号状态
"""
import re
import requests
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AccountStatus(Enum):
    """账号状态枚举"""
    ACTIVE = "active"           # 正常
    BANNED = "banned"           # 被封禁
    LOGIN_FAILED = "login_failed"  # 登录失败（密码错误等）
    NETWORK_ERROR = "network_error"  # 网络错误
    UNKNOWN = "unknown"         # 未知状态


@dataclass
class LoginResult:
    """登录结果"""
    status: AccountStatus
    message: str
    panel_url: str
    username: str
    details: Optional[str] = None


class Serv00Client:
    """
    Serv00 面板客户端
    
    使用 HTTP 请求实现登录和状态检测
    """
    
    # 用于提取 CSRF token 的正则表达式
    CSRF_PATTERN = re.compile(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"')
    
    # 状态检测的关键词
    BANNED_KEYWORDS = ['Konto zablokowane', 'Account blocked', 'blocked']
    SUCCESS_KEYWORDS = ['Strona główna', 'Zalogowany jako', 'Dashboard']
    LOGIN_PAGE_KEYWORDS = ['Zaloguj się', 'Login', 'Sign in']
    
    def __init__(self, panel_url: str, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            panel_url: 面板 URL，如 https://panel12.serv00.com
            timeout: 请求超时时间（秒）
        """
        self.panel_url = panel_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # 设置通用 headers，模拟浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def get_csrf_token(self) -> Optional[str]:
        """
        获取登录页面的 CSRF token
        
        Returns:
            CSRF token 字符串，获取失败返回 None
        """
        login_url = f"{self.panel_url}/login/"
        
        try:
            response = self.session.get(login_url, timeout=self.timeout)
            response.raise_for_status()
            
            match = self.CSRF_PATTERN.search(response.text)
            if match:
                return match.group(1)
            return None
            
        except requests.RequestException:
            return None
    
    def login(self, username: str, password: str, retry_count: int = 3) -> LoginResult:
        """
        执行登录
        
        Args:
            username: 用户名
            password: 密码
            retry_count: 重试次数
        
        Returns:
            LoginResult 对象
        """
        last_error = None
        
        for attempt in range(retry_count):
            try:
                result = self._do_login(username, password)
                return result
            except requests.RequestException as e:
                last_error = str(e)
                # 重试前重建 session
                self.session = requests.Session()
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                })
        
        # 所有重试都失败
        return LoginResult(
            status=AccountStatus.NETWORK_ERROR,
            message=f"网络错误 (重试 {retry_count} 次后失败)",
            panel_url=self.panel_url,
            username=username,
            details=last_error
        )
    
    def _do_login(self, username: str, password: str) -> LoginResult:
        """
        实际执行登录的内部方法
        """
        # 1. 获取 CSRF token
        csrf_token = self.get_csrf_token()
        if not csrf_token:
            return LoginResult(
                status=AccountStatus.NETWORK_ERROR,
                message="无法获取 CSRF token",
                panel_url=self.panel_url,
                username=username
            )
        
        # 2. 提交登录表单
        login_url = f"{self.panel_url}/login/"
        
        data = {
            'csrfmiddlewaretoken': csrf_token,
            'username': username,
            'password': password,
            'next': '/'
        }
        
        headers = {
            'Referer': login_url,
            'Origin': self.panel_url,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        response = self.session.post(
            login_url,
            data=data,
            headers=headers,
            allow_redirects=True,
            timeout=self.timeout
        )
        
        # 3. 解析登录结果
        return self._parse_login_result(response, username)
    
    def _parse_login_result(self, response: requests.Response, username: str) -> LoginResult:
        """
        解析登录响应，判断账号状态
        """
        content = response.text
        
        # 检查是否被封禁
        for keyword in self.BANNED_KEYWORDS:
            if keyword in content:
                # 尝试提取封禁原因
                reason = self._extract_ban_reason(content)
                return LoginResult(
                    status=AccountStatus.BANNED,
                    message="账号已被封禁",
                    panel_url=self.panel_url,
                    username=username,
                    details=reason
                )
        
        # 检查是否登录成功
        for keyword in self.SUCCESS_KEYWORDS:
            if keyword in content:
                # 尝试提取账号有效期
                validity = self._extract_account_validity(content)
                return LoginResult(
                    status=AccountStatus.ACTIVE,
                    message="账号正常",
                    panel_url=self.panel_url,
                    username=username,
                    details=validity
                )
        
        # 仍在登录页面 = 登录失败
        for keyword in self.LOGIN_PAGE_KEYWORDS:
            if keyword in content:
                error_msg = self._extract_error_message(content)
                return LoginResult(
                    status=AccountStatus.LOGIN_FAILED,
                    message="登录失败",
                    panel_url=self.panel_url,
                    username=username,
                    details=error_msg or "用户名或密码错误"
                )
        
        # 无法判断状态
        return LoginResult(
            status=AccountStatus.UNKNOWN,
            message="无法判断账号状态",
            panel_url=self.panel_url,
            username=username,
            details=f"响应 URL: {response.url}"
        )
    
    def _extract_ban_reason(self, content: str) -> Optional[str]:
        """提取封禁原因"""
        # 常见格式: "Konto zablokowane: TOS"
        match = re.search(r'Konto zablokowane[:\s]*([^<\n]+)', content)
        if match:
            return match.group(1).strip()
        return "TOS 违规"
    
    def _extract_account_validity(self, content: str) -> Optional[str]:
        """提取账号有效期"""
        # 格式: "Konto ważne do: 2 stycznia 2036"
        match = re.search(r'Konto ważne do[:\s]*([^<\n]+)', content)
        if match:
            return f"有效期至: {match.group(1).strip()}"
        return None
    
    def _extract_error_message(self, content: str) -> Optional[str]:
        """提取登录错误信息"""
        # 查找 alert 或 error 类的消息
        match = re.search(r'class="[^"]*alert[^"]*"[^>]*>([^<]+)', content)
        if match:
            return match.group(1).strip()
        return None
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
