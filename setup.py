#!/usr/bin/env python3
"""Mnemosyne 一键安装脚本

检测环境 → 安装依赖 → 创建目录 → 初始化数据库 → 验证
用法：python setup.py
"""

import os
import subprocess
import sys

# Windows 终端 GBK 编码修复
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        os.environ['PYTHONIOENCODING'] = 'utf-8'

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DB_PATH = BASE_DIR / "graph.db"

REQUIRED_DIRS = [
    "scripts",
    "scripts/core",
    "hot",
    "warm",
    "cold/archive",
    "engine",
    "proposals",
    "reflections",
    "docs",
]

REQUIRED_PACKAGES = [
    ("torch", "torch>=2.6"),
    ("sentence_transformers", "sentence-transformers"),
    ("numpy", "numpy"),
    ("apscheduler", "apscheduler"),
    ("streamlit", "streamlit"),
]


def step(msg):
    print(f"\n{'='*50}")
    print(f"  {msg}")
    print(f"{'='*50}")


def check_python():
    step("Step 1: 检查 Python 版本")
    v = sys.version_info
    print(f"  Python {v.major}.{v.minor}.{v.micro}")
    if v < (3, 10):
        print(f"  ❌ 需要 Python 3.10+，当前 {v.major}.{v.minor}")
        return False
    print("  ✅ 版本满足要求")
    return True


def create_dirs():
    step("Step 2: 创建目录结构")
    for d in REQUIRED_DIRS:
        p = BASE_DIR / d
        p.mkdir(parents=True, exist_ok=True)
        print(f"  📁 {d}")
    print("  ✅ 目录结构创建完成")


def install_deps():
    step("Step 3: 安装 Python 依赖")
    for module_name, pip_name in REQUIRED_PACKAGES:
        try:
            __import__(module_name)
            print(f"  ✅ {pip_name} 已安装")
        except ImportError:
            print(f"  ⬇️  安装 {pip_name} ...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pip_name,
                "-q", "--disable-pip-version-check"
            ])
            print(f"  ✅ {pip_name} 安装完成")


def init_db():
    step("Step 4: 初始化数据库")
    if DB_PATH.exists():
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        conn.close()
        print(f"  ℹ️  graph.db 已存在（{count} 节点），跳过初始化")
        return

    sys.path.insert(0, str(SCRIPTS_DIR))
    from graph_init import init_db
    init_db(str(DB_PATH))


def verify():
    step("Step 5: 验证安装")
    errors = []

    # 检查数据库
    if not DB_PATH.exists():
        errors.append("graph.db 不存在")
    else:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()
        for t in ['nodes', 'edges', 'fts_nodes', 'meta']:
            if t in tables:
                print(f"  ✅ 表 {t} 存在")
            else:
                errors.append(f"表 {t} 缺失")
                print(f"  ❌ 表 {t} 缺失")

    # 检查核心模块
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from core import SQLiteStore, HarrierEmbedder, AbstractGraphStore, AbstractEmbedder
        print("  ✅ core 模块导入正常")
    except ImportError as e:
        errors.append(f"core 模块导入失败: {e}")
        print(f"  ❌ core 模块导入失败: {e}")

    # 检查 V8 模块
    v8_checks = {
        'V8 核心模块': (ROOT_DIR / 'v8' / 'src' / 'v8_memory').exists(),
        'MCP Server': (SCRIPTS_DIR / 'mcp_server' / '__init__.py').exists(),
        'REST API': (SCRIPTS_DIR / 'api' / 'v8_routes.py').exists(),
        'Web Dashboard': (SCRIPTS_DIR / 'dashboard' / 'web' / 'index.html').exists(),
        '测试用例': (ROOT_DIR / 'tests').exists(),
    }
    for name, exists in v8_checks.items():
        if exists:
            print(f"  ✅ {name} 存在")
        else:
            errors.append(f"{name} 缺失")
            print(f"  ❌ {name} 缺失")

    # 检查 Harrier 可用性（可选）
    try:
        from huggingface_hub import model_info
        info = model_info('microsoft/harrier-oss-v1-0.6b')
        print(f"  ✅ Harrier-OSS-v1-0.6b 可用（{info.downloads} 下载）")
    except Exception:
        print("  ⚠️  Harrier-OSS-v1-0.6b 无法访问（可选，不影响使用）")

    return errors


def main():
    print("""
╔══════════════════════════════════════════════════╗
║        Mnemosyne V8 安装向导                   ║
║        仿生经验与记忆系统 · Harrier + 知识图谱 + SQLite   ║
╚══════════════════════════════════════════════════╝
""")

    if not check_python():
        sys.exit(1)

    create_dirs()
    install_deps()
    init_db()

    errors = verify()

    print(f"\n{'='*50}")
    if errors:
        print("  ⚠️  安装完成，但有以下问题：")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  ✅ 安装完成！所有组件正常。")
    print(f"{'='*50}")

    print(f"""
使用方法：
  写入记忆: python -m v8_memory.cli event-add --type task_completed --actor agent --content "经验"
  搜索记忆: python -m v8_memory.cli context-build --task "关键词"
  查看统计: python -m v8_memory.cli memory-list --limit 10
  Web Dashboard: 浏览器打开 scripts/dashboard/web/index.html
  测试: pytest tests/ -v
"""))


if __name__ == "__main__":
    main()
