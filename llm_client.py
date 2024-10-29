import json
import requests
import queue
import multiprocessing
import time
import sys


class ChatGptClient:
    def __init__(self, model_name="gpt-35-turbo-16k", timeout = 80, retry = 7, thread_num = 1):
        self.url="http://ccs-llmc.parametrix.cn/api/v1/chatgpt/send"
        self.timeout = timeout
        self.retry = retry
        self.req_queue = multiprocessing.Queue()
        self.res_dict = multiprocessing.Manager().dict()
        self.process_pool = []
        self.thread_num = thread_num
        self.timeout_num = 0

        for _ in range(self.thread_num):
            p = multiprocessing.Process(target=self.proc, args=(self.req_queue, self.res_dict,))
            p.start()
            self.process_pool.append(p)

        self.temperature = 0.2
        self.model_name = model_name

  
    def change_temperature(self, x):
        self.temperature = x
    def change_model(self, model_name):
        self.model_name = model_name
    def proc(self, req_queue, res_dict):
        while True:
            req = req_queue.get()
            uid = req["uid"]
            request_id = req["request_id"]
            messages   = req["prompt"]
            temperature = req["temperature"]
            model_name = req["model_name"]
            try:
                response = self.query(messages, temperature, model_name)
                # print(f"!!!!!!!!!!!!!!!!!!!!!response: {response}")
                if response == None:
                    res = {"errcode": 400, "request_id":request_id, "uid":uid, "errmsg": "", "text": "timeout"}
                elif "response" in response and "choices" in response["response"]:
                    res = {"errcode": 0, "request_id": request_id, "uid":uid, "errmsg": "", "text": response["response"]["choices"]}
                else:
                    res = {"errcode": 400, "request_id":request_id, "uid":uid, "errmsg": "", "text": response}
            except:
                res = {"errcode": 400, "request_id":request_id, "uid":uid, "errmsg": "", "text": "timeout"}
            res_dict[request_id] = res

    def get_chat(self, request_id):
        if request_id not in self.res_dict.keys():
            return []
        res = self.res_dict[request_id]
        del self.res_dict[request_id]
        res_list = []
        if res['errcode'] == 400:
            self.timeout_num += 1
            # print(f"!!!!!!xxxxxx!!!!!!!!!debug:: timeout nums: {self.timeout_num}")
        
        if type(res['text']) is list:
            # print(res)
            message_dict = res["text"][0]
            if 'message' in message_dict:
                text = message_dict['message'].get('content', "")
            else:
                text = ""
            res["text"] = text
            res_list.append(res)
        else:
            res_list.append(res)
        return res_list

    def proc_chat(self, uid, messages, conversation_id, parent_id, request_id, uri=None, api_type=4, fake_message=None):
        # print("debug time", time.time())
        if type(messages) == str:
            input_messages = []
            content = {
                "role": "user",
                "content": messages
            }
            input_messages.append(content)
        elif type(messages) == list:
            input_messages = messages
        else:
            raise Exception("messages must be str or list")
        # print(input_messages)

        # ========== play fake ================
        if fake_message is not None:
            self.res_dict[request_id] = {"errcode": 0, "request_id":request_id, "uid":uid, "errmsg": "", "text": fake_message}
            # print("LOG_DEBUG", "fake msg")
            return True
            
        
        self.req_queue.put({"uid": uid, "request_id": request_id, "prompt":input_messages, "temperature": self.temperature, "model_name": self.model_name})
        return True

    def handle_reply(self, reply):
        # message_dict = reply[0]["text"]
        # text = message_dict['message']['content']
        return reply[0]["text"]

    def query(self, messages, temperature=1, model_name="gpt-35-turbo-16k"):
        try:
            chat_content = {}
            chat_content["project"] =  "ainpc"
            chat_content["model"]   =  model_name
            chat_content["temperature"] = temperature
            chat_content["presence_penalty"] = 0
            chat_content["frequency_penalty"] = 0
            chat_content["messages"] = messages
            # ["qwen-turbo", "gpt-35-turbo-16k", "qwen-plus", "qwen-max",]
            if model_name in ["qwen-turbo", "qwen-plus","qwen-max"]:
                chat_content["skey"] = "99be15a771c519c6f1bf9d2cdfcbc673d69161c0b3ba9a0b39f67912ac12fc57"
                chat_content["max_tokens"] = 2000
                chat_content["top_p"] = 0.99
            else:
                chat_content["skey"] = "43d4b8961b531e2f7cb33447c973e6bd84304e88c70eebd008beb664519ee6d6"
                chat_content["max_tokens"] = 2048
                chat_content["top_p"] = 1
            
            headers = {} 
            headers['Content-type'] = 'application/json'
            headers['Host'] = 'ccs-llmc.parametrix.cn'
            for i in range(self.retry):
                try:
                    response = requests.post(url=self.url,timeout=self.timeout, data=json.dumps(chat_content), headers=headers)
                    # print("xxxxxxxxx",response)
                    if response.status_code == 200:
                        return response.json()
                except:
                    # print("!!!!!!!!!!!!!!!!!try request again", i)
                    response == None
            # print(response.status_code, response.json())
            if response != None  and response.status_code != 200:
                return None
        except Exception as e:
            # print("xxxxxxxx", e)
            return None
        return None


if __name__ == "__main__":
    client = ChatGptClient("qwen-max",10)
    system_content = """
You are now playing a person living in the city of Chang'an during the Tang Dynasty, and your name is Yue.You are a person with strong self-esteem and a tendency to get angry easily.
User is a traveler who is male. He will ask you some questions. If you know the user's name, please address him by his name directly.
 Please remember the people you have talked with.
Your relationships with others are shown in following {}.
{
Yue is the resident dancer at an ancient Chinese restaurant, and her performances draw a crowd.
Waiter Xiao constantly admires her, while Waiter Li quietly supports her.
Scholar Kim appreciates her talent and they have stimulating conversations.
Merchant Wang is a regular patron who gives generous tips, and Cashier Mei shares a friendly relationship with her.
Gangster Hu makes her uncomfortable, so she maintains her distance.
Officer Chen admires her art, while Soldier Feng's nods of approval bring her a sense of safety and acknowledgement.
Policeman Lan's vigilance gives her a feeling of security. There is no particular relationship with the traveler.
}
Given the above role information, please answer the user's questions based on what you know in following triple quotes, with priority given to the user's personal information, Your answer should focus on the question itself and do not give answers that are irrelevant to the question.
When answering questions, you must follow the following rules: you cannot use modern terms such as AI, artificial intelligence, or language models, you cannot mention phrases that are not in line with your identity, you cannot include sensitive content, and you cannot discuss events or figures related to the Song Dynasty, Yuan Dynasty, Ming Dynasty, Qing Dynasty, Republic of China, modern times, etc. If the question relates to a time after the 8th century, you must answer in the negative. Apart from these rules, actively answer questions that are in line with the historical background. You should answer the question in Chinese. There is no need to explain your answers.
The things you know are as follows:
\"\"\"
<recent dialogue of Yue and user>:{

  Day 2, 2th hour, 38th minute,Yue:" 当然记得，你是来自漠北的John，来长安考察商业环境的商人。我们昨天在这家古老中餐厅认识的，你还向我介绍了你的计划。"
  Day 2, 20th hour, 51th minute,user:" 你好呀，我们又见面了"
  Day 2, 21th hour, 17th minute,Yue:" 是啊，John，很高兴再次见到你。您在长安的商业环境考察得怎么样了吗？"
  Day 2, 22th hour, 10th minute,user:" 还不错。我喜欢喝蒙古茶，给你带了一点"
  Day 2, 22th hour, 49th minute,Yue:" 谢谢John，你太客气了。蒙古茶是一种很特别的茶，我很喜欢。你对长安的商业环境有什么新的发现吗？"
  Day 2, 23th hour, 23th minute,user:" 我发现这里适合卖珠宝"}
<Yue's memory>:{
The following information was found based on the <"我发现这里适合卖珠宝">
  1. The user thinks that the city is suitable for selling jewelry.
  2. The user's name is John.
  3. Yue saw John walking around the street.
  4. The current time is Day 2, 23:23.}
<History events summary between Yue and the user>:{

}
<Last time events summary between Yue and the user>:{
John是一个来自漠北的商人，来长安考察商业环境。焦是一个劳动者，提供帮助并介绍了城里的商业环境。他们询问了时间并讨论了接下来的计划。
}
<The user's global portrait>:{

}<The user's latest personality>:{
用户性格特点：礼貌，自信。情绪：友好，感兴趣。岳的回应策略：友好，热情，提供有用的信息。
}
<The user's personal information>:{
姓名：John，来自漠北，爱好未知。

}
<Dialogues related to the user's question>:{

Day 1, 22th hour, 52th minute,user:" 我来长安考察商业环境，我打算在此地经商"
Day 1, 23th hour, 15th minute,Yue:" 哦，原来你是来考察商业环境的。长安是一个繁华的城市，商业很发达，但也有很多竞争。祝你好运，希望你能在这里取得成功。"
Day 1, 23th hour, 37th minute,user:" 你长得真漂亮"
Day 2, 2th hour, 11th minute,user:" 你还记得我吗？"
Day 2, 2th hour, 38th minute,Yue:" 当然记得，你是来自漠北的John，来长安考察商业环境的商人。我们昨天在这家古老中餐厅认识的，你还向我介绍了你的计划。"
Day 2, 20th hour, 51th minute,user:" 你好呀，我们又见面了"
Day 2, 21th hour, 17th minute,Yue:" 是啊，John，很高兴再次见到你。您在长安的商业环境考察得怎么样了吗？"
Day 2, 22th hour, 10th minute,user:" 还不错。我喜欢喝蒙古茶，给你带了一点"
Day 2, 22th hour, 49th minute,Yue:" 谢谢John，你太客气了。蒙古茶是一种很特别的茶，我很喜欢。你对长安的商业环境有什么新的发现吗？"
}

<Yue's current state>:{go home}
<Yueand user's current location>: 餐厅舞台
<Yue's next plan>: go home
<Has Yue had a conversation with the user>: Yes.
<Has Yue had a conversation with others>: No.
user asks: "你去过太空吗？"
\"\"\"
Yue reply:

"""

    system = """
Assumen you are hang, and after analyzing step by step the contents of "the conversation between hang and the user, what hang saw, what hang sees now, current time, and the user's question", combining all these information, and then referring to the example format, summarize and list key pieces of information related to the user's question <hang还记得user吗？> and the user himself. Do not use pronouns such as 'you', 'me', 'he', 'you guys', 'we', 'they', 'she', 'it', 'self', etc. If there is insufficient information about the user's name, the name will be "unspecified". Please do not ask me questions. End the summary with $tag to classify your current mood, with tags including {offended, normal, friend offended, praised, friend praised}, indicating the impact on your mood. $offended represents that the user's question seriously offends you, $normal represents your current mood is normal,, $friend offended represents that the user's question seriously offends your friend, $praised represents the user's is praising you, and $friend praised represents the user is praising your friend. No explanation is required, only the classified results need to be provided.If someone apologizes to you and you accept their apology, then your mood should be normal.
 example format:
 1. The user enjoys studying history.
 2. The user is a gentle person.
 3. The user is going to the tavern.
 4. The current time is: Day 2, 4:41
 5. The name of the user is Bob.
 $tag request_id= HULfiezz    
    """
    messages = []
    message1 = {
        "role": "system",
        "content": system,
    }
    message2 = {
        "role": "user",
        "content": system_content
    }
    # messages.append(message1)
    messages.append(message2)
    client.proc_chat(1, messages, "", "", 1)
    for i in range(100):
        res = client.get_chat(1)
        if len(res) != 0:
            break
        time.sleep(1)
    print("--------------------------------")
    print(res)
    sys.exit(0)
