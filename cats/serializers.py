import base64
import datetime as dt
import logging

from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
import webcolors # type: ignore

from .models import Achievement, AchievementCat, Cat

logger = logging.getLogger(__name__)


class Hex2NameColor(serializers.Field):
    """
    Пользовательское поле сериализатора для преобразования шестнадцатеричного цветового кода в его название.
    """

    def to_representation(self, value):
        """
        Преобразует внутреннее значение (название цвета) в представление (название цвета).
        """
        return value

    def to_internal_value(self, data):
        """
        Преобразует входящие данные (шестнадцатеричный цветовой код) во внутреннее значение (название цвета).
        """
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError(
                _('Неверный цветовой код или название для этого цвета не найдено.')
            )
        return data


class AchievementSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели достижений.
    """
    achievement_name = serializers.CharField(source='name',
                                            label=_("Achievement Name"),
                                            help_text=_("Название достижения."))

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')
        read_only_fields = ('id',)  # Достижения, как правило, должны создаваться / обновляться с помощью Cat serializer


class Base64ImageField(serializers.ImageField):
    """
    Пользовательское поле сериализатора для обработки изображений в кодировке base64.
    """

    def to_internal_value(self, data):
        """
        Преобразует данные изображения в кодировке base64 в файл содержимого.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
            except Exception as e:
                logger.error(f"Error decoding base64 image: {e}")
                raise serializers.ValidationError(_("Invalid base64 image data."))
        return super().to_internal_value(data)


class CatSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Cat.
    """
    achievements = AchievementSerializer(
        many=True,
        required=False,
        help_text=_("Список достижений для кошки (необязательно).")
    )
    color = Hex2NameColor(
        help_text=_("Укажите цвет кошки в шестнадцатеричном формате (например, #FFFFFF) или по имени.")
    )
    age = serializers.SerializerMethodField(
        read_only=True,
        help_text=_("Возраст кошки рассчитывается исходя из года рождения.")
    )
    image = Base64ImageField(
        required=False,
        allow_null=True,
        help_text=_("Изображение кошки в кодировке Base64 (необязательно).")
    )

    class Meta:
        model = Cat
        fields = (
            'id', 'name', 'color', 'birth_year', 'achievements', 'owner', 'age',
            'image'
        )
        read_only_fields = ('owner', 'age', 'id')  # owner set on the backend
        extra_kwargs = {
            'name': {'help_text': _("Кошачье имя.")},
            'birth_year': {'help_text': _("В тот год, когда родилась кошка.")},
        }

    def get_age(self, obj):
        """
        Вычисляет возраст кошки.
        """
        return dt.datetime.now().year - obj.birth_year

    def create(self, validated_data):
        """
        Создает новый экземпляр cat. Обрабатывает создание достижения, если оно предусмотрено.
        """
        achievements = validated_data.pop('achievements', [])
        cat = Cat.objects.create(**validated_data)

        for achievement_data in achievements:
            achievement, _ = Achievement.objects.get_or_create(**achievement_data)
            AchievementCat.objects.create(achievement=achievement, cat=cat)

        return cat

    def update(self, instance, validated_data):
        """
        Обновляет существующий экземпляр cat. Обрабатывает обновления достижений.
        """
        achievements_data = validated_data.pop('achievements', None)

        instance.name = validated_data.get('name', instance.name)
        instance.color = validated_data.get('color', instance.color)
        instance.birth_year = validated_data.get('birth_year', instance.birth_year)
        instance.image = validated_data.get('image', instance.image)
        instance.save() # Сохраните здесь, перед манипуляциями с m2m

        if achievements_data is not None:
            # Очистите существующие достижения и добавьте новые
            instance.achievements.clear() #  Эффективно устранять существующие взаимосвязи
            for achievement_data in achievements_data:
                achievement, _ = Achievement.objects.get_or_create(**achievement_data)
                AchievementCat.objects.create(achievement=achievement, cat=instance)

        return instance