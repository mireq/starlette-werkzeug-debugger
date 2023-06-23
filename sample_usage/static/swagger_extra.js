(function(window) {


function E(tagName) {
	var i, leni;
	var attrs = {};
	var contentIndex = 1;
	if (arguments.length > 1 && arguments[1].constructor === Object) {
		attrs = arguments[1];
		contentIndex = 2;
	}
	tagName = tagName.split(/(?=[\.#])/);
	var tag = document.createElement(tagName[0]);
	for (i = 1, leni = tagName.length; i < leni; i++) {
		var tagExtra = tagName[i];
		if (tagExtra[0] === '.') {
			tag.classList.add(tagExtra.slice(1));
		}
		else {
			tag.setAttribute('id', tagExtra.slice(1));
		}
	}

	for (var attrName in attrs) {
		if (Object.prototype.hasOwnProperty.call(attrs, attrName)) {
			tag.setAttribute(attrName, attrs[attrName]);
		}
	}

	for (i = contentIndex, leni = arguments.length; i < leni; i++) {
		var content = arguments[i];
		if (content === undefined) {
			continue;
		}
		if (typeof content === 'string') {
			tag.appendChild(document.createTextNode(content));
		}
		else {
			tag.appendChild(content);
		}
	}

	return tag;
}


function setIframeConteent(iframe, content) {
	var doc = iframe.contentWindow.document;
	doc.open();
	doc.write(content);
	doc.close();
}


function showIframe(content) {
	var closeButton, ifraame;
	var dialog = E('dialog.dialog',
		iframe = E('iframe.dialog__iframe'),
		E('form', {method: 'dialog'},
			closeButton = E('button.dialog__close')
		)
	);
	closeButton.innerHTML = '<svg width="20" height="20"><use href="#close" xlink:href="#close"></use></svg>';
	if (iframe.contentWindow) {
		setIframeConteent(iframe, content);
	}
	else {
		iframe.addEventListener(
			'load',
			function() {
				setIframeConteent(iframe, content);
			}
		);
	}

	dialog.addEventListener(
		'close',
		function() {
			document.body.removeChild(dialog);
		}
	);

	document.body.appendChild(dialog);
	dialog.showModal();
}

window.responseInterceptor = function(response) {
	if (response && response.headers && response.headers['content-type'] && response.headers['content-type'].indexOf('text/html') === 0) {
		showIframe(response.text);
	}
}


}(window));
