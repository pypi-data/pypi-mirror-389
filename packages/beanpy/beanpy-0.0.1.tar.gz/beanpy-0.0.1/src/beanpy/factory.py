from .processor import BeanFactoryPostProcessor, BeanPostProcessor
from .exception import BeanPyException
from .definition import BeanDefinitionContainer, ClsBeanDefinition
from threading import Lock
import inspect

class BeanFactory:

    """bean的创建工厂"""

    def __init__(self):
        # 成品的bean的单例对象池，key是bean的名称，value是bean的实例对象
        self.__single_objects: dict[str, object] = {}
        # 早期创建的bean的对象，还没有完成依赖注入
        self.__early_single_objects: dict[str, object] = {}
        # bean的定义信息，key是bean的名称，value是bean的创建信息
        self.__bean_definitions = BeanDefinitionContainer()
        # 锁对象
        self.__lock = Lock()
        # 判断容器是否已经启动了
        self.__started = False
        # bean工厂的后处理器
        self.__bean_factory_post_processors: list[BeanFactoryPostProcessor] = []
        # bean的后处理器
        self.__bean_post_processors: list[BeanPostProcessor] = []

    def register_bean_factory_post_processor(self, processor: BeanFactoryPostProcessor):
        """
        注册bean工厂的后处理器
        :param processor: 后处理器对象
        :return: None
        """
        self.__bean_factory_post_processors.append(processor)

    def register_bean_post_processor(self, processor: BeanPostProcessor):
        """
        注册bean的后处理器
        :param processor: 后处理器对象
        :return: None
        """
        self.__bean_post_processors.append(processor)

    def register_bean(self, cls: type, name: str, lazy: bool = False, single: bool = True):
        """
        注册bean的定义信息
        :param cls: 类对象
        :param name: bean的名称，不允许重复
        :param lazy: 是否选择懒加载
        :param single: 是否是单例bean
        :return: None
        """
        # 创建bean的定义信息
        definition = ClsBeanDefinition(name, cls, lazy, single)
        # 注册bean
        self.__bean_definitions.put_definition(definition)

    def get_bean(self, name: str):
        """
        根据bean的名称获取bean
        :param name: bean的名称
        :return: bean对象
        """
        with self.__lock:
            # 如果bean没有初始化完毕抛出异常
            if not self.__started:
                raise BeanPyException("bean factory is not started")
            bean, single = self.__get_bean(name)
            # 处理单例bean的情况
            if single:
                if self.__early_single_objects:
                    # 执行依赖注入
                    self.__inject_dependencies()
                return bean
            # 对非单例bean进行依赖注入
            self.__do_inject(bean)
            # 执行处理器
            for processor in self.__bean_post_processors:
                processor.post_before_init(bean)
            # 执行初始化方法
            self.__do_post_construct(bean)
            # 执行bean的后置处理器
            for processor in self.__bean_post_processors:
                processor.post_after_init(bean)
            return bean


    def run(self):
        """
        启动容器
        :return:
        """
        self.__init_container()

    def __init_container(self):
        """
        初始化bean的容器
        :return:
        """
        with self.__lock:
            # 执行bean定义信息的后处理器
            for factory_processor in self.__bean_factory_post_processors:
                factory_processor.handle(self.__bean_definitions)
            # 创建bean对象
            self.__create_instance()
            # 进行依赖注入
            self.__inject_dependencies()
            # 启动容器
            self.__started = True

    def __create_instance(self):
        """
        遍历所有的bean的定义信息，创建bean的对象
        :return:
        """
        definition = self.__bean_definitions.pop_single_no_lazy_definition()
        while definition:
            # 创建bean的实例对象
            instance = definition.create_instance()
            # 存入二级缓存
            self.__early_single_objects[definition.name()] = instance
            # 获取下一个bean的定义信息
            definition = self.__bean_definitions.pop_single_no_lazy_definition()


    def __inject_dependencies(self):
        """
        遍历所有的bean的定义信息，进行依赖注入
        :return:
        """
        while self.__early_single_objects:
            # 从二级缓存中获取第一个元素
            name = next(iter(self.__early_single_objects))
            instance = self.__early_single_objects[name]
            # 对对象进行依赖注入
            self.__do_inject(instance)
            # 对象依赖注入结束之后存入一级缓存，并且从二级缓存删除
            self.__single_objects[name] = instance
            del self.__early_single_objects[name]
            # 执行bean的前置处理器
            for processor in self.__bean_post_processors:
                processor.post_before_init(instance)
            # 执行bean的初始化方法
            self.__do_post_construct(instance)
            # 执行bean的后置处理器
            for processor in self.__bean_post_processors:
                processor.post_after_init(instance)


    def __do_post_construct(self, instance: object):
        """执行bean的初始化方法"""
        cls = instance.__class__
        for _, method in inspect.getmembers(cls, inspect.isfunction):
            if getattr(method, "__post_construct__", False):
                method(instance)

    def __do_inject(self, instance):
        """
        对对象进行依赖注入
        :param instance: 对象
        :return:
        """
        # 获取所有被DI装饰器标注的方法
        method_infos = self.__find_inject_methods(instance)
        # 遍历所有的依赖注入项
        for method, bean_name in method_infos:
            # 获取bean的实例
            bean_obj, _ = self.__get_bean(bean_name)
            if not bean_obj:
                raise BeanPyException("bean is not exists")
            # 调用该方法进行依赖注入
            method(instance, bean_obj)


    def __find_inject_methods(self, obj):
        """
        查找类实例或类定义中所有被 @inject 装饰的方法
        """
        cls = obj if inspect.isclass(obj) else obj.__class__
        result = []
        for _, method in inspect.getmembers(cls, inspect.isfunction):
            if getattr(method, "__inject__", False):
                bean_name = getattr(method, "__bean_name__", None)
                result.append((method, bean_name))
        return result

    def __get_bean(self, name: str) -> (object, bool):
        """
        获取bean的实例
        :param name: bean的名称
        :return: bean的实例，第二个返回值为是否是单例，为True表示单例
        """
        # 从一级缓存中寻找bean
        if name in self.__single_objects:
            return self.__single_objects[name], True
        # 从二级缓存中寻找bean
        if name in self.__early_single_objects:
            return self.__early_single_objects[name], True
        # 获取bean的定义信息
        # 首先尝试获取懒加载的bean
        definition = self.__bean_definitions.pop_single_lazy_definition()
        if definition:
            # 创建bean的实例信息
            instance = definition.create_instance()
            # 存入二级缓存
            self.__early_single_objects[definition.name()] = instance
            return instance, True
        # 如果不存在获取非单例bean
        definition = self.__bean_definitions.get_definition(name)
        if definition:
            instance = definition.create_instance()
            return instance, False
        raise BeanPyException("bean is not exists")


    def stop(self):
        """
        停止容器
        :return:
        """
        with self.__lock:
            for bean in self.__single_objects.values():
                cls = bean.__class__
                for _, method in inspect.getmembers(cls, inspect.isfunction):
                    if getattr(method, "__pre_destroy__", False):
                        method(bean)
            self.__single_objects.clear()
            self.__started = False