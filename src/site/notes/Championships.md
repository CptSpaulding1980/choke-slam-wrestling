---
{"title":"Championships","dg-publish":true,"permalink":"/championships/","dgPassFrontmatter":true,"noteIcon":""}
---

# Championships
Dies ist die Übersicht aller Championship-Titel:

- [[Championships/Choke Slam World Championship\|Choke Slam World Championship]]
- [[Championships/Choke Slam Womens Championship\|Choke Slam Womens Championship]]
- [[Championships/Choke Slam International Championship\|Choke Slam International Championship]]
- [[Championships/Choke Slam Tag Team Championship\|Choke Slam Tag Team Championship]]
- [[Championships/Choke Slam Trios Championship\|Choke Slam Trios Championship]]

<ul>
{% for note in collections.notes %}
  {% if note.file.path.startsWith("Notes/Championships/") %}
    <li>
      <a href="{{ note.url }}">{{ note.data.title or note.fileSlug }}</a>
    </li>
  {% endif %}
{% endfor %}
</ul>
