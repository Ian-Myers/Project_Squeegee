const startSearch = async function startSearch() {
    
    document.getElementById("repopulateTable").innerHTML = "";
    
    var index = document.getElementById("stateDropdown").value.split(" ").join("_");
    var type = document.getElementById("countryDropdown").value;
    var keywords = document.getElementById("keywords").value;
    var size = 50;

    var searchParam = (keywords == "") ? 
    { index: index, type: type, size: size, body: { query: { match_all: {} }}} 
    : { index: index, type: type, size: size, body: { query: { multi_match: { query: keywords, fields: ["title", "summary", "url"] }}}};

    search(searchParam);
}

function search(searchParam) {
    client.search(searchParam).then(function(response) {
        var hits = response.hits.hits;
        var total = response.hits.total;
        if (total == 0) {
            document.getElementById("noMatches").style.visibility = "visible";
            document.getElementById("toggleTableDisplay").style.display = "none";
        }
        else if (total != 0) {
            constructTable(hits, total);
        }
    });
}

function searchWithEnterBtn(event) {
    var code = event.keyCode ? event.keyCode : event.which;
    if (code == 13) {
        document.getElementById("search").click();
    }
}