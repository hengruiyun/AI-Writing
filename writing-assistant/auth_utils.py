"""
认证工具模块
处理密码加密和验证
"""
import hashlib
import secrets
import hmac

def generate_salt() -> str:
    """生成随机盐值"""
    return secrets.token_hex(16)

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    加密密码
    返回 (password_hash, salt)
    """
    if salt is None:
        salt = generate_salt()
    
    # 使用 PBKDF2 算法加密密码
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # 迭代次数
    )
    
    # 将盐值和哈希值组合
    combined = f"{salt}${password_hash.hex()}"
    return combined, salt

def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码
    """
    try:
        # 分离盐值和哈希值
        salt, stored_hash = password_hash.split('$', 1)
        
        # 使用相同的盐值重新计算哈希
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        # 使用 hmac.compare_digest 防止时序攻击
        return hmac.compare_digest(stored_hash, new_hash.hex())
    except (ValueError, AttributeError):
        return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    返回 (is_valid, message)
    """
    if len(password) < 6:
        return False, "密码长度至少6位"
    
    if len(password) > 128:
        return False, "密码长度不能超过128位"
    
    # 简化密码强度要求，只检查长度
    # 检查是否包含至少一个字母和一个数字（可选）
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    # 暂时放宽要求，只要长度够就可以
    # if not (has_letter and has_digit):
    #     return False, "密码必须包含字母和数字"
    
    return True, "密码强度符合要求" 