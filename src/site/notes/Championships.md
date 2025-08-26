---
{"dg-publish":true,"permalink":"/championships/","title":"Championships","noteIcon":"🏆"}
---

# Championships
Dies ist die Übersicht aller Championship-Titel:

| # | Championship |
|---|--------------|
| <img src="/choke-slam-wrestling/img/user/z_Images/Choke Slam World Championship.png" width="120"> | [[Championships/Choke Slam World Championship]] |
| <img src="/choke-slam-wrestling/img/user/z_Images/Choke Slam Womens Championship.png" width="120"> | [[Championships/Choke Slam Womens Championship]] |
| <img src="/choke-slam-wrestling/img/user/z_Images/Choke Slam International Championship.png" width="120"> | [[Championships/Choke Slam International Championship]] |
| <img src="/choke-slam-wrestling/img/user/z_Images/Choke Slam Tag Team Championship.png" width="120"> | [[Championships/Choke Slam Tag Team Championship]] |
| <img src="/choke-slam-wrestling/img/user/z_Images/Choke Slam Trios Championship.png" width="120"> | [[Championships/Choke Slam Trios Championship]] |

<ul>
{% for note in collections.notes %}
  {% if note.file.path.startsWith("Notes/Championships/") %}
    <li>
      <a href="{{ note.url }}">{{ note.data.title or note.fileSlug }}</a>
    </li>
  {% endif %}
{% endfor %}
</ul>
