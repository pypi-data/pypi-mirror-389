## 단일 종목 수집 후 저장  
  
### 환경변수로 기본값 제어 가능  
export SCRAPER_HEADLESS=true  
export SCRAPER_SINK_CHUNK=1000  
  
### Mongo 연결은 db2-hj3415 쪽 init 로직이 CLI 내부에 있다면, 옵션 또는 env로 지정  
export MONGO_URI="mongodb://localhost:27017"  
export MONGO_DB="nfs_db"  
  
### 삼성전자: c103 + c104 모두 저장  
scraper2 ingest one 005930 --pages c103 c104

### 예: 저장하지 않고 번들만 수집  

scraper2 ingest one 005930 --pages c103 c104 --no-save --collect-only

#### 가능 옵션:  
    •  --pages c103 c104 : 처리할 페이지 선택  
    •  --save/--no-save : DB 저장 여부(defalut --save)
    •  --collect-only : 수집만 하고 저장하지 않음(defalut False)

---

## 여러 종목 동시 수집  
  
### 쉼표 구분  
scraper2 ingest many 005930,000660 --pages c103 c104 --concurrency 2 
  
### 파일 입력 (한 줄에 하나)  
scraper2 ingest many --file ./codes.txt --pages c103 c104 --concurrency 3  

---

## 헬스체크/버전  
  
scraper2 health  
scraper2 version  
