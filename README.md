# 主要功能

·记录每次点击物品的价格保存到excel （长时间使用文件太大似乎会导致脚本运行速度变慢，可以清理或者自行关闭excel导出）

·自定义每次点击的间隔时间

·自动购买物品并设置购买的次数

·修复由于OCR识别物品名字不准确导致无法购买的情况

·更新购买时自动点击单次可购买的最大数值（主要为了买子弹）

# 免责声明
免责声明
脚本仅供学习和研究目的使用，作者不对因使用该脚本而导致的任何后果负责。使用该脚本的风险完全由用户自行承担。

本脚本基于@sheldon1998大佬基础上进行修改：https://github.com/sheldon1998/DeltaForceKeyBot


用户须知：

尽管脚本设计为非侵入性，但使用第三方工具可能违反目标平台的使用条款或服务协议。
使用该脚本可能导致账号被封禁或其他形式的处罚。

作者不保证脚本的稳定性、安全性或合法性。
# DeltaForceSpy
三角洲行动拍卖行自动挂卡工具,通过ocr+模拟鼠标点击实现自动购买钥匙卡

## 开始
### 安装
1. 下载本代码,安装requirement.txt
2. 安装[tesseract](https://github.com/tesseract-ocr/tesseract )
3. 下载[tesseract中文识别库](https://github.com/tesseract-ocr/tessdata) （可在上一步安装时选择安装中文识别库）
4. 修改代码中的环境变量为本机安装的位置，默认为C,若更改安装位置需要自行修改以下代码：
```
# Tesseract 环境配置
os.environ["LANGDATA_PATH"] = r"C:\Program Files\Tesseract-OCR\tessdata"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## 运行
```
首次运行请修改keys.json文件，配置需要的购买的物品，运行时请勿打开导出的数据表，否则报错
python main.py
```
F8开始抢卡,F9暂停抢卡,脚本已适配不同分辨率(16:9)以及多显示器的场景
开始抢卡时需要将页面点击到买卡的区域,在keys.json中的"id": "1-1",代表第一行第一个，根据不同需求修改其他数据即可。

成果展示：
![image](https://github.com/user-attachments/assets/a91f22c5-bbaa-4a2d-8957-8324ca5fbbfa)


**如有其他地图的钥匙可以将钥匙添加到收藏，然后通过debug.py 记录钥匙卡的位置来进行监控购买**

## 其他说明
### debug.py
运行debug.py 实时获取鼠标坐标 如得到 58.21%,21.25% 则坐标应该为[0.5821,0.2125]

### keys.json
```

{
    "name": "巴别塔供电权限卡", #目标卡牌名称，需与游戏保持一致
    "id": "1-1", #记录坐标位置为第一行第一个
    "base_price": 489859,  #目标卡牌参考价格,该价格溢价10w内也会自动购买,不需要自行修改代码
    "ideal_price": 500000, #理想购买价格
    "position": [0.6148,0.5174], #卡牌坐标
    "wantBuy":1 #是否加入监控
    "buyMax": 0 #是否单次购买最大值
    }

```

### 购买逻辑

1. 当前价格小于理想购买价格,自动购买
2. 卡牌溢价10w以内,自动购买
3. 卡牌负溢价,自动购买
