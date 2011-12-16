def load_data(orm, fixture_name):

    def _get_model(model_identifier):
        return orm[model_identifier]

    from django.core.serializers import python
    old_deserializer = python._get_model
    python._get_model = _get_model

    # load the initial data
    from django.core.management import call_command
    call_command("loaddata", fixture_name)

    python._get_model = old_deserializer
