import base64
import hashlib
import os
import time
from io import BytesIO

from PIL import Image
from fastapi import FastAPI, Request
from funcaptcha_challenger import predict
from pydantic import BaseModel

from util.log import logger
from util.model_support_fetcher import ModelSupportFetcher

app = FastAPI()
PORT = 8181
IS_DEBUG = True
fetcher = ModelSupportFetcher()


class Task(BaseModel):
    type: str
    image: str
    question: str


class TaskData(BaseModel):
    clientKey: str
    task: Task
    softID: str


def process_image(base64_image: str, variant: str):
    if base64_image.startswith("data:image/"):
        base64_image = base64_image.split(",")[1]

    image_bytes = base64.b64decode(base64_image)
    image = Image.open(BytesIO(image_bytes))

    ans = predict(image, variant)
    logger.debug(f"predict {variant} result: {ans}")
    return ans


@app.post("/createTask")
async def create_task(request: Request):
    try:
        request_data = await request.json()
        data = TaskData.parse_obj(request_data)
        client_key = data.clientKey
        task_type = data.task.type
        image = data.task.image
        question = data.task.question
    except Exception as e:
        print(f"Error: {e}")
    ans = {
        "errorId": 0,
        "errorCode": "",
        "status": "ready",
        "solution": {
            "label": "arrows_objecthand",
        }
    }

    taskId = hashlib.md5(str(int(time.time() * 1000)).encode()).hexdigest()
    ans["taskId"] = taskId
    # 把question写入本地
    if not os.path.exists('question'):
        os.makedirs('question')
    with open(f"question/{taskId}.txt", "w") as f:
        f.write(question)
    # if question in fetcher.supported_models:
    ans["solution"]["objects"] = [process_image(image, '3d_rollball_objects')]
    # else:
    #     ans["errorId"] = 1
    #     ans["errorCode"] = "ERROR_TYPE_NOT_SUPPORTED"
    #     ans["status"] = "error"
    #     ans["solution"]["objects"] = []

    return ans


@app.get("/support")
async def support():
    # 从文件中读取模型列表
    return fetcher.supported_models


@app.post("/getBalance")
async def balance(request: Request):
    # 从文件中读取模型列表
    return {
        "softBalance": 0,
        "inviteBalance": 0,
        "inviteBy": "99",
        "errorId": 0,
        "balance": 9999999
    }


@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    logger.error(f"error: {exc}")
    return {
        "errorId": 1,
        "errorCode": "ERROR_UNKNOWN",
        "status": "error",
        "solution": {"objects": []}
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
