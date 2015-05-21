class CloneableModelMixin (object):
    """
    Mixin providing a clone method that copies all of a models instance's
    fields to a new instance of the model, allowing overrides.

    """
    def get_ignore_fields(self, ModelClass):
        fields = ModelClass._meta.fields
        pk_name = ModelClass._meta.pk.name

        ignore_field_names = set([pk_name])
        for fld in fields:
            if fld.name == pk_name:
                pk_fld = fld
                break
        else:
            raise Exception('Model %s somehow has no PK field' % (ModelClass,))

        if pk_fld.rel and pk_fld.rel.parent_link:
            parent_ignore_fields = self.get_ignore_fields(pk_fld.rel.to)
            ignore_field_names.update(parent_ignore_fields)

        return ignore_field_names

    def get_clone_save_kwargs(self):
        return {}

    def clone_related(self, onto):
        pass

    def clone(self, overrides=None, commit=True):
        """
        Create a duplicate of the model instance, replacing any properties
        specified as keyword arguments. This is a simple base implementation
        and may need to be extended for specific classes, since it is
        does not address related fields in any way.
        """
        fields = self._meta.fields
        ignore_field_names = self.get_ignore_fields(self.__class__)
        inst_kwargs = {}

        for fld in fields:
            if fld.name not in ignore_field_names:
                fld_value = getattr(self, fld.name)
                inst_kwargs[fld.name] = fld_value

        if overrides:
            inst_kwargs.update(overrides)

        new_inst = self.__class__(**inst_kwargs)
        new_inst._cloned_from = self

        if commit:
            save_kwargs = self.get_clone_save_kwargs()
            new_inst.save(**save_kwargs)

            # If commit is true, clone the related submissions. Otherwise,
            # you will have to call clone_related manually on the cloned
            # instance once it is saved.
            self.clone_related(onto=new_inst)

        return new_inst
