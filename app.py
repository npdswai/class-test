import streamlit as st
import pandas as pd
from datetime import date
import firebase_admin
from firebase_admin import credentials, auth, storage, firestore
import tempfile
import uuid

import os
import json


cred = credentials.Certificate(st.secrets["FIREBASE_SERVICE_ACCOUNT"])

# Firebase 초기화
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'class-test-1a3b3.firebasestorage.com'
    })




bucket = storage.bucket()
db = firestore.client()

# 예시 사용자 세션 (실제 구현에서는 로그인 후 세션에 user_id 저장)
user_id = "demo-user"

# Firebase 유틸리티 함수
def upload_pdf_to_firebase(file, filename):
    blob = bucket.blob(f"pdfs/{filename}")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.getbuffer())
        tmp_path = tmp.name
    blob.upload_from_filename(tmp_path, content_type="application/pdf")
    blob.make_public()
    return blob.public_url

def create_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return user.uid
    except Exception as e:
        return str(e)

def verify_user(email):
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except:
        return None

def save_subject(user_id, subject_name, year, semester, pdf_url):
    ref = db.collection("users").document(user_id).collection("subjects").document()
    ref.set({
        "subject_name": subject_name,
        "year": year,
        "semester": semester,
        "pdf_url": pdf_url
    })

def save_student(user_id, class_name, student_id, student_name):
    ref = db.collection("users").document(user_id).collection("classes").document(class_name).collection("students").document(student_id)
    ref.set({"student_name": student_name})

# UI 메뉴
menu = st.sidebar.selectbox("메뉴 선택", [
    "로그인 / 회원가입",
    "교과 관리",
    "수업 관리",
    "학생 관리",
    "수업 기록",
    "출결 및 특기사항 기록",
    "일자별 전체 조회"
])

# 로그인 / 회원가입
if menu == "로그인 / 회원가입":
    st.title("로그인")
    email = st.text_input("이메일")
    password = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        uid = verify_user(email)
        if uid:
            user_id = uid
            st.success("로그인 성공")
        else:
            st.error("존재하지 않는 사용자입니다")
    if st.button("회원가입"):
        result = create_user(email, password)
        st.success(f"회원가입 완료: {result}")

# 교과 관리
elif menu == "교과 관리":
    st.title("교과 관리")
    subject_name = st.text_input("교과명")
    year = st.selectbox("학년도", list(range(2020, 2031)))
    semester = st.selectbox("학기", ["1학기", "2학기"])
    file = st.file_uploader("수업계획 및 평가계획서 (PDF, 최대 10MB)", type=["pdf"])
    if st.button("등록"):
        if file and file.size <= 10 * 1024 * 1024:
            filename = f"{subject_name}_{year}_{semester}_{uuid.uuid4().hex}.pdf"
            pdf_url = upload_pdf_to_firebase(file, filename)
            save_subject(user_id, subject_name, year, semester, pdf_url)
            st.success(f"PDF 업로드 및 교과 등록 완료: [파일 보기]({pdf_url})")
        else:
            st.error("PDF 파일만 허용되며 10MB 이하만 가능합니다.")

# 수업 관리
elif menu == "수업 관리":
    st.title("수업 관리")
    st.info("Firestore 저장은 미구현 상태입니다.")
    selected_subject = st.text_input("교과명 (선택)")
    class_name = st.text_input("학반명")
    weekday = st.selectbox("요일", ["월", "화", "수", "목", "금"])
    period = st.selectbox("교시", list(range(1, 10)))
    if st.button("수업 등록"):
        st.success(f"{selected_subject} - {class_name} 수업 등록 완료")

# 학생 관리
elif menu == "학생 관리":
    st.title("학생 관리")
    selected_class = st.text_input("수업 반명 입력")
    student_id = st.text_input("학번")
    student_name = st.text_input("성명")
    if st.button("학생 추가"):
        save_student(user_id, selected_class, student_id, student_name)
        st.success(f"{student_name} 학생이 등록되었습니다.")
    st.file_uploader("CSV 업로드", type=["csv"])

# 수업 기록
elif menu == "수업 기록":
    st.title("수업 기록")
    selected_class = st.text_input("수업 반 입력")
    lesson_date = st.date_input("수업 일자", date.today())
    lesson_period = st.selectbox("교시", list(range(1, 10)))
    content = st.text_area("진도 내용")
    notes = st.text_area("특기사항")
    if st.button("기록 저장"):
        st.info("Firestore 기록 기능 미구현")
        st.success("수업 기록이 저장되었습니다.")

# 출결 및 특기사항 기록
elif menu == "출결 및 특기사항 기록":
    st.title("출결 및 특기사항 기록")
    selected_class = st.text_input("수업 반 입력")
    record_date = st.date_input("기록 일자", date.today())
    st.info("Firestore 저장은 추후 구현 예정")
    for i in range(2):
        name = st.text_input(f"학생 이름 {i+1}")
        status = st.selectbox(f"{name} 출결 상태", ["출석", "지각", "결석", "조퇴"], key=f"status_{i}")
        remark = st.text_input(f"{name} 특기사항", key=f"remark_{i}")
    st.button("저장")

# 일자별 전체 조회
elif menu == "일자별 전체 조회":
    st.title("일자별 전체 조회")
    view_date = st.date_input("조회 일자", date.today())
    st.markdown("### 예시 수업 기록")
    st.dataframe(pd.DataFrame({"반": ["1반", "2반"], "진도": ["소단원1", "소단원2"], "특기사항": ["우수", "주의"]}))
    st.markdown("### 예시 출결 기록")
    st.dataframe(pd.DataFrame({"성명": ["홍길동", "김영희"], "출결": ["출석", "조퇴"], "특기사항": ["지각", "복통"]}))
