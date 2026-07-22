import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 기본 설정
st.set_page_config(page_title="KOBIS 일별 박스오피스", layout="wide")
st.title("🎬 어제의 박스오피스 대시보드")

# 한국 시간 기준 어제 날짜 자동 계산 (KOBIS는 YYYYMMDD 형식)
yesterday = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=1)
target_dt = yesterday.strftime("%Y%m%d")
st.caption(f"조회 기준일(어제): {yesterday.strftime('%Y-%m-%d')}")

# 비밀 금고에서 인증키 불러오기
KOBIS_KEY = st.secrets["KOBIS_KEY"]

# API 호출
url = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
res = requests.get(url, params={"key": KOBIS_KEY, "targetDt": target_dt})

if res.status_code != 200:
    st.error(f"요청이 실패했어요 (상태코드: {res.status_code})")
    st.stop()

data = res.json()

# 키가 틀리면 faultInfo 상자가 온다
if "faultInfo" in data:
    st.error("인증키가 올바르지 않아요. Secrets의 KOBIS_KEY를 확인해 주세요.")
    st.stop()

box_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
if not box_list:
    st.error("데이터가 없어요. 날짜 형식(YYYYMMDD)을 확인해 주세요.")
    st.stop()

df = pd.DataFrame(box_list)

# 문자열로 오는 숫자들을 진짜 숫자로 변환
for col in ["rank", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]:
    df[col] = pd.to_numeric(df[col])

# 1위 영화 지표 카드
top = df.sort_values("rank").iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("어제 1위", top["movieNm"])
c2.metric("어제 관객수", f"{top['audiCnt']:,}명")
c3.metric("누적 관객", f"{top['audiAcc']:,}명")

# 보기 좋게 한국어 열 이름으로 정리
표 = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
표.columns = ["순위", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]
표 = 표.sort_values("순위").reset_index(drop=True)

st.subheader("📋 박스오피스 TOP 10")
st.dataframe(표, use_container_width=True)

# 관객수 상위 5편 막대그래프
st.subheader("📈 관객수 상위 5편")
top5 = 표.sort_values("관객수", ascending=False).head(5)
st.bar_chart(top5.set_index("영화명")["관객수"])
