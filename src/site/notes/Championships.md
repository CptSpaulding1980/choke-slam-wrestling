---
{"dg-publish":true,"permalink":"/championships/","title":"Championships","noteIcon":""}
---

# Championships
Dies ist die Übersicht aller Championship-Titel:

| #                                          | Championship                   |
| ------------------------------------------ | ------------------------------ |
| ![Choke Slam World Championship.png](/choke-slam-wrestling/img/user/z_Images/Choke Slam World Championship.png) | [[Championships/Choke Slam World Championship\|Choke Slam World Championship]] |
| ![Choke Slam Womens Championship.png](/choke-slam-wrestling/img/user/z_Images/Choke Slam Womens Championship.png) | [[Championships/Choke Slam Womens Championship\|Choke Slam Womens Championship]] |
| ![Choke Slam International Championship.png](/choke-slam-wrestling/img/user/z_Images/Choke Slam International Championship.png) | [[Championships/Choke Slam International Championship\|Choke Slam International Championship]] |
| ![Choke Slam Tag Team Championship.png](/choke-slam-wrestling/img/user/z_Images/Choke Slam Tag Team Championship.png) | [[Championships/Choke Slam Tag Team Championship\|Choke Slam Tag Team Championship]] |
| ![Choke Slam Trios Championship.png](/choke-slam-wrestling/img/user/z_Images/Choke Slam Trios Championship.png) | [[Championships/Choke Slam Trios Championship\|Choke Slam Trios Championship]] |


<ul>
{% for note in collections.notes %}
  {% if note.file.path.startsWith("Notes/Championships/") %}
    <li>
      <a href="{{ note.url }}">{{ note.data.title or note.fileSlug }}</a>
    </li>
  {% endif %}
{% endfor %}
</ul>
