#!/bin/bash

# 推送到GitHub脚本
# 使用方法: 运行此脚本，按照提示操作

echo "=== 品牌AI顾问系统 - GitHub推送脚本 ==="
echo ""

# 检查是否已设置remote
if ! git remote geturl origin >/dev/null 2>&1; then
    echo "尚未设置GitHub仓库地址。"
    echo "请先在GitHub上创建一个新仓库，然后运行以下命令："
    echo ""
    echo "  git remote add origin https://github.com/HuYee2025/<仓库名>.git"
    echo "  git push -u origin master"
    echo ""
    echo "或者如果你想在这里直接创建，可以："
    echo "1. 访问 https://github.com/new 创建新仓库"
    echo "2. 仓库名建议: restaurant-ai-advisor"
    echo "3. 创建后运行上面的git remote和git push命令"
else
    echo "正在推送到GitHub..."
    git push -u origin master
    echo ""
    echo "推送成功！"
    echo "仓库地址: $(git remote geturl origin)"
fi
