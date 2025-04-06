import json
import pyautogui
import time
from PIL import Image
import pytesseract
import winsound
import os
import keyboard  # 用于监听键盘事件
from difflib import SequenceMatcher  # 用于计算字符串相似度
import pandas as pd  # 用于处理 Excel
import logging  # 用于日志记录
from datetime import datetime  # 用于获取当前时间

# 配置部分
CONFIG_FILE = 'keys.json'
LOG_FILE = 'price_log.xlsx'  # Excel 日志文件

# Tesseract 环境配置
os.environ["LANGDATA_PATH"] = r"C:\Program Files\Tesseract-OCR\tessdata"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# 全局变量
keys_config = None
is_running = False  # 控制循环是否运行
is_paused = False   # 控制循环是否暂停
screen_width, screen_height = pyautogui.size()

# 初始化 Excel 日志（如果文件不存在则创建）
if not os.path.exists(LOG_FILE):
    df = pd.DataFrame(columns=['Time', 'Card_Name', 'Target_Name', 'Price', 'Purchased'])
    df.to_excel(LOG_FILE, index=False)

def load_keys_config():
    """加载钥匙价格配置文件（只读取一次）"""
    global keys_config
    if keys_config is not None:
        return keys_config
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            keys_config = config.get('keys', [])
            # 为每张卡初始化购买次数
            for card in keys_config:
                card['buy_count'] = 0
            logger.info("配置文件加载成功")
            return keys_config
    except FileNotFoundError:
        logger.error(f"配置文件 {CONFIG_FILE} 不存在")
        return []
    except json.JSONDecodeError:
        logger.error(f"配置文件 {CONFIG_FILE} 格式错误")
        return []
    except Exception as e:
        logger.error(f"读取配置时发生未知错误: {str(e)}")
        return []

def take_screenshot(region, threshold):
    """截取指定区域的截图并二值化"""
    screenshot = pyautogui.screenshot(region=region)
    gray_image = screenshot.convert('L')
    binary_image = gray_image.point(lambda p: 255 if p > threshold else 0)
    binary_image = Image.eval(binary_image, lambda x: 255 - x)
    screenshot.close()
    return binary_image

def getCardPrice():
    """获取当前卡片价格"""
    region_width = int(screen_width * 0.09)
    region_height = int(screen_height * 0.03)
    region_left = int(screen_width * 0.80)
    region_top = int(screen_height * 0.85)
    region = (region_left, region_top, region_width, region_height)
    
    image = take_screenshot(region=region, threshold=150)
    image.save("price_screenshot.png")
    text = pytesseract.image_to_string(image, lang='eng', config="--psm 13 -c tessedit_char_whitelist=0123456789,")
    try:
        price = int(text.replace(",", "").strip())
        logger.info(f"提取的价格文本: {price}")
        return price
    except ValueError:
        logger.warning("无法解析价格")
        return None

def getCardName():
    """获取当前卡片名称"""
    screen_width, screen_height = pyautogui.size()
    region_width = int(screen_width * 0.1)
    region_height = int(screen_height * 0.025)
    region_left = int(screen_width * 0.765)
    region_top = int(screen_height * 0.148)
    region = (region_left, region_top, region_width, region_height)
    
    screenshot = take_screenshot(region=region, threshold=150)
    screenshot.save("./s.png")
    text = pytesseract.image_to_string(screenshot, lang='chi_sim', config="--psm 10")
    text = text.replace(" ", "").strip()
    return text

def log_to_excel(card_name, target_name, price, purchased):
    """将价格信息记录到 Excel"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_data = pd.DataFrame({
        'Time': [current_time],
        'Card_Name': [card_name],
        'Target_Name': [target_name],
        'Price': [price if price is not None else 'N/A'],
        'Purchased': [purchased]
    })
    # 读取现有数据并追加
    try:
        existing_data = pd.read_excel(LOG_FILE)
        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
        updated_data.to_excel(LOG_FILE, index=False)
    except Exception as e:
        logger.error(f"写入 Excel 失败: {str(e)}")
        new_data.to_excel(LOG_FILE, index=False)  # 如果读取失败，直接覆盖

def price_check_flow(card_info):
    """价格检查主流程"""
    global is_paused
    
    # 检查购买次数限制
    max_buy_limit = 2  # 每张卡最多购买 3 次（可调整）
    if card_info.get('buy_count', 0) >= max_buy_limit:
        logger.info(f"{card_info['name']} 已购买 {max_buy_limit} 次，跳过检查")
        return False
    
    # 移动到卡牌位置并点击
    position = card_info.get('position')
    pyautogui.moveTo(position[0]*screen_width, position[1]*screen_height)
    pyautogui.click()
    time.sleep(0.05)  # 点击后等待 1 秒
    
    try:
        card_name = getCardName().strip()
        time.sleep(0.05)  # 获取名称后稍作等待
        current_price = getCardPrice()
        if current_price is None:
            logger.warning("无法获取有效价格，跳过本次检查")
            log_to_excel(card_name, card_info.get("name"), None, False)
            time.sleep(0.05)
            pyautogui.press('esc')
            return False
    except Exception as e:
        logger.error(f"获取门卡信息失败: {str(e)}")
        log_to_excel("", card_info.get("name"), None, False)
        time.sleep(0.05)
        pyautogui.press('esc')
        return False
    
    base_price = card_info.get('base_price', 0)
    ideal_price = card_info.get('ideal_price', base_price)
    max_price = card_info.get('base_price') * 1.1  # 最高溢价 10%
    premium = ((current_price / base_price) - 1) * 100

    check_card_name = card_info.get("name")
    similarity = SequenceMatcher(None, card_name, check_card_name).ratio()
    logger.info(f"当前门卡: {card_name}\n需要购买的卡: {check_card_name}\n相似度: {similarity:.2%}")
    
    if similarity < 0.8:
        logger.info("卡片名称相似度不足 80%，已返回上一层")
        log_to_excel(card_name, check_card_name, current_price, False)
        time.sleep(0.05)
        pyautogui.press('esc')
        return False
    
    logger.info(f"基准价格: {base_price} | 理想价格: {ideal_price} | 当前价格/溢价: {current_price} ,{premium:.2f}% | 最高溢价：{max_price}")
    logger.info(f"已购买次数: {card_info.get('buy_count', 0)}/{max_buy_limit}")
    
    purchased = False
    if premium < 0 or current_price < ideal_price or current_price - base_price <= 100000:
        pyautogui.moveTo(screen_width*0.825, screen_height*0.852)
        pyautogui.click()  # 确认购买
        logger.info(f"[+]已自动购买{card_name},价格为：{current_price},溢价：{premium:.2f}")
        card_info['buy_count'] = card_info.get('buy_count', 0) + 1
        purchased = True
        time.sleep(0.05)  # 购买后等待 1 秒
        pyautogui.press('esc')
    else:
        logger.info(">> 价格过高，重新刷新价格 <<")
        time.sleep(0.05)
        pyautogui.press('esc')
    
    # 记录日志到 Excel
    log_to_excel(card_name, check_card_name, current_price, purchased)
    return purchased

def start_loop():
    """开始循环"""
    global is_running, is_paused
    is_running = True
    is_paused = False
    logger.info("循环已启动")

def stop_loop():
    """停止循环"""
    global is_running, is_paused
    is_running = False
    is_paused = False
    logger.info("循环已停止")

def main():
    global is_running, is_paused
    
    # 初始化时加载配置
    keys_config = load_keys_config()
    if not keys_config:
        logger.error("无法加载配置文件，程序退出")
        return
    
    # 过滤出需要购买的卡牌（作为监控列表）
    cards_to_monitor = [card for card in keys_config if card.get('wantBuy', 0) == 1]
    if not cards_to_monitor:
        logger.error("没有需要购买的门卡，程序退出")
        return
    for card in cards_to_monitor:
        logger.info(f"当前监控的卡: {card['name']}")
    
    # 监听键盘事件
    keyboard.add_hotkey('f8', start_loop)  # 按 F8 开始循环
    keyboard.add_hotkey('f9', stop_loop)   # 按 F9 停止循环
    
    logger.info("按 F8 开始循环，按 F9 停止循环")
    
    while True:
        if is_running and not is_paused:
            for card_info in cards_to_monitor:
                if not is_running:
                    break
                logger.info(f"正在检查门卡: {card_info['name']}")
                price_check_flow(card_info)
                time.sleep(0.15)  # 每次检查后稍长延迟
        elif is_paused:
            logger.info("循环已暂停，等待手动恢复...")
            time.sleep(1)
        else:
            time.sleep(0.1)  # 空闲时降低 CPU 占用

if __name__ == "__main__":
    main()