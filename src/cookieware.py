class CookieManager:
    def __init__(self):
        self.cookies = []
        self.drop_cookies = []

    def set_cookie(self, *args, **kwargs):
        self.cookies.append((args, kwargs))

    def delete_cookie(self, name):
        self.drop_cookies.append(name)

    def manage_cookies(self, response):
        for cookie in self.drop_cookies:
            response.delete_cookie(cookie)
        for args, kwargs in self.cookies:
            response.set_cookie(*args, **kwargs)


class CookieMiddleware:
    def resolve(self, next, root, info, **args):
        info.context["cook"] = CookieManager()
        response = next(root, info, **args)
        
        print(info.context["cook"].cookies)
        info.context["cook"].manage_cookies(response)
        return response
