import streamlit as st
from pytube import YouTube
from moviepy.editor import *
import google.generativeai as genai
from datetime import datetime
import time
import os
from PIL import Image
from streamlit_player import st_player
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import re
import mock
from pytube.cipher import get_throttling_function_code
from pytube import YouTube

st.set_page_config(
  page_title="나만의 YouTube 요약 서비스",
  page_icon="🎬",
)

google_youtube_api_key = "AIzaSyAuKiyYNDPq_Q3Sf0FLw7onz6vIifsB7NQ"

api_key_index = 0

def patched_throttling_plan(js: str):
    raw_code = get_throttling_function_code(js)
    transform_start = r"try{"
    plan_regex = re.compile(transform_start)
    match = plan_regex.search(raw_code)
    transform_plan_raw = js
    step_start = r"c\[(\d+)\]\(c\[(\d+)\](,c(\[(\d+)\]))?\)"
    step_regex = re.compile(step_start)
    matches = step_regex.findall(transform_plan_raw)
    transform_steps = []
    for match in matches:
        if match[4] != '':
            transform_steps.append((match[0],match[1],match[4]))
        else:
            transform_steps.append((match[0],match[1]))
    return transform_steps

def get_comments(youtube, video_id):
    comments = []
    next_page_token = None
    while True:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            pageToken=next_page_token,
            maxResults=100,
            textFormat="plainText"
        ).execute()
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "authorDisplayName": comment["authorDisplayName"],
                "textDisplay": comment["textDisplay"],
                "likeCount": comment["likeCount"],
                "publishedAt": comment["publishedAt"]
            })
            comment_id = item["snippet"]["topLevelComment"]["id"]
            reply_response = youtube.comments().list(
                part="snippet",
                parentId=comment_id,
                textFormat="plainText"
            ).execute()
            for reply in reply_response["items"]:
                reply_comment = reply["snippet"]
                comments.append({
                    "authorDisplayName": reply_comment["authorDisplayName"],
                    "textDisplay": reply_comment["textDisplay"], 
                    "likeCount": reply_comment["likeCount"],
                    "publishedAt": reply_comment["publishedAt"]
                })
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            return pd.DataFrame(comments)

def get_video_details(youtube, video_id):
    request = youtube.videos().list(
        part=["snippet","statistics","contentDetails"], 
        id=video_id
    )
    response = request.execute()
    for item in response["items"]:
        data = dict(contentDetails=item["snippet"]["description"])
        if "likeCount" in item["statistics"]:
            data["like_count"] = item["statistics"]["likeCount"]
        if "commentCount" in item["statistics"]:
            data["comment_count"] = item["statistics"]["commentCount"]
    return data


st.title("YouTube 영상 요약기")
st.caption("By Park Joon")
        
api_key = st.sidebar.text_input("Gemini API KEY를 입력해주세요:", type="password")

if api_key:
    genai.configure(api_key=api_key)        
else:
    st.warning("API KEY를 입력해주세요.")
    st.stop()

generation_config = {
    "temperature": 0.4,
    "top_p": 0.95,
    "top_k": 0,
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT", 
        "threshold": "BLOCK_NONE"
    },
]

model_selection = st.sidebar.radio("**사용할 모델을 선택하세요 :**",("gemini-1.5-pro", "gemini-1.5-flash"), captions = ("가격↑/성능↑/속도↓", "가격↓/성능↓/속도↑"))

if model_selection == "gemini-1.5-pro":
    model_name = "gemini-1.5-pro"
else:
    model_name = "gemini-1.5-flash"
    
url = st.text_input("YouTube 영상 URL을 입력해주세요:")

youtube = build("youtube", "v3", developerKey=google_youtube_api_key)

if url:
    try:
        if "youtube.com/shorts/" in url:
            video_id = url.split("shorts/")[1]
            url = f"https://www.youtube.com/watch?v={video_id}"
        elif "youtube.com/live/" in url:
            video_id = url.split("live/")[1]
            url = f"https://www.youtube.com/watch?v={video_id}"          

        yt = YouTube(url)
        video_id = yt.vid_info['videoDetails']['videoId']

        st.markdown(f"## {yt.title}")

        st_player(url)        

        with st.expander("영상 정보"):
            detail = get_video_details(youtube, video_id)  
            st.text_area(label="**영상 설명**", value=detail['contentDetails'])
            st.markdown(f"- #### 조회수 : {yt.views:,} 회")
        
            hours, remainder = divmod(yt.length, 3600)
            minutes, seconds = divmod(remainder, 60)
        
            if hours > 0:
                st.markdown(f"- #### 영상 길이 : {hours}시간 {minutes}분 {seconds}초")
            else:
                st.markdown(f"- #### 영상 길이 : {minutes}분 {seconds}초")
        
            publish_date = yt.publish_date.strftime("%Y년 %m월 %d일")
            st.markdown(f"- #### 게시 날짜 : {publish_date}")
            st.markdown(f"- #### 채널명 : [{yt.author}]({yt.channel_url})")
        
            if 'like_count' in detail:
                st.markdown(f"- #### 좋아요 수 : {detail['like_count']} 개")
            else:
                st.markdown("- #### 좋아요 수가 제공되지 않습니다.")
        
            if 'comment_count' in detail:
                st.markdown(f"- #### 댓글 수 : {detail['comment_count']} 개")
            else:  
                st.markdown("- #### 댓글 수 : 댓글 사용이 중지되어 가져올 수 없습니다.")      

        if yt.length > 3599:
            attachment_type = st.radio("**영상 분석 방식을 선택하세요 :**", ("음성만",), index=0)
            st.warning("1시간 이상의 영상은 현재 음성 분석만 가능합니다.")
        else:
            attachment_type = st.radio("**첨부 파일 형식을 선택하세요 :**", ("영상 + 음성", "영상만", "음성만"), index=0)
       
        analyze_video = st.button("영상 분석")                  
        
        if analyze_video:
            with st.spinner("진행 중..."):
                with mock.patch('pytube.cipher.get_throttling_plan', patched_throttling_plan):              
                    videos = yt.streams.filter(adaptive=True, file_extension='mp4', res="360p")
                    if len(videos) == 0:
                        videos = yt.streams.filter(adaptive=True, file_extension='mp4')
                        video = videos[0]
                    else:
                        video = videos[0]    
                    video.download(filename='video.mp4')
            
                    audios = yt.streams.filter(only_audio=True, abr="128kbps", file_extension='mp4')
                    if len(audios) == 0:
                        audios = yt.streams.filter(only_audio=True, file_extension='mp4')
                        audio = audios[0]
                    else:
                        audio = audios[0]
                    audio.download(filename='audio.mp4')
                    audio_clip = AudioFileClip("audio.mp4")
                    audio_clip.write_audiofile("audio.m4a", codec='aac')
            
                    video_file = genai.upload_file(path="video.mp4")
                    audio_file = genai.upload_file(path="audio.m4a")
            
                    while video_file.state.name == "PROCESSING" or audio_file.state.name == "PROCESSING":
                        time.sleep(5)
                        video_file = genai.get_file(video_file.name)
                        audio_file = genai.get_file(audio_file.name)
            
                    if video_file.state.name == "FAILED" or audio_file.state.name == "FAILED":
                        raise ValueError("파일 처리 실패")
        
            with st.spinner("영상 분석 중..."):
                system_instruction = "업로드한 영상을 한국어로 3줄로 요약해줘."
                model = genai.GenerativeModel(model_name=model_name,
                                              generation_config=generation_config,
                                              system_instruction=system_instruction,
                                              safety_settings=safety_settings)          

                if attachment_type == "영상 + 음성":
                    response = model.generate_content([video_file, audio_file], request_options={"timeout": 600})
                elif attachment_type == "영상만":
                    response = model.generate_content(video_file, request_options={"timeout": 600})
                else:
                    response = model.generate_content(audio_file, request_options={"timeout": 600})

                if 'result_text' not in st.session_state:
                    st.session_state.result_text = ""
                
                result_text = st.empty()
                result_text.success(response.text)
                
                st.session_state.result_text = response.text

                with st.expander("📋 마크다운 복사"):
                    st.code(st.session_state.result_text, language='markdown')              
            
            genai.delete_file(video_file.name)
            genai.delete_file(audio_file.name) 
            os.remove("video.mp4")
            os.remove("audio.mp4")
            os.remove("audio.m4a")     

    except Exception as e:
        st.error(f"에러 발생: {str(e)}")
