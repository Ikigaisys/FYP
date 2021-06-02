/* (c) 2017 PeerName | https://peername.com */
chrome.webRequest.onBeforeRequest.addListener(function(details) {
	var parser = document.createElement('a');
	parser.href = details.url;
	var parts = parser.hostname.split('.');
	var tld = parts[parts.length-1];
	if(["iki"].indexOf(tld) !== -1) {
		var name = parts[parts.length-2];
		var domain = parser.hostname;
		var access = (parser.protocol == "https:" ? "HTTPS" : "PROXY");
		var port = (parser.protocol == "https:" ? "443" : "80");

		if(sessionStorage.getItem(domain) == undefined) {
			var xhr = new XMLHttpRequest();
			var url = "http://localhost:5000/get?domain="+encodeURIComponent(name + ".iki");
			xhr.onreadystatechange = function() {
				if(xhr.readyState == 4 && xhr.status == 200) {
					var xmlDoc = xhr.responseXML;
					if(xmlDoc.getElementsByTagName("ip").length > 0) {
						var ip = xmlDoc.getElementsByTagName("ip")[0].childNodes[0].nodeValue;
						var config = {
							mode: "pac_script",
							pacScript: {
								data: "function FindProxyForURL(u,h){if(dnsDomainIs(h,'"+domain+"'))return'"+access+" "+ip+":"+port+"';return'DIRECT'}"
							}
						};
						chrome.proxy.settings.set({value: config, scope: 'regular'}, function() {
							console.log('Got IP '+ip+' from SERVER. Proxy config is set.');
						});
						sessionStorage.setItem(domain, ip);
					}
				}
			}
			xhr.open("GET", url, false);
			xhr.send();

			if(sessionStorage.getItem(domain) == null) {
				var start = new Date().getTime();
				do {} while(((new Date().getTime() - start) < 2000) && (sessionStorage.getItem(domain) == null));
			}
		} else {
			var ip = sessionStorage.getItem(domain);
			var config = {
				mode: "pac_script",
				pacScript: {
					data: "function FindProxyForURL(u,h){if(dnsDomainIs(h,'"+domain+"'))return'"+access+" "+ip+":"+port+"';return'DIRECT'}"
				}
			};
			chrome.proxy.settings.get({'incognito': false}, function(oldcfg) {
				if((oldcfg["value"]["pacScript"] == undefined) || (oldcfg["value"]["pacScript"]["data"] != config["pacScript"]["data"])) {
					chrome.proxy.settings.set({value: config, scope: 'regular'}, function() {
						console.log('Got IP '+ip+' from CACHE. Proxy config is changed!');
					});
				} else {
					console.log('Got IP '+ip+' from CACHE. Proxy config is NOT changed.');
				}
			});
		}
	}
}, { urls: ["<all_urls>"] }, ["blocking"]);

/*
chrome.omnibox.onInputEntered.addListener(function(alias) {
	var xhr = new XMLHttpRequest();
	var url = "https://peername.org/api/?name="+encodeURIComponent(alias)+"&namespace=nxt";
	xhr.onreadystatechange = function() {
		if(xhr.readyState == 4 && xhr.status == 200) {
			var xmlDoc = xhr.responseXML;
			if(xmlDoc.getElementsByTagName("value").length > 0) {
				var url = xmlDoc.getElementsByTagName("value")[0].childNodes[0].nodeValue;
				if(url.substring(0, 7) == "http://" || url.substring(0, 8) == "https://") {
					chrome.tabs.query({active: true, currentWindow: true}, function(tab) {
						chrome.tabs.update(tab[0].id, {url: url});
					});
				}
			}
		}
	}
	xhr.open("GET", url, false);
	xhr.send();
});
*/