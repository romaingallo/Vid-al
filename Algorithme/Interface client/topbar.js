const topbar = document.getElementById('topbar');
if (!topbar) throw new Error('Element #topbar introuvable');

topbar.innerHTML = `
<a class="maintitle" href="/">Vidéal</a>
<input type="text" class="searchbar" id="searchbar" name="searchbar" placeholder="Recherche"/>
<a class="notif" href="/"><img src="/images/bell.svg" class="notiflogo" alt="Notifications"></a>
<a class="user" href="/login"><img src="/pfp" class="userlogo" alt="Paramètres"></a>
<hr/>
`