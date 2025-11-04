from .definition import BeanDefinitionContainer


class BeanFactoryPostProcessor:

    """
    bean工厂的后处理器
    """

    def handle(self, container: BeanDefinitionContainer):
        """
        动态注册bean的定义信息或者删除bean的定义信息
        :param container: 容器对象
        :return: None
        """
        pass


class BeanPostProcessor:

    """
    bean的后处理器
    """

    def post_before_init(self, bean: object) -> None:
        """bean初始化之前执行"""
        pass

    def post_after_init(self, bean: object) -> object:
        """bean初始化之后执行"""
        pass