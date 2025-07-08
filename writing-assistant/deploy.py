#!/usr/bin/env python3
"""
AI智能写作辅导软件部署脚本
"""
import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

class DeploymentManager:
    """部署管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.config_path = self.project_root / "config.env"
        
    def check_requirements(self):
        """检查系统要求"""
        print("🔍 检查系统要求...")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("❌ Python版本需要3.8或更高")
            return False
        
        print(f"✅ Python版本: {sys.version}")
        
        # 检查必要的命令
        required_commands = ['pip', 'git']
        for cmd in required_commands:
            if not shutil.which(cmd):
                print(f"❌ 缺少必要命令: {cmd}")
                return False
            print(f"✅ 找到命令: {cmd}")
        
        return True
    
    def create_virtual_environment(self):
        """创建虚拟环境"""
        print("🐍 创建虚拟环境...")
        
        if self.venv_path.exists():
            print("⚠️  虚拟环境已存在，跳过创建")
            return True
        
        try:
            subprocess.run([
                sys.executable, "-m", "venv", str(self.venv_path)
            ], check=True)
            print("✅ 虚拟环境创建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 虚拟环境创建失败: {e}")
            return False
    
    def install_dependencies(self):
        """安装依赖"""
        print("📦 安装依赖...")
        
        # 确定pip路径
        if os.name == 'nt':  # Windows
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        else:  # Linux/Mac
            pip_path = self.venv_path / "bin" / "pip"
        
        if not pip_path.exists():
            print("❌ 找不到pip，请检查虚拟环境")
            return False
        
        try:
            # 升级pip
            subprocess.run([
                str(pip_path), "install", "--upgrade", "pip"
            ], check=True)
            
            # 安装依赖
            subprocess.run([
                str(pip_path), "install", "-r", "requirements.txt"
            ], check=True)
            
            print("✅ 依赖安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    
    def setup_database(self):
        """设置数据库"""
        print("🗄️  初始化数据库...")
        
        try:
            # 确定python路径
            if os.name == 'nt':  # Windows
                python_path = self.venv_path / "Scripts" / "python.exe"
            else:  # Linux/Mac
                python_path = self.venv_path / "bin" / "python"
            
            subprocess.run([
                str(python_path), "database.py"
            ], check=True, cwd=self.project_root)
            
            print("✅ 数据库初始化成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False
    
    def create_production_config(self):
        """创建生产环境配置"""
        print("⚙️  创建生产环境配置...")
        
        production_config = """# AI智能写作辅导软件 - 生产环境配置

# LLM API配置
LLM_API_URL=http://localhost:8000
DEFAULT_MODEL=gpt-3.5-turbo
LLM_TIMEOUT=30

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
DEBUG=False

# 数据库配置
DATABASE_URL=sqlite:///production.db

# 应用配置
AUTO_SAVE_INTERVAL=30
MAX_WORD_COUNT=2000
SECRET_KEY=your-secret-key-change-this-in-production

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/production.log

# 安全配置
SSL_ENABLED=False
SSL_CERT_PATH=
SSL_KEY_PATH=
"""
        
        prod_config_path = self.project_root / "config.prod.env"
        with open(prod_config_path, 'w', encoding='utf-8') as f:
            f.write(production_config)
        
        print(f"✅ 生产环境配置已创建: {prod_config_path}")
        return True
    
    def create_service_file(self):
        """创建系统服务文件（Linux）"""
        if os.name == 'nt':
            return self.create_windows_service()
        
        print("🔧 创建系统服务文件...")
        
        service_content = f"""[Unit]
Description=AI智能写作辅导软件
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory={self.project_root}
Environment=PATH={self.venv_path}/bin
ExecStart={self.venv_path}/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
        
        service_path = self.project_root / "writing-assistant.service"
        with open(service_path, 'w', encoding='utf-8') as f:
            f.write(service_content)
        
        print(f"✅ 服务文件已创建: {service_path}")
        print("💡 请手动将服务文件复制到 /etc/systemd/system/ 并启用服务")
        return True
    
    def create_windows_service(self):
        """创建Windows服务脚本"""
        print("🔧 创建Windows服务脚本...")
        
        batch_content = f"""@echo off
cd /d "{self.project_root}"
"{self.venv_path}\\Scripts\\python.exe" app.py
pause
"""
        
        batch_path = self.project_root / "start_service.bat"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        print(f"✅ Windows启动脚本已创建: {batch_path}")
        return True
    
    def create_nginx_config(self):
        """创建Nginx配置"""
        print("🌐 创建Nginx配置...")
        
        nginx_config = """server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /static/ {
        alias /path/to/writing-assistant/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
"""
        
        nginx_path = self.project_root / "nginx.conf"
        with open(nginx_path, 'w', encoding='utf-8') as f:
            f.write(nginx_config)
        
        print(f"✅ Nginx配置已创建: {nginx_path}")
        return True
    
    def create_docker_files(self):
        """创建Docker文件"""
        print("🐳 创建Docker配置...")
        
        dockerfile_content = """FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 初始化数据库
RUN python database.py

# 暴露端口
EXPOSE 8080

# 启动应用
CMD ["python", "app.py"]
"""
        
        dockerfile_path = self.project_root / "Dockerfile"
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        
        # Docker Compose文件
        compose_content = """version: '3.8'

services:
  writing-assistant:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DEBUG=False
      - DATABASE_URL=sqlite:///production.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./static:/app/static:ro
    depends_on:
      - writing-assistant
    restart: unless-stopped
"""
        
        compose_path = self.project_root / "docker-compose.yml"
        with open(compose_path, 'w', encoding='utf-8') as f:
            f.write(compose_content)
        
        print(f"✅ Docker文件已创建: {dockerfile_path}, {compose_path}")
        return True
    
    def create_backup_script(self):
        """创建备份脚本"""
        print("💾 创建备份脚本...")
        
        if os.name == 'nt':
            backup_content = f"""@echo off
set BACKUP_DIR=backups
set DATE=%date:~0,4%-%date:~5,2%-%date:~8,2%
set BACKUP_NAME=writing-assistant-backup-%DATE%

if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

echo 正在备份数据库...
copy writing_assistant.db %BACKUP_DIR%\\%BACKUP_NAME%.db

echo 正在备份配置文件...
copy config.env %BACKUP_DIR%\\%BACKUP_NAME%-config.env

echo 正在备份日志文件...
if exist logs (
    xcopy logs %BACKUP_DIR%\\%BACKUP_NAME%-logs\\ /E /I
)

echo 备份完成: %BACKUP_DIR%\\%BACKUP_NAME%
pause
"""
            backup_path = self.project_root / "backup.bat"
        else:
            backup_content = f"""#!/bin/bash
BACKUP_DIR="backups"
DATE=$(date +%Y-%m-%d)
BACKUP_NAME="writing-assistant-backup-$DATE"

mkdir -p "$BACKUP_DIR"

echo "正在备份数据库..."
cp writing_assistant.db "$BACKUP_DIR/$BACKUP_NAME.db"

echo "正在备份配置文件..."
cp config.env "$BACKUP_DIR/$BACKUP_NAME-config.env"

echo "正在备份日志文件..."
if [ -d "logs" ]; then
    cp -r logs "$BACKUP_DIR/$BACKUP_NAME-logs"
fi

echo "备份完成: $BACKUP_DIR/$BACKUP_NAME"
"""
            backup_path = self.project_root / "backup.sh"
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        
        # 设置执行权限（Unix系统）
        if os.name != 'nt':
            os.chmod(backup_path, 0o755)
        
        print(f"✅ 备份脚本已创建: {backup_path}")
        return True
    
    def deploy(self, environment='development'):
        """执行部署"""
        print(f"🚀 开始部署到 {environment} 环境...")
        
        steps = [
            ("检查系统要求", self.check_requirements),
            ("创建虚拟环境", self.create_virtual_environment),
            ("安装依赖", self.install_dependencies),
            ("初始化数据库", self.setup_database),
        ]
        
        if environment == 'production':
            steps.extend([
                ("创建生产配置", self.create_production_config),
                ("创建服务文件", self.create_service_file),
                ("创建Nginx配置", self.create_nginx_config),
                ("创建Docker文件", self.create_docker_files),
                ("创建备份脚本", self.create_backup_script),
            ])
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ {step_name}失败，部署中止")
                return False
        
        print("\n🎉 部署完成！")
        
        if environment == 'production':
            print("\n📝 生产环境部署后续步骤：")
            print("1. 修改 config.prod.env 中的配置")
            print("2. 设置强密码和安全密钥")
            print("3. 配置SSL证书（推荐）")
            print("4. 设置防火墙规则")
            print("5. 配置监控和日志")
            print("6. 定期运行备份脚本")
        
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI智能写作辅导软件部署脚本')
    parser.add_argument(
        '--env', 
        choices=['development', 'production'],
        default='development',
        help='部署环境 (默认: development)'
    )
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='跳过依赖安装'
    )
    
    args = parser.parse_args()
    
    deployer = DeploymentManager()
    
    print("🎯 AI智能写作辅导软件部署工具")
    print("=" * 50)
    
    success = deployer.deploy(args.env)
    
    if success:
        print("\n✨ 部署成功！系统已准备就绪。")
        if args.env == 'development':
            print("💡 开发环境启动命令: python app.py")
        else:
            print("💡 生产环境请按照上述步骤完成配置")
        sys.exit(0)
    else:
        print("\n💥 部署失败！请检查错误信息。")
        sys.exit(1)

if __name__ == '__main__':
    main()