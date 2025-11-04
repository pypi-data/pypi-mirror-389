from beanpy.factory import BeanFactory
from beanpy.wrapper import inject


class UserService:
    pass

class OrderService:

    def __init__(self):
        self.user_service: UserService | None = None

    @inject("userService")
    def set_user_service(self, user_service):
        self.user_service = user_service


factory = BeanFactory()
factory.register_bean(UserService, "userService")
factory.register_bean(OrderService, "orderService")

factory.run()
order_service = factory.get_bean("orderService")
print(order_service.user_service)