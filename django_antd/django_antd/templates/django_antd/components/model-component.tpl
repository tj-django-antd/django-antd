/*
* Auto-generated Antd component using django models.
*/
import React from 'react';
import Form from 'antd/lib/form';
import { PropTypes } from 'prop-types';
import { WrappedFormUtils } from 'antd/lib/form/Form';
{% for import_name, path in extra_imports %}
{% spaceless %}import {{ import_name }} from '{{ path }}';{% endspaceless %}
{% endfor %}
/* eslint-disable react/jsx-closing-tag-location */

const { Item } = Form;
{% for sub_import, base in sub_imports %}
const { {{ sub_import }} } = {{ base }};
{% endfor %}
{% for component in components %}
{% if components|length > 1 %}export {% endif %}const {{ component.name }} = (props) => {
  const { getFieldDecorator } = props.form;
  const { itemProps, layout, onBlur, fieldOptions, inputProps } = props;
  const formItemLayout = layout === 'horizontal' ? {
    labelCol: {
      xs: { span: 24 },
      sm: { span: 8 },
    },
    wrapperCol: {
      xs: { span: 24 },
      sm: { span: 16 },
    },
  } : {};

  return (
    <Item
      {...itemProps}
      {...formItemLayout}
      label="{{ component.label }}"
      {% spaceless %}
      colon={false}
      {% if component.help_text %}help="{{ component.help_text }}"{% endif %}
      {% endspaceless %}
    >
      {getFieldDecorator('{{ component.field_name }}', {
        ...fieldOptions,
        {% spaceless %}
        {% if component.initial is not None %}initialValue: '{{ component.initial }}',{% endif%}
        rules: [{
          required: {% if component.required %}true{% else %}false{% endif %},
          {% if component.message is not None %}message: '{{ component.message }}'{% endif %},
        }],
        {% endspaceless %}
      })({{ component.input|safe }})}
    </Item>
  );
};

{{ component.name }}.defaultProps = {
  itemProps: {},
  handleChange: () => {},
  onBlur: () => {},
  layout: 'vertical',
  fieldOptions: {},
  inputProps: {},
};

{{ component.name }}.propTypes = {
  itemProps: PropTypes.shape({}),
  form: PropTypes.shape(WrappedFormUtils).isRequired,
  handleChange: PropTypes.func,
  onBlur: PropTypes.func,
  layout: PropTypes.oneOf(['vertical', 'horizontal', 'inline']),
  fieldOptions: PropTypes.shape({}),
  inputProps: PropTypes.shape({}),
};
{% endfor %}{% spaceless %}{% if components|length == 1 %}export default {{ components.0.name }};{% endif %}{% endspaceless %}
