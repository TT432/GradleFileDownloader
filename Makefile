.PHONY: install test clean lint format build run-gui run-cli help

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  install     - 安装项目依赖"
	@echo "  install-dev - 安装开发依赖"
	@echo "  test        - 运行测试"
	@echo "  test-basic  - 运行基本功能测试"
	@echo "  lint        - 运行代码检查"
	@echo "  format      - 格式化代码"
	@echo "  build       - 构建项目"
	@echo "  run-gui     - 启动 GUI"
	@echo "  run-cli     - 启动 CLI (需要参数)"
	@echo "  clean       - 清理构建文件"
	@echo "  sync        - 同步依赖"

# 安装项目依赖
install:
	uv venv --python 3.7
	uv sync

# 安装开发依赖
install-dev:
	uv venv --python 3.7
	uv sync --all-extras

# 同步依赖
sync:
	uv sync

# 运行基本功能测试
test-basic:
	uv run python test_basic.py

# 运行单元测试
test:
	uv run pytest

# 运行代码检查
lint:
	uv run flake8 src/ test_basic.py
	uv run mypy src/

# 格式化代码
format:
	uv run black src/ test_basic.py

# 构建项目
build:
	uv build

# 启动 GUI
run-gui:
	uv run gradle-downloader gui

# 启动 CLI (使用示例: make run-cli ARGS="search gson")
run-cli:
	uv run gfd $(ARGS)

# 使用安装的命令
gradle-downloader:
	uv run gradle-downloader $(ARGS)

# 快捷命令
gfd:
	uv run gfd $(ARGS)

# 清理构建文件
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 完整的开发环境设置
dev-setup: install-dev
	uv run pre-commit install

# 发布到 PyPI (测试)
publish-test:
	uv build
	uv publish --index-url https://test.pypi.org/simple/

# 发布到 PyPI (正式)
publish:
	uv build
	uv publish 