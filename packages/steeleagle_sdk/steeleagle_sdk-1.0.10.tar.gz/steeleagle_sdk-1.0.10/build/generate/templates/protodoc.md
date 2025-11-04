---
toc_max_heading_level: 3
---

import Link from '@docusaurus/Link';

# {{ name }} 
---
{% if services | length > 0%}
{% for srv in services %}
## {% raw %}<><code class="docs-class">service</code></>{% endraw %} {{ srv.name }}

{% if srv.comment %}

{{ srv.comment }}
{% endif %}

{% for rpc in srv.rpc %}
### {% raw %}<><code class="docs-method">rpc</code></>{% endraw %} {{ rpc.name }}

{% if rpc.comment %}

{{ rpc.comment }}
{% endif %}

#### Accepts
{{ rpc.input }}

#### Returns
{{ rpc.output }}

{% endfor %}

---
{% endfor %}
{% endif %}

{% if types | length > 0 %}
{% for type in types %}
{% if type.is_enum %}
## {% raw %}<><code class="docs-func">enum</code></>{% endraw %} {{ type.name }}
{% else %}
## {% raw %}<><code class="docs-func">message</code></>{% endraw %} {{ type.name }}
{% endif %}

{% if type.comment %}

{{ type.comment}}
{% endif %}
{% if type.attributes | length > 0%}

#### Fields
{% for attr in type.attributes %}
**{% raw %}<><code class="docs-attr">field</code></>{% endraw %}&nbsp;&nbsp;{{ attr.name }}**{% if attr.type %}&nbsp;&nbsp;({{ attr.type }}){% endif %}
{% if attr.comment %} <text>&#8212;</text> {{ attr.comment }}{% endif %}


{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}
