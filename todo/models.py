from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# Объявляем класс менеджера, наследуясь от базового менеджера пользователей Django
class TelegramUserManager(BaseUserManager):

    # Метод для создания обычного пользователя
    def create_user(self, telegram_id, email=None, password=None):
        # Проверка: если telegram_id не передан, выкидываем ошибку
        if not telegram_id:
            raise ValueError('Пользователь должен иметь Telegram ID')

        # Создаем экземпляр модели (self.model ссылается на класс User ниже)
        user = self.model(
            id=telegram_id,
            # normalize_email приводит домен почты к нижнему регистру (User@GMail.com -> User@gmail.com)
            email=self.normalize_email(email) if email else None,
        )

        # Устанавливаем "невалидный" пароль. Это значит, что через обычную форму входа
        # (логин/пароль) войти нельзя, так как пароля в хэшированном виде просто нет.
        user.set_unusable_password()

        # Сохраняем пользователя в базу данных, используя текущую БД проекта
        user.save(using=self._db)
        return user

    # Метод для создания суперпользователя (админа) через терминал
    def create_superuser(self, id, email=None, password=None):
        # Сначала создаем обычного пользователя, используя метод выше
        user = self.create_user(id, email, password)

        # Даем права доступа к админ-панели
        user.is_staff = True
        # Даем неограниченные права (суперпользователь)
        user.is_superuser = True

        # Для админа пароль всё же нужен, чтобы войти в /admin/
        # Метод set_password хэширует (шифрует) введенную строку
        user.set_password(password)

        # Сохраняем обновленные флаги и пароль
        user.save(using=self._db)
        return user


# AbstractBaseUser дает основу пользователя, PermissionsMixin добавляет систему групп и прав
class User(AbstractBaseUser, PermissionsMixin):
    # Поле ID. Делаем его первичным ключом (primary_key), теперь Django не будет
    # создавать автоматическое поле id=1, 2, 3..., а будет использовать ваш Telegram ID.
    # BigIntegerField нужен, так как ID в Telegram — это очень длинные числа.
    id = models.BigIntegerField(primary_key=True, unique=True)

    # Поле для почты. blank=True позволяет оставлять пустым в формах,
    # null=True позволяет записывать NULL в базу данных.
    email = models.EmailField(blank=True, null=True)

    # Флаг: может ли пользователь вообще входить в систему
    is_active = models.BooleanField(default=True)

    # Флаг: имеет ли пользователь доступ к админ-панели
    is_staff = models.BooleanField(default=False)

    # Указываем, что для операций с базой (создание, поиск) нужно использовать наш менеджер
    objects = TelegramUserManager()

    # Указываем, какое поле является уникальным идентификатором (логином)
    USERNAME_FIELD = 'id'

    # Список полей, которые запросит терминал при выполнении команды createsuperuser
    # Так как id и password запрашиваются автоматически, здесь список пуст.
    REQUIRED_FIELDS = []

    # Как отображать объект пользователя в виде строки (например, в админке)
    def __str__(self):
        return f"TG: {self.id}"

# Ключевые моменты:
# USERNAME_FIELD = 'id': Это самое важное. Теперь везде, где Django ожидает "username", он будет требовать ваш
# Telegram ID.
# set_unusable_password(): Это защита. Поскольку мы не планируем заставлять обычных пользователей придумывать пароли
# (они ведь авторизуются через Telegram), мы помечаем это поле как «не для входа».
# BigIntegerField: Стандартный IntegerField в базах данных часто ограничен числом 2.147.483.647
# Telegram ID уже давно перевалили за эти значения, поэтому Big обязателен.