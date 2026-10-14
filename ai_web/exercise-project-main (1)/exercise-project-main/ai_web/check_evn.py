import sys
import os

print("--- 🔧 環境診斷報告 ---")

# 1. 檢查 Python 版本
print(f"🐍 Python 版本: {sys.version.split()[0]}")

# 2. 檢查有沒有檔名衝突 (最關鍵)
current_files = os.listdir('.')
if 'mediapipe.py' in current_files:
    print("❌ 警告：資料夾裡有 mediapipe.py，請務必改名，否則會報錯！")

# 3. 測試載入工具箱
try:
    import cv2
    print(f"✅ OpenCV 版本: {cv2.__version__}")
    
    import mediapipe as mp
    from mediapipe.solutions import pose as mp_pose
    print(f"✅ MediaPipe 版本: {mp.__version__}")
    print("🎉 恭喜！環境完全正常，可以執行 cam.py 了！")
    
except ImportError as e:
    print(f"❌ 錯誤：找不到套件 - {e}")
    print("💡 請執行指令：python -m pip install opencv-python mediapipe")
except AttributeError:
    print("❌ 錯誤：MediaPipe 載入不完全 (AttributeError)")
    print("💡 通常是資料夾裡有同名檔案，或安裝版本毀損。")
except Exception as e:
    print(f"❌ 發生其他錯誤: {e}")