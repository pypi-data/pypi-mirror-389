#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/10/17 22:55
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.schemas.video_types import SoraVideoRequest, Video
from meutils.apis.volcengine_apis import videos as volc_videos
from meutils.apis.runware import videos as runware_videos # todo 兼容


class OpenAIVideos(object):

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    async def create(self, request: SoraVideoRequest):
        response = {}
        if request.model.startswith("doubao-seedance"):
            response = await volc_videos.create_task(request, self.api_key)  # {'id': 'cgt-20250611152553-r46ql'}

        if task_id := (response.get("id") or response.get("task_id")):
            if self.api_key:
                await redis_aclient.set(task_id, self.api_key, ex=7 * 34 * 3600)

            return Video(id=task_id)

    async def get(self, task_id):
        video = Video(id=task_id)
        if api_key := await redis_aclient.get(task_id):
            api_key = api_key.decode()
        else:
            raise ValueError(f"task_id not found")

        if response := await volc_videos.get_task(task_id, api_key):
            logger.debug(bjson(response))

            status = response.get("status")
            video = Video(id=task_id, status=status, metadata=response)
            if video.status == "completed":
                video.progress = 100
                video.video_url = response.get("content", {}).get("video_url")  # 多个是否兼容

        return video


if __name__ == '__main__':
    model = "doubao-seedance-1-0-pro-fast-251015"
    request = SoraVideoRequest(
        # model=model,
        model=f"{model}_480p",
        # model=f"{model}_720p",
        # model=f"{model}_1080p",

        seconds="4",
        size="720x1280",
    )
    api_key = "267a3b8a-ef06-4d8f-bd24-150f99bb17c1"
    videos = OpenAIVideos(api_key=api_key)

    # video = arun(videos.create(request))

    # Video(id='cgt-20251031183121-zrt26', completed_at=None, created_at=1761906681, error=None, expires_at=None,
    #       model=None, object='video', progress=0, remixed_from_video_id=None, seconds=None, size=None, status='queued',
    #       video_url=None, metadata=None)

    task_id = "cgt-20251031184204-hqcn5"
    arun(videos.get(task_id))
