# 逢甲幹課 Beta：名額查詢版

原專案：[zephyrxvxx7/FCU-grabbed-class](https://github.com/zephyrxvxx7/FCU-grabbed-class)

## 使用前確認

- 加選成功與否以選課系統顯示的已選課清單為準。
- 請勿將帳密、瀏覽器設定檔或執行輸出提交到 Git。

這是改成「多門課依序看名額」的版本。平常只查，不會加選；真的要送出加選才加 `--confirm-enroll`。

## 環境需求

* Windows
* Python 3.10 以上
* Google Chrome
* 一顆平常心

> `.venv` 不會跟著 GitHub 下載，第一次使用一定要自己建一次。這是正常的。

## 怎麼下載

### 有 Git 的人

```powershell
git clone https://github.com/chokakun/fcu-course-availability-helper-2026-.git
cd .\fcu-course-availability-helper-2026-
```

### 沒有 Git 的人

到 [專案頁面](https://github.com/chokakun/fcu-course-availability-helper-2026-) 按 `Code` -> `Download ZIP`，解壓縮後在資料夾內開 PowerShell。

## 第一次使用

在專案資料夾裡依序輸入：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果 `python` 顯示找不到指令，先安裝 Python 3.10 以上，安裝時勾選 `Add Python to PATH`，再重新開 PowerShell。也可以試試 `py -3` 取代上面的 `python`。

## 只看名額

```powershell
.\.venv\Scripts\python.exe .\FCU_grabbed_class.py --course-code 1686 3114 3043 --interval 3 --max-checks 100
```

`1686 3114 3043` 就是想看的選課代碼，前面的優先。程式開始時會問帳號、密碼，然後開 Chrome；驗證碼請看 Chrome 畫面後，自己回 PowerShell 輸入。

`--interval 3` 是每輪查完等 3 秒。可以改成任何非負整數，`0` 就是不額外等。 `--max-checks 100` 是最多查 100 輪。

## 真的要加選

確認要送出加選請求時才用這行：

```powershell
.\.venv\Scripts\python.exe .\FCU_grabbed_class.py --course-code 1686 3114 3043 --interval 3 --max-checks 100 --confirm-enroll
```

找到名額後，每門課只會送一次加選請求，接著繼續看後面的課。Chrome 不會立刻關掉，請自己看已選課清單確認；確認完回 PowerShell 按 Enter 才會關閉。

驗證碼無法自動填，重新整理後也可能變掉。加選結果只以選課系統的已選課清單為準。

## 看不懂輸出？

```text
[1/100] 1686: remaining=0, open=60
```

代表第 1 輪查詢，這門課剩 0 個名額，開放名額是 60。

如果看到 `unrecognized status message`，代表網站回傳的文字不是程式目前認得的格式。先看 Chrome 有沒有跳出通知、登入失效或其他訊息；程式會停下來，避免亂判。

## 測試

這個不會開 Chrome，也不會碰選課系統：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 注意

* 不要把帳密、驗證碼、Chrome 設定檔或執行紀錄上傳到 GitHub。
* `Ctrl+C` 可以停止程式。
* 公開散布前，請自行確認原專案與相依套件的授權，以及校方規範。
