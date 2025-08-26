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
| <img src="/choke-slam-wrestling/img/user/z_Images/Choke Slam Trios Championship.png" width="120"> | [Choke Slam Trios Championship](Championships/Choke%20Slam%20Trios%20Championship.md) |



<table>
  <tr>
    <td><img src="/choke-slam-wrestling/img/user/z_Images/Choke Slam World Championship.png" width="120"></td>
    <td><a href="Championships/Choke%20Slam%20World%20Championship.md">Choke Slam World Championship</a></td>
  </tr>
  <tr>
    <td><img src="/choke-slam-wrestling/img/user/z_Images/Choke Slam Trios Championship.png" width="120"></td>
    <td><a href="Championships/Choke%20Slam%20Trios%20Championship.md">Choke Slam Trios Championship</a></td>
  </tr>
</table>



<ul>
{% for note in collections.notes %}
  {% if note.file.path.startsWith("Notes/Championships/") %}
    <li>
      <a href="{{ note.url }}">{{ note.data.title or note.fileSlug }}</a>
    </li>
  {% endif %}
{% endfor %}
</ul>
