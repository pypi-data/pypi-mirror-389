from .exception import BeanPyException


class BeanDefinition:
    """
    bean的定义信息，用于描述bean的创建细节
    """

    def __init__(self, name: str, lazy: bool = False, single: bool = True):
        """
        构造器
        :param lazy: 是否选择懒加载，默认是False
        :param single: 是否是单例，默认是True
        """
        self.__name = name
        self.__lazy = lazy
        self.__single = single
        self.__instance = None

    def name(self):
        return self.__name

    def is_single(self):
        return self.__single

    def is_lazy(self):
        return self.__lazy

    def create_instance(self) -> object:
        """
        创建bean的实例对象
        :return:
        """
        # 如果不是单例bean，直接创建实例信息
        if not self.__single:
            return self._create_instance()
        # 单例bean缓存实例信息
        if not self.__instance:
            self.__instance = self._create_instance()
        return self.__instance

    def _create_instance(self) -> object:
        """
        创建类的实例方法，由子类实现
        :return: 对象的实例对象
        """
        pass


class ClsBeanDefinition(BeanDefinition):
    """
    基于类信息直接创建bean实例对象的bean定义信息
    """

    def __init__(self, name: str, cls: type, lazy: bool = False, single: bool = True):
        super().__init__(name, lazy, single)
        self.__cls = cls


    def _create_instance(self) -> object:
        """
        创建对象的实例
        :return: 对象的实例
        """
        return self.__cls()


class BeanDefinitionContainer:

    """
    bean定义的容器
    """

    def __init__(self):
        self.__bean_definitions: dict[str, BeanDefinition] = {}

    def put_definition(self, definition: BeanDefinition):
        """
        将定义的信息放入bean的容器
        :param bean_name: bean的名称
        :param definition: bean的定义信息
        """
        # 判断当前bean的名称是否存在
        if definition.name() in self.__bean_definitions:
            raise BeanPyException("bean name is already exists")
        self.__bean_definitions[definition.name()] = definition

    def replace_definition(self, bean_name: str, definition: BeanDefinition):
        """
        替换bean的定义信息
        :param bean_name: bean的名称
        :param definition: bean的定义信息
        """
        self.__bean_definitions[bean_name] = definition

    def delete_definition(self, bean_name: str):
        """
        删除bean的定义信息
        :param bean_name: bean的名称
        """
        del self.__bean_definitions[bean_name]

    def get_definition(self, bean_name: str) -> BeanDefinition | None:
        """
        获取bean的定义信息
        :param bean_name: bean的名称
        :return: bean的定义信息，若不存在返回None
        """
        if bean_name in self.__bean_definitions:
            return self.__bean_definitions[bean_name]
        return None

    def pop_single_no_lazy_definition(self) -> BeanDefinition | None:
        """
        弹出一个单例且非懒加载的bean的定义信息
        :return: bean的定义信息，若不存在返回None
        """
        for bean_name, definition in self.__bean_definitions.items():
            if definition.is_single() and not definition.is_lazy():
                del self.__bean_definitions[bean_name]
                return definition
        return None

    def pop_single_lazy_definition(self) -> BeanDefinition | None:
        """
        弹出一个单例且懒加载的bean的定义信息
        :return: bean的定义信息，若不存在返回None
        """
        for bean_name, definition in self.__bean_definitions.items():
            if definition.is_single() and definition.is_lazy():
                del self.__bean_definitions[bean_name]
                return definition
        return None

