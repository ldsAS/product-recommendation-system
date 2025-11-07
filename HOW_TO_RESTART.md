# 如何重啟服務以應用時區修改

## 當前狀態

你正在使用 Docker Compose 運行推薦系統，包含以下容器：
- `recommendation-api` - API 服務（需要重啟）
- `recommendation-postgres` - PostgreSQL 資料庫（不需要重啟）
- `recommendation-redis` - Redis 快取（不需要重啟）

## 推薦方式：只重啟 API 容器

因為我們只修改了 Python 代碼和 HTML 模板，只需要重啟 API 容器即可。

### 方法 1：使用快速腳本（最簡單）

```bash
restart_api_only.bat
```

或手動執行：
```bash
docker restart recommendation-api
```

### 方法 2：使用 Docker Compose

```bash
docker-compose restart recommendation-api
```

## 如果簡單重啟不生效：重建容器

有時候 Docker 可能會使用緩存，導致代碼更改沒有生效。這時需要重建容器。

### 使用重建腳本

```bash
rebuild_api.bat
```

或手動執行：
```bash
# 停止容器
docker-compose stop recommendation-api

# 重建容器
docker-compose build recommendation-api

# 啟動容器
docker-compose up -d recommendation-api
```

## 完整重啟所有容器（不推薦，除非必要）

如果你想重啟所有容器：

```bash
# 停止所有容器
docker-compose down

# 重建並啟動所有容器
docker-compose up -d --build
```

**注意**：這會重啟資料庫和 Redis，可能會導致數據丟失（如果沒有持久化）。

## 驗證重啟是否成功

### 1. 檢查容器狀態

```bash
docker ps
```

確認 `recommendation-api` 容器的狀態是 `Up` 且是 `healthy`。

### 2. 查看容器日誌

```bash
docker logs recommendation-api
```

或查看最後 20 行：
```bash
docker logs --tail 20 recommendation-api
```

應該看到類似的輸出：
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. 測試 API

```bash
curl http://localhost:8000/health
```

應該返回：
```json
{"status": "healthy"}
```

### 4. 訪問趨勢分析頁面

打開瀏覽器訪問：
- http://localhost:8000/trends

檢查時間是否顯示為台灣時區。

## 時區修改檢查清單

重啟後，請檢查以下項目：

- [ ] 容器狀態為 `Up` 且 `healthy`
- [ ] 容器日誌沒有錯誤
- [ ] 可以訪問 http://localhost:8000
- [ ] 趨勢分析頁面可以正常載入
- [ ] 圖表 X 軸顯示台灣時間（例如：11/07 17:00）
- [ ] Tooltip 顯示完整的台灣時間（例如：2025/11/07 17:00:00）
- [ ] X 軸標題顯示「時間 (台灣時區 UTC+8)」

## 常見問題

### Q1: 重啟後時間還是不對？

**A**: 可能是瀏覽器緩存問題。請：
1. 按 Ctrl+Shift+Delete 清除瀏覽器緩存
2. 或按 Ctrl+F5 強制刷新頁面
3. 或使用無痕模式打開頁面

### Q2: 容器重啟失敗？

**A**: 查看容器日誌找出錯誤原因：
```bash
docker logs recommendation-api
```

常見原因：
- 端口被佔用（8000）
- 資料庫連接失敗
- 代碼語法錯誤

### Q3: 需要重建 Docker 映像嗎？

**A**: 通常不需要，因為：
- Docker Compose 使用 volume 掛載代碼目錄
- 代碼更改會自動反映到容器中
- 只需要重啟容器讓 Python 重新載入代碼

但如果簡單重啟不生效，可以嘗試重建：
```bash
docker-compose build recommendation-api
docker-compose up -d recommendation-api
```

### Q4: 會丟失數據嗎？

**A**: 不會，因為：
- 只重啟 API 容器，不影響資料庫
- PostgreSQL 和 Redis 容器繼續運行
- 數據保存在 volume 中

### Q5: 重啟需要多久？

**A**: 
- 簡單重啟：5-10 秒
- 重建容器：30-60 秒（取決於網速和機器性能）

## 推薦流程

```
1. 執行 restart_api_only.bat
   ↓
2. 等待 5-10 秒
   ↓
3. 訪問 http://localhost:8000/trends
   ↓
4. 檢查時間是否正確
   ↓
5. 如果不正確，清除瀏覽器緩存後重試
   ↓
6. 如果還是不正確，執行 rebuild_api.bat
```

## 快速命令參考

```bash
# 查看運行中的容器
docker ps

# 重啟 API 容器
docker restart recommendation-api

# 查看容器日誌
docker logs recommendation-api

# 查看最後 20 行日誌
docker logs --tail 20 recommendation-api

# 實時查看日誌
docker logs -f recommendation-api

# 進入容器內部（調試用）
docker exec -it recommendation-api bash

# 檢查容器健康狀態
docker inspect recommendation-api | grep -A 5 Health

# 重建並重啟
docker-compose build recommendation-api
docker-compose up -d recommendation-api
```

## 總結

**最簡單的方式**：
```bash
restart_api_only.bat
```

然後訪問 http://localhost:8000/trends 檢查時間是否正確。

如果不行，再嘗試：
```bash
rebuild_api.bat
```
