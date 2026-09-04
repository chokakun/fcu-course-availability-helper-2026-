# FCU Course Availability Helper

以 Selenium 4 操作逢甲選課網站，依優先順序查詢一或多門課是否出現名額。程式不儲存帳密，且預設只查詢；只有明確加入 `--confirm-enroll` 才會對每門偵測到名額的課送出一次加選請求。

## 使用前確認

- 加選成功與否以選課系統顯示的已選課清單為準。
- 請勿將帳密、瀏覽器設定檔或執行輸出提交到 Git。

## 環境需求

- Python 3.10 以上
- Google Chrome
- `selenium>=4.20,<5`

Selenium 4 會由 Selenium Manager 嘗試處理相容的 ChromeDriver；若校內網路環境阻擋下載，請依 Selenium 官方說明安裝相容 driver。

## 安裝

目前這份本機資料夾已建立 `.venv`，可直接使用下方的 `.venv\Scripts\python.exe` 指令，不需要另外啟用環境。

若日後將專案複製到其他電腦，需先安裝 Python 3.10 以上，並在專案根目錄執行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 查詢名額但不送出加選

程式會在執行時以隱藏輸入方式詢問帳密，接著開啟 Chrome 顯示逢甲登入頁；請自行閱讀圖片中的 Captcha，並在 PowerShell 輸入。可依優先順序輸入多個選課代碼；重複代碼只會保留第一次。`--interval` 可設為任意非負整數；設為 `0` 時不等待下一次查詢。預設為 3 秒，預設最多執行 100 輪完整查詢。

```powershell
.\.venv\Scripts\python.exe .\FCU_grabbed_class.py --course-code 1459 1234 5678 --interval 3 --max-checks 100
```

## 明確允許送出一次加選

以下指令會依輸入順序逐門查詢。某門課偵測到剩餘名額時，程式只送出一次加選請求，並繼續處理尚未送出的其他課。只有系統回應明確包含成功文字的課會標記為成功；其餘回應會標記為「未確認」，不會假裝成功。Chrome 會保持開啟，請自行查看瀏覽器中的已選課清單確認結果；確認後回到終端機按 Enter，程式才會關閉 Chrome。

```powershell
.\.venv\Scripts\python.exe .\FCU_grabbed_class.py --course-code 1459 1234 5678 --interval 3 --max-checks 100 --confirm-enroll
```

## 測試

測試不會啟動 Chrome、不會登入選課系統，也不會送出選課請求。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
