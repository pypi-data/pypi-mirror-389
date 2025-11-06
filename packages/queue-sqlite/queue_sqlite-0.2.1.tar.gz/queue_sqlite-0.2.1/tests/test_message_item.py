from queue_sqlite.model import MessageItem
import json


class TestMessageItem:
    messageItem = MessageItem(content={"num": 1}, destination="test")

    @classmethod
    def test_to_dict(cls):
        print(cls.messageItem.to_dict())

    @classmethod
    def test_to_json(cls):
        print(cls.messageItem.to_json())

    @classmethod
    def test_from_dict(cls):
        messageItem = MessageItem.from_dict(cls.messageItem.to_dict())
        data = {
            "id": "ddb66277-503c-4921-8e7f-5091eace49e3",
            "type": "task",
            "status": 2,
            "content": '{"num": 1}',
            "createtime": "2025-09-12T18:41:08.221531",
            "updatetime": "2025-09-12T18:41:08.221531",
            "result": '"{\\"message\\": \\"\\\\u6d4b\\\\u8bd5\\\\u6210\\\\u529f\\"}"',
            "priority": 1,
            "source": "client",
            "destination": "test",
            "retry_count": 0,
            "expire_time": "null",
            "tags": "null",
            "metadata": "{}",
        }
        print(messageItem.to_dict())
        print(MessageItem.from_dict(data).to_dict())

    @classmethod
    def test_from_json(cls):
        json_str = """
        {
            "content": {
                "num": 1
            },
            "createtime": "2025-09-12T16:42:50.663248",
            "destination": "test",
            "expire_time": null,
            "id": "b83c3d72-0b06-4c34-ab4f-32d696aa3875",
            "metadata": {},
            "priority": 1,
            "result": "{\"message\": \"\\u6d4b\\u8bd5\\u6210\\u529f\"}",
            "retry_count": 0,
            "source": "client",
            "status": 2,
            "tags": null,
            "type": "task",
            "updatetime": "2025-09-12T16:42:50.663248"
        }
        """
        messageItem = MessageItem.from_dict(json.loads(json_str))
        print(messageItem.to_json())
