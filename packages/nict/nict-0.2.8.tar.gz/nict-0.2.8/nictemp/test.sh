#!/bin/bash
# 下载常用扩展 VSIX 文件

EXTENSIONS=(
    "ms-vscode/vscode-json"
)

for ext in "${EXTENSIONS[@]}"; do
    PUBLISHER=$(echo $ext | cut -d'/' -f1)
    EXTENSION=$(echo $ext | cut -d'/' -f2)
    
    echo "下载: ${PUBLISHER}.${EXTENSION}"
    
    # 从 Open-VSX 下载
    API_URL="https://open-vsx.org/api/${PUBLISHER}/${EXTENSION}"
    DOWNLOAD_URL=$(curl -s "$API_URL" | grep -o '"download":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$DOWNLOAD_URL" ]; then
        wget -O "${EXTENSION}.vsix" "$DOWNLOAD_URL"
        echo "✅ ${EXTENSION}.vsix 下载完成"
    else
        echo "❌ ${EXTENSION} 下载失败"
    fi
done
