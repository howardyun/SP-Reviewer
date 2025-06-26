import os
import re
import json

# NoSQL/HTTP URL提取正则
url_pattern = re.compile(r"(?<!['\"])(https?://[^\s'\"]+)")

SERVICE_SIGNATURES = {
    "model_api": {
        "openai_api": ["import openai", "api.openai.com", "openai.ChatCompletion"],
        "cohere_api": ["import cohere", "cohere.Client", "api.cohere.ai"],
        "anthropic_api": ["import anthropic", "anthropic.com"],
        "replicate_api": ["import replicate", "replicate.run", "replicate.models"],
        "groq_api": ["import groq", "groq.com"],
        "huggingface_local": ["from transformers", "from_pretrained(", "AutoModel", "pipeline("],
        "huggingface_api": ["huggingface_hub", "hf_hub_download"],
        "vllm": ["import vllm", "vllm.LLMEngine"],
        "llama_index": ["import llama_index", "GPTVectorStoreIndex", "ServiceContext"],
        "langchain": ["import langchain", "langchain.llms", "LLMChain"],
        "gpt4all": ["import gpt4all"],
        "ctransformers": ["import ctransformers"],
        "llamacpp": ["import llama_cpp", "llama_cpp.Llama"]
    },
    "database": {
        "sqlite3": ["import sqlite3", "sqlite3.connect"],
        "sqlalchemy": ["import sqlalchemy", "sqlalchemy.create_engine", "sessionmaker"],
        "mongodb": ["import pymongo", "MongoClient", "mongodb://", "mongodb+srv://"],
        "redis": ["import redis", "redis.StrictRedis", "redis://"],
        "firebase": ["import firebase_admin", "firebase_admin.db"],
        "tinydb": ["import tinydb", "TinyDB", "Query"],
        "postgresql": ["import psycopg2", "psycopg2.connect", "postgresql://", "import asyncpg"],
        "mysql": ["import mysql.connector", "mysql.connector.connect", "mysql://"],
        "supabase": ["import supabase", "supabase.create_client", "supabase.io"],
        "duckdb": ["import duckdb", "duckdb.connect"],
        "neo4j": ["import neo4j", "GraphDatabase", "bolt://"],
        "cassandra": ["import cassandra", "cassandra.cluster", "Cluster"],
        "influxdb": ["import influxdb", "InfluxDBClient"],
        "dynamodb": ["boto3.client(\"dynamodb\")", "dynamodb."],
        "cloud_firestore": ["from google.cloud import firestore", "firestore.Client"]
    },
    "cloud_sdk": {
        "aws": ["import boto3", "boto3.client", "s3.amazonaws.com", "sns.", "dynamodb"],
        "gcp": ["from google.cloud", "googleapiclient.discovery"],
        "azure": ["from azure", "azure.storage.blob"],
        "supabase": ["import supabase", "supabase.io"],
        "vercel": ["vercel.com"],
        "streamlit_cloud": ["streamlit.io", "share.streamlit.io"],
        "render": ["onrender.com"]
    },
    "http_api": {
        "requests": ["requests.get(", "requests.post(", "http://", "https://"],
        "httpx": ["import httpx"],
        "aiohttp": ["import aiohttp", "aiohttp.ClientSession"],
        "urllib": ["import urllib.request"],
        "fetch_api": ["fetch(", "base_url="]
    },
    "web_ui_framework": {
        "gradio": ["import gradio", "gr.Interface", "blocks="],
        "streamlit": ["import streamlit as st"],
        "dash": ["import dash"],
        "panel": ["import panel as pn"],
        "flask": ["from flask", "import flask"],
        "fastapi": ["from fastapi", "FastAPI"]
    },
    "frontend_embed": {
        "iframe_embed": ["<iframe", "src=\"https://"],
        "plotly": ["import plotly"],
        "bokeh": ["import bokeh"],
        "pyvis": ["import pyvis"],
        "ipyleaflet": ["import ipyleaflet"],
        "pydeck": ["import pydeck"]
    },
    "security_and_auth": {
        "auth0": ["auth0.com", "import auth0"],
        "firebase_auth": ["firebase_admin.auth"],
        "jwt": ["import jwt", "pyjwt"],
        "oauthlib": ["import oauthlib"],
        "cryptography": ["import cryptography", "fernet"]
    },
    "media_processing": {
        "opencv": ["import cv2"],
        "pillow": ["from PIL", "import Image"],
        "imageio": ["import imageio"],
        "ffmpeg": ["import ffmpeg", "ffmpeg.input"],
        "torchaudio": ["import torchaudio"],
        "moviepy": ["import moviepy"],
        "librosa": ["import librosa"]
    }
}

# 以下函数保持原有逻辑不变
def extract_http_urls(content):
    return list(set(url_pattern.findall(content)))

def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    service_hits = {}
    http_urls = extract_http_urls(content)

    for service_type, subtypes in SERVICE_SIGNATURES.items():
        service_hits[service_type] = {}
        for subtype, patterns in subtypes.items():
            hits = [p for p in patterns if p in content]
            if hits:
                if service_type == "http_api":
                    service_hits[service_type][subtype] = {
                        "keywords": hits,
                        "urls": http_urls if http_urls else []
                    }
                else:
                    service_hits[service_type][subtype] = hits
    return service_hits

def analyze_repo(repo_path):
    result = {
        "repo": os.path.basename(repo_path),
        "services": {},
    }
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                hits = analyze_file(full_path)
                for s_type, s_hits in hits.items():
                    for s_subtype, value in s_hits.items():
                        if s_type == "http_api" and isinstance(value, dict):
                            result["services"].setdefault(s_type, {}).setdefault(s_subtype, {
                                "keywords": set(),
                                "urls": set()
                            })
                            result["services"][s_type][s_subtype]["keywords"].update(value["keywords"])
                            result["services"][s_type][s_subtype]["urls"].update(value["urls"])
                        else:
                            result["services"].setdefault(s_type, {}).setdefault(s_subtype, set()).update(value)

    # 转换 set 为 list
    for s_type in result["services"]:
        for s_subtype in result["services"][s_type]:
            if isinstance(result["services"][s_type][s_subtype], dict):
                for k in result["services"][s_type][s_subtype]:
                    result["services"][s_type][s_subtype][k] = list(result["services"][s_type][s_subtype][k])
            else:
                result["services"][s_type][s_subtype] = list(result["services"][s_type][s_subtype])
    return result

def main(base_dir):
    all_results = []
    futures = []

    for repo in os.listdir(base_dir):
        repo_path = os.path.join(base_dir, repo)
        if os.path.isdir(repo_path):
            print(f"Analyzing {repo}...")
            result = analyze_repo(repo_path)
            all_results.append(result)

    with open("external_services_report.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main(r"F:\download_space\2022-03")
