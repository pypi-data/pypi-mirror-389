



import json
from pro_craft import AsyncIntel

import os
from typing import Dict, Any
from digital_life.redis_ import get_redis_client, store_with_expiration, get_value
from digital_life.utils import memoryCards2str, extract_article, extract_json
from digital_life.models import BiographyRequest, BiographyResult, Extract_Person,Extract_Place, Biography_Free, ContentVer
from digital_life import logger
import asyncio
import httpx
import uuid
import re
from pydantic import BaseModel, Field, model_validator, field_validator, RootModel


async def aget_(url = ""):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()  # 如果状态码是 4xx 或 5xx，会抛出 HTTPStatusError 异常
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.json()}") # 假设返回的是 JSON
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    return None


def extract_from_text(text: str):
    matches = []
    for match in re.finditer(r'!\[\]\(([^)]+)\)', text):
        url = match.group(1).strip()
        position = match.start()
        matches.append((url, position))
    return matches



user_callback_url = os.getenv("user_callback_url")

# TODO 后续使用redis 进行任务队列设计

class BiographGenerateError(Exception):
    pass

def remove_urls_from_text(text: str) -> str:
    """
    检测文本中的 Markdown 格式图片链接 (![]()) 并将其剔除。

    Args:
        text: 待处理的字符串。

    Returns:
        剔除了 Markdown 格式图片链接的字符串。
    """
    # 使用 re.sub 替换所有匹配的模式为空字符串
    # r'!\[\]\([^)]+\)' 匹配 ![]() 结构，其中括号内的内容是 URL
    cleaned_text = re.sub(r'!\[\]\([^)]+\)', '', text)
    return cleaned_text


class BiographyGenerate:
    def __init__(self,inference_save_case = False,model_name = "doubao-1-5-pro-256k-250115"):
        self.inters = AsyncIntel(model_name = model_name)
        self.inference_save_case = inference_save_case
        # ArkAdapter
        self.biograph_redis = get_redis_client(username = os.getenv("redis_username"), 
                                             password = os.getenv("redis_password"), 
                                             host = os.getenv("redis_host"), 
                                             port = os.getenv("redis_port"),
                                             db = 22)

    def _split_into_chunks(self,my_list, chunk_size=5):
        """
        使用列表推导式将列表分割成大小为 chunk_size 的块。
        """
        return [
            my_list[i : i + chunk_size] for i in range(0, len(my_list), chunk_size)
        ]

    async def amaterial_generate(self, vitae: str, memory_cards: list[str]) -> str:
        """
        素材整理
        vitae : 简历
        memory_cards : 记忆卡片们
        0085 素材整理
        0082 素材增量生成
        """
        try:
            # --- 示例 ---
            chunks = self._split_into_chunks(memory_cards, chunk_size=2)

            material = ""
            for i, chunk in enumerate(chunks):
                chunk = json.dumps(chunk, ensure_ascii=False)
                if i == 0:
                    output_format = ""
                    # 素材整理初始
                    material = await self.inters.intellect(input_data=vitae + chunk,
                                        output_format=output_format,
                                        prompt_id ="biograph_material_init",
                                        version = None,
                                        inference_save_case = self.inference_save_case,
                                        )
                else:
                    # 素材增量生成
                    output_format = ""
                    material = await self.inters.intellect(input_data=material,
                                        output_format=output_format,
                                        prompt_id ="biograph_material_add",
                                        version = None,
                                        inference_save_case = self.inference_save_case,
                                        )
        except Exception as e:
            raise BiographGenerateError(f"素材整理出错 {e}") from e

        return material

    async def aoutline_generate(self, material: str) -> str:
        """
        0084 大纲生成
         #TODO 由于output_format 太过复杂导致无法使用pydantic
        """
        output_format = """
输出格式
```json
{
    "预章" : [
        {
            "chapter_number": "-",
            "title": "标题",
            "topic": "第三人称。指导写作的建议"
        },
    ]
    "第一部 童年与自然启蒙": [
        {
            "chapter_number": "第一章",
            "title": "标题",
            "topic": "指导写作的建议"
        },
        {
            "chapter_number": "第二章",
            "title": "标题",
            "topic": "指导写作的建议"
        }
    ]
    ...
    "尾章" : [
        {
            "chapter_number": "-",
            "title": "标题",
            "topic": "指导写作的建议"
        },
    ]
}
```
"""
        
        try:
            outline_origin = await self.inters.intellect(input_data=material,
                                                output_format=output_format,
                                                prompt_id ="biograph-outline",
                                                version = None,
                                                inference_save_case=self.inference_save_case)
            outline = extract_json(outline_origin)
            result = json.loads(outline)

        except Exception as e:
            raise Exception(f"0084 传记大纲生成失败: {e}")
        return result
    
    async def title_generate(self, outline: dict) -> str:
        """
        0085 传记标题生成
        """
        class BiographPaidTitle(BaseModel):
            title: str = Field(..., description="传记标题")

        result = await self.inters.intellect_format(
            input_data=outline,
            prompt_id ="biograph-paid-title",
            OutputFormat=BiographPaidTitle,
            ExtraFormats=[],
            inference_save_case=self.inference_save_case
        )
        return result.get('title')

    async def agener_biography_brief(self, outline: dict) -> str:
        """
        0083 传记简介
        """
        # result = await self.inters.intellect_remove_format(
        #     input_data = json.dumps(outline, ensure_ascii=False),
        #     prompt_id = "0083",
        #     version = None,
        #     inference_save_case=self.inference_save_case,
        #     OutputFormat = ContentVer,
        # )
        output_format = ""
        result = await self.inters.intellect(input_data=json.dumps(outline, ensure_ascii=False),
                                    output_format=output_format,
                                    prompt_id ="biograph-brief",
                                    version = None,
                                    inference_save_case = self.inference_save_case,
                                    )

        result = extract_json(result)
        result = result.replace('"content":','')
        result = remove_urls_from_text(result)
        return result

    async def extract_person_name(self, bio_chunk: str):
        """0087 提取人名"""

        result = await self.inters.intellect(input_data=bio_chunk,
                                    output_format="",
                                    prompt_id ="biograph-extract-person-name",
                                    version = None,
                                    inference_save_case = self.inference_save_case,
                                    )
        result = json.loads(extract_json(result))
        result = result.get("content")
        return result

    async def extract_person_place(self, bio_chunk: str):
        """0086 提取地名"""

        # result = await self.inters.intellect_remove_format(
        #     input_data = bio_chunk,
        #     prompt_id = "0086",
        #     version = None,
        #     inference_save_case=self.inference_save_case,
        #     OutputFormat = Extract_Place,
        # )

        output_format = ""
        result = await self.inters.intellect(input_data=bio_chunk,
                                    output_format=output_format,
                                    prompt_id ="biograph-extract-place",
                                    version = None,
                                    inference_save_case = self.inference_save_case,
                                    )
        result = json.loads(extract_json(result))
        result = result.get("content")
        return result

    async def awrite_chapter(
        self,
        chapter,
        master="",
        material="",
        outline: dict = {},
        suggest_number_words=3000,
    ):
        created_material = ""
        try:
            # 0080 prompt_get_infos 0080 从素材中抽取必要撰写素材内容 biograph-extract-material
            # 0081 prompt_base  0081
            # TODO 大量的format 怎么办
            
            # material = await self.inters.intellect_remove_format(
            #     input_data = {
            #                     "material": material,
            #                     "frame": json.dumps(outline,ensure_ascii=False),
            #                     "Requirements for Chapter Writing": json.dumps(chapter,ensure_ascii=False)
            #                 },
            #     prompt_id = "0080",
            #     version = None,
            #     inference_save_case=self.inference_save_case,
            #     OutputFormat = ContentVer,
            #         )
            
            output_format = """"""
            try:
                material = await self.inters.intellect(input_data={
                                                                "material": material,
                                                                "frame": json.dumps(outline,ensure_ascii=False),
                                                                "Requirements for Chapter Writing": json.dumps(chapter,ensure_ascii=False)
                                                                },
                                    output_format=output_format,
                                    prompt_id ="biograph-extract-material",
                                    version = None,
                                    inference_save_case = self.inference_save_case,
                                    )
            except Exception as e:
                raise Exception(f'素材收拾的时候报错 {e}')
            

            try:
                output_format = """"""
                article = await self.inters.intellect(input_data = {
                                                                "目标人物": master,
                                                                "章节名称": chapter.get("chapter_number") + "   " + chapter.get("title"),
                                                                "目标字数范围":suggest_number_words,
                                                                "核心主题": chapter.get("topic"),
                                                                "素材":material,
                                                            },
                                            output_format=output_format,
                                            prompt_id ="biograph-writer",
                                            version = None,
                                            inference_save_case = self.inference_save_case,
                                            )
            except Exception as e:
                raise Exception(f'这是在生成文章时候报错 {e}')
            try:
                chapter_name = await self.extract_person_name(article)
                chapter_place = await self.extract_person_place(article)
            except Exception as e:
                raise Exception(f'提取人名地名报错 {e}')
            try:
                # assert isinstance(chapter_name["content"], list)
                # assert isinstance(chapter_place["content"], list)
                1 == 1
            except Exception as e:
                raise Exception(f'断言出错 {e}')
            # a = {
            #                                     "article": article,
            #                                     "素材":material.get("content"),
            #                                             }
            # article = await self.inters.intellect_remove(
            #                             input_data = {
            #                                     "article": article,
            #                                     "素材":material.get("content"),
            #                                             },
            #                             output_format=output_format,
            #                             prompt_id ="0079",
            #                             version = None,
            #                             inference_save_case = self.inference_save_case,
            #                             )

            return {
                "chapter_number": chapter.get("chapter_number"),
                "article": article,
                "material": material,
                "created_material": created_material,
                "chapter_name": chapter_name,
                "chapter_place": chapter_place,
            }

        except Exception as e:
            print(f"Error processing chapter {chapter.get('chapter_number')}: {e}")

            return {
                "chapter_number": chapter.get("chapter_number"),
                "article": "",
                "material": "material",
                "created_material": "created_material",
                "chapter_name": "chapter_name",
                "chapter_place": "chapter_place",
            }

    async def agenerate_biography_free(
        self, user_name: str, vitae: str, memory_cards: list[dict]
    ):
        memoryCards_str, _ = memoryCards2str(memory_cards)
        result = await self.inters.intellect_format(
            input_data = f"{user_name},{vitae},{memoryCards_str}",
            prompt_id = "biograph-free-writer",# biograph-free-writer 0095
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = Biography_Free,
        )

        return result

    async def _generate_biography(self,task_id: str, 
                                  memory_cards: str,
                                  vitae: str,
                                  user_name: str):

        task = {
            "task_id": task_id,
            "status": "PENDING",
            "biography_title": None,
            "biography_brief": None,
            "biography_json": None,
            "biography_name": None,
            "biography_place": None,
            "error_message": None,
            "progress": 0.0,
            "request_data": "",  # 存储请求数据以备后续使用
        }
        task["status"] = "PROCESSING"
        task["progress"] = 0.1

        try:
            
            # 素材整理
            material = await self.amaterial_generate(
                vitae=vitae, memory_cards=memory_cards
            )
            task["progress"] = 0.2
            task["material"] = material
            store_with_expiration(self.biograph_redis, task_id, task, 3600) 

        
            # 生成大纲
            outline = await self.aoutline_generate(material)
            task["progress"] = 0.3
            task["outline"] = outline
            store_with_expiration(self.biograph_redis, task_id, task, 3600) 


            # 生成标题
            title = await self.title_generate(outline)
            task["progress"] = 0.4
            task["biography_title"] = title
            store_with_expiration(self.biograph_redis, task_id, task, 3600) 

            

            # 生成传记简介
            brief = await self.agener_biography_brief(outline)
            task["biography_brief"] = brief
            task["progress"] = 0.5
            store_with_expiration(self.biograph_redis, task_id, task, 3600) 


            # 生成传记正文  

            biography_json = {}
            biography_name = []
            biography_place = []

            tasks = []
            for part, chapters in outline.items():
                for chapter in chapters:
                    tasks.append(
                        self.awrite_chapter(
                            chapter,
                            master=user_name,
                            material=material,
                            outline=outline,
                        )
                    )
            results = await asyncio.gather(*tasks, return_exceptions=False)
            
            # 后处理拼接
            for part, chapters in outline.items():
                biography_json[part] = []
                for chapter in chapters:
                    chapter_number = chapter.get("chapter_number")
                    for x in results:
                        if x.get("chapter_number") == chapter_number:
                            biography_json[part].append(x.get("article"))
                            biography_name += x.get("chapter_name")
                            biography_place += x.get("chapter_place")

            assert isinstance(biography_json, dict)
            assert isinstance(biography_name, list)
            assert isinstance(biography_place, list)

            biography_name = list(set(biography_name))
            biography_place = list(set(biography_place))
            task["biography_json"] = biography_json
            task["biography_name"] = biography_name
            task["biography_place"] = biography_place
            task["status"] = "COMPLETED"
            task["progress"] = 1.0


            biography_callback_url_success = user_callback_url + f'/api/inner/notifyBiographyStatus?generateTaskId={task_id}&status=1'
            store_with_expiration(self.biograph_redis, task_id, task, 3600) 
            await aget_(url = biography_callback_url_success)


        except Exception as e:
            task["status"] = "FAILED"
            task["error_message"] = str(e)
            task["progress"] = 1.0
            biography_callback_url_failed = user_callback_url + f'/api/inner/notifyBiographyStatus?generateTaskId={task_id}&status=0'
            store_with_expiration(self.biograph_redis, task_id, task, 3600) 

            await aget_(url = biography_callback_url_failed)

