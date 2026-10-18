from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class ContactMethodBlock(blocks.StructBlock):
    """Один способ связи контакта: свободный тип и значение."""

    type = blocks.CharBlock(label="Тип", max_length=120)
    value = blocks.CharBlock(label="Значение", max_length=500)

    class Meta:
        label = "Способ связи"
        icon = "link"


class ContactBlock(blocks.StructBlock):
    """Контакт: название, необязательные подназвание и фото, способы связи."""

    name = blocks.CharBlock(label="Название контакта", max_length=300)
    subtitle = blocks.CharBlock(label="Подназвание", required=False, max_length=300)
    photo = ImageChooserBlock(label="Фото (аватар)", required=False)
    methods = blocks.ListBlock(
        ContactMethodBlock(),
        label="Способы связи",
        required=False,
    )

    class Meta:
        label = "Контакт"
        icon = "user"


class ContactsSectionBlock(blocks.StructBlock):
    """Блок контактов: заголовок и список контактов."""

    title = blocks.CharBlock(label="Заголовок блока", max_length=300)
    contacts = blocks.ListBlock(ContactBlock(), label="Контакты")

    class Meta:
        label = "Блок контактов"
        icon = "group"
