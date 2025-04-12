import streamlit as st
from googleapiclient.discovery import build
import datetime

# YouTube API Key ko kahin secure jagah store karein (e.g., Streamlit secrets)
YOUTUBE_API_KEY = st.secrets["AIzaSyAQk4wvU0OKfk3EhUKINI77foI2u76wjmg"]
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_channel_info(channel_id):
    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )
    response = request.execute()
    if response and response['items']:
        return response['items'][0]
    return None

def get_videos_from_channel(channel_id, max_results=50):
    videos = []
    next_page_token = None
    while True:
        request = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=max_results,
            type="video",
            pageToken=next_page_token
        )
        response = request.execute()
        if 'items' in response:
            video_ids = [item['id']['videoId'] for item in response['items']]
            video_details_request = youtube.videos().list(
                part="statistics,snippet",
                id=','.join(video_ids)
            )
            video_details_response = video_details_request.execute()
            if 'items' in video_details_response:
                videos.extend(video_details_response['items'])
        if 'nextPageToken' in response:
            next_page_token = response['nextPageToken']
        else:
            break
        if len(videos) >= 500: # Limit to a reasonable number for analysis
            break
    return videos

def analyze_niche(keyword, max_channels=20):
    results = []
    request = youtube.search().list(
        part="snippet",
        q=keyword,
        type="channel",
        maxResults=max_channels,
        order="relevance" # You might want to experiment with other orders
    )
    response = request.execute()
    if 'items' in response:
        for item in response['items']:
            channel_id = item['id']['channelId']
            channel_info = get_channel_info(channel_id)
            if channel_info:
                published_at = datetime.datetime.strptime(channel_info['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                three_months_ago = datetime.datetime.now() - datetime.timedelta(days=90)
                if published_at > three_months_ago and 'viewCount' in channel_info['statistics'] and int(channel_info['statistics']['viewCount']) >= 500000:
                    total_videos = channel_info['statistics'].get('videoCount', 0)
                    results.append({
                        'channel_id': channel_id,
                        'title': channel_info['snippet']['title'],
                        'published_at': published_at.strftime("%Y-%m-%d"),
                        'total_views': int(channel_info['statistics']['viewCount']),
                        'total_videos': total_videos,
                        'description': channel_info['snippet'].get('description', '')
                    })
    return results

def analyze_competitors(keyword, max_channels=10):
    # Similar logic to analyze_niche but focused on deeper analysis
    competitors_data = []
    search_results = analyze_niche(keyword, max_channels=max_channels)
    for result in search_results:
        channel_id = result['channel_id']
        videos = get_videos_from_channel(channel_id)
        # Analyze video titles, descriptions, tags for keywords and content strategy
        video_keywords = []
        for video in videos:
            video_keywords.extend(video['snippet'].get('tags', []))
            video_keywords.append(video['snippet']['title'])
            video_keywords.append(video['snippet']['description'])
        # Basic keyword frequency analysis (you can use NLP techniques for more advanced analysis)
        keyword_frequency = {}
        for word in ' '.join(video_keywords).lower().split():
            if word in keyword_frequency:
                keyword_frequency[word] += 1
            else:
                keyword_frequency[word] = 1

        competitors_data.append({
            'channel_id': channel_id,
            'title': result['title'],
            'published_at': result['published_at'],
            'total_views': result['total_views'],
            'total_videos': result['total_videos'],
            'description': result['description'],
            'keyword_frequency': keyword_frequency
            # Add more analysis like average views per video, etc.
        })
    return competitors_data

st.title("YouTube Niche Analyzer")

tab1, tab2 = st.tabs(["YouTube Niches Finder", "Niche Analyze"])

with tab1:
    st.header("Find Potential YouTube Niches")
    keyword = st.text_input("Enter a broad keyword to find related niches:")
    if st.button("Analyze Niches"):
        if keyword:
            niche_channels = analyze_niche(keyword)
            if niche_channels:
                st.subheader(f"Channels related to '{keyword}' (within last 3 months and > 500k views):")
                for channel in niche_channels:
                    st.write(f"**Channel:** [{channel['title']}](https://www.youtube.com/channel/{channel['channel_id']})")
                    st.write(f"  - Created At: {channel['published_at']}")
                    st.write(f"  - Total Views: {channel['total_views']:,}")
                    st.write(f"  - Total Videos: {channel['total_videos']}")
                    st.write(f"  - Description: {channel['description'][:200]}...") # Show a snippet
            else:
                st.info(f"No relevant channels found for '{keyword}' based on the criteria.")
        else:
            st.warning("Please enter a keyword.")

with tab2:
    st.header("Deeply Analyze a Specific Niche")
    niche_keyword = st.text_input("Enter the specific niche keyword to analyze:")
    if st.button("Analyze This Niche"):
        if niche_keyword:
            st.subheader(f"Analyzing niche: '{niche_keyword}'")
            competitor_analysis_results = analyze_competitors(niche_keyword)
            if competitor_analysis_results:
                st.subheader("Potential Competitors:")
                for competitor in competitor_analysis_results:
                    st.write(f"**Channel:** [{competitor['title']}](https://www.youtube.com/channel/{competitor['channel_id']})")
                    st.write(f"  - Created At: {competitor['published_at']}")
                    st.write(f"  - Total Views: {competitor['total_views']:,}")
                    st.write(f"  - Total Videos: {competitor['total_videos']}")
                    st.write("  - Top Keywords:")
                    top_keywords = sorted(competitor['keyword_frequency'].items(), key=lambda item: item[1], reverse=True)[:10]
                    for word, count in top_keywords:
                        st.write(f"    - {word}: {count}")
                    st.write("---")
                # Add your logic here to determine niche saturation and viability
                # based on the analyzed competitors. This will require more sophisticated analysis.
                st.info("Further analysis on niche saturation and viability can be added here based on the competitor data.")
            else:
                st.info(f"No relevant competitors found for the niche '{niche_keyword}' based on the criteria.")
        else:
            st.warning("Please enter a niche keyword to analyze.")
