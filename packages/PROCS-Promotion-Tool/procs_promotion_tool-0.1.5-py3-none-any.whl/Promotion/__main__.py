from .main_app import CreatePromotionFile
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import platform
import requests
import shutil
import subprocess
from matplotlib import font_manager
import ctypes

def check_and_install_fonts(fonts: dict, local_folder: str = "fonts"):
    """
    ตรวจสอบและติดตั้งฟอนต์หลายตัวพร้อมกัน
    Args:
        fonts (dict): dict ของชื่อฟอนต์และ URL เช่น {"Sarabun": "https://.../Sarabun-Regular.ttf"}
        local_folder (str): โฟลเดอร์เก็บฟอนต์ชั่วคราว
    """
    os.makedirs(local_folder, exist_ok=True)

    system_fonts = [os.path.basename(f).lower() for f in font_manager.findSystemFonts()]
    os_name = platform.system().lower()
    installed_any = False

    for font_name, font_url in fonts.items():
        print(f"\nตรวจสอบฟอนต์: {font_name}")

        # ถ้ามีอยู่แล้วให้ข้าม
        if any(font_name.lower() in f for f in system_fonts):
            print(f"ฟอนต์ '{font_name}' มีอยู่แล้วในระบบ")
            continue

        # ดาวน์โหลดไฟล์
        font_path = os.path.join(local_folder, f"{font_name}.ttf")
        if not os.path.exists(font_path):
            print(f"กำลังดาวน์โหลด {font_name} ...")
            response = requests.get(font_url, timeout=20)
            if response.status_code == 200:
                with open(font_path, "wb") as f:
                    f.write(response.content)
                print(f"ดาวน์โหลดสำเร็จ: {font_name}")
            else:
                print(f"ดาวน์โหลดไม่สำเร็จ: {response.status_code}")
                continue

        # ติดตั้งเข้าระบบจริง
        try:
            if "windows" in os_name:
                install_font_windows(font_path)
            elif "linux" in os_name:
                install_font_linux(font_path)
            elif "darwin" in os_name:  # macOS
                install_font_macos(font_path)
            installed_any = True
            print(f"ติดตั้งฟอนต์ '{font_name}' สำเร็จ")
        except Exception as e:
            print(f"ติดตั้งฟอนต์ '{font_name}' ล้มเหลว: {e}")

    if installed_any:
        print("\nกำลังรีโหลด cache ฟอนต์ ...")


def install_font_windows(font_path):
    """ติดตั้งฟอนต์ลง Windows"""
    font_dir = r"C:\Windows\Fonts"
    dest_path = os.path.join(font_dir, os.path.basename(font_path))
    shutil.copy(font_path, dest_path)
    ctypes.windll.gdi32.AddFontResourceW(dest_path)
    # แจ้งระบบให้รู้ว่ามีฟอนต์ใหม่
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0, 1000, None)


def install_font_linux(font_path):
    """ติดตั้งฟอนต์ใน Linux"""
    home = os.path.expanduser("~/.local/share/fonts")
    os.makedirs(home, exist_ok=True)
    shutil.copy(font_path, home)
    subprocess.run(["fc-cache", "-f", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def install_font_macos(font_path):
    """ติดตั้งฟอนต์ใน macOS"""
    home = os.path.expanduser("~/Library/Fonts")
    os.makedirs(home, exist_ok=True)
    shutil.copy(font_path, home)


font_list = {
        "Anuphan": "https://github.com/google/fonts/raw/main/ofl/anuphan/Anuphan-Regular.ttf",
        "Bar-Code 39": "https://fonts2u.com/download/bar-code-39.font"
    }

    


def get_version() -> str:
    now = datetime.now()+ relativedelta(months=1)
    month = f"{now.month:02d}"
    year = str(now.year)
    version_code = f"{year[-2:]}0{month}"
    return version_code
def main():
    try:
        check_and_install_fonts(font_list)
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการติดตั้งฟอนต์: {e}")
    CreatePromotion = CreatePromotionFile(load=True,sub_sheet=True)
    version :str = get_version()
    CreatePromotion._set_version(version)
    CreatePromotion.start()


if __name__ == "__main__":
    main()
