from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Achievement(models.Model):
    """
    Represents an achievement a cat can earn.
    """
    name = models.CharField(
        max_length=64,
        verbose_name=_("Achievement Name"),
        help_text=_("Name of the achievement.  Keep it concise and descriptive.")
    )

    class Meta:
        verbose_name = _("Achievement")
        verbose_name_plural = _("Achievements")
        ordering = ['name'] # Alphabetical order, good for display

    def __str__(self):
        return self.name


class Cat(models.Model):
    """
    Represents a cat.
    """
    name = models.CharField(
        max_length=16,
        verbose_name=_("Cat Name"),
        help_text=_("The cat's name.")
    )
    color = models.CharField(
        max_length=16,
        verbose_name=_("Color"),
        help_text=_("The cat's color.")
    )
    birth_year = models.IntegerField(
        verbose_name=_("Birth Year"),
        help_text=_("The year the cat was born.")
    )
    owner = models.ForeignKey(
        User,
        related_name='cats',
        on_delete=models.CASCADE,
        verbose_name=_("Owner"),
        help_text=_("The user who owns this cat.")
    )
    achievements = models.ManyToManyField(
        Achievement,
        through='AchievementCat',
        verbose_name=_("Achievements"),
        help_text=_("Achievements earned by this cat.")
    )
    image = models.ImageField(
        upload_to='cats/images/',
        null=True,
        blank=True, # Use blank=True instead of default=None for ImageFields
        verbose_name=_("Image"),
        help_text=_("An image of the cat.  Recommended size: 200x200 pixels."),
        # Add validators if you need specific image dimensions or file types
    )

    class Meta:
        verbose_name = _("Cat")
        verbose_name_plural = _("Cats")
        ordering = ['name'] # Alphabetical order
        constraints = [
            models.CheckConstraint(
                check=models.Q(birth_year__gt=1900, birth_year__lt=2100), # Example constraint
                name='birth_year_reasonable'
            )
        ]

    def __str__(self):
        return self.name

    def get_age(self): # Example method.  Use this in templates
        """
        Calculates the cat's age based on the current year.
        """
        import datetime
        current_year = datetime.datetime.now().year
        return current_year - self.birth_year


class AchievementCat(models.Model):
    """
    A through model representing the relationship between achievements and cats.
    """
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        verbose_name=_("Achievement")
    )
    cat = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE,
        verbose_name=_("Cat")
    )

    class Meta:
        verbose_name = _("Achievement Cat")
        verbose_name_plural = _("Achievement Cats")
        unique_together = ['achievement', 'cat']  # Prevent duplicate entries

    def __str__(self):
        return f'{self.achievement} - {self.cat}'