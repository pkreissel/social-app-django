import json
import six

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.utils.encoding import force_text
from django.utils.six import PY2, string_types
from encrypted_model_fields.fields import EncryptedTextField as JSONFieldBase
from social_core.utils import setting_name




class JSONField(JSONFieldBase):
    """Simple JSON field that stores python structures as JSON strings
    on database.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict)
        super(JSONField, self).__init__(*args, **kwargs)

    def from_db_value(self, value, *args, **kwargs):
        return self.to_python(value)

    def to_python(self, value):
        """
        Convert the input JSON value into python structures, raises
        django.core.exceptions.ValidationError if the data can't be converted.
        """
        if self.blank and not value:
            return {}
        value = value or '{}'
        if isinstance(value, (bytes, string_types[0])):
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            try:
                return json.loads(decrypt_str(value))
            except Exception as err:
                raise ValidationError(str(err))
        else:
            return super(EncryptedMixin, self).to_python(value)

    def validate(self, value, model_instance):
        """Check value is a valid JSON string, raise ValidationError on
        error."""
        if isinstance(value, six.string_types):
            super(JSONField, self).validate(value, model_instance)
            try:
                json.loads(value)
            except Exception as err:
                raise ValidationError(str(err))

    def get_prep_value(self, value, connection):
        value = super(EncryptedMixin, self).get_db_prep_save(value, connection)
        
        if value is None:
            return value
        try:
            value = json.dumps(value)
        except Exception as err:
            raise ValidationError(str(err))
        if PY2:
            return encrypt_str(unicode(value))
        # decode the encrypted value to a unicode string, else this breaks in pgsql
        return (encrypt_str(str(value))).decode('utf-8')

        """Convert value to JSON string before save"""
        try:
            return encrypt_str(unicode(json.dumps(value)))
        except Exception as err:
            raise ValidationError(str(err))

    def value_to_string(self, obj):
        """Return value from object converted to string properly"""
        return force_text(self.value_from_object(obj))

    def value_from_object(self, obj):
        """Return value dumped to string."""
        orig_val = super(JSONField, self).value_from_object(obj)
        return self.get_prep_value(orig_val)
