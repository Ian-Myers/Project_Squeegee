function loadCountryDropdown() {
    var masterList = countryRegionList;
    var countryList = [];
    for (var country in masterList) {
        countryList.push(country);
    }
    countryList = countryList.sort();
    countryInnerHtml = "<option value=\"\" disabled selected hidden>Select Country</option>";
    for (i = 0; i < countryList.length; i++) {
        countryInnerHtml += "<option>" + countryList[i] + "</option>";
    }
    document.getElementById("country").innerHTML = countryInnerHtml;
}

function populateRegionDropdown() {
    var country = $('#country').val();
    var masterList = countryRegionList;
    var regionList = ["National Data"];
    for (var region in masterList[country]["divisions"]) {
        regionList.push(masterList[country]["divisions"][region]);
    }
    regionInnerHtml = "<option value=\"\" disabled selected hidden>Select Region</option>";
    for (i = 0; i < regionList.length; i++) {
        regionInnerHtml += "<option>" + regionList[i] + "</option>";
    }
    document.getElementById("region").innerHTML = regionInnerHtml;
}

function validURL(str) {
    var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
    '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
    '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
    '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
    '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
    '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return !!pattern.test(str);
}

$(document).ready(function(){
    $('#submit').click(function(){
        var url = $("#url").val();
        var region = $("#region").val().split(" ").join("_");
        var country = $("#country").val().split(" ").join("_");
        var isurlvalid = validURL(url);
        if (isurlvalid) {
            $('#message').text('');
            var params = {
                TableName: "squeegee_master_list",
                Item: {
                    "URL": url,
                    "Region": region.toLowerCase(),
                    "Country": country,
                    "Type": "source"
                }
            };
            docClient.put(params, function (err, data) {
                if (err) {
                    $('#message').text("Unable to add url: " + url);
                    console.log(err);
                } else {
                    $('#message').html("Successfully uploaded: <a href=" + url + ">" + url + "</a><p>Your new source will be included in the next quarterly scraping</p>");
                }
            });
        }
        if (!isurlvalid) {
            $('#message').text('Your URL is not valid!');
        }
    })
});