from django import template
from myapp.models import Media  # Import your Medias model

register = template.Library()

@register.simple_tag

def display_image_by_name(image_name):
    try:
        image_data = Media.objects.get(image_name=image_name)
        return image_data.image.url
    except Media.DoesNotExist:
        return "no image"
