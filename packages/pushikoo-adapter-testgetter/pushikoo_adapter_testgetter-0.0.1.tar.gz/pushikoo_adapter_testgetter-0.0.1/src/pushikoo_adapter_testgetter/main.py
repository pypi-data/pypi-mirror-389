import time

from pushikoo_interface import Detail, Getter, GetterClassConfig, GetterInstanceConfig

from pushikoo_adapter_testgetter.api import MockAPI
from pushikoo_adapter_testgetter.config import ClassConfig, InstanceConfig


class TestGetter(
    Getter[
        ClassConfig,  # If you don't have any configuration, you can just use GetterClassConfig
        InstanceConfig,  # If you don't have any configuration, you can just use GetterInstanceConfig
    ]
):
    # This is your adapter.
    # You should not write any logic to handle errors to avoid a function failing to return.
    # Framework will do it.

    def __init__(self) -> None:
        self.api = MockAPI(
            token=self.instance_config.token,
            userid=self.instance_config.userid,
            delay=self.config.mockapi_delay,
            # You can use self.ctx to access to framework context.
            # Framework provides proxies via ctx
            proxies=self.ctx.get_proxies(),  # {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        )

    def timeline(self) -> list[str]:
        # Return list of message id.
        return self.api.get_list(self.config.get_list_option.count)

    def detail(self, id_: str) -> Detail:
        # Return detail of message.
        post = self.api.get_post(id_)

        return Detail(
            ts=post["timestamp"],
            content=post["content"],
            title=post.get("title"),
            author_id=post.get("userid"),
            author_name=post.get("username"),
            url=post.get("url", []),
            image=post.get("picture", []),
            extra_detail=[post["ip_location"], post["author_statement"]],
        )

    def details(self, ids: list[str]) -> Detail:
        """Get detail of specific ids as a single Detail.

        Different types of messages have different semantic aggregation granularity
        - Some messages (such as long-content game posts) can only be processed separately;
        - Some messages, such as short, frequent posts, can be combined into a single logical message.
        Therefore, adapter developers can implement this method,
        if framework option "getter_instance.prefer_details" is True, this method will be called preferentially.
        This method is not enforced, and if it is not implemented, it will fallback to `detail`.
        """

        posts = [self.api.get_post(i) for i in ids]

        content = "\n".join(p["content"] for p in posts)
        ts = int(time.time())
        title = "Aggregated Messages"
        author_id = ", ".join(p.get("userid", "") for p in posts if p.get("userid"))
        author_name = ", ".join(
            p.get("username", "") for p in posts if p.get("username")
        )
        url = [u for p in posts for u in p.get("url", [])]
        image = [img for p in posts for img in p.get("picture", [])]

        return Detail(
            ts=ts,
            content=content,
            title=title,
            author_id=author_id,
            author_name=author_name,
            url=url,
            image=image,
            extra_detail=[],
        )
