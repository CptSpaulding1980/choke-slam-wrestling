---
{"title":"Championships","dg-publish":true,"permalink":"/championships/","dgPassFrontmatter":true,"noteIcon":""}
---


# Championships Übersicht

Dies ist die Übersicht aller Championship-Notes.

<ul>
{% for note in collections.notes %}
  {% if note.file.path.startsWith("Notes/Championships/") %}
    <li>
      <a href="{{ note.url }}">{{ note.data.title or note.fileSlug }}</a>
    </li>
  {% endif %}
{% endfor %}
</ul>
