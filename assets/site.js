// Injects shared header/footer. Each page sets <body data-root="../.." (relative path to site root)>.
(function(){
  var root=document.body.dataset.root||".";
  var links=[["Timeline","timeline/"],["Eras","eras/"],["Regions","regions/"],["Movements","movements/"],["Artists","artists/"],["Works","works/"],["Themes","themes/"],["Techniques","techniques/"],["Learn","learn/"],["Search","search/"],["About","about/"]];
  var path=location.pathname;
  var nav=links.map(function(l){var cur=path.indexOf("/"+l[1].split("/")[0]+"/")>-1?' aria-current="page"':"";return '<a href="'+root+'/'+l[1]+'"'+cur+'>'+l[0]+'</a>'}).join("");
  var h=document.createElement("header");h.className="site";
  h.innerHTML='<div class="wrap"><a class="brand" href="'+root+'/">Art History</a><nav aria-label="Main">'+nav+'</nav></div>';
  document.body.prepend(h);
  var f=document.createElement("footer");f.className="site";
  f.innerHTML='<div class="wrap">Art History — from the Stone Age onward. Dates are approximate (BCE = before common era; "ya" = years ago). <a href="'+root+'/about/">Sources</a> · <a href="'+root+'/about/credits/">Image credits</a></div>';
  document.body.append(f);
})();
