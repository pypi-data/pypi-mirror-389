# 1 日志不打在server中 不打在工具中, 只打在core 中

import math
import asyncio
from pro_craft import AsyncIntel
from pro_craft.utils import create_async_session
from digital_life.utils import memoryCards2str

from datetime import datetime

# server
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, model_validator, field_validator, RootModel
import re
from digital_life import logger
import os
from pro_craft.utils import extract_
import json

class AIServerInputError(Exception):
    pass


class MemoryCard(BaseModel):
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    time: str = Field(..., description="卡片记录事件的发生时间")


class MemoryCard2(BaseModel):
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    time: str = Field(..., description="卡片记录事件的发生时间")
    tag: str = Field(..., description="标签1,max_length=4")




# 1. 定义记忆卡片模型 (Chapter)
class Chapter(BaseModel):
    """
    表示文档中的一个记忆卡片（章节）。
    """
    title: str = Field(..., description="记忆卡片的标题")
    content: str = Field(..., description="记忆卡片的内容")

# 2. 定义整个文档模型 (Document)
class Document(BaseModel):
    """
    表示一个包含标题和多个记忆卡片的文档。
    """
    title: str = Field(..., description="整个文档的标题内容")
    chapters: List[Chapter] = Field(..., description="文档中包含的记忆卡片列表")


class MemoryCardGenerate(BaseModel):
    title: str = Field(..., description="标题",min_length=1, max_length=30)
    content: str = Field(..., description="内容",min_length=1,max_length=1000)
    time: str = Field(..., description="日期格式,YYYY年MM月DD日,其中YYYY可以是4位数字或4个下划线,MM可以是2位数字或2个--,DD可以是2位数字或2个--。年龄范围格式,X到Y岁,其中X和Y是数字。不接受 --到--岁")
    score: int = Field(..., description="卡片得分", ge=0, le=10)
    tag: str = Field(..., description="标签1",max_length=4)
    topic: int = Field(..., description="主题1-7",ge=0, le=7)

    @field_validator('time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        combined_regex = r"^(?:(\d{4}|-{4}|-{2})年(\d{2}|-{2})月(\d{2}|-{2})日|(\d+)到(\d+)岁|-{1,}到(\d+)岁|(\d+)到-{1,}岁)"
        match = re.match(combined_regex, v)
        if match:
            return v
        else:
            raise ValueError("时间无效")

class MemoryCardsGenerate(BaseModel):
    memory_cards: list[MemoryCardGenerate] = Field(..., description="记忆卡片列表")

class TimeCheck(BaseModel):
    time: str = Field(...,description="")
    @field_validator('time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        combined_regex = r"^(?:(\d{4}|-{4}|-{2})年(\d{2}|-{2})月(\d{2}|-{2})日)"
        match = re.match(combined_regex, v)
        if match:
            return v
        elif v in ["稚龄","少年","弱冠","而立","不惑","知天命","耳顺","古稀","耄耋","鲐背","期颐"]:
            return v
        else:
            raise ValueError("时间无效")
doc = {"稚龄":"0到10岁",
    "少年":"11到20岁",
    "弱冠":"21到30岁",
    "而立":"31到40岁",
    "不惑":"41到50岁",
    "知天命":"51到60岁",
    "耳顺":"61到70岁",
    "古稀":"71到80岁",
    "耄耋":"81到90岁",
    "鲐背":"91到100岁",
    "期颐":"101到110岁"} 


class MemoryCardManager:
    def __init__(self,inference_save_case = False,model_name  = ""):
        self.inters = AsyncIntel(model_name = model_name)
        self.inference_save_case = inference_save_case

    # @staticmethod
    # def get_score_overall(
    #     S: list[int], total_score: int = 0, epsilon: float = 0.001, K: float = 0.8
    # ) -> float:
    #     """
    #     计算 y = sqrt(1/600 * x) 的值。
    #     计算人生总进度
    #     """
    #     x = sum(S)
        
    #     S_r = [math.sqrt((1/101) * i)/5 for i in S]
    #     return sum(S_r)

    #     # return math.sqrt((1/601) * x)  * 100

    # @staticmethod
    # def get_score(
    #     S: list[int], total_score: int = 0, epsilon: float = 0.001, K: float = 0.01
    # ) -> float:
    #     # 人生主题分值计算
    #     # 一个根据 列表分数 计算总分数的方法 如[1,4,5,7,1,5] 其中元素是 1-10 的整数

    #     # 一个非常小的正数，确保0分也有微弱贡献，100分也不是完美1
    #     # 调整系数，0 < K <= 1。K越大，总分增长越快。

    #     for score in S:
    #         # 1. 标准化每个分数到 (0, 1) 区间
    #         normalized_score = (score + epsilon) / (10 + epsilon)

    #         # 2. 更新总分
    #         # 每次增加的是“距离满分的剩余空间”的一个比例
    #         total_score = total_score + (100 - total_score) * normalized_score * K

    #         # 确保不会因为浮点数精度问题略微超过100，虽然理论上不会
    #         if total_score >= 100 - 1e-9:  # 留一点点余地，避免浮点数误差导致判断为100
    #             total_score = 100 - 1e-9  # 强制设置一个非常接近100但不等于100的值
    #             break  # 如果已经非常接近100，可以提前终止

    #     return total_score

    async def ascore_from_memory_card(self, memory_cards: list[str]) -> list[int]:
        # 正式运行 0088
        logger.info(f'函数输入 & {type(memory_cards)} &  {memory_cards}')
        tasks = []
        class MemoryCardScore(BaseModel):
            score: int = Field(..., description="得分")
            reason: str = Field(..., description="给分理由")

        for memory_card in memory_cards:
            tasks.append(
                self.inters.intellect_format(
                    input_data=memory_card,
                    prompt_id = "memorycard-score",
                    version = None,
                    inference_save_case=self.inference_save_case,
                    OutputFormat = MemoryCardScore,
                )
            )
        result = await asyncio.gather(*tasks, return_exceptions=False)
        logger.info(f'函数输出 & {type(result)} &  {result}')
        return result

    async def amemory_card_merge(self, memory_cards: list[str]):
        # 0089

        logger.critical(f'函数输入 & {type(memory_cards)} &  {memory_cards}')
        result = await self.inters.intellect_format(
            input_data=memory_cards,
            prompt_id = "memorycard-merge",
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = MemoryCard2,
        )
        time = await self.get_time(result.get("content"))
        result.update({"time":time})
        logger.info(f'函数输出 & {type(result)} &  {result}')
        return result

    async def amemory_card_polish(self, memory_card: dict) -> dict:
        # 0090
        logger.info(f'函数输入 & {type(memory_card)} &  {memory_card}')
        result = await self.inters.intellect_format(
            input_data="\n记忆卡片标题: "+ memory_card["title"]+ "\n记忆卡片内容: " + memory_card["content"] + "\n记忆卡片发生时间: " + memory_card["time"],
            prompt_id = "memorycard-polish",
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = MemoryCard,
        )
        result.update({"time": ""})
        logger.info(f'函数输出 & {type(result)} &  {result}')
        return result

    def _generate_check(self,chat_history_str):
        if "human" not in chat_history_str:
            raise AIServerInputError("聊天历史生成记忆卡片时, 必须要有用户的输入信息")
        
        if "ai" in chat_history_str:
            chat_history_str = "human" + chat_history_str.split("human",1)[-1]
            chat_history_str = chat_history_str.rsplit("ai:",1)[0]
        return chat_history_str
    
    async def get_time(self,content):
        output_format = """
```json
{
"time":----年--月--日,
"reason": 推理原因
}
```
"""

        output_format2 = """
严格按照格式输出, 

输出格式如下:
```json
{
"stage":"根据发生的事件推测其发生的阶段",
"reason": "推理原因"
}
```
"""
        result_time = "----年--月--日"
        # 先做一个年月日格式的生成
        ai_result_time = await self.inters.intellect(
            input_data=f"当前时间为 {datetime.now()}" + content,
            output_format=output_format,
            prompt_id = "memorycard-get-time",
            version=None,
            )
        try:
            json_str_time = extract_(ai_result_time,r'json')
            result_dict_time = json.loads(json_str_time)
            result_time = result_dict_time.get("time","----年--月--日")
            TimeCheck(time = result_time)
        except Exception as e:
            logger.warning(f'年月日格式的生成 & {type(result_time)} &  {result_time}')
            result_time = "----年--月--日"

        logger.info(f'年月日格式的生成 & {type(result_time)} &  {result_time}')
        result_time2 = result_time
        if "--年--月--日" in result_time:
            ai_result_time = await self.inters.intellect(
                input_data=content,
                output_format=output_format2,
                prompt_id = "memorycard-get-timeline",
                version=None,
                )
            try:
                json_str_time2 = extract_(ai_result_time,r'json')
                result_dict_time2 = json.loads(json_str_time2)
                result_time2 = result_dict_time2.get("stage","而立")
                try:
                    TimeCheck(time = result_time2)
                except Exception as e:
                    try:
                        result_time2 = result_time2.split("到")[0]
                    except Exception as e:
                        raise Exception("生成时间段错误了")
                result_time2 = doc[result_time2]
            except Exception as e:
                result_time2 = "----年--月--日"
        return result_time2

    async def agenerate_memory_card_by_text(self, chat_history_str: str):
        """
        0093 聊天历史生成记忆卡片-memory_card_system_prompt
        0094 聊天历史生成记忆卡片-time_prompt
        """
        logger.info(f'函数输入 & {type(chat_history_str)} &  {chat_history_str}')

        weight=int(os.getenv("card_weight",1000))
        number_ = len(chat_history_str) // weight + 1

        output_format = """
输出结构如下
```json
{
"title": 整个文档的标题内容
"chapters":[
                {
                "title": "记忆卡片的标题",
                "content":"记忆卡片的内容"
                },
                {
                "title": "记忆卡片的标题",
                "content":"记忆卡片的内容"
                },
            ]
}
```
"""
        ai_result = await self.inters.intellect(
            input_data=f"建议输出卡片数量:  {number_} 个记忆卡片" + chat_history_str,
            output_format=output_format,
            prompt_id = "memorycard-generate-content",
            version=None,
            )

        json_str = extract_(ai_result,r'json')
        result_dict = json.loads(json_str)
        chapters = result_dict["chapters"]
        if [chapter.get("content") for chapter in chapters] == [""]:
            raise AIServerInputError("没有记忆卡片生成")
        
        # tasks = []
        # for input_data in input_datas:
        #     tasks.append(
        #         self.intellect(
        #             input_data = input_data,
        #             prompt_id = prompt_id,
        #             OutputFormat = OutputFormat,
        #             ExtraFormats = ExtraFormats,
        #             version = version,
        #             inference_save_case = inference_save_case,
        #             **kwargs,
        #         )
        #     )
        # results = await asyncio.gather(*tasks, return_exceptions=False)



        class MemoryCardGenerate2(BaseModel):
            title: str = Field(..., description="标题",min_length=1, max_length=30)
            content: str = Field(..., description="内容",min_length=1,max_length=1000)
            score: int = Field(..., description="卡片得分", ge=0, le=10)
            tag: str = Field(..., description="标签1, max_length=4")
            time: str = Field(..., description="日期格式,YYYY年MM月DD日,其中YYYY可以是4位数字或4个下划线,MM可以是2位数字或2个--,DD可以是2位数字或2个--。年龄范围 输出对应的文字描述, 比如:而立, 不惑")
            topic: int = Field(..., description="主题1-5",ge=0, le=5)
        try:
            info_dicts = await self.inters.intellect_formats(
                input_datas=[chapter.get("content") for chapter in chapters],
                prompt_id = "memorycard-format",
                version = None,
                inference_save_case=self.inference_save_case,
                OutputFormat = MemoryCardGenerate2,
                logger=logger
            )
        except Exception as e:
            info_dicts = await self.inters.intellect_formats(
                input_datas=[chapter.get("content") for chapter in chapters],
                prompt_id = "memorycard-format",
                version = None,
                inference_save_case=self.inference_save_case,
                OutputFormat = MemoryCardGenerate2,
                logger=logger
            )
        
        logger.info(f'info_dicts & {type(info_dicts)} &  {info_dicts}')
        # [{'title': '牵引空客A380', 'content': '我是白云机场机坪操作部的牵引车司机，2023年的一天，要牵引一架即将执飞国际航线的空客A380。每次靠近它都能感受到压迫力与使命感。抵达远程停机位时，飞机还在夜色中沉睡，机务工程师们已在机腹下忙碌，橙色警示灯闪烁，机坪上空寂寥，只有风声和远处跑道飞机起降的轰鸣。我跳下牵引车，仔细与机务负责人核对信息、检查牵引连接点，深知每个操作关乎数百人的旅行计划与安全。', 'time': '2023年--月--日', 'score': 7, 'tag': '牵引飞机', 'topic': 3}, {'title': '机场紧急牵引任务', 'content': '在机场工作，紧张时刻家常便饭。最让我印象深刻且紧张的一次，是在一个雷雨交加的夜晚。一架航班遭遇强烈乱流，机上一名旅客突发急病紧急降落，降落时轮胎受损需牵引。接到任务时，狂风暴雨，电闪雷鸣，机坪能见度极低，塔台焦急强调飞机上有急需救援的病人。我驾驶牵引车冲进雨幕，雨刮器开到最大也几乎看不清路。平时牵引普通航班时间充裕，可这次每分每秒都至关重要，我必须快速抵达飞机且确保安全。', 'time': '未知', 'score': 7, 'tag': '紧急任务', 'topic': 3}] info_dicts

        
        for info_dict in info_dicts:
            time = await self.get_time(info_dict.get("content"))
            
            info_dict.update({"time":time})
        logger.info(f'info_dicts2 & {type(info_dicts)} &  {info_dicts}')

        # super_log(time_dicts,"generate_memory_card-time_dicts")
        logger.info(f'chapters & {type(chapters)} &  {chapters}')


        for i,chapter in enumerate(chapters):
            chapter.update(info_dicts[i])
        
        for chapter in chapters:
            try:
                MemoryCardsGenerate(memory_cards=[chapter])
            except Exception as e:
                # super_log(f"{e}",'agenerate_memory_card Error')
                chapter.update({"time":"----年--月--日"})
            if len(chapter.get("tag")) >4:
                chapter.update({"tag":""})

        result = chapters
        logger.info(f'函数输出 & {type(result)} &  {result}')
        
        return result
    
    async def agenerate_memory_card(self, chat_history_str: str):

        logger.info(f'函数输入 & {type(chat_history_str)} &  {chat_history_str}')
        
        chat_history_str = self._generate_check(chat_history_str)
        result = await self.agenerate_memory_card_by_text(chat_history_str = chat_history_str)

        return result


# ----年11月--日至次年02月--日