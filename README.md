---
title: Chatbot Llama2 Questions
emoji: 🐨
colorFrom: green
colorTo: yellow
sdk: gradio
sdk_version: 3.47.1
app_file: app.py
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference


TEXT EXTRACTION A CHANGER

docker compose -f examples/server_side_embeddings/huggingface/docker-compose.yml up -d


docker run -p 8001:80 -d -rm --name huggingface-embedding-server ghcr.io/huggingface/text-embeddings-inference:cpu-0.3.0 --model-id BAAI/bge-small-en-v1.5 --revision -main
pip install -U pip setuptools
