import json
import os
import re
import time
import brotli
import random
import requests

from dailycheckin import CheckIn


class ICan(CheckIn):
    """
    爱看健康签到、分享和答题功能。
    传入cookie 自动完成签到、分享、答题和积分信息查询。
    """
    name = '爱看健康'

    def __init__(self, check_item: dict):
        self.name = check_item.get("name")
        self.union_id = check_item.get("union_id")
        self.open_id = check_item.get("open_id")
        self.authorization = check_item.get("authorization")
        self.base_url = 'https://ican.sinocare.com'

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541022) XWEB/16467",
            "Referer": "https://servicewechat.com/wxe92e6f360119272a/245/page-frame.html",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "sino-Auth": self.authorization,
        }

    def get_refresh_token(self):
        # POST https://ican.sinocare.com/api/sino-auth/oauth/token?
        # tenantId=000000&grant_type=wechat&scope=all&type=account&union_id=opm8mw-xKVFY_5M028jwFvZ4g0UA&open_id=oWXSX5PmDalBTXBgY4yF43Qzg-y8
        url = f'{self.base_url}/api/sino-auth/oauth/token'

        params = {
            'tenantId': '000000',
            'grant_type': 'wechat',
            'scope': 'all',
            'type': 'account',
            'union_id': self.union_id,
            'open_id': self.open_id
        }

        # 创建请求头副本并添加必要的头部
        headers = self.headers.copy()
        headers['Accept'] = '*/*'
        headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8'
        headers['Authorization'] = self.authorization

        # 禁用代理并设置超时
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理

        resp = session.post(
            url,
            params=params,
            headers=headers,
            timeout=30,
            verify=True  # 启用 SSL 验证
        )
        resp.headers['Accept-Encoding'] = 'gzip, deflate, br'

        # 检查响应状态
        if resp.status_code == 200:
            # 如果响应中有 JSON 数据，也可以保存

            try:
                response_data = resp.json()
                self.access_token = response_data.get('access_token')
                self.refresh_token = response_data.get('refresh_token')

                msg = f'获取 {response_data.get('nick_name')} 刷新令牌成功'
                return msg
            except ValueError:
                msg = f'获取 {self.name} 刷新令牌失败'
                return msg
        else:
            print(f"请求失败，状态码: {resp.status_code}")
            print(f"响应内容: {resp.text}")
            msg = f'{self.name} 刷新令牌请求失败，状态码: {resp.status_code}， 响应内容: {resp.text}'
            return msg

    def get_sign_status(self):
        url = f'{self.base_url}/api/sino-member/signRecord/signStatus'

        headers = self.headers.copy()
        headers['sino-Auth'] = self.access_token

        # 禁用代理并设置超时
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理

        resp = session.get(
            url,
            headers=headers,
            timeout=30,
            verify=True  # 启用 SSL 验证
        )
        resp.headers['Accept-Encoding'] = 'gzip, deflate, br'
        if resp.status_code == 200:
            # 如果响应中有 JSON 数据，也可以保存

            try:
                response_data = resp.json()
                if response_data.get('msg') == '您已签到':
                    msg = '今日已签到\n'
                    self.sign_status = True
                    return msg
                else:
                    msg = '今日未签到\n'
                    self.sign_status = False
                    return msg
            except ValueError:
                msg = f'获取 {self.name} 签到状态失败，尝试直接签到\n'
                self.sign_status = None
                return msg

        else:
            msg = f'{self.name} 获取签到状态失败，状态码: {resp.status_code}， 响应内容: {resp.text}\n'
            return msg

    def signin(self):
        url = f'{self.base_url}/api/sino-member/signRecord/sign'
        headers = self.headers.copy()
        headers['sino-Auth'] = self.access_token

        # 禁用代理并设置超时
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理

        resp = session.get(
            url,
            headers=headers,
            timeout=30,
            verify=True  # 启用 SSL 验证
        )
        resp.headers['Accept-Encoding'] = 'gzip, deflate, br'
        if resp.status_code == 200:
            # 如果响应中有 JSON 数据，也可以保存

            try:
                response_data = resp.json()
                if response_data.get('code') == 200:
                    msg = f'今日签到{response_data.get('msg')}'
                    return msg
                else:
                    msg = f'今日签到异常{response_data.get('msg')}'
                    return msg
            except ValueError:
                msg = f'今日签到异常 json解析异常 {resp.content}'
                return msg

        else:
            msg = f'{self.name} 签到失败，状态码: {resp.status_code}， 响应内容: {resp.text}'
            return msg

    def get_question(self):
        url = f'{self.base_url}/api/sino-social/dailyQuestion/getQuestion'
        headers = self.headers.copy()
        headers['sino-Auth'] = self.access_token

        # 禁用代理并设置超时
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理

        resp = session.get(
            url,
            headers=headers,
            timeout=30,
            verify=True  # 启用 SSL 验证
        )

        resp.headers['Accept-Encoding'] = 'gzip, deflate, br'
        if resp.status_code == 200:
            # 如果响应中有 JSON 数据，也可以保存

            try:
                response_data = resp.json()
                if response_data.get('code') == 200:
                    if response_data.get('data').get('accountAnswer'):
                        self.answerQuestion = True
                        msg = f'今日已答题，你的答案为：{response_data.get('data').get('accountAnswer')}，正确答案为：{response_data.get('data').get('answer')}'
                        return msg
                    self.answerQuestion = False
                    self.questionId = response_data.get('data').get('questionId')
                    self.answerQuestionSize = len(response_data.get('data').get('options'))
                    msg = f'获取今日问题ID {response_data.get('msg')}'
                    return msg
                else:
                    msg = f'获取今日问题ID {response_data.get('msg')}'
                    return msg
            except ValueError:
                msg = f'获取今日问题ID json解析异常 {resp.content}'
                return msg

        else:
            msg = f'{self.name} 获取今日问题ID失败，状态码: {resp.status_code}， 响应内容: {resp.text}'
            return msg

    def answer_question(self):
        if not self.questionId:
            return '请先获取今日问题ID'
        url = f'{self.base_url}/api/sino-social/dailyQuestion/getQuestionResult'
        headers = self.headers.copy()
        headers['sino-Auth'] = self.access_token
        headers['Content-Type'] = 'application/json'

        # 随机选择一个答案
        options = ['A', 'B', 'C', 'D'][:self.answerQuestionSize]
        answer = random.choice(options)

        params = json.dumps({
            "questionId": self.questionId,
            "answerTime": random.randint(10, 300),
            "accountAnswer": answer
        })

        # 禁用代理并设置超时
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理

        resp = session.post(
            url,
            headers=headers,
            data=params,
            timeout=30,
            verify=True  # 启用 SSL 验证
        )

        resp.headers['Accept-Encoding'] = 'gzip, deflate, br'
        if resp.status_code == 200:
            try:
                response_data = resp.json()
                if response_data.get('code') == 200:
                    msg = f'今天答题 {response_data.get('msg')}'
                    return msg
                else:
                    msg = f'今天答题 {response_data.get('msg')}'
                    return msg
            except ValueError:
                msg = f'今天答题 json解析异常 {resp.content}'
                return msg

        else:
            msg = f'{self.name} 今天答题失败，状态码: {resp.status_code}， 响应内容: {resp.text}'
            return msg

    def get_content_recommendation(self):
        url = f'{self.base_url}/api/sino-social/PGCContentRecommendation/getContentRecommendation?flag=1'
        headers = self.headers.copy()
        headers['sino-Auth'] = self.access_token
        # 禁用代理并设置超时
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理

        resp = session.get(
            url,
            headers=headers,
            timeout=30,
            verify=True  # 启用 SSL 验证
        )

        resp.headers['Accept-Encoding'] = 'gzip, deflate, br'
        if resp.status_code == 200:
            try:
                response_data = resp.json()

                data = response_data.get('data', [])
                # 使用切片获取前2个元素，然后提取 articleId
                self.articleIds = [item.get('articleId') for item in data[:2] if item.get('articleId') is not None]
                msg = f'获取文章ID {response_data.get('msg')}'
                return msg
            except ValueError:
                msg = f'获取文章ID json解析异常 {resp.content}'
                return msg

        else:
            msg = f'{self.name} 获取文章ID失败，状态码: {resp.status_code}， 响应内容: {resp.text}'
            return msg

    def add_for_article(self, articleId):
        url = f'{self.base_url}/api/sino-social/sharerecord/addForArticle'

        headers = self.headers.copy()
        headers['sino-Auth'] = self.access_token
        headers['Content-Type'] = 'application/json'

        # 禁用代理并设置超时
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理

        params = json.dumps({
            "messageContentId": articleId,
            "shareType": 2
        })

        resp = session.post(
            url,
            headers=headers,
            data=params,
            timeout=30,
            verify=True  # 启用 SSL 验证
        )

        resp.headers['Accept-Encoding'] = 'gzip, deflate, br'
        if resp.status_code == 200:
            msg = f'{articleId} 文章分享成功\n'
            return msg
        else:
            msg = f'{articleId} 文章分享失败，状态码: {resp.status_code}， 响应内容: {resp.text}\n'
            return msg

    def get_user_prizes(self):
        url = f'{self.base_url}/api/sino-lottery/activity_record/check-unclaimed-prizes'

        headers = self.headers.copy()
        headers['sino-Auth'] = self.access_token
        # 禁用代理并设置超时
        session = requests.Session()
        session.trust_env = False  # 禁用系统代理

        resp = session.get(
            url,
            headers=headers,
            timeout=30,
            verify=True  # 启用 SSL 验证
        )

        resp.headers['Accept-Encoding'] = 'gzip, deflate, br'
        if resp.status_code == 200:
            try:
                response_data = resp.json()
                nowIntegral = response_data.get('data').get('nowIntegral')
                msg = f'当前积分： {nowIntegral}'
                return msg
            except ValueError:
                msg = f'积分获取 json解析异常 {resp.content}'
                return msg
        else:
            msg = f'{self.name} 积分获取失败，状态码: {resp.status_code}， 响应内容: {resp.text}'
            return msg

    def main(self):
        msg_refresh_token = self.get_refresh_token()
        if self.refresh_token:
            time.sleep(3)
            msg_sign_status = self.get_sign_status()

            if not self.sign_status:
                time.sleep(3)
                msg_sign_status += self.signin()
            time.sleep(3)

            msg_question = self.get_question()

            if self.answerQuestion is False or self.answerQuestion is None:
                time.sleep(2)
                msg_answer = self.answer_question()
                msg_question = f'{msg_question}\n{msg_answer}\n{self.get_question()}'
            time.sleep(3)
            msg_recommendation = self.get_content_recommendation()
            time.sleep(3)
            msg_article = ''
            if self.articleIds:

                for articleId in self.articleIds:
                    msg_article += self.add_for_article(articleId)
                    time.sleep(3)
            msg_prizes = self.get_user_prizes()
            return f'{msg_refresh_token}\n{msg_sign_status}\n{msg_question}\n{msg_recommendation}\n{msg_article}\n{msg_prizes}'
        return msg_refresh_token


if __name__ == "__main__":
    with open(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json"),
            encoding="utf-8",
    ) as f:
        datas = json.loads(f.read())
    _check_item = datas.get("ICAN", [])[0]
    print(ICan(check_item=_check_item).main())
