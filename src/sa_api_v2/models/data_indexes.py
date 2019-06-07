import operator
import ujson as json
from django.db import models
from .mixins import CloneableModelMixin
from functools import reduce


class DataIndex (CloneableModelMixin, models.Model):
    ATTR_TYPE_CHOICES = (
        ('string', 'String'),
    )

    dataset = models.ForeignKey('DataSet', on_delete=models.CASCADE, related_name='indexes')
    attr_name = models.CharField(max_length=100, db_index=True, verbose_name='Attribute name')
    attr_type = models.CharField(max_length=10, choices=ATTR_TYPE_CHOICES, default='string', verbose_name='Attribute type')

    class Meta:
        app_label = 'sa_api_v2'

    def __unicode__(self):
        return self.attr_name

    def index_things(self):
        things = self.dataset.things.all()
        for thing in things:
            IndexedValue.objects.sync(thing, self)

    def get_clone_save_kwargs(self):
        return {'reindex': False}

    def save(self, reindex=True, *args, **kwargs):
        ret = super(DataIndex, self).save(*args, **kwargs)
        if reindex:
            self.index_things()
        return ret


class IndexedValueManager (models.Manager):
    def sync(self, thing, index, data=None):
        if data is None:
            data = json.loads(thing.data)

        if index.attr_name in data:
            # If there is a value, index it.
            try:
                value = self.get(thing_id=thing.id, index_id=index.id)
            except IndexedValue.DoesNotExist:
                value = IndexedValue(thing_id=thing.id, index_id=index.id)

            new_indexable_value = str(data[index.attr_name])
            if value.value != new_indexable_value:
                value.value = new_indexable_value
                value.save()
        else:
            # If there's no value and there was one previously indexed, get
            # rid of it.
            self.filter(thing_id=thing.id, index_id=index.id).delete()


class IndexedValue (models.Model):
    index = models.ForeignKey('DataIndex', on_delete=models.CASCADE, related_name='values')
    thing = models.ForeignKey('SubmittedThing', on_delete=models.CASCADE, related_name='indexed_values')

    value = models.CharField(max_length=100, null=True, db_index=True)
    # TODO: This might be better as:
    #
    #   * string_value
    #   * number_value
    #   * boolean_value
    #   * datetime_value
    #
    #   So that we can use the appropriate comparisons for each (i.e., less
    #   than operates differently on strings than on numbers)

    objects = IndexedValueManager()

    class Meta:
        app_label = 'sa_api_v2'

    def get(self):
        data = json.loads(self.thing.data)
        try:
            return data[self.index.attr_name]
        except KeyError:
            raise KeyError('The thing %s has no data attribute %s' % (self.thing, self.index.attr_name))


class FilterByIndexMixin (object):
    """
    Mixin for model managers of indexed models.
    """
    def filter_by_index(self, key, *values):
        matches_any_values_clause = reduce(
            operator.or_,
            [models.Q(indexed_values__value=value) for value in values])
        return self\
            .filter(indexed_values__index__attr_name=key)\
            .filter(matches_any_values_clause)


