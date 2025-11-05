---
toc_max_heading_level: 2
---

import Link from '@docusaurus/Link';
import { GoFileSymlinkFile } from "react-icons/go";

# {{ name }}

{% if comment %}
{{ comment }}

{% endif %}
---

{% if submodules | length > 0 %}
{% for submodule in submodules %}
## {% raw %}<><code class="docs-submodule">submodule</code></>{% endraw %} {{ submodule.name }} <Link to="{{ submodule.link }}"><GoFileSymlinkFile size={25} /></Link>

{% if submodule.comment %}

{{ submodule.comment }}
{% endif %}

---
{% endfor %}
{% endif %}
{% if attributes | length > 0 %}
{% for attribute in attributes %}
{% if not attribute.name.startswith('_') %}
## {% raw %}<><code class="docs-attr">attr</code></>{% endraw %} {{ attribute.name }}

{% if attribute.type %}
_Type:_ {{ attribute.type }}

{% endif %}

{% if attribute.comment %}

{{ attribute.comment }}
{% endif %}

---
{% endif %}
{% endfor %}
{% endif %}
{% if functions | length > 0 %}
{% for function in functions %}
{% if not function.name.startswith('_') %}
## {% raw %}<><code class="docs-func">func</code></>{% endraw %} {{ function.name }}

_Call Type: {{ function.label }}_

{% if function.comment %}

{{ function.comment}}
{% endif %}
{% if function.args | length > 0%}

### Arguments
{% for arg in function.args %}
{% if not arg.name.startswith('_') %}
**{% raw %}<><code class="docs-arg">arg</code></>{% endraw %}&nbsp;&nbsp;{{ arg.name }}**{% if arg.type %}&nbsp;&nbsp;({{ arg.type }}){% endif %}
{% if arg.comment %} <text>&#8212;</text> {{ arg.comment }}{% endif %}


{% endif %}
{% endfor %}
{% endif %}
{% if function.ret %}

### Returns

{% if function.ret.type %}{{ function.ret.type }}{% endif %}
{% if function.ret.comment %} <text>&#8212;</text> {{ function.ret.comment }}{% endif %}

{% endif %}
{% if function.source %}
<details>
<summary>View Source</summary>
```python
{{ function.source }}
```
</details>
{% endif %}

---
{% endif %}
{% endfor %}
{% endif %}
{% if classes | length > 0%}
{% for class in classes %}
{% if not class.name.startswith('_') %}
## {% raw %}<><code class="docs-class">class</code></>{% endraw %} {{ class.name }}

{% if class.inheritance %}
*Inherits from: {{ class.inheritance }}*
{% endif %}
{% if class.comment %}

{{ class.comment }}
{% endif %}
{% if class.attributes | length > 0%}
#### Attributes
{% for attr in class.attributes %}
{% if not attr.name.startswith('_') %}
**{% raw %}<><code class="docs-attr">attr</code></>{% endraw %}&nbsp;&nbsp;{{ attr.name }}**{% if attr.type %}&nbsp;&nbsp;({{ attr.type }}){% endif %}
{% if attr.comment %} <text>&#8212;</text> {{ attr.comment }}{% endif %}


{% endif %}
{% endfor %}
{% endif %}

{% if class.functions %}

{% for function in class.functions %}
{% if not function.name.startswith('_') %}
### {% raw %}<><code class="docs-method">method</code></>{% endraw %} {{ function.name }}

_Call Type: {{ function.label }}_

{% if function.inheritance %}
*Inherited from {{ function.inheritance }}*
{% endif %}
{% if function.comment %}

{{ function.comment }}
{% endif %}
{% if function.args | length > 0%}

#### Arguments
{% for arg in function.args %}
{% if not arg.name.startswith('_') %}
**{% raw %}<><code class="docs-arg">arg</code></>{% endraw %}&nbsp;&nbsp;{{ arg.name }}**{% if arg.type %}&nbsp;&nbsp;({{ arg.type }}){% endif %}
{% if arg.comment %} <text>&#8212;</text> {{ arg.comment }}{% endif %}


{% endif %}
{% endfor %}
{% endif %}
{% if function.ret %}

#### Returns

{% if function.ret.type %}{{ function.ret.type }}{% endif %}
{% if function.ret.comment %} <text>&#8212;</text> {{ function.ret.comment }}{% endif %}

{% endif %}
{% endif %}
{% endfor %}
{% endif %}

{% if class.source %}
<details>
<summary>View Source</summary>
```python
{{ class.source }}
```
</details>
{% endif %}


---
{% endif %}
{% endfor %}
{% endif %}
