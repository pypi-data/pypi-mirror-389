import functools

def inject(bean_name: str):
    """
    用于依赖注入的装饰器
    :param bean_name: bean 的名称
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # 在函数对象上打标记（可用于扫描）
        wrapper.__inject__ = True
        wrapper.__bean_name__ = bean_name
        return wrapper
    return decorator


def post_construct(func):
    """
    当bean的依赖注入完成之后执行该方法
    :param func:
    :return:
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__post_construct__ = True
    return wrapper

def pre_destroy(func):
    """
    当bean销毁之前执行该方法
    :param func:
    :return:
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__pre_destroy__ = True
    return wrapper