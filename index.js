function filldata() {
    var option = document.getElementById('drop-down-selection').value;

    if (option == "SELECT")
        return ;

    var query = "SELECT * FROM "+option;

    var start = document.getElementById('start-date');
    var end = document.getElementById('end-date');

    if (start.value != "" && end.value != "" && start.disabled == false && end.disabled == false) {
        var start_date = start.value+"T00:00:00.0000000Z";
        var end_date = end.value+"T00:00:00.0000000Z";

        query += " WHERE DATETIME BETWEEN '"+start_date+"' AND '"+end_date+"'";
    }

    query += ';';

	var xmlHttp = new XMLHttpRequest();
	xmlHttp.open("GET", `/api/${query}`, false);
	xmlHttp.send(null);

	var data = JSON.parse(xmlHttp.responseText);

	result = document.getElementById("result");

	if (data['ok']) {
	    content = '<table><tr>';

	    var n, m, i, j, k;
	    m = data['columns'].length;

	    for (i = 0; i < m; i++)
	        content += `<th>${data['columns'][i]}</th>`;

	    content += '<tr>';

	    n = data['values'].length;

	    for (i = 0; i < n; i++) {
	        content += '<tr>';

	        for (j = 0; j < m; j++)
	            content += `<td>${data['values'][i][j]}</td>`;

	        content += '</tr>';
	    }

	    content += '</table>';

	    result.innerHTML = content;
	}
	else
	    result.innerHTML = 'Error occured: '+data['error']
}

function make_disable() {
    var option = document.getElementById('drop-down-selection').value;

    var start = document.getElementById('start-date');
    var end = document.getElementById('end-date');

    if (option == "EVENTS" || option == "CHATS" || option == "EMAILS") {
        start.disabled = false;
        end.disabled = false;
    }
    else {
        start.disabled = true;
        end.disabled = true;
    }
}
