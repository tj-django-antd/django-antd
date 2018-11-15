import os
from importlib import import_module

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management import BaseCommand
from django.forms import fields_for_model
from django.forms import models, fields
from django.template import loader
from django.utils.html import escape


class Command(BaseCommand):
    """
    Auto-generate model fields as react components using this CLI command script.

    Examples:
        $ python manage.py createmodelcomponent -m Offer
        # Use -r to replace existing model components.

    To restrict the number of fields on the model to a subset simply add
    an attribute to the model ANT_MODEL_FIELD_NAMES.

    Examples:
        class MyModel(models.Model)
            title = models.CharField(...)
            extra_field = models.CharField(...)

            ANT_MODEL_FIELD_NAMES = ['title'] # Only creates a title field.

    Model Attributes:
        ANT_MODEL_FIELD_NAMES (list): List of field names.
        ANT_MODEL_FIELD_LABELS (dict): Dictionary of field and labels.
    """
    app_name = 'content_library'
    help = 'Creates an ant design react component based on models fields.'
    exclude_fields = ['client', 'created_by', 'updated_by', 'created_at', 'updated_at']

    FIELD_MAP = {
        fields.IntegerField: ('number', 'InputNumber'),
        fields.DecimalField: ('decimal', 'InputNumber'),
        models.ModelChoiceField: ('select', 'Select'),
        models.ModelMultipleChoiceField: ('multi-select', 'Select'),
        fields.ChoiceField: ('select', 'Select'),
        fields.TypedChoiceField: ('select', 'Select'),
        fields.Select: ('select', 'Select'),
        fields.MultipleChoiceField: ('multi-select', 'Select'),
        fields.SelectMultiple: ('multi-select', 'Select'),
        fields.CharField: ('text', 'Input'),
        fields.BooleanField: ('checkbox', 'Checkbox'),
    }

    FIELD_IMPORT_MAP = {
        'Select': ('Select', 'antd/lib/select'),
        'Input': ('Input', 'antd/lib/input'),
        'InputNumber': ('InputNumber', 'antd/lib/input-number'),
        'Checkbox': ('Checkbox', 'antd/lib/checkbox'),
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '-m', '--model', nargs='+',
            type=str, required=True, help='Model name.',
        )
        parser.add_argument(
            '-r', '--replace-existing', action='store_true',
            help='Replace existing components with the same file name.',
        )
        parser.add_argument(
            '-o', '--output-path', type=str, required=False,
            default=settings.COMPONENT_OUTPUT_PATH,
            help='Output path for the model component.',
        )
        parser.add_argument(
            '-fname', '--file-name', type=str, required=False,
            help='Output file name.',
        )
        parser.add_argument(
            '-u', '--use-placeholder', action='store_true',
            help='Add default placeholder to fields.',
        )

    def _get_model(self, model_name):
        return getattr(import_module(f'{self.app_name}.models'), model_name, None)

    def _get_title_text(self, title):
        return escape(title)

    def _get_input(self, field, field_name, use_placeholder):
        field_type, field_input = self._get_field_type(field)

        field_tag_start = field_input
        field_tag_start += ' onBlur={onBlur} {...inputProps}'

        if field_type == 'decimal':
            field_tag_start += ' step={0.1}'
        elif field_type == 'multi-select':
            field_tag_start += ' mode="multiple"'

        if use_placeholder:
            field_tag_start += f' placeholder="Choose the {field_name.replace("_", " ").title()}"'

        if isinstance(field, models.ChoiceField):
            if isinstance(field, models.ModelChoiceField) or issubclass(field.__class__, models.ModelChoiceField):
                choices = [c for c in field.choices]
            else:
                choices = field.choices
            options = "\n".join([
                f'        <Option value="{value}">{self._get_title_text(title)}</Option>'
                for value, title in choices
            ])
            field_tag_end = f'      </{field_input}>'
            return f'<{field_tag_start}>\n{options}\n{field_tag_end}'

        return f'<{field_tag_start} />'

    def _get_field_type(self, field):
        if isinstance(field, fields.CharField) and not field.max_length:
            return ('textarea', 'TextArea')
        return self.FIELD_MAP.get(field.__class__, ('text', 'Input'))

    def get_field_context(self, field_name, field, model_name, use_placeholder):
        label = field.label
        initial = field.initial
        required = field.required
        error_msg = field.error_messages.get(
            'required', f'Please enter a valid value for: "{label}"',
        )
        help_text = field.help_text

        component_name = f'{field_name.replace("_", " ").title().replace(" ", "")}'
        if model_name.lower() not in component_name.lower():
            component_name = f'{model_name}{component_name}'

        return {
            'name': component_name,
            'field_name': field_name,
            'initial': initial,
            'help_text': help_text,
            'input': self._get_input(field, field_name, use_placeholder),
            'required': required,
            'message': error_msg,
            'label': label,
            'field': field,
        }

    def _get_form(self, form_class):
        return getattr(import_module(f'{self.app_name}.forms'), form_class, None)

    @staticmethod
    def _get_location(options, verbose_name, model_name):
        output_path = os.path.join(options['output_path'], verbose_name.replace(" ", "_").lower())
        file_name = options['file_name'] or f'{model_name}FormFields.js'

        return output_path, file_name

    def get_import(self, field):
        field_type, field_input = self._get_field_type(field)

        if field_input in self.FIELD_IMPORT_MAP.keys():
            return self.FIELD_IMPORT_MAP.get(field_input)

    def get_sub_imports(self, field):
        field_type, field_input = self._get_field_type(field)

        if field_type in ['select', 'multi-select']:
            return ('Option', 'Select')
        elif field_type in ['textarea']:
            return ('TextArea', 'Input')

    def _get_context(self, model, model_name, use_placeholder):
        fields = getattr(model, 'ANT_MODEL_FIELD_NAMES', None)
        labels = getattr(model, 'ANT_MODEL_FIELD_LABELS', None)
        components = []
        imports = set()
        sub_imports = set()

        model_fields = fields_for_model(
            model, fields=fields, exclude=self.exclude_fields, labels=labels,
        )

        for f_name, field in model_fields.items():
            components.append(self.get_field_context(f_name, field, model_name, use_placeholder))
            field_import = self.get_import(field)
            sub_import = self.get_sub_imports(field)
            if sub_import:
                sub_imports.add(sub_import)
            if field_import:
                imports.add(field_import)

        return {
            'components': components,
            'extra_imports': imports,
            'sub_imports': sub_imports,
        }

    def _render_js(self, fs, file_name, context):
        content = loader.render_to_string('django_antd/components/model-component.tpl', context=context)
        return fs.save(file_name, ContentFile(content))

    def handle(self, *args, **options):
        models = options['model']
        replace_existing = options['replace_existing']
        use_placeholder = options['use_placeholder']

        for model_name in models:
            model = self._get_model(model_name)
            verbose_name = model._meta.verbose_name
            output_path, file_name = self._get_location(options, verbose_name, model_name)

            if not os.path.exists(output_path):
                os.makedirs(output_path, exist_ok=True)

            fs = FileSystemStorage(location=output_path)
            if fs.exists(file_name):
                if replace_existing:
                    fs.delete(file_name)
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'File "{file_name}" already exists a new component file will be created.',
                        ),
                    )

            output = self._render_js(fs, file_name, self._get_context(model, model_name, use_placeholder))
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created component file "{output}": \n{fs.path(output)}',
                ),
            )
