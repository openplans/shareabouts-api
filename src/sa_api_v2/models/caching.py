from django.core.exceptions import ObjectDoesNotExist
from importlib import import_module


class CacheClearingModel (object):
    @classmethod
    def resolve_attr(cls, attr):
        if hasattr(cls, attr):
            value = getattr(cls, attr)
            if isinstance(value, str):
                module_name, class_name = value.rsplit('.', 1)
                value = getattr(import_module(module_name), class_name)
            return value
        else:
            return None

    def get_previous_version(self):
        model = self.resolve_attr('previous_version')
        if model:
            return model.objects.get(pk=self.pk)

    def get_next_version(self):
        model = self.resolve_attr('next_version')
        if model:
            return model.objects.get(pk=self.pk)

    def clear_instance_cache(self):
        if hasattr(self, 'cache'):
            self.cache.clear_instance(self)

        try:
            previous_version = self.get_previous_version()
            if previous_version:
                previous_version.cache.clear_instance(previous_version)
        except ObjectDoesNotExist:
            pass

        try:
            next_version = self.get_next_version()
            if next_version:
                next_version.cache.clear_instance(next_version)
        except ObjectDoesNotExist:
            pass

    def save(self, clear_cache=True, *args, **kwargs):
        result = super(CacheClearingModel, self).save(*args, **kwargs)
        if clear_cache:
            self.clear_instance_cache()
        return result

    def delete(self, clear_cache=True, *args, **kwargs):
        if clear_cache:
            self.clear_instance_cache()
        return super(CacheClearingModel, self).delete(*args, **kwargs)
