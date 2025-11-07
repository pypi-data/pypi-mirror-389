# 天翼云CLI工具

基于终端的天翼云API操作平台，提供完整的云资源管理功能。

## 功能特性

- 🔐 **安全认证**: 基于AK/SK的签名认证机制
- 🖥️ **ECS管理**: 云服务器生命周期管理
- 💾 **存储管理**: 对象存储、云硬盘管理
- 🌐 **网络管理**: VPC、弹性IP、安全组配置
- 📊 **监控查询**: 资源监控和日志查询
- ⚡ **批量操作**: 支持批量资源管理
- 📝 **配置管理**: 灵活的配置文件支持

## 项目结构

```
ctyun-cli/
├── src/
│   ├── auth/           # 认证模块
│   ├── ecs/            # 云服务器管理
│   ├── storage/        # 存储管理
│   ├── network/        # 网络管理
│   ├── monitor/        # 监控查询
│   ├── cli/            # 命令行界面
│   ├── config/         # 配置管理
│   └── utils/          # 工具函数
├── tests/              # 测试文件
├── docs/               # 文档
├── examples/           # 示例代码
├── requirements.txt    # Python依赖
├── setup.py           # 安装脚本
└── README.md          # 项目说明
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置认证信息
python setup_config.py

# 查看帮助
python -m ctyun-cli --help

# 列出所有云服务器
python -m ctyun-cli ecs list

# 创建云服务器
python -m ctyun-cli ecs create --instance-type "s6.small" --image "img-ubuntu20"
```

## 技术栈

- **语言**: Python 3.8+
- **HTTP客户端**: requests
- **CLI框架**: click
- **配置管理**: configparser
- **日志**: logging
- **测试**: pytest